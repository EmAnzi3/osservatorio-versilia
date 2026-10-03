#!/usr/bin/env python3
"""Reuse the certified complete MEF 2024 panel for its taxable-income level."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from acquire_a3_benchmark_mef_istat_real_income_annual import verify_records

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/source-snapshots/a3-mef-real-income-benchmark-2024.json"
REFERENCE = str(PANEL.relative_to(ROOT))


def certified_panel():
    source = json.loads(PANEL.read_text())
    if source.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("MEF: prerequisite native panel is not certified")
    records = source["records"]["2024"]
    verify_records(records, 2024)
    native = source["sources"]["2024"]
    if native.get("actualTaxYear") != 2024 or native.get("amountHeader") != "Reddito imponibile - Ammontare in euro" or native.get("frequencyHeader") != "Reddito imponibile - Frequenza":
        raise RuntimeError("MEF: native taxable-income definition/year mismatch")
    return records, native


def records_hash(records):
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def aggregate(records, scope):
    selected = [r for r in records if scope == "italy" or r[1] == "09"]
    return {"amount": sum(r[2] for r in selected), "frequency": sum(r[3] for r in selected), "records": len(selected)}


def validate_snapshot(metric, snapshot):
    records, source = certified_panel()
    if snapshot.get("sourcePanel") != REFERENCE or snapshot.get("source") != source or snapshot.get("recordsSha256") != records_hash(records):
        raise RuntimeError("MEF: certified native panel lineage mismatch")
    meta = metric.get("meta", {})
    if meta.get("year") != "2024" or meta.get("unit") != "currency":
        raise RuntimeError("MEF: public taxable-income period/unit mismatch")
    rows = metric.get("rows", [])
    codes = {"046018", "046033", "046005", "046024", "046028", "046013", "046030"}
    if len(rows) != 7 or {r.get("code") for r in rows} != codes:
        raise RuntimeError("MEF: municipal perimeter mismatch")
    native = {r[0]: r for r in records}
    for row in rows:
        record = native[row["code"]]
        value = row.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not math.isclose(value, record[2] / record[3], rel_tol=0, abs_tol=.005000001):
            raise RuntimeError("MEF: public taxable-income amount/frequency reconciliation mismatch")
    benchmark = snapshot["benchmarks"]["income"]
    if benchmark.get("year") != "2024" or benchmark.get("unit") != "currency":
        raise RuntimeError("MEF: benchmark year/unit mismatch")
    for scope in ("tuscany", "italy"):
        expected = aggregate(records, scope)
        raw = snapshot["raw"][scope]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in raw.values()) or raw != expected:
            raise RuntimeError("MEF: aggregate native components mismatch")
        value = benchmark.get(scope)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not math.isclose(value, expected["amount"] / expected["frequency"], rel_tol=0, abs_tol=1e-9):
            raise RuntimeError("MEF: aggregate taxable-income ratio mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, source = certified_panel()
    raw = {scope: aggregate(records, scope) for scope in ("tuscany", "italy")}
    benchmark = {"year": "2024", "unit": "currency", "formula": "Reddito imponibile — Ammontare / Frequenza"}
    benchmark.update({scope: values["amount"] / values["frequency"] for scope, values in raw.items()})
    snapshot = {"schemaVersion": 1, "profileId": "mef-irpef-annual", "publisher": "MEF — Dipartimento delle Finanze",
                "status": "ACQUIRED_CANDIDATE", "sourceUrl": source["url"], "sourcePanel": REFERENCE,
                "source": source, "recordsSha256": records_hash(records), "raw": raw,
                "benchmarks": {"income": benchmark}, "qualityGate": {"status": "PASS", "errors": [],
                "candidateMetrics": ["income"], "publicSnapshotReconciliation": "7/7 at the public cent; complete 7897-record national panel and 273 Tuscany municipalities"},
                "scope": {"note": "Media imponibile ponderata sui dichiaranti con imponibile della stessa variabile MEF 2024. Italia include il record nazionale senza localizzazione esplicita; nessuna media delle medie comunali e nessun uso del reddito complessivo."}}
    metric = json.loads((ROOT / "data/site-data.json").read_text())["metrics"]["income"]
    validate_snapshot(metric, snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "ACQUIRED_CANDIDATE", "municipalReconciliation": "7/7", "benchmarks": benchmark}))


if __name__ == "__main__":
    main()
