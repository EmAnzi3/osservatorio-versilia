#!/usr/bin/env python3
"""Completa il Lotto A Amministrazione con la formazione del personale RGS 2024.

La v1 materializza dotazione, turnover ed età; questa estensione aggiunge un
quarto indicatore mantenendo i valori esattamente come pubblicati dalla fonte
RGS. In particolare, non reinterpretata la "Media Totale" come giornate per
organico: il sito la espone esplicitamente come valore RGS e mostra a fianco
anche giornate complessive e medie per genere.
"""
from __future__ import annotations

import json
from pathlib import Path

import materialize_amministrazione_lotto_a as base

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
MONITOR_PATH = ROOT / "data" / "source-monitor-state.json"
TRAINING_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "rgs-formazione-2024.json"

TRAINING_KEY = "municipalStaffTraining"
RGS_TRAINING_URL = "https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc"
PROFILE = base.PROFILE


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def training_parts(raw: dict) -> list[dict]:
    return [
        {
            "label": "Media totale RGS",
            "selectorLabel": "Media totale RGS",
            "value": float(raw["meanTotalRgs"]),
            "unit": "decimal",
        },
        {
            "label": "Giornate complessive",
            "selectorLabel": "Giornate complessive",
            "value": int(raw["totalDays"]),
            "unit": "number",
        },
        {
            "label": "Media uomini RGS",
            "selectorLabel": "Media uomini",
            "value": float(raw["meanMen"]),
            "unit": "decimal",
        },
        {
            "label": "Media donne RGS",
            "selectorLabel": "Media donne",
            "value": float(raw["meanWomen"]),
            "unit": "decimal",
        },
    ]


def training_metric(site: dict, snapshot: dict) -> dict:
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    rows = []
    for town in order:
        raw = snapshot["towns"][town]
        if int(raw["menDays"]) + int(raw["womenDays"]) != int(raw["totalDays"]):
            raise RuntimeError(f"{town}: giornate formazione per genere non riconciliate")
        expected_mean = (float(raw["meanMen"]) + float(raw["meanWomen"])) / 2
        if abs(float(raw["meanTotalRgs"]) - expected_mean) > 1e-9:
            raise RuntimeError(f"{town}: Media Totale RGS non riconciliata")
        parts = training_parts(raw)
        rows.append({
            **base.identity(site, town),
            "value": parts[0]["value"],
            "formatted": f"{parts[0]['value']:.2f}".replace(".", ","),
            "series": None,
            "normalized": None,
            "benchmarkValue": parts[0]["value"],
            "parts": parts,
        })

    aggregate_raw = snapshot["versilia"]
    if int(aggregate_raw["menDays"]) + int(aggregate_raw["womenDays"]) != int(aggregate_raw["totalDays"]):
        raise RuntimeError("Versilia: giornate formazione per genere non riconciliate")
    aggregate_parts = training_parts(aggregate_raw)

    return {
        "meta": {
            "key": TRAINING_KEY,
            "theme": "bilanci",
            "label": "Formazione del personale comunale",
            "shortLabel": "Formazione del personale",
            "description": (
                "Giornate di formazione rilevate dal Conto Annuale RGS. La lettura predefinita è la “Media Totale” "
                "pubblicata dalla fonte; il selettore mostra anche le giornate complessive e le medie per genere."
            ),
            "unit": "decimal",
            "year": "2024",
            "source": "RGS — Conto Annuale",
            "polarity": "neutral",
            "compositeType": "securityMeasures",
            "selectorLabel": "Lettura formazione",
            "searchTerms": [
                "formazione personale", "giorni formazione", "dipendenti comunali formazione",
                "media formazione", "aggiornamento personale", "conto annuale formazione",
            ],
        },
        "sourceUrl": RGS_TRAINING_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Versilia · Media totale RGS",
            "note": (
                "Valori restituiti direttamente dall’API RGS selezionando insieme i sette Comuni della Versilia; "
                "non è la media semplice dei sette valori comunali."
            ),
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Valori ufficiali RGS — Conto Annuale",
            "formula": (
                "Nessuna formula applicata ai valori pubblicati. Nel payload 2024 la Media Totale RGS coincide, "
                "per tutti i sette Comuni e per la selezione congiunta, con (Media Uomini + Media Donne) / 2."
            ),
            "caveat": (
                "La Media Totale RGS non viene presentata come giornate complessive divise per il numero di dipendenti. "
                "Le giornate complessive sono disponibili come lettura separata. Un valore più alto non misura da solo "
                "la qualità, la pertinenza o l’efficacia della formazione."
            ),
            "coverage": "7/7",
            "history": (
                "RGS espone annualità dal 2008 al 2024 e documenta l’andamento storico delle giornate di formazione; "
                "questa prima materializzazione comunale usa il 2024 verificato 7/7."
            ),
        },
    }


def update_theme(site: dict) -> None:
    theme = site["themes"]["bilanci"]
    theme["metrics"] = [key for key in theme.get("metrics", []) if key != TRAINING_KEY]
    theme["metrics"].append(TRAINING_KEY)
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    section["metrics"] = [key for key in section.get("metrics", []) if key != TRAINING_KEY]
    section["metrics"].append(TRAINING_KEY)
    section["description"] = (
        "Dotazione di personale, ricambio dell'organico, sostenibilità generazionale e formazione della macchina comunale."
    )


def update_registry(registry: dict, site: dict) -> None:
    registry.setdefault("metricOverrides", {})[TRAINING_KEY] = {"profile": PROFILE}
    registry.setdefault("sourceProfileByUrl", {})[RGS_TRAINING_URL] = PROFILE
    external = sum(
        1 for metric in site["metrics"].values()
        if metric.get("dataStorage", {}).get("type") == "external-climate"
    )
    registry["expectedMetricCount"] = len(site["metrics"])
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(site["metrics"]) - external


def update_monitor(monitor: dict) -> None:
    sources = monitor.setdefault("sources", {})
    state = sources.setdefault(RGS_TRAINING_URL, {
        "url": RGS_TRAINING_URL,
        "ok": True,
        "status": 200,
        "finalUrl": RGS_TRAINING_URL,
        "contentType": "text/html",
        "contentLength": None,
        "etag": "",
        "lastModified": "",
        "contentSha256": "",
        "hashTruncated": False,
        "error": "",
        "metrics": [],
        "roles": ["primary"],
        "profileIds": [PROFILE],
        "frequencies": ["annual"],
    })
    state["metrics"] = sorted(set(state.get("metrics", [])) | {TRAINING_KEY})
    state["profileIds"] = sorted(set(state.get("profileIds", [])) | {PROFILE})
    state["frequencies"] = sorted(set(state.get("frequencies", [])) | {"annual"})


def main() -> None:
    base.main()

    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    snapshot = load(TRAINING_SNAPSHOT_PATH)

    site["metrics"].pop(TRAINING_KEY, None)
    site["metrics"][TRAINING_KEY] = training_metric(site, snapshot)
    update_theme(site)
    update_registry(registry, site)
    update_monitor(monitor)

    if len(site["metrics"]) != 137:
        raise RuntimeError(f"Conteggio inatteso dopo formazione: {len(site['metrics'])}")

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    print("Amministrazione Lotto A v2: 137 indicatori totali; formazione RGS 2024 materializzata 7/7.")


if __name__ == "__main__":
    main()
