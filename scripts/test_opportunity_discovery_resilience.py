#!/usr/bin/env python3
from __future__ import annotations

import urllib.error
from urllib.parse import urlsplit

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


def _test_reader_403_does_not_misattribute_source_failure() -> None:
    original_http = discovery._fetch_browser_html_with_url
    original_browser = discovery._fetch_playwright_html
    original_reader = discovery._fetch_reader_markdown
    try:
        discovery._fetch_browser_html_with_url = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("source timed out")
        )
        discovery._fetch_playwright_html = lambda *args, **kwargs: (_ for _ in ()).throw(
            TimeoutError("browser timed out")
        )
        discovery._fetch_reader_markdown = lambda *args, **kwargs: (_ for _ in ()).throw(
            urllib.error.HTTPError(
                "https://r.jina.ai/https://example.test/list", 403, "Forbidden", hdrs=None, fp=None
            )
        )
        try:
            discovery.fetch_with_diagnostics(
                "https://example.test/list", timeout=5, attempts=1
            )
        except discovery.DiscoveryFetchError as exc:
            diagnostics = exc.diagnostics
        else:
            raise AssertionError("La catena esaurita deve fallire")
    finally:
        discovery._fetch_browser_html_with_url = original_http
        discovery._fetch_playwright_html = original_browser
        discovery._fetch_reader_markdown = original_reader

    assert diagnostics["failureClass"] == "timeout_client", diagnostics
    assert diagnostics["rootFailureClass"] == "timeout_client", diagnostics
    assert diagnostics["browserFailureClass"] == "timeout_client", diagnostics
    assert diagnostics["readerFailureClass"] == "http_403_waf", diagnostics
    assert diagnostics["terminalFailureClass"] == "http_403_waf", diagnostics


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


def _test_exhausted_transport_is_source_scoped_network_error() -> None:
    error = discovery.DiscoveryFetchError(
        "HTTP timeout; Chromium timeout; Reader 403",
        {"failureClass": "http_403_waf"},
    )
    assert isinstance(error, urllib.error.URLError)
    assert error.diagnostics["failureClass"] == "http_403_waf"


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


def _test_endpoint_content_signature_rejects_unrelated_200_page() -> None:
    radar = daily_h4.radar_module
    original_fetch = discovery.fetch_with_diagnostics
    url = "https://mirror.example.test/"
    config = {
        "discoverySources": [{
            "id": "signed-mirror",
            "label": "Mirror firmato",
            "publisher": "Mirror firmato",
            "territory": "Italia",
            "urls": [url],
            "endpointRequiredTerms": {url: ["Notizie da ANCI Nazionale"]},
            "includeTerms": ["bando"],
            "municipalTerms": ["comuni"],
        }]
    }
    try:
        discovery.fetch_with_diagnostics = lambda *args, **kwargs: (
            "<html><body><h1>Pagina di manutenzione</h1></body></html>",
            {
                "status": "ok", "transport": "http_browser", "httpAttempts": 2,
                "fallbackUsed": False, "proxyUsed": False,
                "initialFailureClass": None, "rootFailureClass": None,
                "browserFailureClass": None, "readerFailureClass": None,
                "terminalFailureClass": None, "failureClass": None,
                "resolvedUrl": url, "redirected": False, "errors": [],
            },
        )
        queue, states = discovery.probe_discovery_sources(radar, config)
    finally:
        discovery.fetch_with_diagnostics = original_fetch

    assert queue == [], queue
    assert states[0]["status"] == "error", states[0]
    assert states[0]["endpointOk"] == 0, states[0]
    endpoint = states[0]["endpointResults"][0]
    assert endpoint["failureClass"] == "content_signature_missing", endpoint
    assert endpoint["contentSignatureMissing"] == ["Notizie da ANCI Nazionale"], endpoint


def _test_anci_independent_mirror_survives_national_endpoint_failures() -> None:
    radar = daily_h4.radar_module
    national_feed = "https://www.anci.it/feed/"
    digital_feed = "https://sistemacomunidigitali.anci.it/feed/"
    regional_mirror = "https://www.anci.piemonte.it/"
    config = {
        "discoverySources": [{
            "id": "anci-nazionale",
            "label": "ANCI nazionale",
            "publisher": "ANCI",
            "territory": "Italia",
            "urls": [national_feed, digital_feed, regional_mirror],
            "endpointRoles": {regional_mirror: "supplementary"},
            "endpointRequiredTerms": {
                regional_mirror: ["Notizie da ANCI Nazionale"],
            },
            "includeTerms": ["bando", "avviso", "contributi"],
            "municipalTerms": ["comuni", "enti locali"],
        }]
    }
    original_fetch = discovery.fetch_with_diagnostics

    def fetch(url: str, **kwargs):
        if url in {national_feed, digital_feed}:
            raise discovery.DiscoveryFetchError(
                "HTTP timeout; Chromium timeout; Reader 403",
                {
                    "status": "error", "transport": "failed", "fallbackUsed": True,
                    "proxyUsed": True, "initialFailureClass": "timeout_client",
                    "rootFailureClass": "timeout_client",
                    "browserFailureClass": "timeout_client",
                    "readerFailureClass": "http_403_waf",
                    "terminalFailureClass": "http_403_waf",
                    "failureClass": "timeout_client", "resolvedUrl": None,
                    "redirected": False,
                    "errors": ["HTTP timeout", "Chromium timeout", "Reader 403"],
                },
            )
        return (
            "<html><body><section><h2>Notizie da ANCI Nazionale</h2>"
            "<article><a href='/bando-comuni'>Bando per i Comuni</a>"
            "<p>Avviso per contributi destinati agli enti locali.</p></article>"
            "</section></body></html>",
            {
                "status": "ok", "transport": "http_browser", "httpAttempts": 1,
                "fallbackUsed": False, "proxyUsed": False,
                "initialFailureClass": None, "rootFailureClass": None,
                "browserFailureClass": None, "readerFailureClass": None,
                "terminalFailureClass": None, "failureClass": None,
                "resolvedUrl": regional_mirror, "redirected": False, "errors": [],
            },
        )

    try:
        discovery.fetch_with_diagnostics = fetch
        queue, states = discovery.probe_discovery_sources(radar, config)
    finally:
        discovery.fetch_with_diagnostics = original_fetch

    state = states[0]
    assert state["status"] == "error", state
    assert state["coverageEndpointOk"] == 0, state
    assert state["supplementaryEndpointOk"] == 1, state
    assert state["endpointOk"] == 1, state
    assert state["endpointCount"] == 3, state
    assert state["failureClasses"] == ["timeout_client"], state
    assert state["candidateCount"] >= 1, state
    assert any(
        "Bando per i Comuni" in " ".join(
            [str(item.get("title") or ""), str(item.get("summary") or "")]
        )
        for item in queue
    ), queue
    failed = [row for row in state["endpointResults"] if row["status"] == "error"]
    assert len(failed) == 2, failed
    assert all(row["rootFailureClass"] == "timeout_client" for row in failed), failed
    assert all(row["readerFailureClass"] == "http_403_waf" for row in failed), failed


def _test_anci_news_short_previews_preserve_discovery() -> None:
    # Reduced cards from the owner-provided ANCI News HTML (6 October 2026).
    # Short previews omit municipal beneficiaries: discovery must not infer
    # eligibility, but must retain the school-building notice for review.
    config, _ = daily_h4._compose_runtime_hardened()
    source = next(row for row in config["discoverySources"] if row["id"] == "anci-nazionale")
    listing = "https://www.anci.it/category/generico/news/"
    assert listing in source["urls"]
    assert listing + "feed/" in source["urls"]
    assert discovery.endpoint_role(source, listing) == "listing"
    payload = """
    <h4><a href="/proroga-sport-cultura/">Prorogati al 5 dicembre i bandi Sport Missione Comune e Cultura Missione Comune</a></h4>
    <p>Possono partecipare Comuni e Unioni di Comuni per richiedere mutui.</p>
    <h4><a href="/edilizia-mim/">Edilizia scolastica, avviso MIM su risorse otto per mille per interventi urgenti e indifferibili</a></h4>
    <p>Da oggi 5 ottobre al via alle candidature sulla piattaforma informatica dedicata.</p>
    <h4><a href="/asacom/">Asacom 2026, intesa sul decreto riparto per Comuni e Regioni</a></h4>
    <p>Il decreto prevede lo stanziamento di 160 milioni a favore dei Comuni.</p>
    <h4><a href="/protocollo/">Firma del protocollo di intesa tra Anci e Comitato Paralimpico</a></h4>
    <p>Interverranno il presidente e i sindaci.</p>
    """
    queue = daily_h4.radar_module.discovery_candidates(source, payload, listing)
    assert {row["url"] for row in queue} == {
        "https://www.anci.it/proroga-sport-cultura/",
        "https://www.anci.it/edilizia-mim/",
        "https://www.anci.it/asacom/",
    }, queue
    assert all(row["discovery_only"] and row["status"] == "internal_review" for row in queue)


def _test_rss_and_mim_table_keep_individual_notice_links() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    sources = {row["id"]: row for row in config["discoverySources"]}
    feed = """<rss><channel><title>ANCI</title>
    <item><title>Riparto fondo per Comuni</title><link>https://www.anci.it/riparto/</link><description>Risorse per Comuni e Regioni</description></item>
    <item><title>La bandiera dei Comuni</title><link>https://www.anci.it/bandiera/</link><description>Cerimonia</description></item>
    </channel></rss>"""
    queue = daily_h4.radar_module.discovery_candidates(sources["anci-nazionale"], feed, "https://www.anci.it/category/generico/news/feed/")
    assert [row["url"] for row in queue] == ["https://www.anci.it/riparto/"], queue
    listing = "https://pn20212027.istruzione.it/avvisi/?beneficiari=enti-locali"
    assert listing in sources["mim-enti-locali"]["urls"]
    assert discovery.endpoint_role(sources["mim-enti-locali"], listing) == "listing"
    table = """<table id="table-avvisi"><tbody>
    <tr><td>Arredi didattici innovativi per asili nido</td><td>FESR</td><td>123</td><td>2026</td><td>Enti locali</td><td><a href="/avvisi/arredi/"><i></i></a></td></tr>
    <tr><td>Scuole polo per la comunicazione</td><td>FSE+</td><td>456</td><td>2026</td><td>Istituti scolastici</td><td><a href="/avvisi/estate/"><i></i></a></td></tr>
    </tbody></table>"""
    queue = daily_h4.radar_module.discovery_candidates(sources["mim-enti-locali"], table, listing)
    assert [row["url"] for row in queue] == ["https://pn20212027.istruzione.it/avvisi/arredi/"], queue
    assert all(row["status"] == "internal_review" and row["discovery_only"] for row in queue)
    empty = table.replace("Enti locali", "Istituti scolastici")
    assert daily_h4.radar_module.discovery_candidates(sources["mim-enti-locali"], empty, listing) == []


def _test_runtime_compose_replaces_stale_sources() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    primary_ids = {str(source.get("id") or "") for source in config.get("sources") or []}
    assert "pa-digitale-2026" not in primary_ids

    discovery_by_id = {
        str(source.get("id") or ""): source
        for source in config.get("discoverySources") or []
    }
    mare = discovery_by_id["pcm-politiche-mare"]
    scu = discovery_by_id["pcm-politiche-giovanili-scu"]
    anci = discovery_by_id["anci-nazionale"]

    assert mare["urls"] == list(daily_h4._MARE_OFFICIAL_URLS), mare
    assert scu["urls"] == list(daily_h4._SCU_OFFICIAL_URLS), scu
    assert mare["fetchTimeoutSeconds"] == 12
    assert scu["fetchTimeoutSeconds"] == 12
    assert mare["urls"][0].endswith("/it/bandi-e-avvisi/")
    assert "gazzettaufficiale.it" in mare["urls"][1]
    assert "/avvisi-di-presentazione-programmi-e-progetti/" in scu["urls"][0]
    assert "scelgoilserviziocivile.gov.it/leggi-il-bando/" in scu["urls"][1]
    assert len({urlsplit(url).hostname for url in mare["urls"]}) == len(mare["urls"])
    assert len({urlsplit(url).hostname for url in scu["urls"]}) == len(scu["urls"])
    assert not any("presidenza.governo.it/AmministrazioneTrasparente/" in url for url in mare["urls"])
    assert not any("presidenza.governo.it/AmministrazioneTrasparente/" in url for url in scu["urls"])
    assert "https://www.anci.piemonte.it/" in anci["urls"], anci
    assert len({urlsplit(url).hostname for url in anci["urls"]}) >= 3, anci
    assert anci["endpointRequiredTerms"]["https://www.anci.piemonte.it/"] == [
        "Notizie da ANCI Nazionale"
    ]


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


def _test_chromium_rejects_error_document() -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    class ErrorPage(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"<html><body>Service unavailable</body></html>")
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), ErrorPage)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        try:
            discovery._fetch_playwright_html(f"http://127.0.0.1:{server.server_port}/", timeout_ms=5000)
        except urllib.error.HTTPError as exc:
            assert exc.code == 503, exc
        else:
            raise AssertionError("Chromium treated an HTTP 503 error document as source coverage")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _test_annual_archive_follows_current_year() -> None:
    from datetime import date
    original_date = daily_h4.date
    class FutureDate:
        @staticmethod
        def today():
            return date(2027, 1, 1)
    try:
        daily_h4.date = FutureDate
        config, _ = daily_h4._compose_runtime_hardened()
        source = next(row for row in config["discoverySources"] if row["id"] == "pcm-stato-citta")
        assert "https://www.statocitta.it/home/notizie-e-comunicati/2027/" in source["urls"]
        assert not any("/2026/" in url for url in source["urls"])
    finally:
        daily_h4.date = original_date


def _test_configured_detail_pages_cannot_attest_discovery() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    for key, listing_count in (("gse", 1), ("pcm-sport", 2), ("cinea-life", 1)):
        source = next(row for row in config["discoverySources"] if row["id"] == key)
        listings = [url for url in source["urls"] if discovery.endpoint_role(source, url) == "listing"]
        supplements = [url for url in source["urls"] if discovery.endpoint_role(source, url) == "supplementary"]
        assert len(listings) == listing_count and supplements, (key, listings, supplements)
        audit = [{"role": "listing", "status": "error"} for _ in listings]
        audit += [{"role": "supplementary", "status": "ok"} for _ in supplements]
        assert discovery.coverage_status(audit) == "error", (key, audit)
        audit[0]["status"] = "ok"
        assert discovery.coverage_status(audit) in {"ok", "degraded"}


def _test_listing_coverage_status() -> None:
    secondary = {"role": "supplementary", "status": "ok", "proxyUsed": False}
    primary = {"role": "listing", "status": "ok", "proxyUsed": False}
    assert discovery.coverage_status([secondary]) == "error"
    assert discovery.coverage_status([secondary, {**primary, "status": "error"}]) == "error"
    assert discovery.coverage_status([primary, {**secondary, "status": "error"}]) == "ok"
    assert discovery.coverage_status([primary, {**primary, "status": "error"}]) == "degraded"
    assert discovery.coverage_status([{**primary, "proxyUsed": True}]) == "degraded"
    import opportunity_transport_smoke as smoke
    original = discovery.fetch_with_diagnostics
    try:
        discovery.fetch_with_diagnostics = lambda url, **kwargs: ("<html>unrelated content</html>",
            {"status": "ok", "transport": "http_browser", "httpAttempts": 1})
        result = smoke._probe_source("signature", {"urls": ["https://example.test/"],
            "endpointRequiredTerms": {"https://example.test/": ["national news"]}})
        assert result["status"] == "error", result
        assert result["failureClasses"] == ["content_signature_missing"], result
    finally:
        discovery.fetch_with_diagnostics = original



def _test_live_transport_budget_and_journal() -> None:
    import json
    from pathlib import Path
    import tempfile
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from opportunity_transport_budget import TransportBudget

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/slow":
                time.sleep(2)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html>official notice</html>")
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "progress.jsonl"
            budget = TransportBudget({"sources": [{"id": "official", "url": base + "/ok"}]},
                                     endpoint_seconds=5, source_seconds=10, scan_seconds=20,
                                     journal=journal)
            payload, diagnostics = budget.fetch(base + "/ok")
            assert "official notice" in payload and diagnostics["status"] == "ok"
            assert budget.fetch(base + "/ok")[0] == payload  # same-run cache
            budget.endpoint_seconds = 0.3
            started = time.monotonic()
            payload, diagnostics = budget.fetch(base + "/slow")
            assert payload is None and diagnostics["failureClass"] == "timeout_client"
            assert diagnostics["budgetScope"] == "endpoint"
            assert time.monotonic() - started < 1.5  # all retries/fallbacks bounded
            budget.source_seconds = 0.1
            payload, diagnostics = budget.fetch(base + "/another")
            assert payload is None and diagnostics["budgetScope"] == "source"
            assert diagnostics["elapsedSeconds"] < 0.1
            budget.deadline = time.monotonic() - 1
            payload, diagnostics = budget.fetch("http://localhost:1/not-run")
            assert payload is None and diagnostics["budgetScope"] == "scan"
            assert budget.scan_exhausted
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
            assert [row["event"] for row in rows] == ["start", "end"] * 4
            assert rows[3]["status"] == "error" and rows[3]["sourceId"] == "official"
    finally:
        server.shutdown()
        server.server_close()



def _test_expired_worker_kills_descendants() -> None:
    import os
    from pathlib import Path
    import subprocess
    import sys
    import tempfile
    import time
    from unittest.mock import patch
    import opportunity_transport_budget as bounded

    if os.name == "nt":
        return  # Linux Actions requires whole process-group cleanup.
    original_popen = subprocess.Popen
    with tempfile.TemporaryDirectory() as tmp:
        pid_file = Path(tmp) / "descendant.pid"
        code = ("import subprocess,time,pathlib; "
                "p=subprocess.Popen(['" + sys.executable + "','-c','import time; time.sleep(30)']); "
                "pathlib.Path(" + repr(str(pid_file)) + ").write_text(str(p.pid)); time.sleep(30)")
        def stalled_worker(command, **kwargs):
            return original_popen([sys.executable, "-c", code], **kwargs)
        budget = bounded.TransportBudget({}, endpoint_seconds=0.5, journal=Path(tmp) / "trace.jsonl")
        with patch.object(bounded.subprocess, "Popen", stalled_worker):
            payload, diagnostics = budget.fetch("https://example.test/stall")
        assert payload is None and diagnostics["failureClass"] == "timeout_client"
        assert pid_file.exists(), "Descendant must have started before the deadline"
        status = Path("/proc") / pid_file.read_text() / "stat"
        for _ in range(20):
            if not status.exists() or status.read_text().split()[2] == "Z":
                break
            time.sleep(0.01)
        else:
            raise AssertionError("Expired worker left a running browser descendant")



def _test_parallel_prefetch_keeps_budgets_and_cache() -> None:
    from concurrent.futures import ThreadPoolExecutor
    import json
    from pathlib import Path
    import tempfile
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from opportunity_transport_budget import TransportBudget

    state = {"active": 0, "peak": 0, "requests": 0}
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            with lock:
                state["active"] += 1
                state["requests"] += 1
                state["peak"] = max(state["peak"], state["active"])
            try:
                time.sleep(1)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html>official municipal notice</html>")
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with lock:
                    state["active"] -= 1
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    config = {"sources": [{"id": "source-0", "url": base + "/0"}],
              "discoverySources": [{"id": f"source-{i}", "urls": [base + f"/{i}"]} for i in range(4)]}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "parallel.jsonl"
            budget = TransportBudget(config, endpoint_seconds=2, source_seconds=8,
                                     scan_seconds=3, journal=journal)
            budget.prefetch(config)
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
            assert len(rows) == 8 and sum(row.get("status") == "ok" for row in rows) == 4, rows
            assert state["peak"] >= 2, "A lock must not serialize network I/O"
            assert not budget.scan_exhausted
            # Concurrent consumers of one URL reuse the live result exactly once.
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(budget.fetch, [base + "/0"] * 4))
            assert all(result[1]["status"] == "ok" for result in results)
            assert state["requests"] == 4
            assert len(journal.read_text().splitlines()) == 8
            uncached = TransportBudget(config, endpoint_seconds=2, source_seconds=8,
                                      scan_seconds=3, journal=Path(tmp) / "dedupe.jsonl")
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(uncached.fetch, [base + "/new"] * 4))
            assert all(result[1]["status"] == "ok" for result in results)
            assert state["requests"] == 5, "In-flight requests must also be deduplicated"

            # Two different source IDs share this host: active requests reserve
            # its allowance, so their cumulative work cannot double the budget.
            limited = TransportBudget({}, endpoint_seconds=2, source_seconds=.3,
                                      scan_seconds=3, journal=Path(tmp) / "limited.jsonl")
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(limited.fetch, [base + "/a", base + "/b"]))
            assert all(result[0] is None for result in results)
            assert limited.host_spent[f"127.0.0.1:{server.server_port}"] < .5
            assert sorted(result[1]["elapsedSeconds"] for result in results)[0] < .05
    finally:
        server.shutdown()
        server.server_close()


def _test_anci_toscana_short_cards_are_isolated() -> None:
    config, _ = daily_h4._compose_runtime_hardened()
    source = next(row for row in config["discoverySources"] if row["id"] == "anci-toscana")
    listing = "https://ancitoscana.it/categorie/bandi/"
    payload = '''<div class="e-loop-item">
      <div class="elementor-widget-theme-post-title"><h4><a href="/ccn/">Valorizzazione Centri Commerciali Naturali</a></h4></div>
      <div class="elementor-widget-theme-post-excerpt">Contributi del 60% per eventi e digitalizzazione</div></div>
      <div class="e-loop-item"><a href="/categorie/comuni/">Comuni</a>
      <div class="elementor-widget-theme-post-title"><h4><a href="/jazz/">Avviso pubblico musica jazz</a></h4></div>
      <div class="elementor-widget-theme-post-excerpt">Contributi per festival, domande entro settembre</div></div>
      <div class="e-loop-item"><div class="elementor-widget-theme-post-title"><h4><a href="/cerimonia/">Cerimonia dei Comuni</a></h4></div>
      <div class="elementor-widget-theme-post-excerpt">Incontro istituzionale</div></div>
      <footer>Bandi e finanziamenti ai Comuni</footer>'''
    rows = daily_h4.radar_module.discovery_candidates(source, payload, listing)
    assert [row["url"] for row in rows] == ["https://ancitoscana.it/ccn/", "https://ancitoscana.it/jazz/"], rows
    assert rows[0]["summary"] == "Contributi del 60% per eventi e digitalizzazione", rows
    assert all(row["status"] == "internal_review" and row["discovery_only"] for row in rows), rows
    # A generic topic page must still require municipal evidence in the card.
    assert daily_h4.radar_module.discovery_candidates(source, payload, "https://ancitoscana.it/montagna/") == []
    # A structured archive with no relevant cards must not fall back to its footer.
    empty = payload[payload.index('<div class="e-loop-item"><div'):]
    assert daily_h4.radar_module.discovery_candidates(source, empty, listing) == []


def _test_route_diagnostics_preserve_failures_and_tls() -> None:
    import json
    import os
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    import opportunity_transport_smoke as smoke
    config, _ = daily_h4._compose_runtime_hardened()
    original_run = smoke.subprocess.run
    cwd = Path.cwd()
    def simulated(command, **kwargs):
        assert command[command.index("--proto") + 1] == "=https"
        assert command[command.index("--proto-redir") + 1] == "=https"
        assert "--insecure" not in command and kwargs["timeout"] == 12
        if "--ipv4" in command:
            return SimpleNamespace(returncode=60, stdout='{"http_code":0,"ssl_verify_result":20}', stderr="certificate failure")
        return SimpleNamespace(returncode=0, stdout='{"http_code":403,"remote_ip":"192.0.2.1"}', stderr="")
    try:
        smoke.subprocess.run = simulated
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            assert smoke.diagnose_routes(config) == 0
            report = json.loads(Path("reports/runtime/opportunity-route-diagnostic.json").read_text())
            assert report["diagnosticOnly"] is True
            rows = report["sources"]
            assert {row["sourceId"] for row in rows} == {"anci-toscana", "anci-nazionale", "mim-enti-locali"}
            assert all(row["candidateCount"] == 0 for row in rows)
            assert all(row["http_code"] == 403 for row in rows if row["route"] == "default")
            assert all(row["exitCode"] == 60 and row["ssl_verify_result"] == 20 for row in rows if row["route"] == "ipv4")
    finally:
        os.chdir(cwd)
        smoke.subprocess.run = original_run


def main() -> int:
    _test_route_diagnostics_preserve_failures_and_tls()
    _test_anci_toscana_short_cards_are_isolated()
    _test_annual_archive_follows_current_year()
    _test_chromium_rejects_error_document()
    _test_listing_coverage_status()
    _test_configured_detail_pages_cannot_attest_discovery()
    _test_parallel_prefetch_keeps_budgets_and_cache()
    _test_expired_worker_kills_descendants()
    _test_live_transport_budget_and_journal()
    _test_403_uses_chromium_dom()
    _test_timeout_uses_chromium()
    _test_timeout_uses_reader_after_chromium_failure()
    _test_reader_403_does_not_misattribute_source_failure()
    _test_missing_endpoint_does_not_hide_configuration_drift()
    _test_dns_error_does_not_hide_configuration_drift()
    _test_exhausted_transport_is_source_scoped_network_error()
    _test_probe_exposes_endpoint_diagnostics()
    _test_probe_marks_reader_as_degraded()
    _test_probe_uses_resolved_url_for_relative_links()
    _test_endpoint_content_signature_rejects_unrelated_200_page()
    _test_anci_independent_mirror_survives_national_endpoint_failures()
    _test_anci_news_short_previews_preserve_discovery()
    _test_rss_and_mim_table_keep_individual_notice_links()
    _test_runtime_compose_replaces_stale_sources()
    _test_transport_audit_exposes_endpoint_health()
    print("Discovery resiliente Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
