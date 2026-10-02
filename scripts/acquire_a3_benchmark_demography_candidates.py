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
RCS_2025="https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip"
SITE_DATA=Path(__file__).resolve().parents[1]/"data"/"site-data.json"
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
    total_row=0.0
    age_weight=0.0
    total_rows=0
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
        if age==999:
            total_row+=value
            total_rows+=1
            continue
        if age<0 or age>120:
            raise RuntimeError(f"POSAS età inattesa: {age}")
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
    if total<=0 or total_rows<=0:
        raise RuntimeError("POSAS: righe età o totale 999 mancanti")
    if not math.isclose(total,total_row,rel_tol=0.0,abs_tol=0.1):
        raise RuntimeError(f"POSAS: somma età {total} != totale 999 {total_row}")
    if not math.isclose(sum(bands.values()),total,rel_tol=0.0,abs_tol=0.1):
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

def pick_exact(headers:list[str],expected:str)->str:
    target=norm(expected)
    hits=[header for header in headers if norm(header)==target]
    if len(hits)!=1:
        raise RuntimeError(f"Header esatto non univoco {expected!r}: {hits}")
    return hits[0]


def pick_population_total(headers:list[str],day_token:str)->str:
    hits=[]
    for header in headers:
        h=norm(header)
        if "popolazione" not in h or day_token not in h or "totale" not in h:
            continue
        if "famiglia" in h or "convivenza" in h:
            continue
        hits.append(header)
    if len(hits)!=1:
        raise RuntimeError(f"Header popolazione {day_token} non univoco: {hits}")
    return hits[0]


def p2_population_headers(headers:list[str])->dict[str,str]:
    return {
        "jan1":pick_population_total(headers,"gennaio"),
        "dec31":pick_population_total(headers,"dicembre"),
    }


def p2_natural_headers(headers:list[str])->dict[str,str]:
    return {
        **p2_population_headers(headers),
        "births":pick_exact(headers,"Nati vivi - Totale"),
        "deaths":pick_exact(headers,"Morti - Totale"),
        "natural":pick_exact(headers,"Saldo naturale - Totale"),
    }


def pick_mobility(headers:list[str],movement:str,scope:str)->str:
    hits=[]
    for header in headers:
        h=norm(header)
        if movement not in h or "totale" not in h:
            continue
        if scope=="internal":
            if "comun" not in h or "estero" in h or "motivi" in h:
                continue
        elif scope=="foreign":
            if "estero" not in h:
                continue
        else:
            raise RuntimeError(f"Scope mobilità inatteso: {scope}")
        hits.append(header)
    if len(hits)!=1:
        raise RuntimeError(
            f"Header mobilità non univoco movement={movement} scope={scope}: "
            f"hits={hits}; headers={headers}"
        )
    return hits[0]

def p2_mobility_headers(headers:list[str])->dict[str,str]:
    return {
        **p2_population_headers(headers),
        "internalIn":pick_mobility(headers,"iscritti","internal"),
        "internalOut":pick_mobility(headers,"cancellati","internal"),
        "foreignIn":pick_mobility(headers,"iscritti","foreign"),
        "foreignOut":pick_mobility(headers,"cancellati","foreign"),
    }

def aggregate_p2(
    headers:list[str],
    rows:list[dict[str,str]],
    predicate:Callable[[str],bool],
    mode:str,
)->dict[str,float]:
    if mode=="population":
        h=p2_population_headers(headers)
    elif mode=="natural":
        h=p2_natural_headers(headers)
    elif mode=="mobility":
        h=p2_mobility_headers(headers)
    else:
        raise RuntimeError(f"Modalità P02 non supportata: {mode}")

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


def rcs_benchmark(session:requests.Session)->dict[str,Any]:
    response=session.get(RCS_2025,timeout=300)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members=[name for name in archive.namelist() if name.lower().endswith((".csv",".txt"))]
        if not members:
            raise RuntimeError("RCS cittadinanza senza CSV/TXT")
        member=max(members,key=lambda name:archive.getinfo(name).file_size)
        raw=archive.read(member).decode("utf-8-sig",errors="strict")
    reader=csv.DictReader(io.StringIO(raw),delimiter=";")
    required={"Codice Istat","Codice stato di cittadinanza","Stato di cittadinanza","Maschi","Femmine","Totale"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise RuntimeError(f"Schema RCS inatteso: {reader.fieldnames}")

    scopes={
        "tuscany":{"foreign":0.0,"population":0.0,"municipalities":set()},
        "italy":{"foreign":0.0,"population":0.0,"municipalities":set()},
    }
    towns={}
    for row in reader:
        raw_code=re.sub(r"\D","",str(row.get("Codice Istat") or "").strip())
        # RCS contiene anche righe territoriali aggregate con codici più corti.
        # Non zero-pad: solo codici comunali grezzi esattamente a 6 cifre.
        if not re.fullmatch(r"\d{6}",raw_code):
            continue
        code=raw_code
        value=num(row.get("Totale"))
        men=num(row.get("Maschi")); women=num(row.get("Femmine"))
        if not math.isclose(value,men+women,rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"RCS {code}: Totale != Maschi+Femmine")
        citizenship_code=str(row.get("Codice stato di cittadinanza") or "").strip()
        label=norm(row.get("Stato di cittadinanza"))
        is_foreign=citizenship_code!="100" and label!="italia"

        for scope,predicate in (("tuscany",pred_tuscany),("italy",pred_italy)):
            if not predicate(code):
                continue
            scopes[scope]["population"]+=value
            if is_foreign:
                scopes[scope]["foreign"]+=value
            scopes[scope]["municipalities"].add(code)

        town=towns.setdefault(code,{"foreign":0.0,"population":0.0})
        town["population"]+=value
        if is_foreign:
            town["foreign"]+=value

    site=json.loads(SITE_DATA.read_text(encoding="utf-8"))
    public={str(row["code"]):row for row in site["metrics"]["foreignResidents"]["rows"]}
    for code,row in public.items():
        got=towns.get(code)
        if not got:
            raise RuntimeError(f"RCS: Comune pubblico assente {code}")
        expected_count=float(row["count"])
        expected_population=float(row["population"])
        expected_share=float(row["value"])
        got_share=got["foreign"]/got["population"]*100.0
        if not math.isclose(got["foreign"],expected_count,rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"RCS {code}: residenti stranieri {got['foreign']} != pubblico {expected_count}")
        if not math.isclose(got["population"],expected_population,rel_tol=0.0,abs_tol=0.1):
            raise RuntimeError(f"RCS {code}: popolazione {got['population']} != pubblico {expected_population}")
        if not math.isclose(got_share,expected_share,rel_tol=0.0,abs_tol=1e-10):
            raise RuntimeError(f"RCS {code}: quota {got_share} != pubblico {expected_share}")

    out={}
    for scope,value in scopes.items():
        if value["population"]<=0:
            raise RuntimeError(f"RCS {scope}: popolazione nulla")
        out[scope]={
            "foreign":value["foreign"],
            "population":value["population"],
            "share":value["foreign"]/value["population"]*100.0,
            "municipalityCount":len(value["municipalities"]),
        }
    return {
        "url":RCS_2025,
        "archiveMember":member,
        "validation":"7/7 public rows reconciled",
        "scopes":out,
    }


def mobility_benchmark(headers:list[str],rows:list[dict[str,str]])->dict[str,Any]:
    h=p2_mobility_headers(headers)
    site=json.loads(SITE_DATA.read_text(encoding="utf-8"))
    public={mid:{str(row["code"]):row for row in site["metrics"][mid]["rows"]} for mid in (
        "internalResidentialMobility","foreignResidentialMobility","totalResidentialMobility"
    )}
    town_errors=[]
    for code in sorted(public["internalResidentialMobility"]):
        source=next((row for row in rows if code_of(row)==code),None)
        if source is None:
            town_errors.append(f"{code}: P02 2024 assente"); continue
        jan=num(source[h["jan1"]]); dec=num(source[h["dec31"]]); mean=(jan+dec)/2.0
        ii=num(source[h["internalIn"]]); io=num(source[h["internalOut"]])
        fi=num(source[h["foreignIn"]]); fo=num(source[h["foreignOut"]])
        expected={
            "internalResidentialMobility":(ii-io)/mean*1000.0,
            "foreignResidentialMobility":(fi-fo)/mean*1000.0,
            "totalResidentialMobility":((ii+fi)-(io+fo))/mean*1000.0,
        }
        counts={
            "internalResidentialMobility":[ii,io,ii-io],
            "foreignResidentialMobility":[fi,fo,fi-fo],
            "totalResidentialMobility":[ii+fi,io+fo,(ii+fi)-(io+fo)],
        }
        for mid,value in expected.items():
            prow=public[mid][code]
            if not math.isclose(float(prow["value"]),value,rel_tol=0.0,abs_tol=1e-10):
                town_errors.append(f"{mid}/{code}: {value} != {prow['value']}")
            pcounts=[float(part["count"]) for part in prow.get("parts",[])]
            if len(pcounts)!=3 or any(not math.isclose(a,b,rel_tol=0.0,abs_tol=.1) for a,b in zip(pcounts,counts[mid])):
                town_errors.append(f"{mid}/{code}: component counts {counts[mid]} != {pcounts}")
    if town_errors:
        raise RuntimeError("P02 2024 mobility 7/7 reconciliation FAIL: "+" | ".join(town_errors[:30]))

    out={}
    for scope,predicate in (("tuscany",pred_tuscany),("italy",pred_italy)):
        a=aggregate_p2(headers,rows,predicate,"mobility")
        mean=a["meanPopulation"]
        out[scope]={
            "internalResidentialMobility":(a["internalIn"]-a["internalOut"])/mean*1000.0,
            "foreignResidentialMobility":(a["foreignIn"]-a["foreignOut"])/mean*1000.0,
            "totalResidentialMobility":((a["internalIn"]+a["foreignIn"])-(a["internalOut"]+a["foreignOut"]))/mean*1000.0,
            "components":a,
        }
    return {"scopes":out,"validation":"3 metrics × 7/7 public rows + components PASS"}

def scope_payload(
    posas:dict[str,Any],
    p2019:dict[str,float],
    p2025:dict[str,float],
)->dict[str,Any]:
    population=p2025["dec31"]
    if not math.isclose(population,posas["population"],rel_tol=0.0,abs_tol=1.0):
        raise RuntimeError(f"Popolazione POSAS/P02 non riconciliata: {posas['population']} vs {population}")
    change=(population-p2019["jan1"])/p2019["jan1"]*100.0
    natural=rate(p2025["natural"],p2025["meanPopulation"])
    return {
        "population":population,
        "populationChange":change,
        "ageDistribution":posas["shares"]["20-34"],
        "dependencyIndices":posas["structuralDependencyIndex"],
        "naturalDemographicDynamics":natural,
        "components":{
            "ageDistribution":posas,
            "naturalDemographicDynamics":{
                "birthRatePer1000":rate(p2025["births"],p2025["meanPopulation"]),
                "deathRatePer1000":rate(p2025["deaths"],p2025["meanPopulation"]),
                "naturalBalanceRatePer1000":natural,
                "births":p2025["births"],"deaths":p2025["deaths"],"naturalBalance":p2025["natural"],
                "meanPopulation":p2025["meanPopulation"],
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
    rcs=rcs_benchmark(session)
    mobility=mobility_benchmark(h24,r24)

    scopes={}
    p02_population_2025={}
    for name,predicate in (("tuscany",pred_tuscany),("italy",pred_italy)):
        pos=aggregate_posas(pos_h,pos_rows,predicate)
        p19=aggregate_p2(h19,r19,predicate,"population")
        p25=aggregate_p2(h25,r25,predicate,"natural")
        scopes[name]=scope_payload(pos,p19,p25)
        p02_population_2025[name]=p25["jan1"]

    for name in ("tuscany","italy"):
        rcs_population=float(rcs["scopes"][name]["population"])
        p02_population=float(p02_population_2025[name])
        if not math.isclose(rcs_population,p02_population,rel_tol=0.0,abs_tol=1.0):
            raise RuntimeError(
                f"RCS {name}: popolazione 1/1/2025 {rcs_population} != P02 1/1/2025 {p02_population}"
            )

    specs={
        "population":{"unit":"number","year":"2026"},
        "populationChange":{"unit":"percent","year":"2019–2026"},
        "ageDistribution":{"unit":"percent","year":"2026","defaultPart":"20–34 anni"},
        "dependencyIndices":{"unit":"per100","year":"2026","defaultPart":"Indice di dipendenza strutturale"},
        "naturalDemographicDynamics":{"unit":"per1000","year":"2025","defaultPart":"Saldo naturale"},
        "foreignResidents":{"unit":"percent","year":"2025"},
        "internalResidentialMobility":{"unit":"per1000","year":"2024"},
        "foreignResidentialMobility":{"unit":"per1000","year":"2024"},
        "totalResidentialMobility":{"unit":"per1000","year":"2024"},
    }
    benchmarks={}
    for metric_id,spec in specs.items():
        if metric_id=="foreignResidents":
            tuscany=rcs["scopes"]["tuscany"]["share"]
            italy=rcs["scopes"]["italy"]["share"]
        elif metric_id in {"internalResidentialMobility","foreignResidentialMobility","totalResidentialMobility"}:
            tuscany=mobility["scopes"]["tuscany"][metric_id]
            italy=mobility["scopes"]["italy"][metric_id]
        else:
            tuscany=scopes["tuscany"][metric_id]
            italy=scopes["italy"][metric_id]
        benchmarks[metric_id]={
            **spec,
            "tuscany":tuscany,
            "italy":italy,
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
            "rcs_2025":{"url":RCS_2025,"archiveMember":rcs["archiveMember"]},
        },
        "benchmarks":benchmarks,
        "scopes":scopes,
        "rcs":rcs,
        "mobility2024":mobility,
        "qualityGate":{
            "populationPosasP02Reconciled":True,
            "foreignResidentsRcs7of7Reconciled":True,
            "mobilityP0220247of7Reconciled":True,
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
