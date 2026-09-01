#!/usr/bin/env python3
"""Refresh giornaliero con riconferma robusta delle fonti primarie verificate.

Il Radar mantiene i gate esistenti. Questo wrapper interviene solo sul trasporto
della verifica puntuale: i PDF vengono estratti come testo invece di essere
decodificati come HTML e, per le pagine HTML che rifiutano o degradano il fetch
bot, vengono tentati un fetch browser-like con retry e, come ultima risorsa, un
browser Chromium reale. Per fonti ufficiali note con endpoint primario instabile
può essere usata una seconda pagina istituzionale equivalente. I required_terms
restano obbligatori; se nessuna fonte ufficiale li conferma, il coverage/continuity
hold resta attivo.
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

# Seconda evidenza ufficiale, usata solo quando l'endpoint CINEA primario non
# riesce a riconfermare il topic. Il Funding & Tenders Portal è il portale
# istituzionale UE della stessa call e viene sottoposto agli stessi required_terms.
_OFFICIAL_ALTERNATE_URLS: dict[str, tuple[str, ...]] = {
    "life-2026-cet-pda": (
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/LIFE-2026-CET-PDA",
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
    """Ultimo trasporto: rende la pagina con Chromium e restituisce testo visibile.

    Chromium può proseguire anche in presenza di un certificato TLS mal configurato
    dalla fonte. Questo non rende l'evidenza automaticamente valida: il payload
    ottenuto deve comunque superare integralmente i required_terms già verificati.
    """
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
                # Molti portali mantengono connessioni analytics aperte: il DOM
                # già caricato è sufficiente per verificare i termini obbligatori.
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


def _verify_official_alternates(
    entry: dict[str, Any],
    today: date,
    errors: list[str],
) -> tuple[bool, str, str | None] | None:
    """Prova endpoint istituzionali equivalenti senza cambiare i gate documentali."""
    coverage_id = str(entry.get("coverage_id") or "")
    for alternate_url in _OFFICIAL_ALTERNATE_URLS.get(coverage_id, ()):
        try:
            rendered = _fetch_playwright_text(alternate_url, timeout_ms=60_000)
            checked = _verify_fetched_payload(entry, today, rendered)
            if checked[0]:
                return True, "live", None
            if checked[2]:
                errors.append(f"Fonte ufficiale alternativa: {checked[2]}")
        except Exception as exc:  # pragma: no cover - dipende dalla rete/browser live
            errors.append(f"Fonte ufficiale alternativa: {exc}")
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

    # Fixture/backtest e modalità non-live: comportamento originale, senza sorprese.
    if not live or (detail_payloads and url in detail_payloads):
        return _ORIGINAL_VERIFY(
            entry,
            today,
            detail_payloads=detail_payloads,
            live=live,
            fallback_max_days=fallback_max_days,
        )

    errors: list[str] = []

    if _is_pdf_url(url):
        # Il fetch HTML storico decodificava i byte PDF come UTF-8: i termini
        # obbligatori non potevano essere trovati. Qui estraiamo testo reale.
        try:
            text = pdf_evidence.fetch_pdf_text(url, max_pages=24, max_chars=120000)
            checked = _verify_fetched_payload(entry, today, text)
            if checked[0]:
                return True, "live", None
            if checked[2]:
                errors.append(str(checked[2]))
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            errors.append(f"PDF primario: {exc}")

        # Se l'estrazione live fallisce, resta ammesso esclusivamente il fallback
        # temporaneo già previsto dal contratto; nessuna estensione della grace.
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

    # Primo tentativo invariato: conserva il comportamento collaudato del motore.
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

    # Secondo trasporto: HTTP browser-like con retry. Il gate non cambia:
    # i required_terms vengono sempre ricontrollati dal verificatore originale.
    try:
        html = _fetch_browser_html(url)
        checked = _verify_fetched_payload(entry, today, html)
        if checked[0]:
            return True, "live", None
        if checked[2]:
            errors.append(str(checked[2]))
    except Exception as exc:  # pragma: no cover - dipende dalla rete live
        errors.append(f"HTML browser fallback: {exc}")

    # Terzo trasporto: Chromium reale per portali dinamici/anti-bot o TLS mal
    # configurato. Anche qui una pagina viene accettata solo se contiene tutti
    # i required_terms, quindi nessun gate documentale viene indebolito.
    try:
        rendered = _fetch_playwright_text(url)
        checked = _verify_fetched_payload(entry, today, rendered)
        if checked[0]:
            return True, "live", None
        if checked[2]:
            errors.append(str(checked[2]))
    except Exception as exc:  # pragma: no cover - dipende dalla rete/browser live
        errors.append(f"Chromium fallback: {exc}")

    # Per casi esplicitamente mappati, prova una seconda pagina ufficiale della
    # stessa opportunità. È accettata solo se soddisfa gli stessi required_terms.
    alternate = _verify_official_alternates(entry, today, errors)
    if alternate is not None:
        return alternate

    # Se la verifica robusta non riconferma la fonte, l'unico comportamento
    # permissivo resta il cached_recent originale entro la sua finestra prevista.
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
