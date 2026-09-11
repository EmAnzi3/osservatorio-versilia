#!/usr/bin/env python3
"""Materializza la v1.35.0 dentro catalogo, shell e renderer canonici del sito."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

from biometria_comune_config import (
    BAND_IDS,
    BAND_SUM_TOLERANCE,
    MUNICIPALITY_ORDER,
    NEW_METRIC_KEYS,
    SECTION_KEY,
    SOURCE_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SOURCE = ROOT / SOURCE_PATH
ISTAT_URL = "https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/"


def validate_snapshot(snapshot: dict) -> None:
    municipalities = snapshot.get("municipalities", {})
    if list(municipalities) != MUNICIPALITY_ORDER:
        raise RuntimeError("Perimetro Biometria diverso dai sette Comuni canonici.")
    for town in MUNICIPALITY_ORDER:
        row = municipalities[town]
        area = row.get("surfaceKm2")
        if not isinstance(area, (int, float)) or area <= 0:
            raise RuntimeError(f"{town}: superficie non valida")
        bands = row.get("altitudeBandsPct", {})
        if list(bands) != BAND_IDS:
            raise RuntimeError(f"{town}: schema fasce altimetriche non valido")
        values = list(bands.values())
        if any(not isinstance(value, (int, float)) or value < 0 or value > 100 for value in values):
            raise RuntimeError(f"{town}: percentuale fascia fuori 0..100")
        if abs(sum(values) - 100.0) > BAND_SUM_TOLERANCE + 1e-9:
            raise RuntimeError(f"{town}: somma fasce {sum(values):.1f}% fuori tolleranza")
        if round(sum(values[:2]), 1) != row.get("below600Pct"):
            raise RuntimeError(f"{town}: derivato sotto 600 m incoerente")
        if round(sum(values[1:]), 1) != row.get("from300Pct"):
            raise RuntimeError(f"{town}: derivato da 300 m incoerente")
        altitudes = [row.get("altitudeMinM"), row.get("altitudeMeanM"), row.get("altitudeMaxM")]
        if any(value is not None for value in altitudes):
            if not all(isinstance(value, (int, float)) for value in altitudes):
                raise RuntimeError(f"{town}: altimetria min/media/max parziale")
            if not altitudes[0] <= altitudes[1] <= altitudes[2]:
                raise RuntimeError(f"{town}: altimetria min/media/max incoerente")


def _identity_by_town(site: dict) -> dict[str, dict]:
    population = site.get("metrics", {}).get("population")
    if not population:
        raise RuntimeError("Metrica canonica population non trovata.")
    rows = {row["town"]: row for row in population.get("rows", [])}
    if set(MUNICIPALITY_ORDER) - set(rows):
        raise RuntimeError("Population non copre tutti i sette Comuni.")
    return rows


def _row_identity(pop_row: dict) -> dict:
    return {"town": pop_row["town"], "code": pop_row["code"], "slug": pop_row["slug"]}


def _surface_metric(site: dict, snapshot: dict, identities: dict[str, dict]) -> dict:
    rows = []
    total = 0.0
    for town in [item["name"] for item in site["towns"]]:
        source = snapshot["municipalities"][town]
        value = float(source["surfaceKm2"])
        total += value
        rows.append({
            **_row_identity(identities[town]),
            "value": value,
            "formatted": f"{value:.2f}".replace(".", ",") + " km²",
            "series": None,
            "normalized": None,
            "benchmarkValue": value,
        })
    return {
        "meta": {
            "key": "municipalSurface",
            "theme": "ambiente",
            "label": "Superficie comunale",
            "shortLabel": "Superficie",
            "description": "Estensione territoriale del Comune espressa in chilometri quadrati.",
            "unit": "squareKm",
            "year": "31 dicembre 2021",
            "source": "Istat — Principali statistiche geografiche sui comuni",
            "polarity": "neutral",
            "comparisonReference": "aggregate",
            "searchTerms": ["superficie", "territorio", "km²", "estensione comunale"],
        },
        "sourceUrl": ISTAT_URL,
        "rows": rows,
        "aggregate": {
            "value": total,
            "label": "Versilia · superficie dei 7 Comuni",
            "note": "Somma delle superfici comunali; non è una media.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato territoriale ufficiale",
            "formula": "Superficie territoriale comunale in km².",
            "caveat": "Riferimento territoriale 31 dicembre 2021.",
            "coverage": "7/7",
        },
    }


def _density_metric(site: dict, snapshot: dict, identities: dict[str, dict]) -> dict:
    population = site["metrics"]["population"]
    pop_year = str(population["meta"]["year"])
    rows = []
    total_population = 0.0
    total_area = 0.0
    for town in [item["name"] for item in site["towns"]]:
        pop_row = identities[town]
        residents = float(pop_row["value"])
        area = float(snapshot["municipalities"][town]["surfaceKm2"])
        density = residents / area
        total_population += residents
        total_area += area
        rows.append({
            **_row_identity(pop_row),
            "value": density,
            "formatted": f"{density:.1f}".replace(".", ",") + " ab./km²",
            "series": None,
            "normalized": None,
            "benchmarkValue": density,
            "populationBase": residents,
            "surfaceKm2": area,
        })
    aggregate = total_population / total_area
    return {
        "meta": {
            "key": "populationDensity",
            "theme": "ambiente",
            "label": "Densità abitativa",
            "shortLabel": "Densità",
            "description": "Residenti per chilometro quadrato, calcolati usando la popolazione canonica dell’Osservatorio e la superficie comunale Istat.",
            "unit": "peoplePerSquareKm",
            "year": pop_year,
            "source": "Elaborazione Osservatorio Versilia su Istat",
            "polarity": "neutral",
            "comparisonReference": "aggregate",
            "searchTerms": ["densità", "abitanti per km²", "residenti", "superficie"],
        },
        "sourceUrl": ISTAT_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate,
            "label": "Versilia · densità complessiva",
            "note": "Σ residenti dei 7 Comuni / Σ superficie dei 7 Comuni; non è la media semplice delle densità comunali.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore derivato da dati canonici",
            "formula": "popolazione residente canonica / superficie comunale km²",
            "caveat": f"La popolazione segue il riferimento della metrica canonica Population ({pop_year}); la superficie è riferita al 31 dicembre 2021.",
            "coverage": "7/7",
        },
    }


def _altitude_metric(site: dict, snapshot: dict, identities: dict[str, dict]) -> dict:
    band_defs = snapshot["bands"]
    rows = []
    area_by_band = [0.0 for _ in band_defs]
    total_area = 0.0
    for town in [item["name"] for item in site["towns"]]:
        source = snapshot["municipalities"][town]
        area = float(source["surfaceKm2"])
        values = [float(source["altitudeBandsPct"][band["id"]]) for band in band_defs]
        parts = []
        for index, (band, value) in enumerate(zip(band_defs, values, strict=True)):
            area_by_band[index] += area * value / 100.0
            parts.append({"key": band["id"], "label": band["label"], "value": value, "unit": "percent"})
        total_area += area
        rows.append({
            **_row_identity(identities[town]),
            "value": float(source["from300Pct"]),
            "formatted": f"{float(source['from300Pct']):.1f}".replace(".", ",") + "%",
            "summaryValue": float(source["from300Pct"]),
            "below600Pct": float(source["below600Pct"]),
            "parts": parts,
            "series": None,
            "normalized": None,
            "benchmarkValue": float(source["from300Pct"]),
            "altitudeStats": {
                "minM": source.get("altitudeMinM"),
                "meanM": source.get("altitudeMeanM"),
                "maxM": source.get("altitudeMaxM"),
                "status": source.get("altitudeStatus"),
            },
        })
    aggregate_parts = [
        {"key": band["id"], "label": band["label"], "value": area / total_area * 100.0, "unit": "percent"}
        for band, area in zip(band_defs, area_by_band, strict=True)
    ]
    aggregate_above300 = sum(part["value"] for part in aggregate_parts[1:])
    return {
        "meta": {
            "key": "altitudeProfile",
            "theme": "ambiente",
            "label": "Distribuzione altimetrica del territorio",
            "shortLabel": "Profilo altimetrico",
            "description": "Quota percentuale della superficie comunale nelle otto fasce altimetriche Istat, dal livello 0–299 m a oltre 2.500 m.",
            "unit": "percent",
            "year": "31 dicembre 2021",
            "source": "Istat — Fasce altimetriche dei Comuni",
            "polarity": "neutral",
            "compositeType": "distribution",
            "summaryLabel": "Territorio da 300 m in su",
            "summaryUnit": "percent",
            "comparisonReference": "aggregate",
            "searchTerms": ["altitudine", "fasce altimetriche", "montagna", "pianura", "quota"],
        },
        "sourceUrl": ISTAT_URL,
        "rows": rows,
        "aggregate": {
            "summaryValue": aggregate_above300,
            "summaryLabel": "Versilia · territorio da 300 m in su",
            "parts": aggregate_parts,
            "label": "Versilia · distribuzione altimetrica",
            "note": "Le fasce Versilia sono ponderate per superficie comunale; non sono la media semplice delle percentuali dei sette Comuni.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato territoriale ufficiale + aggregazione Osservatorio",
            "formula": "Comune: quota di superficie in ciascuna fascia. Versilia: Σ(superficie comunale × quota fascia) / Σ superficie.",
            "caveat": "Le percentuali comunali possono totalizzare 99,9% o 100,1% per arrotondamento della fonte. Le quote minima/media/massima restano fuori dalla UI finché non è verificato il file canonico Istat Altimetria 2021.",
            "coverage": "7/7",
        },
    }


def build_metrics(site: dict, snapshot: dict) -> dict[str, dict]:
    validate_snapshot(snapshot)
    identities = _identity_by_town(site)
    return {
        "municipalSurface": _surface_metric(site, snapshot, identities),
        "populationDensity": _density_metric(site, snapshot, identities),
        "altitudeProfile": _altitude_metric(site, snapshot, identities),
    }


def install_environment_section(site: dict) -> None:
    environment = site.get("themes", {}).get("ambiente")
    if not environment:
        raise RuntimeError("Tema Ambiente non trovato.")
    cleaned = []
    for section in environment.get("sections", []):
        if section.get("key") == SECTION_KEY:
            continue
        section = dict(section)
        section["metrics"] = [key for key in section.get("metrics", []) if key not in NEW_METRIC_KEYS]
        cleaned.append(section)
    profile = {
        "key": SECTION_KEY,
        "label": "Profilo fisico del territorio",
        "description": "Superficie, densità abitativa e distribuzione altimetrica per leggere la forma fisica dei sette Comuni.",
        "metrics": list(NEW_METRIC_KEYS),
    }
    environment["sections"] = [profile] + cleaned
    environment["metrics"] = [key for section in environment["sections"] for key in section.get("metrics", [])]


def patch_catalog(snapshot: dict) -> None:
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    site.setdefault("metrics", {}).update(build_metrics(site, snapshot))
    install_environment_section(site)
    site["version"] = "v1.35.0"
    site["release_version"] = "1.35.0"
    site["updated"] = "11 settembre 2026"
    SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    metrics = site["metrics"]
    external = sum(metric.get("dataStorage", {}).get("type") == "external-climate" for metric in metrics.values())
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(metrics) - external
    profiles = registry.setdefault("sourceProfiles", {})
    profiles["istat-geografia-comunale-2021"] = {
        "publisher": "Istat",
        "frequency": "irregular",
        "frequencyLabel": "Secondo gli aggiornamenti delle statistiche geografiche comunali Istat",
        "expectedRelease": "Secondo la fonte",
        "acquisitionMethod": "Statistiche geografiche comunali Istat: superficie e distribuzione della superficie per fascia altimetrica; densità derivata dalla popolazione canonica del sito.",
        "licenseName": "Condizioni di riuso Istat",
        "licenseUrl": ISTAT_URL,
    }
    registry.setdefault("sourceProfileByUrl", {})[ISTAT_URL] = "istat-geografia-comunale-2021"
    overrides = registry.setdefault("metricOverrides", {})
    for key in NEW_METRIC_KEYS:
        overrides[key] = {"profile": "istat-geografia-comunale-2021"}
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    snapshot = json.loads(SOURCE.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    runpy.run_path(str(ROOT / "scripts" / "patch_biometria_runtime.py"), run_name="__main__")
    patch_catalog(snapshot)
    print("Biometria v1.35.0 materializzata nei renderer canonici Ambiente.")


if __name__ == "__main__":
    main()
