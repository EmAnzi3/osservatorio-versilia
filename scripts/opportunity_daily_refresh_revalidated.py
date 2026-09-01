#!/usr/bin/env python3
"""Refresh giornaliero con riconferma robusta delle fonti primarie verificate.

Il Radar mantiene i gate esistenti. Questo wrapper interviene solo sul trasporto
della verifica puntuale: i PDF vengono estratti come testo invece di essere
decodificati come HTML e, per le pagine HTML che rifiutano il bot user-agent,
viene tentato un secondo fetch con intestazioni da browser. I required_terms
restano obbligatori; se la fonte non li conferma, il coverage/continuity hold
resta attivo.
"""
from __future__ import annotations

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


def _is_pdf_url(url: str) -> bool:
    return urlsplit(url).path.casefold().endswith(".pdf")


def _fetch_browser_html(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": _BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


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

    # Alcuni portali istituzionali rispondono diversamente al bot UA. Il secondo
    # trasporto non abbassa il gate: i required_terms vengono ricontrollati.
    try:
        html = _fetch_browser_html(url)
        checked = _verify_fetched_payload(entry, today, html)
        if checked[0]:
            return True, "live", None
        if checked[2]:
            errors.append(str(checked[2]))
    except Exception as exc:  # pragma: no cover - dipende dalla rete live
        errors.append(f"HTML browser fallback: {exc}")

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
