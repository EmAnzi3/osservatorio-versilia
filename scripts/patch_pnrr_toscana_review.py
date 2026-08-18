#!/usr/bin/env python3
"""Correzioni di revisione per la bozza PNRR Toscana.

Lo script viene eseguito subito dopo ``materialize_pnrr_toscana_draft.py`` e
prima della build statica. Non introduce nuovi indicatori: riallinea righe e
aggregati Versilia alla stessa fotografia regionale già validata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path("data/site-data.json")


def rows_by_code(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    return {
        str(row.get("code")): row
        for row in rows
        if isinstance(row, dict) and row.get("code")
    }


def fmt_currency(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + "\u00a0€"


def fmt_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    metrics = data.get("metrics")
    deep = data.get("pnrrDeepDive")
    if not isinstance(metrics, dict) or not isinstance(deep, dict):
        raise RuntimeError("Bozza PNRR Toscana non materializzata")

    population = rows_by_code(metrics["population"])
    funding_rows = rows_by_code(metrics["pnrrFunding"])
    concluded_rows = rows_by_code(metrics["pnrrConcluded"])
    total_population = sum(float(row["value"]) for row in population.values())
    totals = deep["totals"]
    total_projects = int(totals["projects"])
    total_concluded = int(totals["concluded"])
    total_funding = float(totals["funding"])

    if total_projects != 101 or total_concluded != 74:
        raise RuntimeError(
            f"Perimetro PNRR inatteso: {total_projects} progetti / {total_concluded} fase 5"
        )
    if total_population <= 0:
        raise RuntimeError("Popolazione Versilia non valida")

    deep_by_code = {str(row["code"]): row for row in deep["towns"]}
    for code, town in deep_by_code.items():
        pop = float(population[code]["value"])
        funding_value = float(town["funding"]) / pop
        concluded_value = float(town["concluded"]) / float(town["projects"]) * 100.0

        funding_rows[code]["value"] = funding_value
        funding_rows[code]["formatted"] = fmt_currency(funding_value)
        funding_rows[code]["benchmarkValue"] = funding_value

        concluded_rows[code]["value"] = concluded_value
        concluded_rows[code]["formatted"] = fmt_percent(concluded_value)
        concluded_rows[code]["benchmarkValue"] = concluded_value

    funding = metrics["pnrrFunding"].setdefault("aggregate", {})
    funding.update(
        {
            "value": total_funding / total_population,
            "label": "Versilia · risorse PNRR per residente",
            "note": (
                "Quota PNRR complessiva dei 101 progetti divisa per i residenti "
                "dei sette comuni."
            ),
        }
    )

    concluded = metrics["pnrrConcluded"].setdefault("aggregate", {})
    concluded.update(
        {
            "value": total_concluded / total_projects * 100.0,
            "label": "Versilia · 74 su 101",
            "note": (
                "74 progetti su 101 risultano nella macrofase ReGiS 5. conclusione "
                "nella fotografia dell'11 agosto 2026."
            ),
        }
    )

    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "PNRR riallineato: "
        f"Versilia {total_concluded}/{total_projects} = "
        f"{total_concluded / total_projects * 100:.4f}% · "
        f"€{total_funding / total_population:.4f}/residente · righe 7/7 aggiornate"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
