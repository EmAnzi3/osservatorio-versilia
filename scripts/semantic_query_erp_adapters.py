"""ERP Lucca cumulative accounting: public rounding and native ratios separate."""
import math
from materialize_erp_arrears_v125 import build_metric
from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('erpArrears',)
PATH = 'data/source-snapshots/erp-lucca-arrears-2020-2024.json'
HASH = 'cbaf36702a95054797ab96d259549eb76b4caee0c750187df3c91be7a008c661'
FINGERPRINT = '5b01c3efcaf83d085e79a5cee9e21303423e0ca7d3b78982d98c67324aaaf164'
YEARS = [2020, 2021, 2022, 2023, 2024]
NOTES = ['erp_cumulative_accounting_not_annual_unpaid_rent_or_household_share',
         'erp_snapshot_reconciled_original_balance_sheet_pdfs_not_replayed',
         'erp_2022_header_mismatch_2023_printed_percentages_not_used',
         'erp_massarosa_2023_issued_discontinuity_retained_no_interpolation',
         'erp_no_automatic_causal_quality_or_policy_priority_inference']


def dimensions(key): return ['total', 'nativeRatio']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank', 'series'] + (['weighted_ratio'] if dim == 'nativeRatio' else [])


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('erp_accounting_continuity_not_attested_for_temporal_analysis')
    if op == 'weighted_ratio' and dim != 'nativeRatio': raise ValueError('erp_native_ratio_dimension_required')
    if op == 'benchmark_gap': raise ValueError('erp_geographic_benchmark_not_frozen')
    if op == 'correlation': raise ValueError('erp_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('erp_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key) or metric['meta'].get('key') != key:
        raise ValueError('erp_definition_changed')
    return dict(unit='percent', population='ERP Lucca municipal cumulative billed amounts for rent and ancillary expenses',
                definition='cumulative arrears / cumulative issued amounts × 100',
                method='public two-decimal rate from frozen four-decimal rate' if dim == 'total' else 'native euro amounts, no reverse derivation from rounded rate',
                frequency='annual_cumulative_accounting_snapshot', periodBasis='financial exercise; cumulative billed and uncollected euro amounts for same municipality and year',
                nativeComponentsAvailable=dim == 'nativeRatio', adapter='erp/'+key+'/'+dim+'/v1')


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-8):
        raise ValueError('erp_accounting_reconciliation_changed')


def validated(engine, key):
    snap, ref = engine.file(PATH)
    if ref.get('path') != PATH or ref.get('sha256') != HASH or fingerprint(snap) != FINGERPRINT:
        raise ValueError('erp_frozen_input_changed')
    towns = engine._catalog['towns']
    if len(towns) != 7 or {t['code']:t['name'] for t in towns} != TOWNS:
        raise ValueError('erp_municipal_identity_changed')
    # Reconcile full public definition, components, series and aggregate.
    if fingerprint(engine._catalog['metrics'][key]) != fingerprint(build_metric(snap)):
        raise ValueError('erp_catalog_native_reconciliation_changed')
    for j, year in enumerate(YEARS):
        for code, name in TOWNS.items():
            r = snap['rows'][code]; cell = r['values'][j]
            if r['town'] != name or cell['year'] != year or not finite(cell['issued']) or cell['issued'] <= 0 or not finite(cell['arrears']) or cell['arrears'] < 0:
                raise ValueError('erp_accounting_domain_changed')
            equal(cell['rate'], round(cell['arrears']/cell['issued']*100, 4))
        agg = snap['aggregate']['values'][j]
        equal(agg['issued'], round(math.fsum(snap['rows'][c]['values'][j]['issued'] for c in TOWNS), 2))
        equal(agg['arrears'], round(math.fsum(snap['rows'][c]['values'][j]['arrears'] for c in TOWNS), 2))
        equal(agg['rate'], round(agg['arrears']/agg['issued']*100, 4))
    return snap, ref


def available_periods(engine, key, dim, row):
    validated(engine, key)
    return [str(y) for y in YEARS]


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref = validated(engine, key)
    if period not in [str(y) for y in YEARS]: raise ValueError('erp_period_not_frozen')
    row = metric['rows'][index]; code = row['code']; j = YEARS.index(int(period)); cell = snap['rows'][code]['values'][j]
    public = round(cell['rate'], 2); native = cell['arrears']/cell['issued']*100
    pointer = f'/metrics/{key}/rows/{index}/value' if period == '2024' else f'/metrics/{key}/rows/{index}/series/values/{j}'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer, publishedPrecision='two decimals', nativeRatioSeparate=dim == 'nativeRatio'),
                dict(ref, kind='source_snapshot', recordPointer=f'/rows/{code}/values/{j}', nativeComponents=dict(numerator=cell['arrears'], denominator=cell['issued'], scale=100), sourceDocument=snap['sourceDocuments'][j], replayScope='normalized accounting snapshot reconciled; original PDF not replayed')]
    result = dict(ctx, metric=key, dimension=dim, geography=code, period=period, value=public if dim == 'total' else native,
                  source=snap['sourcePageUrl'], evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=False, missingReason=None)
    if dim == 'nativeRatio': result.update(numerator=cell['arrears'], denominator=cell['issued'], scale=100, numeratorPeriod=period, denominatorPeriod=period)
    return result, NOTES[:]
