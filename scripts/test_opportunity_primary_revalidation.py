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
    observed: dict[str, bool] = {}

    def fake_daily_main() -> int:
        observed["patched"] = revalidation.daily.radar.core.verify_entry is revalidation.verify_entry_resilient
        return 0

    try:
        revalidation.daily.main = fake_daily_main
        assert revalidation.main() == 0
    finally:
        revalidation.daily.main = original_main
        revalidation.daily.radar.core.verify_entry = original_verify

    assert observed.get("patched") is True
    assert revalidation.daily.radar.core.verify_entry is original_verify


def main() -> int:
    _test_direct_pdf_revalidation()
    _test_html_browser_fallback_rechecks_terms()
    _test_playwright_fallback_rechecks_terms()
    _test_no_gate_weakening()
    _test_entrypoint_delegation()
    print("Riconferma fonti primarie Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
