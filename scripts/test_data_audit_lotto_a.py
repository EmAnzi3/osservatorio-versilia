#!/usr/bin/env python3
"""Guardrail del Lotto A: fonte prima, UI canonica sempre."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data" / "data-audit-lotto-a.json"
SITE_DATA_PATH = ROOT / "data" / "site-data.json"
TOOLKIT_PATH = ROOT / "assets" / "ux-history-core.js"

EXPECTED_TOWNS = {
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
}


def main() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    site = json.loads(SITE_DATA_PATH.read_text(encoding="utf-8"))
    toolkit = TOOLKIT_PATH.read_text(encoding="utf-8")

    assert audit["schemaVersion"] == 1
    assert audit["baseMainSha"] == "07dcb687aad0f024f582a4730f9330a64dcdaada"
    assert audit["catalogMetricCountAtAuditStart"] == 127

    contract = audit["uiContract"]
    assert contract["historyToolkit"] == "OVUXHistory"
    assert contract["historyMarkup"] == "historicalChartMarkup"
    assert contract["comparisonMarkup"] == "comparisonBarsMarkup"
    assert contract["tooltipMarkup"] == "historyPointMarkup"
    assert contract["tooltipWiring"] == "wireHistoryTooltips"
    assert contract["valueFormatter"] == "formatValue"
    assert contract["allowCustomHistoricalTooltip"] is False
    assert contract["allowCustomComparisonRendererWhenCanonicalExists"] is False
    assert contract["townOrder"] == "alphabetical_it"
    assert contract["rankingAllowed"] is False

    # Le funzioni dichiarate dal contratto devono esistere davvero nel toolkit del sito.
    for function_name in (
        "formatValue",
        "historyPointMarkup",
        "wireHistoryTooltips",
        "historicalChartMarkup",
        "comparisonBarsMarkup",
    ):
        assert f"function {function_name}" in toolkit, f"Funzione canonica assente: {function_name}"

    # Durante l'audit non si modifica ancora il catalogo pubblico.
    if audit["status"] == "audit":
        assert len(site["metrics"]) == audit["catalogMetricCountAtAuditStart"], (
            "Il catalogo è cambiato prima del superamento del gate 7×N"
        )

    towns = {town["name"] for town in site["towns"]}
    assert towns == EXPECTED_TOWNS, (towns, EXPECTED_TOWNS)

    candidates = audit["candidates"]
    keys = [candidate["key"] for candidate in candidates]
    assert len(keys) == len(set(keys)), "Chiavi candidate duplicate"
    assert len(candidates) == 23, f"Lotto A inatteso: {len(candidates)} candidati"

    valid_statuses = {
        "go_source",
        "verify",
        "go_source_hold_structure",
        "verify_hold_structure",
        "no_go",
    }
    valid_kinds = {
        "indicator",
        "composite_indicator",
        "derived_indicator",
        "indicator_or_composite",
        "composite_or_derived_indicator",
        "detail_dataset",
    }
    for candidate in candidates:
        assert candidate["auditStatus"] in valid_statuses, candidate["key"]
        assert candidate["kind"] in valid_kinds, candidate["key"]
        if candidate.get("notApplicableTowns"):
            assert set(candidate["notApplicableTowns"]) <= EXPECTED_TOWNS
        if candidate.get("coverageExpected"):
            assert 1 <= int(candidate["coverageExpected"]) <= 7
        if candidate.get("coverageApplicable"):
            assert 1 <= int(candidate["coverageApplicable"]) <= 7

        ui = str(candidate.get("ui", ""))
        assert "custom" not in ui.lower(), f"UI custom non ammessa: {candidate['key']}"
        assert "tooltip" not in ui.lower(), (
            f"Il candidato non deve dichiarare un tooltip proprio: {candidate['key']}"
        )

    assert contract["missingValueStates"] == {
        "nd": "dato pertinente ma non disponibile",
        "na": "indicatore non applicabile al Comune",
    }

    print(
        "Lotto A audit OK: 23 candidati, catalogo ancora a 127, "
        "OVUXHistory/tooltip/formattazione canonici vincolati."
    )


if __name__ == "__main__":
    main()
