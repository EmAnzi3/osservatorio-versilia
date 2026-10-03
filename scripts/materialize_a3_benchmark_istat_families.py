#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
SNAP=ROOT/"data"/"source-snapshots"/"a3-istat-famiglie-benchmark-2023.json"
SNAP_REF="data/source-snapshots/a3-istat-famiglie-benchmark-2023.json"

def load(path):
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"JSON non-oggetto: {path}")
    return value

def main():
    site=load(SITE); snap=load(SNAP); spec=snap["benchmark"]
    metric=(site.get("metrics") or {}).get(spec["metricId"])
    if not isinstance(metric,dict): raise RuntimeError("householdSize: metrica mancante")
    meta=metric.get("meta")
    if not isinstance(meta,dict): raise RuntimeError("householdSize: meta mancante")
    if str(meta.get("year"))!="2023" or str(meta.get("unit"))!="decimal":
        raise RuntimeError(f"householdSize: contratto inatteso anno={meta.get('year')} unità={meta.get('unit')}")
    meta["benchmark"]={
        "year":2023,
        "tuscany":spec["tuscany"],
        "italy":None,
        "source":"Istat — A misura di Comune · Famiglie",
        "url":snap["sourceUrl"],
        "sourceSnapshot":SNAP_REF,
        "note":spec["note"],
    }
    SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("A3 benchmark Famiglie: householdSize Toscana 2023 materializzato; Italia non pubblicata nella stessa tavola.")

if __name__=="__main__":
    main()
