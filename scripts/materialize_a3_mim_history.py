#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
SNAP=ROOT/"data"/"source-snapshots"/"a3-mim-history-2019-2025.json"
SNAP_REF="data/source-snapshots/a3-mim-history-2019-2025.json"

TARGETS={
    "schoolStudents":("students",0.0),
    "studentsPerClass":("studentsPerClass",1e-9),
    "primaryFullTimeShare":("primaryFullTimeShare",1e-9),
}


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path:Path,value:dict[str,Any])->None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def rows_by_town(metric:dict[str,Any],metric_id:str)->dict[str,dict[str,Any]]:
    rows=metric.get("rows")
    if not isinstance(rows,list):
        raise RuntimeError(f"{metric_id}: rows mancanti")
    result={str(row.get("town")):row for row in rows if isinstance(row,dict) and row.get("town")}
    if len(result)!=7:
        raise RuntimeError(f"{metric_id}: attesi 7 Comuni")
    return result


def main()->None:
    site=load(SITE)
    snap=load(SNAP)
    years=snap.get("years")
    if not isinstance(years,dict) or len(years)<2 or "2024/25" not in years:
        raise RuntimeError("Snapshot MIM storico incompleto")
    labels=list(years.keys())
    latest=years["2024/25"]
    metrics=site.get("metrics")
    if not isinstance(metrics,dict):
        raise RuntimeError("Catalogo privo di metrics")

    acquired=0
    for metric_id,(field,tolerance) in TARGETS.items():
        metric=metrics.get(metric_id)
        if not isinstance(metric,dict):
            raise RuntimeError(f"{metric_id}: metrica mancante")
        rows=rows_by_town(metric,metric_id)
        unit=str((metric.get("meta") or {}).get("unit") or "")
        for town,row in rows.items():
            if town not in latest:
                raise RuntimeError(f"{metric_id}/{town}: ultimo anno assente")
            expected=float(row.get("value"))
            actual=float(latest[town][field])
            if not math.isclose(actual,expected,rel_tol=0.0,abs_tol=tolerance):
                raise RuntimeError(f"{metric_id}/{town}: snapshot {actual} != pubblico {expected}")
            values=[]
            for school_year in labels:
                payload=years[school_year].get(town)
                if not isinstance(payload,dict) or field not in payload:
                    raise RuntimeError(f"{metric_id}/{town}/{school_year}: valore assente")
                values.append(payload[field])
            row["series"]={
                "years":labels,
                "values":values,
                "unit":unit,
                "source":"MIM — Portale unico dei dati della scuola",
                "sourceSnapshot":SNAP_REF,
                "note":"Serie scolastica omogenea acquisita dai CSV annuali MIM; il 2024/25 è riconciliato con il valore pubblico corrente.",
            }
        meta=metric.setdefault("meta",{})
        meta["historySourceSnapshot"]=SNAP_REF
        meta["historyPeriodStart"]=labels[0]
        meta["historyPeriodEnd"]=labels[-1]
        meta["historyFrequency"]="school_year"
        acquired+=1

    save(SITE,site)
    print(f"A3 MIM history materializer: {acquired} metriche · {len(labels)} anni · 7/7 Comuni.")


if __name__=="__main__":
    main()
