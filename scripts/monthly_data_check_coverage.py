#!/usr/bin/env python3
"""Estensione del monitor che valida coperture dichiarate 6/7 o 7/7."""
from __future__ import annotations

import copy
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import monthly_data_check as base  # noqa: E402

ORIGINAL_VALIDATE = base.validate_dataset
ORIGINAL_CANONICAL_URL = base.canonical_url
ORIGINAL_COMPARE_STATES = base.compare_states
COVERAGE_RE = re.compile(r"^(\d+)\s*/\s*(\d+)$")

# Il portale del Dipartimento delle Finanze aggiunge a ogni accesso un parametro
# `t` variabile alla stessa pagina. Non rappresenta un cambio di fonte e non deve
# quindi generare una segnalazione mensile di redirect.
VOLATILE_REDIRECT_QUERY_PARAMS = {
    ("www1.finanze.gov.it", "/finanze/analisi_stat/public/index.php"): {"t"},
}


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    ignored = VOLATILE_REDIRECT_QUERY_PARAMS.get(
        (parsed.netloc.lower(), parsed.path or "/"),
        set(),
    )
    if ignored:
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = urllib.parse.urlencode(
            [(key, item) for key, item in query_pairs if key.lower() not in ignored]
        )
        value = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, filtered_query, parsed.fragment)
        )
    return ORIGINAL_CANONICAL_URL(value)


def compare_states(
    previous: dict[str, Any], current: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Normalizza anche la baseline precedente prima di confrontare i redirect."""
    prepared_previous = copy.deepcopy(previous)
    previous_sources = prepared_previous.get("sources")
    if isinstance(previous_sources, dict):
        for item in previous_sources.values():
            if isinstance(item, dict) and item.get("finalUrl"):
                item["finalUrl"] = canonical_url(str(item["finalUrl"]))

    prepared_current = copy.deepcopy(current)
    for item in prepared_current.values():
        if isinstance(item, dict) and item.get("finalUrl"):
            item["finalUrl"] = canonical_url(str(item["finalUrl"]))

    return ORIGINAL_COMPARE_STATES(prepared_previous, prepared_current)


def _prepare_missing_row_for_base_validation(row: dict[str, Any]) -> None:
    """Mantiene i null reali nei dati, neutralizzandoli solo nella copia di test.

    Il controllore base richiede valori numerici ovunque. Per una copertura
    esplicitamente parziale (es. 6/7) un Comune può invece avere `value: null` e
    valori null anche nella serie. Questi null sono informazione, non errori e
    non devono essere sostituiti nel dataset canonico.
    """
    row["value"] = 0
    series = row.get("series")
    if not isinstance(series, dict):
        return
    values = series.get("values")
    if isinstance(values, list):
        series["values"] = [0 if value is None else value for value in values]


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
                # `formatted` può essere assente, null o vuoto: in questi casi il
                # renderer canonico applica `n.d.` a partire da value=null. Se è
                # presente una stringa esplicita, deve invece essere `n.d.`.
                formatted = row.get("formatted")
                if formatted not in (None, "", "n.d."):
                    findings.append(
                        base.finding(
                            "error",
                            "missing_value_label",
                            f"Il valore mancante per {row.get('town', row.get('code', '?'))} deve essere mostrato come n.d.",
                            metric_key,
                        )
                    )
                _prepare_missing_row_for_base_validation(row)

    base_findings, source_map, stats = ORIGINAL_VALIDATE(prepared, registry)
    return findings + base_findings, source_map, stats


def main(argv: list[str] | None = None) -> int:
    base.canonical_url = canonical_url
    base.compare_states = compare_states
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
