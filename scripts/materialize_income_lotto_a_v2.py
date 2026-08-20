#!/usr/bin/env python3
"""Completa la tranche Redditi Lotto A rendendo visibili tutti i candidati promossi.

Aggiunge alla materializzazione v1:
- `incomeSourceProfile`: un solo composito con selettore per fonte di reddito;
- `taxpayersAdultPopulationRate`: contribuenti MEF ogni 100 residenti 18+;
- dettaglio pubblico a 8 fasce MEF dentro `incomeDistribution`;
- registry, monitor e matrice audit coerenti con 132 indicatori complessivi.

La v1 resta il primo stadio di acquisizione. Questa estensione è idempotente:
se i due nuovi indicatori sono già presenti non riesegue la v1, ma riallinea
comunque metadati e controlli.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import materialize_income_lotto_a as base

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
REGISTRY_PATH = ROOT / 'data' / 'source-registry.json'
MONITOR_PATH = ROOT / 'data' / 'source-monitor-state.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
INCOME_SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'mef-income-lotto-a-2024.json'
DEMO_SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'istat-demography-lotto-a-2026-08.json'

MEF_URL = 'https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'
ISTAT_URL = 'https://demo.istat.it/'
SOURCE_METRIC = 'incomeSourceProfile'
TAXPAYER_METRIC = 'taxpayersAdultPopulationRate'

SOURCE_ORDER = [
    ('employment', 'Lavoro dipendente e assimilati'),
    ('pension', 'Pensione'),
    ('selfEmployment', 'Lavoro autonomo'),
    ('entrepreneurOrdinary', 'Impresa · contabilità ordinaria'),
    ('entrepreneurSimplified', 'Impresa · contabilità semplificata'),
    ('participation', 'Partecipazione'),
    ('buildings', 'Fabbricati'),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(site: dict, town: str) -> dict:
    row = next(row for row in site['metrics']['income']['rows'] if row['town'] == town)
    return {'town': town, 'code': row['code'], 'slug': row['slug']}


def formatted_currency(value: float | None) -> str:
    if value is None:
        return 'n.d.'
    return f'{float(value):,.0f}'.replace(',', '.') + ' €'


def formatted_per100(value: float | None) -> str:
    if value is None:
        return 'n.d.'
    return f'{float(value):.1f}'.replace('.', ',') + ' ogni 100'


def adult_population_2026(demography: dict, town: str) -> int:
    detail = demography['posas']['ageSex2026'][town]
    adults = sum(int(row['total']) for row in detail if 18 <= int(row['age']) <= 120)
    if adults <= 0:
        raise RuntimeError(f'{town}: popolazione 18+ non calcolabile')
    return adults


def source_part(detail: dict, key: str, label: str) -> dict:
    raw = next(item for item in detail['incomeSources'] if item['key'] == key)
    frequency = raw.get('frequency')
    amount = raw.get('amountEuro')
    value = None
    if frequency not in (None, 0) and amount is not None:
        value = amount / frequency
    return {
        'label': label,
        'selectorLabel': label,
        'value': value,
        'unit': 'currency',
        'count': frequency,
        'amountEuro': amount,
    }


def income_source_metric(site: dict, snapshot: dict) -> dict:
    order = [row['town'] for row in site['metrics']['income']['rows']]
    rows = []
    aggregates = {key: {'frequency': 0, 'amount': 0, 'complete': True} for key, _label in SOURCE_ORDER}

    for town in order:
        detail = snapshot['towns'][town]
        parts = []
        for key, label in SOURCE_ORDER:
            part = source_part(detail, key, label)
            parts.append(part)
            if part['count'] is None or part['amountEuro'] is None:
                aggregates[key]['complete'] = False
            else:
                aggregates[key]['frequency'] += int(part['count'])
                aggregates[key]['amount'] += int(part['amountEuro'])
        primary = parts[0]['value']
        rows.append({
            **identity(site, town),
            'value': primary,
            'formatted': formatted_currency(primary),
            'series': None,
            'normalized': None,
            'benchmarkValue': primary,
            'parts': parts,
        })

    aggregate_parts = []
    for key, label in SOURCE_ORDER:
        state = aggregates[key]
        value = None
        count = None
        amount = None
        if state['complete'] and state['frequency'] > 0:
            count = state['frequency']
            amount = state['amount']
            value = amount / count
        aggregate_parts.append({
            'label': label,
            'selectorLabel': label,
            'value': value,
            'unit': 'currency',
            'count': count,
            'amountEuro': amount,
        })

    return {
        'meta': {
            'key': SOURCE_METRIC,
            'theme': 'economia',
            'label': 'Reddito medio dichiarato per fonte',
            'shortLabel': 'Reddito per fonte',
            'description': (
                'Importo medio dichiarato per ciascuna fonte di reddito, calcolato dividendo l’ammontare MEF '
                'per il numero di contribuenti che dichiarano quella specifica fonte. Il selettore consente di '
                'confrontare lavoro dipendente, pensione, autonomo, impresa, partecipazione e fabbricati.'
            ),
            'unit': 'currency',
            'year': '2024',
            'source': 'Dipartimento delle Finanze — MEF',
            'polarity': 'neutral',
            'compositeType': 'securityMeasures',
            'selectorLabel': 'Fonte di reddito',
            'searchTerms': [
                'fonti reddito', 'reddito dipendente', 'reddito pensione', 'reddito autonomo',
                'reddito impresa', 'reddito partecipazione', 'reddito fabbricati',
            ],
        },
        'sourceUrl': MEF_URL,
        'rows': rows,
        'aggregate': {
            'value': aggregate_parts[0]['value'],
            'label': 'Versilia · reddito medio da lavoro dipendente',
            'note': (
                'Per ogni fonte il valore Versilia è ammontare complessivo / frequenza complessiva dei sette Comuni. '
                'Se una cella comunale MEF non è valorizzata, l’aggregato di quella fonte resta n.d. invece di imputare zero.'
            ),
            'parts': aggregate_parts,
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati ufficiali MEF',
            'formula': 'per ciascuna fonte: ammontare del reddito / frequenza dei contribuenti che dichiarano quella fonte',
            'caveat': (
                'Le frequenze delle diverse fonti non sono persone uniche e non vanno sommate: lo stesso contribuente '
                'può dichiarare più fonti. Le celle MEF non valorizzate restano n.d.; non vengono trasformate in zero.'
            ),
            'coverage': '7/7 righe comunali; singole componenti possono essere n.d. quando il MEF non valorizza la cella',
        },
    }


def taxpayers_metric(site: dict, snapshot: dict, demography: dict) -> dict:
    order = [row['town'] for row in site['metrics']['income']['rows']]
    rows = []
    total_taxpayers = 0
    total_adults = 0

    for town in order:
        taxpayers = snapshot['towns'][town].get('taxpayers')
        adults = adult_population_2026(demography, town)
        if taxpayers is None:
            raise RuntimeError(f'{town}: numero contribuenti MEF mancante')
        value = taxpayers / adults * 100
        total_taxpayers += int(taxpayers)
        total_adults += adults
        snapshot['towns'][town]['adultPopulation2026'] = adults
        snapshot['towns'][town]['taxpayersPer100AdultResidents'] = value
        rows.append({
            **identity(site, town),
            'value': value,
            'formatted': formatted_per100(value),
            'series': None,
            'normalized': None,
            'benchmarkValue': value,
            'taxpayers': int(taxpayers),
            'adultPopulation2026': adults,
        })

    aggregate = total_taxpayers / total_adults * 100
    return {
        'meta': {
            'key': TAXPAYER_METRIC,
            'theme': 'economia',
            'label': 'Contribuenti ogni 100 maggiorenni',
            'shortLabel': 'Contribuenti / maggiorenni',
            'description': (
                'Rapporto tra il numero di contribuenti registrati dal MEF e i residenti di 18 anni e più. '
                'Il denominatore usa la popolazione Istat per singola età al 1° gennaio 2026.'
            ),
            'unit': 'per100',
            'year': 'MEF a.i. 2024 · residenti 1.1.2026',
            'source': 'Dipartimento delle Finanze — MEF / Istat',
            'polarity': 'neutral',
            'searchTerms': [
                'contribuenti', 'maggiorenni', 'adulti', 'dichiaranti', 'ogni 100 residenti', 'irpef',
            ],
        },
        'sourceUrl': MEF_URL,
        'rows': rows,
        'aggregate': {
            'value': aggregate,
            'label': 'Versilia · contribuenti ogni 100 maggiorenni',
            'note': (
                'Rapporto tra la somma dei contribuenti MEF e la popolazione residente 18+ complessiva dei sette Comuni.'
            ),
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati ufficiali MEF e Istat',
            'formula': 'numero contribuenti MEF / residenti di 18 anni e più al 1° gennaio 2026 × 100',
            'caveat': (
                'Non è la percentuale degli adulti che paga l’IRPEF. Il numeratore MEF è il numero complessivo di '
                'contribuenti e può includere anche contribuenti minorenni; il denominatore è invece limitato ai residenti 18+.'
            ),
            'coverage': '7/7',
            'additionalSource': ISTAT_URL,
        },
    }


def add_distribution_detail(site: dict, snapshot: dict) -> None:
    metric = site['metrics']['incomeDistribution']
    rows = {row['town']: row for row in metric['rows']}
    for town, detail in snapshot['towns'].items():
        total = detail['totalIncome']['frequency']
        if not total:
            raise RuntimeError(f'{town}: frequenza reddito complessivo mancante')
        parts = []
        for band in detail['incomeBands']:
            count = band.get('frequency')
            value = None if count is None else count / total * 100
            parts.append({
                'key': band['key'],
                'label': band['label'],
                'value': value,
                'unit': 'percent',
                'count': count,
                'amountEuro': band.get('amountEuro'),
            })
        rows[town]['detailParts'] = parts
        rows[town]['detailCoverage'] = detail['bandCoverage']

    metric['meta']['detailLabel'] = 'Dettaglio · 8 fasce MEF'
    metric['meta']['description'] = (
        'Distribuzione dei dichiaranti in quattro gruppi di sintesi ricavati dalle classi ufficiali MEF. '
        'Il dettaglio espandibile mostra separatamente le otto fasce originali e mantiene n.d. le celle non valorizzate dalla fonte.'
    )
    metric.setdefault('method', {})['detailCaveat'] = (
        'Nel dettaglio a otto fasce ogni quota usa come denominatore la frequenza complessiva del reddito complessivo. '
        'Le celle MEF vuote restano n.d.; per questo, nei Comuni interessati, le sole quote note possono sommare a meno del 100%.'
    )


def insert_metrics(site: dict, source_metric: dict, taxpayer_metric: dict) -> None:
    metrics = site['metrics']
    out = OrderedDict()
    for key, metric in metrics.items():
        out[key] = metric
        if key == 'incomeDistribution':
            out[SOURCE_METRIC] = source_metric
        if key == 'pensionIncomeShare':
            out[TAXPAYER_METRIC] = taxpayer_metric
    site['metrics'] = out

    theme = site['themes']['economia']
    desired = [
        'income',
        'incomeDistribution',
        SOURCE_METRIC,
        'pensionIncomeShare',
        TAXPAYER_METRIC,
        'incomeVsInflation',
    ]
    section = next(item for item in theme['sections'] if item['key'] == 'redditi')
    section['metrics'] = desired
    section['description'] = (
        'Reddito imponibile, distribuzione per fascia, fonti di reddito, peso delle pensioni, '
        'rapporto tra contribuenti e residenti maggiorenni e confronto con l’inflazione.'
    )

    current = [key for key in theme['metrics'] if key not in {SOURCE_METRIC, TAXPAYER_METRIC}]
    anchor = current.index('incomeDistribution') + 1
    current.insert(anchor, SOURCE_METRIC)
    pension_index = current.index('pensionIncomeShare') + 1
    current.insert(pension_index, TAXPAYER_METRIC)
    theme['metrics'] = current


def update_registry(registry: dict) -> None:
    registry['expectedMetricCount'] = 132
    registry['expectedInlineMetricCount'] = 128
    registry['expectedExternalMetricCount'] = 4
    overrides = registry.setdefault('metricOverrides', {})
    overrides[SOURCE_METRIC] = {'profile': 'mef-irpef-annual'}
    overrides[TAXPAYER_METRIC] = {'profile': 'mef-irpef-annual'}


def add_monitor_metric(monitor: dict, url: str, key: str) -> None:
    source = monitor.get('sources', {}).get(url)
    if not source:
        raise RuntimeError(f'Fonte monitor non trovata: {url}')
    metrics = source.setdefault('metrics', [])
    if key not in metrics:
        metrics.append(key)
        metrics.sort()


def update_audit(audit: dict) -> None:
    audit['status'] = 'implementation_income_complete_draft'
    audit['catalogMetricCountCurrentDraft'] = 132
    for candidate in audit.get('candidates', []):
        if candidate.get('key') == 'taxpayersAdultPopulationRate':
            candidate['implementationStatus'] = 'draft_materialized'
            candidate['denominatorDefinition'] = 'residenti di 18 anni e più al 1° gennaio 2026 (Istat POSAS)'
            candidate['formula'] = 'Numero contribuenti MEF / popolazione residente 18+ × 100'
        if candidate.get('key') == 'incomeSourceAndBandsDetail':
            candidate['implementationStatus'] = 'visible_composite_and_8_band_detail'
            candidate['visibleOutputs'] = [SOURCE_METRIC, 'incomeDistribution.detailParts']
            candidate['snapshot'] = 'data/source-snapshots/mef-income-lotto-a-2024.json'
        if candidate.get('key') == 'pensionIncomeShare':
            candidate['implementationStatus'] = 'draft_materialized'


def main() -> None:
    initial = load(SITE_PATH)
    if not {SOURCE_METRIC, TAXPAYER_METRIC}.issubset(initial.get('metrics', {})):
        base.main()

    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    audit = load(AUDIT_PATH)
    snapshot = load(INCOME_SNAPSHOT_PATH)
    demography = load(DEMO_SNAPSHOT_PATH)

    # Se una precedente esecuzione aveva già inserito i due indicatori, li rimuove
    # prima di ricostruirli per mantenere l'ordine deterministico.
    site['metrics'].pop(SOURCE_METRIC, None)
    site['metrics'].pop(TAXPAYER_METRIC, None)

    add_distribution_detail(site, snapshot)
    source_metric = income_source_metric(site, snapshot)
    taxpayer_metric = taxpayers_metric(site, snapshot, demography)
    insert_metrics(site, source_metric, taxpayer_metric)

    snapshot.setdefault('method', {})['taxpayersPer100AdultResidents'] = (
        'numero contribuenti MEF / residenti di 18 anni e più al 1° gennaio 2026 × 100'
    )
    snapshot['demographySource'] = {
        'publisher': 'Istat',
        'snapshot': 'data/source-snapshots/istat-demography-lotto-a-2026-08.json',
        'reference': 'popolazione per singola età al 1° gennaio 2026',
        'url': ISTAT_URL,
    }

    site['version'] = 'v1.15.0'
    site['updated'] = '20 agosto 2026'
    update_registry(registry)
    add_monitor_metric(monitor, MEF_URL, SOURCE_METRIC)
    add_monitor_metric(monitor, MEF_URL, TAXPAYER_METRIC)
    add_monitor_metric(monitor, ISTAT_URL, TAXPAYER_METRIC)
    update_audit(audit)

    external = [
        metric for metric in site['metrics'].values()
        if metric.get('dataStorage', {}).get('type') == 'external-climate'
    ]
    if len(site['metrics']) != 132 or len(external) != 4:
        raise RuntimeError(f'Conteggio inatteso: {len(site["metrics"])} totali, {len(external)} esterni')

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    save(AUDIT_PATH, audit)
    save(INCOME_SNAPSHOT_PATH, snapshot)
    print('Lotto A Redditi v2: 132 indicatori = 128 inline + 4 climatici; tutti e quattro i candidati approvati sono consultabili.')


if __name__ == '__main__':
    main()
