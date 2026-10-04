#!/usr/bin/env python3
"""Add two MEF histories from native municipal components without changing levels."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/source-snapshots/a3-simple-mef-history-2023-2024.json'
CURRENT = ROOT / 'data/source-snapshots/mef-income-lotto-a-2024.json'
YEARS = [2023, 2024]
SOURCE_KEYS = ['buildings', 'employment', 'pension', 'selfEmployment',
               'entrepreneurOrdinary', 'entrepreneurSimplified', 'participation']
LABELS = {'buildings': 'Fabbricati', 'employment': 'Lavoro dipendente e assimilati',
          'pension': 'Pensione', 'selfEmployment': 'Lavoro autonomo',
          'entrepreneurOrdinary': 'Impresa · contabilità ordinaria',
          'entrepreneurSimplified': 'Impresa · contabilità semplificata',
          'participation': 'Partecipazione'}
PRIOR_URL = ('https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
             'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2023.zip?d=1615465800')
PRIOR_COLUMNS = ['Reddito da fabbricati', 'Reddito da lavoro dipendente e assimilati',
                 'Reddito da pensione', 'Reddito da lavoro autonomo (comprensivo dei valori nulli)',
                 "Reddito di spettanza dell'imprenditore in contabilita' ordinaria  (comprensivo dei valori nulli)",
                 "Reddito di spettanza dell'imprenditore in contabilita' semplificata (comprensivo dei valori nulli)",
                 'Reddito da partecipazione  (comprensivo dei valori nulli)']


def check_prior_archive(body: bytes, frozen: dict) -> None:
    """Replay extraction of seven native CSV rows; no geographic aggregation."""
    source = frozen['source']
    if len(body) != source['archiveBytes'] or hashlib.sha256(body).hexdigest() != source['archiveSha256']:
        raise RuntimeError('MEF history: downloaded archive fingerprint mismatch')
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        text = archive.read(source['member']).decode('utf-8-sig')
    wanted = {item['code']: item for item in frozen['towns'].values()}
    seen = set()
    for row in csv.DictReader(io.StringIO(text), delimiter=';'):
        code = row['Codice Istat Comune']
        if code not in wanted:
            continue
        if code in seen or row['Anno di imposta'] != '2023':
            raise RuntimeError('MEF history: duplicate municipal row/period mismatch')
        seen.add(code)
        def number(field):
            return int(row[field]) if row[field].strip() else None
        sources = [{'key': key, 'frequency': number(prefix + ' - Frequenza'),
                    'amountEuro': number(prefix + ' - Ammontare in euro')}
                   for key, prefix in zip(SOURCE_KEYS, PRIOR_COLUMNS, strict=True)]
        raw = {'totalIncome': {'frequency': number('Reddito complessivo - Frequenza'),
                              'amountEuro': number('Reddito complessivo - Ammontare in euro')},
               'incomeSources': sources, 'pensionIncome': sources[2]}
        if raw != wanted[code]['countsByYear']['2023']:
            raise RuntimeError('MEF history: CSV native components mismatch')
    if seen != set(wanted):
        raise RuntimeError('MEF history: CSV municipal coverage mismatch')


def _close(actual, expected, label):
    if actual is None or expected is None:
        if actual is not expected:
            raise RuntimeError(f'MEF history: {label}: null mismatch')
    elif (isinstance(actual, bool) or not isinstance(actual, (int, float))
          or not math.isfinite(actual)
          or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-8)):
        raise RuntimeError(f'MEF history: {label}: current value mismatch')


def _components(raw):
    sources = raw.get('incomeSources', [])
    if [x.get('key') for x in sources] != SOURCE_KEYS:
        raise RuntimeError('MEF history: native source order mismatch')
    for item in [raw['totalIncome'], raw['pensionIncome'], *sources]:
        for field in ('frequency', 'amountEuro'):
            value = item.get(field)
            if value is not None and (isinstance(value, bool)
                    or not isinstance(value, int) or value < 0):
                raise RuntimeError('MEF history: invalid native count')
    if raw['totalIncome']['amountEuro'] <= 0:
        raise RuntimeError('MEF history: missing total income')
    if any(raw['pensionIncome'].get(k) != sources[2].get(k)
           for k in ('frequency', 'amountEuro')):
        raise RuntimeError('MEF history: pension components disagree')
    return {item['key']: item for item in sources}


def _ratio(item):
    frequency, amount = item['frequency'], item['amountEuro']
    return None if frequency is None or amount is None or frequency == 0 else amount / frequency


def _series(values):
    observed = [(year, value) for year, value in zip(YEARS, values, strict=True)
                if value is not None]
    return {'years': [year for year, _ in observed],
            'values': [value for _, value in observed],
            'source': 'Dipartimento delle Finanze — MEF',
            'sourceUrl': PRIOR_URL,
            'sourceSnapshot': str(SNAPSHOT.relative_to(ROOT)),
            'note': 'Anni di imposta 2023–2024; celle MEF soppresse non generano osservazioni.'}


def _attach(container, key, value):
    existing = container.get(key)
    if existing and existing != value:
        # A one-year public series is a current-level placeholder, not a history.
        if (key != 'series' or existing.get('years') != [2024]
                or existing.get('values') != [value['values'][-1]]):
            raise RuntimeError(f'MEF history: conflicting {key}')
    container[key] = value


def apply_history(site: dict, snapshot: dict | None = None) -> None:
    """Validate the complete lot first; mutate only after all source/level checks."""
    frozen = snapshot if snapshot is not None else json.loads(SNAPSHOT.read_text())
    current = json.loads(CURRENT.read_text())
    src = frozen.get('source', {})
    digest = hashlib.sha256(json.dumps(frozen.get('towns'), ensure_ascii=False,
                       sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (frozen.get('schemaVersion') != 1 or frozen.get('profileId') != 'mef-irpef-annual'
            or frozen.get('years') != YEARS or src.get('url') != PRIOR_URL
            or src.get('archiveSha256') != '2d8fafc10c728fcc132ee9f0f0a123d77b889093419f427163bc629bdb70b060'
            or src.get('archiveBytes') != 1065416
            or src.get('member') != 'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2023.csv'
            or src.get('currentSnapshot') != str(CURRENT.relative_to(ROOT))
            or src.get('currentSnapshotSha256') != hashlib.sha256(CURRENT.read_bytes()).hexdigest()
            or digest != frozen.get('nativeComponentsSha256')
            or digest != '8bb26d4bf7becebfe3593ec7bf1400171c9fbc151fe3090b5f8929684f03d413'):
        raise RuntimeError('MEF history: source fingerprint/period mismatch')
    towns = frozen['towns']
    if len(towns) != 7 or set(towns) != set(current['towns']):
        raise RuntimeError('MEF history: municipal coverage mismatch')
    metrics = copy.deepcopy({key: site['metrics'][key]
                            for key in ('incomeSourceProfile', 'pensionIncomeShare')})
    rows = {}
    for key, metric in metrics.items():
        if str(metric['meta'].get('year')) != '2024':
            raise RuntimeError('MEF history: public period mismatch')
        rows[key] = {r['town']: r for r in metric['rows']}
        if len(metric['rows']) != 7 or set(rows[key]) != set(towns):
            raise RuntimeError('MEF history: public municipal coverage mismatch')
    by_year = {year: {} for year in YEARS}
    for town, item in towns.items():
        latest = item['countsByYear'].get('2024')
        expected = current['towns'][town]
        if (item['code'] != expected['code']
                or set(item['countsByYear']) != {'2023', '2024'}
                or any(latest.get(k) != expected[k]
                       for k in ('incomeSources', 'totalIncome', 'pensionIncome'))):
            raise RuntimeError('MEF history: frozen current components mismatch')
        for key in metrics:
            if rows[key][town]['code'] != item['code']:
                raise RuntimeError('MEF history: public municipal code mismatch')
        for year in YEARS:
            raw = item['countsByYear'][str(year)]
            by_year[year][town] = (_components(raw), raw['totalIncome']['amountEuro'])
        profile, pension = rows['incomeSourceProfile'][town], rows['pensionIncomeShare'][town]
        if [p.get('selectorLabel') for p in profile['parts']] != [LABELS[k] for k in
                ['employment', 'pension', 'selfEmployment', 'entrepreneurOrdinary',
                 'entrepreneurSimplified', 'participation', 'buildings']]:
            raise RuntimeError('MEF history: public source selectors mismatch')
        component_series = {}
        for part in profile['parts']:
            source_key = next(k for k, label in LABELS.items() if label == part['selectorLabel'])
            latest_source = by_year[2024][town][0][source_key]
            _close(part['value'], _ratio(latest_source), f'{town}/{source_key}')
            if part.get('count') != latest_source['frequency'] or part.get('amountEuro') != latest_source['amountEuro']:
                raise RuntimeError('MEF history: public part components mismatch')
            component_series[part['selectorLabel']] = _series([
                _ratio(by_year[year][town][0][source_key]) for year in YEARS])
        _close(profile['value'], component_series[LABELS['employment']]['values'][-1], town)
        pension_values = [by_year[y][town][0]['pension']['amountEuro'] /
                          by_year[y][town][1] * 100 for y in YEARS]
        _close(pension['value'], pension_values[-1], town)
        _attach(profile, 'componentSeries', component_series)
        _attach(profile, 'series', component_series[LABELS['employment']])
        _attach(pension, 'series', _series(pension_values))
    aggregate_profile = metrics['incomeSourceProfile']['aggregate']
    aggregate_components = {}
    for part in aggregate_profile['parts']:
        source_key = next(k for k, label in LABELS.items() if label == part['selectorLabel'])
        values = []
        for year in YEARS:
            sources = [by_year[year][t][0][source_key] for t in towns]
            values.append(None if any(x['frequency'] is None or x['amountEuro'] is None for x in sources)
                          else sum(x['amountEuro'] for x in sources) / sum(x['frequency'] for x in sources))
        _close(part['value'], values[-1], f'aggregate/{source_key}')
        aggregate_components[part['selectorLabel']] = _series(values)
    _close(aggregate_profile['value'], aggregate_components[LABELS['employment']]['values'][-1], 'aggregate/profile')
    _attach(aggregate_profile, 'componentSeries', aggregate_components)
    _attach(aggregate_profile, 'series', aggregate_components[LABELS['employment']])
    aggregate_pension = metrics['pensionIncomeShare']['aggregate']
    values = [sum(by_year[y][t][0]['pension']['amountEuro'] for t in towns) /
              sum(by_year[y][t][1] for t in towns) * 100 for y in YEARS]
    _close(aggregate_pension['value'], values[-1], 'aggregate/pension')
    _attach(aggregate_pension, 'series', _series(values))
    site['metrics'].update(metrics)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/site-data.json')
    parser.add_argument('--check-source', action='store_true',
                        help='Re-download the small official 2023 ZIP with a 45-second timeout.')
    args = parser.parse_args()
    site = json.loads(args.input.read_text())
    apply_history(site)
    if args.check_source:
        with urllib.request.urlopen(PRIOR_URL, timeout=45) as response:
            check_prior_archive(response.read(), json.loads(SNAPSHOT.read_text()))
    print('MEF histories validated: 2 metrics × 7 municipalities, 2023–2024; input unchanged.')
