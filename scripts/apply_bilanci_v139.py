#!/usr/bin/env python3
"""Applica la snapshot Bilanci v1.39 al catalogo pubblico senza accesso rete.

Questo script è un overlay di release: legge esclusivamente la snapshot
versionata `data/source-snapshots/bilanci-v139.json`, aggiunge i sei indicatori
approvati e lascia intatti gli indicatori Bilanci già pubblicati. Viene eseguito
nella catena di build dopo la v1.38.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/site-data.json"
REGISTRY_PATH = ROOT / "data/source-registry.json"
SNAPSHOT_PATH = ROOT / "data/source-snapshots/bilanci-v139.json"
PORTAL_URL = "https://openbdap.rgs.mef.gov.it/it/FET/Analizza"

METRICS = {
    "fcdePerResident": {
        "label": "Fondo crediti di dubbia esigibilità per residente",
        "shortLabel": "FCDE",
        "description": "Accantonamento al Fondo crediti di dubbia esigibilità al 31 dicembre, rapportato alla popolazione residente.",
        "formula": "FCDE al 31 dicembre / popolazione residente",
        "caveat": "Il FCDE è un accantonamento prudenziale del risultato di amministrazione a presidio del rischio di mancata riscossione; non equivale alla quota di crediti che il Comune sa di non incassare.",
        "aggregate_note": "Somma del FCDE dei sette Comuni rapportata alla popolazione complessiva.",
    },
    "yearEndCashFundPerResident": {
        "label": "Fondo di cassa al 31 dicembre per residente",
        "shortLabel": "Fondo cassa finale",
        "description": "Consistenza del fondo di cassa al 31 dicembre, rapportata alla popolazione residente.",
        "formula": "fondo di cassa al 31 dicembre / popolazione residente",
        "caveat": "È lo stock complessivo di cassa a fine esercizio: può comprendere somme vincolate e non coincide con la sola cassa libera o immediatamente spendibile.",
        "aggregate_note": "Somma del fondo di cassa finale dei sette Comuni rapportata alla popolazione complessiva.",
    },
    "generalAdministrationMissionExpenditurePerResident": {
        "label": "Spesa impegnata per servizi istituzionali e generali per residente",
        "shortLabel": "Servizi generali",
        "description": "Impegni della Missione 01 «Servizi istituzionali, generali e di gestione», rapportati ai residenti.",
        "formula": "impegni Missione 01 / popolazione residente",
        "caveat": "La classificazione comprende spesa corrente e in conto capitale; organizzazione interna, servizi associati e investimenti straordinari incidono sul confronto.",
        "aggregate_note": "Totale degli impegni Missione 01 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "territorialPlanningMissionExpenditurePerResident": {
        "label": "Spesa impegnata per assetto del territorio ed edilizia abitativa per residente",
        "shortLabel": "Assetto territorio",
        "description": "Impegni della Missione 08 «Assetto del territorio ed edilizia abitativa», rapportati ai residenti.",
        "formula": "impegni Missione 08 / popolazione residente",
        "caveat": "La classificazione comprende spesa corrente e in conto capitale; programmi pluriennali e investimenti straordinari possono rendere i singoli anni molto variabili.",
        "aggregate_note": "Totale degli impegni Missione 08 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "civilProtectionMissionExpenditurePerResident": {
        "label": "Spesa impegnata per soccorso civile per residente",
        "shortLabel": "Soccorso civile",
        "description": "Impegni della Missione 11 «Soccorso civile», rapportati ai residenti.",
        "formula": "impegni Missione 11 / popolazione residente",
        "caveat": "Il valore riflette la classificazione contabile comunale; gestione associata, emergenze e investimenti straordinari possono incidere sul confronto annuale.",
        "aggregate_note": "Totale degli impegni Missione 11 dei sette Comuni rapportato alla popolazione complessiva.",
    },
    "economicDevelopmentMissionExpenditurePerResident": {
        "label": "Spesa impegnata per sviluppo economico e competitività per residente",
        "shortLabel": "Sviluppo economico",
        "description": "Impegni della sola Missione 14 «Sviluppo economico e competitività», rapportati ai residenti.",
        "formula": "impegni Missione 14 / popolazione residente",
        "caveat": "Questo indicatore isola la Missione 14. La serie storica già pubblicata «Turismo e sviluppo» resta invece la somma delle Missioni 07 e 14 e non viene modificata.",
        "aggregate_note": "Totale degli impegni Missione 14 dei sette Comuni rapportato alla popolazione complessiva.",
    },
}

EXCLUDED = {"energyMissionExpenditurePerResident", "liquidityManagementProfile"}
LEGACY_KEY = "tourismDevelopmentMissionExpenditurePerResident"


def format_euro(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") + "\u00a0€"


def add_after(items: list[str], anchor: str, additions: list[str]) -> list[str]:
    clean = [item for item in items if item not in additions]
    if anchor not in clean:
        raise RuntimeError(f"Bilanci v1.39: anchor mancante: {anchor}")
    pos = clean.index(anchor) + 1
    return clean[:pos] + additions + clean[pos:]


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    if snapshot.get("version") != "bilanci-v139":
        raise RuntimeError("Snapshot Bilanci v1.39 inattesa")
    if set(snapshot.get("series", {})) != set(METRICS):
        raise RuntimeError("Snapshot Bilanci v1.39: set metriche inatteso")
    for key in EXCLUDED:
        if key in data.get("metrics", {}):
            raise RuntimeError(f"Indicatore escluso già presente: {key}")

    legacy_before = json.dumps(data["metrics"][LEGACY_KEY], ensure_ascii=False, sort_keys=True)
    population_rows = data["metrics"]["population"]["rows"]
    town_meta = {row["town"]: row for row in population_rows}
    expected_towns = set(town_meta)

    for key, spec in METRICS.items():
        source = snapshot["series"][key]
        if source.get("year") != "2025":
            raise RuntimeError(f"{key}: ultimo anno inatteso")
        towns = source.get("towns", {})
        if set(towns) != expected_towns:
            raise RuntimeError(f"{key}: copertura comunale snapshot inattesa")

        rows = []
        common_years = None
        for town in town_meta:
            series = towns[town]
            years = list(series["years"])
            values = list(series["values"])
            if not years or years[-1] != 2025 or len(years) != len(values):
                raise RuntimeError(f"{key}/{town}: serie incoerente")
            if common_years is None:
                common_years = years
            elif years != common_years:
                raise RuntimeError(f"{key}: anni non omogenei tra Comuni")
            latest = float(values[-1])
            base = town_meta[town]
            rows.append({
                "town": town,
                "code": base["code"],
                "slug": base["slug"],
                "value": latest,
                "formatted": format_euro(latest),
                "series": {"years": years, "values": values},
                "normalized": None,
                "benchmarkValue": latest,
            })

        coverage = snapshot["coverage"][key]
        if list(coverage["included_years"]) != common_years:
            raise RuntimeError(f"{key}: coverage e serie non coincidono")

        data["metrics"][key] = {
            "meta": {
                "key": key,
                "theme": "bilanci",
                "label": spec["label"],
                "shortLabel": spec["shortLabel"],
                "description": spec["description"],
                "unit": "currency",
                "year": "2025",
                "source": "Ragioneria generale dello Stato — OpenBDAP",
                "polarity": "neutral",
            },
            "sourceUrl": PORTAL_URL,
            "rows": rows,
            "aggregate": {
                "value": float(source["aggregate"]),
                "label": "Valore pro capite Versilia",
                "note": spec["aggregate_note"],
            },
            "normalizedAggregate": None,
            "method": {
                "type": "Elaborazione Osservatorio su dati ufficiali",
                "formula": spec["formula"],
                "caveat": spec["caveat"],
                "coverage": (
                    f"7/7 per ciascun anno pubblicato ({common_years[0]}–{common_years[-1]})"
                    if len(common_years) > 1 else "7/7"
                ),
            },
        }

    theme = data["themes"]["bilanci"]
    equity_add = ["fcdePerResident"]
    cash_add = ["yearEndCashFundPerResident"]
    mission_add = [
        "generalAdministrationMissionExpenditurePerResident",
        "territorialPlanningMissionExpenditurePerResident",
        "civilProtectionMissionExpenditurePerResident",
        "economicDevelopmentMissionExpenditurePerResident",
    ]
    theme["metrics"] = add_after(theme["metrics"], "availableAdministrationResultPerResident", equity_add)
    theme["metrics"] = add_after(theme["metrics"], "cashBalancePerResident", cash_add)
    theme["metrics"] = add_after(theme["metrics"], "tourismDevelopmentMissionExpenditurePerResident", mission_add)

    sections = {section["key"]: section for section in theme.get("sections", [])}
    for required in ("equilibri", "cassa", "priorita"):
        if required not in sections:
            raise RuntimeError(f"Bilanci v1.39: sezione mancante {required}")
    sections["equilibri"]["metrics"] = add_after(
        sections["equilibri"]["metrics"], "availableAdministrationResultPerResident", equity_add
    )
    sections["cassa"]["metrics"] = add_after(
        sections["cassa"]["metrics"], "cashBalancePerResident", cash_add
    )
    sections["cassa"]["description"] = (
        "Pagamenti, incassi e saldo registrati da SIOPE nell’anno, con la consistenza "
        "del fondo di cassa a fine esercizio da OpenBDAP."
    )
    sections["priorita"]["metrics"] = add_after(
        sections["priorita"]["metrics"], "tourismDevelopmentMissionExpenditurePerResident", mission_add
    )

    if json.dumps(data["metrics"][LEGACY_KEY], ensure_ascii=False, sort_keys=True) != legacy_before:
        raise RuntimeError("Bilanci v1.39 ha modificato la serie legacy Turismo e sviluppo")

    data["version"] = "v1.39.0"
    data["release_version"] = "1.39.0"
    data["updated"] = "13 settembre 2026"
    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedExternalMetricCount"] = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedInlineMetricCount"] = registry["expectedMetricCount"] - registry["expectedExternalMetricCount"]

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Bilanci v1.39 applicato da snapshot locale: {len(data['metrics'])} indicatori nel workspace")


if __name__ == "__main__":
    main()
