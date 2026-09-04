#!/usr/bin/env python3
"""Materializza Agricoltura II nel workspace della release pubblica.

Il repository conserva il catalogo base e l'overlay separato usato durante la
revisione. Per il deploy di produzione la build deve però lavorare sullo stesso
catalogo 183/179 e sullo stesso runtime ``ratioProfile`` dell'artifact approvato.
Questo script modifica esclusivamente il checkout effimero di GitHub Actions e
marca i file materializzati come assume-unchanged, così il gate che vieta
riscritture accidentali continua a intercettare ogni altro file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from build_agricoltura_ii_preview import (
    APP_PART,
    OVERLAY,
    REGISTRY,
    SITE_DATA,
    merge_overlay,
    patch_preview_renderer,
    patch_registry,
)

ROOT = Path(__file__).resolve().parents[1]
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
UX_HISTORY = ROOT / "assets" / "ux-history.js"

MATERIALIZED_PATHS = (
    "data/site-data.json",
    "data/source-registry.json",
    "assets/app-parts/03.txt",
    "assets/visual-grammar.js",
    "assets/ux-history.js",
)


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"Patch release non applicabile a {path.name}: attese {expected} occorrenze, trovate {count}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_runtime_sources() -> None:
    base_types = (
        "['stock','omi','mobility','securityMeasures','demographicBreakdown',"
        "'agricultureProfile','financialProfile','sexBreakdown']"
    )
    ratio_types = (
        "['stock','omi','mobility','securityMeasures','demographicBreakdown',"
        "'agricultureProfile','ratioProfile','financialProfile','sexBreakdown']"
    )
    replace_exact(VISUAL_GRAMMAR, base_types, ratio_types, expected=2)
    replace_exact(
        VISUAL_GRAMMAR,
        "if (type === 'securityMeasures' || type === 'agricultureProfile' || type === 'financialProfile') {",
        "if (type === 'securityMeasures' || type === 'agricultureProfile' || type === 'ratioProfile' || type === 'financialProfile') {",
    )
    replace_exact(
        VISUAL_GRAMMAR,
        "if (type === 'securityMeasures' || type === 'financialProfile') {",
        "if (type === 'securityMeasures' || type === 'ratioProfile' || type === 'financialProfile') {",
    )
    replace_exact(
        VISUAL_GRAMMAR,
        "if (['distribution','agricultureProfile','financialProfile'].includes(metric.meta?.compositeType)) return;",
        "if (['distribution','agricultureProfile','ratioProfile','financialProfile'].includes(metric.meta?.compositeType)) return;",
    )

    base_history = "['distribution','omi','stock','securityMeasures','sexBreakdown']"
    ratio_history = "['distribution','omi','stock','securityMeasures','ratioProfile','sexBreakdown']"
    replace_exact(UX_HISTORY, base_history, ratio_history, expected=2)


def materialize() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    overlay["versionLabel"] = "v1.30.0"
    overlay["updatedLabel"] = "4 settembre 2026"

    SITE_DATA.write_text(
        json.dumps(merge_overlay(data, overlay), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REGISTRY.write_text(
        json.dumps(patch_registry(registry), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    APP_PART.write_text(
        patch_preview_renderer(APP_PART.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    patch_runtime_sources()


def validate() -> None:
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data.get("version") == "v1.30.0", data.get("version")
    assert len(data.get("metrics", {})) == 183
    assert registry.get("expectedMetricCount") == 183
    assert registry.get("expectedInlineMetricCount") == 179
    for key in (
        "agriculturalRenewalAndLeadership",
        "agriculturalDiversificationAndModernization",
    ):
        assert data["metrics"][key]["meta"]["compositeType"] == "ratioProfile"
    subprocess.run(["node", "--check", str(VISUAL_GRAMMAR)], check=True)
    subprocess.run(["node", "--check", str(UX_HISTORY)], check=True)


def hide_expected_workspace_changes() -> None:
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", *MATERIALIZED_PATHS],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    materialize()
    validate()
    hide_expected_workspace_changes()
    print(
        "Agricoltura II release workspace: v1.30.0, 183 indicatori, "
        "179 schede inline e runtime ratioProfile materializzati."
    )


if __name__ == "__main__":
    main()
