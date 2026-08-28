#!/usr/bin/env python3
"""Finalizza e valida il contratto del catalogo pubblico v1.22.0.

Le trasformazioni tematiche restano nei rispettivi materializzatori. Questo
passaggio assegna soltanto i metadati di release e impedisce la pubblicazione di
un catalogo con indicatori orfani, duplicati o conteggi non riconciliati.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"

VERSION = "v1.22.0"
UPDATED = "28 agosto 2026"
EXPECTED_TOWNS = 7
EXPECTED_THEMES = 11
EXPECTED_METRICS = 157
EXPECTED_INLINE = 153
EXPECTED_EXTERNAL = 4


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finalize(site: dict, registry: dict) -> None:
    site["version"] = VERSION
    site["updated"] = UPDATED
    registry["expectedMetricCount"] = EXPECTED_METRICS
    registry["expectedInlineMetricCount"] = EXPECTED_INLINE
    registry["expectedExternalMetricCount"] = EXPECTED_EXTERNAL


def validate(site: dict, registry: dict) -> None:
    metrics = site.get("metrics", {})
    themes = site.get("themes", {})
    if len(site.get("towns", [])) != EXPECTED_TOWNS:
        raise RuntimeError(f"Comuni attesi: {EXPECTED_TOWNS}; trovati: {len(site.get('towns', []))}")
    if len(themes) != EXPECTED_THEMES:
        raise RuntimeError(f"Temi attesi: {EXPECTED_THEMES}; trovati: {len(themes)}")
    if len(metrics) != EXPECTED_METRICS:
        raise RuntimeError(f"Indicatori attesi: {EXPECTED_METRICS}; trovati: {len(metrics)}")

    external = {
        key for key, metric in metrics.items()
        if metric.get("dataStorage", {}).get("type") == "external-climate"
    }
    if len(external) != EXPECTED_EXTERNAL:
        raise RuntimeError(f"Indicatori climatici esterni attesi: {EXPECTED_EXTERNAL}; trovati: {len(external)}")
    if len(metrics) - len(external) != EXPECTED_INLINE:
        raise RuntimeError("La ripartizione fra indicatori incorporati ed esterni non riconcilia")

    references: list[str] = []
    for theme_key, theme in themes.items():
        theme_metrics = list(theme.get("metrics", []))
        if len(theme_metrics) != len(set(theme_metrics)):
            raise RuntimeError(f"{theme_key}: indicatore duplicato nell'elenco del tema")
        section_metrics = [
            key
            for section in theme.get("sections", [])
            for key in section.get("metrics", [])
        ]
        if Counter(section_metrics) != Counter(theme_metrics):
            raise RuntimeError(f"{theme_key}: sezioni e catalogo del tema non coincidono")
        references.extend(theme_metrics)

    counts = Counter(references)
    missing = sorted(set(metrics) - set(counts))
    unknown = sorted(set(counts) - set(metrics))
    duplicated = sorted(key for key, count in counts.items() if count != 1)
    if missing or unknown or duplicated:
        raise RuntimeError(
            f"Riferimenti tematici incoerenti; orfani={missing}, sconosciuti={unknown}, duplicati={duplicated}"
        )

    expected_registry = {
        "expectedMetricCount": EXPECTED_METRICS,
        "expectedInlineMetricCount": EXPECTED_INLINE,
        "expectedExternalMetricCount": EXPECTED_EXTERNAL,
    }
    actual_registry = {key: registry.get(key) for key in expected_registry}
    if actual_registry != expected_registry:
        raise RuntimeError(f"Conteggi source-registry incoerenti: {actual_registry}")
    if site.get("version") != VERSION or site.get("updated") != UPDATED:
        raise RuntimeError("Metadati di versione pubblica non finalizzati")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fallisce se i file richiedono modifiche")
    args = parser.parse_args()

    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    desired_site = copy.deepcopy(site)
    desired_registry = copy.deepcopy(registry)
    finalize(desired_site, desired_registry)
    validate(desired_site, desired_registry)

    if args.check:
        if desired_site != site or desired_registry != registry:
            raise SystemExit("Il catalogo non è finalizzato: eseguire scripts/finalize_catalog_release.py")
    else:
        if desired_site != site:
            save(SITE_PATH, desired_site)
        if desired_registry != registry:
            save(REGISTRY_PATH, desired_registry)

    print(
        f"Catalogo {VERSION} verificato: {EXPECTED_METRICS} indicatori "
        f"({EXPECTED_INLINE} incorporati + {EXPECTED_EXTERNAL} esterni), "
        f"{EXPECTED_THEMES} temi, {EXPECTED_TOWNS}/7 Comuni."
    )


if __name__ == "__main__":
    main()
