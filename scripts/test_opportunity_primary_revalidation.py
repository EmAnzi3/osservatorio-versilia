#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

import opportunity_daily_refresh_revalidated as revalidation


def _entry(url: str) -> dict:
    return {
        "coverage_id": "test-primary",
        "source_id": "test-source",
        "title": "Fonte primaria di test",
        "url": url,
        "required_terms": ["termine alfa", "30 settembre 2026"],
        "evidence_verified_at": "2026-08-01",
        "allow_recent_evidence_fallback": True,
    }


def _test_direct_pdf_revalidation() -> None:
    entry = _entry("https://example.test/bando.pdf")
    original_loader = revalidation.pdf_evidence.fetch_pdf_text
    try:
        revalidation.pdf_evidence.fetch_pdf_text = lambda *args, **kwargs: (
            "Documento ufficiale. Termine alfa. Scadenza 30 settembre 2026."
        )
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation.pdf_evidence.fetch_pdf_text = original_loader
    assert ok is True, error
    assert status == "live", status
    assert error is None


def _fake_verify(entry, today, *, detail_payloads=None, live=True, fallback_max_days=7):
    if detail_payloads:
        payload = detail_payloads[str(entry.get("url"))].casefold()
        missing = [term for term in entry.get("required_terms") or [] if term.casefold() not in payload]
        if not missing:
            return True, "live", None
        return False, "failed", "termini obbligatori non trovati"
    return False, "failed", "HTTP 403 dal trasporto bot"


def _test_html_browser_fallback_rechecks_terms() -> None:
    entry = _entry("https://example.test/bando")
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    try:
        revalidation._ORIGINAL_VERIFY = _fake_verify
        revalidation._fetch_browser_html = lambda url, timeout=30, attempts=3: (
            "<html><body>Termine alfa · 30 settembre 2026</body></html>"
        )
        revalidation._fetch_playwright_text = lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Chromium non deve essere chiamato se il fetch HTTP è sufficiente")
        )
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
    assert ok is True, error
    assert status == "live", status
    assert error is None


def _test_playwright_fallback_rechecks_terms() -> None:
    entry = _entry("https://example.test/dynamic")
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    try:
        revalidation._ORIGINAL_VERIFY = _fake_verify
        revalidation._fetch_browser_html = lambda *args, **kwargs: "pagina intermedia senza evidenza"
        revalidation._fetch_playwright_text = lambda *args, **kwargs: (
            "Pagina resa da Chromium: termine alfa · 30 settembre 2026"
        )
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
    assert ok is True, error
    assert status == "live", status
    assert error is None


def _test_official_alternate_rechecks_same_terms() -> None:
    entry = _entry("https://primary.example.test/pda")
    entry["coverage_id"] = "life-2026-cet-pda"
    entry["required_terms"] = ["LIFE-2026-CET-PDA", "Open", "16 September 2026"]
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    calls: list[str] = []

    def browser_fetch(url: str, timeout: int = 30, attempts: int = 3) -> str:
        calls.append(url)
        return "pagina senza evidenza sufficiente"

    def rendered(url: str, timeout_ms: int = 45_000) -> str:
        calls.append(url)
        if "funding-tenders" in url:
            return "LIFE-2026-CET-PDA · Open · 16 September 2026"
        return "pagina primaria senza evidenza sufficiente"

    try:
        revalidation._ORIGINAL_VERIFY = _fake_verify
        revalidation._fetch_browser_html = browser_fetch
        revalidation._fetch_playwright_text = rendered
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright

    assert ok is True, error
    assert status == "live", status
    assert error is None
    assert any("funding-tenders" in url for url in calls), calls


def _test_pcm_html_alternate_rechecks_same_terms() -> None:
    entry = _entry("https://primary.example.test/capitale-mare")
    entry["coverage_id"] = "pcm-capitale-mare-2027"
    entry["required_terms"] = ["capitale italiana del mare", "comuni costieri", "30 settembre 2026"]
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text

    def browser_fetch(url: str, timeout: int = 30, attempts: int = 3) -> str:
        if "statocitta.pcm.gov.it" in url:
            return "Capitale italiana del mare 2027 · Comuni costieri · 30 settembre 2026"
        return "pagina primaria senza evidenza sufficiente"

    try:
        revalidation._ORIGINAL_VERIFY = _fake_verify
        revalidation._fetch_browser_html = browser_fetch
        revalidation._fetch_playwright_text = lambda *args, **kwargs: "pagina primaria senza evidenza sufficiente"
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright

    assert ok is True, error
    assert status == "live", status
    assert error is None


def _test_pcm_pdf_alternate_rechecks_same_terms() -> None:
    entry = _entry("https://primary.example.test/bando-8")
    entry["coverage_id"] = "pcm-pari-tratta-bando-8-2026"
    entry["required_terms"] = ["Bando n. 8/2026", "enti locali", "30 settembre 2026"]
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    original_pdf = revalidation.pdf_evidence.fetch_pdf_text

    try:
        revalidation._ORIGINAL_VERIFY = _fake_verify
        revalidation._fetch_browser_html = lambda *args, **kwargs: "pagina primaria senza evidenza sufficiente"
        revalidation._fetch_playwright_text = lambda *args, **kwargs: "pagina primaria senza evidenza sufficiente"
        revalidation.pdf_evidence.fetch_pdf_text = lambda *args, **kwargs: (
            "Bando n. 8/2026 · enti locali · termine 30 settembre 2026"
        )
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
        revalidation.pdf_evidence.fetch_pdf_text = original_pdf

    assert ok is True, error
    assert status == "live", status
    assert error is None


def _test_verified_detail_uses_direct_evidence_after_listing_loss() -> None:
    entry = {
        "rule_id": "mic-jazz-2027",
        "source_id": "mic-spettacolo",
        "title": "Bando per la promozione della musica Jazz 2027",
        "url": "https://example.test/jazz",
        "required_terms": ["autonomie territoriali", "10 settembre 2026", "16:00", "35 mila euro"],
    }
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    try:
        revalidation._fetch_browser_html = lambda *args, **kwargs: "pagina indice/intermedia senza il bando"
        revalidation._fetch_playwright_text = lambda *args, **kwargs: (
            "Bando musica jazz. Autonomie territoriali. 35 mila euro. "
            "Domande entro le ore 16:00 del 10 settembre 2026."
        )
        text = revalidation.verified_detail_text_resilient(
            revalidation.daily.radar.radar,
            entry,
            None,
            True,
        )
    finally:
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
    assert text is not None
    assert "10 settembre 2026" in text


def _test_verified_detail_does_not_weaken_required_terms() -> None:
    entry = {
        "rule_id": "mic-jazz-2027",
        "source_id": "mic-spettacolo",
        "title": "Bando per la promozione della musica Jazz 2027",
        "url": "https://example.test/jazz",
        "required_terms": ["autonomie territoriali", "10 settembre 2026", "16:00", "35 mila euro"],
    }
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text
    try:
        revalidation._fetch_browser_html = lambda *args, **kwargs: "pagina senza termini"
        revalidation._fetch_playwright_text = lambda *args, **kwargs: "ancora senza evidenza completa"
        text = revalidation.verified_detail_text_resilient(
            revalidation.daily.radar.radar,
            entry,
            None,
            True,
        )
    finally:
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
    assert text is None


def _test_no_gate_weakening() -> None:
    entry = _entry("https://example.test/bando")
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html
    original_playwright = revalidation._fetch_playwright_text

    def always_fail(entry, today, *, detail_payloads=None, live=True, fallback_max_days=7):
        if detail_payloads:
            return False, "failed", "termini obbligatori non trovati"
        return False, "failed", "fonte primaria non verificabile"

    try:
        revalidation._ORIGINAL_VERIFY = always_fail
        revalidation._fetch_browser_html = lambda *args, **kwargs: "<html><body>contenuto diverso</body></html>"
        revalidation._fetch_playwright_text = lambda *args, **kwargs: "contenuto reso ma ancora privo dei termini"
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
        revalidation._fetch_playwright_text = original_playwright
    assert ok is False
    assert status == "failed"
    assert error


def _test_entrypoint_delegation() -> None:
    original_main = revalidation.daily.main
    original_verify = revalidation.daily.radar.core.verify_entry
    original_detail = revalidation.v03_post._verified_text
    observed: dict[str, bool] = {}

    def fake_daily_main() -> int:
        observed["verify_patched"] = revalidation.daily.radar.core.verify_entry is revalidation.verify_entry_resilient
        observed["detail_patched"] = revalidation.v03_post._verified_text is revalidation.verified_detail_text_resilient
        return 0

    try:
        revalidation.daily.main = fake_daily_main
        assert revalidation.main() == 0
    finally:
        revalidation.daily.main = original_main
        revalidation.daily.radar.core.verify_entry = original_verify
        revalidation.v03_post._verified_text = original_detail

    assert observed.get("verify_patched") is True
    assert observed.get("detail_patched") is True
    assert revalidation.daily.radar.core.verify_entry is original_verify
    assert revalidation.v03_post._verified_text is original_detail


def main() -> int:
    _test_direct_pdf_revalidation()
    _test_html_browser_fallback_rechecks_terms()
    _test_playwright_fallback_rechecks_terms()
    _test_official_alternate_rechecks_same_terms()
    _test_pcm_html_alternate_rechecks_same_terms()
    _test_pcm_pdf_alternate_rechecks_same_terms()
    _test_verified_detail_uses_direct_evidence_after_listing_loss()
    _test_verified_detail_does_not_weaken_required_terms()
    _test_no_gate_weakening()
    _test_entrypoint_delegation()
    print("Riconferma fonti primarie Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
