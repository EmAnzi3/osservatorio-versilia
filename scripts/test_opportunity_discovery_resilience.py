#!/usr/bin/env python3
from __future__ import annotations

import urllib.error

import opportunity_daily_refresh_resilient as daily_h3
import opportunity_discovery_resilient as discovery


def _test_403_uses_chromium() -> None:
    original_http = discovery.transport._fetch_browser_html
    original_browser = discovery.transport._fetch_playwright_text
    calls: list[str] = []
    try:
        def blocked(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://example.test/waf", 403, "Forbidden", hdrs=None, fp=None
            )

        def rendered(url: str, timeout_ms: int = 45_000) -> str:
            calls.append(url)
            return "Pagina istituzionale resa da Chromium"

        discovery.transport._fetch_browser_html = blocked
        discovery.transport._fetch_playwright_text = rendered
        payload, diagnostics = discovery.fetch_with_diagnostics(
            "https://example.test/waf", timeout=5, attempts=1
        )
    finally:
        discovery.transport._fetch_browser_html = original_http
        discovery.transport._fetch_playwright_text = original_browser

    assert "Chromium" in payload
    assert diagnostics["transport"] == "chromium", diagnostics
    assert diagnostics["fallbackUsed"] is True
    assert diagnostics["initialFailureClass"] == "http_403_waf"
    assert calls == ["https://example.test/waf"]


def _test_timeout_uses_chromium() -> None:
    original_http = discovery.transport._fetch_browser_html
    original_browser = discovery.transport._fetch_playwright_text
    try:
        discovery.transport._fetch_browser_html = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("timed out")
        )
        discovery.transport._fetch_playwright_text = lambda *args, **kwargs: "contenuto dinamico"
        _, diagnostics = discovery.fetch_with_diagnostics(
            "https://example.test/timeout", timeout=5, attempts=1
        )
    finally:
        discovery.transport._fetch_browser_html = original_http
        discovery.transport._fetch_playwright_text = original_browser

    assert diagnostics["transport"] == "chromium", diagnostics
    assert diagnostics["initialFailureClass"] == "timeout_client"


def _test_missing_endpoint_does_not_hide_configuration_drift() -> None:
    original_http = discovery.transport._fetch_browser_html
    original_browser = discovery.transport._fetch_playwright_text
    browser_called = False
    try:
        discovery.transport._fetch_browser_html = lambda *args, **kwargs: (_ for _ in ()).throw(
            urllib.error.HTTPError(
                "https://example.test/moved", 404, "Not Found", hdrs=None, fp=None
            )
        )

        def browser(*args, **kwargs):
            nonlocal browser_called
            browser_called = True
            return "non deve essere usato"

        discovery.transport._fetch_playwright_text = browser
        try:
            discovery.fetch_with_diagnostics("https://example.test/moved", timeout=5, attempts=1)
        except discovery.DiscoveryFetchError as exc:
            diagnostics = exc.diagnostics
        else:
            raise AssertionError("Un endpoint 404 deve restare un errore di configurazione")
    finally:
        discovery.transport._fetch_browser_html = original_http
        discovery.transport._fetch_playwright_text = original_browser

    assert diagnostics["failureClass"] == "endpoint_missing", diagnostics
    assert diagnostics["fallbackUsed"] is False
    assert browser_called is False


def _test_probe_exposes_endpoint_diagnostics() -> None:
    radar = daily_h3.radar_module
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


def _test_runtime_compose_replaces_stale_sources() -> None:
    config, _ = daily_h3._compose_runtime_hardened()
    primary_ids = {str(source.get("id") or "") for source in config.get("sources") or []}
    assert "pa-digitale-2026" not in primary_ids

    scu = next(
        source for source in config.get("discoverySources") or []
        if str(source.get("id") or "") == "pcm-politiche-giovanili-scu"
    )
    assert scu["urls"] == [daily_h3._SCU_CURRENT_URL]
    assert "/servizio-civile/bandi-e-avvisi-di-servizio-civile/" in scu["urls"][0]


def main() -> int:
    _test_403_uses_chromium()
    _test_timeout_uses_chromium()
    _test_missing_endpoint_does_not_hide_configuration_drift()
    _test_probe_exposes_endpoint_diagnostics()
    _test_runtime_compose_replaces_stale_sources()
    print("Discovery resiliente Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
