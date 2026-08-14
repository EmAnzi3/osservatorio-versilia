#!/usr/bin/env python3
"""Materializza il draft Sicurezza e territorio nel catalogo e nei moduli canonici.

Idempotente sul branch di lavoro. I dati Istat sono conservati nello snapshot
versionato; la Missione 03 viene acquisita da OpenBDAP solo se non è già stata
materializzata.
"""
from __future__ import annotations

import csv
import io
import json
import statistics
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "sicurezza-territorio-draft-2026-08.json"
APP00 = ROOT / "assets" / "app-parts" / "00.txt"
APP03 = ROOT / "assets" / "app-parts" / "03.txt"
APP05 = ROOT / "assets" / "app-parts" / "05.txt"

OPENBDAP_BASE = "https://openbdap.rgs.mef.gov.it"
OPENBDAP_PORTAL = OPENBDAP_BASE + "/it/FET/Analizza"
TOWN_CODES = {
    "Massarosa": "018", "Viareggio": "033", "Camaiore": "005",
    "Pietrasanta": "024", "Seravezza": "028", "Forte dei Marmi": "013",
    "Stazzema": "030",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mean(values):
    clean = [float(v) for v in values if v is not None]
    return statistics.fmean(clean) if clean else None


def population_lookup(data: dict) -> dict[str, dict[int, float]]:
    result = {}
    for row in data["metrics"]["population"]["rows"]:
        series = row.get("series") or {}
        result[row["town"]] = {
            int(year): float(value)
            for year, value in zip(series.get("years", []), series.get("values", []))
        }
        result[row["town"]].setdefault(
            int(data["metrics"]["population"]["meta"]["year"]), float(row["value"])
        )
    return result


def fetch_mission03(year: int) -> dict[str, float]:
    url = (
        f"{OPENBDAP_BASE}/Datasets_FET/Rendiconto/{year}/"
        f"{year}_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [
            info for info in archive.infolist()
            if info.filename.endswith("Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv")
        ]
        if len(members) != 1:
            raise RuntimeError(f"{year}: file missioni inatteso")
        raw = archive.read(members[0])
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    reverse = {code: town for town, code in TOWN_CODES.items()}
    result = {}
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
            continue
        if (row.get("Codice Provincia") or "").strip() != "046":
            continue
        code = (row.get("Codice Comune") or "").strip().zfill(3)
        if code not in reverse:
            continue
        if (row.get("Codice Missione") or "").strip().zfill(2) != "03":
            continue
        value = (row.get("Impegni") or "").strip()
        if value:
            result[reverse[code]] = float(value)
    if set(result) != set(TOWN_CODES):
        raise RuntimeError(f"{year}: Missione 03 incompleta ({sorted(result)})")
    return result


def build_road_safety(data: dict, snapshot: dict) -> dict:
    old = data["metrics"]["roadInjuries"]
    rows, accum = [], [[], [], [], []]
    for old_row in old["rows"]:
        raw = snapshot["towns"][old_row["town"]]
        specifications = [
            ("Incidenti con lesioni", "Incidenti", raw["roadIncidentRate"], "per1000"),
            ("Indice di mortalità", "Mortalità", raw["roadMortalityIndex"], "per100"),
            ("Indice di lesività", "Lesività", raw["roadInjuryIndex"], "per100"),
            ("Feriti ogni 10.000 residenti", "Feriti", {
                "years": old_row["series"]["years"],
                "values": old_row["series"]["values"],
            }, "per10k"),
        ]
        parts, component_series = [], {}
        for index, (label, selector, series, unit) in enumerate(specifications):
            value = series["values"][-1]
            accum[index].append(value)
            parts.append({"label": label, "selectorLabel": selector, "value": value, "unit": unit})
            component_series[selector] = series
        rows.append({
            "town": old_row["town"], "code": old_row["code"], "slug": old_row["slug"],
            "value": parts[0]["value"], "formatted": "", "series": specifications[0][2],
            "normalized": None, "benchmarkValue": parts[0]["value"], "parts": parts,
            "componentSeries": component_series,
        })
    labels = [
        ("Incidenti con lesioni", "Incidenti", "per1000"),
        ("Indice di mortalità", "Mortalità", "per100"),
        ("Indice di lesività", "Lesività", "per100"),
        ("Feriti ogni 10.000 residenti", "Feriti", "per10k"),
    ]
    aggregate_parts = [
        {"label": label, "selectorLabel": selector, "value": mean(accum[index]), "unit": unit}
        for index, (label, selector, unit) in enumerate(labels)
    ]
    benchmark = snapshot["benchmarks"]["roadIncidentRate"]
    return {
        "meta": {
            "key": "roadSafety", "theme": "sicurezza", "label": "Sicurezza stradale",
            "shortLabel": "Sicurezza stradale",
            "description": "Incidenti stradali con lesioni e gravità delle conseguenze. Il selettore distingue incidentalità, mortalità, lesività e feriti.",
            "unit": "per1000", "year": "2024",
            "source": "Istat — A misura di Comune, incidenti stradali",
            "polarity": "negative", "compositeType": "securityMeasures", "selectorLabel": "Lettura",
            "searchTerms": ["incidenti", "mortalità stradale", "lesività", "feriti"],
            "benchmark": {
                "year": 2024, "tuscany": benchmark["tuscany"], "italy": benchmark["italy"],
                "source": "Istat — A misura di Comune", "url": snapshot["sources"]["istat15a"]["url"],
                "note": "Benchmark riferito agli incidenti con lesioni ogni 1.000 residenti.",
            },
        },
        "sourceUrl": snapshot["sources"]["istat15a"]["url"], "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"], "label": "Media semplice dei 7 comuni",
            "note": "Ogni Comune pesa allo stesso modo; non è un dato ufficiale di area.",
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dati ufficiali ed elaborazione Osservatorio",
            "formula": "Incidentalità: incidenti con lesioni / popolazione residente media × 1.000; mortalità: morti / incidenti × 100; lesività: feriti / incidenti × 100; feriti: feriti / residenti × 10.000.",
            "caveat": "L’intensità del traffico e la funzione delle strade incidono sul confronto. Mortalità e lesività sono instabili nei Comuni con pochi incidenti.",
            "coverage": "7/7",
        },
    }


def build_fines(snapshot: dict) -> dict:
    rows, accumulator = [], [[], []]
    for town, raw in snapshot["towns"].items():
        parts = [
            {"label": "Proventi complessivi per abitante", "selectorLabel": "Proventi €/abitante", "value": raw["roadFinesPerResident"]["values"][-1], "unit": "currency"},
            {"label": "Quota riferita ai limiti di velocità", "selectorLabel": "Quota da velocità", "value": raw["speedFineShare"]["values"][-1], "unit": "percent"},
        ]
        accumulator[0].append(parts[0]["value"])
        accumulator[1].append(parts[1]["value"])
        rows.append({
            "town": town, "code": raw["code"],
            "slug": town.lower().replace(" ", "-").replace("à", "a"),
            "value": parts[0]["value"], "formatted": "", "series": raw["roadFinesPerResident"],
            "normalized": None, "benchmarkValue": parts[0]["value"], "parts": parts,
            "componentSeries": {
                "Proventi €/abitante": raw["roadFinesPerResident"],
                "Quota da velocità": raw["speedFineShare"],
            },
        })
    aggregate_parts = [
        {"label": "Proventi complessivi per abitante", "selectorLabel": "Proventi €/abitante", "value": mean(accumulator[0]), "unit": "currency"},
        {"label": "Quota riferita ai limiti di velocità", "selectorLabel": "Quota da velocità", "value": mean(accumulator[1]), "unit": "percent"},
    ]
    benchmark = snapshot["benchmarks"]["roadFinesPerResident"]
    return {
        "meta": {
            "key": "roadFinesPerResident", "theme": "sicurezza",
            "label": "Proventi da sanzioni al Codice della strada", "shortLabel": "Sanzioni stradali",
            "description": "Proventi per violazioni al Codice della strada rapportati alla popolazione residente media; il dettaglio distingue la quota riferita ai limiti di velocità.",
            "unit": "currency", "year": "2024",
            "source": "Istat / Ministero dell’Interno — A misura di Comune",
            "polarity": "neutral", "compositeType": "securityMeasures", "selectorLabel": "Lettura",
            "searchTerms": ["multe", "sanzioni", "codice della strada", "autovelox"],
            "benchmark": {
                "year": 2024, "tuscany": benchmark["tuscany"], "italy": benchmark["italy"],
                "source": "Istat / Ministero dell’Interno", "url": snapshot["sources"]["istat15c"]["url"],
                "note": "Benchmark riferito ai proventi complessivi per abitante.",
            },
        },
        "sourceUrl": snapshot["sources"]["istat15c"]["url"], "rows": rows,
        "aggregate": {
            "value": aggregate_parts[0]["value"], "label": "Media semplice dei 7 comuni",
            "note": "Ogni Comune pesa allo stesso modo; il dato non misura direttamente il livello di sicurezza.",
            "parts": aggregate_parts,
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Dato ufficiale Istat / DAIT",
            "formula": "Proventi complessivi CdS / popolazione residente media; quota velocità: proventi per violazioni dei limiti / proventi CdS complessivi × 100.",
            "caveat": "Il valore dipende anche da turismo, traffico di attraversamento, intensità dei controlli e organizzazione della riscossione. Polarità neutra.",
            "coverage": "7/7",
        },
    }


def build_mission(data: dict) -> dict:
    raw = {year: fetch_mission03(year) for year in (2024, 2025)}
    populations = population_lookup(data)
    population_rows = {row["town"]: row for row in data["metrics"]["population"]["rows"]}
    rows, total, population_total = [], 0.0, 0.0
    for town in TOWN_CODES:
        values = [raw[year][town] / populations[town][year] for year in (2024, 2025)]
        population_row = population_rows[town]
        rows.append({
            "town": town, "code": population_row["code"], "slug": population_row["slug"],
            "value": values[-1], "formatted": "", "series": {"years": [2024, 2025], "values": values},
            "normalized": None, "benchmarkValue": values[-1],
        })
        total += raw[2025][town]
        population_total += populations[town][2025]
    return {
        "meta": {
            "key": "securityMissionExpenditurePerResident", "theme": "sicurezza",
            "label": "Spesa impegnata per ordine pubblico e sicurezza per residente",
            "shortLabel": "Spesa per sicurezza",
            "description": "Impegni della Missione 03 «Ordine pubblico e sicurezza» del rendiconto comunale, rapportati ai residenti.",
            "unit": "currency", "year": "2025", "source": "Ragioneria generale dello Stato — OpenBDAP",
            "polarity": "neutral", "searchTerms": ["ordine pubblico", "sicurezza", "missione 03", "spesa sicurezza"],
        },
        "sourceUrl": OPENBDAP_PORTAL, "rows": rows,
        "aggregate": {
            "value": total / population_total, "label": "Valore pro capite Versilia",
            "note": "Totale degli impegni Missione 03 dei sette Comuni rapportato alla popolazione complessiva.",
        },
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio su dati ufficiali", "formula": "Impegni Missione 03 / popolazione residente.",
            "caveat": "La classificazione comprende spesa corrente e in conto capitale; gestione associata, stagionalità e organizzazione dei servizi incidono sul confronto.",
            "coverage": "7/7",
        },
    }


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Patch non applicabile: {label}")
    return text.replace(old, new, 1)


def patch_app03(app: str) -> str:
    replacements = [
        (
            "    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n    return { choice:'', scale:'value' };",
            "    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n    if (metric.meta.compositeType === 'securityMeasures') return { choice:'part-0', scale:'value' };\n    return { choice:'', scale:'value' };",
            "default securityMeasures",
        ),
        (
            "    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);\n      const part = row.parts?.[index] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, part, index };\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));",
            "selection securityMeasures",
        ),
        (
            "    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));\n      const part = metric.aggregate?.parts?.[index] || {};",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));\n      const part = metric.aggregate?.parts?.[index] || {};",
            "aggregate securityMeasures",
        ),
        (
            "    if (metric.meta.compositeType === 'mobility') {\n      const labels = metric.rows?.[0]?.parts || [];",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      const labels = metric.rows?.[0]?.parts || [];\n      return `<div class=\"compare-view-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${labels.map((part,index)=>`<option value=\"part-${index}\" ${choice === `part-${index}` ? 'selected' : ''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`;\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const labels = metric.rows?.[0]?.parts || [];",
            "controls securityMeasures",
        ),
        (
            "    const selectableComposite = ['stock','mobility','omi'].includes(compositeType);",
            "    const selectableComposite = ['stock','mobility','omi','securityMeasures'].includes(compositeType);",
            "compare selectable",
        ),
        (
            "    if (metric.meta.compositeType === 'mobility') {\n      const headParts = metric.rows?.[0]?.parts || [];",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      const defaults = compositeCompareDefaults(metric);\n      return `<div class=\"comparison-bars\">${compositeCompareBarRows(data,metricKey,defaults.choice,defaults.scale)}</div>`;\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const headParts = metric.rows?.[0]?.parts || [];",
            "comparison markup securityMeasures",
        ),
        (
            "    if (metric.meta.compositeType === 'mobility') {\n      return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>`<article class=\"${index===0?'balance':''}\"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>`;\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>",
            "town detail securityMeasures",
        ),
        (
            "    if (metric.meta.compositeType !== 'distribution') return [];",
            "    if (metric.meta.compositeType === 'securityMeasures') return (row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatValue(part.value,part.unit || metric.meta.unit), index }));\n    if (metric.meta.compositeType !== 'distribution') return [];",
            "town options securityMeasures",
        ),
        (
            "    if (choice === 'summary') return compositeAggregateSummary(metric);",
            "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index = Math.max(0, Number(String(choice || 'part-0').replace('part-','')) || 0);\n      const part = metric.aggregate?.parts?.[index] || {};\n      const unit = part.unit || metric.meta.unit;\n      return { label:`Versilia · ${part.label || metric.meta.label}`, value:part.value, unit, formatted:formatValue(part.value,unit) };\n    }\n    if (choice === 'summary') return compositeAggregateSummary(metric);",
            "town aggregate securityMeasures",
        ),
        (
            "      if (metric.meta.compositeType === 'omi') return { code:r.code, value:Number(choice === 'rent' ? r.rentMean : r.saleMean) };\n      if (choice === 'summary')",
            "      if (metric.meta.compositeType === 'omi') return { code:r.code, value:Number(choice === 'rent' ? r.rentMean : r.saleMean) };\n      if (metric.meta.compositeType === 'securityMeasures') { const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); return { code:r.code, value:Number(r.parts?.[index]?.value) }; }\n      if (choice === 'summary')",
            "town rank securityMeasures",
        ),
        (
            "    const stock = metric.meta.compositeType === 'stock';\n    const selectable = distribution || omi || stock;",
            "    const stock = metric.meta.compositeType === 'stock';\n    const securityMeasures = metric.meta.compositeType === 'securityMeasures';\n    const selectable = distribution || omi || stock || securityMeasures;",
            "town selectable flag",
        ),
        (
            "    const summary = distribution ? compositeSummary(metric,row) : ((omi || stock) ? options[0] : null);",
            "    const summary = distribution ? compositeSummary(metric,row) : ((omi || stock || securityMeasures) ? options[0] : null);",
            "town summary",
        ),
        (
            "    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : null));",
            "    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)));",
            "town aggregate summary",
        ),
        (
            "    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')",
            "    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')",
            "town panel overline",
        ),
        (
            "    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`)",
            "    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`)",
            "town panel title",
        ),
        (
            "    else if (metric.meta.compositeType) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, metric.meta.unit, part.count, metric.sourceUrl])));",
            "    else if (metric.meta.compositeType) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, part.unit || metric.meta.unit, part.count, metric.sourceUrl])));",
            "CSV unità composito",
        ),
    ]
    for old, new, label in replacements:
        app = replace_once(app, old, new, label)

    app = replace_once(
        app,
        "      ${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}\n      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}",
        "      ${themeKey === 'sicurezza' ? localPoliceDraftMarkup(data) + crimeMarkup(data) : ''}\n      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}",
        "Polizia Locale nella pagina confronto",
    )
    app = replace_once(
        app,
        "    context.innerHTML = themeKey === 'sicurezza' ? crimeMarkup(data) : (themeKey === 'demografia' ? brainDrainMarkup(data) : '');",
        "    context.innerHTML = themeKey === 'sicurezza' ? localPoliceDraftMarkup(data) + crimeMarkup(data) : (themeKey === 'demografia' ? brainDrainMarkup(data) : '');",
        "Polizia Locale nella scheda comunale",
    )
    return app


def patch_app05(app: str) -> str:
    if "function localPoliceDraftMarkup(data)" in app:
        return app
    marker = "  function crimeMarkup(data) {"
    if marker not in app:
        raise RuntimeError("crimeMarkup non trovato in app-parts/05.txt")
    function = '''  function localPoliceDraftMarkup(data) {
    const p = data.securityDraft?.localPolice;
    if (!p) return '';
    return `<section class="crime-context brain-drain-context page-width" id="polizia-locale"><div class="crime-context-copy"><span class="overline">Presidio locale · dato in verifica</span><h2>Polizia Locale</h2><p>Il monitoraggio regionale 2025 quantifica il personale complessivo toscano, ma le tavole pubblicate non espongono righe comunali utilizzabili per un confronto 7/7. L’Osservatorio non attribuisce quindi valori stimati ai singoli Comuni.</p><a class="source-pill" href="${html(p.sourceUrl)}" target="_blank" rel="noreferrer">Fonte Regione Toscana ↗</a></div><div class="crime-context-data"><h3>Monitoraggio regionale · 2025</h3><div class="crime-stats"><article><span>Addetti rilevati</span><strong>${html(number0.format(p.tuscanyStaff))}</strong><small>totale Toscana</small></article><article><span>Strutture rispondenti</span><strong>${html(number0.format(p.respondingStructures))}</strong><small>Polizie Locali</small></article><article><span>Comuni rappresentati</span><strong>${html(number0.format(p.municipalitiesRepresented))}</strong><small>dato aggregato</small></article></div><p class="brain-drain-note">Il riquadro non è conteggiato come indicatore comunale: verrà promosso solo con una fonte ufficiale omogenea per Comune.</p></div></section>`;
  }

'''
    return app.replace(marker, function + marker, 1)


def update_data_and_registry(data: dict, snapshot: dict) -> None:
    if "roadInjuries" in data["metrics"]:
        data["metrics"]["roadSafety"] = build_road_safety(data, snapshot)
        data["metrics"].pop("roadInjuries")
    data["metrics"]["roadFinesPerResident"] = build_fines(snapshot)

    mission = data["metrics"].get("securityMissionExpenditurePerResident")
    mission_status = data.get("securityDraft", {}).get("mission03Status", "")
    if not mission:
        try:
            mission = build_mission(data)
            data["metrics"]["securityMissionExpenditurePerResident"] = mission
            mission_status = "ok"
        except Exception as error:
            mission_status = f"{type(error).__name__}: {error}"

    metrics = ["roadSafety"]
    if mission:
        metrics.append("securityMissionExpenditurePerResident")
    metrics.append("roadFinesPerResident")
    data["themes"]["sicurezza"].update({
        "question": "Quanto è sicuro il territorio e quali risorse vengono dedicate al presidio?",
        "description": "Sicurezza stradale, risorse comunali e controllo della circolazione, mantenendo criminalità e Polizia Locale alla scala realmente disponibile.",
        "metrics": metrics,
        "sections": [
            {"key": "sicurezza-stradale", "label": "Sicurezza stradale", "description": "Frequenza degli incidenti e gravità delle conseguenze, con serie comunali omogenee.", "metrics": ["roadSafety"]},
            {"key": "risorse-controllo", "label": "Risorse e controllo", "description": "Spesa comunale per ordine pubblico e sicurezza e proventi delle sanzioni al Codice della strada.", "metrics": [key for key in ("securityMissionExpenditurePerResident", "roadFinesPerResident") if key in data["metrics"]]},
        ],
        "featured": metrics[:3],
    })
    local = snapshot["sources"]["localPolice2025"]
    data["securityDraft"] = {
        "status": "draft", "mission03Status": mission_status,
        "localPolice": {
            "sourceUrl": local["url"], "usableForMunicipalComparison": False,
            "note": local["note"], "tuscanyStaff": local["tuscany"]["staff"],
            "respondingStructures": local["tuscany"]["respondingStructures"],
            "municipalitiesRepresented": local["tuscany"]["municipalitiesRepresented"],
        },
    }
    save(DATA_PATH, data)

    registry = load(REGISTRY_PATH)
    external = int(registry.get("expectedExternalMetricCount", 4))
    registry["expectedMetricCount"] = len(data["metrics"])
    registry["expectedInlineMetricCount"] = len(data["metrics"]) - external
    registry["expectedExternalMetricCount"] = external
    registry.setdefault("sourceProfileByUrl", {})[snapshot["sources"]["istat15a"]["url"]] = "istat-road-annual"
    registry["sourceProfileByUrl"][snapshot["sources"]["istat15c"]["url"]] = "istat-road-annual"
    registry.setdefault("metricOverrides", {})["roadSafety"] = {"profile": "istat-road-annual"}
    registry["metricOverrides"]["roadFinesPerResident"] = {"profile": "istat-road-annual"}
    if mission:
        registry["metricOverrides"]["securityMissionExpenditurePerResident"] = {
            "frequency": "annual", "frequencyLabel": "Annuale",
            "expectedRelease": "Dopo il consolidamento del rendiconto",
            "acquisitionMethod": "Download OpenBDAP del rendiconto e lettura degli impegni della Missione 03.",
            "publisher": "Ragioneria generale dello Stato — OpenBDAP",
        }
    save(REGISTRY_PATH, registry)


def main() -> None:
    data = load(DATA_PATH)
    snapshot = load(SNAPSHOT_PATH)
    update_data_and_registry(data, snapshot)

    app00 = APP00.read_text(encoding="utf-8")
    anchor = "    capitalPayments: ['investimenti', 'conto capitale', 'pagamenti capitale']"
    if "roadSafety:" not in app00:
        if anchor not in app00:
            raise RuntimeError("Anchor sinonimi non trovato")
        app00 = app00.replace(
            anchor,
            "    roadSafety: ['incidenti', 'sicurezza stradale', 'mortalità', 'lesività', 'feriti'],\n"
            "    roadFinesPerResident: ['multe', 'sanzioni', 'codice della strada', 'autovelox'],\n"
            "    securityMissionExpenditurePerResident: ['ordine pubblico', 'sicurezza', 'missione 03', 'spesa sicurezza'],\n"
            + anchor,
            1,
        )
        APP00.write_text(app00, encoding="utf-8")

    APP03.write_text(patch_app03(APP03.read_text(encoding="utf-8")), encoding="utf-8")
    APP05.write_text(patch_app05(APP05.read_text(encoding="utf-8")), encoding="utf-8")
    print(
        f"Draft sicurezza applicato: {len(data['metrics'])} indicatori; "
        f"Missione 03: {data['securityDraft']['mission03Status']}"
    )


if __name__ == "__main__":
    main()
