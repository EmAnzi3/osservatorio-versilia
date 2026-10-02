#!/usr/bin/env python3
from __future__ import annotations

import argparse,json,math
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

def six(v:Any)->str:
    s=str(v or "").strip()
    return s if len(s)==6 and s.isdigit() else ""
def request_docs(session:requests.Session,dims:dict[str,list[str]],offset:int=0,limit:int=PAGE)->dict:
    r=session.get(API,params={"dimensions":json.dumps(dims,separators=(",",":")),"observations":"1","limit":str(limit),"offset":str(offset)},timeout=180)
    r.raise_for_status()
    return r.json().get("series") or {}
def fetch_type(session:requests.Session,data_type:str)->dict[str,dict[int,float]]:
    dims={"FREQ":["A"],"PERS_EMPL_SIZE_CLASS":["TOTAL"],"DATA_TYPE":[data_type],"ECON_ACTIVITY_NACE_2007":["0010"]}
    out={}; offset=0; expected=None
    while expected is None or offset<expected:
        p=request_docs(session,dims,offset)
        expected=int(p.get("num_found") or 0); docs=p.get("docs") or []
        if expected<=0: return {}
        for doc in docs:
            code=six((doc.get("dimensions") or {}).get("REF_AREA"))
            if not code: continue
            for period,value in zip(doc.get("period") or [],doc.get("value") or []):
                try:y=int(str(period)[:4]); x=float(value)
                except Exception: continue
                if y not in YEARS or not math.isfinite(x): continue
                old=out.setdefault(code,{}).get(y)
                if old is not None and not math.isclose(old,x,rel_tol=0.0,abs_tol=1e-9):
                    raise RuntimeError(f"ASIA-UL {data_type}: duplicato {code}/{y}")
                out[code][y]=x
        if len(docs)<PAGE: break
        offset+=PAGE
    return out
def discover_types(session:requests.Session)->list[str]:
    dims={"FREQ":["A"],"PERS_EMPL_SIZE_CLASS":["TOTAL"],"ECON_ACTIVITY_NACE_2007":["0010"]}
    p=request_docs(session,dims,0,300)
    return sorted({str((doc.get("dimensions") or {}).get("DATA_TYPE") or "").strip() for doc in p.get("docs") or [] if str((doc.get("dimensions") or {}).get("DATA_TYPE") or "").strip()})
def scope_sum(values:dict[str,dict[int,float]],year:int,scope:str)->tuple[float,int]:
    vals=[]
    for code,series in values.items():
        if year not in series: continue
        if scope=="tuscany" and code[:3] not in TUSCANY_PREFIXES: continue
        vals.append(series[year])
    if not vals: raise RuntimeError(f"ASIA-UL: scope vuoto {scope}/{year}")
    return sum(vals),len(vals)
def local_reconciliation(values:dict[str,dict[int,float]],local:dict,field:str)->list[str]:
    errors=[]
    for town in local.get("towns") or []:
        code=str(town.get("code") or ""); asia=town.get("asia") or {}
        years=[int(x) for x in asia.get("years") or []]; expected=list(asia.get(field) or [])
        for year in YEARS:
            if year not in years: errors.append(f"{code}: anno {year} assente"); continue
            got=(values.get(code) or {}).get(year); exp=float(expected[years.index(year)])
            if got is None or not math.isclose(got,exp,rel_tol=0.0,abs_tol=.011):
                errors.append(f"{code}/{year}/{field}: {got} != {exp}")
    return errors
def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    local=json.loads(LOCAL.read_text(encoding="utf-8"))
    session=requests.Session(); session.headers["User-Agent"]="OsservatorioVersilia-A3-ASIAUL-benchmark/2.0"
    units=fetch_type(session,"LU")
    unit_errors=local_reconciliation(units,local,"localUnits")
    blocked={}; benchmarks={}; scopes={}; discovered=[]
    if not unit_errors:
        for scope in ("tuscany","italy"):
            u18,c18=scope_sum(units,2018,scope); u23,c23=scope_sum(units,2023,scope)
            scopes.setdefault(scope,{})["units"]={"2018":u18,"2023":u23,"coverage2018":c18,"coverage2023":c23}
            if scope=="tuscany" and c23!=273: unit_errors.append(f"Toscana LU coverage {c23} != 273")
            if scope=="italy" and c23<7800: unit_errors.append(f"Italia LU coverage insufficiente {c23}")
    if not unit_errors:
        for scope,d in scopes.items(): d["units"]["change"]=(d["units"]["2023"]/d["units"]["2018"]-1.0)*100.0
        benchmarks["localUnits"]={"year":"2023","unit":"number","formula":"unità locali attive","tuscany":scopes["tuscany"]["units"]["2023"],"italy":scopes["italy"]["units"]["2023"]}
        benchmarks["localUnitsChange"]={"year":"2018–2023","unit":"percent","formula":"((UL 2023 / UL 2018)-1)×100","tuscany":scopes["tuscany"]["units"]["change"],"italy":scopes["italy"]["units"]["change"]}
    else:
        blocked["localUnits"]="; ".join(unit_errors[:20]); blocked["localUnitsChange"]=blocked["localUnits"]

    employee_type=None; employees={}
    for candidate in ["AENTEMPDAA"]:
        values=fetch_type(session,candidate)
        if values and not local_reconciliation(values,local,"employeesAverageAnnual"):
            employee_type=candidate; employees=values; break
    if employee_type is None:
        try: discovered=discover_types(session)
        except Exception as exc: blocked["employeeTypeDiscovery"]=f"{type(exc).__name__}: {exc}"
        for candidate in discovered:
            if candidate=="LU": continue
            try: values=fetch_type(session,candidate)
            except Exception: continue
            if values and not local_reconciliation(values,local,"employeesAverageAnnual"):
                employee_type=candidate; employees=values; break

    if employee_type:
        emp_errors=[]
        for scope in ("tuscany","italy"):
            e18,c18=scope_sum(employees,2018,scope); e23,c23=scope_sum(employees,2023,scope)
            scopes.setdefault(scope,{})["employees"]={"2018":e18,"2023":e23,"coverage2018":c18,"coverage2023":c23}
            if scope=="tuscany" and c23!=273: emp_errors.append(f"Toscana EMP coverage {c23} != 273")
            if scope=="italy" and c23<7800: emp_errors.append(f"Italia EMP coverage insufficiente {c23}")
        if not emp_errors and "localUnits" in benchmarks:
            for scope,d in scopes.items():
                d["employees"]["change"]=(d["employees"]["2023"]/d["employees"]["2018"]-1.0)*100.0
                d["employeesPerLocalUnit"]=d["employees"]["2023"]/d["units"]["2023"]
            benchmarks.update({
              "localEmployees":{"year":"2023","unit":"number","formula":"addetti medi annui","tuscany":scopes["tuscany"]["employees"]["2023"],"italy":scopes["italy"]["employees"]["2023"]},
              "employeesPerLocalUnit":{"year":"2023","unit":"decimal","formula":"addetti medi annui / unità locali","tuscany":scopes["tuscany"]["employeesPerLocalUnit"],"italy":scopes["italy"]["employeesPerLocalUnit"]},
              "localEmployeesChange":{"year":"2018–2023","unit":"percent","formula":"((addetti 2023 / addetti 2018)-1)×100","tuscany":scopes["tuscany"]["employees"]["change"],"italy":scopes["italy"]["employees"]["change"]},
            })
        else:
            blocked["localEmployees"]="; ".join(emp_errors[:20]); blocked["employeesPerLocalUnit"]=blocked["localEmployees"]; blocked["localEmployeesChange"]=blocked["localEmployees"]
    else:
        reason=f"datatype addetti non riconciliato; DATA_TYPE osservati={discovered}"
        blocked["localEmployees"]=reason; blocked["employeesPerLocalUnit"]=reason; blocked["localEmployeesChange"]=reason

    blocked["microUnits"]="richiede la distribuzione per classe dimensionale ASIA-UL; non inferita dal totale"
    status="ACQUIRED_CANDIDATE" if benchmarks else "CANDIDATE_REJECTED"
    payload={"schemaVersion":2,"publisher":"Istat — ASIA Unità Locali","profileId":"istat-business-annual","status":status,
      "officialSourceUrl":OFFICIAL_URL,"retrievalMirror":"DBnomics mirror of Istat SDMX","dataset":DATASET,
      "employeeDataType":employee_type,"discoveredDataTypes":discovered,"benchmarks":benchmarks,"scopes":scopes,
      "qualityGate":{"status":"PASS" if benchmarks else "FAIL","publicSnapshotReconciliation":"metric-level 7/7 × 2018/2023","unitErrors":unit_errors},
      "blocked":blocked}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"candidateMetrics":sorted(benchmarks),"employeeDataType":employee_type,"blocked":blocked},ensure_ascii=False))
if __name__=="__main__": main()
