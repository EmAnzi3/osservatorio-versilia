#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/istat-agricoltura-territorio-2020.json"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
TOWNS="046005+046013+046018+046024+046028+046030+046033"
SCOPES={"tuscany":"ITI1","italy":"IT"}

def fetch(session:requests.Session,flow:str,key:str)->tuple[list[dict[str,str]],str]:
    errors=[]
    for url in (f"{BASE}/{flow}/{key}/IT1",f"{BASE}/IT1,{flow},1.0/{key}/all"):
        try:
            r=session.get(url,params={"startPeriod":"2020","endPeriod":"2020","format":"csvfile"},timeout=240)
            r.raise_for_status()
            text=r.content.decode("utf-8-sig",errors="strict")
            rows=list(csv.DictReader(io.StringIO(text)))
            if rows and "REF_AREA" in rows[0] and "OBS_VALUE" in rows[0]:
                return rows,r.url
            errors.append(f"{r.url}: schema inatteso")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(" | ".join(errors))

def num(v:Any)->float:
    s=str(v or "").strip().replace(",",".")
    if not s: raise RuntimeError("valore SDMX vuoto")
    x=float(s)
    if not math.isfinite(x): raise RuntimeError("valore SDMX non finito")
    return x

def index(rows:list[dict[str,str]],extra:tuple[str,...]=())->dict[tuple[str,...],float]:
    out={}
    for r in rows:
        k=(str(r.get("REF_AREA") or "").strip(),str(r.get("DATA_TYPE") or "").strip(),*(str(r.get(x) or "").strip() for x in extra))
        v=num(r.get("OBS_VALUE"))
        if k in out and not math.isclose(out[k],v,abs_tol=1e-9): raise RuntimeError(f"duplicato {k}")
        out[k]=v
    return out

def direct(rows:list[dict[str,str]],area:str,data_type:str,extra:tuple[str,...]=(),extra_values:tuple[str,...]=())->float:
    hits=[]
    for r in rows:
        if str(r.get("REF_AREA") or "").strip()!=area: continue
        if str(r.get("DATA_TYPE") or "").strip()!=data_type: continue
        if any(str(r.get(k) or "").strip()!=v for k,v in zip(extra,extra_values)): continue
        hits.append(num(r.get("OBS_VALUE")))
    if len(hits)!=1: raise RuntimeError(f"{area}/{data_type}/{extra_values}: righe={len(hits)}")
    return hits[0]

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    session=requests.Session(); session.headers["User-Agent"]="OsservatorioVersilia-A3-agriculture/3.0"
    local=json.loads(LOCAL.read_text(encoding="utf-8"))["towns"]

    town_surface,u1=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_ALL",f"A.{TOWNS}.HO+ARU+FUAA")
    town_irr,u2=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",f"A.{TOWNS}.IA")
    town_loc,u3=fetch(session,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2",f"A.{TOWNS}.ARU.ALL.TOT")
    scope_codes="+".join(SCOPES.values())
    scope_surface,u4=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_ALL",f"A.{scope_codes}.HO+ARU+FUAA")
    scope_irr,u5=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",f"A.{scope_codes}.IA")
    scope_loc,u6=fetch(session,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2",f"A.{scope_codes}.ARU.ALL.TOT")

    s=index(town_surface); irr=index(town_irr); loc=index(town_loc,("TYPE_OF_CROP","ALTIMETRIC_ZONE"))
    errors=[]
    for code,d in local.items():
        checks={
          "farms":s.get((code,"HO")),
          "sauCenterHa":s.get((code,"ARU")),
          "farmsWithSau":s.get((code,"FUAA")),
          "irrigatedAreaHa":irr.get((code,"IA")),
          "sauLocalizedHa":loc.get((code,"ARU","ALL","TOT")),
        }
        for field,value in checks.items():
            if value is None or not math.isclose(float(value),float(d[field]),rel_tol=0.0,abs_tol=.02):
                errors.append(f"{code}/{field}: {value} != {d[field]}")

    benchmarks={}
    raw={}
    for scope,area in SCOPES.items():
        farms=direct(scope_surface,area,"HO")
        sau_center=direct(scope_surface,area,"ARU")
        farms_sau=direct(scope_surface,area,"FUAA")
        irrigated=direct(scope_irr,area,"IA")
        sau_local=direct(scope_loc,area,"ARU",("TYPE_OF_CROP","ALTIMETRIC_ZONE"),("ALL","TOT"))
        if farms<=0 or farms_sau<=0 or sau_center<=0 or sau_local<=0 or irrigated<0:
            raise RuntimeError(f"{scope}: componenti aggregate non valide")
        raw[scope]={"farms":farms,"sauCenterHa":sau_center,"farmsWithSau":farms_sau,"sauLocalizedHa":sau_local,"irrigatedAreaHa":irrigated}
    specs={
      "agriculturalFarms":("number",lambda x:x["farms"]),
      "agriculturalUsedArea":("hectares",lambda x:x["sauLocalizedHa"]),
      "averageAgriculturalFarmSize":("hectaresPerFarm",lambda x:x["sauCenterHa"]/x["farmsWithSau"]),
      "irrigatedAgriculturalArea":("hectares",lambda x:x["irrigatedAreaHa"]),
    }
    for metric,(unit,fn) in specs.items():
        benchmarks[metric]={"year":"2020","unit":unit,"tuscany":fn(raw["tuscany"]),"italy":fn(raw["italy"])}
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":2,"publisher":"Istat — 7° Censimento generale dell’agricoltura 2020",
      "profileId":"istat-agriculture-census-2020","referenceYear":2020,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"townSurface":u1,"townIrrigation":u2,"townLocalizedSau":u3,"scopeSurface":u4,"scopeIrrigation":u5,"scopeLocalizedSau":u6},
      "benchmarks":benchmarks,"raw":raw,
      "qualityGate":{"status":gate,"publicSnapshotReconciliation":"4 metrics × 7/7 towns PASS" if not errors else "FAIL","errors":errors},
      "blocked":{
        "cropProfile":"composite: benchmark della componente selezionata da certificare separatamente",
        "agriculturalRenewalAndLeadership":"Tav.13 usa classi <=29 e 30-44, non consente di ricostruire <=40 senza una fonte più granulare",
        "agriculturalDiversificationAndModernization":"attività connesse richiede il totale distinto delle aziende, non la somma delle sottocategorie"
      }
    }
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"benchmarks":benchmarks,"gate":payload["qualityGate"]},ensure_ascii=False))

if __name__=="__main__": main()
