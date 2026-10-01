#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data"/"site-data.json"
SNAP=ROOT/"data"/"source-snapshots"/"a3-regione-toscana-indicators-benchmark-2024.json"
REF="data/source-snapshots/a3-regione-toscana-indicators-benchmark-2024.json"
SOURCE_URL="https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali"
TARGETS={
    "youthOtherStatus":("2024","percent"),
    "foreignBornSoleProprietorShare":("2024","percent"),
    "emsResponseTimeP75":("2024","minutes"),
    "disability064Per1000":("2024","per1000"),
    "municipalOnlineServicesAdvanced":("2022","percent"),
    "innovationBusinessShare":("2024","percent"),
    "organicAgriculturalAreaShare":("2024","percent"),
}

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"JSON non-oggetto: {path}")
    return value

def close(a:Any,b:Any,label:str,tol:float=1e-8)->None:
    av=float(a); bv=float(b)
    if not math.isfinite(av) or not math.isfinite(bv) or not math.isclose(av,bv,rel_tol=0.0,abs_tol=tol):
        raise RuntimeError(f"{label}: {a} != {b}")

def main()->None:
    site=load(SITE); snap=load(SNAP)
    gate=snap.get("qualityGate") or {}
    if gate.get("status")!="PASS" or gate.get("municipalReconciliation")!="7 metrics × 7/7 towns PASS":
        raise RuntimeError("Toscana indicators benchmark senza quality gate PASS")
    metrics=site.get("metrics") or {}
    benchmarks=snap.get("benchmarks") or {}
    public_rows=snap.get("publicRows") or {}
    if set(benchmarks)!=set(TARGETS) or set(public_rows)!=set(TARGETS):
        raise RuntimeError("Toscana indicators snapshot non 7/7 metriche")

    updated=0
    for metric_id,(year,unit) in TARGETS.items():
        metric=metrics.get(metric_id)
        if not isinstance(metric,dict): raise RuntimeError(f"{metric_id}: metrica pubblica mancante")
        meta=metric.get("meta") or {}
        if str(meta.get("year"))!=year or str(meta.get("unit"))!=unit:
            raise RuntimeError(f"{metric_id}: contratto inatteso anno={meta.get('year')} unit={meta.get('unit')}")
        rows={str(r.get("town")):r for r in (metric.get("rows") or []) if isinstance(r,dict) and r.get("town")}
        expected=public_rows[metric_id]
        if set(rows)!=set(expected) or len(rows)!=7:
            raise RuntimeError(f"{metric_id}: perimetro pubblico non 7/7")
        for town,value in expected.items():
            close(rows[town].get("value"),value,f"{metric_id}/{town}",1e-8)

        spec=benchmarks[metric_id]
        if str(spec.get("year"))!=year or str(spec.get("unit"))!=unit:
            raise RuntimeError(f"{metric_id}: benchmark anno/unità non allineati")
        tus=float(spec["tuscany"])
        if not math.isfinite(tus): raise RuntimeError(f"{metric_id}: Toscana non numerica")
        if spec.get("italy") is not None:
            raise RuntimeError(f"{metric_id}: Italia deve restare n.d. per questa fonte")

        meta["benchmark"]={
            "year":year,
            "tuscany":tus,
            "italy":None,
            "source":"Regione Toscana — Indicatori comunali per le politiche locali",
            "url":metric.get("sourceUrl") or SOURCE_URL,
            "sourceSnapshot":REF,
            "note":"Confronto Toscana dalla riga regionale ufficiale della stessa tavola. Italia non disponibile nella stessa fonte con definizione omogenea."
        }
        updated+=1

    SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"A3 benchmark Indicatori Toscana: {updated} metriche materializzate; Toscana 7/7, Italia n.d., comuni 7/7 PASS.")

if __name__=="__main__":
    main()
