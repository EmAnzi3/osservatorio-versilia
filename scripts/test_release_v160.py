#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json").read_text(encoding="utf-8"))

TOWNS = [
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
]
NEW_METRICS = [
    "currentRevenueAccruedPerResident",
    "currentExpenditureCommittedPerResident",
    "capitalExpenditureCommittedPerResident",
    "ownRevenueShare",
    "currentCollectionCapacity",
    "currentPaymentCapacity",
    "availableAdministrationResultPerResident",
    "rigidExpenditureShare",
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
]
CASH_METRICS = [
    "siopePayments", "currentPayments", "capitalPayments",
    "cashReceiptsPerResident", "cashBalancePerResident",
]
EXPECTED_YEARS = list(range(2019, 2026))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, message: str) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=1e-7):
        raise AssertionError(f"{message}: {actual} != {expected}")


def raw(town: str, year: int) -> dict:
    return SNAPSHOT["raw"][town]["years"][str(year)]


def expected_value(key: str, town: str, year: int) -> float:
    item = raw(town, year)
    population = item["population_at_1_january"]
    if key == "currentRevenueAccruedPerResident":
        return item["current_revenue_accruals_titles_1_2_3"] / population
    if key == "currentExpenditureCommittedPerResident":
        return item["current_expenditure_commitments_title_1"] / population
    if key == "capitalExpenditureCommittedPerResident":
        return item["capital_expenditure_commitments_title_2"] / population
    if key == "ownRevenueShare":
        return item["own_revenue_accruals_titles_1_3"] / item["current_revenue_accruals_titles_1_2_3"] * 100
    if key == "currentCollectionCapacity":
        return item["current_revenue_competence_receipts_titles_1_2_3"] / item["current_revenue_accruals_titles_1_2_3"] * 100
    if key == "currentPaymentCapacity":
        return item["current_expenditure_competence_payments_title_1"] / item["current_expenditure_commitments_title_1"] * 100
    if key == "availableAdministrationResultPerResident":
        return item["available_administration_result_code_0502"] / population
    if key == "rigidExpenditureShare":
        return item["rigid_expenditure_share_official_code_01_01"]
    mission_codes = {
        "educationMissionExpenditurePerResident": ["04"],
        "socialMissionExpenditurePerResident": ["12"],
        "environmentMissionExpenditurePerResident": ["09"],
        "mobilityMissionExpenditurePerResident": ["10"],
        "cultureSportMissionExpenditurePerResident": ["05", "06"],
        "tourismDevelopmentMissionExpenditurePerResident": ["07", "14"],
    }[key]
    return sum(item["mission_commitments"].get(code, 0) for code in mission_codes) / population


def expected_aggregate(key: str) -> float:
    items = [raw(town, 2025) for town in TOWNS]
    population = sum(item["population_at_1_january"] for item in items)
    if key == "currentRevenueAccruedPerResident":
        return sum(item["current_revenue_accruals_titles_1_2_3"] for item in items) / population
    if key == "currentExpenditureCommittedPerResident":
        return sum(item["current_expenditure_commitments_title_1"] for item in items) / population
    if key == "capitalExpenditureCommittedPerResident":
        return sum(item["capital_expenditure_commitments_title_2"] for item in items) / population
    if key == "ownRevenueShare":
        return sum(item["own_revenue_accruals_titles_1_3"] for item in items) / sum(item["current_revenue_accruals_titles_1_2_3"] for item in items) * 100
    if key == "currentCollectionCapacity":
        return sum(item["current_revenue_competence_receipts_titles_1_2_3"] for item in items) / sum(item["current_revenue_accruals_titles_1_2_3"] for item in items) * 100
    if key == "currentPaymentCapacity":
        return sum(item["current_expenditure_competence_payments_title_1"] for item in items) / sum(item["current_expenditure_commitments_title_1"] for item in items) * 100
    if key == "availableAdministrationResultPerResident":
        return sum(item["available_administration_result_code_0502"] for item in items) / population
    if key == "rigidExpenditureShare":
        return statistics.median(item["rigid_expenditure_share_official_code_01_01"] for item in items)
    mission_codes = {
        "educationMissionExpenditurePerResident": ["04"],
        "socialMissionExpenditurePerResident": ["12"],
        "environmentMissionExpenditurePerResident": ["09"],
        "mobilityMissionExpenditurePerResident": ["10"],
        "cultureSportMissionExpenditurePerResident": ["05", "06"],
        "tourismDevelopmentMissionExpenditurePerResident": ["07", "14"],
    }[key]
    return sum(sum(item["mission_commitments"].get(code, 0) for code in mission_codes) for item in items) / population


def main() -> None:
    require(DATA["version"] == "v1.6.0", "Versione pubblica v1.6.0 assente")
    require(len(DATA["themes"]) == 10, "Il sito deve avere 10 temi")
    require(len(DATA["metrics"]) == 98, "Il sito deve avere 98 indicatori")
    require(list(DATA["themes"])[-2:] == ["bilanci", "comunita"], "Ordine dei temi inatteso")

    budget_theme = DATA["themes"]["bilanci"]
    require(budget_theme["number"] == "09", "Bilanci deve essere il tema 09")
    require(len(budget_theme["metrics"]) == 19, "Bilanci deve contenere 19 indicatori")
    require(len(budget_theme["sections"]) == 4, "Bilanci deve avere quattro sezioni")
    for key in NEW_METRICS + CASH_METRICS:
        require(key in budget_theme["metrics"], f"{key} assente dal tema Bilanci")
        require(DATA["metrics"][key]["meta"]["theme"] == "bilanci", f"{key} non assegnato a Bilanci")

    community = DATA["themes"]["comunita"]
    require(community["number"] == "10", "Comunità deve diventare il tema 10")
    require(community["label"] == "Investimenti e comunità", "Titolo Comunità inatteso")
    require(community["metrics"] == ["publicWorks", "pnrrFunding", "pnrrConcluded", "thirdSector"], "Comunità contiene indicatori impropri")

    for theme_key, theme in DATA["themes"].items():
        for key in theme["metrics"]:
            require(key in DATA["metrics"], f"{theme_key} riferisce l’indicatore inesistente {key}")
            require(DATA["metrics"][key]["meta"]["theme"] == theme_key, f"{key} assegnato al tema errato")

    require(SNAPSHOT["selection_rules"]["subject_type"].startswith("ELCOMU"), "Filtro ELCOMU non dichiarato")
    require(SNAPSHOT["selection_rules"]["years"] == EXPECTED_YEARS, "Intervallo snapshot inatteso")
    require(set(SNAPSHOT["raw"]) == set(TOWNS), "Copertura snapshot diversa da 7/7")
    require(SNAPSHOT["history_audit"]["coverage"].startswith("7/7"), "Audit storico senza copertura completa")
    for town in TOWNS:
        require(sorted(map(int, SNAPSHOT["raw"][town]["years"])) == EXPECTED_YEARS, f"Annualità incomplete per {town}")

    for key in NEW_METRICS:
        metric = DATA["metrics"][key]
        source_years = [int(year) for year in SNAPSHOT["metrics"][key]["years"]]
        require(metric["meta"]["year"] == "2025", f"Anno corrente errato per {key}")
        require(metric["method"]["coverage"].startswith("7/7"), f"Copertura errata per {key}")
        require(metric["sourceUrl"].startswith("https://openbdap.rgs.mef.gov.it/"), f"Fonte errata per {key}")
        require(len(metric["rows"]) == 7, f"Righe incomplete per {key}")
        rows = {row["town"]: row for row in metric["rows"]}
        require(set(rows) == set(TOWNS), f"Comuni incompleti per {key}")
        for town in TOWNS:
            row = rows[town]
            close(row["value"], expected_value(key, town, 2025), f"{key} {town} 2025")
            if key == "rigidExpenditureShare":
                require(not row.get("series"),
                        "Spese rigide: lo storico discontinuo non deve essere pubblicato")
            elif len(source_years) >= 2:
                require(row["series"]["years"] == source_years, f"Serie anni errata per {key} {town}")
                require(len(row["series"]["values"]) == len(source_years), f"Serie valori incompleta per {key} {town}")
                for year, value in zip(source_years, row["series"]["values"], strict=True):
                    close(value, expected_value(key, town, year), f"{key} {town} {year}")
            else:
                require(row["series"] is None, f"Serie non ammessa per {key} {town}")
        close(metric["aggregate"]["value"], expected_aggregate(key), f"Aggregato errato per {key}")

    rigid_years = [int(year) for year in SNAPSHOT["metrics"]["rigidExpenditureShare"]["years"]]
    require(2024 not in rigid_years, "Il 2024 anomalo delle spese rigide deve restare escluso")
    require(len(rigid_years) >= 2, "Serie valida delle spese rigide troppo corta")
    for town in TOWNS:
        for year in rigid_years:
            require(0 <= expected_value("rigidExpenditureShare", town, year) <= 100, f"Spese rigide fuori scala: {town} {year}")
    require(all(not row.get("series") for row in DATA["metrics"]["rigidExpenditureShare"]["rows"]),
            "Spese rigide: serie pubblicata nonostante la discontinuità")
    require("storico non viene pubblicato" in DATA["metrics"]["rigidExpenditureShare"]["method"]["caveat"],
            "Spese rigide: motivazione metodologica assente")

    require(DATA["metrics"]["availableAdministrationResultPerResident"]["rows"][2]["value"] < 0, "I valori negativi devono essere conservati")
    require(DATA["metrics"]["rigidExpenditureShare"]["meta"]["polarity"] == "negative", "Polarità spese rigide errata")
    for key in [
        "currentRevenueAccruedPerResident", "currentExpenditureCommittedPerResident",
        "capitalExpenditureCommittedPerResident", "availableAdministrationResultPerResident",
        "educationMissionExpenditurePerResident", "socialMissionExpenditurePerResident",
        "environmentMissionExpenditurePerResident", "mobilityMissionExpenditurePerResident",
        "cultureSportMissionExpenditurePerResident", "tourismDevelopmentMissionExpenditurePerResident",
    ]:
        require(DATA["metrics"][key]["meta"]["polarity"] == "neutral", f"{key} non deve produrre una pagella")

    bundle = (ROOT / "assets" / "app-core.js").read_text(encoding="utf-8")
    for token in ["bilanci:", *NEW_METRICS]:
        require(token in bundle, f"Bundle privo di {token}")
    require("Object.keys(data.themes).length" in bundle, "Conteggio temi ancora statico")

    dist = ROOT / "dist"
    if dist.exists():
        budget_page = dist / "confronta" / "bilanci" / "index.html"
        require(budget_page.exists(), "Pagina statica Bilanci non generata")
        text = budget_page.read_text(encoding="utf-8")
        require("Bilanci comunali" in text, "Titolo Bilanci assente dal prerender")
        require("Capacità di riscossione corrente" in text, "Indicatore Bilanci assente dal prerender")
        for slug in ["massarosa", "viareggio", "camaiore", "pietrasanta", "seravezza", "forte-dei-marmi", "stazzema"]:
            town_page = dist / "comuni" / slug / "index.html"
            require(town_page.exists(), f"Pagina comunale assente: {slug}")
            require("Bilanci comunali" in town_page.read_text(encoding="utf-8"), f"Bilanci assente da {slug}")

    print("Tutti i controlli v1.6.0 Bilanci storici sono superati.")


if __name__ == "__main__":
    main()
