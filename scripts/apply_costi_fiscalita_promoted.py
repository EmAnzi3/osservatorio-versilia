#!/usr/bin/env python3
"""Materializza gli indicatori promossi dopo l'audit costi/fiscalità del 15-08-2026."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'site-data.json'
REGISTRY_PATH = ROOT / 'data' / 'source-registry.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'costi-fiscalita-promoted-2026-08.json'
APP00 = ROOT / 'assets' / 'app-parts' / '00.txt'
APP03 = ROOT / 'assets' / 'app-parts' / '03.txt'


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(data: dict) -> dict[str, dict]:
    return {row['town']: {'code': row['code'], 'slug': row['slug']} for row in data['metrics']['income']['rows']}


def basic_metric(data: dict, *, key: str, theme: str, label: str, short: str, description: str,
                 unit: str, year: str, source: str, source_url: str, values: dict[str, float | None],
                 polarity: str = 'neutral', formula: str, caveat: str, coverage: str,
                 search_terms: list[str]) -> dict:
    ids = identity(data)
    rows = []
    clean = []
    for town in ids:
        value = values.get(town)
        if value is not None:
            clean.append(float(value))
        rows.append({
            'town': town, 'code': ids[town]['code'], 'slug': ids[town]['slug'],
            'value': value, 'formatted': '',
            'series': {'years': [int(year)] if year.isdigit() else [year], 'values': [value]},
            'normalized': None, 'benchmarkValue': value,
        })
    return {
        'meta': {
            'key': key, 'theme': theme, 'label': label, 'shortLabel': short,
            'description': description, 'unit': unit, 'year': year, 'source': source,
            'polarity': polarity, 'searchTerms': search_terms,
        },
        'sourceUrl': source_url,
        'rows': rows,
        'aggregate': {
            'value': statistics.fmean(clean) if clean else None,
            'label': 'Media semplice dei valori comunali disponibili',
            'note': f'Media semplice sui Comuni con dato disponibile ({coverage}). Non è un dato ufficiale di area.',
        },
        'normalizedAggregate': None,
        'method': {'type': 'Dato ufficiale / elaborazione Osservatorio', 'formula': formula, 'caveat': caveat, 'coverage': coverage},
    }


def build_fuel(data: dict, raw: dict) -> dict:
    ids = identity(data)
    rows = []
    collected = {'benzina': [], 'gasolio': []}
    for town in ids:
        item = raw['towns'][town]
        parts = []
        for fuel, label in [('benzina', 'Benzina self'), ('gasolio', 'Gasolio self')]:
            value = item[fuel]
            if value is not None:
                collected[fuel].append(float(value))
            parts.append({
                'label': label, 'selectorLabel': label.replace(' self', ''),
                'value': value, 'unit': 'eurLiter',
                'stationCount': item[f'{fuel}Stations'],
            })
        rows.append({
            'town': town, 'code': ids[town]['code'], 'slug': ids[town]['slug'],
            'value': parts[0]['value'], 'formatted': '',
            'series': {'years': [raw['referenceDate']], 'values': [parts[0]['value']]},
            'normalized': None, 'benchmarkValue': parts[0]['value'], 'parts': parts,
        })
    aggregate_parts = [
        {'label': 'Benzina self', 'selectorLabel': 'Benzina', 'value': statistics.fmean(collected['benzina']), 'unit': 'eurLiter'},
        {'label': 'Gasolio self', 'selectorLabel': 'Gasolio', 'value': statistics.fmean(collected['gasolio']), 'unit': 'eurLiter'},
    ]
    return {
        'meta': {
            'key': 'fuelPrices', 'theme': 'economia', 'label': 'Prezzi dei carburanti',
            'shortLabel': 'Prezzi carburanti',
            'description': 'Mediana comunale dei prezzi self-service praticati dagli impianti attivi. Il selettore distingue benzina e gasolio.',
            'unit': 'eurLiter', 'year': raw['referenceDate'], 'source': raw['source'],
            'polarity': 'negative', 'compositeType': 'securityMeasures', 'selectorLabel': 'Carburante',
            'searchTerms': ['benzina', 'gasolio', 'carburanti', 'prezzo carburante', 'distributori'],
        },
        'sourceUrl': raw['sourceUrl'], 'rows': rows,
        'aggregate': {
            'value': aggregate_parts[0]['value'], 'label': 'Media semplice delle mediane comunali disponibili',
            'note': 'Stazzema è n.d. perché l’anagrafica MIMIT non registra impianti attivi. La media Versilia usa quindi 6 Comuni.',
            'parts': aggregate_parts,
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su open data MIMIT',
            'formula': 'Per ciascun Comune e carburante: mediana dei prezzi self-service degli impianti attivi alla data di riferimento.',
            'caveat': 'Fotografia puntuale dei prezzi: non misura il costo annuo sostenuto dalle famiglie. Stazzema resta n.d.; non viene attribuito il prezzo di un Comune vicino.',
            'coverage': '6/7',
        },
    }


def insert_after(items: list, anchor: str, values: list[str]) -> None:
    for value in values:
        if value in items:
            items.remove(value)
    index = items.index(anchor) + 1 if anchor in items else len(items)
    for value in values:
        items.insert(index, value)
        index += 1


def patch_app() -> None:
    app00 = APP00.read_text(encoding='utf-8')
    if "case 'eurLiter'" not in app00:
        anchor = "      case 'rentm2': return `${number1.format(v)} €/m²/mese`;"
        app00 = app00.replace(anchor, anchor + "\n      case 'eurLiter': return `${number2.format(v)} €/l`;", 1)
    synonym_anchor = "    municipalIrpef: ['addizionale comunale', 'irpef comunale', 'aliquota irpef', 'fiscalità locale', 'tasse comunali'],"
    additions = [
        "    municipalTari: ['tari', 'tassa rifiuti', 'costo rifiuti famiglia'],",
        "    municipalImu: ['imu', 'seconda casa', 'altri fabbricati', 'imposta municipale'],",
        "    fuelPrices: ['benzina', 'gasolio', 'carburanti', 'prezzi carburanti'],",
        "    wasteServiceCost: ['costo rifiuti', 'ctot', 'igiene urbana', 'costo servizio rifiuti'],",
    ]
    if synonym_anchor in app00:
        block = synonym_anchor + ''.join('\n' + line for line in additions if line.split(':',1)[0].strip() + ':' not in app00)
        app00 = app00.replace(synonym_anchor, block, 1)
    APP00.write_text(app00, encoding='utf-8')

    app03 = APP03.read_text(encoding='utf-8')
    old = """    const rows = metric.rows.map(row => {\n      const selected = compositeCompareSelection(metric,row,choice,scale);\n      return { ...row, displayValue:selected.value, displayUnit:selected.unit };\n    }).sort((a,b)=>{const av=Number(a.displayValue),bv=Number(b.displayValue);return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);});\n    const max = Math.max(...rows.map(r => Math.abs(Number(r.displayValue) || 0)), 0.0001);\n    return rows.map((row,index) => {\n      const query = new URLSearchParams({ tema:metric.meta.theme, indicatore:metricKey });\n      const href = route(`comuni/${row.slug}/?${query}`);\n      return `<a href=\"${href}\" class=\"bar-row\" aria-label=\"${html(row.town)}: ${html(formatValue(row.displayValue,row.displayUnit))}\"><span class=\"bar-rank\">${index+1}</span><span class=\"bar-town\">${html(row.town)}</span><span class=\"bar-track\"><span class=\"bar-fill\" style=\"width:${Math.max(1.5,Math.abs(Number(row.displayValue)||0)/max*100)}%\"></span><span class=\"bar-hover-label\">${html(row.town)} · ${html(formatValue(row.displayValue,row.displayUnit))}</span></span><strong>${html(formatValue(row.displayValue,row.displayUnit))}</strong></a>`;\n    }).join('');"""
    new = """    const rows = metric.rows.map(row => {\n      const selected = compositeCompareSelection(metric,row,choice,scale);\n      return { ...row, displayValue:selected.value, displayUnit:selected.unit, missing:selected.value === null || selected.value === undefined || Number.isNaN(Number(selected.value)) };\n    }).sort((a,b)=>{const av=a.missing?-Infinity:Number(a.displayValue),bv=b.missing?-Infinity:Number(b.displayValue);return bv-av;});\n    const valid = rows.filter(r=>!r.missing);\n    const max = Math.max(...valid.map(r => Math.abs(Number(r.displayValue))), 0.0001);\n    return rows.map((row,index) => {\n      const query = new URLSearchParams({ tema:metric.meta.theme, indicatore:metricKey });\n      const href = route(`comuni/${row.slug}/?${query}`);\n      const rank = row.missing ? '—' : String(valid.findIndex(r=>r.code===row.code)+1);\n      const fill = row.missing ? 0 : Math.max(1.5,Math.abs(Number(row.displayValue))/max*100);\n      return `<a href=\"${href}\" class=\"bar-row${row.missing?' is-missing':''}\" aria-label=\"${html(row.town)}: ${html(formatValue(row.displayValue,row.displayUnit))}\"><span class=\"bar-rank\">${rank}</span><span class=\"bar-town\">${html(row.town)}</span><span class=\"bar-track\"><span class=\"bar-fill\" style=\"width:${fill}%\"></span><span class=\"bar-hover-label\">${html(row.town)} · ${html(formatValue(row.displayValue,row.displayUnit))}</span></span><strong>${html(formatValue(row.displayValue,row.displayUnit))}</strong></a>`;\n    }).join('');"""
    if old in app03:
        app03 = app03.replace(old, new, 1)
    old_rank = "if (metric.meta.compositeType === 'securityMeasures') { const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); return { code:r.code, value:Number(r.parts?.[index]?.value) }; }"
    new_rank = "if (metric.meta.compositeType === 'securityMeasures') { const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); const raw=r.parts?.[index]?.value; return { code:r.code, value:(raw===null||raw===undefined)?NaN:Number(raw) }; }"
    app03 = app03.replace(old_rank, new_rank, 1)
    APP03.write_text(app03, encoding='utf-8')


def main() -> None:
    data = load(DATA_PATH)
    raw = load(SNAPSHOT_PATH)

    data['metrics']['municipalTari'] = basic_metric(
        data, key='municipalTari', theme='economia', label='TARI standardizzata', short='TARI standardizzata',
        description='Spesa annua TARI per un’utenza domestica residente standard di 3 componenti e 100 m², senza agevolazioni personali.',
        unit='currency', year='2025', source=raw['tari']['source'], source_url=raw['tari']['sourceUrl'],
        values={town:item['annualCost'] for town,item in raw['tari']['towns'].items()}, polarity='negative',
        formula=raw['tari']['formula'], caveat='Benchmark standardizzato: non rappresenta la bolletta di una specifica famiglia. Sono escluse riduzioni ed esenzioni personali.',
        coverage='7/7', search_terms=['tari','tassa rifiuti','100 m²','3 componenti','costo rifiuti famiglia'])
    data['metrics']['municipalImu'] = basic_metric(
        data, key='municipalImu', theme='economia', label='IMU su seconda abitazione standard', short='IMU seconda abitazione',
        description='Imposta annua su una seconda abitazione A/2 con base imponibile IMU standardizzata di 100.000 €, identica nei sette Comuni.',
        unit='currency', year='2025', source=raw['imu']['source'], source_url=raw['imu']['sourceUrl'],
        values={town:item['annualTax'] for town,item in raw['imu']['towns'].items()}, polarity='negative',
        formula='Base imponibile standardizzata 100.000 € × aliquota 2025 per la fattispecie «Altri fabbricati».',
        caveat='È un benchmark della pressione fiscale comunale, non una stima della seconda casa tipica. La rendita catastale reale non viene stimata.',
        coverage='7/7', search_terms=['imu','seconda abitazione','seconda casa','altri fabbricati'])
    data['metrics']['fuelPrices'] = build_fuel(data, raw['fuelPrices'])
    data['metrics']['wasteServiceCost'] = basic_metric(
        data, key='wasteServiceCost', theme='ambiente', label='Costo del servizio rifiuti per abitante', short='Costo servizio rifiuti',
        description='Costo totale del servizio di igiene urbana CTOTab pubblicato da ISPRA, espresso per abitante e anno.',
        unit='currency', year='2024', source=raw['wasteServiceCost']['source'], source_url=raw['wasteServiceCost']['sourceUrl'],
        values={town:item['value'] for town,item in raw['wasteServiceCost']['towns'].items()}, polarity='neutral',
        formula='CTOTab ISPRA: costi totali di gestione del servizio di igiene urbana / abitanti.',
        caveat='Il costo del servizio non coincide con la TARI pagata dalla singola famiglia. Sono state accettate solo righe comunali ISPRA con N. comuni = 1.',
        coverage='7/7', search_terms=['ctot','costo rifiuti','igiene urbana','costo servizio rifiuti'])

    economy = data['themes']['economia']
    insert_after(economy['metrics'], 'municipalIrpef', ['municipalTari','municipalImu','fuelPrices'])
    fiscal = next(section for section in economy['sections'] if section.get('key') == 'costi-fiscalita')
    fiscal['label'] = 'Costi e fiscalità locale'
    fiscal['description'] = 'Confronti standardizzati su tributi comunali e alcuni costi osservabili sul territorio.'
    fiscal['metrics'] = ['municipalIrpef','municipalTari','municipalImu','fuelPrices']

    environment = data['themes']['ambiente']
    insert_after(environment['metrics'], 'wastePerResident', ['wasteServiceCost'])
    waste_section = next(section for section in environment['sections'] if section.get('key') == 'rifiuti')
    insert_after(waste_section['metrics'], 'wastePerResident', ['wasteServiceCost'])
    waste_section['description'] = 'Produzione, raccolta differenziata, residuo e costo del servizio di igiene urbana.'

    draft = data.setdefault('costsFiscalDraft', {})
    published = draft.setdefault('publishedInDraft', [])
    for key in ['municipalTari','municipalImu','fuelPrices','wasteServiceCost']:
        if key not in published:
            published.append(key)
    draft['notPublished'] = [key for key in draft.get('notPublished', []) if key not in {'tari','imu','fuelPrices','wasteServiceCost'}]
    draft['note'] = 'IRPEF, TARI, IMU e CTOT sono 7/7; carburanti sono 6/7 con Stazzema n.d. Mensa esclusa per eterogeneità tariffaria.'
    save(DATA_PATH, data)

    registry = load(REGISTRY_PATH)
    external = int(registry.get('expectedExternalMetricCount', 4))
    registry['expectedMetricCount'] = len(data['metrics'])
    registry['expectedInlineMetricCount'] = len(data['metrics']) - external
    overrides = registry.setdefault('metricOverrides', {})
    overrides['municipalTari'] = {'frequency':'annual','frequencyLabel':'Annuale','publisher':'MEF / Comuni / ARERA','expectedRelease':'Dopo l’approvazione delle tariffe comunali'}
    overrides['municipalImu'] = {'frequency':'annual','frequencyLabel':'Annuale','publisher':'Dipartimento delle Finanze — MEF','expectedRelease':'Dopo la pubblicazione dei prospetti comunali'}
    overrides['fuelPrices'] = {'frequency':'daily','frequencyLabel':'Giornaliera','publisher':'MIMIT','expectedRelease':'Aggiornamento open data prezzi praticati'}
    overrides['wasteServiceCost'] = {'profile':'ispra-environment-annual'}
    save(REGISTRY_PATH, registry)
    patch_app()
    print(f"Promossi materializzati: TARI 7/7, IMU 7/7, carburanti 6/7, CTOT 7/7; indicatori totali {len(data['metrics'])}.")


if __name__ == '__main__':
    main()
