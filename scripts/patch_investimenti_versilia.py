#!/usr/bin/env python3
"""Rende coerente il confronto comunale di Investimenti e opere.

I tre indicatori della sezione hanno un aggregato Versilia calcolato sui
numeratori e denominatori elementari. Non devono essere sostituiti dalla media
semplice delle sette percentuali o dei sette valori pro capite.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"


CONFIG = {
    "publicWorks": {
        "comparisonDifference": "absolute",
        "comparisonLabel": "valore Versilia",
        "comparisonOverline": "Rispetto al valore Versilia",
        "comparisonNote": (
            "Il riferimento Versilia divide il valore complessivo delle opere "
            "monitorate per i residenti dei sette Comuni; non è la media semplice "
            "dei sette valori comunali."
        ),
    },
    "pnrrFunding": {
        "comparisonDifference": "absolute",
        "comparisonLabel": "valore Versilia",
        "comparisonOverline": "Rispetto al valore Versilia",
        "comparisonNote": (
            "Il riferimento Versilia divide le risorse complessive dei progetti "
            "selezionati per i residenti dei sette Comuni; non è la media semplice "
            "dei sette valori comunali."
        ),
    },
    "pnrrConcluded": {
        "comparisonDifference": "percentagePoints",
        "comparisonLabel": "quota Versilia",
        "comparisonOverline": "Rispetto alla quota Versilia",
        "comparisonNote": (
            "Il riferimento Versilia è la quota complessiva di progetti conclusi "
            "(74 su 101); non è la media semplice delle sette percentuali comunali."
        ),
    },
}


def main() -> int:
    data = json.loads(SITE_PATH.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})
    for key, config in CONFIG.items():
        metric = metrics.get(key)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Indicatore canonico mancante: {key}")
        metric.setdefault("meta", {}).update(
            {
                "comparisonReference": "aggregate",
                **config,
            }
        )

    SITE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Investimenti e opere: confronto riallineato agli aggregati Versilia "
        "(rapporti dei totali; scarti in euro o percentuale)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
