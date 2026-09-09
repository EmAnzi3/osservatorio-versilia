#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from urllib.parse import urlsplit

import opportunity_daily_refresh_stable as stable


def _test_recent_success_gives_family_grace() -> None:
    original_load = stable.h4.core._load
    original_previous = stable._PREVIOUS_HEALTH
    original_date = stable._RUN_DATE
    try:
        stable.h4.core._load = lambda _path: {
            "requiredFamilies": [{"id": "maritime-coastal", "sourceIds": ["pcm-mare"]}]
        }
        stable._PREVIOUS_HEALTH = {
            "pcm-mare": {
                "lastSuccessfulFetch": "2026-09-04",
                "consecutiveFailures": 0,
                "effectiveStatus": "ok",
            }
        }
        stable._RUN_DATE = date(2026, 9, 5)
        result = {
            "sourceCoverage": {"rows": [{"source_id": "pcm-mare", "runtimeStatus": "error"}]},
            "coverageAudit": {},
        }
        uncovered = stable._runtime_uncovered_families_stable(result)
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date

    assert uncovered == [], uncovered
    grace = result["coverageAudit"]["runtimeGraceFamilies"]
    assert grace and grace[0]["familyId"] == "maritime-coastal", grace
    assert grace[0]["sources"][0]["graceReason"] == "recent_success", grace


def _test_legacy_error_gets_bootstrap_failure_window() -> None:
    original_previous = stable._PREVIOUS_HEALTH
    try:
        snapshot = {
            "referenceDate": "2026-09-04",
            "sourceCoverage": {
                "rows": [{"source_id": "legacy-error", "runtimeStatus": "error"}]
            },
        }
        stable._PREVIOUS_HEALTH = stable._seed_previous_health(snapshot)
        state = stable._health_state("legacy-error", "error", date(2026, 9, 5))
    finally:
        stable._PREVIOUS_HEALTH = original_previous

    assert state["lastSuccessfulFetch"] is None, state
    assert state["consecutiveFailures"] == 2, state
    assert state["effectiveStatus"] == "grace", state
    assert state["graceReason"] == "consecutive_failure_window", state


def _test_expired_grace_blocks_family() -> None:
    original_load = stable.h4.core._load
    original_previous = stable._PREVIOUS_HEALTH
    original_date = stable._RUN_DATE
    try:
        stable.h4.core._load = lambda _path: {
            "requiredFamilies": [{"id": "maritime-coastal", "sourceIds": ["pcm-mare"]}]
        }
        stable._PREVIOUS_HEALTH = {
            "pcm-mare": {
                "lastSuccessfulFetch": "2026-09-02",
                "consecutiveFailures": 2,
                "effectiveStatus": "grace",
            }
        }
        stable._RUN_DATE = date(2026, 9, 5)
        result = {
            "sourceCoverage": {"rows": [{"source_id": "pcm-mare", "runtimeStatus": "error"}]},
            "coverageAudit": {},
        }
        uncovered = stable._runtime_uncovered_families_stable(result)
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date

    assert uncovered == ["maritime-coastal"], uncovered
    assert result["coverageAudit"]["runtimeGraceFamilies"] == []


def _test_success_resets_failure_counter() -> None:
    original_previous = stable._PREVIOUS_HEALTH
    try:
        stable._PREVIOUS_HEALTH = {
            "source": {
                "lastSuccessfulFetch": "2026-09-01",
                "consecutiveFailures": 4,
                "effectiveStatus": "error",
            }
        }
        state = stable._health_state("source", "ok", date(2026, 9, 5))
    finally:
        stable._PREVIOUS_HEALTH = original_previous

    assert state["lastSuccessfulFetch"] == "2026-09-05", state
    assert state["consecutiveFailures"] == 0, state
    assert state["effectiveStatus"] == "ok", state
    assert state["graceUsed"] is False


def _test_pre_h5_snapshot_seeds_health() -> None:
    snapshot = {
        "referenceDate": "2026-09-04",
        "sourceCoverage": {
            "rows": [
                {"source_id": "healthy", "runtimeStatus": "ok"},
                {"source_id": "broken", "runtimeStatus": "error"},
            ]
        },
    }
    seeded = stable._seed_previous_health(snapshot)
    assert seeded["healthy"]["lastSuccessfulFetch"] == "2026-09-04", seeded
    assert seeded["healthy"]["consecutiveFailures"] == 0, seeded
    assert seeded["broken"]["lastSuccessfulFetch"] is None, seeded
    assert seeded["broken"]["consecutiveFailures"] == 1, seeded


def _test_critical_sources_use_independent_official_hosts() -> None:
    config, _ = stable.h4._compose_runtime_hardened()
    discovery_by_id = {
        str(source.get("id") or ""): source
        for source in config.get("discoverySources") or []
    }
    mare_urls = list(discovery_by_id["pcm-politiche-mare"]["urls"])
    scu_urls = list(discovery_by_id["pcm-politiche-giovanili-scu"]["urls"])

    mare_hosts = {urlsplit(url).hostname for url in mare_urls}
    scu_hosts = {urlsplit(url).hostname for url in scu_urls}
    assert len(mare_urls) == 2 and len(mare_hosts) == 2, mare_urls
    assert len(scu_urls) == 2 and len(scu_hosts) == 2, scu_urls
    assert "www.dipartimentopolitichemare.gov.it" in mare_hosts, mare_hosts
    assert "www.gazzettaufficiale.it" in mare_hosts, mare_hosts
    assert "www.politichegiovanili.gov.it" in scu_hosts, scu_hosts
    assert "www.scelgoilserviziocivile.gov.it" in scu_hosts, scu_hosts
    assert mare_hosts.isdisjoint(scu_hosts), (mare_hosts, scu_hosts)


def _test_secondary_endpoint_keeps_critical_families_covered() -> None:
    discovery = stable.h4.discovery
    config, _ = stable.h4._compose_runtime_hardened()
    critical_ids = {"pcm-politiche-mare", "pcm-politiche-giovanili-scu"}
    critical_sources = [
        source for source in config.get("discoverySources") or []
        if str(source.get("id") or "") in critical_ids
    ]
    assert {str(source.get("id") or "") for source in critical_sources} == critical_ids

    primary_urls = {str(source.get("urls")[0]) for source in critical_sources}
    original_fetch = discovery.fetch_with_diagnostics
    try:
        def fake_fetch(url: str, timeout: int = 30, attempts: int = 2):
            if url in primary_urls:
                diagnostics = {
                    "status": "error",
                    "transport": "failed",
                    "fallbackUsed": True,
                    "proxyUsed": True,
                    "initialFailureClass": "timeout_client",
                    "browserFailureClass": "timeout_client",
                    "failureClass": "timeout_client",
                    "resolvedUrl": None,
                    "redirected": False,
                    "errors": ["primary endpoint simulated timeout"],
                }
                raise discovery.DiscoveryFetchError("primary endpoint simulated timeout", diagnostics)
            return (
                "<html><body><h3>Bando istituzionale</h3><p>Avviso pubblico per enti e comuni.</p></body></html>",
                {
                    "status": "ok",
                    "transport": "http_browser",
                    "httpAttempts": 2,
                    "fallbackUsed": False,
                    "proxyUsed": False,
                    "initialFailureClass": None,
                    "browserFailureClass": None,
                    "failureClass": None,
                    "resolvedUrl": url,
                    "redirected": False,
                    "errors": [],
                },
            )

        discovery.fetch_with_diagnostics = fake_fetch
        _, states = discovery.probe_discovery_sources(
            stable.h4.radar_module,
            {"discoverySources": critical_sources},
        )
    finally:
        discovery.fetch_with_diagnostics = original_fetch

    by_id = {str(row.get("sourceId") or ""): row for row in states}
    for source_id in critical_ids:
        state = by_id[source_id]
        assert state["status"] == "degraded", state
        assert state["endpointCount"] == 2, state
        assert state["endpointOk"] == 1, state

    result = {
        "sourceCoverage": {
            "rows": [
                {"source_id": source_id, "runtimeStatus": "degraded"}
                for source_id in sorted(critical_ids)
            ]
        }
    }
    uncovered = stable.h4._runtime_uncovered_families(result)
    assert "maritime-coastal" not in uncovered, uncovered
    assert "youth-civic-service" not in uncovered, uncovered


def main() -> int:
    _test_recent_success_gives_family_grace()
    _test_legacy_error_gets_bootstrap_failure_window()
    _test_expired_grace_blocks_family()
    _test_success_resets_failure_counter()
    _test_pre_h5_snapshot_seeds_health()
    _test_critical_sources_use_independent_official_hosts()
    _test_secondary_endpoint_keeps_critical_families_covered()
    print("Salute persistente fonti Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
