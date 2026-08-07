#!/usr/bin/env python3
"""Audit prudenziale dei conteggi comunali AGCOM Broadband Map.

La percentuale Copertura FTTH DESI è il campo indicato da AGCOM come riferimento
per l'analisi comparativa. I conteggi assoluti vengono considerati utilizzabili
solo se disponibili e internamente coerenti con quella percentuale.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

MAX_PERCENTAGE_GAP = 1.5
ABSOLUTE_KEYS = ["ftthReachedHouseholds", "ftthUnreachedHouseholds"]


def num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def audit(agcom: dict[str, dict[str, Any]], towns: list[dict[str, str]]) -> dict[str, Any]:
    rows = []
    reliable = 0
    for town in towns:
        code = town["code"]
        kpi = (agcom.get(code) or {}).get("kpi") or {}
        resident = num(kpi.get("famiglie_residenti"))
        reached = num(kpi.get("famiglie_ftth"))
        pct = num(kpi.get("copertura_ftth_desi_pct"))
        reasons: list[str] = []
        calculated = None
        gap = None
        if resident is None or resident <= 0:
            reasons.append("famiglie_residenti mancante o non valido")
        if reached is None:
            reasons.append("famiglie_ftth mancante")
        if pct is None:
            reasons.append("copertura_ftth_desi_pct mancante")
        if resident and reached is not None:
            if reached < 0 or reached > resident:
                reasons.append("famiglie_ftth fuori intervallo")
            calculated = reached / resident * 100.0
            if pct is not None:
                gap = abs(calculated - pct)
                if gap > MAX_PERCENTAGE_GAP:
                    reasons.append(
                        f"conteggio incoerente con Copertura FTTH DESI: {calculated:.2f}% vs {pct:.2f}%"
                    )
        ok = not reasons
        if ok:
            reliable += 1
        rows.append({
            "town": town["town"], "code": code, "residentHouseholds": resident,
            "ftthHouseholds": reached, "officialDesiPercent": pct,
            "calculatedPercent": calculated, "percentageGap": gap,
            "absoluteCountsReliable": ok, "reasons": reasons,
        })
    return {
        "schemaVersion": 1,
        "rule": f"conteggi presenti e scarto massimo {MAX_PERCENTAGE_GAP} punti dalla Copertura FTTH DESI",
        "absoluteCountsReliableCoverage": f"{reliable}/7",
        "absoluteCountsPublishable": reliable >= 6,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--report", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "audit-agcom.json")
    args = parser.parse_args(argv)

    data = base._json_load(args.site_data)
    towns = base._town_rows(data)
    codes = [town["code"] for town in towns]
    _asia, agcom, _provenance = base.load_source_shards(codes, args.source_dir)
    result = audit(agcom, towns)

    if not result["absoluteCountsPublishable"]:
        for key in ABSOLUTE_KEYS:
            data.get("metrics", {}).pop(key, None)
        mobility = data.get("themes", {}).get("mobilita", {})
        mobility["metrics"] = [key for key in mobility.get("metrics", []) if key not in ABSOLUTE_KEYS]
        for section in mobility.get("sections", []):
            if section.get("key") == "connettivita":
                section["metrics"] = ["ftthCoverageDesi", "ftthCoverage20m"]
                section["description"] = (
                    "Copertura comunale FTTH secondo le percentuali ufficiali AGCOM. "
                    "I conteggi assoluti sono esclusi quando non raggiungono la copertura minima affidabile 6/7."
                )
    for key in ("ftthCoverageDesi", "ftthCoverage20m"):
        metric = data.get("metrics", {}).get(key)
        if metric:
            caveat = metric["method"].get("caveat", "").rstrip()
            metric["method"]["caveat"] = (
                caveat + " AGCOM indica la colonna Copertura FTTH DESI come riferimento per i confronti comunali; "
                "i conteggi assoluti sono sottoposti a un controllo di coerenza separato."
            ).strip()

    data["broadbandAudit"] = result
    base._json_write(args.site_data, data)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
