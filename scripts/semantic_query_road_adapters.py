"""Istat road measures and DAIT nominal proceeds, with distinct denominators."""
import math

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

SAFETY, FINES = KEYS = ('roadSafety', 'roadFinesPerResident')
NATIVE = 'data/source-snapshots/sicurezza-territorio-draft-2026-08.json'
CANONICAL = 'data/site-data.json'
HASHES = {NATIVE: ('3fa39838392f75bf4642298929123093eee189419bbaf38e422d4569fc870bcf',
                  'f8d26ae2375505e7d2d2329724fbb24b4e72680cc19bc4ad40d60d57fdcd7db9')}
CANONICAL_HASH = '2a1f1ba0ee2ba4de98e12c00fe7e09c6a30d6edca2505f12587aefde1889a12b'
INJURED_HASH = '9ef9463e4e14141e57626190033d0e4dc397d0d27d132e5110ffd0102c6bc6d8'
INCIDENTS, MORTALITY, INJURY, INJURED = VIEWS = ('measure:incidents', 'measure:mortality', 'measure:injury', 'measure:injured')
# field, public selector, public label, unit, denominator universe
SPECS = {
 INCIDENTS: ('roadIncidentRate', 'Incidenti', 'Incidenti con lesioni', 'per1000', 'annual average resident population; incidents localized to municipality'),
 MORTALITY: ('roadMortalityIndex', 'Mortalità', 'Indice di mortalità', 'per100', 'incidents with injuries; deaths per 100 incidents'),
 INJURY: ('roadInjuryIndex', 'Lesività', 'Indice di lesività', 'per100', 'incidents with injuries; injured persons per 100 incidents'),
 INJURED: (None, 'Feriti', 'Feriti ogni 10.000 residenti', 'per10k', 'resident population in legacy Istat rate; injured persons localized to accident municipality'),
}
URLS = {SAFETY: 'https://www.istat.it/storage/misura-comune/15a-Infrastrutture-e-mobilita-incidenti-stradali.xlsx',
         FINES: 'https://www.istat.it/storage/misura-comune/15c-Infrastrutture-e-mobilita-per-tassi-di-motorizzazione-e-proventi-dalle-sanzioni.xlsx'}
FORMULAS = {
 SAFETY: 'Incidentalità: incidenti con lesioni / popolazione residente media × 1.000; mortalità: morti / incidenti × 100; lesività: feriti / incidenti × 100; feriti: feriti / residenti × 10.000.',
 FINES: 'Proventi complessivi rendicontati per violazioni al Codice della strada / popolazione residente media.'}
NOTES = ['road_published_rates_no_reverse_derived_counts_or_denominators',
         'road_municipal_mean_not_pooled_versilia_rate',
         'road_temporal_continuity_and_pairs_not_reviewed',
         'road_traffic_tourism_and_small_counts_preclude_automatic_policy_ranking']


def view(key, dim): return INCIDENTS if key == SAFETY and dim == 'total' else dim
def dimensions(key): return ['total', *VIEWS] if key == SAFETY else ['total']
def years(key, dim): return list(range(2021, 2025)) if key == FINES else list(range(2020, 2025)) if view(key, dim) == INJURED else list(range(2014, 2025))
def scopes(key, dim): return [] if key == SAFETY and view(key, dim) == INJURED else ['tuscany', 'italy']
def operations(key, dim): return ['compare', 'rank', 'series'] + (['benchmark_gap'] if scopes(key, dim) else [])


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('road_temporal_continuity_not_reviewed')
    if op == 'weighted_ratio': raise ValueError('road_native_counts_and_denominators_not_frozen')
    if op == 'correlation': raise ValueError('road_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('road_peer_anomaly_not_reviewed')
    if op == 'benchmark_gap' and not scopes(key, dim): raise ValueError('road_injured_benchmark_not_frozen')


def equal(actual, expected):
    if not finite(actual) or not finite(expected) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('road_public_frozen_mismatch')


def frozen(engine):
    snap, ref = engine.file(NATIVE)
    if ref.get('path') != NATIVE or (ref.get('sha256'), fingerprint(snap)) != HASHES[NATIVE]:
        raise ValueError('road_frozen_input_changed')
    return snap, ref


def context(metric, key, dim):
    meta = metric['meta']
    if (dim not in dimensions(key) or meta.get('key') != key or str(meta.get('year')) != '2024'
            or meta.get('theme') != 'sicurezza' or meta.get('unit') != ('per1000' if key == SAFETY else 'currency')
            or meta.get('polarity') != ('negative' if key == SAFETY else 'neutral')
            or metric.get('sourceUrl') != URLS[key] or metric.get('method', {}).get('formula') != FORMULAS[key]
            or metric['method'].get('coverage') != '7/7'
            or key == SAFETY and meta.get('compositeType') != 'securityMeasures'):
        raise ValueError('road_definition_changed')
    if key == FINES:
        unit, population, definition = 'currency', 'annual average resident population', 'nominal total DAIT reported road-code proceeds / annual average resident population'
    else:
        field, selector, label, unit, population = SPECS[view(key, dim)]
        definition = label + '; ' + population
    return dict(unit=unit, population=population, definition=definition,
                method='direct published rate; municipal mean is descriptive, native counts/denominators not embedded',
                frequency='annual', periodBasis='reference year of Istat observation, distinct from acquisition/publication',
                nativeComponentsAvailable=False, adapter='road/' + key + '/v1')


def published_series(series):
    cells = [(y, v) for y, v in zip(series['years'], series['values']) if v is not None]
    return dict(years=[y for y, _ in cells], values=[v for _, v in cells])


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    snap, ref = frozen(engine)
    rows = metric['rows']
    if (len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS)
            or {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS
            or set(snap['towns']) != set(TOWNS.values())):
        raise ValueError('road_municipal_identity_changed')
    canonical, source_ref = engine.file(CANONICAL)
    if source_ref.get('path') != CANONICAL or source_ref.get('sha256') != CANONICAL_HASH:
        raise ValueError('road_legacy_canonical_carrier_changed')
    legacy = canonical['metrics'][SAFETY]['rows']
    injured = {r['code']: r['componentSeries']['Feriti'] for r in legacy}
    if len(legacy) != 7 or set(injured) != set(TOWNS) or fingerprint(injured) != INJURED_HASH:
        raise ValueError('road_legacy_canonical_carrier_changed')
    for row in rows:
        code = row['code']; name = TOWNS[code]; raw = snap['towns'][name]
        if (row.get('town') != name or row.get('slug') != '-'.join(name.lower().split()) or raw.get('code') != code
                or row.get('notApplicable') or row.get('dataUnavailable')
                or any(row.get(k) is not None for k in ('normalized', 'ratioComponents'))):
            raise ValueError('road_municipal_row_changed')
        if key == FINES:
            series = raw['roadFinesPerResident']
            if series['years'] != years(key, 'total') or len(series['values']) != 4 or any(v is not None and (not finite(v) or v < 0) for v in series['values']):
                raise ValueError('road_native_periods_or_values_changed')
            if row.get('series') != series: raise ValueError('road_public_history_changed')
            equal(row.get('value'), series['values'][-1]); equal(row.get('benchmarkValue'), series['values'][-1])
        else:
            if len(row.get('parts', [])) != 4 or set(row.get('componentSeries', {})) != {s[1] for s in SPECS.values()}:
                raise ValueError('road_public_components_changed')
            for j, dim in enumerate(VIEWS):
                field, selector, label, unit, _ = SPECS[dim]
                series = injured[code] if dim == INJURED else raw[field]
                if series['years'] != years(key, dim) or len(series['values']) != len(series['years']) or any(v is not None and (not finite(v) or v < 0) for v in series['values']):
                    raise ValueError('road_native_periods_or_values_changed')
                if row['componentSeries'][selector] != published_series(series): raise ValueError('road_public_history_changed')
                part = row['parts'][j]
                if part.get('label') != label or part.get('selectorLabel') != selector or part.get('unit') != unit:
                    raise ValueError('road_public_components_changed')
                equal(part.get('value'), series['values'][-1])
            if row.get('series') != published_series(raw['roadIncidentRate']): raise ValueError('road_public_history_changed')
            equal(row.get('value'), raw['roadIncidentRate']['values'][-1]); equal(row.get('benchmarkValue'), row['value'])
    aggregate = metric.get('aggregate') or {}
    if aggregate.get('label') != 'Media semplice dei 7 comuni' or metric.get('normalizedAggregate') is not None:
        raise ValueError('road_aggregate_definition_changed')
    equal(aggregate.get('value'), math.fsum(r['value'] for r in rows)/7)
    if key == SAFETY:
        if len(aggregate.get('parts', [])) != 4: raise ValueError('road_aggregate_definition_changed')
        for j, dim in enumerate(VIEWS):
            p = aggregate['parts'][j]; spec = SPECS[dim]
            if p.get('label') != spec[2] or p.get('selectorLabel') != spec[1] or p.get('unit') != spec[3]:
                raise ValueError('road_aggregate_definition_changed')
            equal(p.get('value'), math.fsum(r['parts'][j]['value'] for r in rows)/7)
    bench = metric['meta'].get('benchmark') or {}; field = 'roadIncidentRate' if key == SAFETY else FINES
    if bench.get('year') != 2024 or bench.get('url') != URLS[key]: raise ValueError('road_benchmark_definition_changed')
    for scope in ('tuscany', 'italy'): equal(bench.get(scope), snap['benchmarks'][field][scope])
    return snap, ref, injured, source_ref


def available_periods(engine, key, dim, row):
    validated(engine, key)
    return list(map(str, years(key, dim)))


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref, injured, source_ref = validated(engine, key); row = metric['rows'][index]
    if period not in list(map(str, years(key, dim))) or not historical and period != '2024':
        raise ValueError('road_period_not_frozen')
    i = years(key, dim).index(int(period)); notes = NOTES[:]
    if key == FINES:
        series = snap['towns'][row['town']][FINES]; cat_pointer = f'/metrics/{key}/rows/{index}/series/values/{i}' if historical else f'/metrics/{key}/rows/{index}/value'
        native_pointer = f'/towns/{row["town"]}/{FINES}/values/{i}'
        source = dict(ref, kind='source_snapshot', recordPointer=native_pointer, workbookSha256=snap['sources']['istat15c']['sha256'])
        notes += ['road_fines_nominal_proceeds_not_number_of_fines_control_intensity_or_safety', 'road_speed_fine_share_intentionally_unpublished']
    else:
        selected = view(key, dim); field, selector, label, unit, _ = SPECS[selected]
        series = injured[row['code']] if selected == INJURED else snap['towns'][row['town']][field]
        public_years = row['componentSeries'][selector]['years']
        if historical:
            cat_pointer = f'/metrics/{key}/rows/{index}/componentSeries/{selector}'
            if int(period) in public_years: cat_pointer += f'/values/{public_years.index(int(period))}'
            else: notes += ['road_missing_native_cell_omitted_from_public_series_not_zero']
        else: cat_pointer = f'/metrics/{key}/rows/{index}/parts/{VIEWS.index(selected)}/value'
        if selected == INJURED:
            j = next(j for j, r in enumerate(engine.file(CANONICAL)[0]['metrics'][SAFETY]['rows']) if r['code'] == row['code'])
            source = dict(source_ref, kind='canonical_legacy_carrier', recordPointer=f'/metrics/{SAFETY}/rows/{j}/componentSeries/Feriti/values/{i}', limits='published canonical legacy Istat rate only; original workbook and native counts not frozen here')
            notes += ['road_injured_legacy_canonical_rate_no_raw_workbook_replay']
        else:
            source = dict(ref, kind='source_snapshot', recordPointer=f'/towns/{row["town"]}/{field}/values/{i}', workbookSha256=snap['sources']['istat15a']['sha256'])
        notes += ['road_accident_location_not_injured_residence_or_resident_risk', 'road_mortality_and_injury_indices_per100_incidents_not_population_percentages']
    source.update(sourceUrl=URLS[key], referenceYear=int(period))
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=cat_pointer), source]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=series['values'][i],
                source=URLS[key], evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=series['values'][i] is None, missingReason='frozen_official_cell_missing_no_zero_or_interpolation' if series['values'][i] is None else None), notes


def benchmark(engine, key, scope, municipal):
    dim = municipal['dimension']
    if scope not in scopes(key, dim) or municipal['period'] != '2024':
        raise ValueError('road_benchmark_scope_or_period_not_reviewed')
    snap, ref, _, _ = validated(engine, key)
    field = FINES if key == FINES else SPECS[view(key, dim)][0]
    source_id = 'istat15c' if key == FINES else 'istat15a'
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/benchmarks/{field}/{scope}', workbookSha256=snap['sources'][source_id]['sha256'])]
    return dict(municipal, geography=scope, value=snap['benchmarks'][field][scope], evidence=evidence, provenance=evidence,
                benchmarkAggregation='official published Istat scope row; parsed frozen values with workbook hash, no workbook or underlying national panel replay')
