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
PROVINCE_FLOW="IT1,183_1163_DF_DICA_ASIAULP_TERRIFDATA_6,1.0"
ITALY_FLOW="IT1,183_1163_DF_DICA_ASIAULP_TERRIFDATA_4,1.0"
OFFICIAL_URL="https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0900ENT,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
TUSCANY_PROVINCES=("045","046","047","048","049","050","051","052","053","100")
DATA_TYPES=("LU","LUEMPDAA")
YEARS=(2018,2023)
ACCEPT="application/vnd.sdmx.data+csv;version=1.0.0"

def code6(v:Any)->str:
    raw=str(v or "").strip()
    if not raw: return ""
    if re.fullmatch(r"\d+(?:\.0+)?",raw):
        digits=str(int(float(raw)))
    else:
        digits=re.sub(r"\D","",raw)
    return digits.zfill(6) if 1<=len(digits)<=6 else ""

def fetch_rows(session:requests.Session,flow:str,areas:list[str],label:str)->list[dict[str,str]]:
    key=f"A.{'+'.join(areas)}.{'+'.join(DATA_TYPES)}.0010.TOTAL"
    url=f"{BASE}/{flow}/{key}"
    response=session.get(
        url,
        params={"startPeriod":"2018"},
        headers={"Accept":ACCEPT},
        timeout=300,
    )
    response.raise_for_status()
    text=response.content.decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(io.StringIO(text))
    rows=[dict(row) for row in reader]
    if not rows:
        raise RuntimeError(f"ASIA-UL {label}: risposta CSV vuota {response.url}")
    required={"REF_AREA","DATA_TYPE","TIME_PERIOD","OBS_VALUE"}
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError(f"ASIA-UL {label}: schema CSV inatteso {reader.fieldnames}")
    return rows

def parse(rows:list[dict[str,str]],area_mode:str)->dict[str,dict[str,dict[int,float]]]:
    out={dtype:{} for dtype in DATA_TYPES}
    for row in rows:
        dtype=str(row.get("DATA_TYPE") or "").strip()
        if dtype not in out: continue
        raw_area=str(row.get("REF_AREA") or "").strip()
        if area_mode=="municipality":
            area=code6(raw_area)
        else:
            area=re.sub(r"\D","",raw_area) if raw_area!="IT" else "IT"
            if area_mode=="province" and area:
                area=area.zfill(3)
        if not area: continue
        try:
            year=int(str(row.get("TIME_PERIOD") or "")[:4])
            value=float(str(row.get("OBS_VALUE") or "").replace(",","."))
        except Exception:
            continue
        if year not in YEARS or not math.isfinite(value): continue
        old=out[dtype].setdefault(area,{}).get(year)
        if old is not None and not math.isclose(old,value,rel_tol=0.0,abs_tol=1e-9):
            raise RuntimeError(f"ASIA-UL duplicato incoerente {dtype}/{area}/{year}: {old} != {value}")
        out[dtype][area][year]=value
    return out

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

    municipal=parse(fetch_rows(session,MUNICIPAL_FLOW,town_codes,"municipal"),"municipality")
    province=parse(fetch_rows(session,PROVINCE_FLOW,list(TUSCANY_PROVINCES),"province"),"province")
    italy=parse(fetch_rows(session,ITALY_FLOW,["IT"],"italy"),"italy")

    benchmarks={}
    blocked={}
    evidence={}
    specs={
      "LU":{"field":"localUnits","metricIds":["localUnits","localUnitsChange"]},
      "LUEMPDAA":{"field":"employeesAverageAnnual","metricIds":["localEmployees","employeesPerLocalUnit","localEmployeesChange"]},
    }

    for dtype,spec in specs.items():
        errors=local_reconciliation(municipal.get(dtype) or {},local,spec["field"])
        try:
            tus={year:sum_scope(province.get(dtype) or {},list(TUSCANY_PROVINCES),year,f"Toscana/{dtype}") for year in YEARS}
            ita={}
            for year in YEARS:
                value=((italy.get(dtype) or {}).get("IT") or {}).get(year)
                if value is None:
                    raise RuntimeError(f"ASIA-UL Italia {dtype}: anno {year} assente")
                ita[year]=float(value)
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
      "flows":{"municipal":MUNICIPAL_FLOW,"province":PROVINCE_FLOW,"italy":ITALY_FLOW},
      "requestCount":3,
      "benchmarks":benchmarks,
      "evidence":evidence,
      "qualityGate":{
        "status":"PASS" if benchmarks else "FAIL",
        "publicSnapshotReconciliation":"metric-level 7/7 × 2018/2023; Toscana da 10 province; Italia da flow nazionale",
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
