#!/usr/bin/env python3
"""Arricchisce 5 indicatori esistenti con fascia d'età e genere, senza nuovi indicatori."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-lavoro-istruzione-eta-genere-2024.json"

GENDERS = [
    {"key": "total", "label": "Totale"},
    {"key": "men", "label": "Uomini"},
    {"key": "women", "label": "Donne"},
]
LABOUR_AGES = [
    {"key": "15-24", "label": "15–24 anni", "group": "Fasce non sovrapposte"},
    {"key": "25-49", "label": "25–49 anni", "group": "Fasce non sovrapposte"},
    {"key": "50-64", "label": "50–64 anni", "group": "Fasce non sovrapposte"},
    {"key": "65plus", "label": "65 anni e oltre", "group": "Fasce non sovrapposte"},
    {"key": "25-64", "label": "25–64 anni", "group": "Aggregati"},
    {"key": "15plus", "label": "15 anni e oltre", "group": "Aggregati"},
]
EDUCATION_AGES = [
    {"key": "9-24", "label": "9–24 anni", "group": "Fasce non sovrapposte"},
    {"key": "25-49", "label": "25–49 anni", "group": "Fasce non sovrapposte"},
    {"key": "50-64", "label": "50–64 anni", "group": "Fasce non sovrapposte"},
    {"key": "65plus", "label": "65 anni e oltre", "group": "Fasce non sovrapposte"},
    {"key": "25-64", "label": "25–64 anni", "group": "Aggregati"},
    {"key": "9plus", "label": "9 anni e oltre", "group": "Aggregati"},
]

CONFIG = {
    "employmentRate": {
        "section": "labour", "field": "employmentRate", "numerator": "employed", "denominator": "population",
        "ages": LABOUR_AGES, "pyramidAgeKeys": ["15-24", "25-49", "50-64", "65plus"],
        "description": "Quota di residenti occupati nella fascia di età selezionata. La lettura iniziale resta 25–64 anni; età e genere possono essere combinati.",
        "formula": "occupati della fascia e del genere selezionati / residenti della stessa fascia e genere × 100",
    },
    "unemploymentRate": {
        "section": "labour", "field": "unemploymentRate", "numerator": "unemployed", "denominator": "active",
        "ages": LABOUR_AGES, "pyramidAgeKeys": ["15-24", "25-49", "50-64", "65plus"],
        "description": "Quota di persone in cerca di occupazione sulle forze di lavoro della fascia selezionata. La lettura iniziale resta 25–64 anni; età e genere possono essere combinati.",
        "formula": "persone in cerca della fascia e del genere selezionati / forze di lavoro della stessa fascia e genere × 100",
    },
    "activityRate": {
        "section": "labour", "field": "activityRate", "numerator": "active", "denominator": "population",
        "ages": LABOUR_AGES, "pyramidAgeKeys": ["15-24", "25-49", "50-64", "65plus"],
        "description": "Quota di residenti che partecipano al mercato del lavoro nella fascia selezionata. La lettura iniziale resta 25–64 anni; età e genere possono essere combinati.",
        "formula": "forze di lavoro della fascia e del genere selezionati / residenti della stessa fascia e genere × 100",
    },
    "diplomaPlus": {
        "section": "education", "field": "diplomaPlus", "numerator": "upperSecondaryPlus", "denominator": "population",
        "ages": EDUCATION_AGES, "pyramidAgeKeys": ["9-24", "25-49", "50-64", "65plus"],
        "description": "Quota di residenti con almeno un diploma secondario superiore nella fascia selezionata. La lettura iniziale resta 25–64 anni; età e genere possono essere combinati.",
        "formula": "residenti con diploma secondario superiore o titolo più elevato / residenti della stessa fascia e genere × 100",
    },
    "tertiary": {
        "section": "education", "field": "tertiaryRate", "numerator": "tertiary", "denominator": "population",
        "ages": EDUCATION_AGES, "pyramidAgeKeys": ["9-24", "25-49", "50-64", "65plus"],
        "description": "Quota di residenti con titolo terziario nella fascia selezionata. La lettura iniziale resta 25–64 anni; età e genere possono essere combinati.",
        "formula": "residenti con titolo terziario / residenti della stessa fascia e genere × 100",
    },
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cell(raw: dict, cfg: dict, age: dict, gender: dict) -> dict:
    source = raw[cfg["section"]][age["key"]][gender["key"]]
    value = source[cfg["field"]]
    return {
        "key": f"{age['key']}|{gender['key']}",
        "ageKey": age["key"], "ageLabel": age["label"],
        "genderKey": gender["key"], "genderLabel": gender["label"],
        "label": f"{age['label']} · {gender['label']}",
        "value": value,
        "unit": "percent",
        "numerator": source[cfg["numerator"]],
        "denominator": source[cfg["denominator"]],
    }


def aggregate_parts(metric: dict) -> list[dict]:
    head = metric["rows"][0]["parts"]
    result = []
    for template in head:
        key = template["key"]
        matching = [next(part for part in row["parts"] if part["key"] == key) for row in metric["rows"]]
        numerator = sum(float(part["numerator"]) for part in matching)
        denominator = sum(float(part["denominator"]) for part in matching)
        result.append({**{k: template[k] for k in ("key", "ageKey", "ageLabel", "genderKey", "genderLabel", "label", "unit")},
                       "value": numerator / denominator * 100 if denominator else None,
                       "numerator": numerator, "denominator": denominator})
    return result


def enrich_metric(site: dict, snapshot: dict, key: str, cfg: dict) -> None:
    metric = site["metrics"][key]
    metric["meta"]["compositeType"] = "demographicBreakdown"
    metric["meta"]["ageOptions"] = cfg["ages"]
    metric["meta"]["pyramidAgeKeys"] = cfg["pyramidAgeKeys"]
    metric["meta"]["genderOptions"] = GENDERS
    metric["meta"]["defaultAge"] = "25-64"
    metric["meta"]["defaultGender"] = "total"
    metric["meta"]["selectorLabel"] = "Età e genere"
    metric["meta"]["description"] = cfg["description"]
    metric["meta"].setdefault("searchTerms", [])
    for term in ("fascia età", "genere", "uomini", "donne"):
        if term not in metric["meta"]["searchTerms"]:
            metric["meta"]["searchTerms"].append(term)

    for row in metric["rows"]:
        raw = snapshot["towns"][row["town"]]
        row["parts"] = [cell(raw, cfg, age, gender) for age in cfg["ages"] for gender in GENDERS]
        default = next(part for part in row["parts"] if part["key"] == "25-64|total")
        if not math.isclose(float(row["value"]), float(default["value"]), abs_tol=0.11):
            raise RuntimeError(f"{key}/{row['town']}: il dettaglio 25-64 totale non riconcilia il valore esistente")

    parts = aggregate_parts(metric)
    default_agg = next(part for part in parts if part["key"] == "25-64|total")
    metric["aggregate"]["value"] = default_agg["value"]
    metric["aggregate"]["parts"] = parts
    metric["aggregate"]["label"] = f"Versilia · {metric['meta']['shortLabel']} · 25–64 anni · Totale"
    metric["aggregate"]["note"] = "Valore Versilia calcolato sui numeratori e denominatori complessivi dei sette Comuni, non come media semplice delle percentuali comunali."

    method = metric.setdefault("method", {})
    method["type"] = "Elaborazione Osservatorio su microdati comunali ufficiali Istat — Censimento permanente"
    method["formula"] = cfg["formula"]
    method["coverage"] = "7/7"
    method["breakdown"] = (
        "Genere: Totale, Uomini, Donne. Le fasce non sovrapposte sono mostrate in ordine anagrafico; "
        "25–64 e la fascia complessiva sono indicate separatamente come aggregati. "
        "25–64 è ricostruita esattamente sommando 25–49 e 50–64 sui conteggi prima di calcolare il tasso."
    )
    extra = "Il dettaglio 2024 è una fotografia trasversale: lo storico già presente resta riferito alla definizione originaria dell'indicatore e non viene esteso artificialmente alle singole combinazioni età × genere."
    if extra not in method.get("caveat", ""):
        method["caveat"] = (method.get("caveat", "").rstrip() + " " + extra).strip()


def update_theme(site: dict) -> None:
    theme = site["themes"]["lavoro"]
    obsolete = {"femaleEmploymentRate", "maleEmploymentRate"}
    theme["metrics"] = [key for key in theme.get("metrics", []) if key not in obsolete]
    for section in theme.get("sections", []):
        section["metrics"] = [key for key in section.get("metrics", []) if key not in obsolete]
        if section.get("key") == "mercato":
            section["description"] = "Occupazione, disoccupazione e partecipazione al mercato del lavoro, leggibili per fascia d'età e genere."
        if section.get("key") == "genere":
            section["description"] = "Il dettaglio per uomini e donne è integrato negli indicatori principali; qui resta il divario occupazionale tra i generi."
    theme["description"] = "Occupazione, disoccupazione e partecipazione con letture per età e genere, più divario occupazionale e condizione dei giovani."

    edu = site["themes"]["istruzione"]
    for section in edu.get("sections", []):
        if section.get("key") == "capitale":
            section["description"] = "Livello di istruzione della popolazione residente, leggibile per fascia d'età e genere."
    edu["description"] = "Titoli di studio con letture per età e genere, popolazione scolastica, classi e tempo pieno."


def main() -> None:
    site = load(SITE_PATH)
    snapshot = load(SNAPSHOT_PATH)
    if snapshot.get("referenceYear") != 2024 or len(snapshot.get("towns", {})) != 7:
        raise RuntimeError("Snapshot ISTAT 2024 non valido o non 7/7")
    initial_count = len(site["metrics"])
    for key, cfg in CONFIG.items():
        enrich_metric(site, snapshot, key, cfg)
    update_theme(site)
    if len(site["metrics"]) != initial_count:
        raise RuntimeError("L'arricchimento non deve creare o rimuovere oggetti indicatore")
    save(SITE_PATH, site)
    print(f"Lavoro/Istruzione età×genere: 5 indicatori arricchiti, 7/7 Comuni, totale indicatori invariato a {initial_count}.")


if __name__ == "__main__":
    main()
