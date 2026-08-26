#!/usr/bin/env python3
"""Contratto pubblico e metodologico della release v1.19.0."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from finalize_catalog_release import (
    EXPECTED_EXTERNAL,
    EXPECTED_INLINE,
    EXPECTED_METRICS,
    EXPECTED_THEMES,
    EXPECTED_TOWNS,
    UPDATED,
    VERSION,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def formatted_strings(value, path: str = "root"):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "formatted" and isinstance(item, str):
                yield path + ".formatted", item
            yield from formatted_strings(item, path + "." + str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from formatted_strings(item, f"{path}[{index}]")


def main() -> None:
    site = load(ROOT / "data" / "site-data.json")
    registry = load(ROOT / "data" / "source-registry.json")
    assert site["version"] == VERSION and site["updated"] == UPDATED
    assert len(site["towns"]) == EXPECTED_TOWNS
    assert len(site["themes"]) == EXPECTED_THEMES
    assert len(site["metrics"]) == EXPECTED_METRICS
    assert registry["expectedMetricCount"] == EXPECTED_METRICS
    assert registry["expectedInlineMetricCount"] == EXPECTED_INLINE
    assert registry["expectedExternalMetricCount"] == EXPECTED_EXTERNAL

    references = [key for theme in site["themes"].values() for key in theme["metrics"]]
    assert Counter(references) == Counter({key: 1 for key in site["metrics"]}), "Indicatori orfani o duplicati nei temi"
    for theme in site["themes"].values():
        section_refs = [key for section in theme["sections"] for key in section["metrics"]]
        assert Counter(section_refs) == Counter(theme["metrics"])

    lavoro = site["themes"]["lavoro"]
    gender = next(section for section in lavoro["sections"] if section["key"] == "genere")
    assert gender["label"] == "Serie storiche 15–64"
    assert gender["metrics"] == ["femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"]
    assert "2021–2023" in gender["description"] and "2024" in gender["description"]

    age_method = site["metrics"]["ageDistribution"]["method"]
    disclosure = " ".join(str(age_method.get(key, "")) for key in ("formula", "caveat", "detail"))
    assert "1° gennaio 2026" in disclosure and "singola età" in disclosure
    assert "31 dicembre 2024" not in disclosure and "1° gennaio 2025" not in disclosure
    assert "età media" in age_method["formula"]

    malformed = [(path, value) for path, value in formatted_strings(site) if "ogni 1,000" in value]
    assert not malformed, f"Separatore delle migliaia corrotto: {malformed[:3]}"

    app = (ROOT / "assets" / "app-parts" / "05.txt").read_text(encoding="utf-8")
    assert "2026.08.26-v1.19.0" in app and "149 indicatori complessivi" in app
    assert "2026.08.20-v1.15.0" in app and "2026.08.20-v1.14.0" in app
    chart_app = (ROOT / "assets" / "app-parts" / "03.txt").read_text(encoding="utf-8")
    assert 'part.count === null || part.count === undefined' in chart_app, 'Le distribuzioni senza conteggi non devono mostrare NaN'
    for token in (
        "function demographicAgeOptionsMarkup(",
        'data-lavoro-istruzione-pyramid="1"',
        'id="compare-demographic-pyramid"',
        "function demographicRateTooltipMarkup(",
    ):
        assert token in chart_app, f"UI età×genere non canonicalizzata: {token}"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "**v1.19.0** — 26 agosto 2026" in readme
    assert "149 indicatori" in readme and "145 con valori incorporati" in readme
    build_safe = (ROOT / "scripts" / "build_static_safe.py").read_text(encoding="utf-8")
    build_brand = (ROOT / "scripts" / "build_static_brand.py").read_text(encoding="utf-8")
    development_loader = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert 'UX_ASSET_VERSION = "20260826-v119"' in build_safe
    assert 'APP_BUNDLE_ASSET_VERSION = "20260826-v119"' in build_brand
    assert 'CHART_SURFACE_ASSET_VERSION = "20260826-v119"' in build_brand
    assert 'PWA_JS_REVISION = "catalog-v119"' in build_brand
    assert "const VERSION = '20260826-v119'" in development_loader
    assert "ov-pwa-20260826-v119" in service_worker

    print(
        f"Release {VERSION} verificata: catalogo completo, tooltip coerenti, "
        f"{EXPECTED_METRICS} indicatori tutti assegnati a un tema e UI età×genere canonica."
    )


if __name__ == "__main__":
    main()
