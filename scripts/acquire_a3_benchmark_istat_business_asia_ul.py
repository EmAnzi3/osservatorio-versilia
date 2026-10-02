#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import requests

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/agid-asia-agcom-2026-08.json"
DATASET="ISTAT/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
API=f"https://api.db.nomics.world/v22/series/{DATASET}"
OFFICIAL_URL="https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
TUSCANY_PREFIXES={"045","046","047","048","049","050","051","052","053","100"}
YEARS={2018,2023}
PAGE=1000

def six(value:Any)->str:
    text=str(value or "").strip()
    return text if len(text)==6 and text.isdigit() else ""

def fetch_type(session:requests.Session,data_type:str)->dict[str,dict[int,float]]:
    dims={
      "FREQ":["A"],
      "PERS_EMPL_SIZE_CLASS":["TOTAL"],
      "DATA_TYPE":[data_type],
      "ECON_ACTIVITY_NACE_2007":["0010"],
    }
    out={}
    offset=0
    expected=None
    while expected is None or offset<expected:
        response=session.get(API,params={
          "dimensions":json.dumps(dims,separators=(",",":")),
          "observations":"1","limit":str(PAGE),"offset":str(offset),
        },timeout=180)
        response.raise_for_status()
        payload=response.json().get("series") or {}
        expected=int(payload.get("num_found") or 0)
        docs=payload.get("docs") or []
        if expected<=0:
            raise RuntimeError(f"ASIA-UL {data_type}: DBnomics non restituisce serie")
        for doc in docs:
            code=six((doc.get("dimensions") or {}).get("REF_AREA"))
            if not code: continue
            periods=doc.get("period") or []
            values=doc.get("value") or []
            for period,value in zip(periods,values):
                try: year=int(str(period)[:4]); number=float(value)
                except Exception: continue
                if year not in YEARS or not math.isfinite(number): continue
                old=out.setdefault(code,{}).get(year)
                if old is not None and not math.isclose(old,number,rel_tol=0.0,abs_tol=1e-9):
                    raise RuntimeError(f"ASIA-UL {data_type}: duplicato incoerente {code}/{year}: {old} != {number}")
                out[code][year]=number
        if len(docs)<PAGE: break
        offset+=PAGE
    return out

def scope_sum(values:dict[str,dict[int,float]],year:int,scope:str)->tuple[float,int]:
    rows=[]
    for code,series in values.items():
        if year not in series: continue
        if scope=="tuscany" and code[:3] not in TUSCANY_PREFIXES: continue
        rows.append(series[year])
    if not rows: raise RuntimeError(f"ASIA-UL: scope vuoto {scope}/{year}")
    return sum(rows),len(rows)

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    local=json.loads(LOCAL.read_text(encoding="utf-8"))
    session=requests.Session()
    session.headers["User-Agent"]="OsservatorioVersilia-A3-ASIAUL-benchmark/1.0"
    units=fetch_type(session,"LU")
    employees=fetch_type(session,"AENTEMPDAA")

    errors=[]
    for town in local.get("towns") or []:
        code=str(town.get("code") or "")
        asia=town.get("asia") or {}
        years=[int(x) for x in asia.get("years") or []]
        lu=list(asia.get("localUnits") or [])
        emp=list(asia.get("employeesAverageAnnual") or [])
        for year in YEARS:
            if year not in years:
                errors.append(f"{code}: anno {year} assente snapshot"); continue
            i=years.index(year)
            got_u=(units.get(code) or {}).get(year)
            got_e=(employees.get(code) or {}).get(year)
            if got_u is None or not math.isclose(got_u,float(lu[i]),rel_tol=0.0,abs_tol=.01):
                errors.append(f"{code}/{year}/LU: {got_u} != {lu[i]}")
            if got_e is None or not math.isclose(got_e,float(emp[i]),rel_tol=0.0,abs_tol=.011):
                errors.append(f"{code}/{year}/EMP: {got_e} != {emp[i]}")

    scopes={}
    for scope in ("tuscany","italy"):
        u18,c_u18=scope_sum(units,2018,scope); u23,c_u23=scope_sum(units,2023,scope)
        e18,c_e18=scope_sum(employees,2018,scope); e23,c_e23=scope_sum(employees,2023,scope)
        if scope=="tuscany" and (c_u23!=273 or c_e23!=273):
            errors.append(f"Toscana 2023 coverage LU/EMP {c_u23}/{c_e23} != 273")
        if scope=="italy" and min(c_u23,c_e23)<7800:
            errors.append(f"Italia 2023 coverage LU/EMP insufficiente {c_u23}/{c_e23}")
        scopes[scope]={
          "localUnits2018":u18,"localUnits2023":u23,
          "localEmployees2018":e18,"localEmployees2023":e23,
          "coverage":{"units2018":c_u18,"units2023":c_u23,"employees2018":c_e18,"employees2023":c_e23},
        }

    benchmarks={}
    if not errors:
        for scope,d in scopes.items():
            d["employeesPerLocalUnit"]=d["localEmployees2023"]/d["localUnits2023"]
            d["localUnitsChange"]=(d["localUnits2023"]/d["localUnits2018"]-1.0)*100.0
            d["localEmployeesChange"]=(d["localEmployees2023"]/d["localEmployees2018"]-1.0)*100.0
        specs={
          "localUnits":("number","localUnits2023","unità locali attive"),
          "localEmployees":("number","localEmployees2023","addetti medi annui"),
          "employeesPerLocalUnit":("decimal","employeesPerLocalUnit","addetti medi annui / unità locali"),
          "localUnitsChange":("percent","localUnitsChange","((UL 2023 / UL 2018) - 1) × 100"),
          "localEmployeesChange":("percent","localEmployeesChange","((addetti 2023 / addetti 2018) - 1) × 100"),
        }
        for metric_id,(unit,key,formula) in specs.items():
            benchmarks[metric_id]={
              "year":"2023" if "Change" not in metric_id else "2018–2023",
              "unit":unit,"formula":formula,
              "tuscany":scopes["tuscany"][key],"italy":scopes["italy"][key],
            }

    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":1,"publisher":"Istat — ASIA Unità Locali","profileId":"istat-business-annual",
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "officialSourceUrl":OFFICIAL_URL,"retrievalMirror":"DBnomics mirror of Istat SDMX",
      "dataset":DATASET,"benchmarks":benchmarks,"scopes":scopes,
      "qualityGate":{"status":gate,"publicSnapshotReconciliation":"5 metrics lineage · 7/7 towns × 2018/2023 PASS" if gate=="PASS" else "FAIL","errors":errors},
      "blocked":{"microUnits":"richiede la distribuzione per classe dimensionale ASIA-UL; non inferita dal totale"},
    }
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(benchmarks),"scopes":scopes,"errors":errors[:20]},ensure_ascii=False))
if __name__=="__main__": main()
