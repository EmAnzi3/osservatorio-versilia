#!/usr/bin/env python3
from __future__ import annotations
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
FAMILIES_SNAP=ROOT/"data"/"source-snapshots"/"a3-istat-famiglie-benchmark-2023.json"
FAMILIES_REF="data/source-snapshots/a3-istat-famiglie-benchmark-2023.json"
LABOUR_SNAP=ROOT/"data"/"source-snapshots"/"a3-istat-lavoro-benchmark-2023.json"
LABOUR_REF="data/source-snapshots/a3-istat-lavoro-benchmark-2023.json"

def load(path):
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"JSON non-oggetto: {path}")
    return value

def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value))

def metric(site,metric_id):
    item=(site.get("metrics") or {}).get(metric_id)
    if not isinstance(item,dict): raise RuntimeError(f"{metric_id}: metrica mancante")
    meta=item.get("meta")
    if not isinstance(meta,dict): raise RuntimeError(f"{metric_id}: meta mancante")
    return item,meta

def apply_families(site):
    snap=load(FAMILIES_SNAP); spec=snap["benchmark"]; metric_id=spec["metricId"]
    _,meta=metric(site,metric_id)
    if str(meta.get("year"))!="2023" or str(meta.get("unit"))!="decimal":
        raise RuntimeError(f"{metric_id}: contratto inatteso anno={meta.get('year')} unità={meta.get('unit')}")
    if not finite(spec.get("tuscany")):
        raise RuntimeError(f"{metric_id}: benchmark Toscana non numerico")
    meta["benchmark"]={
        "year":2023,
        "tuscany":spec["tuscany"],
        "italy":None,
        "source":"Istat — A misura di Comune · Famiglie",
        "url":snap["sourceUrl"],
        "sourceSnapshot":FAMILIES_REF,
        "note":spec["note"],
    }
    return 1

def apply_labour(site):
    snap=load(LABOUR_SNAP); specs=snap.get("benchmarks")
    if not isinstance(specs,dict): raise RuntimeError("Snapshot Lavoro senza benchmarks")
    updated=0
    for metric_id,spec in sorted(specs.items()):
        if not isinstance(spec,dict): raise RuntimeError(f"{metric_id}: benchmark Lavoro non-oggetto")
        _,meta=metric(site,metric_id)
        if str(meta.get("year"))!="2023" or str(meta.get("unit"))!=str(spec.get("unit")):
            raise RuntimeError(
                f"{metric_id}: contratto inatteso anno={meta.get('year')} unità={meta.get('unit')} "
                f"(snapshot={spec.get('unit')})"
            )
        if not finite(spec.get("tuscany")):
            raise RuntimeError(f"{metric_id}: benchmark Toscana non numerico")
        italy=spec.get("italy")
        if italy is not None and not finite(italy):
            raise RuntimeError(f"{metric_id}: benchmark Italia non numerico")
        meta["benchmark"]={
            "year":2023,
            "tuscany":spec["tuscany"],
            "italy":italy,
            "source":"Istat — A misura di Comune · Lavoro",
            "url":snap["sourceUrl"],
            "sourceSnapshot":LABOUR_REF,
            "note":snap["note"],
        }
        updated+=1
    return updated

def main():
    site=load(SITE)
    families=apply_families(site)
    labour=apply_labour(site)
    SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "A3 benchmark Istat A misura di Comune: "
        f"{families} Famiglie + {labour} Lavoro materializzati nel contratto pubblico."
    )

if __name__=="__main__":
    main()
