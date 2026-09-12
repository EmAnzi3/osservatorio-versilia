#!/usr/bin/env python3
"""Materializza forestCoverIndex da Foreste in Comune 2026 / CFI-SINFor."""
from __future__ import annotations

import json
from pathlib import Path

from foreste_comune_config import (
    EXPECTED_INPUT_METRIC_COUNT,
    EXPECTED_RELEASE_METRIC_COUNT,
    FOREST_METRIC_KEY,
    FOREST_RATIO_TOLERANCE_PCT,
    FOREST_SECTION_KEY,
    FOREST_SOURCE_PATH,
    MUNICIPALITY_ORDER,
)

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data/site-data.json"
REGISTRY = ROOT / "data/source-registry.json"
SOURCE = ROOT / FOREST_SOURCE_PATH
UNCEM_URL = "https://uncem.it/il-rapporto-foreste-in-comune-presentato-a-marcetelli-con-pefc-uncem-legambiente-caire/"


def _pct(forest_ha: float, area_ha: float) -> float:
    return float(forest_ha) / float(area_ha) * 100.0


def validate_snapshot(snapshot: dict) -> None:
    municipalities = snapshot.get("municipalities", {})
    if list(municipalities) != MUNICIPALITY_ORDER:
        raise RuntimeError("v1.36 foreste: XLSX non copre esattamente i sette Comuni canonici.")
    reference = snapshot.get("reference", {})
    if reference.get("forestMapNominalYear") != 2020 or reference.get("forestMapUpdatedThrough") != 2024:
        raise RuntimeError("v1.36 foreste: riferimento CFI atteso 2020 aggiornato al 2024.")
    if "TUFF" not in str(reference.get("definition", "")):
        raise RuntimeError("v1.36 foreste: definizione nazionale TUFF non documentata.")

    for town in MUNICIPALITY_ORDER:
        item = municipalities[town]
        area = float(item["municipalityAreaHa"])
        forest = float(item["forestAreaHa"])
        published = float(item["forestCoverPct"])
        if area <= 0 or forest < 0 or forest > area:
            raise RuntimeError(f"v1.36 foreste: superfici fuori dominio per {town}.")
        calculated = _pct(forest, area)
        if abs(calculated - published) > FOREST_RATIO_TOLERANCE_PCT:
            raise RuntimeError(
                f"v1.36 foreste: Indice di Boscosità non riconciliato per {town}: "
                f"{calculated:.6f}% vs {published:.3f}%."
            )


def _identity_rows(site: dict) -> dict[str, dict]:
    rows = {row["town"]: row for row in site["metrics"]["population"]["rows"]}
    if set(MUNICIPALITY_ORDER) - set(rows):
        raise RuntimeError("v1.36 foreste: population non copre i sette Comuni.")
    return rows


def _id(row: dict) -> dict:
    return {"town": row["town"], "code": row["code"], "slug": row["slug"]}


def build_metric(site: dict, snapshot: dict) -> dict:
    identities = _identity_rows(site)
    rows = []
    total_area = 0.0
    total_forest = 0.0
    for town in MUNICIPALITY_ORDER:
        raw = snapshot["municipalities"][town]
        area = float(raw["municipalityAreaHa"])
        forest = float(raw["forestAreaHa"])
        pct = float(raw["forestCoverPct"])
        total_area += area
        total_forest += forest
        rows.append({
            **_id(identities[town]),
            "value": pct,
            "formatted": f"{pct:.1f}".replace(".", ",") + "%",
            "forestCoverPct": pct,
            "forestAreaHa": forest,
            "municipalityAreaHa": area,
            "series": None,
            "normalized": None,
            "benchmarkValue": None,
        })

    aggregate_pct = _pct(total_forest, total_area)
    return {
        "meta": {
            "key": FOREST_METRIC_KEY,
            "theme": "ambiente",
            "label": "Copertura forestale",
            "shortLabel": "Copertura forestale",
            "description": "Fotografia comunale della superficie forestale e dell'Indice di Boscosità da Foreste in Comune 2026, basata su Carta Forestale d'Italia e SINFor.",
            "unit": "percent",
            "year": "CFI 2020 · aggiornamento 2024",
            "source": "PEFC Italia / SINFor — Foreste in Comune 2026",
            "polarity": "neutral",
            "compositeType": "forestCoverIndex",
            "primaryLabel": "Indice di Boscosità",
            "comparisonReference": "aggregate",
            "searchTerms": ["foreste", "boschi", "boscosità", "superficie forestale", "Carta Forestale d'Italia", "SINFor", "PEFC"],
        },
        "sourceUrl": UNCEM_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_pct,
            "forestCoverPct": aggregate_pct,
            "forestAreaHa": total_forest,
            "municipalityAreaHa": total_area,
            "label": "Versilia · Indice di Boscosità",
            "note": "Aggregato Versilia = Σ superficie forestale / Σ superficie comunale dei 7 Comuni; non è la media aritmetica degli indici comunali.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione comunale su Carta Forestale d'Italia / SINFor",
            "formula": "Indice di Boscosità = superficie forestale / superficie territoriale del Comune × 100. Versilia = Σ ha forestali / Σ ha comunali.",
            "definition": snapshot["reference"]["definition"],
            "reference": "Carta Forestale d'Italia: riferimento nominale 2020, aggiornata al 2024; rapporto pubblicato a giugno 2026.",
            "caveat": "Indicatore distinto da landCoverProfile → Boschi UCS 2007–2019: fonti e metodologia non vengono concatenate in un'unica serie storica.",
            "coverage": "7/7 Comuni",
        },
    }


def install_section(site: dict) -> None:
    environment = site["themes"].get("ambiente")
    if not environment:
        raise RuntimeError("v1.36 foreste: tema Ambiente non trovato.")
    sections = []
    for raw in environment.get("sections", []):
        if raw.get("key") == FOREST_SECTION_KEY:
            continue
        section = dict(raw)
        section["metrics"] = [key for key in section.get("metrics", []) if key != FOREST_METRIC_KEY]
        sections.append(section)
    land_index = next((i for i, section in enumerate(sections) if section.get("key") == "uso-copertura-suolo"), None)
    if land_index is None:
        raise RuntimeError("v1.36 foreste: sezione UCS v1.36 assente; ordine materializzatori non canonico.")
    sections.insert(land_index + 1, {
        "key": FOREST_SECTION_KEY,
        "label": "Copertura forestale",
        "description": "Fotografia forestale nazionale CFI/SINFor, distinta dalla serie storica regionale UCS.",
        "metrics": [FOREST_METRIC_KEY],
    })
    environment["sections"] = sections
    environment["metrics"] = [key for section in sections for key in section.get("metrics", [])]


def patch_catalog(snapshot: dict) -> None:
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    metrics = site.setdefault("metrics", {})
    already = 1 if FOREST_METRIC_KEY in metrics else 0
    expected_before = EXPECTED_INPUT_METRIC_COUNT + already
    if len(metrics) != expected_before:
        raise RuntimeError(f"v1.36 foreste: baseline materializzata {len(metrics)}, attese {expected_before}.")
    metrics[FOREST_METRIC_KEY] = build_metric(site, snapshot)
    install_section(site)
    if len(metrics) != EXPECTED_RELEASE_METRIC_COUNT:
        raise RuntimeError(f"v1.36 foreste: catalogo finale {len(metrics)}, attese {EXPECTED_RELEASE_METRIC_COUNT}.")
    site.update({"version": "v1.36.0", "release_version": "1.36.0", "updated": "12 settembre 2026"})
    SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    external = sum(m.get("dataStorage", {}).get("type") == "external-climate" for m in metrics.values())
    registry["expectedMetricCount"] = len(metrics)
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(metrics) - external
    profiles = registry.setdefault("sourceProfiles", {})
    profiles["pefc-sinfor-foreste-in-comune-2026"] = {
        "publisher": "PEFC Italia / SINFor",
        "frequency": "irregular",
        "frequencyLabel": "Aggiornamento non periodico",
        "expectedRelease": "Secondo aggiornamenti CFI/SINFor e nuove edizioni del rapporto",
        "acquisitionMethod": "XLSX comunale Foreste in Comune; CFI nominale 2020 aggiornata al 2024; definizione nazionale TUFF.",
        "licenseName": "Fonte istituzionale / rapporto pubblico",
        "licenseUrl": UNCEM_URL,
    }
    registry.setdefault("sourceProfileByUrl", {})[UNCEM_URL] = "pefc-sinfor-foreste-in-comune-2026"
    registry.setdefault("metricOverrides", {})[FOREST_METRIC_KEY] = {"profile": "pefc-sinfor-foreste-in-comune-2026"}
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    snapshot = json.loads(SOURCE.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    patch_catalog(snapshot)
    print("v1.36.0 foreste materializzata: 202 indicatori; forestCoverIndex composito PEFC/CFI-SINFor.")


if __name__ == "__main__":
    main()
