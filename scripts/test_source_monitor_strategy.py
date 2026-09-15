#!/usr/bin/env python3
"""Regressione A2.4: strategia per fonte derivata e ultimo successo."""
from __future__ import annotations

import source_monitor_strategy as strategy


def fixtures():
    data = {
        "version": "v-test",
        "updated": "15 settembre 2026",
        "metrics": {
            "alpha": {"sourceUrl": "https://example.test/a.csv"},
            "fuelPrices": {"sourceUrl": "https://example.test/fuel.csv"},
        },
    }
    registry = {
        "defaults": {"monitorMode": "availability"},
        "sourceProfiles": {
            "annual": {
                "frequency": "annual",
                "frequencyLabel": "Annuale",
                "expectedRelease": "Ogni anno",
            },
            "daily": {
                "frequency": "daily",
                "frequencyLabel": "Giornaliera",
                "expectedRelease": "Ogni giorno",
            },
        },
        "sourceProfileByUrl": {
            "https://example.test/a.csv": "annual",
            "https://example.test/fuel.csv": "daily",
        },
        "metricOverrides": {},
        "sourceChangePolicies": {
            "https://example.test/a.csv": {
                "contentChange": "informational",
                "redirectChange": "substantial",
                "reason": "fixture",
            }
        },
    }
    source_map = {
        "https://example.test/a.csv": {
            "metrics": ["alpha"],
            "roles": ["primary"],
            "profileIds": ["annual"],
        },
        "https://example.test/fuel.csv": {
            "metrics": ["fuelPrices"],
            "roles": ["primary"],
            "profileIds": ["daily"],
        },
    }
    return data, registry, source_map


def test_live_success() -> None:
    data, registry, source_map = fixtures()
    previous = {
        "mode": "live",
        "checkedAt": "2026-09-01T00:00:00+00:00",
        "sources": {
            "https://example.test/a.csv": {"ok": True},
            "https://example.test/fuel.csv": {"ok": False},
        },
    }
    current = {
        "mode": "live",
        "depth": "light",
        "checkedAt": "2026-09-15T05:41:00+00:00",
        "sources": {
            "https://example.test/a.csv": {"ok": False, "status": 503},
            "https://example.test/fuel.csv": {"ok": True, "status": 200},
        },
    }
    payload = strategy.build_strategy_from_source_map(
        data, registry, current, previous, source_map
    )
    assert payload["summary"]["publicMetricCount"] == 2
    assert payload["summary"]["metricsWithStrategy"] == 2
    assert payload["summary"]["sourceCount"] == 2

    annual = payload["sources"]["https://example.test/a.csv"]
    assert annual["frequency"] == ["annual"]
    assert annual["lastCheck"]["lastResult"] == "unreachable"
    assert annual["lastCheck"]["lastSuccessfulCheck"] == "2026-09-01T00:00:00+00:00"
    assert annual["changePolicy"]["content"] == "informational"

    fuel = payload["sources"]["https://example.test/fuel.csv"]
    assert fuel["frequency"] == ["daily"]
    assert fuel["lastCheck"]["lastSuccessfulCheck"] == "2026-09-15T05:41:00+00:00"
    assert "semantic:mimit-fuel" in fuel["changeDetection"]


def test_offline_does_not_fake_success() -> None:
    data, registry, source_map = fixtures()
    previous = {
        "mode": "live",
        "checkedAt": "2026-09-01T00:00:00+00:00",
        "sources": {"https://example.test/a.csv": {"ok": True}},
    }
    current = {
        "mode": "offline",
        "depth": "light",
        "checkedAt": "2026-09-15T18:00:00+00:00",
        "sources": {
            "https://example.test/a.csv": {"ok": True, "status": 200},
            "https://example.test/fuel.csv": {"ok": True, "status": 200},
        },
    }
    payload = strategy.build_strategy_from_source_map(
        data, registry, current, previous, source_map
    )
    annual = payload["sources"]["https://example.test/a.csv"]
    fuel = payload["sources"]["https://example.test/fuel.csv"]
    assert annual["lastCheck"]["lastResult"] == "offline_validation"
    assert annual["lastCheck"]["lastSuccessfulCheck"] == "2026-09-01T00:00:00+00:00"
    assert fuel["lastCheck"]["lastSuccessfulCheck"] == ""


if __name__ == "__main__":
    test_live_success()
    test_offline_does_not_fake_success()
    print("Source monitor strategy regression passed.")
