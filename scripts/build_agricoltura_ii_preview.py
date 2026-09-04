#!/usr/bin/env python3
"""Costruisce esclusivamente l'artifact di revisione Agricoltura II.

Il catalogo e il registro fonti canonici restano a v1.29.0/181 indicatori.
Durante questa build vengono temporaneamente materializzate le due metriche
Agricoltura II, così il prerender e lo Stato dati vedono lo stesso catalogo
183. I file sorgente sono ripristinati byte-per-byte nel finally.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
OVERLAY = ROOT / "data" / "agricoltura-ii-draft.json"
DIST = ROOT / "dist"

EXPECTED_KEYS = {
    "agriculturalRenewalAndLeadership",
    "agriculturalDiversificationAndModernization",
}


def merge_overlay(data: dict, overlay: dict) -> dict:
    before = len(data.get("metrics", {}))
    metrics = overlay.get("metrics", {})
    if set(metrics) != EXPECTED_KEYS:
        raise RuntimeError(f"Metriche Agricoltura II inattese: {sorted(metrics)}")

    data["metrics"].update(metrics)
    theme_key = overlay["theme"]
    section_key = overlay["section"]
    theme = data["themes"][theme_key]
    section = next(
        (item for item in theme.get("sections", []) if item.get("key") == section_key),
        None,
    )
    if section is None:
        raise RuntimeError(f"Sezione {theme_key}/{section_key} non trovata")

    additions = list(overlay.get("metricOrder", []))
    section["label"] = overlay.get("sectionLabel", section.get("label"))
    section["description"] = overlay.get("sectionDescription", section.get("description"))
    section["metrics"] = [
        key for key in section.get("metrics", []) if key not in additions
    ] + additions
    theme["metrics"] = [
        key
        for item in theme.get("sections", [])
        for key in item.get("metrics", [])
    ]
    data["version"] = overlay.get("versionLabel", data.get("version"))
    data["updated"] = overlay.get("updatedLabel", data.get("updated"))

    after = len(data["metrics"])
    if after != before + 2 or after != 183:
        raise RuntimeError(f"Catalogo preview inatteso: {before} -> {after}; atteso 183")
    return data


def patch_registry(registry: dict) -> dict:
    if int(registry.get("expectedMetricCount", 0)) != 181:
        raise RuntimeError("Baseline registry inattesa: expectedMetricCount deve essere 181")
    if int(registry.get("expectedInlineMetricCount", 0)) != 177:
        raise RuntimeError("Baseline registry inattesa: expectedInlineMetricCount deve essere 177")
    registry["expectedMetricCount"] = 183
    registry["expectedInlineMetricCount"] = 179
    return registry


def append_draft_css() -> None:
    css_source = ROOT / "assets" / "agricoltura-ii-draft.css"
    static_css = DIST / "assets" / "static.css"
    marker = "/* Agricoltura II draft review */"
    css = css_source.read_text(encoding="utf-8")
    current = static_css.read_text(encoding="utf-8")
    if marker not in current:
        static_css.write_text(
            current + f"\n\n{marker}\n" + css + "\n",
            encoding="utf-8",
        )


def validate_preview() -> None:
    dist_data = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    if len(dist_data.get("metrics", {})) != 183:
        raise RuntimeError("Preview non materializzata a 183 indicatori")
    if not EXPECTED_KEYS.issubset(dist_data.get("metrics", {})):
        raise RuntimeError("Metriche Agricoltura II assenti da dist/data/site-data.json")

    home = (DIST / "index.html").read_text(encoding="utf-8")
    ambiente = (DIST / "confronta" / "ambiente" / "index.html").read_text(encoding="utf-8")
    if "183 indicatori" not in home:
        raise RuntimeError("Home preview non espone 183 indicatori")
    for label in (
        "Ricambio e conduzione delle aziende agricole",
        "Diversificazione e modernizzazione delle aziende agricole",
    ):
        if label not in ambiente:
            raise RuntimeError(f"Card Agricoltura II assente dal prerender: {label}")

    status = json.loads((DIST / "data" / "data-status.json").read_text(encoding="utf-8"))
    if int(status.get("metricCount", 0)) != 183:
        raise RuntimeError("Stato dati preview non allineato a 183 indicatori")

    indicator_pages = list((DIST / "indicatori").glob("*/index.html"))
    if len(indicator_pages) != 179:
        raise RuntimeError(f"Schede indicatore preview: {len(indicator_pages)}, attese 179")

    print("Agricoltura II preview verificata: 183 indicatori, 179 schede inline, Stato dati 183.")


def main() -> None:
    original_site = SITE_DATA.read_bytes()
    original_registry = REGISTRY.read_bytes()
    try:
        data = json.loads(original_site.decode("utf-8"))
        overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        registry = json.loads(original_registry.decode("utf-8"))

        SITE_DATA.write_text(
            json.dumps(merge_overlay(data, overlay), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        REGISTRY.write_text(
            json.dumps(patch_registry(registry), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        runpy.run_path(str(ROOT / "scripts" / "build_static_brand.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "scripts" / "build_data_status.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "scripts" / "inject_data_status_runtime.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "scripts" / "build_pnrr_toscana_deep_dive.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "scripts" / "inject_pnrr_town_experience.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "scripts" / "copy_percorsi_dist.py"), run_name="__main__")
        append_draft_css()
        validate_preview()
    finally:
        SITE_DATA.write_bytes(original_site)
        REGISTRY.write_bytes(original_registry)


if __name__ == "__main__":
    main()
