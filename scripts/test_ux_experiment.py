#!/usr/bin/env python3
"""Controlli dell’esperimento UX su sezioni e serie storiche comparative."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data" / "site-data.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def common_years(metric: dict) -> list[str]:
    sets: list[set[str]] = []
    for row in metric.get("rows", []):
        series = row.get("series") or {}
        years = series.get("years") or []
        values = series.get("values") or []
        valid = {
            str(year)
            for year, value in zip(years, values, strict=False)
            if isinstance(value, (int, float))
        }
        sets.append(valid)
    if not sets:
        return []
    return sorted(set.intersection(*sets), key=lambda value: int(value))


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    for name in (
        "ux-experiment.css",
        "ux-accordion.js",
        "ux-history-core.js",
        "ux-history.js",
    ):
        require((DIST / "assets" / name).exists(), f"Asset UX mancante: {name}")

    comparable = {
        key: common_years(metric)
        for key, metric in data["metrics"].items()
        if len(common_years(metric)) >= 2
    }
    require(len(comparable) >= 20, "Troppo pochi indicatori dispongono di uno storico comparabile")
    require(len(comparable.get("currentRevenueAccruedPerResident", [])) == 2,
            "I bilanci devono offrire il confronto 2024–2025")
    require(len(comparable.get("population", [])) >= 3,
            "La popolazione deve offrire una serie storica estesa")

    pages = {
        "bilanci": DIST / "confronta" / "bilanci" / "index.html",
        "massarosa": DIST / "comuni" / "massarosa" / "index.html",
    }
    for label, path in pages.items():
        require(path.exists(), f"Pagina non generata: {label}")
        text = path.read_text(encoding="utf-8")
        for token in (
            "assets/ux-experiment.css",
            "assets/ux-accordion.js",
            "assets/ux-history-core.js",
            "assets/ux-history.js",
            "ux-section-toggle",
            "ux-view-shell",
            'data-view-mode="current"',
            'data-view-mode="history"',
        ):
            require(token in text, f"{label}: manca {token}")

    bilanci = pages["bilanci"].read_text(encoding="utf-8")
    require("Confronto 2024–2025" in bilanci, "Bilanci: confronto a due anni non prerenderizzato")
    require(bilanci.count("data-history-town=") == 7,
            "Bilanci: lo storico non contiene sette serie comunali")

    massarosa = pages["massarosa"].read_text(encoding="utf-8")
    require("ux-comparison-bars" in massarosa,
            "Scheda comunale: confronto attuale non prerenderizzato")
    require("ux-history-chart has-selection" in massarosa,
            "Scheda comunale: comune aperto non evidenziato nello storico")

    print(
        "Esperimento UX validato: sezioni espandibili, vista attuale e storico comparato "
        f"su {len(comparable)} indicatori."
    )


if __name__ == "__main__":
    main()
