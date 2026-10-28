#!/usr/bin/env python3
"""Il rumore delle Prefetture non deve bloccare la qualifica dei bandi reali."""
from __future__ import annotations

from opportunity_discovery_noise import classify_signal
from opportunity_review_actions import build_actions

PREF = "https://prefettura.interno.gov.it/it/prefetture/"


def _item(title: str, *, place: str = "terni", deadline: str | None = None) -> dict:
    item = {"url": PREF + place + "/comunicazioni/" + title.lower().replace(" ", "-"),
            "title": title}
    if deadline:
        item["deadline_at"] = deadline
    return item


def test_prefecture_noise() -> None:
    cases = [
        ("Avviso estrazione del 28 Ottobre 2026", "administrative_update"),
        ("Nomina revisore dei conti Enti Locali", "administrative_update"),
        ("Verbale estrazione 2026 Revisori dei Conti Comune di AIELLO CALABRO", "administrative_update"),
        ("Comunicazione distacco energia elettrica del Centralino della Prefettura", "administrative_update"),
        ("Istituzione dell'elenco comunale degli elettori fuori sede", "administrative_update"),
        ("COMUNICATO STAMPA", "administrative_update"),
        ("Accordo Prefettura, Comune e Soprintendenza per Santa Maria della Verità", "administrative_update"),
        ("Avviso pubblico per ricerca immobile Comune di San Venanzo", "procurement_notice"),
        ("Avvisi Pubblici esplorativi di ricerca immobili in locazione", "procurement_notice"),
        ("Affidamento servizio videosorveglianza Progetto Occhio sulla dormiente", "procurement_notice"),
        ("Comunicazione seduta pubblica servizio di sorveglianza armata", "procurement_notice"),
    ]
    for title, expected in cases:
        actual = classify_signal(_item(title), "2026-10-28")
        assert actual == expected, (title, actual, expected)

    # Non tagliare call nazionali reali ripubblicate da Prefetture non lucchesi.
    for title in (
        "Bando di finanziamento per installazione di sistemi di videosorveglianza",
        "Realizzazione sistemi videosorveglianza per i Comuni con fondi statali",
        "Scuole sicure 2026/27",
    ):
        assert classify_signal(_item(title, place="trapani"), "2026-10-28") is None, title
    # Il nuovo avviso esplicito e una riapertura prevalgono sempre sul filtro.
    assert classify_signal(_item("Nomina revisore dei conti Enti Locali", deadline="2026-11-12"), "2026-10-28") is None
    reopened = _item("Avviso pubblico per ricerca immobile: nuova finestra per domande")
    assert classify_signal(reopened, "2026-10-28") is None

    result = build_actions({
        "referenceDate": "2026-10-28",
        "opportunities": [],
        "discoveryQueue": [_item(title) for title, _ in cases],
    })
    assert result["counts"].get("technical", 0) == 0, result["counts"]
    assert result["discardedCount"] == len(cases), result["counts"]


def main() -> int:
    test_prefecture_noise()
    print("Rumore Prefetture: 11 scarti mirati + 5 salvaguardie PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
