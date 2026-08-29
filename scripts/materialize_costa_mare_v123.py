#!/usr/bin/env python3
"""Materializza il lotto Costa e mare v1.23.0 dallo snapshot verificato."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
STATE_PATH = ROOT / "data" / "source-monitor-state.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "costa-mare-v123.json"
FINALIZER = ROOT / "scripts" / "finalize_catalog_release.py"
CATALOG_TEST = ROOT / "scripts" / "test_catalog_release_v116.py"
README = ROOT / "README.md"
HISTORY_DOC = ROOT / "docs" / "copertura-serie-storiche.md"
COHERENCE_DOC = ROOT / "docs" / "coerenza-interfaccia.md"
APP_JS = ROOT / "assets" / "app.js"
APP_PART_00 = ROOT / "assets" / "app-parts" / "00.txt"
APP_PART_05 = ROOT / "assets" / "app-parts" / "05.txt"
UX_HISTORY = ROOT / "assets" / "ux-history.js"
EXPORT_JS = ROOT / "assets" / "export-v161.js"
SERVICE_WORKER = ROOT / "service-worker.js"
BUILD_SAFE = ROOT / "scripts" / "build_static_safe.py"
BUILD_BRAND = ROOT / "scripts" / "build_static_brand.py"

VERSION = "v1.23.0"
UPDATED = "28 agosto 2026"
ASSET_VERSION = "20260829-v123-coast-ui2"
PWA_VERSION = "ov-pwa-20260829-v123-coast-ui2"
SNAPSHOT_REF = "data/source-snapshots/costa-mare-v123.json"

KEYS = (
    "bathingWaterQuality",
    "bathingNonCompliantSamples",
    "blueFlagBeaches",
    "shorelineDynamics",
    "rigidDefenceProtectedCoast",
)

ARPAT_URL = "https://www.arpat.toscana.it/pubblicazione/il-controllo-delle-acque-di-balneazione-stagione-2025/"
ARPAT_ARCHIVE_URL = "https://www.arpat.toscana.it/datiemappe/balneazione-in-toscana-dati-relativi-alle-stagioni-precedenti/"
BLUE_FLAG_URL = "https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb"
ISPRA_DYNAMICS_URL = "https://indicatoriambientali.isprambiente.it/it/coste/dinamica-litoranea"
ISPRA_PROTECTED_URL = "https://indicatoriambientali.isprambiente.it/it/coste/costa-protetta"

COASTAL_CODES = {"046005", "046013", "046024", "046033"}
NOT_APPLICABLE_CODES = {"046018", "046028", "046030"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Pattern non trovato in {path}: {old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def share(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise RuntimeError("Denominatore costiero non positivo")
    return numerator / denominator * 100.0


def validate_snapshot(snapshot: dict[str, Any], site: dict[str, Any]) -> None:
    site_codes = {town["code"] for town in site["towns"]}
    if site_codes != COASTAL_CODES | NOT_APPLICABLE_CODES:
        raise RuntimeError("Perimetro dei sette Comuni canonici inatteso")
    scope = snapshot["scope"]
    if set(scope["coastalTownCodes"]) != COASTAL_CODES:
        raise RuntimeError("Perimetro dei Comuni costieri incoerente")
    if set(scope["notApplicableTownCodes"]) != NOT_APPLICABLE_CODES:
        raise RuntimeError("Perimetro n.a. incoerente")
    expected_hashes = {
        "arpatSamples2025": "90d25c2b47ceae7d2222c718948a46fac6d11985eb0df464a30cc6236be4f1bf",
        "arpatQualityHistory": "cfcd5b2b5d48084468b43d0bf9f03fb63fb70239a07cca8b8afae56343633752",
        "arpatControlsHistory": "79fbbc55472fd9cc7a69d631c0826378fa8cb1661fd4b29e622ec9eefe903b90",
        "arpatReport2025": "c190a78c0cf0d8a3e728d84aaa5fd50c7aefc6c0918cb8efa06305d0b965e76a",
        "blueFlag2026": "dbfbb3f4f7ea1397015f69b93b91f0acaa2ec71f7cd2e7a2fcad8f76bbd048fc",
        "ispraShorelineDynamics": "a00fb97649e293c73c923e43fd0ee53ecfa42df9568ec162a9668c2adb4c9b11",
        "ispraProtectedCoast": "9ca2b81cff7375f4af9f86af50543637d23329828d3556ccbe174a16e27d956e",
    }
    for key, expected in expected_hashes.items():
        if snapshot["sources"][key]["sha256"] != expected:
            raise RuntimeError(f"Hash sorgente inatteso: {key}")

    quality = snapshot["bathingWaterQuality2025"]
    samples = snapshot["bathingNonCompliantSamples2025"]
    dynamics = snapshot["shorelineDynamics2006_2020"]
    protected = snapshot["rigidDefenceProtectedCoast2020"]
    if set(quality["towns"]) != COASTAL_CODES or set(samples["towns"]) != COASTAL_CODES:
        raise RuntimeError("Copertura ARPAT diversa dai quattro Comuni costieri")
    if samples["uniqueSamples"] != 167 or samples["versilia"]["all"] != {"nonCompliant": 35, "total": 167}:
        raise RuntimeError("Perimetro dei campioni ARPAT 2025 inatteso")
    if quality["versilia"]["areas"] != {"excellent": 14, "good": 6, "sufficient": 0, "poor": 1, "total": 21}:
        raise RuntimeError("Classificazione ARPAT 2025 inattesa")
    for section, fields in ((dynamics, ("analysedKm", "erosionKm", "stableKm", "advanceKm")),):
        for code, row in section["towns"].items():
            if abs(row[fields[0]] - sum(row[field] for field in fields[1:])) > 1e-9:
                raise RuntimeError(f"Dinamica litoranea non riconciliata: {code}")
    if abs(protected["versilia"]["protectedKm"] - sum(row["protectedKm"] for row in protected["towns"].values())) > 1e-9:
        raise RuntimeError("Costa protetta Versilia non riconciliata")
    if snapshot["blueFlagBeaches"]["versiliaValues"] != [5, 5, 4, 6, 6, 6, 6, 6]:
        raise RuntimeError("Storico Bandiera Blu inatteso")


def base_meta(
    key: str,
    label: str,
    short: str,
    description: str,
    unit: str,
    year: str,
    source: str,
    search_terms: list[str],
) -> dict[str, Any]:
    return {
        "key": key,
        "theme": "ambiente",
        "label": label,
        "shortLabel": short,
        "description": description,
        "unit": unit,
        "year": year,
        "source": source,
        "polarity": "neutral",
        "context": "Costa e mare",
        "detailGroup": "coast",
        "searchTerms": search_terms,
        "sourceMeta": {
            "snapshot": SNAPSHOT_REF,
            "note": "Quattro Comuni costieri; Massarosa, Seravezza e Stazzema sono non applicabili e restano n.a.",
        },
    }


def town_context(site: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    slugs = {row["code"]: row["slug"] for row in site["metrics"]["population"]["rows"]}
    return slugs, site["towns"]


def not_applicable_row(town: dict[str, Any], slug: str, parts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "town": town["name"],
        "code": town["code"],
        "slug": slug,
        "value": None,
        "formatted": "n.a.",
        "series": None,
        "normalized": None,
        "benchmarkValue": None,
        "notApplicable": True,
        "applicabilityNote": "Comune non costiero: indicatore marino non applicabile.",
    }
    if parts is not None:
        row["parts"] = [{**part, "value": None} for part in parts]
    return row


def build_metrics(site: dict[str, Any], snapshot: dict[str, Any]) -> OrderedDict[str, dict[str, Any]]:
    slugs, towns = town_context(site)
    quality_source = snapshot["bathingWaterQuality2025"]
    samples_source = snapshot["bathingNonCompliantSamples2025"]
    flags_source = snapshot["blueFlagBeaches"]
    dynamics_source = snapshot["shorelineDynamics2006_2020"]
    protected_source = snapshot["rigidDefenceProtectedCoast2020"]

    quality_parts = [
        {"key": "areas", "label": "Aree eccellenti", "selectorLabel": "Aree", "unit": "percent"},
        {"key": "kilometres", "label": "Costa classificata eccellente", "selectorLabel": "km di costa", "unit": "percent"},
    ]
    quality_rows = []
    for town in towns:
        code = town["code"]
        if code in NOT_APPLICABLE_CODES:
            quality_rows.append(not_applicable_row(town, slugs[code], quality_parts))
            continue
        raw = quality_source["towns"][code]
        areas = raw["areas"]
        kilometres = raw["kilometres"]
        area_share = share(areas["excellent"], areas["total"])
        km_share = share(kilometres["excellent"], kilometres["total"])
        quality_rows.append({
            "town": town["name"], "code": code, "slug": slugs[code],
            "value": area_share, "formatted": f"{area_share:.1f}%".replace(".", ","),
            "series": None, "normalized": None, "benchmarkValue": area_share,
            "parts": [
                {**quality_parts[0], "value": area_share},
                {**quality_parts[1], "value": km_share},
            ],
            "coastDetail": {"areas": areas, "kilometres": kilometres},
        })
    qa = quality_source["versilia"]["areas"]
    qk = quality_source["versilia"]["kilometres"]
    quality_aggregate_parts = [
        {**quality_parts[0], "value": share(qa["excellent"], qa["total"]), "numerator": qa["excellent"], "denominator": qa["total"]},
        {**quality_parts[1], "value": share(qk["excellent"], qk["total"]), "numerator": qk["excellent"], "denominator": qk["total"]},
    ]
    quality_meta = base_meta(
        KEYS[0], "Qualità delle aree di balneazione", "Qualità balneazione",
        "Quota delle aree e dei chilometri di costa classificati eccellenti da ARPAT per il 2025, sulla base dei dati 2022–2025.",
        "percent", "2025", "ARPAT — classificazione delle acque di balneazione",
        ["balneazione", "qualità acque", "mare", "costa", "aree eccellenti"],
    )
    quality_meta.update({
        "compositeType": "securityMeasures",
        "selectorLabel": "Lettura",
        "comparisonReference": "aggregate",
        "comparisonDifference": "percentagePoints",
        "comparisonLabel": "quota Versilia costiera",
        "comparisonOverline": "Rispetto alla quota Versilia costiera",
        "comparisonNote": "Il riferimento usa il rapporto tra le somme elementari dei quattro Comuni costieri; non la media semplice delle percentuali comunali.",
    })
    quality = {
        "meta": quality_meta,
        "sourceUrl": ARPAT_URL,
        "sourceUrls": {"report2025": ARPAT_URL, "archive": ARPAT_ARCHIVE_URL},
        "rows": quality_rows,
        "aggregate": {
            "value": quality_aggregate_parts[0]["value"],
            "label": "Versilia costiera · aree eccellenti",
            "parts": quality_aggregate_parts,
            "coastDetail": quality_source["versilia"],
            "note": "Rapporti tra le somme dei numeratori e dei denominatori dei quattro Comuni costieri; non medie semplici delle percentuali comunali.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Classificazione ufficiale ARPAT quadriennale",
            "formula": "Aree: aree eccellenti / aree classificate × 100. km: km in classe eccellente / km classificati × 100. Aggregati Versilia calcolati sulle somme elementari.",
            "caveat": "La classificazione 2025 usa i dati 2022–2025 e non coincide con gli esiti dei soli campioni 2025. Nessuna lunghezza è stimata.",
            "coverage": "4/4 Comuni costieri + 3 n.a.",
            "snapshot": SNAPSHOT_REF,
        },
    }

    sample_parts = [
        {"key": "all", "label": "Tutti i campioni", "selectorLabel": "Tutti", "unit": "percent"},
        {"key": "routine", "label": "Campioni routinari", "selectorLabel": "Routinari", "unit": "percent"},
        {"key": "supplementary", "label": "Campioni supplettivi", "selectorLabel": "Supplettivi", "unit": "percent"},
    ]
    sample_rows = []
    for town in towns:
        code = town["code"]
        if code in NOT_APPLICABLE_CODES:
            sample_rows.append(not_applicable_row(town, slugs[code], sample_parts))
            continue
        raw = samples_source["towns"][code]
        parts = []
        for template in sample_parts:
            item = raw[template["key"]]
            parts.append({**template, "value": share(item["nonCompliant"], item["total"]), "nonCompliant": item["nonCompliant"], "total": item["total"]})
        sample_rows.append({
            "town": town["name"], "code": code, "slug": slugs[code],
            "value": parts[0]["value"], "formatted": f"{parts[0]['value']:.1f}%".replace(".", ","),
            "series": None, "normalized": None, "benchmarkValue": parts[0]["value"],
            "parts": parts, "coastDetail": raw,
        })
    sample_aggregate_parts = []
    for template in sample_parts:
        item = samples_source["versilia"][template["key"]]
        sample_aggregate_parts.append({**template, "value": share(item["nonCompliant"], item["total"]), "nonCompliant": item["nonCompliant"], "total": item["total"]})
    sample_meta = base_meta(
        KEYS[1], "Campioni di balneazione non conformi", "Campioni non conformi",
        "Quota dei campioni 2025 che superano almeno uno dei limiti microbiologici per le acque marine, distinguendo routinari e supplettivi.",
        "percent", "2025", "ARPAT — controlli delle acque di balneazione",
        ["balneazione", "campioni", "non conformi", "escherichia coli", "enterococchi", "mare"],
    )
    sample_meta.update({
        "compositeType": "securityMeasures",
        "selectorLabel": "Tipo di campione",
        "comparisonReference": "aggregate",
        "comparisonDifference": "percentagePoints",
        "comparisonLabel": "quota Versilia costiera",
        "comparisonOverline": "Rispetto alla quota Versilia costiera",
        "comparisonNote": "Il riferimento usa campioni non conformi complessivi divisi per i campioni complessivi dei quattro Comuni costieri; non la media semplice delle percentuali comunali.",
    })
    samples = {
        "meta": sample_meta,
        "sourceUrl": ARPAT_URL,
        "rows": sample_rows,
        "aggregate": {
            "value": sample_aggregate_parts[0]["value"],
            "label": "Versilia costiera · campioni non conformi",
            "parts": sample_aggregate_parts,
            "coastDetail": samples_source["versilia"],
            "note": "35 campioni non conformi su 167 unici. Una riga che supera entrambi i parametri conta una sola volta.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su campioni ufficiali ARPAT",
            "formula": "Non conforme se Enterococchi intestinali > 200 oppure Escherichia coli > 500 MPN/100 ml; deduplica su Codice area + Data + Rout./Suppl.; quota = campioni non conformi / campioni unici × 100.",
            "caveat": "I campioni non conformi non sono chiamati episodi. Il dettaglio delle aree interessate usa soltanto i campioni routinari.",
            "coverage": "4/4 Comuni costieri + 3 n.a.; 167 campioni unici",
            "snapshot": SNAPSHOT_REF,
        },
    }

    flag_rows = []
    years = flags_source["years"]
    for town in towns:
        code = town["code"]
        if code in NOT_APPLICABLE_CODES:
            flag_rows.append(not_applicable_row(town, slugs[code]))
            continue
        raw = flags_source["towns"][code]
        current = raw["values"][-1]
        flag_rows.append({
            "town": town["name"], "code": code, "slug": slugs[code],
            "value": current, "formatted": str(current), "normalized": None,
            "benchmarkValue": current,
            "series": {"years": years, "values": raw["values"]},
            "coastDetail": {"localities2026": raw["localities2026"]},
        })
    flag_meta = base_meta(
        KEYS[2], "Spiagge Bandiera Blu", "Spiagge Bandiera Blu",
        "Numero di spiagge o località costiere riconosciute da FEE Italia. Le denominazioni unite da una barra non vengono spezzate.",
        "number", "2026", "FEE Italia — Programma Bandiera Blu",
        ["bandiera blu", "spiagge", "mare", "costa", "fee"],
    )
    flags = {
        "meta": flag_meta,
        "sourceUrl": BLUE_FLAG_URL,
        "rows": flag_rows,
        "aggregate": {
            "value": flags_source["versiliaValues"][-1],
            "label": "Versilia costiera · totale",
            "note": "Somma delle sei località 2026 elencate separatamente da FEE Italia nei quattro Comuni costieri.",
            "series": {"years": years, "values": flags_source["versiliaValues"]},
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Conteggio da elenco ufficiale FEE Italia",
            "formula": "Conteggio delle località elencate separatamente per Comune; le denominazioni unite con / restano una sola località.",
            "caveat": "Bandiera Blu considera un insieme di criteri ambientali e gestionali e non è un proxy diretto della sola qualità microbiologica. Pietrasanta è assente nel 2021 e ricompare nel 2022: nessuna interpolazione.",
            "coverage": "4/4 Comuni costieri + 3 n.a.; storico 2019–2026",
            "snapshot": SNAPSHOT_REF,
        },
    }

    dynamics_parts = [
        {"key": "erosion", "label": "Costa in erosione", "selectorLabel": "Erosione", "unit": "percent"},
        {"key": "stable", "label": "Costa stabile", "selectorLabel": "Stabile", "unit": "percent"},
        {"key": "advance", "label": "Costa in avanzamento", "selectorLabel": "Avanzamento", "unit": "percent"},
    ]
    dynamics_rows = []
    for town in towns:
        code = town["code"]
        if code in NOT_APPLICABLE_CODES:
            dynamics_rows.append(not_applicable_row(town, slugs[code], dynamics_parts))
            continue
        raw = dynamics_source["towns"][code]
        parts = [
            {**dynamics_parts[0], "value": share(raw["erosionKm"], raw["analysedKm"]), "kilometres": raw["erosionKm"]},
            {**dynamics_parts[1], "value": share(raw["stableKm"], raw["analysedKm"]), "kilometres": raw["stableKm"]},
            {**dynamics_parts[2], "value": share(raw["advanceKm"], raw["analysedKm"]), "kilometres": raw["advanceKm"]},
        ]
        dynamics_rows.append({
            "town": town["name"], "code": code, "slug": slugs[code],
            "value": parts[0]["value"], "formatted": f"{parts[0]['value']:.1f}%".replace(".", ","),
            "series": None, "normalized": None, "benchmarkValue": parts[0]["value"],
            "parts": parts, "coastDetail": raw,
        })
    dr = dynamics_source["versilia"]
    dynamics_aggregate_parts = [
        {**dynamics_parts[0], "value": share(dr["erosionKm"], dr["analysedKm"]), "kilometres": dr["erosionKm"]},
        {**dynamics_parts[1], "value": share(dr["stableKm"], dr["analysedKm"]), "kilometres": dr["stableKm"]},
        {**dynamics_parts[2], "value": share(dr["advanceKm"], dr["analysedKm"]), "kilometres": dr["advanceKm"]},
    ]
    dynamics_meta = base_meta(
        KEYS[3], "Dinamica del litorale", "Dinamica del litorale",
        "Quota della costa naturale bassa in erosione, stabile o in avanzamento tra 2006 e 2020 secondo le variazioni superiori a 5 metri rilevate da ISPRA.",
        "percent", "2006–2020", "ISPRA — Dinamica litoranea",
        ["erosione", "avanzamento", "litorale", "costa", "spiaggia", "stabilità"],
    )
    dynamics_meta.update({
        "compositeType": "securityMeasures",
        "selectorLabel": "Dinamica",
        "comparisonReference": "aggregate",
        "comparisonDifference": "percentagePoints",
        "comparisonLabel": "quota Versilia costiera",
        "comparisonOverline": "Rispetto alla quota Versilia costiera",
        "comparisonNote": "Il riferimento usa i chilometri della classe selezionata divisi per i chilometri analizzati complessivi dei quattro Comuni costieri; non la media semplice delle percentuali comunali.",
    })
    dynamics = {
        "meta": dynamics_meta,
        "sourceUrl": ISPRA_DYNAMICS_URL,
        "rows": dynamics_rows,
        "aggregate": {
            "value": dynamics_aggregate_parts[0]["value"],
            "label": "Versilia costiera · dinamica del litorale",
            "parts": dynamics_aggregate_parts,
            "coastDetail": dr,
            "note": "Quote calcolate sulle somme dei chilometri dei quattro Comuni costieri, non come media delle percentuali comunali.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione su indicatore territoriale ISPRA",
            "formula": "Erosione: arretramento >5 m; stabile: variazione entro ±5 m; avanzamento: >5 m. Quota = km della classe / km di costa naturale bassa analizzata × 100.",
            "caveat": "L'universo è la costa naturale bassa analizzata da ISPRA, diverso dalla lunghezza usata nella card Costa protetta. Avanzamento ed erosione non sono classificati automaticamente come esito positivo o negativo.",
            "coverage": "4/4 Comuni costieri + 3 n.a.",
            "snapshot": SNAPSHOT_REF,
        },
    }

    protected_rows = []
    for town in towns:
        code = town["code"]
        if code in NOT_APPLICABLE_CODES:
            protected_rows.append(not_applicable_row(town, slugs[code]))
            continue
        raw = protected_source["towns"][code]
        value = share(raw["protectedKm"], raw["coastKm"])
        protected_rows.append({
            "town": town["name"], "code": code, "slug": slugs[code],
            "value": value, "formatted": f"{value:.1f}%".replace(".", ","),
            "series": None, "normalized": None, "benchmarkValue": value,
            "coastDetail": raw,
        })
    pr = protected_source["versilia"]
    protected_value = share(pr["protectedKm"], pr["coastKm"])
    protected_meta = base_meta(
        KEYS[4], "Costa protetta da opere di difesa rigide", "Costa protetta",
        "Quota della costa protetta da opere di difesa rigide secondo la metodologia territoriale ISPRA 2020.",
        "percent", "2020", "ISPRA — Costa protetta",
        ["costa protetta", "opere rigide", "difesa costiera", "litorale", "erosione"],
    )
    protected_meta.update({
        "comparisonReference": "aggregate",
        "comparisonDifference": "percentagePoints",
        "comparisonLabel": "quota Versilia",
        "comparisonOverline": "Rispetto alla quota Versilia",
        "comparisonNote": "La quota Versilia è il rapporto tra i chilometri complessivamente protetti e la costa complessiva dei quattro Comuni costieri; non è la media semplice delle percentuali comunali.",
    })
    protected = {
        "meta": protected_meta,
        "sourceUrl": ISPRA_PROTECTED_URL,
        "rows": protected_rows,
        "aggregate": {
            "value": protected_value,
            "label": "Versilia costiera · costa protetta",
            "note": "0,634 km protetti su 20,754 km di costa nel perimetro ISPRA 2020.",
            "coastDetail": pr,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Indicatore territoriale ISPRA",
            "formula": "km di costa protetta da opere rigide / km di costa dell'universo ISPRA × 100; aggregato Versilia sui km elementari.",
            "caveat": "Il denominatore è diverso da quello della Dinamica del litorale. L'indicatore esclude i ripascimenti artificiali. Lo zero di Viareggio è un valore reale della fonte, non un dato mancante.",
            "coverage": "4/4 Comuni costieri + 3 n.a.",
            "snapshot": SNAPSHOT_REF,
        },
    }

    return OrderedDict(zip(KEYS, (quality, samples, flags, dynamics, protected), strict=True))


def apply_site(site: dict[str, Any], snapshot: dict[str, Any]) -> None:
    validate_snapshot(snapshot, site)
    metrics = build_metrics(site, snapshot)
    rebuilt: OrderedDict[str, dict[str, Any]] = OrderedDict()
    inserted = False
    for key, metric in site["metrics"].items():
        if key in KEYS:
            continue
        rebuilt[key] = metric
        if key == "irrigatedAgriculturalArea" and not inserted:
            rebuilt.update(metrics)
            inserted = True
    if not inserted:
        raise RuntimeError("Punto di inserimento Ambiente non trovato")
    site["metrics"] = rebuilt

    theme = site["themes"]["ambiente"]
    theme["description"] = "Clima, suolo, costa, mare, rifiuti, agricoltura, uso del territorio ed esposizione ai rischi idrogeologici."
    sections = [section for section in theme["sections"] if section.get("key") != "costa-mare"]
    coast_section = {
        "key": "costa-mare",
        "label": "Costa e mare",
        "description": "Balneazione, riconoscimenti FEE e assetto fisico del litorale nei quattro Comuni costieri.",
        "metrics": list(KEYS),
    }
    climate_index = next((index for index, section in enumerate(sections) if section.get("key") == "clima"), None)
    if climate_index is None:
        raise RuntimeError("Sezione Clima non trovata")
    sections.insert(climate_index + 1, coast_section)
    theme["sections"] = sections
    theme["metrics"] = [key for section in sections for key in section["metrics"]]
    site["version"] = VERSION
    site["updated"] = UPDATED


def apply_registry(registry: dict[str, Any]) -> None:
    profiles = registry.setdefault("sourceProfiles", {})
    profiles["arpat-bathing-annual"] = {
        "publisher": "ARPAT",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Dopo la conclusione e validazione della stagione balneare",
        "acquisitionMethod": "Download dei dati e del rapporto ufficiale ARPAT; deduplica dei campioni su Codice area + Data + Rout./Suppl.; classificazioni e chilometri conservati nello snapshot.",
        "licenseName": "Condizioni ARPAT",
        "licenseUrl": ARPAT_URL,
    }
    profiles["fee-blue-flag-annual"] = {
        "publisher": "FEE Italia",
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Primavera dell'anno di assegnazione",
        "acquisitionMethod": "Consultazione degli elenchi ufficiali FEE Italia; località separate contate una volta, denominazioni unite da / non spezzate.",
        "licenseName": "Condizioni FEE Italia",
        "licenseUrl": BLUE_FLAG_URL,
    }
    profiles["ispra-coast-irregular"] = {
        "publisher": "ISPRA",
        "frequency": "census_or_irregular",
        "frequencyLabel": "Quinquennale o irregolare",
        "expectedRelease": "Alla pubblicazione di un nuovo rilievo costiero ISPRA omogeneo",
        "acquisitionMethod": "Download delle tabelle comunali ufficiali ISPRA e calcolo delle quote sui chilometri elementari, senza medie di percentuali.",
        "licenseName": "Condizioni ISPRA",
        "licenseUrl": ISPRA_DYNAMICS_URL,
    }
    mapping = {
        ARPAT_URL: "arpat-bathing-annual",
        ARPAT_ARCHIVE_URL: "arpat-bathing-annual",
        BLUE_FLAG_URL: "fee-blue-flag-annual",
        ISPRA_DYNAMICS_URL: "ispra-coast-irregular",
        ISPRA_PROTECTED_URL: "ispra-coast-irregular",
    }
    for url, profile in mapping.items():
        registry.setdefault("sourceProfileByUrl", {})[url] = profile
        registry.setdefault("sourceUrlProfiles", {})[url] = profile
    overrides = registry.setdefault("metricOverrides", {})
    overrides[KEYS[0]] = {"profile": "arpat-bathing-annual"}
    overrides[KEYS[1]] = {"profile": "arpat-bathing-annual"}
    overrides[KEYS[2]] = {"profile": "fee-blue-flag-annual"}
    overrides[KEYS[3]] = {"profile": "ispra-coast-irregular"}
    overrides[KEYS[4]] = {"profile": "ispra-coast-irregular"}
    registry["expectedMetricCount"] = 162
    registry["expectedInlineMetricCount"] = 158
    registry["expectedExternalMetricCount"] = 4


def apply_monitor_state(state: dict[str, Any]) -> None:
    checked = "2026-08-28T18:00:00+00:00"
    source_config = {
        ARPAT_URL: ([KEYS[0], KEYS[1]], "arpat-bathing-annual", "annual"),
        BLUE_FLAG_URL: ([KEYS[2]], "fee-blue-flag-annual", "annual"),
        ISPRA_DYNAMICS_URL: ([KEYS[3]], "ispra-coast-irregular", "census_or_irregular"),
        ISPRA_PROTECTED_URL: ([KEYS[4]], "ispra-coast-irregular", "census_or_irregular"),
    }
    for url, (metrics, profile, frequency) in source_config.items():
        state.setdefault("sources", {})[url] = {
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
            "metrics": metrics,
            "roles": ["primary"],
            "profileIds": [profile],
            "frequencies": [frequency],
        }
    periods = {
        KEYS[0]: "2025",
        KEYS[1]: "2025",
        KEYS[2]: "2026",
        KEYS[3]: "2006–2020",
        KEYS[4]: "2020",
    }
    for key, period in periods.items():
        state.setdefault("metrics", {})[key] = {
            "publishedPeriod": period,
            "checkedAt": checked,
            "observedLatestPeriod": period,
            "status": "current",
        }


def patch_search_terms() -> None:
    marker = "    irrigatedAgriculturalArea: ['irrigazione', 'superficie irrigata', 'sau irrigata'],"
    addition = marker + "\n    bathingWaterQuality: ['balneazione', 'qualità acque', 'mare', 'aree eccellenti'],\n    bathingNonCompliantSamples: ['balneazione', 'campioni non conformi', 'escherichia coli', 'enterococchi'],\n    blueFlagBeaches: ['bandiera blu', 'spiagge', 'mare', 'fee'],\n    shorelineDynamics: ['erosione', 'avanzamento', 'litorale', 'costa'],\n    rigidDefenceProtectedCoast: ['costa protetta', 'opere rigide', 'difesa costiera'],"
    replace_required(APP_PART_00, marker, addition)


def patch_release_files() -> None:
    replacements = {
        FINALIZER: [
            ('catalogo pubblico v1.22.0', 'catalogo pubblico v1.23.0'),
            ('VERSION = "v1.22.0"', 'VERSION = "v1.23.0"'),
            ('EXPECTED_METRICS = 157', 'EXPECTED_METRICS = 162'),
            ('EXPECTED_INLINE = 153', 'EXPECTED_INLINE = 158'),
        ],
        README: [
            ('Versione dati corrente: **v1.22.0** — 28 agosto 2026.', 'Versione dati corrente: **v1.23.0** — 28 agosto 2026.'),
            ('157 indicatori nel catalogo canonico: 153 con valori incorporati', '162 indicatori nel catalogo canonico: 158 con valori incorporati'),
            ('`indicatori/`: 153 pagine canoniche', '`indicatori/`: 158 pagine canoniche'),
            ('catalogo canonico dei 157 indicatori, con dati incorporati per 153', 'catalogo canonico dei 162 indicatori, con dati incorporati per 158'),
            ('metadati dei 157 indicatori', 'metadati dei 162 indicatori'),
            ('valida tutti i 157 indicatori canonici, la ripartizione fra 153 valori incorporati', 'valida tutti i 162 indicatori canonici, la ripartizione fra 158 valori incorporati'),
            ('ciascuno dei 153 indicatori incorporati', 'ciascuno dei 158 indicatori incorporati'),
        ],
        APP_JS: [("const VERSION='20260828-v122-lifeexp-ui1';", f"const VERSION='{ASSET_VERSION}';")],
        UX_HISTORY: [("const HOTFIX_VERSION = '20260828-v122-lifeexp-ui1';", f"const HOTFIX_VERSION = '{ASSET_VERSION}';")],
        EXPORT_JS: [("const VERSION = '20260828-v122-lifeexp-ui1';", f"const VERSION = '{ASSET_VERSION}';")],
        SERVICE_WORKER: [("const VERSION = 'ov-pwa-20260828-v122-lifeexp-ui1';", f"const VERSION = '{PWA_VERSION}';")],
        BUILD_SAFE: [
            ('UX_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'UX_ASSET_VERSION = "{ASSET_VERSION}"'),
            ('HISTORY_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'HISTORY_ASSET_VERSION = "{ASSET_VERSION}"'),
        ],
        BUILD_BRAND: [
            ('APP_BUNDLE_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'APP_BUNDLE_ASSET_VERSION = "{ASSET_VERSION}"'),
            ('PWA_JS_REVISION = "catalog-v122"', 'PWA_JS_REVISION = "catalog-v123"'),
        ],
    }
    for path, pairs in replacements.items():
        for old, new in pairs:
            replace_required(path, old, new)

    v123 = "      ['2026.08.28-v1.23.0','28 agosto 2026','162 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Costa e mare: qualità delle aree di balneazione, campioni non conformi, spiagge Bandiera Blu, dinamica del litorale e costa protetta da opere rigide, con 4 Comuni costieri e 3 n.a. senza stime.'],"
    v122 = "      ['2026.08.28-v1.22.0','28 agosto 2026','157 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Estesa la Speranza di vita alla nascita con serie ufficiali ARS 2008–2022 per Totale, Maschi e Femmine, aggregato ufficiale Versilia e benchmark Toscana.'],"
    text = APP_PART_05.read_text(encoding="utf-8")
    if v123 not in text:
        if v122 not in text:
            raise RuntimeError("Changelog v1.22.0 non trovato")
        APP_PART_05.write_text(text.replace(v122, f"{v123}\n{v122}", 1), encoding="utf-8")

    history = HISTORY_DOC.read_text(encoding="utf-8")
    if "## Lotto Costa e mare v1.23.0" not in history:
        history += (
            "\n\n## Lotto Costa e mare v1.23.0\n\n"
            "Il lotto usa quattro Comuni costieri (Camaiore, Forte dei Marmi, Pietrasanta e Viareggio). "
            "Massarosa, Seravezza e Stazzema sono fuori dall'universo marino e vengono resi `n.a.`, mai zero o `n.d.`. "
            "La classificazione ARPAT 2025 è quadriennale (2022–2025), mentre i campioni non conformi descrivono la sola stagione 2025. "
            "Gli aggregati delle quote sono rapporti delle somme elementari. Bandiera Blu conserva lo storico ufficiale 2019–2026; "
            "Pietrasanta è assente nel 2021 senza interpolazione. Dinamica del litorale e Costa protetta restano card separate perché usano universi ISPRA diversi.\n\n"
            "Il candidato Ripascimenti resta rinviato: non è stato reperito un dataset ufficiale strutturato con codice, tratto o Comune, anno, volume, stato di realizzazione e chiave di deduplicazione.\n"
        )
        HISTORY_DOC.write_text(history, encoding="utf-8")

    coherence = COHERENCE_DOC.read_text(encoding="utf-8")
    if "### Selettori Costa e mare" not in coherence:
        note = (
            "\n### Selettori Costa e mare\n\n"
            "Qualità delle aree, campioni non conformi e dinamica del litorale riusano il selettore composito canonico. "
            "Le tabelle di dettaglio dichiarano numeratori, denominatori e chilometri. I Comuni non costieri espongono `n.a.` "
            "e non partecipano a ordinamento, media o aggregazione.\n"
        )
        coherence = coherence.replace("\n## Profili ed eccezioni esplicite", note + "\n## Profili ed eccezioni esplicite")
        COHERENCE_DOC.write_text(coherence, encoding="utf-8")

    test = CATALOG_TEST.read_text(encoding="utf-8")
    test = test.replace("release v1.22.0", "release v1.23.0")
    test = test.replace(
        'assert "2026.08.28-v1.22.0" in app and "2026.08.27-v1.21.0" in app and "157 indicatori complessivi" in app',
        'assert "2026.08.28-v1.23.0" in app and "2026.08.28-v1.22.0" in app and "162 indicatori complessivi" in app',
    )
    test = test.replace('assert "**v1.22.0** — 28 agosto 2026" in readme', 'assert "**v1.23.0** — 28 agosto 2026" in readme')
    test = test.replace('assert "157 indicatori" in readme and "153 con valori incorporati" in readme', 'assert "162 indicatori" in readme and "158 con valori incorporati" in readme')
    test = test.replace('UX_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'UX_ASSET_VERSION = "{ASSET_VERSION}"')
    test = test.replace('HISTORY_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'HISTORY_ASSET_VERSION = "{ASSET_VERSION}"')
    test = test.replace('APP_BUNDLE_ASSET_VERSION = "20260828-v122-lifeexp-ui1"', f'APP_BUNDLE_ASSET_VERSION = "{ASSET_VERSION}"')
    test = test.replace('PWA_JS_REVISION = "catalog-v122"', 'PWA_JS_REVISION = "catalog-v123"')
    test = test.replace('assert "20260828-v122" in development_loader', 'assert "20260828-v123" in development_loader')
    test = test.replace("const VERSION = '20260828-v122-lifeexp-ui1';", f"const VERSION = '{ASSET_VERSION}';")
    test = test.replace('assert "ov-pwa-20260828-v122" in service_worker', 'assert "ov-pwa-20260828-v123" in service_worker')
    CATALOG_TEST.write_text(test, encoding="utf-8")


def main() -> int:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    state = load(STATE_PATH)
    snapshot = load(SNAPSHOT_PATH)
    apply_site(site, snapshot)
    apply_registry(registry)
    apply_monitor_state(state)
    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(STATE_PATH, state)
    patch_search_terms()
    patch_release_files()
    subprocess.run([sys.executable, str(FINALIZER)], check=True, cwd=ROOT)
    print("Costa e mare v1.23.0 materializzata: 5 indicatori canonici, 4 Comuni costieri + 3 n.a.; Ripascimenti rinviato.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
