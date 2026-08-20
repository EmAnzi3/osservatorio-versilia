#!/usr/bin/env python3
"""Materializza il primo blocco del Lotto A Demografia da fonti Istat ufficiali.

La trasformazione:
- scarica P02 Lucca 2019-2025 e POSAS Lucca 2019-2026;
- conserva uno snapshot versionato e riproducibile;
- aggiunge solo due nuovi indicatori canonici (dinamica naturale e dipendenza);
- NON duplica la quota 80+, già presente in ageDistribution;
- riusa il tipo composito multi-misura già supportato dal sito.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import urllib.request
import zipfile
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
REGISTRY_PATH = ROOT / 'data' / 'source-registry.json'
MONITOR_PATH = ROOT / 'data' / 'source-monitor-state.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'istat-demography-lotto-a-2026-08.json'

TOWNS = {
    '046005': 'Camaiore',
    '046013': 'Forte dei Marmi',
    '046018': 'Massarosa',
    '046024': 'Pietrasanta',
    '046028': 'Seravezza',
    '046030': 'Stazzema',
    '046033': 'Viareggio',
}
P2_YEARS = list(range(2019, 2026))
POSAS_YEARS = list(range(2019, 2027))
DEMO_ROOT = 'https://demo.istat.it/'


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-materializer/1.0'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def read_csv_from_zip(url: str) -> tuple[list[str], list[list[str]], str]:
    body = download(url)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(('.csv', '.txt'))]
        if len(names) != 1:
            raise RuntimeError(f'Archivio inatteso {url}: {names}')
        name = names[0]
        raw = archive.read(name).decode('utf-8-sig', errors='strict')
    rows = list(csv.reader(io.StringIO(raw), delimiter=';'))
    if len(rows) < 3:
        raise RuntimeError(f'CSV troppo corto: {url}')
    title = rows[0][0].strip()
    header = [cell.strip() for cell in rows[1]]
    return header, rows[2:], title


def records_by_code(url: str) -> tuple[dict[str, dict[str, str]], str]:
    header, rows, title = read_csv_from_zip(url)
    result = {}
    for row in rows:
        if not row:
            continue
        padded = row + [''] * max(0, len(header) - len(row))
        rec = dict(zip(header, padded, strict=False))
        code = rec.get('Codice comune', '').strip()
        if code in TOWNS:
            result[code] = rec
    if set(result) != set(TOWNS):
        raise RuntimeError(f'Copertura non 7/7 per {url}: {sorted(result)}')
    return result, title


def posas_by_code_age(url: str) -> tuple[dict[str, list[dict[str, str]]], str]:
    header, rows, title = read_csv_from_zip(url)
    result = {code: [] for code in TOWNS}
    for row in rows:
        if not row:
            continue
        padded = row + [''] * max(0, len(header) - len(row))
        rec = dict(zip(header, padded, strict=False))
        code = rec.get('Codice comune', '').strip()
        if code in result:
            result[code].append(rec)
    if any(not rows for rows in result.values()):
        raise RuntimeError(f'Copertura POSAS non 7/7 per {url}')
    return result, title


def num(value: str | int | float) -> float:
    text = str(value).strip().replace('.', '').replace(',', '.')
    if not text:
        return 0.0
    return float(text)


def age_number(value: str) -> int:
    match = re.search(r'\d+', str(value))
    if not match:
        raise ValueError(f'Età non riconosciuta: {value!r}')
    return int(match.group())


def round_clean(value: float, digits: int = 10) -> float:
    return round(float(value), digits)


def format_rate(value: float) -> str:
    return f'{value:.1f}'.replace('.', ',') + ' ogni 1.000'


def format_index(value: float) -> str:
    return f'{value:.1f}'.replace('.', ',')


def slug_for(site: dict, town: str) -> str:
    row = next(r for r in site['metrics']['population']['rows'] if r['town'] == town)
    return row['slug']


def code_for(site: dict, town: str) -> str:
    row = next(r for r in site['metrics']['population']['rows'] if r['town'] == town)
    return row['code']


def p2_snapshot() -> dict:
    out = {TOWNS[code]: [] for code in TOWNS}
    sources = []
    for year in P2_YEARS:
        url = f'https://demo.istat.it/data/p2/P2_{year}_it_046_Lucca.zip'
        records, title = records_by_code(url)
        sources.append({'year': year, 'url': url, 'title': title})
        for code, town in TOWNS.items():
            r = records[code]
            jan1 = int(num(r['Popolazione censita al 1° gennaio - Totale']))
            dec31 = int(num(r['Popolazione al 31 dicembre - Totale']))
            births = int(num(r['Nati vivi - Totale']))
            deaths = int(num(r['Morti - Totale']))
            natural = int(num(r['Saldo naturale - Totale']))
            information = r.get('Informazioni', '').strip()
            mean_population = (jan1 + dec31) / 2
            out[town].append({
                'year': year,
                'populationJan1': jan1,
                'populationDec31': dec31,
                'meanPopulation': mean_population,
                'births': births,
                'deaths': deaths,
                'naturalBalance': natural,
                'birthRatePer1000': round_clean(births / mean_population * 1000),
                'deathRatePer1000': round_clean(deaths / mean_population * 1000),
                'naturalBalanceRatePer1000': round_clean(natural / mean_population * 1000),
                'informationFlag': information,
            })
    return {'sources': sources, 'towns': out}


def age_bands(records: list[dict[str, str]]) -> dict:
    counts = {'0-14': 0, '15-64': 0, '65+': 0, '80+': 0}
    total = 0
    by_age_sex = []
    for r in records:
        age = age_number(r['Età'])
        men = int(num(r['Totale maschi']))
        women = int(num(r['Totale femmine']))
        value = int(num(r['Totale']))
        if men + women != value:
            raise RuntimeError(f'Totale età incoerente: {r}')
        total += value
        if age <= 14:
            counts['0-14'] += value
        elif age <= 64:
            counts['15-64'] += value
        else:
            counts['65+'] += value
        if age >= 80:
            counts['80+'] += value
        by_age_sex.append({'age': age, 'men': men, 'women': women, 'total': value})
    if sum(counts[k] for k in ('0-14', '15-64', '65+')) != total:
        raise RuntimeError('Classi di età non esaustive')
    return {'total': total, 'counts': counts, 'ageSex': by_age_sex}


def posas_snapshot() -> dict:
    out = {TOWNS[code]: [] for code in TOWNS}
    latest_detail = {}
    sources = []
    for year in POSAS_YEARS:
        url = f'https://demo.istat.it/data/posas/POSAS_{year}_it_046_Lucca.zip'
        records, title = posas_by_code_age(url)
        sources.append({'year': year, 'url': url, 'title': title})
        for code, town in TOWNS.items():
            b = age_bands(records[code])
            c = b['counts']
            working = c['15-64']
            structural = (c['0-14'] + c['65+']) / working * 100
            elderly = c['65+'] / working * 100
            out[town].append({
                'year': year,
                'population': b['total'],
                'age0to14': c['0-14'],
                'age15to64': c['15-64'],
                'age65plus': c['65+'],
                'age80plus': c['80+'],
                'share80plus': round_clean(c['80+'] / b['total'] * 100),
                'structuralDependencyIndex': round_clean(structural),
                'oldAgeDependencyIndex': round_clean(elderly),
            })
            if year == POSAS_YEARS[-1]:
                latest_detail[town] = b['ageSex']
    return {'sources': sources, 'towns': out, 'ageSex2026': latest_detail}


def row_meta(site: dict, town: str) -> dict:
    return {'town': town, 'code': code_for(site, town), 'slug': slug_for(site, town)}


def natural_metric(site: dict, p2: dict) -> dict:
    order = [r['town'] for r in site['metrics']['population']['rows']]
    rows = []
    agg_latest = {'births': 0, 'deaths': 0, 'natural': 0, 'meanPopulation': 0.0}
    for town in order:
        series = p2['towns'][town]
        years = [x['year'] for x in series]
        balance = [x['naturalBalanceRatePer1000'] for x in series]
        births = [x['birthRatePer1000'] for x in series]
        deaths = [x['deathRatePer1000'] for x in series]
        latest = series[-1]
        agg_latest['births'] += latest['births']
        agg_latest['deaths'] += latest['deaths']
        agg_latest['natural'] += latest['naturalBalance']
        agg_latest['meanPopulation'] += latest['meanPopulation']
        parts = [
            {'label': 'Saldo naturale', 'selectorLabel': 'Saldo naturale', 'value': latest['naturalBalanceRatePer1000'], 'count': latest['naturalBalance'], 'unit': 'per1000'},
            {'label': 'Natalità', 'selectorLabel': 'Natalità', 'value': latest['birthRatePer1000'], 'count': latest['births'], 'unit': 'per1000'},
            {'label': 'Mortalità', 'selectorLabel': 'Mortalità', 'value': latest['deathRatePer1000'], 'count': latest['deaths'], 'unit': 'per1000'},
        ]
        rows.append({
            **row_meta(site, town),
            'value': balance[-1],
            'formatted': format_rate(balance[-1]),
            'series': {'years': years, 'values': balance},
            'normalized': None,
            'benchmarkValue': balance[-1],
            'parts': parts,
            'componentSeries': {
                'Saldo naturale': {'years': years, 'values': balance},
                'Natalità': {'years': years, 'values': births},
                'Mortalità': {'years': years, 'values': deaths},
            },
        })
    pop = agg_latest['meanPopulation']
    agg_parts = [
        {'label': 'Saldo naturale', 'selectorLabel': 'Saldo naturale', 'value': agg_latest['natural'] / pop * 1000, 'count': agg_latest['natural'], 'unit': 'per1000'},
        {'label': 'Natalità', 'selectorLabel': 'Natalità', 'value': agg_latest['births'] / pop * 1000, 'count': agg_latest['births'], 'unit': 'per1000'},
        {'label': 'Mortalità', 'selectorLabel': 'Mortalità', 'value': agg_latest['deaths'] / pop * 1000, 'count': agg_latest['deaths'], 'unit': 'per1000'},
    ]
    return {
        'meta': {
            'key': 'naturalDemographicDynamics',
            'theme': 'demografia',
            'label': 'Dinamica naturale della popolazione',
            'shortLabel': 'Dinamica naturale',
            'description': 'Nascite, decessi e saldo naturale rapportati alla popolazione media annua. Il 2025 è un dato Istat provvisorio.',
            'unit': 'per1000',
            'year': '2025',
            'source': 'Istat — bilancio demografico comunale (P02)',
            'polarity': 'neutral',
            'compositeType': 'securityMeasures',
            'selectorLabel': 'Voce',
            'searchTerms': ['nascite', 'decessi', 'saldo naturale', 'natalità', 'mortalità'],
        },
        'sourceUrl': DEMO_ROOT,
        'rows': rows,
        'aggregate': {
            'value': agg_parts[0]['value'],
            'label': 'Versilia · saldo naturale',
            'note': 'Tasso calcolato sommando gli eventi dei sette Comuni e rapportandoli alla popolazione media annua complessiva.',
            'parts': agg_parts,
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati Istat',
            'formula': 'tasso = eventi dell’anno / media tra popolazione al 1° gennaio e popolazione al 31 dicembre × 1.000; saldo naturale = nati vivi − morti',
            'caveat': 'Il bilancio 2025 è provvisorio (flag Istat “p”) e verrà sostituito dal dato definitivo quando pubblicato. Le annualità precedenti restano quelle diffuse negli archivi P02.',
            'coverage': '7/7',
        },
    }


def dependency_metric(site: dict, posas: dict) -> dict:
    order = [r['town'] for r in site['metrics']['population']['rows']]
    rows = []
    latest_totals = {'young': 0, 'working': 0, 'elderly': 0}
    for town in order:
        series = posas['towns'][town]
        years = [x['year'] for x in series]
        structural = [x['structuralDependencyIndex'] for x in series]
        elderly = [x['oldAgeDependencyIndex'] for x in series]
        latest = series[-1]
        latest_totals['young'] += latest['age0to14']
        latest_totals['working'] += latest['age15to64']
        latest_totals['elderly'] += latest['age65plus']
        parts = [
            {'label': 'Indice di dipendenza strutturale', 'selectorLabel': 'Strutturale', 'value': structural[-1], 'unit': 'index'},
            {'label': 'Indice di dipendenza degli anziani', 'selectorLabel': 'Anziani', 'value': elderly[-1], 'unit': 'index'},
        ]
        rows.append({
            **row_meta(site, town),
            'value': structural[-1],
            'formatted': format_index(structural[-1]),
            'series': {'years': years, 'values': structural},
            'normalized': None,
            'benchmarkValue': structural[-1],
            'parts': parts,
            'componentSeries': {
                'Strutturale': {'years': years, 'values': structural},
                'Anziani': {'years': years, 'values': elderly},
            },
        })
    working = latest_totals['working']
    structural_agg = (latest_totals['young'] + latest_totals['elderly']) / working * 100
    elderly_agg = latest_totals['elderly'] / working * 100
    agg_parts = [
        {'label': 'Indice di dipendenza strutturale', 'selectorLabel': 'Strutturale', 'value': structural_agg, 'unit': 'index'},
        {'label': 'Indice di dipendenza degli anziani', 'selectorLabel': 'Anziani', 'value': elderly_agg, 'unit': 'index'},
    ]
    return {
        'meta': {
            'key': 'dependencyIndices',
            'theme': 'demografia',
            'label': 'Indici di dipendenza demografica',
            'shortLabel': 'Indici di dipendenza',
            'description': 'Rapporto tra popolazione nelle età non attive e popolazione 15–64 anni, con lettura separata del peso della componente anziana.',
            'unit': 'index',
            'year': '2026',
            'source': 'Istat — popolazione residente per età e sesso (POSAS)',
            'polarity': 'neutral',
            'compositeType': 'securityMeasures',
            'selectorLabel': 'Indice',
            'searchTerms': ['dipendenza demografica', 'dipendenza anziani', 'età non attive', '65+', '0-14'],
        },
        'sourceUrl': DEMO_ROOT,
        'rows': rows,
        'aggregate': {
            'value': structural_agg,
            'label': 'Versilia · dipendenza strutturale',
            'note': 'Rapporto calcolato sulla somma delle popolazioni per classe di età dei sette Comuni.',
            'parts': agg_parts,
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati Istat',
            'formula': 'dipendenza strutturale = (0–14 + 65+) / 15–64 × 100; dipendenza anziani = 65+ / 15–64 × 100',
            'caveat': 'La popolazione al 1° gennaio 2026 è una stima Istat coerente con il bilancio demografico provvisorio 2025. L’indice non misura direttamente il carico economico effettivo sulle persone occupate.',
            'coverage': '7/7',
        },
    }


def update_theme(site: dict) -> None:
    theme = site['themes']['demografia']
    metrics = theme['metrics']
    if 'dependencyIndices' not in metrics:
        metrics.insert(metrics.index('oldAgeIndex') + 1, 'dependencyIndices')
    if 'naturalDemographicDynamics' not in metrics:
        metrics.insert(metrics.index('populationChange'), 'naturalDemographicDynamics')
    for section in theme['sections']:
        if section['key'] == 'quadro':
            if 'dependencyIndices' not in section['metrics']:
                section['metrics'].insert(section['metrics'].index('oldAgeIndex') + 1, 'dependencyIndices')
            section['description'] = 'Quanti siamo, come si distribuisce la popolazione per età e cittadinanza e quale rapporto esiste tra fasce dipendenti e popolazione 15–64 anni.'
        if section['key'] == 'dinamica':
            section['metrics'] = ['naturalDemographicDynamics', 'populationChange']
            section['description'] = 'Nascite, decessi, saldo naturale e variazione complessiva dei residenti.'


def insert_metrics(site: dict, generated: dict[str, dict]) -> None:
    if all(key in site['metrics'] for key in generated):
        for key, metric in generated.items():
            site['metrics'][key] = metric
        return
    out = OrderedDict()
    for key, metric in site['metrics'].items():
        out[key] = metric
        if key == 'oldAgeIndex':
            out['dependencyIndices'] = generated['dependencyIndices']
        if key == 'totalResidentialMobility':
            out['naturalDemographicDynamics'] = generated['naturalDemographicDynamics']
    site['metrics'] = out


def update_registry(registry: dict) -> None:
    registry['expectedMetricCount'] = 129
    registry['expectedInlineMetricCount'] = 125
    registry['expectedExternalMetricCount'] = 4
    registry.setdefault('sourceProfileByUrl', {})[DEMO_ROOT] = 'istat-demography-annual'


def update_monitor(monitor: dict) -> None:
    source = monitor.get('sources', {}).get(DEMO_ROOT)
    if not source:
        return
    metrics = source.setdefault('metrics', [])
    for key in ('naturalDemographicDynamics', 'dependencyIndices'):
        if key not in metrics:
            metrics.append(key)
    metrics.sort()


def update_audit(audit: dict) -> None:
    audit['status'] = 'implementation_demography_draft'
    audit['catalogMetricCountCurrentDraft'] = 129
    decisions = {
        'naturalDemographicDynamics': 'draft_materialized',
        'dependencyIndices': 'draft_materialized',
        'share80Plus': 'covered_by_existing_ageDistribution',
        'populationAgeSexDetail': 'snapshot_materialized_2026',
    }
    for candidate in audit['candidates']:
        if candidate['key'] in decisions:
            candidate['implementationStatus'] = decisions[candidate['key']]


def main() -> None:
    site = json.loads(SITE_PATH.read_text(encoding='utf-8'))
    registry = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    monitor = json.loads(MONITOR_PATH.read_text(encoding='utf-8'))
    audit = json.loads(AUDIT_PATH.read_text(encoding='utf-8'))

    p2 = p2_snapshot()
    posas = posas_snapshot()
    snapshot = {
        'schemaVersion': 1,
        'generatedAt': '2026-08-20',
        'publisher': 'Istat',
        'territory': 'Provincia di Lucca · sette Comuni dell’Osservatorio Versilia',
        'status': {
            'p02_2025': 'provvisorio secondo flag Istat p',
            'posas_2026': 'stima al 1° gennaio 2026',
        },
        'p02': p2,
        'posas': posas,
        'formulas': {
            'birthRatePer1000': 'nati vivi / popolazione media annua × 1.000',
            'deathRatePer1000': 'morti / popolazione media annua × 1.000',
            'naturalBalanceRatePer1000': '(nati vivi − morti) / popolazione media annua × 1.000',
            'structuralDependencyIndex': '(0–14 + 65+) / 15–64 × 100',
            'oldAgeDependencyIndex': '65+ / 15–64 × 100',
        },
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    generated = {
        'dependencyIndices': dependency_metric(site, posas),
        'naturalDemographicDynamics': natural_metric(site, p2),
    }
    update_theme(site)
    insert_metrics(site, generated)
    site['version'] = 'v1.14.0'
    site['updated'] = '20 agosto 2026'
    update_registry(registry)
    update_monitor(monitor)
    update_audit(audit)

    external = [m for m in site['metrics'].values() if m.get('dataStorage', {}).get('type') == 'external-climate']
    if len(site['metrics']) != 129 or len(external) != 4:
        raise RuntimeError(f'Conteggio inatteso: {len(site["metrics"])} totali, {len(external)} esterni')
    for key in generated:
        metric = site['metrics'][key]
        if len(metric['rows']) != 7:
            raise RuntimeError(f'{key}: copertura non 7/7')
        if metric['meta'].get('compositeType') != 'securityMeasures':
            raise RuntimeError(f'{key}: deve riusare il composito multi-misura canonico')

    SITE_PATH.write_text(json.dumps(site, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    MONITOR_PATH.write_text(json.dumps(monitor, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Demografia Lotto A materializzata: 129 indicatori = 125 inline + 4 climatici esterni.')


if __name__ == '__main__':
    main()
