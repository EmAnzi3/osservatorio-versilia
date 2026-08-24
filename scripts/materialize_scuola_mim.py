#!/usr/bin/env python3
"""Materializza il lotto Scuola MIM nel tema Istruzione.

Il perimetro è l'Anagrafe dell'Edilizia Scolastica MIM, a.s. 2024/25,
109 edifici univoci nei 7 Comuni della Versilia. I valori NON DEFINITO non
sono mai trasformati in NO: quando un campo ha risposte mancanti/non definite,
la percentuale di presenza usa come denominatore le sole risposte definite e
la quota non definita resta disponibile nel dettaglio.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
MONITOR_PATH = ROOT / "data" / "source-monitor-state.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "mim-edilizia-scolastica-versilia-2024-25.json"

PROFILE = "mim-school-year"
SCHOOL_YEAR = "2024/25"
DATA_AS_OF = "06/08/2025"

SAFETY_KEY = "schoolBuildingSafetyDocs"
ACCESS_KEY = "schoolBuildingAccessibility"
FACILITIES_KEY = "schoolBuildingFacilities"
AGE_KEY = "schoolBuildingAge"
TRANSPORT_KEY = "schoolBuildingTransport"
NEW_KEYS = (SAFETY_KEY, ACCESS_KEY, FACILITIES_KEY, AGE_KEY, TRANSPORT_KEY)

SOURCE_PAGES = {
    "sicurezza": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0171EDICONSICUREZZASTA2021",
    "accessibilita": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0156EDISUPBARARCSTA2021",
    "spazi": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0151EDIAMBFUNZSTA2021",
    "eta": "https://dati.istruzione.it/opendata/opendata/catalog/EDIETAORIGINESTA2021",
    "collegamenti": "https://dati.istruzione.it/opendata/opendata/catalog/EDICOLLEGAMENTISTA2021",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity(site: dict, town: str) -> dict:
    row = next(row for row in site["metrics"]["population"]["rows"] if row["town"] == town)
    return {"town": town, "code": row["code"], "slug": row["slug"]}


def town_order(site: dict) -> list[str]:
    return [row["town"] for row in site["metrics"]["population"]["rows"]]


def pct(value: float | None) -> str:
    if value is None:
        return "n.d."
    return f"{value:.1f}%".replace(".", ",")


def count(statuses: dict, key: str) -> int:
    return int(statuses.get(key, 0) or 0)


def known_total(statuses: dict) -> int:
    return sum(int(v or 0) for k, v in statuses.items() if k not in {"NON DEFINITO", "", "-"})


def unknown_total(statuses: dict) -> int:
    return sum(int(v or 0) for k, v in statuses.items() if k in {"NON DEFINITO", "", "-"})


def presence_part(label: str, selector: str, statuses: dict, positive: str = "SI") -> dict:
    yes = count(statuses, positive)
    denominator = known_total(statuses)
    value = yes / denominator * 100 if denominator else None
    return {"label": label, "selectorLabel": selector, "value": value, "unit": "percent", "count": yes, "defined": denominator, "unknown": unknown_total(statuses)}


def status_part(label: str, selector: str, statuses: dict, status: str) -> dict:
    n = count(statuses, status)
    denominator = known_total(statuses)
    value = n / denominator * 100 if denominator else None
    return {"label": label, "selectorLabel": selector, "value": value, "unit": "percent", "count": n, "defined": denominator, "unknown": unknown_total(statuses)}


def aggregate_status(snapshot: dict, field: str) -> dict:
    total = Counter()
    for raw in snapshot["towns"].values():
        total.update({k: int(v or 0) for k, v in raw[field].items()})
    return dict(total)


def make_row(site: dict, town: str, parts: list[dict], buildings: int) -> dict:
    value = parts[0]["value"]
    return {**identity(site, town), "value": value, "formatted": pct(value), "series": None, "normalized": None, "benchmarkValue": value, "buildings": buildings, "parts": parts}


def safety_parts(raw: dict) -> list[dict]:
    return [
        status_part("Agibilità piena", "Agibilità", raw["agibilita"], "SI"),
        presence_part("Certificato prevenzione incendi (CPI)", "CPI", raw["cpi"]),
        presence_part("SCIA antincendio", "SCIA", raw["sciaAntincendio"]),
        presence_part("Rinnovo periodico conformità antincendio", "Rinnovo", raw["rinnovoAntincendio"]),
    ]


def safety_metric(site: dict, snapshot: dict) -> dict:
    rows = [make_row(site, town, safety_parts(snapshot["towns"][town]), int(snapshot["towns"][town]["buildings"])) for town in town_order(site)]
    aggregate_raw = {"agibilita": aggregate_status(snapshot, "agibilita"), "cpi": aggregate_status(snapshot, "cpi"), "sciaAntincendio": aggregate_status(snapshot, "sciaAntincendio"), "rinnovoAntincendio": aggregate_status(snapshot, "rinnovoAntincendio")}
    agg_parts = safety_parts(aggregate_raw)
    return {
        "meta": {"key": SAFETY_KEY, "theme": "istruzione", "label": "Certificazioni di sicurezza degli edifici scolastici", "shortLabel": "Sicurezza edifici scolastici", "description": "Quota di edifici con agibilità piena e presenza dei principali documenti antincendio. CPI, SCIA e rinnovo sono mostrati separatamente: non vengono fusi in un unico sì/no.", "unit": "percent", "year": SCHOOL_YEAR, "source": "MIM — Anagrafe dell'Edilizia Scolastica", "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Documento / requisito", "searchTerms": ["scuola sicurezza", "agibilità scuola", "cpi scuola", "scia antincendio scuola", "edilizia scolastica"]},
        "sourceUrl": SOURCE_PAGES["sicurezza"], "rows": rows,
        "aggregate": {"value": agg_parts[0]["value"], "label": "Versilia · agibilità piena", "note": "109 edifici univoci. Ogni documento usa il proprio denominatore di risposte definite; NON DEFINITO non è trattato come NO.", "buildings": int(snapshot["uniqueBuildingsVersilia"]), "parts": agg_parts},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione Osservatorio su open data MIM per edificio", "formula": "quota documento = edifici con risposta SI / edifici con risposta definita del relativo campo × 100", "caveat": "Per l'agibilità, IN PARTE non è considerato agibilità piena. Per antincendio CPI, SCIA e rinnovo periodico restano indicatori distinti: non si costruisce un OR tra campi, così da evitare deduplicazioni non dimostrabili. NON DEFINITO resta fuori dal denominatore e viene conservato come informazione mancante.", "coverage": "7/7 Comuni · 109 edifici", "reference": f"Anno scolastico {SCHOOL_YEAR}; dati MIM al {DATA_AS_OF}."},
    }


def accessibility_parts(raw: dict) -> list[dict]:
    statuses = raw["accessibilita"]
    total = sum(int(v or 0) for v in statuses.values())
    return [
        presence_part("Con accorgimenti per il superamento delle barriere", "Con accorgimenti", statuses),
        status_part("Senza accorgimenti dichiarati", "Senza", statuses, "NO"),
        {"label": "Dato non definito", "selectorLabel": "Non definito", "value": (unknown_total(statuses) / total * 100) if total else None, "unit": "percent", "count": unknown_total(statuses), "defined": total, "unknown": unknown_total(statuses)},
    ]


def accessibility_metric(site: dict, snapshot: dict) -> dict:
    rows = [make_row(site, town, accessibility_parts(snapshot["towns"][town]), int(snapshot["towns"][town]["buildings"])) for town in town_order(site)]
    agg_parts = accessibility_parts({"accessibilita": aggregate_status(snapshot, "accessibilita")})
    return {
        "meta": {"key": ACCESS_KEY, "theme": "istruzione", "label": "Accessibilità degli edifici scolastici", "shortLabel": "Accessibilità scuole", "description": "Presenza dichiarata di accorgimenti per il superamento delle barriere architettoniche negli edifici scolastici.", "unit": "percent", "year": SCHOOL_YEAR, "source": "MIM — Anagrafe dell'Edilizia Scolastica", "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Stato accessibilità", "searchTerms": ["barriere architettoniche scuola", "accessibilità scuola", "edifici scolastici accessibili", "disabilità scuola"]},
        "sourceUrl": SOURCE_PAGES["accessibilita"], "rows": rows,
        "aggregate": {"value": agg_parts[0]["value"], "label": "Versilia · edifici con accorgimenti", "note": "La quota principale usa solo risposte SI/NO; i NON DEFINITO sono esposti separatamente e non diventano NO.", "buildings": int(snapshot["uniqueBuildingsVersilia"]), "parts": agg_parts},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione Osservatorio su open data MIM per edificio", "formula": "edifici con accorgimenti = SI / (SI + NO) × 100", "caveat": "L'indicatore riporta il campo MIM sugli accorgimenti per il superamento delle barriere; non certifica autonomamente la conformità completa a tutte le prescrizioni di accessibilità. I valori NON DEFINITO sono esclusi dal denominatore e mostrati a parte.", "coverage": "7/7 Comuni · 109 edifici", "reference": f"Anno scolastico {SCHOOL_YEAR}; dati MIM al {DATA_AS_OF}."},
    }


def facilities_parts(raw: dict) -> list[dict]:
    return [presence_part("Edifici con mensa", "Mensa", raw["mensa"]), presence_part("Edifici con palestra", "Palestra", raw["palestra"])]


def facilities_metric(site: dict, snapshot: dict) -> dict:
    rows = [make_row(site, town, facilities_parts(snapshot["towns"][town]), int(snapshot["towns"][town]["buildings"])) for town in town_order(site)]
    agg_parts = facilities_parts({"mensa": aggregate_status(snapshot, "mensa"), "palestra": aggregate_status(snapshot, "palestra")})
    return {
        "meta": {"key": FACILITIES_KEY, "theme": "istruzione", "label": "Mensa e palestra negli edifici scolastici", "shortLabel": "Mensa e palestra", "description": "Quota di edifici scolastici nei quali il MIM registra la presenza di mensa o palestra, selezionabili separatamente.", "unit": "percent", "year": SCHOOL_YEAR, "source": "MIM — Anagrafe dell'Edilizia Scolastica", "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Spazio funzionale", "searchTerms": ["mensa scuola", "palestra scuola", "spazi scolastici", "edilizia scolastica"]},
        "sourceUrl": SOURCE_PAGES["spazi"], "rows": rows,
        "aggregate": {"value": agg_parts[0]["value"], "label": "Versilia · edifici con mensa", "note": "Le quote sono calcolate sui conteggi degli edifici, non sul numero di plessi o studenti.", "buildings": int(snapshot["uniqueBuildingsVersilia"]), "parts": agg_parts},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione Osservatorio su open data MIM per edificio", "formula": "quota spazio = edifici con risposta SI / edifici con risposta definita × 100", "caveat": "La presenza dello spazio non misura dimensione, qualità, capienza, stato manutentivo o disponibilità effettiva per tutte le classi.", "coverage": "7/7 Comuni · 109 edifici", "reference": f"Anno scolastico {SCHOOL_YEAR}; dati MIM al {DATA_AS_OF}."},
    }


PERIOD_ORDER = ["prima del 1800", "tra il 1800 e il 1899", "tra il 1900 e il 1933", "tra il 1934 e il 1949", "tra il 1950 e il 1970", "tra il 1971 e il 1975", "tra il 1976 e il 1992", "tra il 1997 e il 2008", "tra il 2009 e il 2017"]
PERIOD_LABEL = {"prima del 1800": "Prima del 1800", "tra il 1800 e il 1899": "1800–1899", "tra il 1900 e il 1933": "1900–1933", "tra il 1934 e il 1949": "1934–1949", "tra il 1950 e il 1970": "1950–1970", "tra il 1971 e il 1975": "1971–1975", "tra il 1976 e il 1992": "1976–1992", "tra il 1997 e il 2008": "1997–2008", "tra il 2009 e il 2017": "2009–2017"}


def age_parts(raw: dict) -> list[dict]:
    statuses = raw["periodoCostruzione"]
    defined = sum(count(statuses, key) for key in PERIOD_ORDER)
    old_count = sum(count(statuses, key) for key in PERIOD_ORDER[:5])
    result = [{"label": "Edifici costruiti entro il 1970", "selectorLabel": "Entro 1970", "value": old_count / defined * 100 if defined else None, "unit": "percent", "count": old_count, "defined": defined, "unknown": unknown_total(statuses)}]
    for key in PERIOD_ORDER:
        n = count(statuses, key)
        result.append({"label": PERIOD_LABEL[key], "selectorLabel": PERIOD_LABEL[key], "value": n / defined * 100 if defined else None, "unit": "percent", "count": n, "defined": defined, "unknown": unknown_total(statuses)})
    total = defined + unknown_total(statuses)
    result.append({"label": "Periodo non definito", "selectorLabel": "Non definito", "value": unknown_total(statuses) / total * 100 if total else None, "unit": "percent", "count": unknown_total(statuses), "defined": total, "unknown": unknown_total(statuses)})
    return result


def age_metric(site: dict, snapshot: dict) -> dict:
    rows = [make_row(site, town, age_parts(snapshot["towns"][town]), int(snapshot["towns"][town]["buildings"])) for town in town_order(site)]
    agg_parts = age_parts({"periodoCostruzione": aggregate_status(snapshot, "periodoCostruzione")})
    return {
        "meta": {"key": AGE_KEY, "theme": "istruzione", "label": "Epoca di costruzione degli edifici scolastici", "shortLabel": "Età del patrimonio scolastico", "description": "Distribuzione degli edifici scolastici per periodo di costruzione. La lettura iniziale mostra la quota costruita entro il 1970; il selettore espone le classi MIM e i periodi non definiti.", "unit": "percent", "year": SCHOOL_YEAR, "source": "MIM — Anagrafe dell'Edilizia Scolastica", "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Periodo di costruzione", "searchTerms": ["età scuole", "anno costruzione scuola", "patrimonio scolastico", "edifici scolastici vecchi"]},
        "sourceUrl": SOURCE_PAGES["eta"], "rows": rows,
        "aggregate": {"value": agg_parts[0]["value"], "label": "Versilia · edifici costruiti entro il 1970", "note": "La distribuzione usa il periodo MIM dichiarato per edificio. I periodi non definiti restano visibili e non sono stimati.", "buildings": int(snapshot["uniqueBuildingsVersilia"]), "parts": agg_parts},
        "normalizedAggregate": None,
        "method": {"type": "Distribuzione per epoca su open data MIM per edificio", "formula": "quota periodo = edifici nel periodo / edifici con periodo di costruzione definito × 100", "caveat": "L'epoca di costruzione non equivale allo stato manutentivo, alla sicurezza o all'anno dell'ultimo adeguamento. I periodi NON DEFINITO sono esclusi dalle quote per epoca e riportati separatamente.", "coverage": "7/7 Comuni · 109 edifici", "reference": f"Anno scolastico {SCHOOL_YEAR}; dati MIM al {DATA_AS_OF}."},
    }


def transport_parts(raw: dict) -> list[dict]:
    return [presence_part("Edifici raggiungibili con scuolabus", "Scuolabus", raw["scuolabus"]), presence_part("Edifici raggiungibili con TPL urbano", "TPL urbano", raw["tplUrbano"]), presence_part("Edifici raggiungibili con TPL interurbano", "TPL interurbano", raw["tplInterurbano"])]


def transport_metric(site: dict, snapshot: dict) -> dict:
    rows = [make_row(site, town, transport_parts(snapshot["towns"][town]), int(snapshot["towns"][town]["buildings"])) for town in town_order(site)]
    agg_parts = transport_parts({"scuolabus": aggregate_status(snapshot, "scuolabus"), "tplUrbano": aggregate_status(snapshot, "tplUrbano"), "tplInterurbano": aggregate_status(snapshot, "tplInterurbano")})
    return {
        "meta": {"key": TRANSPORT_KEY, "theme": "istruzione", "label": "Raggiungibilità degli edifici scolastici", "shortLabel": "Raggiungibilità scuole", "description": "Quota di edifici per i quali il MIM registra collegamenti tramite scuolabus, trasporto pubblico urbano o trasporto pubblico interurbano.", "unit": "percent", "year": SCHOOL_YEAR, "source": "MIM — Anagrafe dell'Edilizia Scolastica", "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Modalità di collegamento", "searchTerms": ["scuolabus", "trasporto pubblico scuola", "tpl scuola", "raggiungibilità scuola"]},
        "sourceUrl": SOURCE_PAGES["collegamenti"], "rows": rows,
        "aggregate": {"value": agg_parts[0]["value"], "label": "Versilia · edifici raggiungibili con scuolabus", "note": "La fonte indica la presenza del collegamento per edificio; non misura frequenza, distanza dalla fermata, tempi di viaggio o accessibilità pedonale.", "buildings": int(snapshot["uniqueBuildingsVersilia"]), "parts": agg_parts},
        "normalizedAggregate": None,
        "method": {"type": "Elaborazione Osservatorio su open data MIM per edificio", "formula": "quota modalità = edifici con risposta SI / edifici con risposta definita × 100", "caveat": "La presenza dichiarata di un collegamento non equivale a qualità o adeguatezza del servizio e non sostituisce un'analisi GTFS di frequenze e fermate.", "coverage": "7/7 Comuni · 109 edifici", "reference": f"Anno scolastico {SCHOOL_YEAR}; dati MIM al {DATA_AS_OF}."},
    }


def update_theme(site: dict) -> None:
    theme = site["themes"]["istruzione"]
    theme["metrics"] = [key for key in theme.get("metrics", []) if key not in NEW_KEYS] + list(NEW_KEYS)
    sections = [section for section in theme.get("sections", []) if section.get("key") != "edilizia-scolastica"]
    sections.append({"key": "edilizia-scolastica", "label": "Edifici e servizi scolastici", "description": "Sicurezza documentale, accessibilità, spazi, epoca di costruzione e collegamenti dei 109 edifici scolastici censiti dal MIM nei sette Comuni.", "metrics": list(NEW_KEYS)})
    theme["sections"] = sections
    theme["description"] = "Titoli di studio della popolazione, popolazione scolastica e caratteristiche degli edifici e dei servizi scolastici."


def update_registry(registry: dict, site: dict) -> None:
    for key in NEW_KEYS:
        registry.setdefault("metricOverrides", {})[key] = {"profile": PROFILE}
    for url in SOURCE_PAGES.values():
        registry.setdefault("sourceProfileByUrl", {})[url] = PROFILE
    external = sum(1 for metric in site["metrics"].values() if metric.get("dataStorage", {}).get("type") == "external-climate")
    registry["expectedMetricCount"] = len(site["metrics"])
    registry["expectedInlineMetricCount"] = len(site["metrics"]) - external
    registry["expectedExternalMetricCount"] = external


def ensure_monitor_source(sources: dict, url: str, metrics: list[str]) -> None:
    state = sources.setdefault(url, {"url": url, "ok": True, "status": 200, "finalUrl": url, "contentType": "text/html", "contentLength": None, "etag": "", "lastModified": "", "contentSha256": "", "hashTruncated": False, "error": "", "metrics": [], "roles": ["primary"], "profileIds": [PROFILE], "frequencies": ["school_year"]})
    state["metrics"] = sorted(set(state.get("metrics", [])) | set(metrics))
    state["profileIds"] = sorted(set(state.get("profileIds", [])) | {PROFILE})
    state["frequencies"] = sorted(set(state.get("frequencies", [])) | {"school_year"})


def update_monitor(monitor: dict) -> None:
    sources = monitor.setdefault("sources", {})
    ensure_monitor_source(sources, SOURCE_PAGES["sicurezza"], [SAFETY_KEY])
    ensure_monitor_source(sources, SOURCE_PAGES["accessibilita"], [ACCESS_KEY])
    ensure_monitor_source(sources, SOURCE_PAGES["spazi"], [FACILITIES_KEY])
    ensure_monitor_source(sources, SOURCE_PAGES["eta"], [AGE_KEY])
    ensure_monitor_source(sources, SOURCE_PAGES["collegamenti"], [TRANSPORT_KEY])


def main() -> None:
    site, registry, monitor, snapshot = load(SITE_PATH), load(REGISTRY_PATH), load(MONITOR_PATH), load(SNAPSHOT_PATH)
    if snapshot.get("schoolYear") != SCHOOL_YEAR or int(snapshot.get("uniqueBuildingsVersilia", 0)) != 109:
        raise RuntimeError("Snapshot scuola non valido: attesi a.s. 2024/25 e 109 edifici")
    if set(snapshot.get("towns", {})) != set(town_order(site)):
        raise RuntimeError("Snapshot scuola: copertura Comuni diversa dal catalogo")
    site["metrics"].update({SAFETY_KEY: safety_metric(site, snapshot), ACCESS_KEY: accessibility_metric(site, snapshot), FACILITIES_KEY: facilities_metric(site, snapshot), AGE_KEY: age_metric(site, snapshot), TRANSPORT_KEY: transport_metric(site, snapshot)})
    update_theme(site)
    update_registry(registry, site)
    update_monitor(monitor)
    save(SITE_PATH, site); save(REGISTRY_PATH, registry); save(MONITOR_PATH, monitor)
    print(f"Scuola MIM: {len(NEW_KEYS)} indicatori materializzati, 7/7 Comuni, 109 edifici; totale catalogo {len(site['metrics'])}.")

if __name__ == "__main__":
    main()
