#!/usr/bin/env python3
"""Build wrapper for the Agricoltura II review artifact.

The canonical source catalog stays unchanged on the branch. For the duration of
this build only, the approved Agricoltura II overlay is merged into site-data so
the static prerender, indicator routes and browser bundle all see the same 183
indicator catalog. The original source file is restored byte-for-byte in a
finally block.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"
OVERLAY = ROOT / "data" / "agricoltura-ii-draft.json"
BASE_BUILD = ROOT / "scripts" / "build_static_brand_base.py"
DIST = ROOT / "dist"


def merge_agricoltura_ii(data: dict, overlay: dict) -> dict:
    before = len(data.get("metrics", {}))
    metrics = overlay.get("metrics", {})
    expected = {
        "agriculturalRenewalAndLeadership",
        "agriculturalDiversificationAndModernization",
    }
    if set(metrics) != expected:
        raise RuntimeError(f"Metriche Agricoltura II inattese: {sorted(metrics)}")

    data["metrics"].update(metrics)
    theme_key = overlay["theme"]
    section_key = overlay["section"]
    theme = data["themes"][theme_key]
    section = next((item for item in theme.get("sections", []) if item.get("key") == section_key), None)
    if section is None:
        raise RuntimeError(f"Sezione {theme_key}/{section_key} non trovata")

    additions = list(overlay.get("metricOrder", []))
    section["label"] = overlay.get("sectionLabel", section.get("label"))
    section["description"] = overlay.get("sectionDescription", section.get("description"))
    section["metrics"] = [key for key in section.get("metrics", []) if key not in additions] + additions
    theme["metrics"] = [key for item in theme.get("sections", []) for key in item.get("metrics", [])]
    data["version"] = overlay.get("versionLabel", data.get("version"))
    data["updated"] = overlay.get("updatedLabel", data.get("updated"))

    after = len(data["metrics"])
    if after != before + 2:
        raise RuntimeError(f"Catalogo inatteso: {before} -> {after}, atteso +2")
    return data


def validate_dist() -> None:
    dist_data = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    for key in (
        "agriculturalRenewalAndLeadership",
        "agriculturalDiversificationAndModernization",
    ):
        if key not in dist_data.get("metrics", {}):
            raise RuntimeError(f"Artifact privo della metrica {key}")

    if len(dist_data.get("metrics", {})) != 183:
        raise RuntimeError(f"Artifact con {len(dist_data.get('metrics', {}))} metriche; attese 183")

    home = (DIST / "index.html").read_text(encoding="utf-8")
    ambiente = (DIST / "confronta" / "ambiente" / "index.html").read_text(encoding="utf-8")
    if "183 indicatori" not in home:
        raise RuntimeError("Home prerender non espone 183 indicatori")
    for label in (
        "Ricambio e conduzione delle aziende agricole",
        "Diversificazione e modernizzazione delle aziende agricole",
    ):
        if label not in ambiente:
            raise RuntimeError(f"Card Agricoltura II assente dal prerender: {label}")

    css_source = (ROOT / "assets" / "agricoltura-ii-draft.css").read_text(encoding="utf-8")
    static_css = DIST / "assets" / "static.css"
    static_css.write_text(
        static_css.read_text(encoding="utf-8") + "\n\n" + css_source + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    original = SITE_DATA.read_bytes()
    try:
        data = json.loads(original.decode("utf-8"))
        overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        merged = merge_agricoltura_ii(data, overlay)
        SITE_DATA.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runpy.run_path(str(BASE_BUILD), run_name="__main__")
        validate_dist()
        print("Agricoltura II preview: prerender verificato a 183 indicatori.")
    finally:
        SITE_DATA.write_bytes(original)
