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


def _test_html_browser_fallback_rechecks_terms() -> None:
    entry = _entry("https://example.test/bando")
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html

    def fake_verify(entry, today, *, detail_payloads=None, live=True, fallback_max_days=7):
        if detail_payloads:
            payload = detail_payloads[str(entry.get("url"))].casefold()
            missing = [term for term in entry.get("required_terms") or [] if term.casefold() not in payload]
            if not missing:
                return True, "live", None
            return False, "failed", "termini obbligatori non trovati"
        return False, "failed", "HTTP 403 dal trasporto bot"

    try:
        revalidation._ORIGINAL_VERIFY = fake_verify
        revalidation._fetch_browser_html = lambda url, timeout=30: (
            "<html><body>Termine alfa · 30 settembre 2026</body></html>"
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
    assert ok is True, error
    assert status == "live", status
    assert error is None


def _test_no_gate_weakening() -> None:
    entry = _entry("https://example.test/bando")
    original_verify = revalidation._ORIGINAL_VERIFY
    original_fetch = revalidation._fetch_browser_html

    def fake_verify(entry, today, *, detail_payloads=None, live=True, fallback_max_days=7):
        if detail_payloads:
            return False, "failed", "termini obbligatori non trovati"
        return False, "failed", "fonte primaria non verificabile"

    try:
        revalidation._ORIGINAL_VERIFY = fake_verify
        revalidation._fetch_browser_html = lambda url, timeout=30: "<html><body>contenuto diverso</body></html>"
        ok, status, error = revalidation.verify_entry_resilient(
            entry,
            date(2026, 9, 1),
            live=True,
            fallback_max_days=7,
        )
    finally:
        revalidation._ORIGINAL_VERIFY = original_verify
        revalidation._fetch_browser_html = original_fetch
    assert ok is False
    assert status == "failed"
    assert error


def main() -> int:
    _test_direct_pdf_revalidation()
    _test_html_browser_fallback_rechecks_terms()
    _test_no_gate_weakening()
    print("Riconferma fonti primarie Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
