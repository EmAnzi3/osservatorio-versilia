#!/usr/bin/env python3
"""Materializza i tre indicatori TPL v1.19.0 dallo snapshot verificato.

Lo script non interroga la rete e non modifica componenti dell'interfaccia. I
valori derivano esclusivamente dallo snapshot versionato, che conserva URL,
hash e regole della lavorazione GTFS effettuata sul 26 agosto 2026.
"""
from __future__ import annotations

import json
import math
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "mobilita-tpl-2026-08-26.json"

REFERENCE_DATE = "26 agosto 2026"
SNAPSHOT_REF = "data/source-snapshots/mobilita-tpl-2026-08-26.json"
CATALOG_URL = "https://dati.toscana.it/dataset/rt-oraritb"
BUS_URL = "https://regionetoscana.smartregion.toscana.it/mobility/artifacts/gtfs"
RAIL_URL = (
    "https://dati.toscana.it/dataset/8bb8f8fe-fe7d-41d0-90dc-49f2456180d1/"
    "resource/4f85393b-357d-443d-8378-65de4198505f/download/trenitalia.gtfs"
)
BOUNDARIES_URL = (
    "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/"
    "2026/Limiti01012026_g.zip"
)
SOURCE_URLS = {
    "catalogo": CATALOG_URL,
    "gtfs-autolinee": BUS_URL,
    "gtfs-trenitalia": RAIL_URL,
    "confini-istat": BOUNDARIES_URL,
}
TPL_KEYS = (
    "scheduledTplTripsPer1000",
    "activeTplAccessPoints",
    "tplServiceSpan",
)
SLUGS = {
    "Camaiore": "camaiore",
    "Forte dei Marmi": "forte-dei-marmi",
    "Massarosa": "massarosa",
    "Pietrasanta": "pietrasanta",
    "Seravezza": "seravezza",
    "Stazzema": "stazzema",
    "Viareggio": "viareggio",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clock_seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def validate_snapshot(snapshot: dict, towns: list[dict]) -> None:
    if snapshot.get("snapshotVersion") != "2026-08-26-v3":
        raise RuntimeError("Versione snapshot TPL inattesa")
    if snapshot.get("referenceDate") != "2026-08-26":
        raise RuntimeError("Data di servizio TPL inattesa")
    if snapshot.get("scope", {}).get("coverage") != "7/7":
        raise RuntimeError("Copertura TPL diversa da 7/7")

    expected_hashes = {
        "Istat confini 2026": "b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6",
        "GTFS Autolinee Toscane": "799ece1cdfc517044fcd4cf6ff9366effceeab9fa15c8ee5cf9fd7f20b5ed3de",
        "GTFS Trenitalia": "a262c5bdfccd98a5c7e7ae08eea8eecb3189222f34c1015f5d4608faf3efc152",
    }
    for source, expected_hash in expected_hashes.items():
        if snapshot.get("sources", {}).get(source, {}).get("sha256") != expected_hash:
            raise RuntimeError(f"Hash fonte TPL inatteso: {source}")

    raw = snapshot.get("raw", {})
    expected_towns = {town["name"] for town in towns}
    if set(raw) != expected_towns or len(raw) != 7:
        raise RuntimeError("I Comuni dello snapshot non coincidono con il catalogo")
    for name, item in raw.items():
        if item.get("status") != "ok":
            raise RuntimeError(f"Dato TPL non validato: {name}")
        if item["trips"] != item["busTrips"] + item["railTrips"]:
            raise RuntimeError(f"Ripartizione bus/ferrovia incoerente: {name}")
        span = round((clock_seconds(item["last"]) - clock_seconds(item["first"])) / 3600, 2)
        if not math.isclose(span, item["serviceSpanHours"], abs_tol=1e-12):
            raise RuntimeError(f"Ampiezza oraria incoerente: {name}")
        if not math.isclose(item["tripsPer1000"], item["trips"] / item["population"] * 1000):
            raise RuntimeError(f"Tasso corse incoerente: {name}")
        if not math.isclose(
            item["accessPointsPer1000"], item["activeAccessPoints"] / item["population"] * 1000
        ):
            raise RuntimeError(f"Tasso punti GTFS incoerente: {name}")


def row(town: dict, raw: dict, value_field: str, normalized_field: str | None = None) -> dict:
    item = raw[town["name"]]
    normalized = None
    if normalized_field:
        normalized = {
            "value": item[normalized_field],
            "label": (
                "Corse TPL programmate ogni 1.000 residenti"
                if value_field == "trips"
                else "Punti di accesso GTFS ogni 1.000 residenti"
            ),
            "description": (
                "Corse programmate rapportate alla popolazione residente al 1° gennaio 2026."
                if value_field == "trips"
                else "Punti di accesso GTFS attivi rapportati alla popolazione residente al 1° gennaio 2026."
            ),
            "unit": "per1000",
        }
    return {
        "town": town["name"],
        "code": town["code"],
        "slug": SLUGS[town["name"]],
        "value": item[value_field],
        "formatted": None,
        "series": None,
        "normalized": normalized,
        "benchmarkValue": item[value_field],
    }


def metric_meta(key: str, label: str, description: str, unit: str, search_terms: list[str]) -> dict:
    return {
        "key": key,
        "theme": "mobilita",
        "label": label,
        "shortLabel": label,
        "description": description,
        "unit": unit,
        "year": REFERENCE_DATE,
        "source": "Regione Toscana — GTFS Autolinee Toscane e Trenitalia",
        "polarity": "neutral",
        "detailGroup": "tpl",
        "searchTerms": search_terms,
    }


def build_metrics(site: dict, snapshot: dict) -> OrderedDict[str, dict]:
    towns = site["towns"]
    raw = snapshot["raw"]
    total_population = sum(raw[town["name"]]["population"] for town in towns)

    trip_values = [raw[town["name"]]["trips"] for town in towns]
    point_values = [raw[town["name"]]["activeAccessPoints"] for town in towns]
    span_values = [raw[town["name"]]["serviceSpanHours"] for town in towns]
    trip_total = sum(trip_values)
    point_total = sum(point_values)
    span_total = sum(span_values)

    trip_meta = metric_meta(
        TPL_KEYS[0],
        "Corse TPL programmate",
        "Corse di autobus e ferrovia programmate nel giorno di riferimento che servono almeno un punto di accesso utilizzabile dai passeggeri nel Comune. Nel confronto puoi passare dal valore assoluto alle corse ogni 1.000 residenti.",
        "number",
        ["tpl", "trasporto pubblico", "autobus", "bus", "treno", "ferrovia", "corse", "partenze"],
    )
    trip_meta["normalized"] = {
        "label": "Corse TPL programmate ogni 1.000 residenti",
        "description": "Corse programmate rapportate alla popolazione residente: consente un confronto meno dipendente dalla dimensione demografica dei Comuni.",
        "unit": "per1000",
    }
    points_meta = metric_meta(
        TPL_KEYS[1],
        "Punti di accesso GTFS attivi",
        "Punti di accesso presenti nei GTFS ufficiali e serviti nel giorno di riferimento. Ogni punto è identificato dalla coppia feed e stop_id; nel confronto puoi leggere sia il conteggio sia i punti ogni 1.000 residenti.",
        "number",
        ["tpl", "fermate", "stop", "gtfs", "accesso", "autobus", "treno"],
    )
    points_meta["shortLabel"] = "Punti di accesso TPL"
    points_meta["normalized"] = {
        "label": "Punti di accesso GTFS ogni 1.000 residenti",
        "description": "Punti GTFS attivi rapportati ai residenti. È una densità dell'offerta dati, non la distanza pedonale della popolazione dalle fermate.",
        "unit": "per1000",
    }
    span_meta = metric_meta(
        TPL_KEYS[2],
        "Ampiezza oraria programmata del servizio TPL",
        "Intervallo, calcolato sui secondi GTFS, tra la prima e l'ultima partenza programmata che serve il Comune nella giornata operativa di riferimento.",
        "hours",
        ["tpl", "orario", "prima corsa", "ultima corsa", "ampiezza", "servizio", "bus", "treno"],
    )
    span_meta["shortLabel"] = "Ampiezza oraria TPL"

    metrics = OrderedDict()
    metrics[TPL_KEYS[0]] = {
        "meta": trip_meta,
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": [row(town, raw, "trips", "tripsPer1000") for town in towns],
        "aggregate": {
            "value": trip_total / 7,
            "label": "Media dei 7 Comuni",
            "note": "Media aritmetica dei sette conteggi comunali. Il totale territoriale non è usato come benchmark perché una stessa corsa può servire più Comuni.",
            "formatted": "227",
            "totalValue": trip_total,
            "totalFormatted": "1.586",
        },
        "normalizedAggregate": {
            "value": trip_total / total_population * 1000,
            "label": "Media ponderata dei 7 Comuni",
            "note": "Rapporto tra la somma dei conteggi comunali e la popolazione complessiva dei sette Comuni.",
            "formatted": "10,01",
        },
        "method": {
            "type": "Elaborazione GTFS Osservatorio Versilia",
            "formula": "Per il 26 agosto 2026 si selezionano i service_id attivi da calendar e calendar_dates. Una trip_id è contata una sola volta per Comune se serve almeno uno stop_id geolocalizzato nel territorio comunale in cui sia consentita salita o discesa; il dettaglio separa autobus e ferrovia.",
            "caveat": "Fotografia del servizio programmato di un mercoledì feriale estivo: non misura corse effettivamente svolte, puntualità, capacità o passeggeri. Una stessa corsa può servire più Comuni.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    metrics[TPL_KEYS[1]] = {
        "meta": points_meta,
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": [row(town, raw, "activeAccessPoints", "accessPointsPer1000") for town in towns],
        "aggregate": {
            "value": point_total / 7,
            "label": "Media dei 7 Comuni",
            "note": "Media aritmetica dei sette conteggi comunali di punti di accesso GTFS attivi. Il totale territoriale resta descrittivo e non è il riferimento del lollipop.",
            "formatted": "122",
            "totalValue": point_total,
            "totalFormatted": "856",
        },
        "normalizedAggregate": {
            "value": point_total / total_population * 1000,
            "label": "Media ponderata dei 7 Comuni",
            "note": "Rapporto tra gli 856 punti di accesso GTFS comunali e la popolazione complessiva.",
            "formatted": "5,40",
        },
        "method": {
            "type": "Elaborazione GTFS Osservatorio Versilia",
            "formula": "Si contano le coppie (feed, stop_id) attive il 26 agosto 2026, utilizzabili dai passeggeri e attribuite al Comune tramite coordinate e confini Istat 2026; gli identificativi dei due feed non vengono fusi.",
            "caveat": "Un punto GTFS è un punto di accesso dati: direzioni, banchine o feed differenti possono rappresentare separatamente luoghi fisicamente molto vicini. Non misura la copertura pedonale entro 500 metri.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    metrics[TPL_KEYS[2]] = {
        "meta": span_meta,
        "sourceUrl": CATALOG_URL,
        "sourceUrls": SOURCE_URLS,
        "rows": [row(town, raw, "serviceSpanHours") for town in towns],
        "aggregate": {
            "value": span_total / 7,
            "label": "Media dei 7 Comuni",
            "note": "Media aritmetica delle sette ampiezze orarie comunali; la somma delle ore comunali non è un benchmark interpretabile.",
            "formatted": "20,48 h",
            "totalValue": span_total,
            "totalFormatted": "143,34 h",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione GTFS Osservatorio Versilia",
            "formula": "Differenza in ore, calcolata sui secondi GTFS, tra la prima e l'ultima partenza programmata che serve almeno un punto di accesso del Comune il 26 agosto 2026. Gli orari oltre 24:00 restano nella stessa giornata operativa.",
            "caveat": "Misura l'estensione temporale dell'offerta, non la frequenza: una singola corsa molto presto o molto tardi può ampliare la finestra senza implicare un servizio frequente durante tutta la giornata.",
            "coverage": "7/7",
            "snapshot": SNAPSHOT_REF,
        },
    }
    return metrics


def apply_site(site: dict, snapshot: dict) -> None:
    validate_snapshot(snapshot, site["towns"])
    tpl_metrics = build_metrics(site, snapshot)
    old_metrics = site["metrics"]
    rebuilt = OrderedDict()
    inserted = False
    for key, metric in old_metrics.items():
        if key in TPL_KEYS:
            continue
        rebuilt[key] = metric
        if key == "inboundCommutersRate":
            rebuilt.update(tpl_metrics)
            inserted = True
    if not inserted:
        raise RuntimeError("Ancora mobilità non trovata nel catalogo")
    site["metrics"] = rebuilt

    theme = site["themes"]["mobilita"]
    theme["description"] = "Pendolarismo, trasporto pubblico, parco veicolare, ricarica elettrica, connettività digitale e mobilità lenta."
    sections = [section for section in theme["sections"] if section.get("key") != "trasporto-pubblico"]
    section = {
        "key": "trasporto-pubblico",
        "label": "Trasporto pubblico",
        "description": "Offerta programmata di autobus e ferrovia: corse, punti di accesso e ampiezza della giornata di servizio sui GTFS ufficiali regionali.",
        "metrics": list(TPL_KEYS),
    }
    index = next((i + 1 for i, item in enumerate(sections) if item.get("key") == "pendolarismo"), None)
    if index is None:
        raise RuntimeError("Sezione pendolarismo non trovata")
    sections.insert(index, section)
    theme["sections"] = sections
    theme["metrics"] = [key for item in sections for key in item["metrics"]]

    for town in site["towns"]:
        item = snapshot["raw"][town["name"]]
        site["details"][town["code"]]["mobility"]["tpl"] = {
            "referenceDate": REFERENCE_DATE,
            "trips": item["trips"],
            "busTrips": item["busTrips"],
            "railTrips": item["railTrips"],
            "activeAccessPoints": item["activeAccessPoints"],
            "routes": item["routes"],
            "firstDeparture": item["firstDisplay"],
            "lastDeparture": item["lastDisplay"],
            "serviceSpanHours": item["serviceSpanHours"],
        }


def apply_registry(registry: dict) -> None:
    profile_id = "regione-toscana-gtfs-scheduled"
    registry["sourceProfiles"][profile_id] = {
        "publisher": "Regione Toscana",
        "frequency": "continuous",
        "frequencyLabel": "Aggiornamento continuo del feed programmato",
        "expectedRelease": "Feed mobile; la data di servizio viene congelata tramite snapshot e hash delle fonti",
        "acquisitionMethod": "Download dei GTFS ufficiali Autolinee Toscane e Trenitalia; selezione del calendario della data di riferimento; join spaziale dei punti di accesso ai confini comunali Istat 2026; conteggi senza stime.",
        "licenseName": "CC BY",
        "licenseUrl": CATALOG_URL,
    }
    for url in SOURCE_URLS.values():
        registry["sourceProfileByUrl"][url] = profile_id
        registry.setdefault("sourceUrlProfiles", {})[url] = profile_id
    for key in TPL_KEYS:
        registry["metricOverrides"][key] = {"profile": profile_id}
    registry["expectedMetricCount"] = 149
    registry["expectedInlineMetricCount"] = 145
    registry["expectedExternalMetricCount"] = 4


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    snapshot = load(SNAPSHOT_PATH)
    apply_site(site, snapshot)
    apply_registry(registry)
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    print("TPL v1.19.0 materializzato: 3 indicatori, 7/7 Comuni, 856 punti GTFS verificati.")


if __name__ == "__main__":
    main()
