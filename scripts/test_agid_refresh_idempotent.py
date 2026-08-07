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


if __name__ == "__main__":
    test_old_dataset()
    test_rerun_with_managed_metrics_already_present()
    print("OK: aggiornamento ASIA/AGCOM idempotente")
