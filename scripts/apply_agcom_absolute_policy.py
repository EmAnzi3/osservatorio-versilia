#!/usr/bin/env python3
"""Applica la soglia di pubblicabilità 6/7 ai conteggi assoluti AGCOM."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402
import restore_partial_agcom_metrics as restore  # noqa: E402

OUTPUT_KEYS = [
    "localEmployees",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
    "ftthCoverageDesi",
    "ftthReachedHouseholds",
    "ftthUnreachedHouseholds",
    "ftthCoverage20m",
]


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


def display_value(row):
    if row.get("value") is None:
        return "n.d."
    return row.get("formatted") or str(row.get("value"))


def write_outputs(data, snapshot, report_md: Path, report_csv: Path):
    keys = [key for key in OUTPUT_KEYS if key in data.get("metrics", {})]
    lines = ["# Output nuovi indicatori", "", f"**Indicatori presenti:** {len(keys)}/8", ""]
    omitted = [key for key in OUTPUT_KEYS if key not in data.get("metrics", {})]
    if omitted:
        lines.extend([
            "> I conteggi assoluti FTTH non sono inclusi perché non raggiungono la copertura minima 6/7 prevista dalla policy. Nessun valore è stato stimato.",
            "",
        ])
    for key in keys:
        metric = data["metrics"][key]
        meta = metric["meta"]
        aggregate = metric.get("aggregate") or {}
        lines.extend([
            f"## {meta['label']}",
            "",
            f"- **Anno:** {meta['year']}",
            f"- **Copertura:** {metric.get('method', {}).get('coverage', 'n.d.')}",
            f"- **Aggregato:** {aggregate.get('label', 'n.d.')} — {aggregate.get('value', 'n.d.')}",
            "",
            "| Comune | Valore |",
            "|---|---:|",
        ])
        for row in metric.get("rows", []):
            lines.append(f"| {row['town']} | {display_value(row)} |")
        lines.append("")
    coverage_note = snapshot.get("coveragePolicy", {}).get("note")
    if coverage_note:
        lines.extend(["## Policy di copertura", "", coverage_note, ""])
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report_csv.parent.mkdir(parents=True, exist_ok=True)
    with report_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["indicatore", "comune", "codice_istat", "valore", "visualizzazione", "anno", "copertura"])
        for key in keys:
            metric = data["metrics"][key]
            for row in metric.get("rows", []):
                writer.writerow([
                    metric["meta"]["label"], row["town"], row["code"],
                    "" if row.get("value") is None else row.get("value"),
                    display_value(row), metric["meta"]["year"],
                    metric.get("method", {}).get("coverage", "n.d."),
                ])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    parser.add_argument("--report-md", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "indicatori.md")
    parser.add_argument("--report-csv", type=Path, default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "indicatori.csv")
    args = parser.parse_args(argv)
    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    before = len(data.get("metrics", {}))
    data, snapshot, status, invalid = apply_policy(data, snapshot)
    base._json_write(args.site_data, data)
    base._json_write(args.snapshot, snapshot)
    after = len(data.get("metrics", {}))
    write_outputs(data, snapshot, args.report_md, args.report_csv)
    if args.site_data.resolve() == base.SITE_DATA.resolve() and after != before:
        base.update_count_files(after, before)
    print(json.dumps({"status": status, "invalidCodes": invalid, "metricCount": after,
                      "coveragePolicy": snapshot.get("coveragePolicy"),
                      "reportMd": str(args.report_md), "reportCsv": str(args.report_csv)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
