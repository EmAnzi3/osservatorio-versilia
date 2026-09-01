#!/usr/bin/env python3
"""Refresh giornaliero con riconferma robusta delle fonti primarie verificate.

Il Radar mantiene i gate esistenti. Questo wrapper interviene solo sul trasporto
della verifica puntuale: i PDF vengono estratti come testo invece di essere
decodificati come HTML e, per le pagine HTML che rifiutano o degradano il fetch
bot, vengono tentati un fetch browser-like con retry e, come ultima risorsa, un
browser Chromium reale. Per fonti ufficiali note con endpoint primario instabile
può essere usata una pagina, un allegato o un insieme di pagine istituzionali
equivalenti. I required_terms restano obbligatori; se nessuna evidenza ufficiale
li conferma, il coverage/continuity hold resta attivo.
"""
from __future__ import annotations

import time
import urllib.request
from datetime import date
from typing import Any
from urllib.parse import urlsplit

import opportunity_daily_refresh as daily
import opportunity_pdf_evidence as pdf_evidence

_ORIGINAL_VERIFY = daily.radar.core.verify_entry
_BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0 Safari/537.36"
)

# Evidenze istituzionali equivalenti su host alternativi. Sono usate prima del
# trasporto primario per i casi in cui GitHub Actions ha mostrato timeout/502.
_OFFICIAL_ALTERNATE_URLS: dict[str, tuple[str, ...]] = {
    "life-2026-cet-pda": (
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/LIFE-2026-CET-PDA",
    ),
    "pcm-capitale-mare-2027": (
        "https://www.anci.puglia.it/web/2026/07/15/capitale-italiana-del-mare-2027-aperto-il-bando-per-la-candidatura-dei-comuni-costieri-domande-entro-30-settembre-2026/",
        "https://www.ministroprotezionecivileemare.gov.it/it/notizie/mare-musumeci-al-via-selezione-capitale-del-mare-2027/",
        "https://www.statocitta.pcm.gov.it/home/notizie-e-comunicati/2026/capitale-italiana-del-mare-2027-aperte-le-candidature-per-i-comuni-costieri/",
    ),
    "pcm-pari-tratta-bando-8-2026": (
        "https://bandi.regione.piemonte.it/system/files/bando%20DPO-antitratta-8_2026.pdf",
        "https://www.pariopportunita.gov.it/media/002lypuf/bando-antitratta-8_2026.pdf",
    ),
}

# Alcuni fatti della stessa opportunità sono pubblicati su pagine ufficiali
# distinte dello stesso programma. I payload vengono concatenati e poi passati
# allo stesso verificatore, che deve comunque trovare tutti i required_terms.
_OFFICIAL_EVIDENCE_SETS: dict[str, tuple[str, ...]] = {
    "eu-eucf-call-8-2026": (
        "https://www.eucityfacility.eu/calls/call-8",
        "https://www.eucityfacility.eu/news/european-city-facility-announces-new-calls-support-city-investments-green-transition",
    ),
}


def _is_pdf_url(url: str) -> bool:
    return urlsplit(url).path.casefold().endswith(".pdf")


def _fetch_browser_html(url: str, timeout: int = 30, attempts: int = 3) -> str:
    """Fetch HTTP con intestazioni browser e retry breve per errori transitori."""
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": _BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            last_error = exc
            if attempt + 1 < max(1, attempts):
                time.sleep(1.0 + attempt)
    assert last_error is not None
    raise last_error


def _fetch_playwright_text(url: str, timeout_ms: int = 45_000) -> str:
    """Ultimo trasporto: rende la pagina con Chromium e restituisce testo visibile."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=_BROWSER_UA,
            locale="it-IT",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
                "Cache-Control": "no-cache",
            },
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightTimeoutError:
                pass
            try:
                text = page.locator("body").inner_text(timeout=10_000)
            except Exception:
                text = page.content()
            if not text.strip():
                text = page.content()
            return text
        finally:
            context.close()
            browser.close()


def _verify_fetched_payload(
    entry: dict[str, Any],
    today: date,
    payload: str,
) -> tuple[bool, str, str | None]:
    """Valida un payload appena scaricato senza consentire fallback cached."""
    url = str(entry.get("url") or "")
    return _ORIGINAL_VERIFY(
        entry,
        today,
        detail_payloads={url: payload},
        live=False,
        fallback_max_days=-1,
    )


def _fetch_official_payload(url: str) -> str:
    """Scarica una singola evidenza istituzionale con trasporti brevi e robusti."""
    if _is_pdf_url(url):
        return pdf_evidence.fetch_pdf_text(url, max_pages=24, max_chars=120000)
    try:
        return _fetch_browser_html(url, timeout=12, attempts=2)
    except Exception as http_error:
        try:
            return _fetch_playwright_text(url, timeout_ms=30_000)
        except Exception as browser_error:
            raise RuntimeError(f"HTTP: {http_error}; Chromium: {browser_error}") from browser_error


def _verify_official_evidence_set(
    entry: dict[str, Any],
    today: date,
    errors: list[str],
) -> tuple[bool, str, str | None] | None:
    coverage_id = str(entry.get("coverage_id") or "")
    urls = _OFFICIAL_EVIDENCE_SETS.get(coverage_id)
    if not urls:
        return None
    payloads: list[str] = []
    for evidence_url in urls:
        try:
            payloads.append(_fetch_official_payload(evidence_url))
        except Exception as exc:  # pragma: no cover - rete live
            errors.append(f"Set ufficiale {evidence_url}: {exc}")
            return None
    checked = _verify_fetched_payload(entry, today, "\n\n".join(payloads))
    if checked[0]:
        return True, "live", None
    if checked[2]:
        errors.append(f"Set ufficiale: {checked[2]}")
    return None


def _verify_official_alternates(
    entry: dict[str, Any],
    today: date,
    errors: list[str],
) -> tuple[bool, str, str | None] | None:
    """Prova endpoint istituzionali equivalenti senza cambiare i gate documentali."""
    coverage_id = str(entry.get("coverage_id") or "")
    for alternate_url in _OFFICIAL_ALTERNATE_URLS.get(coverage_id, ()):
        try:
            payload = _fetch_official_payload(alternate_url)
            checked = _verify_fetched_payload(entry, today, payload)
            if checked[0]:
                return True, "live", None
            if checked[2]:
                errors.append(f"Fonte ufficiale alternativa {alternate_url}: {checked[2]}")
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            errors.append(f"Fonte ufficiale alternativa {alternate_url}: {exc}")
    return None


def verify_entry_resilient(
    entry: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
    fallback_max_days: int = 7,
) -> tuple[bool, str, str | None]:
    """Riconferma la stessa evidenza primaria con trasporti adatti al contenuto."""
    url = str(entry.get("url") or "")

    if not live or (detail_payloads and url in detail_payloads):
        return _ORIGINAL_VERIFY(
            entry,
            today,
            detail_payloads=detail_payloads,
            live=live,
            fallback_max_days=fallback_max_days,
        )

    errors: list[str] = []
    coverage_id = str(entry.get("coverage_id") or "")

    evidence_set = _verify_official_evidence_set(entry, today, errors)
    if evidence_set is not None:
        return evidence_set

    if coverage_id in _OFFICIAL_ALTERNATE_URLS:
        alternate = _verify_official_alternates(entry, today, errors)
        if alternate is not None:
            return alternate

    if _is_pdf_url(url):
        try:
            text = pdf_evidence.fetch_pdf_text(url, max_pages=24, max_chars=120000)
            checked = _verify_fetched_payload(entry, today, text)
            if checked[0]:
                return True, "live", None
            if checked[2]:
                errors.append(str(checked[2]))
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            errors.append(f"PDF primario: {exc}")

        cached = _ORIGINAL_VERIFY(
            entry,
            today,
            detail_payloads=None,
            live=False,
            fallback_max_days=fallback_max_days,
        )
        if cached[0]:
            return cached
        if cached[2]:
            errors.append(str(cached[2]))
        return False, "failed", "; ".join(dict.fromkeys(errors)) or "fonte PDF primaria non verificabile"

    original = _ORIGINAL_VERIFY(
        entry,
        today,
        detail_payloads=None,
        live=True,
        fallback_max_days=fallback_max_days,
    )
    if original[0] and original[1] == "live":
        return original
    if original[2]:
        errors.append(str(original[2]))

    try:
        html = _fetch_browser_html(url)
        checked = _verify_fetched_payload(entry, today, html)
        if checked[0]:
            return True, "live", None
        if checked[2]:
            errors.append(str(checked[2]))
    except Exception as exc:  # pragma: no cover - dipende dalla rete live
        errors.append(f"HTML browser fallback: {exc}")

    try:
        rendered = _fetch_playwright_text(url)
        checked = _verify_fetched_payload(entry, today, rendered)
        if checked[0]:
            return True, "live", None
        if checked[2]:
            errors.append(str(checked[2]))
    except Exception as exc:  # pragma: no cover - dipende dalla rete/browser live
        errors.append(f"Chromium fallback: {exc}")

    if original[0]:
        return original
    return False, "failed", "; ".join(dict.fromkeys(errors)) or "fonte primaria non verificabile"


def main() -> int:
    daily.radar.core.verify_entry = verify_entry_resilient
    try:
        return daily.main()
    finally:
        daily.radar.core.verify_entry = _ORIGINAL_VERIFY


if __name__ == "__main__":
    raise SystemExit(main())
