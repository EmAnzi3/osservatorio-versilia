#!/usr/bin/env python3
"""Materializza i tre indicatori compositi approvati per il catalogo v1.9.0.

La trasformazione parte dallo snapshot grezzo versionato e aggiorna il dataset
canonico. Non viene eseguita durante il deploy.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "composite-indicators-v1.9.0.json"

AGE_LABELS = [
    "0–14 anni", "15–19 anni", "20–34 anni", "35–49 anni",
    "50–64 anni", "65–79 anni", "80 anni e oltre",
]
AGE_SELECTOR_LABELS = ["0–14", "15–19", "20–34", "35–49", "50–64", "65–79", "80+"]
INCOME_LABELS = [
    "Fino a 15.000 €", "15.001–26.000 €", "26.001–55.000 €", "Oltre 55.000 €",
]
MOBILITY_LABELS = [
    "Iscritti da altri Comuni", "Cancellati verso altri Comuni", "Saldo migratorio interno",
]
REMOVED_KEYS = {"share014", "share65", "incomeUnder15k"}


def percentage(count: int, total: float) -> float:
    return count / total * 100


def rate(count: int, population: float) -> float:
    return count / population * 1000


def percent_text(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def rate_text(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " ogni 1.000"


def town_meta(data: dict, town: str) -> dict:
    item = next(entry for entry in data["towns"] if entry["name"] == town)
    return {
        "town": town,
        "code": item["code"],
        "slug": town.lower().replace(" ", "-").replace("à", "a"),
    }


def population_by_year(data: dict, town: str) -> dict[int, int]:
    row = next(entry for entry in data["metrics"]["population"]["rows"] if entry["town"] == town)
    return dict(zip(row["series"]["years"], row["series"]["values"], strict=True))


def age_metric(data: dict, snapshot: dict) -> dict:
    rows = []
    aggregate_counts = [0] * len(AGE_LABELS)
    weighted_age = 0.0
    population_total = 0
    for town in snapshot["raw"]:
        raw = snapshot["raw"][town]
        counts = raw["ageBands"]
        total = sum(counts)
        parts = []
        for index, (label, count) in enumerate(zip(AGE_LABELS, counts, strict=True)):
            aggregate_counts[index] += count
            parts.append({
                "label": label,
                "selectorLabel": AGE_SELECTOR_LABELS[index],
                "value": percentage(count, total),
                "count": count,
            })
        average_age = raw["averageAge"]
        weighted_age += average_age * total
        population_total += total
        primary = parts[2]
        rows.append({
            **town_meta(data, town),
            "value": primary["value"],
            "formatted": percent_text(primary["value"]),
            "series": None,
            "normalized": None,
            "benchmarkValue": primary["value"],
            "parts": parts,
            "summaryValue": average_age,
        })

    aggregate_parts = [
        {"label": label, "count": count, "value": percentage(count, population_total)}
        for label, count in zip(AGE_LABELS, aggregate_counts, strict=True)
    ]
    return {
        "meta": {
            "key": "ageDistribution",
            "theme": "demografia",
            "label": "Distribuzione per fasce d’età",
            "shortLabel": "Distribuzione per fasce d’età",
            "description": "Quota dei residenti nelle fasce 0–14, 15–19, 20–34, 35–49, 50–64, 65–79 e 80 anni e oltre. Le fasce coprono l’intera popolazione senza sovrapposizioni.",
            "unit": "percent",
            "year": "2025",
            "source": "Istat — popolazione residente per età (POSAS)",
            "polarity": "neutral",
            "compositeType": "distribution",
            "searchTerms": ["fasce d'età", "giovani", "anziani", "struttura popolazione"],
            "summaryLabel": "Età media",
            "summaryUnit": "years",
            "selectorLabel": "Dato in evidenza",
        },
        "sourceUrl": snapshot["sources"]["ageDistribution"]["url"],
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[2]["value"],
            "label": "Versilia · 20–34 anni",
            "note": "Quota calcolata sul totale dei residenti dei sette comuni; nel dettaglio sono mostrate tutte le fasce.",
            "parts": aggregate_parts,
            "summaryValue": weighted_age / population_total,
            "summaryLabel": "Età media Versilia",
            "summaryNote": "Età media ponderata sulla popolazione dei sette comuni; la barra mostra la distribuzione completa per fascia.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio",
            "formula": "residenti della fascia / popolazione residente totale × 100; età media: indicatore Istat riferito alla stessa popolazione residente",
            "caveat": "Le fasce sono costruite dalla popolazione per singola età. L’età media comunale è verificata sulla Tavola 1e di Istat A misura di Comune, riferita al 31 dicembre 2024, la stessa data della popolazione POSAS al 1° gennaio 2025.",
            "coverage": "7/7",
        },
    }


def mobility_metric(data: dict, snapshot: dict) -> dict:
    rows = []
    aggregate_latest = [0, 0, 0]
    aggregate_population = 0.0
    for town in snapshot["raw"]:
        raw_series = snapshot["raw"][town]["internalResidentialMobility"]
        populations = population_by_year(data, town)
        years, inbound_rates, outbound_rates, balances = [], [], [], []
        for item in raw_series:
            year = item["year"]
            mean_population = (populations[year] + populations[year + 1]) / 2
            inbound = rate(item["registeredIn"], mean_population)
            outbound = rate(item["registeredOut"], mean_population)
            years.append(year)
            inbound_rates.append(inbound)
            outbound_rates.append(outbound)
            balances.append(inbound - outbound)
        latest = raw_series[-1]
        latest_population = (populations[2024] + populations[2025]) / 2
        counts = [latest["registeredIn"], latest["registeredOut"], latest["registeredIn"] - latest["registeredOut"]]
        values = [inbound_rates[-1], outbound_rates[-1], balances[-1]]
        aggregate_latest = [current + count for current, count in zip(aggregate_latest, counts, strict=True)]
        aggregate_population += latest_population
        parts = [
            {"label": label, "value": value, "count": count}
            for label, value, count in zip(MOBILITY_LABELS, values, counts, strict=True)
        ]
        rows.append({
            **town_meta(data, town),
            "value": balances[-1],
            "formatted": rate_text(balances[-1]),
            "series": {"years": years, "values": balances},
            "normalized": None,
            "benchmarkValue": balances[-1],
            "parts": parts,
            "componentSeries": {
                MOBILITY_LABELS[0]: {"years": years, "values": inbound_rates},
                MOBILITY_LABELS[1]: {"years": years, "values": outbound_rates},
                MOBILITY_LABELS[2]: {"years": years, "values": balances},
            },
        })
    aggregate_parts = [
        {"label": label, "value": rate(count, aggregate_population), "count": count}
        for label, count in zip(MOBILITY_LABELS, aggregate_latest, strict=True)
    ]
    return {
        "meta": {
            "key": "internalResidentialMobility",
            "theme": "demografia",
            "label": "Mobilità residenziale interna",
            "shortLabel": "Mobilità residenziale interna",
            "description": "Trasferimenti di residenza tra ciascun Comune e gli altri Comuni italiani: iscritti, cancellati e saldo, rapportati alla popolazione media annua.",
            "unit": "per1000",
            "year": "2024",
            "source": "Istat — bilancio demografico, trasferimenti di residenza",
            "polarity": "neutral",
            "compositeType": "mobility",
            "primaryLabel": "Saldo migratorio interno",
            "searchTerms": ["trasferimenti di residenza", "iscritti", "cancellati", "saldo migratorio interno"],
        },
        "sourceUrl": snapshot["sources"]["internalResidentialMobility"]["url"],
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[2]["value"],
            "label": "Versilia · saldo migratorio interno",
            "note": "Tasso calcolato sul totale dei trasferimenti dei sette comuni e sulla popolazione media annua complessiva.",
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio",
            "formula": "(iscritti da altri Comuni − cancellati verso altri Comuni) / popolazione media annua × 1.000; nel dettaglio sono riportati anche i due trasferimenti separati.",
            "caveat": "Riguarda trasferimenti anagrafici di residenza, non entrate o uscite pendolari per lavoro. Non consente di attribuire cause individuali ai trasferimenti.",
            "coverage": "7/7",
        },
    }


def income_metric(data: dict, snapshot: dict) -> dict:
    income_rows = {row["town"]: row for row in data["metrics"]["income"]["rows"]}
    rows = []
    aggregate_counts = [0] * len(INCOME_LABELS)
    weighted_income = 0.0
    declarants_total = 0
    for town in snapshot["raw"]:
        counts = snapshot["raw"][town]["incomeBands"]
        total = sum(counts)
        parts = []
        for index, (label, count) in enumerate(zip(INCOME_LABELS, counts, strict=True)):
            aggregate_counts[index] += count
            parts.append({"label": label, "value": percentage(count, total), "count": count})
        average_income = income_rows[town]["value"]
        weighted_income += average_income * total
        declarants_total += total
        rows.append({
            **town_meta(data, town),
            "value": parts[0]["value"],
            "formatted": percent_text(parts[0]["value"]),
            "series": None,
            "normalized": None,
            "benchmarkValue": parts[0]["value"],
            "parts": parts,
            "summaryValue": average_income,
        })
    aggregate_parts = [
        {"label": label, "count": count, "value": percentage(count, declarants_total)}
        for label, count in zip(INCOME_LABELS, aggregate_counts, strict=True)
    ]
    return {
        "meta": {
            "key": "incomeDistribution",
            "theme": "economia",
            "label": "Distribuzione dei dichiaranti per fascia di reddito",
            "shortLabel": "Distribuzione per fascia di reddito",
            "description": "Distribuzione dei dichiaranti in quattro fasce esclusive ricavate dalle classi ufficiali MEF: fino a 15.000 €, 15.001–26.000 €, 26.001–55.000 € e oltre 55.000 €.",
            "unit": "percent",
            "year": "2024",
            "source": "Dipartimento delle Finanze — MEF",
            "polarity": "neutral",
            "compositeType": "distribution",
            "searchTerms": ["fasce reddito", "irpef", "dichiaranti", "distribuzione redditi"],
            "summaryLabel": "Reddito medio",
            "summaryUnit": "currency",
            "selectorLabel": "Dato in evidenza",
        },
        "sourceUrl": snapshot["sources"]["incomeDistribution"]["url"],
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Versilia · fino a 15.000 €",
            "note": "Quota ponderata sul numero di dichiaranti presenti nelle classi di reddito dei sette comuni.",
            "parts": aggregate_parts,
            "summaryValue": weighted_income / declarants_total,
            "summaryLabel": "Reddito medio Versilia",
            "summaryNote": "Reddito medio ponderato dei dichiaranti dei sette comuni; la barra mostra la distribuzione completa per fascia.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio",
            "formula": "numero di dichiaranti della fascia / totale dichiaranti presenti nelle classi di reddito × 100",
            "caveat": "Le quattro fasce sono esclusive e ottenute soltanto sommando le classi statistiche ufficiali MEF indicate nello snapshot, senza interpolazioni. Non coincidono con gli scaglioni fiscali IRPEF vigenti.",
            "coverage": "7/7",
        },
    }


def update_themes(data: dict) -> None:
    demography = data["themes"]["demografia"]
    demography["metrics"] = [
        "population", "ageDistribution", "oldAgeIndex",
        "internalResidentialMobility", "populationChange",
    ]
    demography["sections"] = [
        {
            "key": "quadro",
            "label": "Consistenza e struttura",
            "description": "Quanti siamo e come si distribuisce la popolazione per età.",
            "metrics": ["population", "ageDistribution", "oldAgeIndex"],
        },
        {
            "key": "mobilita-residenziale",
            "label": "Mobilità residenziale",
            "description": "Trasferimenti di residenza tra ciascun Comune e gli altri Comuni italiani.",
            "metrics": ["internalResidentialMobility"],
        },
        {
            "key": "dinamica",
            "label": "Dinamica demografica",
            "description": "Come cambia nel tempo il numero dei residenti.",
            "metrics": ["populationChange"],
        },
    ]
    demography["featured"] = ["population", "oldAgeIndex", "populationChange"]

    economy = data["themes"]["economia"]
    economy["metrics"] = [
        "incomeDistribution" if key == "incomeUnder15k" else key
        for key in economy["metrics"]
    ]
    for section in economy["sections"]:
        if section["key"] == "redditi":
            section["description"] = "Livello medio e distribuzione dei redditi dichiarati."
            section["metrics"] = ["income", "incomeDistribution"]


def update_dataset() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    generated = {
        "ageDistribution": age_metric(data, snapshot),
        "internalResidentialMobility": mobility_metric(data, snapshot),
        "incomeDistribution": income_metric(data, snapshot),
    }
    update_themes(data)

    metrics = OrderedDict()
    for key, metric in data["metrics"].items():
        if key in REMOVED_KEYS or key in generated:
            continue
        metrics[key] = metric
        if key == "population":
            metrics["ageDistribution"] = generated["ageDistribution"]
        elif key == "oldAgeIndex":
            metrics["internalResidentialMobility"] = generated["internalResidentialMobility"]
        elif key == "income":
            metrics["incomeDistribution"] = generated["incomeDistribution"]
    data["metrics"] = metrics

    external_metrics = {
        key for key, metric in metrics.items()
        if metric.get("dataStorage", {}).get("type") == "external-climate"
    }
    inline_metric_count = len(metrics) - len(external_metrics)
    if len(metrics) != 115 or inline_metric_count != 111 or len(external_metrics) != 4:
        raise RuntimeError(
            "Conteggio inatteso: "
            f"{len(metrics)} indicatori canonici, "
            f"{inline_metric_count} con valori incorporati e "
            f"{len(external_metrics)} climatici esterni"
        )
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    update_dataset()
    print("Indicatori compositi materializzati: 115 canonici = 111 con valori incorporati + 4 climatici esterni.")
