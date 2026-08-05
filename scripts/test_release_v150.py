#!/usr/bin/env python3
"""Controlli di compatibilità per gli indicatori comunali regionali v1.5.0."""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "toscana-indicatori-v1.5.0.json"
TOWNS = {
    "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
    "Seravezza", "Forte dei Marmi", "Stazzema",
}
NEW_KEYS = {
    "youthOtherStatus",
    "foreignBornSoleProprietorShare",
    "innovationBusinessShare",
    "emsResponseTimeP75",
    "disability064Per1000",
    "organicAgriculturalAreaShare",
}
EXPECTED_UNITS = {
    "youthOtherStatus": "percent",
    "foreignBornSoleProprietorShare": "percent",
    "innovationBusinessShare": "percent",
    "emsResponseTimeP75": "minutes",
    "disability064Per1000": "per1000",
    "organicAgriculturalAreaShare": "percent",
}
SUPPORTED_VERSIONS = {
    "2026.08.05-local-v1.5.0-toscana",
    "2026.08.05-v1.5.0",
    "2026.08.05-local-v1.6.0-bilanci",
    "2026.08.05-v1.6.0",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, label: str) -> None:
    require(
        math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=1e-10),
        f"{label}: {actual} != {expected}",
    )


def row_map(metric: dict) -> dict[str, dict]:
    return {row["town"]: row for row in metric["rows"]}


def main() -> None:
    source = json.loads(DATA.read_text(encoding="utf-8"))
    built = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    require(source == built, "Il dataset pubblicato non coincide con il sorgente")
    require(source.get("version") in SUPPORTED_VERSIONS, "Versione inattesa")
    if "local" not in source["version"]:
        require(
            "anteprima" not in source.get("updated", "").lower(),
            "La versione pubblica è ancora marcata come anteprima",
        )

    require(len(source.get("towns", [])) == 7, "Copertura comunale diversa da 7")
    require(len(source.get("themes", {})) >= 9, "Sono stati rimossi temi della v1.5.0")
    require(len(source.get("metrics", {})) >= 84, "Sono stati rimossi indicatori della v1.5.0")
    require(NEW_KEYS <= set(source["metrics"]), "Mancano indicatori regionali v1.5.0")

    expected_theme_metrics = {
        "lavoro": [
            "employmentRate", "unemploymentRate", "activityRate",
            "femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap",
            "youthOtherStatus",
        ],
        "economia": [
            "income", "incomeUnder15k", "businessValueAdded", "labourProductivity",
            "industryValueAddedShare", "industryWorkerShare", "localUnits", "microUnits",
            "foreignBornSoleProprietorShare", "innovationBusinessShare",
            "tourismPresences", "tourismArrivals", "tourismAverageStay", "tourismBeds",
            "tourismSeasonality", "foreignTourismShare", "tourismIntensity",
            "tourismBedsPer1000", "tourismStructuresPer1000",
        ],
        "salute": [
            "lifeExpectancy", "mortalityAll", "chronicTotal", "diabetes", "dementia",
            "disability064Per1000", "emergencyAccess", "emsResponseTimeP75",
            "hospitalizedAll", "elderlyHomeCare", "pharmaciesPer1000", "hospitals",
        ],
        "ambiente": [
            "landUse", "landUseChange", "floodExposure", "landslideExposure",
            "organicAgriculturalAreaShare", "recycling", "wastePerResident", "residualWaste",
        ],
    }
    expected_sections = {"lavoro": 3, "economia": 4, "salute": 3, "ambiente": 3}
    for theme, metrics in expected_theme_metrics.items():
        require(
            source["themes"][theme]["metrics"] == metrics,
            f"{theme}: struttura indicatori inattesa",
        )
        require(
            len(source["themes"][theme]["sections"]) == expected_sections[theme],
            f"{theme}: numero sezioni inatteso",
        )

    for key, metric in source["metrics"].items():
        towns = {row.get("town") for row in metric.get("rows", [])}
        require(towns == TOWNS, f"{key}: copertura diversa da 7/7")
        meta = metric.get("meta", {})
        require(meta.get("year") not in (None, ""), f"{key}: anno mancante")
        require(meta.get("source") not in (None, ""), f"{key}: fonte mancante")
        require(
            metric.get("method", {}).get("coverage") == "7/7",
            f"{key}: copertura metodologica mancante",
        )

    require(
        snapshot.get("version") == "toscana-indicatori-v1.5.0",
        "Snapshot regionale inatteso",
    )
    require(
        snapshot.get("source", {}).get("coverage") == "7/7",
        "Snapshot regionale senza copertura 7/7",
    )
    require(
        set(snapshot.get("indicators", {})) == NEW_KEYS,
        "Snapshot e dataset non hanno gli stessi nuovi indicatori",
    )

    for key in NEW_KEYS:
        metric = source["metrics"][key]
        snap_metric = snapshot["indicators"][key]
        require(
            metric["meta"]["unit"] == EXPECTED_UNITS[key],
            f"{key}: unità inattesa",
        )
        require(metric["meta"]["year"] == "2024", f"{key}: anno inatteso")
        require(
            metric["sourceUrl"].startswith("https://www.regione.toscana.it/"),
            f"{key}: URL fonte inatteso",
        )

        rows = row_map(metric)
        snap_rows = {row["town"]: row for row in snap_metric["rows"]}
        require(
            set(rows) == TOWNS and set(snap_rows) == TOWNS,
            f"{key}: copertura snapshot incompleta",
        )

        latest_values = []
        for town in TOWNS:
            actual = rows[town]
            expected = snap_rows[town]
            require(
                actual["series"]["years"] == expected["years"],
                f"{key}/{town}: anni della serie non allineati",
            )
            require(
                actual["series"]["values"] == expected["values"],
                f"{key}/{town}: valori della serie non allineati",
            )
            close(
                actual["value"],
                expected["values"][-1],
                f"{key}/{town}: ultimo valore",
            )
            latest_values.append(expected["values"][-1])

        close(
            metric["aggregate"]["value"],
            median(latest_values),
            f"{key}: mediana dei sette Comuni",
        )
        require(
            metric["aggregate"]["label"] == "Mediana dei 7 Comuni",
            f"{key}: aggregato non dichiarato come mediana",
        )

    youth = snapshot["indicators"]["youthOtherStatus"]["rows"]
    require(
        all(2020 not in row["years"] for row in youth),
        "Il 2020 non deve essere inventato nella serie giovanile",
    )

    disability_rows = row_map(source["metrics"]["disability064Per1000"])
    require(
        all("ogni 1.000" in row["formatted"] for row in disability_rows.values()),
        "La disabilità non è formattata come valore per 1.000",
    )
    response_rows = row_map(source["metrics"]["emsResponseTimeP75"])
    require(
        all(row["formatted"].endswith(" min") for row in response_rows.values()),
        "Il tempo del 118 non è formattato in minuti",
    )

    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    for token in (
        *sorted(NEW_KEYS),
        "case 'minutes'",
        "function compareContextNav",
        "function townContextNav",
        "function updateTownContextLinks",
    ):
        require(token in bundle, f"Bundle privo di {token}")

    labels = {
        "lavoro": "Giovani 15–24 anni in altra condizione professionale",
        "economia": "Imprese attive nei settori dell’innovazione",
        "salute": "Tempo di risposta del 118 — 75° percentile",
        "ambiente": "Superficie agricola utilizzata biologica",
    }
    for theme, label in labels.items():
        html = (DIST / "confronta" / theme / "index.html").read_text(encoding="utf-8")
        require(label in html, f"{theme}: indicatore non pre-renderizzato: {label}")

    manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("dataVersion") == source["version"], "Manifest non allineato")
    print(
        "Compatibilità v1.5.0 validata: sei serie regionali e copertura comunale 7/7."
    )


if __name__ == "__main__":
    main()
