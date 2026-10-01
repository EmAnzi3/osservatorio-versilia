#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data"/"source-snapshots"/"a3-mim-history-source-manifest.json"
SITE=ROOT/"data"/"site-data.json"
TOWNS=("Camaiore","Forte dei Marmi","Massarosa","Pietrasanta","Seravezza","Stazzema","Viareggio")
TOWN_NORM={}


def norm(value: str) -> str:
    value=unicodedata.normalize("NFKD",str(value or ""))
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]+"," ",value.upper()).strip()


for _town in TOWNS:
    TOWN_NORM[norm(_town)]=_town


def load(path: Path) -> dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def integer(value: Any) -> int:
    text=str(value or "").strip().replace(".","").replace(",",".")
    if not text: return 0
    return int(round(float(text)))


def fetch_csv(session: requests.Session, url: str) -> list[dict[str,str]]:
    response=session.get(url,timeout=240)
    response.raise_for_status()
    raw=response.content
    text=raw.decode("utf-8-sig",errors="replace")
    sample=text[:8192]
    try:
        dialect=csv.Sniffer().sniff(sample,delimiters=",;|\t")
        delimiter=dialect.delimiter
    except csv.Error:
        delimiter=","
    rows=list(csv.DictReader(io.StringIO(text),delimiter=delimiter))
    if not rows:
        raise RuntimeError(f"CSV vuoto: {url}")
    return rows


def school_map(rows: list[dict[str,str]]) -> dict[str,str]:
    mapping={}
    for row in rows:
        town=TOWN_NORM.get(norm(row.get("DESCRIZIONECOMUNE") or row.get("COMUNE") or ""))
        if not town: continue
        for key in ("CODICEPLESSO","CODICESCUOLA"):
            code=str(row.get(key) or "").strip()
            if code:
                previous=mapping.get(code)
                if previous and previous!=town:
                    raise RuntimeError(f"Codice scuola {code} associato a due Comuni: {previous}/{town}")
                mapping[code]=town
    return mapping


def aggregate_year(session: requests.Session, spec: dict[str,str]) -> dict[str,dict[str,float]]:
    registry=[]
    for key in ("registry_state","registry_private"):
        registry.extend(fetch_csv(session,spec[key]))
    mapping=school_map(registry)
    if not mapping:
        raise RuntimeError("Nessuna scuola della Versilia individuata nell'anagrafe MIM")

    totals={town:{"students":0,"classes":0,"primaryStudents":0,"fullTimeStudents":0} for town in TOWNS}
    allowed_orders=("SCUOLA PRIMARIA","SCUOLA SECONDARIA I GRADO","SCUOLA SECONDARIA II GRADO")

    for key in ("classes_state","classes_private"):
        for row in fetch_csv(session,spec[key]):
            town=mapping.get(str(row.get("CODICESCUOLA") or "").strip())
            if not town: continue
            order=norm(row.get("ORDINESCUOLA") or "")
            if order not in {norm(x) for x in allowed_orders}: continue
            students=integer(row.get("ALUNNIMASCHI"))+integer(row.get("ALUNNIFEMMINE"))
            totals[town]["students"]+=students
            totals[town]["classes"]+=integer(row.get("CLASSI"))

    for key in ("time_state","time_private"):
        for row in fetch_csv(session,spec[key]):
            town=mapping.get(str(row.get("CODICESCUOLA") or "").strip())
            if not town: continue
            if norm(row.get("ORDINESCUOLA") or "")!=norm("SCUOLA PRIMARIA"): continue
            students=integer(row.get("ALUNNIMASCHI"))+integer(row.get("ALUNNIFEMMINE"))
            totals[town]["primaryStudents"]+=students
            if norm(row.get("TEMPOSCUOLA") or "")==norm("TEMPO PIENO"):
                totals[town]["fullTimeStudents"]+=students

    for town,raw in totals.items():
        if raw["students"]<=0 or raw["classes"]<=0 or raw["primaryStudents"]<=0:
            raise RuntimeError(f"{town}: aggregati MIM incompleti {raw}")
        raw["studentsPerClass"]=raw["students"]/raw["classes"]
        raw["primaryFullTimeShare"]=raw["fullTimeStudents"]/raw["primaryStudents"]*100.0
    return totals


def validate_latest(snapshot: dict[str,Any], site: dict[str,Any]) -> None:
    latest=snapshot["years"]["2024/25"]
    for metric_id,field,tol in (
        ("schoolStudents","students",0.0),
        ("studentsPerClass","studentsPerClass",1e-9),
        ("primaryFullTimeShare","primaryFullTimeShare",1e-9),
    ):
        metric=(site.get("metrics") or {}).get(metric_id)
        if not isinstance(metric,dict): raise RuntimeError(f"{metric_id}: metrica pubblica mancante")
        rows={str(row["town"]):row for row in metric.get("rows",[]) if isinstance(row,dict) and row.get("town")}
        if set(rows)!=set(TOWNS): raise RuntimeError(f"{metric_id}: perimetro pubblico non 7/7")
        for town in TOWNS:
            actual=float(latest[town][field])
            expected=float(rows[town]["value"])
            if not math.isclose(actual,expected,rel_tol=0.0,abs_tol=tol):
                raise RuntimeError(f"{metric_id}/{town}: acquisito {actual} != pubblico {expected}")


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    manifest=load(MANIFEST)
    session=requests.Session()
    session.headers["User-Agent"]="OsservatorioVersilia-A3-MIM-history/1.0"
    result={
        "schemaVersion":1,
        "publisher":manifest["publisher"],
        "sourceProfileId":manifest["sourceProfileId"],
        "metricDefinitions":{
            "schoolStudents":"alunni primarie e secondarie statali/paritarie localizzate nel Comune",
            "studentsPerClass":"alunni primarie e secondarie / classi delle stesse scuole",
            "primaryFullTimeShare":"alunni primaria TEMPO PIENO / alunni primaria × 100",
        },
        "years":{},
        "sources":manifest["years"],
    }
    for school_year,spec in manifest["years"].items():
        print(f"MIM {school_year}: acquisizione 6 CSV...")
        result["years"][school_year]=aggregate_year(session,spec)
    validate_latest(result,load(SITE))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"A3 MIM history acquisition OK: {len(result['years'])} anni × {len(TOWNS)} Comuni; 2024/25 riconciliato con il catalogo pubblico.")

if __name__=="__main__":
    main()
