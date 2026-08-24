#!/usr/bin/env python3
"""Materializza il draft Welfare + prima infanzia sul catalogo canonico.

Lo script è idempotente e viene eseguito nel workflow di anteprima: il file
`data/site-data.json` non viene ancora committato finché il draft non è
collaudato. I dati derivano esclusivamente dallo snapshot verificato 7/7.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "welfare-prima-infanzia-draft-2026-08.json"

SPENDING_KEY = "socialSpendingPerResident"
COMPOSITION_KEY = "socialSpendingByUserArea"
EARLY_KEY = "earlyChildhoodPotentialCapacityRate"
NEW_KEYS = (SPENDING_KEY, COMPOSITION_KEY, EARLY_KEY)

AREA_SELECTORS = [
    "Famiglie e minori", "Disabilità", "Dipendenze", "Anziani",
    "Immigrazione", "Povertà e disagio", "Multiutenza",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity(site: dict, town: str) -> dict:
    row = next(row for row in site["metrics"]["population"]["rows"] if row["town"] == town)
    return {"town": town, "code": row["code"], "slug": row["slug"]}


def town_order(site: dict) -> list[str]:
    return [row["town"] for row in site["metrics"]["population"]["rows"]]


def pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def eur_ab(value: float) -> str:
    return f"{value:.2f} €/ab".replace(".", ",")


def spending_metric(site: dict, snapshot: dict) -> dict:
    rows = []
    latest_values = []
    for town in town_order(site):
        raw = snapshot["towns"][town]["socialSpendingPerResident"]
        years = list(raw["years"])
        # Il dato Istat sorgente resta nello snapshot con la precisione originale;
        # nel catalogo pubblico esponiamo euro/abitante a due decimali, così anche
        # grafici, ranking, tooltip e schede comunali non mostrano code decimali.
        values = [round(float(v), 2) for v in raw["values"]]
        value = values[-1]
        latest_values.append(value)
        rows.append({
            **identity(site, town),
            "value": value,
            "formatted": eur_ab(value),
            "series": {"years": years, "values": values},
            "normalized": None,
            "benchmarkValue": value,
        })
    mean = round(sum(latest_values) / len(latest_values), 2)
    source = snapshot["sources"][SPENDING_KEY]
    return {
        "meta": {
            "key": SPENDING_KEY,
            "theme": "comunita",
            "label": "Spesa per interventi e servizi sociali per abitante",
            "shortLabel": "Spesa sociale per abitante",
            "description": "Spesa corrente dei Comuni e delle associazioni di Comuni per servizi e interventi socio-assistenziali, al netto della compartecipazione degli utenti e del Servizio sanitario nazionale, rapportata alla popolazione residente media.",
            "unit": "eurPerResident",
            "year": "2022",
            "source": "Istat — A misura di Comune",
            "polarity": "neutral",
            "searchTerms": ["spesa sociale", "welfare", "servizi sociali", "spesa per abitante", "assistenza sociale"],
        },
        "sourceUrl": source["url"],
        "rows": rows,
        "aggregate": {
            "value": mean,
            "label": "Versilia · media comunale",
            "note": "Media aritmetica dei sette valori comunali 2022. Non è presentata come spesa territoriale consolidata, perché la fonte pubblica espone qui indicatori comunali già rapportati alla rispettiva popolazione residente media.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore ufficiale Istat a livello comunale",
            "formula": source["formula"],
            "caveat": "La serie 2014–2022 usa il perimetro storico comparabile Istat e include i servizi educativi per la prima infanzia. Non viene concatenata con la successiva lettura 'al netto dei servizi educativi per la prima infanzia'. Un valore più alto descrive maggiore spesa per abitante ma non misura da solo qualità, efficacia o bisogno sociale.",
            "coverage": "7/7 Comuni · serie 2014–2022",
        },
    }


def composition_metric(site: dict, snapshot: dict, spending: dict) -> dict:
    areas = snapshot["areas"]
    rows = []
    component_values: list[list[float]] = [[] for _ in areas]
    spending_by_town = {row["town"]: row["value"] for row in spending["rows"]}
    for town in town_order(site):
        values = [float(v) for v in snapshot["towns"][town]["socialSpendingByUserArea"]]
        if len(values) != len(areas):
            raise RuntimeError(f"{town}: numero aree Welfare inatteso")
        if abs(sum(values) - 100.0) > 0.05:
            raise RuntimeError(f"{town}: composizione spesa non riconciliata a 100% ({sum(values)})")
        parts = []
        for index, (label, value) in enumerate(zip(areas, values, strict=True)):
            component_values[index].append(value)
            parts.append({"label": label, "selectorLabel": AREA_SELECTORS[index], "value": value, "unit": "percent"})
        rows.append({
            **identity(site, town),
            "value": values[0],
            "formatted": pct(values[0]),
            "series": None,
            "normalized": None,
            "benchmarkValue": values[0],
            "parts": parts,
            "summaryValue": spending_by_town[town],
        })
    aggregate_parts = [
        {"label": label, "selectorLabel": AREA_SELECTORS[index], "value": sum(values) / len(values), "unit": "percent"}
        for index, (label, values) in enumerate(zip(areas, component_values, strict=True))
    ]
    source = snapshot["sources"][COMPOSITION_KEY]
    mean_spending = round(sum(spending_by_town.values()) / len(spending_by_town), 2)
    return {
        "meta": {
            "key": COMPOSITION_KEY,
            "theme": "comunita",
            "label": "Composizione della spesa sociale per area di utenza",
            "shortLabel": "Spesa sociale per area",
            "description": "Quota della spesa sociale comunale destinata alle sette aree di utenza pubblicate da Istat. Le quote sono selezionabili separatamente e, per ciascun Comune, sommano al 100%.",
            "unit": "percent",
            "year": "2022",
            "source": "Istat — A misura di Comune",
            "polarity": "neutral",
            "compositeType": "distribution",
            "selectorLabel": "Area di utenza",
            "summaryLabel": "Spesa sociale per abitante",
            "summaryUnit": "eurPerResident",
            "searchTerms": ["welfare", "famiglie minori", "disabilità", "anziani", "povertà", "immigrazione", "spesa sociale per area"],
        },
        "sourceUrl": source["url"],
        "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"],
            "label": "Versilia · media comunale per area",
            "note": "Per il riepilogo Versilia viene mostrata la media aritmetica delle sette quote comunali: è un confronto sintetico tra Comuni, non una ricostruzione della spesa consolidata dell'intero territorio.",
            "parts": aggregate_parts,
            "summaryValue": mean_spending,
            "summaryLabel": "Media comunale della spesa per abitante",
            "summaryNote": "Media aritmetica dei sette valori comunali 2022.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore ufficiale Istat a livello comunale",
            "formula": source["formula"],
            "caveat": "Le percentuali descrivono la destinazione della spesa, non il livello di bisogno né la qualità dei servizi. La categoria 'Dipendenze' può risultare pari a zero in alcuni Comuni senza implicare assenza del bisogno o dei servizi sanitari dedicati.",
            "coverage": "7/7 Comuni · anno 2022",
        },
    }


def early_metric(site: dict, snapshot: dict) -> dict:
    rows = []
    total_children = 0
    total_capacity = 0
    for town in town_order(site):
        raw = snapshot["towns"][town]["earlyChildhood"]
        children = int(raw["children3to36Months"])
        capacity = int(raw["potentialCapacity"])
        services = int(raw["services"])
        value = capacity / children * 100 if children else None
        if value is None:
            raise RuntimeError(f"{town}: popolazione 3-36 mesi assente")
        total_children += children
        total_capacity += capacity
        rows.append({
            **identity(site, town),
            "value": value,
            "formatted": pct(value),
            "series": None,
            "normalized": None,
            "benchmarkValue": value,
            "potentialCapacity": capacity,
            "children3to36Months": children,
            "services": services,
            "lisbonIndicatorSource": float(raw["lisbonIndicator"]),
        })
    aggregate_value = total_capacity / total_children * 100
    source = snapshot["sources"][EARLY_KEY]
    return {
        "meta": {
            "key": EARLY_KEY,
            "theme": "istruzione",
            "label": "Tasso di ricettività potenziale dei servizi educativi 0–3 anni",
            "shortLabel": "Ricettività potenziale 0–3",
            "description": "Posti potenzialmente disponibili nei nidi e nei servizi integrativi del Comune ogni 100 bambini residenti di 3–36 mesi.",
            "unit": "percent",
            "year": "2024/25",
            "source": "Regione Toscana — Servizi educativi per la prima infanzia",
            "polarity": "positive",
            "searchTerms": ["asili nido", "nidi", "prima infanzia", "0 3 anni", "posti nido", "ricettività", "servizi educativi"],
        },
        "sourceUrl": source["datasetPage"],
        "rows": rows,
        "aggregate": {
            "value": aggregate_value,
            "label": "Versilia · ricettività potenziale",
            "note": f"{total_capacity} posti potenziali su {total_children} bambini di 3–36 mesi nei sette Comuni. Aggregazione ottenuta sommando numeratori e denominatori comunali della stessa fonte.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali Regione Toscana",
            "formula": source["formula"],
            "caveat": "Misura l'offerta potenziale localizzata nel Comune, non gli iscritti effettivi, la lista d'attesa, la qualità del servizio o la possibilità di frequentare strutture in altri Comuni. Non va confuso con l'Indicatore di Lisbona pubblicato nello stesso dataset: per questo motivo quest'ultimo non è usato nel calcolo.",
            "coverage": "7/7 Comuni · anno educativo 2024/25",
        },
    }


def upsert_section(theme: dict, section: dict) -> None:
    sections = [item for item in theme.get("sections", []) if item.get("key") != section["key"]]
    sections.append(section)
    theme["sections"] = sections


def update_themes(site: dict) -> None:
    community = site["themes"]["comunita"]
    community["label"] = "Comunità e welfare"
    community["description"] = "Investimenti pubblici, Terzo settore, welfare e servizi sociali per leggere risorse e reti della comunità."
    community["metrics"] = [key for key in community.get("metrics", []) if key not in {SPENDING_KEY, COMPOSITION_KEY}] + [SPENDING_KEY, COMPOSITION_KEY]
    upsert_section(community, {
        "key": "welfare-servizi-sociali",
        "label": "Welfare e servizi sociali",
        "description": "Quanto spendono i Comuni per il welfare e come la spesa si distribuisce tra le principali aree di utenza.",
        "metrics": [SPENDING_KEY, COMPOSITION_KEY],
    })

    education = site["themes"]["istruzione"]
    education["description"] = "Titoli di studio, popolazione scolastica, edifici e offerta educativa dalla prima infanzia alla scuola."
    education["metrics"] = [key for key in education.get("metrics", []) if key != EARLY_KEY] + [EARLY_KEY]
    upsert_section(education, {
        "key": "prima-infanzia",
        "label": "Prima infanzia",
        "description": "Offerta potenziale dei servizi educativi per bambini di 3–36 mesi nei sette Comuni.",
        "metrics": [EARLY_KEY],
    })


def main() -> None:
    site = load(SITE_PATH)
    snapshot = load(SNAPSHOT_PATH)
    if set(snapshot["towns"]) != set(town_order(site)):
        raise RuntimeError("Snapshot Welfare: copertura comunale diversa dal catalogo")

    spending = spending_metric(site, snapshot)
    composition = composition_metric(site, snapshot, spending)
    early = early_metric(site, snapshot)
    site["metrics"][SPENDING_KEY] = spending
    site["metrics"][COMPOSITION_KEY] = composition
    site["metrics"][EARLY_KEY] = early
    update_themes(site)

    site["version"] = "1.18.0-draft"
    site["updated"] = "25 agosto 2026"
    save(SITE_PATH, site)
    print(f"Draft Welfare materializzato: {len(site['metrics'])} indicatori complessivi")
    print("Nuovi indicatori: " + ", ".join(NEW_KEYS))


if __name__ == "__main__":
    main()
