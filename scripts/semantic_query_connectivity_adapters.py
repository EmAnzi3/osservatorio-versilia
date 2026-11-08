"""AGCOM declared FTTH coverage and native counts; no household imputation."""
from a6_pins import Pin as _pin
import json
import math
from datetime import datetime

import agcom_sources

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

DESI, NEAR, REACHED, UNREACHED = KEYS = ('ftthCoverageDesi', 'ftthCoverage20m', 'ftthReachedHouseholds', 'ftthUnreachedHouseholds')
PERCENTAGES = (DESI, NEAR)
COUNTS = (REACHED, UNREACHED)
NATIVE = agcom_sources.NATIVE
BENCHMARK = agcom_sources.BENCHMARK
URL = 'https://maps.agcom.it/'
_AUDIT = json.loads((agcom_sources.ROOT / NATIVE).read_text(encoding='utf-8'))['agcomAudit']
CSV = _AUDIT['officialCsvUrl']
PERIOD = _AUDIT['dataPeriod']
REFERENCE = datetime.strptime(PERIOD, '%d/%m/%Y').date().isoformat()
_MONTHS = ('gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre')
_DAY = datetime.strptime(PERIOD, '%d/%m/%Y').date()
LABEL = f'{_DAY.day} {_MONTHS[_DAY.month - 1]} {_DAY.year}'
_REVISION = _AUDIT.get('revisionDate')
MISSING_COUNTS = sorted(t['code'] for t in json.loads((agcom_sources.ROOT / NATIVE).read_text(encoding='utf-8'))['towns']
                        if t['agcom']['primaryOfficialCsv']['famiglie_ftth'] is None)
COUNT_COVERAGE = f'{7 - len(MISSING_COUNTS)}/7'
FIELDS = {DESI: 'copertura_ftth_desi_pct', NEAR: 'copertura_ftth_20m_pct', REACHED: 'famiglie_ftth'}
FORMULAS = {DESI: 'Copertura FTTH DESI comunale pubblicata da AGCOM; media Versilia ponderata per famiglie residenti AGCOM', NEAR: 'Copertura FTTH entro 20 metri comunale pubblicata da AGCOM; media Versilia ponderata per famiglie residenti AGCOM', REACHED: 'Famiglie FTTH pubblicate da AGCOM nella reportistica comunale Broadband Map.', UNREACHED: 'famiglie residenti AGCOM − famiglie raggiunte da FTTH DESI'}
HASHES = {NATIVE: (_pin('connectivity#1'), _pin('connectivity#2')), BENCHMARK: (_pin('connectivity#3'), _pin('connectivity#4'))}
NOTES = ['connectivity_declared_network_not_subscriptions_speed_or_civic_activation', 'connectivity_no_automatic_causal_or_policy_priority_claim']


def frozen(engine, path):
    data, ref = engine.file(path)
    if ref.get('path') != path or (ref.get('sha256'), fingerprint(data)) != HASHES[path]:
        raise ValueError('connectivity_frozen_input_changed')
    return data, ref


def equal(actual, expected):
    if expected is None:
        if actual is not None: raise ValueError('connectivity_missing_count_imputed')
    elif not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('connectivity_public_native_mismatch')


def token(key, period):
    if str(period) in (REFERENCE[:4], LABEL, REFERENCE): return REFERENCE
    raise ValueError('connectivity_reference_date_not_frozen')


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany', 'italy'] if key in PERCENTAGES else []
def operations(key, dim): return ['compare', 'rank'] + (['benchmark_gap'] if key in PERCENTAGES else [])


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('connectivity_single_reference_no_history')
    if op == 'weighted_ratio': raise ValueError('connectivity_rounded_percentages_not_native_pooling')
    if op == 'correlation': raise ValueError('connectivity_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('connectivity_peer_anomaly_not_reviewed')
    if op == 'benchmark_gap' and key in COUNTS:
        raise ValueError('connectivity_absolute_benchmarks_incomplete')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim != 'total' or meta.get('key') != key or meta.get('year') != LABEL
            or meta.get('unit') != ('percent' if key in PERCENTAGES else 'number')
            or meta.get('polarity') != 'neutral' or metric.get('sourceUrl') != URL
            or metric.get('method', {}).get('formula') != FORMULAS[key]
            or metric['method'].get('coverage') != ('7/7' if key in PERCENTAGES else COUNT_COVERAGE)):
        raise ValueError('connectivity_definition_changed')
    return dict(unit=meta['unit'], population='AGCOM resident households; declared network availability, not active contracts',
                definition=FIELDS.get(key, 'famiglie_residenti minus famiglie_ftth; missing count remains missing'),
                method='direct primary official municipal percentage, published one-decimal precision retained' if key in PERCENTAGES else FORMULAS[key],
                frequency='reference_snapshot', periodBasis=f'official consistencies reference {REFERENCE}' + (f'; report revised {_REVISION}' if _REVISION else '') + '; acquisition dates retained',
                nativeComponentsAvailable=False, adapter='connectivity/' + key + '/v1')


def value(key, record):
    if key != UNREACHED: return record[FIELDS[key]]
    return None if record['famiglie_ftth'] is None else record['famiglie_residenti'] - record['famiglie_ftth']


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    snap, ref = frozen(engine, NATIVE)
    if (len(snap['towns']) != 7 or {t['code'] for t in snap['towns']} != set(TOWNS)
            or {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS):
        raise ValueError('connectivity_municipal_identity_changed')
    native = {t['code']: (i, t['agcom']['primaryOfficialCsv']) for i,t in enumerate(snap['towns'])}
    rows = metric['rows']
    if len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS):
        raise ValueError('connectivity_municipal_identity_changed')
    for row in rows:
        code = row['code']; index, record = native[code]; town = snap['towns'][index]
        if (row.get('town') != TOWNS[code] or row.get('slug') != '-'.join(TOWNS[code].lower().split())
                or town['town'] != TOWNS[code] or record['comune'] != TOWNS[code]
                or snap['agcomAudit'].get('dataPeriod') != PERIOD or row.get('notApplicable') or row.get('dataUnavailable')
                or any(row.get(k) is not None for k in ('series', 'normalized', 'ratioComponents'))):
            raise ValueError('connectivity_row_definition_changed')
        expected = value(key, record)
        equal(row.get('value'), expected); equal(row.get('benchmarkValue'), expected)
    aggregate = metric.get('aggregate') or {}
    if key in PERCENTAGES:
        weights = [r['famiglie_residenti'] for _,r in native.values()]
        total = math.fsum(value(key,r)*r['famiglie_residenti'] for _,r in native.values()) / sum(weights)
        aggregate_label = 'Media ponderata Versilia'
    else:
        total = sum(value(key,r) for _,r in native.values() if value(key,r) is not None)
        aggregate_label = f'Totale parziale Versilia ({COUNT_COVERAGE})' if MISSING_COUNTS else 'Totale Versilia'
    equal(aggregate.get('value'), total)
    if aggregate.get('label') != aggregate_label or metric.get('normalizedAggregate') is not None:
        raise ValueError('connectivity_aggregate_definition_changed')
    if key in PERCENTAGES:
        bench, _ = frozen(engine, BENCHMARK); b = bench['benchmarks'][key]; meta = metric['meta'].get('benchmark') or {}
        if meta.get('year') != LABEL or meta.get('sourceSnapshot') != BENCHMARK or meta.get('url') != CSV:
            raise ValueError('connectivity_benchmark_definition_changed')
        for scope in scopes(key,'total'): equal(meta.get(scope), b[scope])
    elif metric['meta'].get('benchmark') is not None:
        raise ValueError('connectivity_absolute_benchmarks_incomplete')
    return snap, ref, native


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric,key,dim)
    snap, ref, native = validated(engine,key); row = metric['rows'][index]; code = row['code']
    if period != REFERENCE: raise ValueError('connectivity_reference_date_not_frozen')
    j, record = native[code]
    evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/value'),
                dict(ref,kind='source_snapshot',recordPointer=f'/towns/{j}/agcom/primaryOfficialCsv',sourceUrl=CSV,nativeFields={k:record[k] for k in ('famiglie_residenti','famiglie_ftth','famiglie_ftth_20m','copertura_ftth_desi_pct','copertura_ftth_20m_pct')},referenceDate=REFERENCE)]
    notes = NOTES[:]
    if key in PERCENTAGES: notes += ['connectivity_percentages_and_counts_independent_no_reverse_derivation', 'connectivity_public_aggregate_weights_rounded_percentages_not_native_count_ratio']
    elif MISSING_COUNTS == ['046013']: notes += ['connectivity_counts_6_of_7_forte_missing_no_imputation', 'connectivity_available_municipal_mean_not_complete_versilia_total']
    elif MISSING_COUNTS: notes += ['connectivity_counts_partial_missing_no_imputation', 'connectivity_available_municipal_mean_not_complete_versilia_total']
    if key == NEAR: notes += ['connectivity_within20m_distinct_from_desi_coverage']
    return dict(ctx,metric=key,dimension=dim,geography=code,period=period,value=row['value'],source=CSV,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=row['value'] is None,missingReason='official_absolute_count_missing_not_reconstructed_from_zero_percent' if row['value'] is None else None), notes


def benchmark(engine, key, scope, municipal):
    if key not in PERCENTAGES or scope not in scopes(key,'total') or municipal['period'] != REFERENCE:
        raise ValueError('connectivity_benchmark_scope_not_reviewed')
    validated(engine,key); snap,ref = frozen(engine,BENCHMARK)
    evidence = [dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/{scope}',acquisitionEvidence=snap['acquisitionEvidence']),
                dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal,geography=scope,value=snap['benchmarks'][key][scope],evidence=evidence,provenance=evidence,source=CSV,benchmarkAggregation='frozen A3 audited aggregate of official municipal percentages weighted by AGCOM households; national panel not frozen here, no raw replay claim')
