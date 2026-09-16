#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import test_agid_indicators as fixtures  # noqa: E402
import update_agid_indicators as base  # noqa: E402
import update_agid_indicators_resilient as resilient  # noqa: E402


def test_old_dataset() -> None:
    source = fixtures.base_data()
    asia, agcom = fixtures.source_maps()
    updated, _ = resilient.apply_policy(
        source, asia, agcom, "2026-08-07T00:00:00+00:00"
    )
    assert len(updated["metrics"]) == resilient.expected_metric_count(source) == 8


def test_rerun_with_managed_metrics_already_present() -> None:
    source = fixtures.base_data()
    asia, agcom = fixtures.source_maps()
    full_v17, _ = base.apply_updates(
        source, asia, agcom, "2026-08-07T00:00:00+00:00"
    )
    assert len(full_v17["metrics"]) == 10

    rerun, _ = resilient.apply_policy(
        copy.deepcopy(full_v17), asia, agcom, "2026-08-08T00:00:00+00:00"
    )
    assert resilient.expected_metric_count(full_v17) == 8
    assert len(rerun["metrics"]) == 8
    assert set(base.NEW_ECONOMY_KEYS) <= set(rerun["metrics"])
    assert set(resilient.PUBLISHED_BROADBAND_KEYS) <= set(rerun["metrics"])
    assert not (set(resilient.OMITTED_ABSOLUTE_KEYS) & set(rerun["metrics"]))

    # Una seconda esecuzione della stessa fase non deve cambiare il conteggio.
    second, _ = resilient.apply_policy(
        copy.deepcopy(rerun), asia, agcom, "2026-08-09T00:00:00+00:00"
    )
    assert resilient.expected_metric_count(rerun) == 8
    assert len(second["metrics"]) == 8


def test_refresh_preserves_catalog_contract() -> None:
    source = fixtures.base_data()
    asia, agcom = fixtures.source_maps()

    source["version"] = "v9.9.0"
    source["updated"] = "16 settembre 2026"
    source["themes"]["economia"]["description"] = "Descrizione economia corrente"
    source["themes"]["economia"]["featured"] = ["microUnits"]
    source["themes"]["economia"]["sections"][0]["description"] = (
        "Descrizione produzione corrente"
    )

    mobility = source["themes"]["mobilita"]
    mobility["label"] = "Mobilità corrente"
    mobility["question"] = "Domanda corrente"
    mobility["description"] = "Descrizione mobilità corrente"
    mobility["featured"] = ["roadInjuries"]
    mobility["metrics"] = [
        "evPoints",
        "ftthCoverageDesi",
        "ftthReachedHouseholds",
        "ftthUnreachedHouseholds",
        "ftthCoverage20m",
        "roadInjuries",
    ]
    mobility["sections"] = [
        {"key": "veicoli", "metrics": ["evPoints"]},
        {
            "key": "connettivita",
            "label": "Connettività digitale",
            "description": "Descrizione connettività corrente",
            "metrics": [
                "ftthCoverageDesi",
                "ftthReachedHouseholds",
                "ftthUnreachedHouseholds",
                "ftthCoverage20m",
            ],
        },
        {"key": "sicurezza", "metrics": ["roadInjuries"]},
    ]

    updated, snapshot = resilient.apply_policy(
        copy.deepcopy(source), asia, agcom, "2026-09-16T00:00:00+00:00"
    )

    assert updated["version"] == source["version"]
    assert updated["updated"] == source["updated"]
    assert updated["themes"]["economia"]["description"] == source["themes"]["economia"]["description"]
    assert updated["themes"]["economia"]["featured"] == source["themes"]["economia"]["featured"]
    assert updated["themes"]["economia"]["sections"][0]["description"] == source["themes"]["economia"]["sections"][0]["description"]
    assert updated["themes"]["mobilita"]["label"] == mobility["label"]
    assert updated["themes"]["mobilita"]["question"] == mobility["question"]
    assert updated["themes"]["mobilita"]["description"] == mobility["description"]
    assert updated["themes"]["mobilita"]["featured"] == mobility["featured"]
    assert [section["key"] for section in updated["themes"]["mobilita"]["sections"]] == [
        "veicoli",
        "connettivita",
        "sicurezza",
    ]
    assert updated["themes"]["mobilita"]["sections"][1]["metrics"] == resilient.PUBLISHED_BROADBAND_KEYS
    assert updated["themes"]["mobilita"]["metrics"] == [
        "evPoints",
        "ftthCoverageDesi",
        "ftthCoverage20m",
        "roadInjuries",
    ]
    assert snapshot["sources"]["agcom"]["url"] == resilient.AGCOM_PUBLIC_MAP_URL


if __name__ == "__main__":
    test_old_dataset()
    test_rerun_with_managed_metrics_already_present()
    test_refresh_preserves_catalog_contract()
    print("OK: aggiornamento ASIA/AGCOM idempotente e catalogo preservato")
