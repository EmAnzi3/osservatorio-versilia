#!/usr/bin/env python3
"""Apply validated OpenBDAP and SIOPE histories to the public data model."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
BUDGET_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
SIOPE_PATH = ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json"
TEST_PATH = ROOT / "scripts" / "test_ux_experiment.py"
TEST_V150_PATH = ROOT / "scripts" / "test_release_v150.py"
HISTORY_VERSION = "2026.08.05-local-v1.6.0-bilanci-storici"

SIOPE_COMPONENTS = {
    "siopePayments": "cash_payments",
    "currentPayments": "current_payments",
    "capitalPayments": "capital_payments",
    "cashReceiptsPerResident": "cash_receipts",
    "cashBalancePerResident": "cash_balance",
}


def format_currency(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + "\u00a0€"


def apply_snapshot(
    data: dict,
    snapshot: dict,
    keys: list[str],
    *,
    update_current: bool = False,
) -> None:
    for key in keys:
        source_metric = snapshot["metrics"][key]
        years = [int(year) for year in source_metric["years"]]
        lookup = {row["town"]: row for row in data["metrics"][key]["rows"]}
        for town, row in lookup.items():
            values = [float(source_metric["values"][town][str(year)]) for year in years]
            row["series"] = {"years": years, "values": values} if len(years) >= 2 else None
            if update_current:
                latest = values[-1]
                row["value"] = latest
                row["benchmarkValue"] = latest
                if data["metrics"][key]["meta"].get("unit") == "currency":
                    row["formatted"] = format_currency(latest)

        method = data["metrics"][key]["method"]
        method["coverage"] = f"7/7 per ciascun anno ammesso ({years[0]}–{years[-1]})"
        if update_current:
            method["formula"] = snapshot["formulas"][key]
            method["caveat"] = (
                "Il numeratore è il flusso SIOPE cumulato a dicembre; il denominatore è la popolazione "
                "residente Istat al 1° gennaio dell’anno successivo, applicata in modo uniforme a tutta la serie. "
                "Flussi di cassa e stock finanziari non sono intercambiabili."
            )

    if update_current:
        latest_year = max(int(year) for year in snapshot["selection_rules"]["years"])
        for key in keys:
            component = SIOPE_COMPONENTS[key]
            numerator = sum(
                float(snapshot["raw"][town][str(latest_year)][component])
                for town in snapshot["raw"]
            )
            population = sum(
                float(snapshot["raw"][town][str(latest_year)]["population_resident"])
                for town in snapshot["raw"]
            )
            aggregate = data["metrics"][key].get("aggregate")
            if aggregate is not None:
                aggregate["value"] = numerator / population


def update_tests() -> None:
    text = TEST_PATH.read_text(encoding="utf-8")
    replacements = {
        'require(len(comparable.get("currentRevenueAccruedPerResident", [])) == 2,\n            "I bilanci devono offrire il confronto 2024–2025")':
        'require(len(comparable.get("currentRevenueAccruedPerResident", [])) >= 7,\n            "I bilanci devono offrire una serie storica estesa con copertura 7/7")',
        'require(page.locator(".ux-two-point-row").count() == 7,\n                "Bilanci: il confronto a due punti non contiene sette Comuni")':
        'require(page.locator(".ux-series-group").count() == 7,\n                "Bilanci: lo storico esteso non contiene sette serie comunali")',
        'require("Confronto a due punti 2024–2025" in page.locator(".ux-history-head").inner_text(),\n                "Bilanci: confronto a due anni non riconosciuto")':
        'require("Andamento 2019–2025" in page.locator(".ux-history-head").inner_text(),\n                "Bilanci: intervallo storico esteso non riconosciuto")',
        'require(page.locator(\'.ux-two-point-row[data-history-town="massarosa"].is-selected\').count() == 1,\n                "Bilanci: selezione di Massarosa non applicata")':
        'require(page.locator(\'.ux-series-group[data-history-town="massarosa"].is-selected\').count() == 1,\n                "Bilanci: selezione di Massarosa non applicata")',
    }
    for old, new in replacements.items():
        if new not in text:
            if old not in text:
                raise RuntimeError(f"Aggiornamento test non trovato: {old[:80]}")
            text = text.replace(old, new, 1)

    mobile_old = '''        mobile_page.locator('[data-view-mode="history"]').click()
        require(mobile_page.locator(".ux-two-point-row").count() == 7,
                "Mobile: confronto a due punti incompleto")
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"],
                f"Mobile: overflow orizzontale della pagina {widths}")
        require("€" in mobile_page.locator(".ux-history-card").inner_text(),
                "Mobile: unità monetaria assente nello storico")
'''
    mobile_new = '''        mobile_page.locator('[data-view-mode="history"]').click()
        require(mobile_page.locator(".ux-series-group").count() == 7,
                "Mobile: storico esteso dei bilanci incompleto")
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"],
                f"Mobile: overflow orizzontale della pagina {widths}")
        require("€" in mobile_page.locator(".ux-history-card").inner_text(),
                "Mobile: unità monetaria assente nello storico")
'''
    if mobile_new not in text:
        if mobile_old not in text:
            raise RuntimeError("Blocco test mobile Bilanci non trovato")
        text = text.replace(mobile_old, mobile_new, 1)

    two_point_anchor = '''        require(page.locator('.ux-series-group[data-history-town="massarosa"].is-selected').count() == 1,
                "Bilanci: selezione di Massarosa non applicata")
'''
    two_point_block = two_point_anchor + '''
        page.goto(
            base + "confronta/economia/?indicatore=income",
            wait_until="networkidle",
        )
        page.wait_for_selector(".ux-view-shell")
        page.locator('[data-view-mode="history"]').click()
        require(page.locator(".ux-two-point-row").count() == 7,
                "Economia: confronto a due punti incompleto")
        require("Confronto a due punti 2023–2024" in page.locator(".ux-history-head").inner_text(),
                "Economia: intervallo a due punti non riconosciuto")
'''
    if "Economia: confronto a due punti incompleto" not in text:
        if two_point_anchor not in text:
            raise RuntimeError("Punto di inserimento test a due punti non trovato")
        text = text.replace(two_point_anchor, two_point_block, 1)
    TEST_PATH.write_text(text, encoding="utf-8")

    v150 = TEST_V150_PATH.read_text(encoding="utf-8")
    version_line = f'    "{HISTORY_VERSION}",\n'
    if version_line not in v150:
        anchor = '    "2026.08.05-local-v1.6.0-bilanci",\n'
        if anchor not in v150:
            raise RuntimeError("Whitelist versioni v1.5.0 non riconosciuta")
        v150 = v150.replace(anchor, anchor + version_line, 1)
        TEST_V150_PATH.write_text(v150, encoding="utf-8")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    budget_keys = list(budget["metrics"])
    apply_snapshot(data, budget, budget_keys)
    rigid = data["metrics"]["rigidExpenditureShare"]
    rigid["method"]["caveat"] = (
        "Indicatore ufficiale OpenBDAP. La serie include soltanto gli anni in cui tutti e sette i valori "
        "sono formalmente compresi tra 0 e 100; il 2024 resta escluso per l’anomalia rilevata nel file ufficiale."
    )

    if SIOPE_PATH.exists():
        siope = json.loads(SIOPE_PATH.read_text(encoding="utf-8"))
        apply_snapshot(data, siope, list(siope["metrics"]), update_current=True)

    data["version"] = HISTORY_VERSION
    data["updated"] = "anteprima locale · 5 agosto 2026"
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_tests()
    print("Serie storiche validate applicate al modello del sito.")


if __name__ == "__main__":
    main()
