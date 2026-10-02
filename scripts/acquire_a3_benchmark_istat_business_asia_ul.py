#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,io,json,math,re
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/agid-asia-agcom-2026-08.json"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
MUNICIPAL_FLOW="IT1,183_1163_DF_DICA_ASIAULP_TERRIFDATA_7,1.0"

OFFICIAL_URL="https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0900ENT,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
TUSCANY_PREFIXES=("045","046","047","048","049","050","051","052","053","100")
DATA_TYPES=("LU","LUEMPDAA")
YEARS=(2018,2023)
ACCEPT="application/vnd.sdmx.data+csv;version=1.0.0"

def code6(v:Any)->str:
    raw=str(v or "").strip()
    if not raw or not re.fullmatch(r"\d+(?:\.0+)?",raw):
        return ""
    digits=str(int(float(raw)))
    return digits.zfill(6) if 1<=len(digits)<=6 else ""

def fetch_year(session:requests.Session,data_type:str,year:int)->dict[str,float]:
    key=f"A..{data_type}.0010.TOTAL"
    url=f"{BASE}/{MUNICIPAL_FLOW}/{key}"
    response=session.get(
        url,
        params={"startPeriod":str(year),"endPeriod":str(year)},
        headers={"Accept":ACCEPT},
        timeout=300,
    )
    response.raise_for_status()
    text=response.content.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(io.StringIO(text))
    required={"REF_AREA","DATA_TYPE","TIME_PERIOD","OBS_VALUE"}
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError(f"ASIA-UL {data_type}/{year}: schema CSV inatteso {reader.fieldnames}")
    out={}
    for row in reader:
        if str(row.get("DATA_TYPE") or "").strip()!=data_type: continue
        try: row_year=int(str(row.get("TIME_PERIOD") or "")[:4])
        except Exception: continue
        if row_year!=year: continue
        code=code6(row.get("REF_AREA"))
        if not code: continue
        try: value=float(str(row.get("OBS_VALUE") or "").replace(",","."))
        except Exception: continue
        if not math.isfinite(value): continue
        old=out.get(code)
        if old is not None and not math.isclose(old,value,rel_tol=0.0,abs_tol=1e-9):
            raise RuntimeError(f"ASIA-UL {data_type}/{year}: duplicato {code}: {old} != {value}")
        out[code]=value
    if len(out)<7800:
        raise RuntimeError(f"ASIA-UL {data_type}/{year}: copertura comunale insufficiente {len(out)}")
    return out

def build_series(session:requests.Session,data_type:str)->dict[str,dict[int,float]]:
    result={}
    for year in YEARS:
        values=fetch_year(session,data_type,year)
        for code,value in values.items():
            result.setdefault(code,{})[year]=value
    return result

def aggregate_scope(values:dict[str,dict[int,float]],year:int,scope:str)->tuple[float,int]:
    selected=[]
    for code,series in values.items():
        if year not in series: continue
        if scope=="tuscany" and code[:3] not in TUSCANY_PREFIXES: continue
        selected.append(float(series[year]))
    if not selected:
        raise RuntimeError(f"ASIA-UL {scope}/{year}: aggregato vuoto")
    return sum(selected),len(selected)

def local_reconciliation(values:dict[str,dict[int,float]],local:dict,field:str)->list[str]:
    errors=[]
    for town in local.get("towns") or []:
        code=str(town.get("code") or "")
        asia=town.get("asia") or {}
        years=[int(x) for x in asia.get("years") or []]
        expected=list(asia.get(field) or [])
        for year in YEARS:
            if year not in years:
                errors.append(f"{code}: anno {year} assente snapshot")
                continue
            got=(values.get(code) or {}).get(year)
            exp=float(expected[years.index(year)])
            if got is None or not math.isclose(got,exp,rel_tol=0.0,abs_tol=.011):
                errors.append(f"{code}/{year}/{field}: {got} != {exp}")
    return errors

def sum_scope(values:dict[str,dict[int,float]],areas:list[str],year:int,label:str)->float:
    missing=[area for area in areas if year not in (values.get(area) or {})]
    if missing:
        raise RuntimeError(f"ASIA-UL {label}: aree mancanti {year}: {missing}")
    return sum(float(values[area][year]) for area in areas)

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    local=json.loads(LOCAL.read_text(encoding="utf-8"))
    town_codes=[str(t.get("code") or "") for t in local.get("towns") or []]
    if len(town_codes)!=7 or any(not code6(code) for code in town_codes):
        raise RuntimeError(f"ASIA-UL: town codes inattesi {town_codes}")

    session=requests.Session()
    session.headers["User-Agent"]="OsservatorioVersilia-A3-ASIAUL-benchmark/4.0"

    data={dtype:build_series(session,dtype) for dtype in DATA_TYPES}

    benchmarks={}
    blocked={}
    evidence={}
    specs={
      "LU":{"field":"localUnits","metricIds":["localUnits","localUnitsChange"]},
      "LUEMPDAA":{"field":"employeesAverageAnnual","metricIds":["localEmployees","employeesPerLocalUnit","localEmployeesChange"]},
    }

    for dtype,spec in specs.items():
        values=data.get(dtype) or {}
        errors=local_reconciliation(values,local,spec["field"])
        try:
            tus={}
            ita={}
            for year in YEARS:
                tus[year],tus_count=aggregate_scope(values,year,"tuscany")
                ita[year],ita_count=aggregate_scope(values,year,"italy")
                if tus_count!=273:
                    errors.append(f"Toscana {dtype}/{year}: coverage {tus_count} != 273")
                if ita_count<7800:
                    errors.append(f"Italia {dtype}/{year}: coverage {ita_count} < 7800")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            tus={}; ita={}
        evidence[dtype]={"errors":errors,"tuscany":tus,"italy":ita}
        if errors:
            for mid in spec["metricIds"]:
                blocked[mid]="; ".join(errors[:20])
            continue

        if dtype=="LU":
            benchmarks["localUnits"]={
              "year":"2023","unit":"number","formula":"unità locali attive",
              "tuscany":tus[2023],"italy":ita[2023],
            }
            benchmarks["localUnitsChange"]={
              "year":"2018–2023","unit":"percent",
              "formula":"((UL 2023 / UL 2018)-1)×100",
              "tuscany":(tus[2023]/tus[2018]-1.0)*100.0,
              "italy":(ita[2023]/ita[2018]-1.0)*100.0,
            }
        else:
            benchmarks["localEmployees"]={
              "year":"2023","unit":"number","formula":"addetti medi annui",
              "tuscany":tus[2023],"italy":ita[2023],
            }
            benchmarks["localEmployeesChange"]={
              "year":"2018–2023","unit":"percent",
              "formula":"((addetti 2023 / addetti 2018)-1)×100",
              "tuscany":(tus[2023]/tus[2018]-1.0)*100.0,
              "italy":(ita[2023]/ita[2018]-1.0)*100.0,
            }

    if "localUnits" in benchmarks and "localEmployees" in benchmarks:
        benchmarks["employeesPerLocalUnit"]={
          "year":"2023","unit":"decimal","formula":"addetti medi annui / unità locali",
          "tuscany":benchmarks["localEmployees"]["tuscany"]/benchmarks["localUnits"]["tuscany"],
          "italy":benchmarks["localEmployees"]["italy"]/benchmarks["localUnits"]["italy"],
        }
    else:
        blocked["employeesPerLocalUnit"]="richiede LU e LUEMPDAA entrambi riconciliati"

    blocked["microUnits"]="richiede distribuzione per classe dimensionale ASIA-UL; non inferita dal totale"
    status="ACQUIRED_CANDIDATE" if benchmarks else "CANDIDATE_REJECTED"
    payload={
      "schemaVersion":3,
      "publisher":"Istat — ASIA Unità Locali",
      "profileId":"istat-business-annual",
      "status":status,
      "officialSourceUrl":OFFICIAL_URL,
      "retrieval":"Istat SEP SDMX ufficiale",
      "flows":{"municipal":MUNICIPAL_FLOW},
      "requestCount":4,
      "benchmarks":benchmarks,
      "evidence":evidence,
      "qualityGate":{
        "status":"PASS" if benchmarks else "FAIL",
        "publicSnapshotReconciliation":"metric-level 7/7 × 2018/2023; Toscana e Italia aggregati dalle stesse osservazioni comunali ufficiali",
        "candidateMetrics":sorted(benchmarks),
      },
      "blocked":blocked,
    }
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"candidateMetrics":sorted(benchmarks),"blocked":blocked},ensure_ascii=False))

if __name__=="__main__":
    main()
