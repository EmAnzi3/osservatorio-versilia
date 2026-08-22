#!/usr/bin/env python3
"""Materializza il Lotto A Amministrazione nel tema Bilanci.

Indicatori pubblicati:
- dipendenti comunali per 1.000 residenti;
- turnover netto del personale comunale;
- struttura per età del personale (macrofasce <40, 40-54, 55+).

Il perimetro è sempre 7/7 Comuni. I valori RGS 2024 sono conservati nello
snapshot versionato. Gli assunti/cessati usati nel turnover escludono i passaggi
tra amministrazioni, coerentemente con la definizione RGS.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
MONITOR_PATH = ROOT / "data" / "source-monitor-state.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "rgs-amministrazione-2024.json"

RGS_INDICATOR_URL = "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dipendenti/abitanti-comune-acc"
RGS_DATA_URL = "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dati-pubblicati"
PROFILE = "rgs-conto-annuale-annual"

EMPLOYEES_KEY = "municipalEmployeesPer1000"
TURNOVER_KEY = "municipalStaffTurnover"
AGE_KEY = "municipalStaffAgeStructure"
NEW_KEYS = (EMPLOYEES_KEY, TURNOVER_KEY, AGE_KEY)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def population_2024(site: dict, town: str) -> float:
    row = next(row for row in site["metrics"]["population"]["rows"] if row["town"] == town)
    series = row.get("series") or {}
    for year, value in zip(series.get("years", []), series.get("values", [])):
        if int(year) == 2024:
            return float(value)
    if str(site["metrics"]["population"]["meta"].get("year")) == "2024":
        return float(row["value"])
    raise RuntimeError(f"{town}: popolazione 2024 non disponibile nel dataset canonico")


def identity(site: dict, town: str) -> dict:
    row = next(row for row in site["metrics"]["population"]["rows"] if row["town"] == town)
    return {"town": town, "code": row["code"], "slug": row["slug"]}


def pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def per1000(value: float) -> str:
    return f"{value:.1f} ogni 1.000".replace(".", ",")


def employees_metric(site: dict, snapshot: dict) -> dict:
    rows = []
    total_staff = 0.0
    total_population = 0.0
    for town in [row["town"] for row in site["metrics"]["population"]["rows"]]:
        raw = snapshot["towns"][town]
        staff = float(raw["staffAt31Dec"])
        population = population_2024(site, town)
        value = staff / population * 1000
        total_staff += staff
        total_population += population
        rows.append({
            **identity(site, town),
            "value": value,
            "formatted": per1000(value),
            "series": {"years": [2024], "values": [value]},
            "normalized": None,
            "benchmarkValue": value,
            "staffAt31Dec": int(staff),
            "residentPopulation": int(population),
        })
    aggregate = total_staff / total_population * 1000
    return {
        "meta": {
            "key": EMPLOYEES_KEY,
            "theme": "bilanci",
            "label": "Dipendenti comunali per 1.000 residenti",
            "shortLabel": "Dipendenti / 1.000 residenti",
            "description": "Dotazione di personale del Comune rapportata alla popolazione residente. Il rapporto consente di confrontare enti di dimensione diversa, ma non misura da solo efficienza o qualità dei servizi.",
            "unit": "per1000",
            "year": "2024",
            "source": "RGS — Conto Annuale / Istat",
            "polarity": "neutral",
            "searchTerms": ["dipendenti comunali", "personale comune", "dipendenti per abitante", "organico comunale"],
        },
        "sourceUrl": RGS_INDICATOR_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate,
            "label": "Versilia · dipendenti per 1.000 residenti",
            "note": "Somma dei dipendenti dei sette Comuni rapportata alla popolazione complessiva; non è la media semplice dei sette rapporti.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali RGS e popolazione Istat già materializzata",
            "formula": "dipendenti al 31 dicembre / residenti 2024 × 1.000",
            "caveat": "La consistenza del personale dipende anche da esternalizzazioni, gestioni associate e organizzazione dei servizi. Un valore maggiore non è automaticamente migliore. La pagina RGS pubblica lo stesso concetto di indicatore; il controllo di parità sul denominatore della tabella dedicata resta separato dalla materializzazione.",
            "coverage": "7/7",
        },
    }


def turnover_metric(site: dict, snapshot: dict) -> dict:
    rows = []
    total_staff = total_net_hires = total_net_cessations = 0.0
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    for town in order:
        raw = snapshot["towns"][town]
        staff = float(raw["staffAt31Dec"])
        net_hires = float(raw["netHires"])
        net_cessations = float(raw["netCessations"])
        value = (net_hires - net_cessations) / staff * 100
        if abs(value - float(raw["netTurnoverRatePct"])) > 0.0002:
            raise RuntimeError(f"{town}: turnover non riconciliato")
        total_staff += staff
        total_net_hires += net_hires
        total_net_cessations += net_cessations
        rows.append({
            **identity(site, town),
            "value": value,
            "formatted": pct(value),
            "series": {"years": [2024], "values": [value]},
            "normalized": None,
            "benchmarkValue": value,
            "netHires": int(net_hires),
            "netCessations": int(net_cessations),
            "netTurnoverHeadcount": int(net_hires - net_cessations),
        })
    aggregate = (total_net_hires - total_net_cessations) / total_staff * 100
    return {
        "meta": {
            "key": TURNOVER_KEY,
            "theme": "bilanci",
            "label": "Turnover netto del personale comunale",
            "shortLabel": "Turnover del personale",
            "description": "Saldo tra assunzioni e cessazioni, al netto dei passaggi tra amministrazioni, rapportato al personale in servizio a fine anno. Valori positivi indicano crescita netta dell'organico; valori negativi una riduzione netta.",
            "unit": "percent",
            "year": "2024",
            "source": "RGS — Conto Annuale / OpenBDAP",
            "polarity": "neutral",
            "searchTerms": ["turnover", "assunzioni comune", "cessazioni comune", "ricambio personale", "organico"],
        },
        "sourceUrl": RGS_DATA_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate,
            "label": "Versilia · turnover netto",
            "note": "Saldo complessivo tra assunti e cessati netti dei sette Comuni rapportato alla somma del personale al 31 dicembre.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su microdati ufficiali RGS",
            "formula": "(assunti al netto dei passaggi da altre amministrazioni − cessati al netto dei passaggi ad altre amministrazioni) / dipendenti al 31 dicembre × 100",
            "caveat": "Il segno descrive la variazione netta dell'organico nell'anno e non costituisce una graduatoria di qualità amministrativa. Nei Comuni con pochi dipendenti anche una singola unità produce variazioni percentuali elevate.",
            "coverage": "7/7",
        },
    }


def age_metric(site: dict, snapshot: dict) -> dict:
    rows = []
    totals = {"under40": 0, "age40to54": 0, "age55plus": 0}
    labels = [
        ("age55plus", "55 anni e oltre", "55+"),
        ("age40to54", "Da 40 a 54 anni", "40–54"),
        ("under40", "Meno di 40 anni", "<40"),
    ]
    order = [row["town"] for row in site["metrics"]["population"]["rows"]]
    for town in order:
        raw = snapshot["towns"][town]
        staff = int(raw["staffAt31Dec"])
        age = raw["age"]
        if sum(int(age[key]) for key in totals) != staff:
            raise RuntimeError(f"{town}: fasce di età non riconciliate con il personale totale")
        parts = []
        for key, label, selector in labels:
            count = int(age[key])
            totals[key] += count
            parts.append({
                "label": label,
                "selectorLabel": selector,
                "value": count / staff * 100,
                "count": count,
                "unit": "percent",
            })
        rows.append({
            **identity(site, town),
            "value": parts[0]["value"],
            "formatted": pct(parts[0]["value"]),
            "series": {"years": [2024], "values": [parts[0]["value"]]},
            "normalized": None,
            "benchmarkValue": parts[0]["value"],
            "parts": parts,
        })
    total_staff = sum(totals.values())
    aggregate_parts = []
    for key, label, selector in labels:
        aggregate_parts.append({
            "label": label,
            "selectorLabel": selector,
            "value": totals[key] / total_staff * 100,
            "count": totals[key],
            "unit": "percent",
        })
    return {
        "meta": {
            "key": AGE_KEY,
            "theme": "bilanci",
            "label": "Struttura per età del personale comunale",
            "shortLabel": "Età del personale",
            "description": "Composizione del personale comunale per macrofasce di età. La lettura predefinita mostra la quota di dipendenti con 55 anni o più; il selettore consente di confrontare anche le altre fasce.",
            "unit": "percent",
            "year": "2024",
            "source": "RGS — Conto Annuale / OpenBDAP",
            "polarity": "neutral",
            "compositeType": "securityMeasures",
            "selectorLabel": "Fascia di età",
            "searchTerms": ["età dipendenti", "personale anziano", "personale giovane", "55 anni", "ricambio generazionale"],
        },
        "sourceUrl": RGS_DATA_URL,
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Versilia · personale 55+",
            "note": "Le quote Versilia sono calcolate sui conteggi complessivi dei sette Comuni; non sono medie semplici delle percentuali comunali.",
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su microdati ufficiali RGS",
            "formula": "quota fascia = dipendenti nella fascia / dipendenti totali × 100; macrofasce ottenute sommando le classi anagrafiche ufficiali RGS",
            "caveat": "La struttura per età segnala la composizione dell'organico, non la qualità del personale. Non viene stimata un'età media a partire dai punti medi delle classi.",
            "coverage": "7/7",
        },
    }


def update_theme(site: dict) -> None:
    theme = site["themes"]["bilanci"]
    theme["label"] = "Bilanci e amministrazione"
    theme["question"] = "Come stanno i conti e la macchina amministrativa?"
    theme["description"] = "Bilanci comunali, capacità di spesa e struttura del personale degli enti."
    metrics = [key for key in theme.get("metrics", []) if key not in NEW_KEYS]
    metrics.extend(NEW_KEYS)
    theme["metrics"] = metrics
    sections = [section for section in theme.get("sections", []) if section.get("key") != "personale-amministrazione"]
    sections.append({
        "key": "personale-amministrazione",
        "label": "Personale e capacità amministrativa",
        "description": "Dotazione di personale, ricambio dell'organico e sostenibilità generazionale della macchina comunale.",
        "metrics": list(NEW_KEYS),
    })
    theme["sections"] = sections


def update_registry(registry: dict, site: dict) -> None:
    profiles = registry.setdefault("sourceProfiles", {})
    profiles[PROFILE] = {
        "publisher": "Ragioneria Generale dello Stato — Conto Annuale",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la chiusura e pubblicazione del Conto Annuale",
        "acquisitionMethod": "Download dei dataset analitici per ente da OpenBDAP/Conto Annuale e materializzazione da snapshot verificato 7/7.",
        "licenseName": "Condizioni indicate dalla Ragioneria Generale dello Stato",
        "licenseUrl": "https://www.rgs.mef.gov.it/",
    }
    overrides = registry.setdefault("metricOverrides", {})
    for key in NEW_KEYS:
        overrides[key] = {"profile": PROFILE}
    by_url = registry.setdefault("sourceProfileByUrl", {})
    by_url[RGS_INDICATOR_URL] = PROFILE
    by_url[RGS_DATA_URL] = PROFILE
    external = sum(1 for metric in site["metrics"].values() if metric.get("dataStorage", {}).get("type") == "external-climate")
    registry["expectedMetricCount"] = len(site["metrics"])
    registry["expectedExternalMetricCount"] = external
    registry["expectedInlineMetricCount"] = len(site["metrics"]) - external


def update_monitor(monitor: dict) -> None:
    sources = monitor.setdefault("sources", {})
    for url, keys in ((RGS_INDICATOR_URL, [EMPLOYEES_KEY]), (RGS_DATA_URL, [TURNOVER_KEY, AGE_KEY])):
        state = sources.setdefault(url, {
            "url": url,
            "ok": True,
            "status": 200,
            "finalUrl": url,
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
        state["metrics"] = sorted(set(state.get("metrics", [])) | set(keys))
        state["profileIds"] = sorted(set(state.get("profileIds", [])) | {PROFILE})
        state["frequencies"] = sorted(set(state.get("frequencies", [])) | {"annual"})


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    snapshot = load(SNAPSHOT_PATH)

    for key in NEW_KEYS:
        site["metrics"].pop(key, None)

    site["metrics"][EMPLOYEES_KEY] = employees_metric(site, snapshot)
    site["metrics"][TURNOVER_KEY] = turnover_metric(site, snapshot)
    site["metrics"][AGE_KEY] = age_metric(site, snapshot)
    update_theme(site)
    update_registry(registry, site)
    update_monitor(monitor)

    # Questo materializzatore aggiunge il lotto al dataset corrente senza
    # sovrascrivere la versione/data di release stabilita dalla pipeline canonica.
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)

    print(
        f"Amministrazione Lotto A: {len(site['metrics'])} indicatori totali; "
        f"aggiunti {', '.join(NEW_KEYS)}; copertura RGS 2024 7/7."
    )


if __name__ == "__main__":
    main()
