#!/usr/bin/env python3
"""Applica la soglia di pubblicabilità 6/7 ai conteggi assoluti AGCOM."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402
import restore_partial_agcom_metrics as restore  # noqa: E402


def apply_policy(data, snapshot):
    audit = snapshot.get("agcomAudit", {}) if isinstance(snapshot, dict) else {}
    invalid = set(audit.get("invalidAbsoluteTownCodes", []))
    for town in snapshot.get("towns", []):
        ag = town.get("agcom", {})
        if ag.get("ftthHouseholds") is None:
            invalid.add(str(town.get("code")))

    town_name = {str(t.get("code")): t.get("town") for t in snapshot.get("towns", [])}
    for town in snapshot.get("towns", []):
        code = str(town.get("code"))
        if code in invalid:
            town.setdefault("agcom", {})["ftthHouseholds"] = None

    if len(invalid) <= restore.MAX_MISSING_TOWNS:
        data, snapshot = restore.apply_partial_coverage(data, snapshot)
        status = "published_partial" if invalid else "published_full"
    else:
        for key in restore.PARTIAL_KEYS:
            data.get("metrics", {}).pop(key, None)
        mobility = data.get("themes", {}).get("mobilita", {})
        mobility["metrics"] = [key for key in mobility.get("metrics", []) if key not in restore.PARTIAL_KEYS]
        for section in mobility.get("sections", []):
            if section.get("key") == "connettivita":
                section["metrics"] = ["ftthCoverageDesi", "ftthCoverage20m"]
                section["description"] = (
                    "Copertura percentuale FTTH ufficiale. I conteggi assoluti sono sospesi quando "
                    "più di un Comune non supera i controlli di disponibilità/coerenza."
                )
        snapshot["coveragePolicy"] = {
            "standardCoverage": "7/7",
            "minimumAcceptedCoverage": "6/7",
            "maximumMissingTownsPerMetric": restore.MAX_MISSING_TOWNS,
            "publishedBroadbandMetrics": ["ftthCoverageDesi", "ftthCoverage20m"],
            "omittedBroadbandMetrics": restore.PARTIAL_KEYS,
            "invalidTownCodes": sorted(invalid),
            "invalidTowns": [town_name.get(code, code) for code in sorted(invalid)],
            "note": (
                "I conteggi assoluti richiedono almeno 6/7 Comuni validi. Con più di un Comune "
                "mancante o incoerente non vengono pubblicati e nessun valore viene stimato."
            ),
        }
        status = "omitted_below_6_of_7"
    return data, snapshot, status, sorted(invalid)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    args = parser.parse_args(argv)
    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    before = len(data.get("metrics", {}))
    data, snapshot, status, invalid = apply_policy(data, snapshot)
    base._json_write(args.site_data, data)
    base._json_write(args.snapshot, snapshot)
    after = len(data.get("metrics", {}))
    if args.site_data.resolve() == base.SITE_DATA.resolve() and after != before:
        base.update_count_files(after, before)
    print(json.dumps({"status": status, "invalidCodes": invalid, "metricCount": after,
                      "coveragePolicy": snapshot.get("coveragePolicy")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
