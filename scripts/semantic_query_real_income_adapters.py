"""Cumulative taxable mean income: municipal rounding and national NIC explicit."""
import math
from acquire_a3_benchmark_mef_istat_real_income_annual import validate_snapshot
from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('incomeVsInflation',)
YEARS = list(range(2016, 2025))
PANEL = 'data/source-snapshots/a3-mef-real-income-benchmark-2024.json'
NIC = 'data/source-snapshots/nic-italia-2016-2024.json'
HASHES = {
    PANEL: ('7944f7454584d9047fc8c53087328a99f60309119f61de0f6894bf8e88806a0a', '61a9c47a7c677692d901aa3957d11c65f85a417f18ca74229514d7ebc3d4462a'),
    NIC: ('78d9c621e60eceb09269dbeddc09a2828ffc06f909611e0ee6cb8d9898ed8b71', 'a2b3398351169f38affa270c3cb3ee93df43332cbcdebfa24b199b711e08eef3'),
}
METRIC_HASH = 'c362a50dfe910b9a5bd7396c3d25c9f5347122e2fc78ca02eb9bd3a8edafc54e'
NOTES = ['real_income_taxable_mean_not_disposable_household_income',
         'real_income_national_nic_not_local_prices_or_individual_purchasing_power',
         'real_income_cumulative_2016_baseline_not_annual_growth',
         'real_income_intermediate_history_catalog_only_native_endpoint_panels_2016_2024',
         'real_income_normalized_panels_reconciled_original_archives_not_replayed',
         'real_income_numerical_rank_not_quality_or_causal_inference']


def dimensions(key): return ['total', 'nominal']
def scopes(key, dim): return ['tuscany', 'italy'] if dim == 'total' else []
def operations(key, dim): return ['compare', 'rank', 'series'] + (['benchmark_gap'] if dim == 'total' else [])


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('real_income_cumulative_temporal_analysis_not_reviewed')
    if op == 'weighted_ratio': raise ValueError('real_income_growth_not_additive_no_pooling')
    if op == 'anomaly': raise ValueError('real_income_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('real_income_pair_not_jointly_reviewed')
    if op == 'benchmark_gap' and dim != 'total': raise ValueError('real_income_nominal_benchmark_not_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('real_income_dimension_not_reviewed')
    return dict(unit='percent', population='MEF municipal declarants with taxable income; changing yearly populations, not a household cohort',
                definition='cumulative taxable mean income change relative to 2016' + (' deflated by national NIC chained annual rates' if dim == 'total' else ' in nominal euros'),
                method='municipal mean income rounded to cents; published cumulative change rounded to four decimals; national NIC 2016=100',
                frequency='annual', periodBasis='income tax year, not publication year; common baseline 2016; national prices vs municipal income',
                adapter='real-income/'+key+'/'+dim+'/v1')


def close(actual, expected, tolerance=1e-9):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError('real_income_arithmetic_changed')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]
    if fingerprint(metric) != METRIC_HASH: raise ValueError('real_income_public_definition_or_history_changed')
    if len(engine._catalog['towns']) != 7 or {t['code']:t['name'] for t in engine._catalog['towns']} != TOWNS:
        raise ValueError('real_income_municipal_identity_changed')
    snapshots = {}; refs = {}
    for path in (PANEL, NIC):
        snap, ref = engine.file(path)
        if ref.get('path') != path or (ref.get('sha256'), fingerprint(snap)) != HASHES[path]:
            raise ValueError('real_income_frozen_input_changed')
        snapshots[path] = snap; refs[path] = ref
    panel, nic = snapshots[PANEL], snapshots[NIC]
    # The exact mutable state was checked above on every access; replay large panels once.
    if not getattr(engine, '_real_income_validated', False):
        try: validate_snapshot(metric, panel)
        except (RuntimeError, KeyError, ValueError) as exc:
            raise ValueError('real_income_native_endpoint_reconciliation_changed') from exc
        if nic['years'] != YEARS or nic['comparisonBase'] != '2016=100' or nic['territory']['level'] != 'national':
            raise ValueError('real_income_nic_basis_changed')
        chain = 100
        for j, y in enumerate(YEARS):
            if j: chain *= 1 + nic['annualRatesPercent'][str(y)]/100
            close(nic['comparisonIndex'][j], round(chain, 4))
            close(metric['inflationSeries']['values'][j], round(nic['comparisonIndex'][j]-100, 4))
        for row in metric['rows']:
            if row['town'] != TOWNS[row['code']]: raise ValueError('real_income_municipal_identity_changed')
            for j, y in enumerate(YEARS):
                nominal = row['nominalSeries']['values'][j]
                real = row['realSeries']['values'][j]
                close(real, ((1+nominal/100)/(nic['comparisonIndex'][j]/100)-1)*100, .00011)
                close(row['series']['values'][j], real)
            close(row['value'], row['series']['values'][-1])
        engine._real_income_validated = True
    return metric, panel, nic, refs


def available_periods(engine, key, dim, row):
    validated(engine, key)
    return [str(y) for y in YEARS]


def observation(engine, key, index, dim, period, historical):
    metric, panel, nic, refs = validated(engine, key); ctx = context(metric, key, dim)
    if period not in [str(y) for y in YEARS]: raise ValueError('real_income_period_not_frozen')
    row = metric['rows'][index]; code = row['code']; j = YEARS.index(int(period))
    field = 'series' if dim == 'total' else 'nominalSeries'
    pointer = f'/metrics/{key}/rows/{index}/value' if dim == 'total' and period == '2024' else f'/metrics/{key}/rows/{index}/{field}/values/{j}'
    value = row[field]['values'][j]
    ev = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer,
               historyReplay='public normalized cumulative series; no native intermediate-year income components')]
    ev.append(dict(refs[NIC], kind='price_snapshot', valuePointer=f'/comparisonIndex/{j}', period=period, territory='italy',
                   usage='national deflator' if dim == 'total' else 'context only; nominal observation is not deflated'))
    if period in ('2016', '2024'):
        ev.append(dict(refs[PANEL], kind='income_endpoint_snapshot', recordPointer=f'/municipalReconciliation/{code}',
                       components=panel['municipalReconciliation'][code][period], sourceDocument=panel['sources'][period],
                       replayScope='normalized complete endpoint panels; original MEF archives not replayed'))
    return dict(ctx, metric=key, dimension=dim, geography=code, period=period, value=value,
                source=metric['sourceUrl'], evidence=ev, provenance=ev, notApplicable=False, dataUnavailable=False), NOTES[:]


def benchmark(engine, key, scope, municipal):
    if scope not in scopes(key, municipal['dimension']): raise ValueError('real_income_benchmark_scope_not_reviewed')
    if municipal['period'] != '2024': raise ValueError('real_income_benchmark_only_2024')
    metric, panel, nic, refs = validated(engine, key)
    b = panel['benchmarks'][key]; value = b[scope]
    close(metric['meta']['benchmark'][scope], value)
    ev = [dict(refs[PANEL], kind='benchmark_snapshot', valuePointer=f'/benchmarks/{key}/{scope}',
               components=panel['raw'][scope],
               method='ratio of aggregate amount/frequency in 2016 and 2024, deflated by same national NIC; not mean of municipal growth rates; Italy includes unlocated record'),
          dict(refs[NIC], kind='price_snapshot', valuePointer='/comparisonIndex/8', period='2024', territory='italy')]
    return dict(context(metric,key,municipal['dimension']), metric=key, dimension=municipal['dimension'], geography=scope,
                period='2024', value=value, source=metric['sourceUrl'], evidence=ev, provenance=ev,
                notApplicable=False, dataUnavailable=False)
