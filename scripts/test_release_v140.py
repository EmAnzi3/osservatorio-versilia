#!/usr/bin/env python3
"""Controlli di rilascio per l'espansione Lavoro, Istruzione e Abitare."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "lia-v1.4.0.json"
TOWNS = {
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
}
NEW_KEYS = {
    "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap",
    "schoolStudents", "studentsPerClass", "primaryFullTimeShare",
    "housingStockPer1000", "nonOccupiedHomesPer1000", "cohabitingHouseholds",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, label: str) -> None:
    require(math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=1e-10),
            f"{label}: {actual} != {expected}")


def row_map(metric: dict) -> dict[str, dict]:
    return {row["town"]: row for row in metric["rows"]}


def main() -> None:
    source = json.loads(DATA.read_text(encoding="utf-8"))
    built = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    require(source == built, "Il dataset pubblicato non coincide con il sorgente")
    require(source.get("version") in {"2026.08.05-local-v1.4.0-lia", "2026.08.05-v1.4.0"},
            "Versione inattesa")
    if "local" not in source["version"]:
        require("anteprima" not in source.get("updated", "").lower(),
                "La versione pubblica è ancora marcata come anteprima")
    require(len(source.get("towns", [])) == 7, "Copertura comunale diversa da 7")
    require(len(source.get("themes", {})) == 9, "Numero temi diverso da 9")
    require(len(source.get("metrics", {})) == 78, "Numero indicatori diverso da 78")
    require(NEW_KEYS <= set(source["metrics"]), "Mancano nuovi indicatori LIA")

    expected_theme_metrics = {
        "lavoro": ["employmentRate", "unemploymentRate", "activityRate",
                    "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"],
        "istruzione": ["diplomaPlus", "tertiary", "schoolSites",
                        "schoolStudents", "studentsPerClass", "primaryFullTimeShare"],
        "abitare": ["housingStockPer1000", "vacantHomes", "nonOccupiedHomesPer1000",
                     "singleHouseholds", "householdSize", "cohabitingHouseholds"],
    }
    expected_sections = {"lavoro": 2, "istruzione": 3, "abitare": 3}
    for theme, metrics in expected_theme_metrics.items():
        require(source["themes"][theme]["metrics"] == metrics,
                f"{theme}: struttura indicatori inattesa")
        require(len(source["themes"][theme]["sections"]) == expected_sections[theme],
                f"{theme}: numero sezioni inatteso")

    for key, metric in source["metrics"].items():
        towns = {row.get("town") for row in metric.get("rows", [])}
        require(towns == TOWNS, f"{key}: copertura diversa da 7/7")
        meta = metric.get("meta", {})
        require(meta.get("year") not in (None, ""), f"{key}: anno mancante")
        require(meta.get("source") not in (None, ""), f"{key}: fonte mancante")
        require(metric.get("method", {}).get("coverage") == "7/7",
                f"{key}: copertura metodologica mancante")

    require(snapshot.get("version") == "lia-v1.4.0", "Snapshot LIA inatteso")
    require(snapshot.get("scope", {}).get("coverage") == "7/7", "Snapshot senza copertura 7/7")
    accepted = {item["key"] for item in snapshot.get("acceptedIndicators", [])}
    require(accepted == NEW_KEYS, "Snapshot e dataset non hanno gli stessi nuovi indicatori")
    require(len(snapshot.get("rejectedCandidates", [])) >= 6, "Audit delle esclusioni incompleto")

    istat = {row["town"]: row for row in snapshot["raw"]["istat2023"]}
    mim = {row["town"]: row for row in snapshot["raw"]["mim2024_25"]}
    require(set(istat) == TOWNS and set(mim) == TOWNS, "Snapshot grezzo non copre i sette Comuni")

    female = row_map(source["metrics"]["femaleEmploymentRate"])
    male = row_map(source["metrics"]["maleEmploymentRate"])
    gap = row_map(source["metrics"]["employmentGenderGap"])
    students = row_map(source["metrics"]["schoolStudents"])
    per_class = row_map(source["metrics"]["studentsPerClass"])
    full_time = row_map(source["metrics"]["primaryFullTimeShare"])
    housing = row_map(source["metrics"]["housingStockPer1000"])
    non_occupied = row_map(source["metrics"]["nonOccupiedHomesPer1000"])
    cohabiting = row_map(source["metrics"]["cohabitingHouseholds"])
    vacant = row_map(source["metrics"]["vacantHomes"])

    for town in TOWNS:
        ir = istat[town]
        mr = mim[town]
        female_expected = 100 * ir["P103"] / ir["female1564"]
        male_expected = 100 * ir["P102"] / ir["male1564"]
        close(female[town]["value"], female_expected, f"{town}: occupazione femminile")
        close(male[town]["value"], male_expected, f"{town}: occupazione maschile")
        close(gap[town]["value"], male_expected - female_expected, f"{town}: divario")
        close(students[town]["value"], mr["students"], f"{town}: alunni")
        close(per_class[town]["value"], mr["students"] / mr["classes"], f"{town}: alunni/classe")
        close(full_time[town]["value"], 100 * mr["full_time_students"] / mr["primary_students"],
              f"{town}: tempo pieno")
        close(housing[town]["value"], 1000 * ir["A8"] / ir["P1"], f"{town}: patrimonio")
        close(non_occupied[town]["value"], 1000 * ir["A3"] / ir["P1"],
              f"{town}: non occupate/residenti")
        close(cohabiting[town]["value"], 100 * ir["PF9"] / ir["PF1"], f"{town}: coabitazione")
        close(vacant[town]["value"], 100 * ir["A3"] / ir["A8"], f"{town}: non occupate/patrimonio")

    require(source["metrics"]["vacantHomes"]["meta"]["year"] == "2023",
            "Anno delle abitazioni non occupate non corretto")
    require("A3" in source["metrics"]["vacantHomes"]["method"]["formula"] or
            "abitazioni vuote" in source["metrics"]["vacantHomes"]["method"]["formula"],
            "Formula delle abitazioni non occupate non esplicitata")

    for source_group in ("istatSections2023", "mimSchool2024_25", "tuscanyTourism2025"):
        require(source_group in snapshot["sources"], f"Fonte audit assente: {source_group}")
    hashes = re.findall(r'"sha256":\s*"([0-9a-f]{64})"', SNAPSHOT.read_text(encoding="utf-8"))
    require(len(hashes) >= 9, "Hash delle fonti originali incompleti")

    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    for token in (
        "femaleEmploymentRate", "schoolStudents", "housingStockPer1000",
        "case 'percentagePoints'", "case 'studentsPerClass'",
        "function compareContextNav", "function townContextNav", "function updateTownContextLinks",
    ):
        require(token in bundle, f"Bundle privo di {token}")

    for theme, labels in {
        "lavoro": ("Occupazione femminile", "Divario occupazionale di genere"),
        "istruzione": ("Alunni nelle scuole del Comune", "Alunni della primaria a tempo pieno"),
        "abitare": ("Abitazioni ogni 1.000 residenti", "Famiglie coabitanti"),
    }.items():
        html = (DIST / "confronta" / theme / "index.html").read_text(encoding="utf-8")
        for label in labels:
            require(label in html, f"{theme}: indicatore non pre-renderizzato: {label}")

    manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("dataVersion") == source["version"], "Manifest non allineato")
    print("v1.4.0 LIA validata: 78 indicatori, tre temi da 6 indicatori e formule ricalcolate dallo snapshot.")


if __name__ == "__main__":
    main()
