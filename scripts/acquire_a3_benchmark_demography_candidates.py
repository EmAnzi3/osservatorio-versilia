#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Any, Callable

import requests

POSAS_2026="https://demo.istat.it/data/posas/POSAS_2026_it_Comuni.zip"
P2_2019="https://demo.istat.it/data/p2/P2_2019_it_Comuni.zip"
P2_2024="https://demo.istat.it/data/p2/P2_2024_it_Comuni.zip"
P2_2025="https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip"
TOSCANY_PROVINCES={"045","046","047","048","049","050","051","052","053","100"}


def norm(value:Any)->str:
    text=unicodedata.normalize("NFKD",str(value or ""))
    text="".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+"," ",text.lower()).strip()


def num(value:Any)->float:
    text=str(value or "").strip().replace(".","").replace(",",".")
    return float(text) if text else 0.0


def download_rows(session:requests.Session,url:str)->tuple[list[str],list[dict[str,str]],str]:
    response=session.get(url,timeout=300)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names=[n for n in archive.namelist() if n.lower().endswith((".csv",".txt"))]
        if len(names)!=1:
            raise RuntimeError(f"Archivio inatteso {url}: {names}")
        raw=archive.read(names[0]).decode("utf-8-sig",errors="strict")
    parsed=list(csv.reader(io.StringIO(raw),delimiter=";"))
    if len(parsed)<3:
        raise RuntimeError(f"CSV troppo corto: {url}")
    title=parsed[0][0].strip()
    headers=[cell.strip() for cell in parsed[1]]
    rows=[]
    for row in parsed[2:]:
        if not row:
            continue
        padded=row+[""]*max(0,len(headers)-len(row))
        rows.append(dict(zip(headers,padded,strict=False)))
    return headers,rows,title


def code_of(row:dict[str,str])->str:
    for key,value in row.items():
        if norm(key)=="codice comune":
            return re.sub(r"\D","",str(value or "")).zfill(6)[-6:]
    return ""


def pred_tuscany(code:str)->bool:
    return len(code)==6 and code[:3] in TOSCANY_PROVINCES


def pred_italy(code:str)->bool:
    return bool(re.fullmatch(r"\d{6}",code))


def pick(headers:list[str],required:tuple[str,...],reject:tuple[str,...]=())->str:
    hits=[]
    for header in headers:
        h=norm(header)
        if all(token in h for token in required) and not any(token in h for token in reject):
            hits.append(header)
    if len(hits)!=1:
        raise RuntimeError(f"Header non univoco required={required} reject={reject}: {hits}")
    return hits[0]


def age_number(value:Any)->int|None:
    text=norm(value)
    if not text or text in {"totale","total"}:
        return None
    match=re.search(r"\d+",text)
    return int(match.group()) if match else None


def aggregate_posas(headers:list[str],rows:list[dict[str,str]],predicate:Callable[[str],bool])->dict[str,Any]:
    age_h=pick(headers,("eta",))
    total_h=pick(headers,("totale",),("maschi","femmine"))
    men_h=pick(headers,("totale","maschi"))
    women_h=pick(headers,("totale","femmine"))
    bands={"0-14":0.0,"15-19":0.0,"20-34":0.0,"35-49":0.0,"50-64":0.0,"65-79":0.0,"80-84":0.0,"85+":0.0}
    total=0.0
    age_weight=0.0
    for row in rows:
        code=code_of(row)
        if not predicate(code):
            continue
        age=age_number(row.get(age_h))
        if age is None:
            continue
        value=num(row.get(total_h))
        men=num(row.get(men_h)); women=num(row.get(women_h))
        if not math.isclose(value,men+women,rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"POSAS {code}/{age}: totale != uomini+donne")
        total+=value
        age_weight+=age*value
        if age<=14: bands["0-14"]+=value
        elif age<=19: bands["15-19"]+=value
        elif age<=34: bands["20-34"]+=value
        elif age<=49: bands["35-49"]+=value
        elif age<=64: bands["50-64"]+=value
        elif age<=79: bands["65-79"]+=value
        elif age<=84: bands["80-84"]+=value
        else: bands["85+"]+=value
    if total<=0 or not math.isclose(sum(bands.values()),total,rel_tol=0.0,abs_tol=0.1):
        raise RuntimeError("POSAS: classi di età non esaustive")
    age0_14=bands["0-14"]
    age15_64=bands["15-19"]+bands["20-34"]+bands["35-49"]+bands["50-64"]
    age65plus=bands["65-79"]+bands["80-84"]+bands["85+"]
    shares={k:v/total*100 for k,v in bands.items()}
    return {
        "population":total,
        "bands":bands,
        "shares":shares,
        "meanAge":age_weight/total,
        "age0_14":age0_14,
        "age15_64":age15_64,
        "age65plus":age65plus,
        "structuralDependencyIndex":(age0_14+age65plus)/age15_64*100,
        "oldAgeDependencyIndex":age65plus/age15_64*100,
    }


def p2_headers(headers:list[str])->dict[str,str]:
    return {
        "jan1":pick(headers,("popolazione","1 gennaio","totale")),
        "dec31":pick(headers,("popolazione","31 dicembre","totale")),
        "births":pick(headers,("nati vivi","totale")),
        "deaths":pick(headers,("morti","totale")),
        "natural":pick(headers,("saldo naturale","totale")),
        "internalIn":pick(headers,("iscritti","altri comuni","totale")),
        "internalOut":pick(headers,("cancellati","altri comuni","totale")),
        "foreignIn":pick(headers,("iscritti","estero","totale")),
        "foreignOut":pick(headers,("cancellati","estero","totale")),
    }


def aggregate_p2(headers:list[str],rows:list[dict[str,str]],predicate:Callable[[str],bool])->dict[str,float]:
    h=p2_headers(headers)
    out={key:0.0 for key in h}
    matched=0
    for row in rows:
        code=code_of(row)
        if not predicate(code):
            continue
        matched+=1
        for key,header in h.items():
            out[key]+=num(row.get(header))
    if matched<=0:
        raise RuntimeError("P02: nessun Comune nel perimetro")
    out["meanPopulation"]=(out["jan1"]+out["dec31"])/2.0
    return out


def rate(value:float,pop:float)->float:
    return value/pop*1000.0 if pop else float("nan")


def scope_payload(
    posas:dict[str,Any],
    p2019:dict[str,float],
    p2024:dict[str,float],
    p2025:dict[str,float],
)->dict[str,Any]:
    population=p2025["dec31"]
    if not math.isclose(population,posas["population"],rel_tol=0.0,abs_tol=1.0):
        raise RuntimeError(f"Popolazione POSAS/P02 non riconciliata: {posas['population']} vs {population}")
    change=(population-p2019["jan1"])/p2019["jan1"]*100.0
    natural=rate(p2025["natural"],p2025["meanPopulation"])
    internal_balance=p2024["internalIn"]-p2024["internalOut"]
    foreign_balance=p2024["foreignIn"]-p2024["foreignOut"]
    total_in=p2024["internalIn"]+p2024["foreignIn"]
    total_out=p2024["internalOut"]+p2024["foreignOut"]
    total_balance=total_in-total_out
    return {
        "population":population,
        "populationChange":change,
        "ageDistribution":posas["shares"]["20-34"],
        "dependencyIndices":posas["structuralDependencyIndex"],
        "naturalDemographicDynamics":natural,
        "internalResidentialMobility":rate(internal_balance,p2024["meanPopulation"]),
        "foreignResidentialMobility":rate(foreign_balance,p2024["meanPopulation"]),
        "totalResidentialMobility":rate(total_balance,p2024["meanPopulation"]),
        "components":{
            "ageDistribution":posas,
            "naturalDemographicDynamics":{
                "birthRatePer1000":rate(p2025["births"],p2025["meanPopulation"]),
                "deathRatePer1000":rate(p2025["deaths"],p2025["meanPopulation"]),
                "naturalBalanceRatePer1000":natural,
                "births":p2025["births"],"deaths":p2025["deaths"],"naturalBalance":p2025["natural"],
                "meanPopulation":p2025["meanPopulation"],
            },
            "internalResidentialMobility":{
                "incoming":p2024["internalIn"],"outgoing":p2024["internalOut"],"balance":internal_balance,
                "meanPopulation":p2024["meanPopulation"],
            },
            "foreignResidentialMobility":{
                "incoming":p2024["foreignIn"],"outgoing":p2024["foreignOut"],"balance":foreign_balance,
                "meanPopulation":p2024["meanPopulation"],
            },
            "totalResidentialMobility":{
                "incoming":total_in,"outgoing":total_out,"balance":total_balance,
                "meanPopulation":p2024["meanPopulation"],
            },
            "populationChange":{"start2019":p2019["jan1"],"end2026":population},
        },
    }


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    session=requests.Session()
    session.headers["User-Agent"]="OsservatorioVersilia-A3-demography-benchmark/2.0"

    pos_h,pos_rows,pos_title=download_rows(session,POSAS_2026)
    h19,r19,t19=download_rows(session,P2_2019)
    h24,r24,t24=download_rows(session,P2_2024)
    h25,r25,t25=download_rows(session,P2_2025)

    scopes={}
    for name,predicate in (("tuscany",pred_tuscany),("italy",pred_italy)):
        pos=aggregate_posas(pos_h,pos_rows,predicate)
        p19=aggregate_p2(h19,r19,predicate)
        p24=aggregate_p2(h24,r24,predicate)
        p25=aggregate_p2(h25,r25,predicate)
        scopes[name]=scope_payload(pos,p19,p24,p25)

    specs={
        "population":{"unit":"number","year":"2026"},
        "populationChange":{"unit":"percent","year":"2019–2026"},
        "ageDistribution":{"unit":"percent","year":"2026","defaultPart":"20–34 anni"},
        "dependencyIndices":{"unit":"per100","year":"2026","defaultPart":"Indice di dipendenza strutturale"},
        "naturalDemographicDynamics":{"unit":"per1000","year":"2025","defaultPart":"Saldo naturale"},
        "internalResidentialMobility":{"unit":"per1000","year":"2024","defaultPart":"Saldo migratorio interno"},
        "foreignResidentialMobility":{"unit":"per1000","year":"2024","defaultPart":"Saldo migratorio con l’estero"},
        "totalResidentialMobility":{"unit":"per1000","year":"2024","defaultPart":"Saldo complessivo dei trasferimenti"},
    }
    benchmarks={}
    for metric_id,spec in specs.items():
        benchmarks[metric_id]={
            **spec,
            "tuscany":scopes["tuscany"][metric_id],
            "italy":scopes["italy"][metric_id],
        }

    payload={
        "schemaVersion":2,
        "publisher":"Istat",
        "profileId":"istat-demography-annual",
        "status":"ACQUIRED_CANDIDATE",
        "sources":{
            "posas2026":{"url":POSAS_2026,"title":pos_title},
            "p2_2019":{"url":P2_2019,"title":t19},
            "p2_2024":{"url":P2_2024,"title":t24},
            "p2_2025":{"url":P2_2025,"title":t25},
        },
        "benchmarks":benchmarks,
        "scopes":scopes,
        "qualityGate":{
            "populationPosasP02Reconciled":True,
            "ageBandsExhaustive":True,
            "tuscanyProvincePrefixes":sorted(TOSCANY_PROVINCES),
            "note":"I benchmark sono aggregati sui Comuni del perimetro; tassi e rapporti sono ricalcolati su numeratori e denominatori aggregati, non come media semplice dei Comuni.",
        },
    }
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "A3 demography benchmark acquisition: "
        f"{len(benchmarks)} metriche candidate · Toscana/Italia · "
        f"popolazione Italia 2026={scopes['italy']['population']:.0f}."
    )


if __name__=="__main__":
    main()
