#!/usr/bin/env python3
"""Ripristina gli indicatori AGCOM assoluti con copertura dichiarata 6/7.

Va eseguito dopo ``update_agid_indicators_resilient.py``. Usa esclusivamente i
valori grezzi conservati nello snapshot: il Comune privo del conteggio
``famiglie_ftth`` resta a ``n.d.`` e gli aggregati sono totali parziali.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_agid_indicators as base  # noqa: E402

MAX_MISSING_TOWNS = 1
FULL_BROADBAND_KEYS = [
    "ftthCoverageDesi",
    "ftthReachedHouseholds",
    "ftthUnreachedHouseholds",
    "ftthCoverage20m",
]
PARTIAL_KEYS = ["ftthReachedHouseholds", "ftthUnreachedHouseholds"]


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise base.DataError(f"{label}: valore numerico mancante o non valido")
    number = float(value)
    if not math.isfinite(number):
        raise base.DataError(f"{label}: valore non finito")
    return number


def _missing_row(town: dict[str, str]) -> dict[str, Any]:
    return {
        **town,
        "value": None,
        "formatted": "n.d.",
        "series": None,
        "normalized": None,
        "benchmarkValue": None,
    }


def _partial_aggregate(
    rows: list[dict[str, Any]], missing_names: list[str]
) -> dict[str, Any]:
    available_rows = [row for row in rows if row.get("value") is not None]
    available = len(available_rows)
    total = len(rows)
    return {
        "value": sum(float(row["value"]) for row in available_rows),
        "label": f"Totale parziale Versilia ({available}/{total})",
        "note": (
            f"Somma dei valori ufficiali disponibili per {available} Comuni; "
            f"escluso {', '.join(missing_names)}, per cui il dato AGCOM non è disponibile."
        ),
    }


def _metric_rows(
    towns: list[dict[str, str]], snapshot_by_code: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    reached_rows: list[dict[str, Any]] = []
    unreached_rows: list[dict[str, Any]] = []
    missing_codes: list[str] = []
    missing_names: list[str] = []

    for town in towns:
        code = town["code"]
        source = snapshot_by_code.get(code)
        if not source:
            raise base.DataError(f"Snapshot AGCOM assente per il Comune {code}")
        resident = _number(source.get("residentHouseholds"), f"AGCOM {code} famiglie residenti")
        reached_raw = source.get("ftthHouseholds")
        if reached_raw is None:
            missing_codes.append(code)
            missing_names.append(town["town"])
            reached_rows.append(_missing_row(town))
            unreached_rows.append(_missing_row(town))
            continue

        reached = _number(reached_raw, f"AGCOM {code} famiglie FTTH")
        if resident < 0 or reached < 0 or reached > resident:
            raise base.DataError(f"AGCOM {code}: conteggio famiglie FTTH incoerente")
        unreached = resident - reached
        reached_rows.append(base._row(town, reached, base._format_int(reached)))
        unreached_rows.append(base._row(town, unreached, base._format_int(unreached)))

    if len(missing_codes) > MAX_MISSING_TOWNS:
        raise base.DataError(
            f"Conteggio famiglie FTTH mancante per {len(missing_codes)} Comuni; "
            "la policy consente al massimo una copertura 6/7."
        )
    return reached_rows, unreached_rows, missing_codes, missing_names


def apply_partial_coverage(
    data: dict[str, Any], snapshot: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    towns = base._town_rows(data)
    snapshot_by_code = {
        str(item.get("code")): item.get("agcom", {})
        for item in snapshot.get("towns", [])
        if isinstance(item, dict)
    }
    reached_rows, unreached_rows, missing_codes, missing_names = _metric_rows(
        towns, snapshot_by_code
    )
    available = 7 - len(missing_codes)
    coverage = f"{available}/7"
    missing_text = ", ".join(missing_names) if missing_names else "nessuno"

    reached = base._metric(
        "ftthReachedHouseholds",
        "mobilita",
        "Famiglie raggiunte da FTTH",
        "Famiglie raggiunte da FTTH",
        "Numero di famiglie residenti considerate raggiunte dalla rete FTTH secondo la metrica DESI.",
        "number",
        "31 dicembre 2025",
        "AGCOM — Broadband Map",
        base.AGCOM_SOURCE_URL,
        reached_rows,
        _partial_aggregate(reached_rows, missing_names) if missing_names else {
            "value": sum(float(row["value"]) for row in reached_rows),
            "label": "Totale Versilia",
            "note": "Somma delle famiglie raggiunte nei sette Comuni.",
        },
        "Dato ufficiale",
        "Famiglie FTTH pubblicate da AGCOM nella reportistica comunale Broadband Map.",
        (
            "Il numero deriva dalla modellazione territoriale AGCOM e non coincide con gli accessi o i contratti attivi. "
            f"Dato non disponibile per {missing_text}; nessuna stima effettuata."
            if missing_names else
            "Il numero deriva dalla modellazione territoriale AGCOM e non coincide con gli accessi o i contratti attivi."
        ),
    )
    reached["method"]["coverage"] = coverage

    unreached = base._metric(
        "ftthUnreachedHouseholds",
        "mobilita",
        "Famiglie non raggiunte da FTTH",
        "Famiglie non raggiunte",
        "Differenza tra famiglie residenti e famiglie raggiunte da FTTH secondo la metrica DESI.",
        "number",
        "31 dicembre 2025",
        "Elaborazione Osservatorio su dati AGCOM Broadband Map",
        base.AGCOM_SOURCE_URL,
        unreached_rows,
        _partial_aggregate(unreached_rows, missing_names) if missing_names else {
            "value": sum(float(row["value"]) for row in unreached_rows),
            "label": "Totale Versilia",
            "note": "Somma delle famiglie non raggiunte nei sette Comuni.",
        },
        "Elaborazione Osservatorio su dati ufficiali",
        "famiglie residenti AGCOM − famiglie raggiunte da FTTH DESI",
        (
            "È il complemento aritmetico della copertura dichiarata AGCOM, non un censimento dei civici privi di servizio attivabile. "
            f"Dato non calcolabile per {missing_text}; nessuna stima effettuata."
            if missing_names else
            "È il complemento aritmetico della copertura dichiarata AGCOM, non un censimento dei civici privi di servizio attivabile."
        ),
    )
    unreached["method"]["coverage"] = coverage

    data["metrics"]["ftthReachedHouseholds"] = reached
    data["metrics"]["ftthUnreachedHouseholds"] = unreached

    mobility = data["themes"]["mobilita"]
    mobility["metrics"] = base._insert_after(
        mobility["metrics"],
        "ftthCoverageDesi",
        ["ftthReachedHouseholds", "ftthUnreachedHouseholds"],
    )
    for section in mobility.get("sections", []):
        if section.get("key") == "connettivita":
            section["metrics"] = FULL_BROADBAND_KEYS
            section["description"] = (
                "Copertura della rete fissa FTTH: percentuali comunali 7/7 e "
                "conteggi assoluti con copertura dichiarata, senza stime dei valori mancanti."
            )

    snapshot.setdefault("formulas", {})["ftthUnreachedHouseholds"] = (
        "famiglie residenti - famiglie FTTH DESI"
    )
    snapshot["coveragePolicy"] = {
        "standardCoverage": "7/7",
        "minimumAcceptedCoverage": "6/7",
        "maximumMissingTownsPerMetric": MAX_MISSING_TOWNS,
        "publishedBroadbandMetrics": FULL_BROADBAND_KEYS,
        "partialMetrics": {
            key: {
                "coverage": coverage,
                "missingTownCodes": missing_codes,
                "missingTowns": missing_names,
            }
            for key in PARTIAL_KEYS
        },
        "note": (
            "Un indicatore può essere pubblicato con copertura 6/7 quando un solo Comune presenta un dato ufficiale mancante. "
            "Il valore resta n.d.; nessuna stima o ricostruzione viene effettuata."
        ),
    }
    return data, snapshot


def write_report(data: dict[str, Any], path: Path) -> None:
    keys = [
        "localEmployees",
        "employeesPerLocalUnit",
        "localUnitsChange",
        "localEmployeesChange",
        *FULL_BROADBAND_KEYS,
    ]
    lines = ["# Output nuovi indicatori", ""]
    for key in keys:
        metric = data["metrics"][key]
        meta = metric["meta"]
        lines.extend([
            f"## {meta['label']}",
            "",
            f"- **Anno:** {meta['year']}",
            f"- **Copertura:** {metric['method']['coverage']}",
            f"- **Aggregato:** {metric['aggregate']['label']} — {base._format_decimal(metric['aggregate']['value'], 2)}",
            "",
            "| Comune | Valore |",
            "|---|---:|",
        ])
        for row in metric["rows"]:
            value = "n.d." if row.get("value") is None else row.get("formatted") or str(row["value"])
            lines.append(f"| {row['town']} | {value} |")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(data: dict[str, Any], path: Path) -> None:
    keys = [
        "localEmployees",
        "employeesPerLocalUnit",
        "localUnitsChange",
        "localEmployeesChange",
        *FULL_BROADBAND_KEYS,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["indicatore", "comune", "codice_istat", "valore", "visualizzazione", "anno", "copertura"])
        for key in keys:
            metric = data["metrics"][key]
            for row in metric["rows"]:
                writer.writerow([
                    metric["meta"]["label"],
                    row["town"],
                    row["code"],
                    "" if row.get("value") is None else row["value"],
                    "n.d." if row.get("value") is None else row.get("formatted", ""),
                    metric["meta"]["year"],
                    metric["method"]["coverage"],
                ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-data", type=Path, default=base.SITE_DATA)
    parser.add_argument("--snapshot", type=Path, default=base.SNAPSHOT)
    parser.add_argument(
        "--report-md",
        type=Path,
        default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "indicatori.md",
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        default=base.ROOT / "reports" / "previews" / "imprese-banda-larga" / "indicatori.csv",
    )
    args = parser.parse_args(argv)

    data = base._json_load(args.site_data)
    snapshot = base._json_load(args.snapshot)
    previous_count = len(data["metrics"])
    updated, updated_snapshot = apply_partial_coverage(data, snapshot)
    expected_count = previous_count + 2
    if len(updated["metrics"]) != expected_count:
        raise base.DataError(
            f"Conteggio indicatori inatteso: {len(updated['metrics'])}; previsto {expected_count}"
        )

    base._json_write(args.site_data, updated)
    base._json_write(args.snapshot, updated_snapshot)
    write_report(updated, args.report_md)
    write_csv(updated, args.report_csv)
    if args.site_data.resolve() == base.SITE_DATA.resolve():
        base.update_count_files(expected_count, previous_count)

    print(json.dumps({
        "status": "ok",
        "metricCount": expected_count,
        "restoredMetrics": PARTIAL_KEYS,
        "coveragePolicy": updated_snapshot["coveragePolicy"],
        "reportMd": str(args.report_md),
        "reportCsv": str(args.report_csv),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.DataError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(2)
