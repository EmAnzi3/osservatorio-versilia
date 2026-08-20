#!/usr/bin/env python3
"""Materializza il primo stadio Redditi / fiscalità del Lotto A da fonte MEF.

Il primo stadio acquisisce e conserva il dataset comunale 2024 e materializza
`pensionIncomeShare`. La materializzazione completa è eseguita da
`materialize_income_lotto_a_v2.py`, che rende consultabili anche reddito per
fonte, dettaglio a 8 fasce e contribuenti ogni 100 maggiorenni.
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

import probe_mef_income_lotto_a as probe

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
REGISTRY_PATH = ROOT / 'data' / 'source-registry.json'
MONITOR_PATH = ROOT / 'data' / 'source-monitor-state.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'mef-income-lotto-a-2024.json'
HISTORY_TEST_PATH = ROOT / 'scripts' / 'test_history_v180.py'

SOURCE_URL = 'https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'
METRIC_KEY = 'pensionIncomeShare'
EXPECTED_TOWNS = [
    'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta',
    'Seravezza', 'Stazzema', 'Viareggio',
]

PENSION_FREQ = 'Reddito da pensione - Frequenza'
PENSION_AMOUNT = 'Reddito da pensione - Ammontare in euro'
TOTAL_FREQ = 'Reddito complessivo - Frequenza'
TOTAL_AMOUNT = 'Reddito complessivo - Ammontare in euro'
TAXPAYERS = 'Numero contribuenti'

SOURCE_DEFINITIONS = [
    ('buildings', 'Reddito da fabbricati', 'Reddito da fabbricati'),
    ('employment', 'Lavoro dipendente e assimilati', 'Reddito da lavoro dipendente e assimilati'),
    ('pension', 'Pensione', 'Reddito da pensione'),
    ('selfEmployment', 'Lavoro autonomo', 'Reddito da lavoro autonomo (comprensivo dei valori nulli)'),
    ('entrepreneurOrdinary', 'Impresa · contabilità ordinaria', "Reddito di spettanza dell'imprenditore in contabilita' ordinaria  (comprensivo dei valori nulli)"),
    ('entrepreneurSimplified', 'Impresa · contabilità semplificata', "Reddito di spettanza dell'imprenditore in contabilita' semplificata (comprensivo dei valori nulli)"),
    ('participation', 'Partecipazione', 'Reddito da partecipazione  (comprensivo dei valori nulli)'),
]

BAND_DEFINITIONS = [
    ('le0', 'Fino a 0 €', 'Reddito complessivo minore o uguale a zero euro'),
    ('0to10k', '0–10.000 €', 'Reddito complessivo da 0 a 10000 euro'),
    ('10to15k', '10.000–15.000 €', 'Reddito complessivo da 10000 a 15000 euro'),
    ('15to26k', '15.000–26.000 €', 'Reddito complessivo da 15000 a 26000 euro'),
    ('26to55k', '26.000–55.000 €', 'Reddito complessivo da 26000 a 55000 euro'),
    ('55to75k', '55.000–75.000 €', 'Reddito complessivo da 55000 a 75000 euro'),
    ('75to120k', '75.000–120.000 €', 'Reddito complessivo da 75000 a 120000 euro'),
    ('over120k', 'Oltre 120.000 €', 'Reddito complessivo oltre 120000 euro'),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def parse_integer(value: object) -> int | None:
    text = str(value or '').strip()
    if not text:
        return None
    cleaned = re.sub(r'[^0-9-]', '', text)
    if not cleaned or cleaned == '-':
        return None
    return int(cleaned)


def percent(value: float) -> str:
    return f'{float(value):.1f}'.replace('.', ',') + '%'


def identity(site: dict, town: str) -> dict:
    row = next(row for row in site['metrics']['income']['rows'] if row['town'] == town)
    return {'town': town, 'code': row['code'], 'slug': row['slug']}


def load_source() -> tuple[list[str], list[dict[str, str]], dict[str, dict[str, str]], dict]:
    body = probe.download(probe.SOURCE_ZIP)
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if not candidates:
            raise RuntimeError('Archivio MEF senza CSV/TXT')
        member = max(candidates, key=lambda name: archive.getinfo(name).file_size)
        headers, rows, parsing = probe.parse_csv(archive.read(member))
    name_header = probe.find_name_header(headers, rows)
    towns = probe.select_towns(rows, name_header)
    return headers, rows, towns, {**parsing, 'nameHeader': name_header, 'archiveMember': member}


def raw_pair(row: dict[str, str], prefix: str) -> dict:
    return {
        'frequency': parse_integer(row.get(f'{prefix} - Frequenza')),
        'amountEuro': parse_integer(row.get(f'{prefix} - Ammontare in euro')),
    }


def build_snapshot(site: dict, headers: list[str], towns: dict[str, dict[str, str]], parsing: dict) -> dict:
    result = {}
    for town in EXPECTED_TOWNS:
        raw = towns[town]
        pension_amount = parse_integer(raw.get(PENSION_AMOUNT))
        total_amount = parse_integer(raw.get(TOTAL_AMOUNT))
        share = None if pension_amount is None or total_amount in (None, 0) else pension_amount / total_amount * 100

        sources = []
        for key, label, prefix in SOURCE_DEFINITIONS:
            pair = raw_pair(raw, prefix)
            sources.append({'key': key, 'label': label, **pair})

        bands = []
        available_frequency_total = 0
        missing_band_cells = 0
        for key, label, prefix in BAND_DEFINITIONS:
            pair = raw_pair(raw, prefix)
            if pair['frequency'] is None:
                missing_band_cells += 1
            else:
                available_frequency_total += pair['frequency']
            bands.append({'key': key, 'label': label, **pair})

        total_frequency = parse_integer(raw.get(TOTAL_FREQ))
        result[town] = {
            **identity(site, town),
            'taxpayers': parse_integer(raw.get(TAXPAYERS)),
            'totalIncome': {'frequency': total_frequency, 'amountEuro': total_amount},
            'pensionIncome': {
                'frequency': parse_integer(raw.get(PENSION_FREQ)),
                'amountEuro': pension_amount,
                'shareOfTotalIncomePercent': share,
            },
            'incomeSources': sources,
            'incomeBands': bands,
            'bandCoverage': {
                'availableFrequencyTotal': available_frequency_total,
                'reportedTotalIncomeFrequency': total_frequency,
                'differenceVsReportedTotal': None if total_frequency is None else total_frequency - available_frequency_total,
                'missingBandFrequencyCells': missing_band_cells,
                'note': (
                    'Le celle vuote del CSV MEF restano null e non vengono trasformate in zero. '
                    'La differenza rispetto alla frequenza totale è conservata senza attribuirle una causa non dichiarata dalla fonte.'
                ),
            },
        }

    return {
        'schemaVersion': 1,
        'generatedAt': '2026-08-20',
        'source': {
            'publisher': 'Dipartimento delle Finanze — MEF',
            'dataset': 'Redditi e principali variabili IRPEF su base comunale',
            'reference': '2025 a.i. 2024',
            'published': '2026-04-23',
            'pageUrl': SOURCE_URL,
            'downloadUrl': probe.SOURCE_ZIP,
        },
        'parsing': {**parsing, 'headerCount': len(headers)},
        'coverage': '7/7',
        'towns': result,
        'method': {
            'pensionIncomeShare': 'ammontare reddito da pensione / ammontare reddito complessivo × 100',
            'incomeSources': 'valori e frequenze MEF conservati senza riclassificazioni arbitrarie',
            'incomeBands': 'otto classi MEF conservate separatamente; celle vuote mantenute null',
        },
    }


def pension_metric(site: dict, snapshot: dict) -> dict:
    order = [row['town'] for row in site['metrics']['income']['rows']]
    rows = []
    pension_total = 0
    income_total = 0
    for town in order:
        detail = snapshot['towns'][town]
        pension_amount = detail['pensionIncome']['amountEuro']
        total_amount = detail['totalIncome']['amountEuro']
        value = detail['pensionIncome']['shareOfTotalIncomePercent']
        if value is None or pension_amount is None or total_amount in (None, 0):
            raise RuntimeError(f'{town}: quota pensioni non calcolabile')
        pension_total += pension_amount
        income_total += total_amount
        rows.append({
            **identity(site, town),
            'value': value,
            'formatted': percent(value),
            'series': {'years': [2024], 'values': [value]},
            'normalized': None,
            'benchmarkValue': value,
        })

    aggregate = pension_total / income_total * 100
    return {
        'meta': {
            'key': METRIC_KEY,
            'theme': 'economia',
            'label': 'Peso dei redditi da pensione',
            'shortLabel': 'Redditi da pensione',
            'description': (
                'Quota dell’ammontare complessivo dei redditi dichiarati che proviene da pensioni. '
                'Misura il peso economico di questa fonte di reddito, non la quota di pensionati tra i residenti.'
            ),
            'unit': 'percent',
            'year': '2024',
            'source': 'Dipartimento delle Finanze — MEF',
            'polarity': 'neutral',
            'searchTerms': ['pensione','pensioni','redditi da pensione','struttura redditi','fonti reddito','reddito pensionistico'],
        },
        'sourceUrl': SOURCE_URL,
        'rows': rows,
        'aggregate': {
            'value': aggregate,
            'label': 'Versilia · peso redditi da pensione',
            'note': 'Rapporto tra la somma dell’ammontare dei redditi da pensione e la somma del reddito complessivo dichiarato nei sette Comuni.',
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati ufficiali MEF',
            'formula': 'ammontare reddito da pensione / ammontare reddito complessivo × 100',
            'caveat': (
                'Non è la percentuale di pensionati e non misura il reddito disponibile delle famiglie. '
                'Le frequenze delle diverse fonti di reddito non sono sommabili come persone distinte, perché uno stesso contribuente può dichiarare più fonti.'
            ),
            'coverage': '7/7',
        },
    }


def update_site(site: dict, metric: dict, snapshot: dict) -> None:
    metrics = site['metrics']
    if METRIC_KEY in metrics:
        metrics[METRIC_KEY] = metric
    else:
        out = OrderedDict()
        for key, value in metrics.items():
            out[key] = value
            if key == 'incomeDistribution':
                out[METRIC_KEY] = metric
        site['metrics'] = out

    theme = site['themes']['economia']
    if METRIC_KEY not in theme['metrics']:
        theme['metrics'].insert(theme['metrics'].index('incomeDistribution') + 1, METRIC_KEY)
    redditi = next(section for section in theme['sections'] if section['key'] == 'redditi')
    if METRIC_KEY not in redditi['metrics']:
        redditi['metrics'].insert(redditi['metrics'].index('incomeDistribution') + 1, METRIC_KEY)
    redditi['description'] = 'Reddito imponibile, distribuzione dei redditi dichiarati, peso delle pensioni e confronto comunale con l’inflazione.'

    distribution = site['metrics']['incomeDistribution']
    distribution['meta']['detailDataset'] = {
        'key': 'incomeBandsFull2024',
        'snapshot': 'data/source-snapshots/mef-income-lotto-a-2024.json',
        'description': 'Otto fasce MEF complete disponibili nello snapshot di approfondimento; le celle MEF non valorizzate restano n.d.',
    }
    distribution.setdefault('method', {})['detailCaveat'] = (
        'Il dataset completo conserva separatamente le otto classi MEF e mantiene null le celle vuote.'
    )

    site['detailDatasets'] = site.get('detailDatasets', {})
    site['detailDatasets']['incomeSourcesAndBands2024'] = {
        'label': 'Redditi per fonte e fasce complete',
        'theme': 'economia',
        'year': '2024',
        'source': 'Dipartimento delle Finanze — MEF',
        'sourceUrl': SOURCE_URL,
        'snapshot': 'data/source-snapshots/mef-income-lotto-a-2024.json',
        'coverage': '7/7',
        'contents': ['incomeSources', 'incomeBands'],
        'note': 'Dataset di approfondimento utilizzato dalla materializzazione completa v2.',
    }
    site['version'] = 'v1.15.0'
    site['updated'] = '20 agosto 2026'


def update_registry(registry: dict, site: dict) -> None:
    registry['expectedMetricCount'] = len(site['metrics'])
    registry['expectedInlineMetricCount'] = len(site['metrics']) - 4
    registry['expectedExternalMetricCount'] = 4
    registry.setdefault('metricOverrides', {})[METRIC_KEY] = {'profile': 'mef-irpef-annual'}


def update_monitor(monitor: dict) -> None:
    source = monitor.get('sources', {}).get(SOURCE_URL)
    if not source:
        raise RuntimeError('Fonte MEF redditi assente dal monitor')
    metrics = source.setdefault('metrics', [])
    if METRIC_KEY not in metrics:
        metrics.append(METRIC_KEY)
        metrics.sort()


def update_audit(audit: dict) -> None:
    audit['status'] = 'implementation_income_stage1'
    audit['catalogMetricCountCurrentDraft'] = 130
    decisions = {
        'taxpayersAdultPopulationRate': 'awaiting_v2_materialization',
        'pensionIncomeShare': 'draft_materialized',
        'incomeSourceAndBandsDetail': 'snapshot_materialized_2024',
    }
    for candidate in audit.get('candidates', []):
        if candidate.get('key') in decisions:
            candidate['implementationStatus'] = decisions[candidate['key']]


def patch_history_expectation() -> None:
    text = HISTORY_TEST_PATH.read_text(encoding='utf-8')
    old = 'require(DATA["version"] == "v1.14.0", "Versione dati v1.14.0 non applicata")'
    new = 'require(DATA["version"] == "v1.15.0", "Versione dati v1.15.0 non applicata")'
    if new in text:
        return
    if old not in text:
        raise RuntimeError('Aspettativa versione storico v1.14 non trovata')
    HISTORY_TEST_PATH.write_text(text.replace(old, new, 1), encoding='utf-8')


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    audit = load(AUDIT_PATH)
    if 'dependencyIndices' not in site['metrics']:
        raise RuntimeError('La tranche Redditi deve essere materializzata dopo Demografia Lotto A')

    headers, _all_rows, towns, parsing = load_source()
    snapshot = build_snapshot(site, headers, towns, parsing)
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save(SNAPSHOT_PATH, snapshot)

    metric = pension_metric(site, snapshot)
    update_site(site, metric, snapshot)
    update_registry(registry, site)
    update_monitor(monitor)
    update_audit(audit)
    patch_history_expectation()

    external = [item for item in site['metrics'].values() if item.get('dataStorage', {}).get('type') == 'external-climate']
    if len(site['metrics']) != 130 or len(external) != 4:
        raise RuntimeError(f'Conteggio inatteso: {len(site["metrics"])} totali, {len(external)} esterni')

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    save(AUDIT_PATH, audit)
    print('Lotto A Redditi stage 1: 130 indicatori = 126 inline + 4 climatici; snapshot MEF 2024 acquisito.')


if __name__ == '__main__':
    main()
