#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
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
    original_path = stable.PUBLISHABILITY_DIAGNOSTIC_PATH
    original_base_build = stable._BASE_BUILD_AUDIT
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
        stable._BASE_BUILD_AUDIT = lambda _result: {
            "schemaVersion": "1.1",
            "summary": {},
            "sources": [{"sourceId": "pcm-mare", "runtimeStatus": "error", "endpoints": []}],
            "extraFetches": [],
        }
        with TemporaryDirectory() as tmp:
            stable.PUBLISHABILITY_DIAGNOSTIC_PATH = Path(tmp) / "publishability.json"
            result = {
                "sourceCoverage": {"rows": [{"source_id": "pcm-mare", "runtimeStatus": "error"}]},
                "coverageAudit": {},
            }
            uncovered = stable._runtime_uncovered_families_stable(result)
            assert stable.PUBLISHABILITY_DIAGNOSTIC_PATH.exists()
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date
        stable.PUBLISHABILITY_DIAGNOSTIC_PATH = original_path
        stable._BASE_BUILD_AUDIT = original_base_build

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


def _test_blocked_critical_families_persist_failure_diagnostic() -> None:
    original_load = stable.h4.core._load
    original_previous = stable._PREVIOUS_HEALTH
    original_date = stable._RUN_DATE
    original_path = stable.PUBLISHABILITY_DIAGNOSTIC_PATH
    original_base_build = stable._BASE_BUILD_AUDIT
    original_assert = stable.h4._ORIGINAL_ASSERT
    original_runtime = stable.h4._runtime_uncovered_families
    try:
        stable.h4.core._load = lambda _path: {
            "requiredFamilies": [
                {"id": "maritime-coastal", "sourceIds": ["pcm-politiche-mare"]},
                {"id": "youth-civic-service", "sourceIds": ["pcm-politiche-giovanili-scu"]},
            ]
        }
        stable._PREVIOUS_HEALTH = {
            "pcm-politiche-mare": {
                "lastSuccessfulFetch": "2026-09-01",
                "consecutiveFailures": 2,
                "effectiveStatus": "grace",
            },
            "pcm-politiche-giovanili-scu": {
                "lastSuccessfulFetch": "2026-09-01",
                "consecutiveFailures": 2,
                "effectiveStatus": "grace",
            },
        }
        stable._RUN_DATE = date(2026, 9, 10)
        stable._BASE_BUILD_AUDIT = lambda _result: {
            "schemaVersion": "1.1",
            "summary": {"configuredSources": 2, "configuredEndpoints": 4},
            "sources": [
                {
                    "sourceId": "pcm-politiche-mare",
                    "runtimeStatus": "error",
                    "endpointCount": 2,
                    "endpointOk": 0,
                    "endpoints": [],
                },
                {
                    "sourceId": "pcm-politiche-giovanili-scu",
                    "runtimeStatus": "error",
                    "endpointCount": 2,
                    "endpointOk": 0,
                    "endpoints": [],
                },
            ],
            "extraFetches": [],
        }
        stable.h4._ORIGINAL_ASSERT = lambda _result: None
        stable.h4._runtime_uncovered_families = stable._runtime_uncovered_families_stable

        with TemporaryDirectory() as tmp:
            diagnostic_path = Path(tmp) / "opportunity-publishability-diagnostic.json"
            stable.PUBLISHABILITY_DIAGNOSTIC_PATH = diagnostic_path
            result = {
                "sourceCoverage": {
                    "rows": [
                        {"source_id": "pcm-politiche-mare", "runtimeStatus": "error"},
                        {"source_id": "pcm-politiche-giovanili-scu", "runtimeStatus": "error"},
                    ]
                },
                "coverageAudit": {},
            }
            try:
                stable.h4._assert_publishable_hardened(result)
            except RuntimeError as exc:
                message = str(exc)
            else:
                raise AssertionError("Il gate deve bloccare due famiglie obbligatorie fuori grace")

            assert diagnostic_path.exists(), diagnostic_path
            diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date
        stable.PUBLISHABILITY_DIAGNOSTIC_PATH = original_path
        stable._BASE_BUILD_AUDIT = original_base_build
        stable.h4._ORIGINAL_ASSERT = original_assert
        stable.h4._runtime_uncovered_families = original_runtime

    assert "maritime-coastal" in message, message
    assert "youth-civic-service" in message, message
    assert diagnostic["runtimeUncoveredFamilies"] == ["maritime-coastal", "youth-civic-service"], diagnostic
    assert diagnostic["transportAudit"]["schemaVersion"] == "1.2", diagnostic
    by_id = {row["sourceId"]: row for row in diagnostic["transportAudit"]["sources"]}
    assert by_id["pcm-politiche-mare"]["effectiveStatus"] == "error", by_id
    assert by_id["pcm-politiche-giovanili-scu"]["effectiveStatus"] == "error", by_id


_DETAIL_URL = "https://www.sviluppo.toscana.it/bando/avviso-mercati-rionali/"
_DETAIL_RULE_ID = "st-mercati-rionali-2026"


def _detail_fixture() -> tuple[dict, dict, dict]:
    rule = {
        "id": _DETAIL_RULE_ID,
        "source_id": "sviluppo-toscana",
        "title_pattern": "^Avviso Mercati Rionali$",
        "evidence_url": _DETAIL_URL,
        "deadline_override": "2026-09-15",
        "actionable": True,
    }
    old = {
        "id": "fixture-mercati-rionali",
        "rule_id": _DETAIL_RULE_ID,
        "source_id": "sviluppo-toscana",
        "title": "Avviso Mercati Rionali",
        "url": _DETAIL_URL,
        "deadline_at": "2026-09-15",
        "lifecycle_stage": "application_open",
        "quality_gate": {"status": "pass"},
        "verified_direct": True,
        "verified_at": "2026-09-09",
    }
    result = {
        "opportunities": [],
        "continuityHold": [
            {
                "kind": "existing_opportunity",
                "identity_key": "rule:" + _DETAIL_RULE_ID,
                "rule_id": _DETAIL_RULE_ID,
                "source_id": "sviluppo-toscana",
                "title": "Avviso Mercati Rionali",
                "url": _DETAIL_URL,
                "deadline_at": "2026-09-15",
                "reason": "missing_from_scan",
            }
        ],
        "sourceCoverage": {
            "rows": [{"source_id": "sviluppo-toscana", "runtimeStatus": "ok"}]
        },
        "counts": {},
    }
    previous = {"opportunities": [old]}
    return rule, result, previous


def _direct_detail_diagnostics() -> dict:
    return {
        "status": "ok",
        "transport": "http_browser",
        "fallbackUsed": False,
        "proxyUsed": False,
        "initialFailureClass": None,
        "browserFailureClass": None,
        "failureClass": None,
        "resolvedUrl": _DETAIL_URL,
        "redirected": False,
        "errors": [],
    }


def _test_live_open_detail_restores_listing_false_negative() -> None:
    rule, result, previous = _detail_fixture()
    original_rules = stable.h4.radar_module.load_rules
    original_fetch = stable._fetch_continuity_detail
    original_reconcile = stable.h4.daily._reconcile_final_continuity
    original_recompute = stable.h4.daily._recompute_after_continuity_restore
    try:
        stable.h4.radar_module.load_rules = lambda: ([rule], {}, {})
        stable._fetch_continuity_detail = lambda _url: (
            "<html><body><h1>Avviso Mercati Rionali</h1><p>Stato: Aperto. "
            "Scadenza presentazione domanda 15 settembre 2026. Presenta domanda.</p></body></html>",
            _direct_detail_diagnostics(),
        )
        stable.h4.daily._reconcile_final_continuity = lambda payload: payload.update(
            {"continuityHold": [], "continuityReconciliation": {"remaining": 0}}
        )
        stable.h4.daily._recompute_after_continuity_restore = lambda _payload: None
        restored = stable._revalidate_unresolved_continuity_details(
            result,
            previous,
            date(2026, 9, 10),
        )
    finally:
        stable.h4.radar_module.load_rules = original_rules
        stable._fetch_continuity_detail = original_fetch
        stable.h4.daily._reconcile_final_continuity = original_reconcile
        stable.h4.daily._recompute_after_continuity_restore = original_recompute

    assert len(restored) == 1, restored
    assert result["continuityHold"] == [], result
    restored_item = restored[0]
    assert restored_item["verification_status"] == "live_detail_revalidated", restored_item
    assert restored_item["verified_at"] == "2026-09-10", restored_item
    assert restored_item["continuity_revalidation"]["transport"] == "http_browser", restored_item


def _test_closed_or_404_detail_keeps_continuity_hold() -> None:
    rule, _, _ = _detail_fixture()
    original_rules = stable.h4.radar_module.load_rules
    original_fetch = stable._fetch_continuity_detail
    try:
        stable.h4.radar_module.load_rules = lambda: ([rule], {}, {})
        scenarios = [
            (
                "closed",
                "<html><body><h1>Avviso Mercati Rionali</h1><p>Stato: Chiuso. "
                "Scadenza 15 settembre 2026.</p></body></html>",
                _direct_detail_diagnostics(),
            ),
            (
                "404",
                None,
                {
                    "status": "error",
                    "transport": "failed",
                    "fallbackUsed": False,
                    "proxyUsed": False,
                    "initialFailureClass": "endpoint_missing",
                    "browserFailureClass": None,
                    "failureClass": "endpoint_missing",
                    "resolvedUrl": None,
                    "redirected": False,
                    "errors": ["HTTP [endpoint_missing]: 404"],
                },
            ),
        ]
        for label, payload, diagnostics in scenarios:
            _, result, previous = _detail_fixture()
            stable._fetch_continuity_detail = lambda _url, p=payload, d=diagnostics: (p, d)
            restored = stable._revalidate_unresolved_continuity_details(
                result,
                previous,
                date(2026, 9, 10),
            )
            assert restored == [], (label, restored)
            assert len(result["continuityHold"]) == 1, (label, result)
            assert result["continuityHold"][0]["reason"] == "missing_from_scan", (label, result)
    finally:
        stable.h4.radar_module.load_rules = original_rules
        stable._fetch_continuity_detail = original_fetch


def _test_reader_proxy_detail_cannot_clear_continuity_hold() -> None:
    rule, result, previous = _detail_fixture()
    original_rules = stable.h4.radar_module.load_rules
    original_fetch = stable._fetch_continuity_detail
    try:
        stable.h4.radar_module.load_rules = lambda: ([rule], {}, {})
        diagnostics = _direct_detail_diagnostics()
        diagnostics.update({"transport": "reader_proxy", "proxyUsed": True, "fallbackUsed": True})
        stable._fetch_continuity_detail = lambda _url: (
            "<html><body><h1>Avviso Mercati Rionali</h1><p>Stato: Aperto. "
            "Scadenza presentazione domanda 15 settembre 2026. Presenta domanda.</p></body></html>",
            diagnostics,
        )
        restored = stable._revalidate_unresolved_continuity_details(
            result,
            previous,
            date(2026, 9, 10),
        )
    finally:
        stable.h4.radar_module.load_rules = original_rules
        stable._fetch_continuity_detail = original_fetch

    assert restored == [], restored
    assert len(result["continuityHold"]) == 1, result
    assert result["continuityHold"][0]["reason"] == "missing_from_scan", result


def main() -> int:
    _test_recent_success_gives_family_grace()
    _test_legacy_error_gets_bootstrap_failure_window()
    _test_expired_grace_blocks_family()
    _test_success_resets_failure_counter()
    _test_pre_h5_snapshot_seeds_health()
    _test_critical_sources_use_independent_official_hosts()
    _test_secondary_endpoint_keeps_critical_families_covered()
    _test_blocked_critical_families_persist_failure_diagnostic()
    _test_live_open_detail_restores_listing_false_negative()
    _test_closed_or_404_detail_keeps_continuity_hold()
    _test_reader_proxy_detail_cannot_clear_continuity_hold()
    print("Salute persistente fonti e continuity detail Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())