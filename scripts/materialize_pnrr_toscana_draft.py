#!/usr/bin/env python3
"""Materializza la bozza PNRR Regione Toscana per il solo preview di PR.

Lo script aggiorna la working copy, non scarica dati e non pubblica nulla. I valori
sono la fotografia Regione Toscana dell'11 agosto 2026 già validata dal workflow
forense della PR #75. Serve a vedere il risultato nel preview prima di rendere
canonico l'aggiornamento.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
SOURCE_LABEL = "Regione Toscana — Open Data PNRR"
SNAPSHOT_LABEL = "11 agosto 2026"
PROFILE_KEY = "regione-toscana-pnrr-monthly"

# Fotografia validata: area PNRR o PNRR-PNC; PNC puro escluso; Comune soggetto
# attuatore; deduplicazione su id_progetto; importo = importo_finanziato_pnrr;
# concluso = fase_avanzamento_da_regis == "5. conclusione".
PNRR = {
    "046005": {"town": "Camaiore", "projects": 16, "concluded": 10, "funding": 3270511.41},
    "046013": {"town": "Forte dei Marmi", "projects": 15, "concluded": 10, "funding": 1337644.46},
    "046018": {"town": "Massarosa", "projects": 11, "concluded": 10, "funding": 5965208.14},
    "046024": {"town": "Pietrasanta", "projects": 12, "concluded": 9, "funding": 9478237.98},
    "046028": {"town": "Seravezza", "projects": 12, "concluded": 8, "funding": 2485485.63},
    "046030": {"town": "Stazzema", "projects": 11, "concluded": 9, "funding": 2055502.34},
    "046033": {"town": "Viareggio", "projects": 24, "concluded": 18, "funding": 12090517.68},
}


def rows_by_code(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    return {
        str(row.get("code")): row
        for row in rows
        if isinstance(row, dict) and row.get("code")
    }


def patch_nested_pnrr_bundle(node: Any, values: dict[str, Any]) -> int:
    """Aggiorna i blocchi riepilogativi già presenti nelle schede comunali."""
    patched = 0
    if isinstance(node, dict):
        required = {"pnrrProjects", "pnrrConcluded", "pnrrInProgress", "pnrrFunding"}
        if required.issubset(node):
            node["pnrrProjects"] = values["projects"]
            node["pnrrConcluded"] = values["concluded"]
            node["pnrrInProgress"] = values["projects"] - values["concluded"]
            node["pnrrFunding"] = values["funding"]
            patched += 1
        for child in node.values():
            patched += patch_nested_pnrr_bundle(child, values)
    elif isinstance(node, list):
        for child in node:
            patched += patch_nested_pnrr_bundle(child, values)
    return patched


def patch_town_summaries(data: dict[str, Any]) -> dict[str, int]:
    counts = {code: 0 for code in PNRR}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in PNRR and isinstance(child, (dict, list)):
                    counts[key] += patch_nested_pnrr_bundle(child, PNRR[key])
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(data)
    missing = [code for code, count in counts.items() if count == 0]
    if missing:
        raise RuntimeError(f"Riepilogo PNRR comunale non trovato per: {', '.join(missing)}")
    return counts


def patch_site_data(data: dict[str, Any]) -> None:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo metrics assente")
    population = rows_by_code(metrics["population"])
    funding_metric = metrics["pnrrFunding"]
    concluded_metric = metrics["pnrrConcluded"]
    funding_rows = rows_by_code(funding_metric)
    concluded_rows = rows_by_code(concluded_metric)

    for code, values in PNRR.items():
        pop = population.get(code, {}).get("value")
        if not isinstance(pop, (int, float)) or pop <= 0:
            raise RuntimeError(f"Popolazione non valida per {code}")
        if code not in funding_rows or code not in concluded_rows:
            raise RuntimeError(f"Riga PNRR assente per {code}")
        funding_rows[code]["value"] = values["funding"] / float(pop)
        concluded_rows[code]["value"] = values["concluded"] / values["projects"] * 100.0

    funding_meta = funding_metric.setdefault("meta", {})
    funding_meta.update(
        {
            "year": "2026",
            "source": SOURCE_LABEL,
            "description": (
                "Importo PNRR assegnato ai progetti PNRR o PNRR-PNC con il comune "
                "come soggetto attuatore, rapportato alla popolazione."
            ),
        }
    )
    funding_metric["sourceUrl"] = DATASET_URL
    funding_method = funding_metric.setdefault("method", {})
    funding_method.update(
        {
            "type": "Elaborazione Osservatorio su open data Regione Toscana",
            "formula": "somma importo_finanziato_pnrr / popolazione residente",
            "caveat": (
                "Fotografia Regione Toscana 11 agosto 2026. Inclusi PNRR e PNRR-PNC con Comune "
                "soggetto attuatore; escluso PNC puro; deduplicazione su id_progetto. Il valore è "
                "finanziamento PNRR censito, non importo erogato o speso."
            ),
            "coverage": "7/7",
        }
    )

    concluded_meta = concluded_metric.setdefault("meta", {})
    concluded_meta.update(
        {
            "year": "2026",
            "source": SOURCE_LABEL,
            "description": (
                "Quota dei progetti PNRR o PNRR-PNC con il comune come soggetto attuatore "
                "classificati da ReGiS nella fase 5. conclusione."
            ),
        }
    )
    concluded_metric["sourceUrl"] = DATASET_URL
    concluded_method = concluded_metric.setdefault("method", {})
    concluded_method.update(
        {
            "type": "Elaborazione Osservatorio su open data Regione Toscana / ReGiS",
            "formula": "progetti con fase_avanzamento_da_regis = 5. conclusione / progetti selezionati × 100",
            "caveat": (
                "Fotografia Regione Toscana 11 agosto 2026. Inclusi PNRR e PNRR-PNC con Comune "
                "soggetto attuatore; escluso PNC puro; deduplicazione su id_progetto. La fase ReGiS "
                "è uno stato amministrativo di avanzamento e non equivale, da sola, a collaudo concluso."
            ),
            "coverage": "7/7",
        }
    )

    patch_town_summaries(data)
    data["updated"] = "18 agosto 2026"


def patch_registry(registry: dict[str, Any]) -> None:
    profiles = registry.setdefault("sourceProfiles", {})
    profiles[PROFILE_KEY] = {
        "publisher": "Regione Toscana",
        "frequency": "monthly",
        "frequencyLabel": "Mensile",
        "expectedRelease": "Aggiornamento di norma mensile",
        "acquisitionMethod": (
            "CSV ufficiale Regione Toscana; selezione area PNRR o PNRR-PNC, esclusione PNC puro, "
            "Comune come soggetto attuatore, deduplicazione su id_progetto e verifica delle fasi ReGiS."
        ),
        "licenseName": "Creative Commons Attribuzione",
        "licenseUrl": DATASET_URL,
    }
    by_url = registry.setdefault("sourceProfileByUrl", {})
    by_url[DATASET_URL] = PROFILE_KEY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--registry", type=Path, default=Path("data/source-registry.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    patch_site_data(data)
    patch_registry(registry)
    args.data.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.registry.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Bozza PNRR Regione Toscana materializzata: "
        f"{sum(v['projects'] for v in PNRR.values())} progetti, "
        f"{sum(v['concluded'] for v in PNRR.values())} conclusi, "
        f"€{sum(v['funding'] for v in PNRR.values()):,.2f} PNRR"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
