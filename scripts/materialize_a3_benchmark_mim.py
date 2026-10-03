#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
SNAP=ROOT/"data"/"source-snapshots"/"a3-mim-benchmark-2024-25.json"
SNAP_REF="data/source-snapshots/a3-mim-benchmark-2024-25.json"
SOURCE_URL="https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti"

TARGETS={
    "schoolStudents":{
        "unit":"people",
        "year":"a.s. 2024/25",
        "formula":"somma di alunni maschi e femmine per scuola, unendo anagrafe e dati di classe di istituti statali e paritari",
    },
    "studentsPerClass":{
        "unit":"studentsPerClass",
        "year":"a.s. 2024/25",
        "formula":"alunni delle scuole primarie e secondarie / classi delle stesse scuole",
    },
    "primaryFullTimeShare":{
        "unit":"percent",
        "year":"a.s. 2024/25",
        "formula":"alunni della primaria con TEMPOSCUOLA = “TEMPO PIENO” / alunni totali della primaria × 100",
    },
}


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def norm(value:Any)->str:
    return re.sub(r"\s+"," ",str(value or "").strip().lower())


def finite(value:Any)->bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))


def validate_snapshot(snap:dict[str,Any])->None:
    if snap.get("schoolYear")!="2024/25":
        raise RuntimeError("Snapshot MIM benchmark con anno scolastico inatteso")
    if (snap.get("acquisitionGate") or {}).get("status")!="PASS":
        raise RuntimeError("Snapshot MIM benchmark senza acquisition gate PASS")
    raw=snap.get("raw") or {}
    bench=snap.get("benchmarks") or {}
    for scope in ("tuscany","italy"):
        r=raw.get(scope)
        if not isinstance(r,dict):
            raise RuntimeError(f"MIM benchmark {scope}: raw mancante")
        for key in ("schoolStudents","classes","primaryStudents","fullTimeStudents"):
            if not finite(r.get(key)) or float(r[key])<=0:
                raise RuntimeError(f"MIM benchmark {scope}: {key} non valido")
        expected_students=float(r["schoolStudents"])/float(r["classes"])
        expected_full=float(r["fullTimeStudents"])/float(r["primaryStudents"])*100.0
        actual_students=float((bench.get("studentsPerClass") or {}).get(scope))
        actual_full=float((bench.get("primaryFullTimeShare") or {}).get(scope))
        if not math.isclose(actual_students,expected_students,rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"MIM benchmark {scope}: studentsPerClass non riconciliato")
        if not math.isclose(actual_full,expected_full,rel_tol=0.0,abs_tol=1e-12):
            raise RuntimeError(f"MIM benchmark {scope}: primaryFullTimeShare non riconciliato")
        if float((bench.get("schoolStudents") or {}).get(scope))!=float(r["schoolStudents"]):
            raise RuntimeError(f"MIM benchmark {scope}: schoolStudents non riconciliato")


def main()->None:
    site=load(SITE)
    snap=load(SNAP)
    validate_snapshot(snap)
    metrics=site.get("metrics")
    if not isinstance(metrics,dict):
        raise RuntimeError("Catalogo senza metrics")

    updated=0
    for metric_id,cfg in TARGETS.items():
        metric=metrics.get(metric_id)
        if not isinstance(metric,dict):
            raise RuntimeError(f"{metric_id}: metrica mancante")
        meta=metric.get("meta")
        if not isinstance(meta,dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        if str(meta.get("year"))!=cfg["year"] or str(meta.get("unit"))!=cfg["unit"]:
            raise RuntimeError(
                f"{metric_id}: contratto inatteso anno={meta.get('year')} unità={meta.get('unit')}"
            )
        if str(metric.get("sourceUrl") or "")!=SOURCE_URL:
            raise RuntimeError(f"{metric_id}: sourceUrl non allineato al profilo MIM Studenti")
        method=metric.get("method")
        if not isinstance(method,dict) or norm(method.get("formula"))!=norm(cfg["formula"]):
            raise RuntimeError(f"{metric_id}: formula pubblica non allineata allo snapshot MIM")

        spec=(snap.get("benchmarks") or {}).get(metric_id)
        if not isinstance(spec,dict):
            raise RuntimeError(f"{metric_id}: benchmark assente dallo snapshot")
        if str(spec.get("unit"))!=cfg["unit"]:
            raise RuntimeError(f"{metric_id}: unità snapshot non allineata")
        tuscany=spec.get("tuscany"); italy=spec.get("italy")
        if not finite(tuscany) or not finite(italy):
            raise RuntimeError(f"{metric_id}: benchmark Toscana/Italia non numerico")

        meta["benchmark"]={
            "year":"2024/25",
            "tuscany":tuscany,
            "italy":italy,
            "source":"MIM — Portale unico dei dati della scuola",
            "url":SOURCE_URL,
            "sourceSnapshot":SNAP_REF,
            "note":"Benchmark aggregato sugli stessi conteggi MIM 2024/25 della metrica comunale; rapporti e quote sono ricalcolati su numeratori e denominatori complessivi, non come media semplice dei Comuni.",
        }
        updated+=1

    SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"A3 benchmark MIM: {updated} metriche Toscana/Italia materializzate con contratto omogeneo 2024/25.")


if __name__=="__main__":
    main()
