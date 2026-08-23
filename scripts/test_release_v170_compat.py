#!/usr/bin/env python3
"""Controlli di retrocompatibilità per Osservatorio Versilia v1.7+.

Verifica che le release v1.5/v1.6 non abbiano perso indicatori o struttura,
consentendo le aggiunte della v1.7 e la policy esplicita 6/7 per i soli
conteggi assoluti FTTH.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
DIST_DATA = ROOT / "dist" / "data" / "site-data.json"
TOSCANA_SNAPSHOT = ROOT / "data" / "source-snapshots" / "toscana-indicatori-v1.5.0.json"
BUDGET_SNAPSHOT = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"

TOWNS = {
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
}
V15_KEYS = {
    "youthOtherStatus",
    "foreignBornSoleProprietorShare",
    "innovationBusinessShare",
    "emsResponseTimeP75",
    "disability064Per1000",
    "organicAgriculturalAreaShare",
}
V16_BUDGET_KEYS = {
    "currentRevenueAccruedPerResident",
    "currentExpenditureCommittedPerResident",
    "capitalExpenditureCommittedPerResident",
    "ownRevenueShare",
    "currentCollectionCapacity",
    "currentPaymentCapacity",
    "availableAdministrationResultPerResident",
    "rigidExpenditureShare",
    "siopePayments",
    "currentPayments",
    "capitalPayments",
    "cashReceiptsPerResident",
    "cashBalancePerResident",
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
}
V17_KEYS = {
    "localEmployees",
    "employeesPerLocalUnit",
    "localUnitsChange",
    "localEmployeesChange",
    "ftthCoverageDesi",
    "ftthReachedHouseholds",
    "ftthUnreachedHouseholds",
    "ftthCoverage20m",
}
PARTIAL_MISSING = {
    "ftthReachedHouseholds": "Forte dei Marmi",
    "ftthUnreachedHouseholds": "Forte dei Marmi",
    "fuelPrices": "Stazzema",
}

LEGACY_THEME_KEYS = {
    "lavoro": {
        "employmentRate", "unemploymentRate", "activityRate",
        "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap",
        "youthOtherStatus",
    },
    "economia": {
        "income", "incomeDistribution", "businessValueAdded", "labourProductivity",
        "industryValueAddedShare", "industryWorkerShare", "localUnits", "microUnits",
        "foreignBornSoleProprietorShare", "innovationBusinessShare",
        "tourismPresences", "tourismArrivals", "tourismAverageStay", "tourismBeds",
        "tourismSeasonality", "foreignTourismShare", "tourismIntensity",
        "tourismBedsPer1000", "tourismStructuresPer1000",
    },
    "salute": {
        "lifeExpectancy", "mortalityAll", "chronicTotal", "diabetes", "dementia",
        "disability064Per1000", "emergencyAccess", "emsResponseTimeP75",
        "hospitalizedAll", "elderlyHomeCare", "pharmaciesPer1000", "hospitals",
    },
    "ambiente": {
        "landUse", "landUseChange", "floodExposure", "landslideExposure",
        "organicAgriculturalAreaShare", "recycling", "wastePerResident", "residualWaste",
    },
}

# PR91 integra le due vecchie card di genere dentro employmentRate.
# Gli oggetti legacy restano nel dataset per compatibilità dei link/dati, ma
# non devono più occupare due voci autonome nel catalogo pubblico Lavoro.
MIGRATED_THEME_KEYS = {
    "lavoro": {"femaleEmploymentRate", "maleEmploymentRate"},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def version_tuple(value: str) -> tuple[int, int, int]:
    clean = value.strip().lower().lstrip("v")
    parts = clean.split(".")
    require(len(parts) >= 2, f"Versione non interpretabile: {value}")
    nums = [int(part) for part in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)  # type: ignore[return-value]


def main() -> None:
    source = json.loads(DATA.read_text(encoding="utf-8"))
    built = json.loads(DIST_DATA.read_text(encoding="utf-8"))
    regional = json.loads(TOSCANA_SNAPSHOT.read_text(encoding="utf-8"))
    budget = json.loads(BUDGET_SNAPSHOT.read_text(encoding="utf-8"))

    require(source == built, "Il dataset pubblicato non coincide con il sorgente")
    require(version_tuple(source.get("version", "0.0.0")) >= (1, 7, 0), "Release precedente alla v1.7")
    require(len(source.get("towns", [])) == 7, "Copertura anagrafica diversa da 7 Comuni")
    require(len(source.get("themes", {})) >= 10, "Il sito deve mantenere almeno i 10 temi della v1.7")
    require(len(source.get("metrics", {})) >= 106, "La v1.7 deve contenere almeno 106 indicatori")

    all_keys = set(source["metrics"])
    require(V15_KEYS <= all_keys, "Sono stati rimossi indicatori della v1.5")
    require(V16_BUDGET_KEYS <= all_keys, "Sono stati rimossi indicatori della v1.6")
    require(V17_KEYS <= all_keys, "Mancano indicatori introdotti nella v1.7")

    for theme_key, legacy_keys in LEGACY_THEME_KEYS.items():
        current = set(source["themes"][theme_key]["metrics"])
        migrated = MIGRATED_THEME_KEYS.get(theme_key, set())
        require((legacy_keys - migrated) <= current, f"{theme_key}: rimossi indicatori delle release precedenti")
        require(migrated <= all_keys, f"{theme_key}: oggetti legacy migrati non più disponibili nel dataset")

    employment = source["metrics"]["employmentRate"]
    require(
        employment.get("meta", {}).get("compositeType") == "demographicBreakdown",
        "lavoro: employmentRate deve assorbire il dettaglio per genere dopo PR91",
    )
    gender_keys = {
        item.get("key") for item in employment.get("meta", {}).get("genderOptions", [])
        if isinstance(item, dict)
    }
    require(
        {"total", "men", "women"} <= gender_keys,
        "lavoro: la migrazione PR91 deve preservare Totale/Uomini/Donne",
    )
    require(
        MIGRATED_THEME_KEYS["lavoro"].isdisjoint(set(source["themes"]["lavoro"]["metrics"])),
        "lavoro: le card legacy uomo/donna non devono duplicare il filtro Genere",
    )

    budget_theme = source["themes"]["bilanci"]
    require(budget_theme["number"] == "10", "Bilanci deve essere il tema 10 dopo l’introduzione di Sicurezza")
    require(V16_BUDGET_KEYS <= set(budget_theme["metrics"]), "Bilanci ha perso indicatori v1.6")
    require(len(budget_theme.get("sections", [])) >= 4, "Bilanci ha perso sezioni")

    community = source["themes"]["comunita"]
    require(community["number"] == "11", "Investimenti e comunità deve essere il tema 11 dopo l’introduzione di Sicurezza")
    require(
        community["metrics"] == ["publicWorks", "pnrrFunding", "pnrrConcluded", "thirdSector"],
        "Struttura del tema Investimenti e comunità inattesa",
    )

    for key, metric in source["metrics"].items():
        if metric.get("dataStorage", {}).get("type") == "external-climate":
            continue
        rows = metric.get("rows", [])
        require({row.get("town") for row in rows} == TOWNS, f"{key}: righe comunali incomplete")
        require(metric.get("meta", {}).get("year") not in (None, ""), f"{key}: anno mancante")
        require(metric.get("meta", {}).get("source") not in (None, ""), f"{key}: fonte mancante")
        coverage = str(metric.get("method", {}).get("coverage", ""))
        if key in PARTIAL_MISSING:
            require(coverage == "6/7", f"{key}: deve dichiarare copertura 6/7")
            missing = [row for row in rows if row.get("value") is None]
            require(len(missing) == 1, f"{key}: copertura 6/7 senza un solo valore mancante")
            require(missing[0].get("town") == PARTIAL_MISSING[key], f"{key}: Comune n.d. inatteso")
            if key == "fuelPrices":
                require(missing[0].get("stationCount") == 0, "fuelPrices: Stazzema non deve avere impianti attivi")
                parts = missing[0].get("parts") or []
                require(len(parts) == 2 and all(part.get("value") is None for part in parts),
                        "fuelPrices: benzina e gasolio di Stazzema devono restare null/n.d., mai zero")
            else:
                require(missing[0].get("formatted") == "n.d.", f"{key}: valore mancante non etichettato n.d.")
        else:
            require("7/7" in coverage, f"{key}: copertura diversa da 7/7")

    require(regional.get("version") == "toscana-indicatori-v1.5.0", "Snapshot v1.5 inatteso")
    require(set(regional.get("indicators", {})) == V15_KEYS, "Snapshot v1.5 non allineato")
    require(set(budget.get("raw", {})) == TOWNS, "Snapshot bilanci v1.6 incompleto")

    ateco = source.get("economyAteco", {})
    require(ateco.get("year") == 2023, "Anno ATECO inatteso")
    require(ateco.get("coverage") == "7/7", "Copertura ATECO diversa da 7/7")
    require(ateco.get("classification") not in (None, ""), "Classificazione ATECO mancante")
    require(len(ateco.get("sectorCodes", [])) >= 50, "Dettaglio ATECO troppo ridotto")
    for town in source["towns"]:
        economy = source["details"][town["code"]]["economy"]
        require(economy.get("atecoYear") == 2023, f"{town['name']}: anno ATECO inatteso")
        require(len(economy.get("atecoSectors", [])) > 0, f"{town['name']}: dettaglio ATECO assente")
        require(len(economy.get("topSectorsByUnits", [])) <= 10, f"{town['name']}: Top ATECO unità locali invalido")
        require(len(economy.get("topSectors", [])) <= 10, f"{town['name']}: Top ATECO addetti invalido")

    massarosa_ftth = next(row for row in source["metrics"]["ftthReachedHouseholds"]["rows"] if row["town"] == "Massarosa")
    require(massarosa_ftth["value"] == 4219, "Massarosa: conteggio FTTH non allineato al CSV primario AGCOM")
    massarosa_desi = next(row for row in source["metrics"]["ftthCoverageDesi"]["rows"] if row["town"] == "Massarosa")
    require(float(massarosa_desi["value"]) == 47.0, "Massarosa: copertura FTTH DESI inattesa")

    print("Controlli di retrocompatibilità v1.7 superati.")


if __name__ == "__main__":
    main()
