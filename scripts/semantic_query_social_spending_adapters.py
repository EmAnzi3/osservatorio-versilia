"""Frozen Istat social expenditure: nominal municipal indices and user-area shares."""
import math

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

SPENDING, COMPOSITION = KEYS = ('socialSpendingPerResident', 'socialSpendingByUserArea')
NATIVE = 'data/source-snapshots/welfare-prima-infanzia-2026-08.json'
BENCHMARK = 'data/source-snapshots/a3-istat-social-services-benchmark-2022.json'
URLS = dict(zip(KEYS, ('https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx',
                       'https://www.istat.it/storage/misura-comune/10a-Servizi-sociali-per-tipologia-di-utenza.xlsx')))
BENCHMARK_URL = 'https://www.istat.it/comunicato-stampa/la-spesa-dei-comuni-per-i-servizi-sociali-anno-2022/'
UNITS = {SPENDING: 'eurPerResident', COMPOSITION: 'percent'}
FORMULAS = {SPENDING: 'Spesa dei comuni / Popolazione residente media (euro)',
            COMPOSITION: 'Spesa dei comuni per tipologia di utenza / Spesa totale dei comuni x 100'}
AREAS = ('Famiglia e minori', 'Disabili', 'Dipendenze', 'Anziani (65 anni e più)',
         'Immigrati, Rom, Sinti e Caminanti', 'Povertà, disagio adulti e senza dimora', 'Multiutenza')
SELECTORS = ('Famiglie e minori', 'Disabilità', 'Dipendenze', 'Anziani', 'Immigrazione', 'Povertà e disagio', 'Multiutenza')
# Explicit semantic selectors: source parts have labels and positional identity, no keys.
PARTS = ('families-minors', 'disability', 'addictions', 'elderly', 'immigration', 'poverty-hardship', 'multiuser')
HASHES = {
    NATIVE: ('b13bdc5b1c579b9db6f6875637b68653869e44b898c59803415f829a6ef3455d',
             'ad30ce8d8779b275860d1c2e0a083950192792c028ac1977e237ff2a3a1ba3d9'),
    BENCHMARK: ('d48e8dd1ffdaabf45068a54e5daafabebfc9083073a1d370e6aa1e99303b66d0',
                'b7917cb3457f0a3ab2cd2e439f5a68283c09d93f83df4b35470c751ec2da47f3'),
}
NOTES = ['social_municipal_arithmetic_means_not_consolidated_versilia',
         'social_spending_not_need_quality_effectiveness_or_policy_priority',
         'social_native_denominators_unavailable_no_pooling_or_reverse_derived_counts']


def frozen(engine, path):
    value, ref = engine.file(path)
    if ref.get('path') != path or (ref.get('sha256'), fingerprint(value)) != HASHES[path]:
        raise ValueError('social_frozen_input_changed')
    return value, ref


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('social_public_native_value_changed')


def dimensions(key): return ['total'] + (['part:'+p for p in PARTS] if key == COMPOSITION else [])
def scopes(key, dim): return ['tuscany', 'italy'] if key == SPENDING else []
def operations(key, dim): return ['compare', 'rank'] + (['series', 'benchmark_gap'] if key == SPENDING else [])


def area(dim): return 0 if dim == 'total' else PARTS.index(dim[5:])


def selection_guard(key, dim, op):
    if op == 'weighted_ratio': raise ValueError('social_native_denominators_unavailable')
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('social_temporal_operations_not_reviewed')
    if op == 'correlation': raise ValueError('social_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('social_peer_anomaly_not_reviewed')
    if key == COMPOSITION and op == 'series': raise ValueError('social_area_history_not_published')
    if key == COMPOSITION and op == 'benchmark_gap': raise ValueError('social_area_benchmark_not_available')


def context(metric, key, dim):
    meta = metric['meta']; method = metric.get('method') or {}
    if (dim not in dimensions(key) or meta.get('key') != key or meta.get('year') != '2022'
            or meta.get('unit') != UNITS[key] or meta.get('polarity') != 'neutral'
            or metric.get('sourceUrl') != URLS[key] or method.get('formula') != FORMULAS[key]):
        raise ValueError('social_definition_changed')
    if key == SPENDING:
        if 'include i servizi educativi per la prima infanzia' not in method.get('caveat', ''):
            raise ValueError('social_including_early_childhood_scope_changed')
        definition = 'nominal municipal social expenditure per average resident, including early-childhood educational services'
    else:
        if (meta.get('compositeType') != 'distribution' or meta.get('summaryUnit') != 'eurPerResident'
                or meta.get('summaryLabel') != 'Spesa sociale per abitante' or meta.get('benchmark') is not None):
            raise ValueError('social_area_definition_changed')
        definition = 'municipal social expenditure share: '+AREAS[area(dim)]
    return dict(unit=UNITS[key], population='municipal social expenditure by Istat user-area perimeter, including early childhood',
                definition=definition,
                method='official inclusive nominal social expenditure / average resident; source precision retained' if key == SPENDING else 'direct published percentage; total aliases first area, never total spending',
                frequency='annual', periodBasis='2014–2022 frozen inclusive expenditure series' if key == SPENDING else '2022 composition only',
                nativeComponentsAvailable=False, adapter='social-spending/'+key+'/'+dim+'/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    snap, ref = frozen(engine, NATIVE); rows = metric['rows']
    if (len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS)
            or {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS
            or set(snap['towns']) != set(TOWNS.values()) or tuple(snap['areas']) != AREAS):
        raise ValueError('social_municipal_identity_changed')
    for row in rows:
        code = row['code']; name = TOWNS[code]; native = snap['towns'][name]
        if (row.get('town') != name or native['istatCode'] != code
                or row.get('slug') != '-'.join(name.lower().split())
                or row.get('notApplicable') or row.get('dataUnavailable')):
            raise ValueError('social_municipal_identity_changed')
        history = native[SPENDING]
        published = dict(years=history['years'], values=[round(v, 2) for v in history['values']])
        if key == SPENDING:
            if row.get('series') != published: raise ValueError('social_public_history_changed')
            value = published['values'][-1]
        else:
            shares = native[COMPOSITION]
            expected = [dict(label=l, selectorLabel=s, value=v, unit='percent') for l,s,v in zip(AREAS, SELECTORS, shares)]
            if (row.get('parts') != expected or row.get('series') is not None
                    or any(not finite(p.get('value')) for p in row.get('parts', []))):
                raise ValueError('social_public_area_parts_changed')
            if not math.isclose(math.fsum(shares), 100, abs_tol=1e-9):
                raise ValueError('social_area_partition_changed')
            equal(row.get('summaryValue'), published['values'][-1])
            value = shares[0]
        equal(row.get('value'), value); equal(row.get('benchmarkValue'), value)
        if row.get('normalized') is not None or row.get('ratioComponents') is not None:
            raise ValueError('social_unreviewed_components_changed')
    aggregate = metric.get('aggregate') or {}
    spending_mean = round(math.fsum(round(snap['towns'][n][SPENDING]['values'][-1], 2) for n in TOWNS.values()) / 7, 2)
    if key == SPENDING:
        equal(aggregate.get('value'), spending_mean)
        expected_label = 'Versilia · media comunale'; coverage = '7/7 Comuni · serie 2014–2022'
    else:
        means = [math.fsum(snap['towns'][n][COMPOSITION][i] for n in TOWNS.values()) / 7 for i in range(7)]
        parts = aggregate.get('parts') or []
        if len(parts) != 7: raise ValueError('social_summary_definition_changed')
        for i, p in enumerate(parts):
            if {k:p.get(k) for k in ('label','selectorLabel','unit')} != dict(label=AREAS[i], selectorLabel=SELECTORS[i], unit='percent'):
                raise ValueError('social_summary_definition_changed')
            equal(p.get('value'), means[i])
        equal(aggregate.get('value'), means[0]); equal(aggregate.get('summaryValue'), spending_mean)
        expected_label = 'Versilia · media comunale per area'; coverage = '7/7 Comuni · anno 2022'
    if (aggregate.get('label') != expected_label or 'media aritmetica' not in aggregate.get('note', '').lower()
            or metric.get('method', {}).get('coverage') != coverage or metric.get('normalizedAggregate') is not None):
        raise ValueError('social_summary_definition_changed')
    return snap, ref


def available_periods(engine, key, dim, row):
    snap, _ = validated(engine, key)
    if key == COMPOSITION: raise ValueError('social_area_history_not_published')
    return list(map(str, snap['towns'][row['town']][SPENDING]['years']))


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref = validated(engine, key); row = metric['rows'][index]; native = snap['towns'][row['town']]
    public = f'/metrics/{key}/rows/{index}/value'; record = f'/towns/{row["town"]}/{key}'
    if key == SPENDING:
        years = list(map(str, native[key]['years']))
        if period not in years or (not historical and period != '2022'): raise ValueError('social_period_not_frozen')
        i = years.index(period); original = native[key]['values'][i]; value = round(original, 2)
        record += f'/values/{i}'
        if historical: public = f'/metrics/{key}/rows/{index}/series/values/{i}'
        extra = dict(transformation='round(native value, 2); same public materialization', nativeValue=original, publishedDecimals=2)
        notes = ['social_nominal_euros_no_inflation_adjustment', 'social_2014_2022_includes_early_childhood_no_excluded_scope_concatenation']
    else:
        if period != '2022': raise ValueError('social_period_not_frozen')
        i = area(dim); value = native[key][i]; record += f'/{i}'; extra = {}
        if dim != 'total': public = f'/metrics/{key}/rows/{index}/parts/{i}/value'
        notes = ['social_total_alias_families_minors_not_sum', 'social_summary_eur_per_resident_not_area_percent',
                 'social_area_zero_not_absence_of_need_or_health_services']
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=public),
                dict(ref, kind='source_snapshot', recordPointer=record, **extra)]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value,
                source=URLS[key], evidence=evidence, provenance=evidence, notApplicable=False,
                dataUnavailable=False, missingReason=None), NOTES + notes


def benchmark(engine, key, scope, municipal):
    if key != SPENDING: raise ValueError('social_area_benchmark_not_available')
    if scope not in scopes(key, municipal['dimension']) or municipal['period'] != '2022':
        raise ValueError('social_benchmark_scope_or_period_not_reviewed')
    validated(engine, key); snap, ref = frozen(engine, BENCHMARK)
    spec = snap['benchmarks'][key]; meta = engine._catalog['metrics'][key]['meta'].get('benchmark') or {}
    if (spec.get('year') != '2022' or spec.get('unit') != 'eurPerResident'
            or meta.get('year') != '2022' or meta.get('unit', 'eurPerResident') != 'eurPerResident'
            or meta.get('url') != BENCHMARK_URL or meta.get('sourceSnapshot') != BENCHMARK):
        raise ValueError('social_benchmark_definition_changed')
    for s in scopes(key, municipal['dimension']): equal(meta.get(s), spec[s])
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/benchmarks/{key}/{scope}'),
                dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal, geography=scope, value=spec[scope], source=BENCHMARK_URL,
                evidence=evidence, provenance=evidence, dataUnavailable=False, missingReason=None,
                publishedDecimals=0,
                benchmarkAggregation='official Tav. 1 inclusive social expenditure per resident; integer source precision; not municipal mean')
