#!/usr/bin/env python3
from __future__ import annotations

import urllib.error

import opportunity_daily_refresh_resilient as daily_h4
import opportunity_discovery_resilient as discovery


def _test_403_uses_chromium_dom() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    calls: list[str] = []
    try:
        def blocked(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://example.test/waf", 403, "Forbidden", hdrs=None, fp=None
            )

        def rendered(url: str, timeout_ms: int = 45_000) -> tuple[str, str]:
            calls.append(url)
            return (
                "<html><body><h3><a href='/bandi/nuovo'>Nuovo bando Comuni</a></h3></body></html>",
                "https://example.test/avvisi/",
            )

        discovery._fetch_browser_html_with_url = blocked
        discovery._fetch_playwright_html = rendered
        discovery.reset_trace()
        payload, diagnostics = discovery.fetch_with_diagnostics(
            "https://example.test/waf", timeout=5, attempts=1
        )
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser

    assert "href='/bandi/nuovo'" in payload, payload
    assert diagnostics["transport"] == "chromium", diagnostics
    assert diagnostics["fallbackUsed"] is True
    assert diagnostics["proxyUsed"] is False
    assert diagnostics["initialFailureClass"] == "http_403_waf"
    assert diagnostics["resolvedUrl"] == "https://example.test/avvisi/"
    assert diagnostics["redirected"] is True
    trace = discovery.FETCH_TRACE["https://example.test/waf"]
    assert trace["status"] == "ok", trace
    assert trace["transport"] == "chromium", trace
    assert calls == ["https://example.test/waf"]


def _test_timeout_uses_chromium() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    try:
        discovery._fetch_browser_html_with_url = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("timed out")
        )
        discovery._fetch_playwright_html = lambda url, **kwargs: (
            "<html><body>contenuto dinamico</body></html>", url
        )
        _, diagnostics = discovery.fetch_with_diagnostics(
            "https://example.test/timeout", timeout=5, attempts=1
        )
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser

    assert diagnostics["transport"] == "chromium", diagnostics
    assert diagnostics["initialFailureClass"] == "timeout_client"


def _test_timeout_uses_reader_after_chromium_failure() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    original_reader = discovery._fetch_reader_markdown
    try:
        discovery._fetch_browser_html_with_url = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("http timed out")
        )
        discovery._fetch_playwright_html = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("browser timed out")
        )
        discovery._fetch_reader_markdown = lambda *args, **kwargs: (
            "### Nuovo bando per i Comuni\n"
            "Contributi per enti locali.\n"
            "[SCOPRI TUTTO](https://example.test/bandi/nuovo)\n"
        )
        payload, diagnostics = discovery.fetch_with_diagnostics(
            "https://example.test/blocked", timeout=5, attempts=1
        )
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser
        discovery._fetch_reader_markdown = original_reader

    assert diagnostics["transport"] == "reader_proxy", diagnostics
    assert diagnostics["proxyUsed"] is True
    assert diagnostics["initialFailureClass"] == "timeout_client"
    assert diagnostics["browserFailureClass"] == "timeout_client"
    assert "Nuovo bando per i Comuni" in payload, payload
    assert "https://example.test/bandi/nuovo" in payload, payload


def _test_missing_endpoint_does_not_hide_configuration_drift() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    original_reader = discovery._fetch_reader_markdown
    browser_called = False
    reader_called = False
    try:
        discovery._fetch_browser_html_with_url = lambda *args, **kwargs: (_ for _ in ()).throw(
            urllib.error.HTTPError(
                "https://example.test/moved", 404, "Not Found", hdrs=None, fp=None
            )
        )

        def browser(*args, **kwargs):
            nonlocal browser_called
            browser_called = True
            return "<html></html>", "https://example.test/moved"

        def reader(*args, **kwargs):
            nonlocal reader_called
            reader_called = True
            return "contenuto"

        discovery._fetch_playwright_html = browser
        discovery._fetch_reader_markdown = reader
        try:
            discovery.fetch_with_diagnostics("https://example.test/moved", timeout=5, attempts=1)
        except discovery.DiscoveryFetchError as exc:
            diagnostics = exc.diagnostics
        else:
            raise AssertionError("Un endpoint 404 deve restare un errore di configurazione")
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser
        discovery._fetch_reader_markdown = original_reader

    assert diagnostics["failureClass"] == "endpoint_missing", diagnostics
    assert diagnostics["fallbackUsed"] is False
    assert browser_called is False
    assert reader_called is False


def _test_dns_error_does_not_hide_configuration_drift() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    original_reader = discovery._fetch_reader_markdown
    browser_called = False
    reader_called = False
    try:
        discovery._fetch_browser_html_with_url = lambda *args, **kwargs: (_ for _ in ()).throw(
            urllib.error.URLError("Name or service not known")
        )

        def browser(*args, **kwargs):
            nonlocal browser_called
            browser_called = True
            return "<html></html>", "https://missing.example.test/"

        def reader(*args, **kwargs):
            nonlocal reader_called
            reader_called = True
            return "contenuto"

        discovery._fetch_playwright_html = browser
        discovery._fetch_reader_markdown = reader
        try:
            discovery.fetch_with_diagnostics("https://missing.example.test/", timeout=5, attempts=1)
        except discovery.DiscoveryFetchError as exc:
            diagnostics = exc.diagnostics
        else:
            raise AssertionError("Un DNS failure deve restare errore di configurazione/rete")
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser
        discovery._fetch_reader_markdown = original_reader

    assert diagnostics["failureClass"] == "dns_error", diagnostics
    assert diagnostics["fallbackUsed"] is False
    assert browser_called is False
    assert reader_called is False


def _test_probe_exposes_endpoint_diagnostics() -> None:
    radar = daily_h4.radar_module
    config = {
        "discoverySources": [{
            "id": "test-source",
            "label": "Fonte test",
            "publisher": "Fonte test",
            "territory": "Italia",
            "urls": ["https://example.test/list"],
            "includeTerms": ["bando"],
            "municipalTerms": ["comuni"],
        }]
    }
    payloads = {
        "https://example.test/list": (
            "<html><body><h4><a href='/bando'>Bando per i Comuni</a></h4>"
            "<p>Avviso e finanziamento per comuni.</p></body></html>"
        )
    }
    _, states = discovery.probe_discovery_sources(radar, config, payloads=payloads)
    state = states[0]
    assert state["status"] == "ok", state
    assert state["endpointOk"] == 1
    assert state["endpointResults"][0]["transport"] == "fixture"
    assert state["failureClasses"] == []


def _test_probe_marks_reader_as_degraded() -> None:
    radar = daily_h4.radar_module
    original_fetch = discovery.fetch_with_diagnostics
    config = {
        "discoverySources": [{
            "id": "proxy-source",
            "label": "Fonte proxy",
            "publisher": "Fonte proxy",
            "territory": "Italia",
            "urls": ["https://example.test/list"],
            "includeTerms": ["bando"],
            "municipalTerms": ["comuni"],
        }]
    }
    try:
        discovery.fetch_with_diagnostics = lambda *args, **kwargs: (
            "<html><body><h4><a href='/bando'>Bando per i Comuni</a></h4>"
            "<p>Avviso per comuni.</p></body></html>",
            {
                "status": "ok", "transport": "reader_proxy", "httpAttempts": 2,
                "fallbackUsed": True, "proxyUsed": True,
                "initialFailureClass": "timeout_client", "browserFailureClass": "timeout_client",
                "failureClass": None, "resolvedUrl": "https://example.test/list",
                "redirected": False, "errors": [],
            },
        )
        queue, states = discovery.probe_discovery_sources(radar, config)
    finally:
        discovery.fetch_with_diagnostics = original_fetch

    assert queue, queue
    assert states[0]["status"] == "degraded", states[0]
    assert states[0]["proxySuccessCount"] == 1, states[0]
    assert states[0]["fallbackSuccessCount"] == 1, states[0]


def _test_probe_uses_resolved_url_for_relative_links() -> None:
    radar = daily_h4.radar_module
    original_fetch = discovery.fetch_with_diagnostics
    config = {
        "discoverySources": [{
            "id": "redirect-source",
            "label": "Fonte redirect",
            "publisher": "Fonte redirect",
            "territory": "Italia",
            "urls": ["https://example.test/vecchio"],
            "includeTerms": ["bando"],
            "municipalTerms": ["comuni"],
        }]
    }
    try:
        discovery.fetch_with_diagnostics = lambda *args, **kwargs: (
            "<html><body><h4><a href='nuovo-bando'>Bando per i Comuni</a></h4>"
            "<p>Avviso per comuni.</p></body></html>",
            {
                "status": "ok", "transport": "chromium", "httpAttempts": 2,
                "fallbackUsed": True, "proxyUsed": False,
                "initialFailureClass": "http_403_waf", "browserFailureClass": None,
                "failureClass": None, "resolvedUrl": "https://example.test/avvisi/",
                "redirected": True, "errors": [],
            },
        )
        queue, states = discovery.probe_discovery_sources(radar, config)
    finally:
        discovery.fetch_with_diagnostics = original_fetch

    assert states[0]["fallbackSuccessCount"] == 1, states[0]
    assert queue, "Il DOM renderizzato deve produrre almeno un candidato"
    assert any(
        str(item.get("url") or "") == "https://example.test/avvisi/nuovo-bando"
        for item in queue
    ), queue


def _test_runtime_compose_replaces_stale_sources() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    primary_ids = {str(source.get("id") or "") for source in config.get("sources") or []}
    assert "pa-digitale-2026" not in primary_ids

    scu = next(
        source for source in config.get("discoverySources") or []
        if str(source.get("id") or "") == "pcm-politiche-giovanili-scu"
    )
    assert scu["urls"] == [daily_h4._SCU_CURRENT_URL]
    assert "/servizio-civile/bandi-e-avvisi-di-servizio-civile/" in scu["urls"][0]


def _test_transport_audit_exposes_endpoint_health() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    source = next(row for row in config.get("sources") or [] if str(row.get("url") or "").strip())
    source_id = str(source["id"])
    url = str(source["url"])

    discovery.reset_trace()
    discovery.FETCH_TRACE[url] = {
        "url": url,
        "status": "ok",
        "transport": "reader_proxy",
        "httpAttempts": 2,
        "fallbackUsed": True,
        "proxyUsed": True,
        "initialFailureClass": "timeout_client",
        "browserFailureClass": "timeout_client",
        "failureClass": None,
        "resolvedUrl": url,
        "redirected": False,
        "errors": ["HTTP timeout", "Chromium timeout"],
    }
    audit = daily_h4._build_transport_audit({
        "sources": [{"sourceId": source_id, "status": "degraded"}],
        "discoverySources": [],
    })

    assert audit["schemaVersion"] == "1.1", audit
    matching = next(row for row in audit["sources"] if row["sourceId"] == source_id)
    assert matching["endpointOk"] == 1, matching
    assert matching["fallbackSuccessCount"] == 1, matching
    assert matching["proxySuccessCount"] == 1, matching
    assert audit["summary"]["fallbackSuccesses"] >= 1, audit["summary"]
    assert audit["summary"]["proxySuccesses"] >= 1, audit["summary"]
    assert audit["summary"]["configuredSources"] > 0, audit["summary"]


def main() -> int:
    _test_403_uses_chromium_dom()
    _test_timeout_uses_chromium()
    _test_timeout_uses_reader_after_chromium_failure()
    _test_missing_endpoint_does_not_hide_configuration_drift()
    _test_dns_error_does_not_hide_configuration_drift()
    _test_probe_exposes_endpoint_diagnostics()
    _test_probe_marks_reader_as_degraded()
    _test_probe_uses_resolved_url_for_relative_links()
    _test_runtime_compose_replaces_stale_sources()
    _test_transport_audit_exposes_endpoint_health()
    print("Discovery resiliente Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
