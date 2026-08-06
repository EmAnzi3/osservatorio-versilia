#!/usr/bin/env python3
"""Apply the final manual-review corrections for the private v1.6.0 preview."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
RELEASE_TEST_PATH = ROOT / "scripts" / "test_release_v160.py"
UX_TEST_PATH = ROOT / "scripts" / "test_ux_experiment.py"


def patch_rigid_expenditure_history() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    metric = data["metrics"]["rigidExpenditureShare"]
    for row in metric["rows"]:
        row.pop("series", None)
    metric["method"]["caveat"] = (
        "Indicatore ufficiale OpenBDAP. Nei file 2023 e 2024 il valore di Camaiore è "
        "formalmente anomalo (3100 e 3199). Per evitare di collegare come continua una serie "
        "interrotta, lo storico non viene pubblicato; resta disponibile il valore 2025."
    )
    metric["method"]["coverage"] = (
        "Valore corrente 2025 con copertura 7/7; storico non pubblicato per discontinuità della fonte."
    )
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_release_test() -> None:
    text = RELEASE_TEST_PATH.read_text(encoding="utf-8")
    marker = "Spese rigide: lo storico discontinuo non deve essere pubblicato"
    if marker not in text:
        old = '''            if len(source_years) >= 2:
                require(row["series"]["years"] == source_years, f"Serie anni errata per {key} {town}")
                require(len(row["series"]["values"]) == len(source_years), f"Serie valori incompleta per {key} {town}")
                for year, value in zip(source_years, row["series"]["values"], strict=True):
                    close(value, expected_value(key, town, year), f"{key} {town} {year}")
            else:
                require(row["series"] is None, f"Serie non ammessa per {key} {town}")
'''
        new = '''            if key == "rigidExpenditureShare":
                require(not row.get("series"),
                        "Spese rigide: lo storico discontinuo non deve essere pubblicato")
            elif len(source_years) >= 2:
                require(row["series"]["years"] == source_years, f"Serie anni errata per {key} {town}")
                require(len(row["series"]["values"]) == len(source_years), f"Serie valori incompleta per {key} {town}")
                for year, value in zip(source_years, row["series"]["values"], strict=True):
                    close(value, expected_value(key, town, year), f"{key} {town} {year}")
            else:
                require(row["series"] is None, f"Serie non ammessa per {key} {town}")
'''
        if old not in text:
            raise RuntimeError("Blocco di verifica delle serie Bilanci non trovato")
        text = text.replace(old, new, 1)

        anchor = '''    require(len(rigid_years) >= 2, "Serie valida delle spese rigide troppo corta")
    for town in TOWNS:
        for year in rigid_years:
            require(0 <= expected_value("rigidExpenditureShare", town, year) <= 100, f"Spese rigide fuori scala: {town} {year}")
'''
        replacement = anchor + '''    require(all(not row.get("series") for row in DATA["metrics"]["rigidExpenditureShare"]["rows"]),
            "Spese rigide: serie pubblicata nonostante la discontinuità")
    require("storico non viene pubblicato" in DATA["metrics"]["rigidExpenditureShare"]["method"]["caveat"],
            "Spese rigide: motivazione metodologica assente")
'''
        if anchor not in text:
            raise RuntimeError("Blocco di audit delle spese rigide non trovato")
        text = text.replace(anchor, replacement, 1)
        RELEASE_TEST_PATH.write_text(text, encoding="utf-8")


def patch_ux_test() -> None:
    text = UX_TEST_PATH.read_text(encoding="utf-8")
    background_marker = "Sfondo storico diverso dal pannello del valore attuale"
    if background_marker not in text:
        old = '''        page.locator('[data-view-mode="history"]').click()
        require(page.locator('[data-view-mode="history"].active').count() == 1,
                "Bilanci: selettore storico non attivato")
'''
        new = '''        current_background = page.locator(".topic-bars").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        page.locator('[data-view-mode="history"]').click()
        require(page.locator('[data-view-mode="history"].active').count() == 1,
                "Bilanci: selettore storico non attivato")
        history_background = page.locator(".ux-history-card").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        require(history_background == current_background,
                f"Sfondo storico diverso dal pannello del valore attuale: {history_background} != {current_background}")
'''
        if old not in text:
            raise RuntimeError("Punto di inserimento del controllo sfondo non trovato")
        text = text.replace(old, new, 1)

        anchor = '''        require("Confronto a due punti 2023–2024" in page.locator(".ux-history-head").inner_text(),
                "Economia: intervallo a due punti non riconosciuto")

'''
        block = anchor + '''        page.goto(
            base + "confronta/bilanci/?indicatore=rigidExpenditureShare",
            wait_until="networkidle",
        )
        page.wait_for_selector(".ux-view-shell")
        require(page.locator('[data-view-mode="history"]').is_disabled(),
                "Spese rigide: la vista storica deve restare disabilitata")

'''
        if anchor not in text:
            raise RuntimeError("Punto di inserimento del controllo spese rigide non trovato")
        text = text.replace(anchor, block, 1)
        UX_TEST_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    patch_rigid_expenditure_history()
    patch_release_test()
    patch_ux_test()
    print("Correzioni della verifica manuale v1.6.0 applicate.")


if __name__ == "__main__":
    main()
