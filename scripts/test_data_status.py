#!/usr/bin/env python3
from __future__ import annotations

from data_status import build_metric_statuses, exact_next_release


def fixture():
    data = {
        "metrics": {
            "alpha": {
                "meta": {"key": "alpha", "theme": "demografia", "label": "Alpha", "year": "2024", "source": "Fonte"},
                "sourceUrl": "https://example.test/data",
                "rows": [],
            },
            "climate": {
                "meta": {"key": "climate", "theme": "ambiente", "label": "Clima", "year": "2025", "source": "Fonte clima"},
                "sourceUrl": "https://example.test/climate",
                "dataStorage": {"type": "external-climate"},
                "rows": [],
            },
        }
    }
    registry = {
        "defaults": {"monitorMode": "availability", "frequencyLabel": "Annuale", "expectedRelease": "Nel corso dell'anno"},
        "sourceProfiles": {
            "test": {"publisher": "Fonte", "frequency": "annual", "frequencyLabel": "Annuale", "expectedRelease": "Nel corso dell'anno"},
            "climate": {"publisher": "Clima", "frequency": "annual", "frequencyLabel": "Annuale", "expectedRelease": "Dopo l'anno completo"},
        },
        "sourceProfileByUrl": {
            "https://example.test/data": "test",
            "https://example.test/climate": "climate",
        },
        "metricOverrides": {},
    }
    state = {
        "schemaVersion": 2,
        "checkedAt": "2026-08-17T20:00:00+00:00",
        "mode": "live",
        "sources": {
            "https://example.test/data": {"ok": True, "metrics": ["alpha"]},
            "https://example.test/climate": {"ok": True, "metrics": ["climate"]},
        },
        "metrics": {},
    }
    return data, registry, state


def main():
    data, registry, state = fixture()
    statuses = build_metric_statuses(data, registry, state)
    assert statuses["alpha"]["status"] == "verification_required"

    state["metrics"]["alpha"] = {"observedLatestPeriod": "2024"}
    assert build_metric_statuses(data, registry, state)["alpha"]["status"] == "current"

    state["metrics"]["alpha"] = {"observedLatestPeriod": "2025"}
    assert build_metric_statuses(data, registry, state)["alpha"]["status"] == "new_release_to_review"

    state["sources"]["https://example.test/data"]["ok"] = False
    assert build_metric_statuses(data, registry, state)["alpha"]["status"] == "source_unavailable"

    state["metrics"]["climate"] = {"observedLatestPeriod": "2026 YTD"}
    climate = build_metric_statuses(data, registry, state)["climate"]
    assert climate["observedLatestPeriod"] is None
    assert climate["status"] == "verification_required"
    assert climate["climateCompleteYearsOnly"] is True

    policy = {"frequency": "annual", "expectedRelease": "gennaio"}
    assert exact_next_release(policy) is None
    policy["nextExpectedRelease"] = {"value": "2027-01", "basis": "guess"}
    assert exact_next_release(policy) is None
    policy["nextExpectedRelease"] = {
        "value": "2027-01", "precision": "month", "basis": "official_calendar", "evidenceUrl": "https://example.test/calendar"
    }
    assert exact_next_release(policy)["value"] == "2027-01"
    print("Data status model tests passed.")


if __name__ == "__main__":
    main()
