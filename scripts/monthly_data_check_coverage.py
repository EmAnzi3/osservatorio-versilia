#!/usr/bin/env python3
"""Estensione del monitor che valida coperture dichiarate 6/7 o 7/7."""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import monthly_data_check as base  # noqa: E402

ORIGINAL_VALIDATE = base.validate_dataset
COVERAGE_RE = re.compile(r"^(\d+)\s*/\s*(\d+)$")


def validate_dataset(data: dict[str, Any], registry: dict[str, Any]):
    prepared = copy.deepcopy(data)
    findings = []
    expected_total = len(registry.get("expectedTowns", []))

    metrics = prepared.get("metrics")
    if isinstance(metrics, dict):
        for metric_key, metric in metrics.items():
            if not isinstance(metric, dict):
                continue
            rows = metric.get("rows")
            method = metric.get("method")
            if not isinstance(rows, list) or not isinstance(method, dict):
                continue

            coverage_text = str(method.get("coverage", "")).strip()
            match = COVERAGE_RE.fullmatch(coverage_text)
            if not match:
                continue
            declared_available, declared_total = map(int, match.groups())
            if expected_total and declared_total != expected_total:
                findings.append(
                    base.finding(
                        "error",
                        "coverage_denominator",
                        f"Copertura dichiarata {coverage_text}, ma i Comuni attesi sono {expected_total}.",
                        metric_key,
                    )
                )

            missing_rows = [
                row for row in rows
                if isinstance(row, dict) and row.get("value") is None
            ]
            available = len([
                row for row in rows
                if isinstance(row, dict) and row.get("value") is not None
            ])
            if available != declared_available:
                findings.append(
                    base.finding(
                        "error",
                        "coverage_value_mismatch",
                        f"Copertura dichiarata {coverage_text}, ma i valori disponibili sono {available}/{declared_total}.",
                        metric_key,
                    )
                )

            for row in missing_rows:
                if row.get("formatted") != "n.d.":
                    findings.append(
                        base.finding(
                            "error",
                            "missing_value_label",
                            f"Il valore mancante per {row.get('town', row.get('code', '?'))} deve essere mostrato come n.d.",
                            metric_key,
                        )
                    )
                # Lo zero è usato soltanto nella copia temporanea di validazione
                # richiesta dal controllore base e non viene mai scritto nei dati.
                row["value"] = 0

    base_findings, source_map, stats = ORIGINAL_VALIDATE(prepared, registry)
    return findings + base_findings, source_map, stats


def main(argv: list[str] | None = None) -> int:
    base.validate_dataset = validate_dataset
    if argv is None:
        return base.main()

    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], *argv]
        return base.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
