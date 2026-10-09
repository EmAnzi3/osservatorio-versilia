"""Frozen tourism movement and capacity, with public precision and resident dates."""
import copy
import hashlib
import json
import math
import acquire_a3_benchmark_istat_tourism_annual as capacity
import acquire_a3_benchmark_regione_toscana_tourism_annual as movement
from semantic_operations import finite

ARRIVALS, PRESENCES, STAY, FOREIGN = MOVEMENT = ('tourismArrivals', 'tourismPresences', 'tourismAverageStay', 'foreignTourismShare')
BEDS, BED_RATE, STRUCTURE_RATE = CAPACITY = ('tourismBeds', 'tourismBedsPer1000', 'tourismStructuresPer1000')
KEYS = (*MOVEMENT, *CAPACITY)
MOVE = 'data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json'
CAP = 'data/source-snapshots/a3-istat-tourism-capacity-benchmark-2024.json'
DEMO = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
POSAS = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
MOVE_LANDING = 'https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0'
UNITS = dict(zip(KEYS, ('number', 'number', 'nights', 'percent', 'number', 'per1000', 'per1000')))
HASHES = {
 MOVE: ('f09c50bc3016cc2793eab4737c6dff1f625da67798b4c8b5c4dae16af2c8ac37', 'bc2b4f4f8a5233e7233e8ee92b5bc4a0102c36baf443efcd5a160114613cb2e8'),
 CAP: ('4e4dccca04b98ccf0fc51fa336cc93ce8541cb6ea06aba66e298e71c0ca0ab4f', '87ae1965473ec73c593202ff61c5b90e52671c189b35cb56cc3fbbc0435e07e7'),
 DEMO: ('63a5fdefa71a4484edd65f69d1a754ce4f291fd563f9683c76332635a145f943', '82ea7b47b6f4ca16d7c4a71cd1a6806d537aa75940ffbb4aa9dc1f79776acef3'),
 POSAS: ('8ec47305870a84cd0da4fd0b36dc0ee33693557cec4df0796f56d04f78bb68f7', '24713ad8f1ebeb3b588790973fa4909aa2151f1005b63342691e4129ca852a07'),
}


def fingerprint(s):
    return hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def frozen(engine, path):
    s, ref = engine.file(path)
    if (ref.get('sha256'), fingerprint(s)) != HASHES[path]: raise ValueError('tourism_frozen_input_changed')
    return s, ref


def close(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9): raise ValueError('tourism_public_native_mismatch')


def dimensions(key): return ['total', 'nativeRatio'] if key == FOREIGN else ['total']
def weighted(key, dim): return key in (STAY, BED_RATE, STRUCTURE_RATE) or key == FOREIGN and dim == 'nativeRatio'
def scopes(key, dim): return [] if dim == 'nativeRatio' else ['tuscany'] if key in MOVEMENT else ['tuscany', 'italy']
def history_available(key): return key in MOVEMENT or key == BEDS
def operations(key, dim): return [*(['absolute_change', 'relative_change', 'trend', 'correlation', 'anomaly'] if key == PRESENCES else []), 'compare', 'rank', *(['series'] if history_available(key) else []), *(['weighted_ratio'] if weighted(key, dim) else []), *(['benchmark_gap'] if scopes(key, dim) else [])]


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend') and key != PRESENCES: raise ValueError('tourism_temporal_continuity_not_reviewed')
    if op == 'series' and not history_available(key): raise ValueError('tourism_historical_resident_ratio_not_frozen')
    if op == 'correlation' and key != PRESENCES: raise ValueError('tourism_pair_not_jointly_reviewed')
    if op == 'anomaly' and key != PRESENCES: raise ValueError('tourism_peer_anomaly_not_reviewed')
    if op == 'weighted_ratio' and not weighted(key, dim): raise ValueError('tourism_native_ratio_dimension_required')
    if op == 'benchmark_gap' and not scopes(key, dim): raise ValueError('tourism_benchmark_dimension_not_reviewed')


def context(metric, key, dim):
    year = '2025' if key in MOVEMENT else '2024'
    if dim not in dimensions(key) or metric['meta'].get('year') != year or metric['meta'].get('unit') != UNITS[key] or metric.get('sourceUrl') != (MOVE_LANDING if key in MOVEMENT else capacity.LANDING): raise ValueError('tourism_definition_changed')
    definitions = {ARRIVALS: 'registered accommodation arrivals, not unique tourists', PRESENCES: 'registered accommodation nights', STAY: 'registered nights / registered arrivals', FOREIGN: 'foreign-resident nights / all registered nights × 100; ' + ('native unrounded ratio distinct from public rounded percentage' if dim == 'nativeRatio' else 'public municipal percentage rounded to one decimal'), BEDS: 'hotel + non-hotel beds, Istat 2024 scope', BED_RATE: 'Istat beds 2024 / Istat estimated residents 1 January 2026 × 1000', STRUCTURE_RATE: 'Istat accommodation structures 2024 / Istat estimated residents 1 January 2026 × 1000'}
    return dict(unit=UNITS[key], population='registered accommodation movement net of rentals; foreign means residence abroad, not citizenship' if key in MOVEMENT else 'Istat hotel and non-hotel capacity 2024; private non-business accommodation expansion 2025 excluded', definition=definitions[key], method='frozen source extraction and public reconciliation; numerical rank is not destination quality', frequency='annual', periodBasis='regional reference year; provisional until Istat publication' if key in MOVEMENT else 'capacity reference 2024; resident denominator estimated 1 January 2026' if key != BEDS else 'Istat capacity annual reference; 2025 scope excluded', adapter='tourism/' + key + '/' + dim + '/v1')


def identity(engine, metric):
    names = {t['code']: t['name'] for t in engine._catalog['towns']}
    rows = metric['rows']
    if len(rows) != len(names) or {r['code'] for r in rows} != set(names) or any(r.get('town') != names[r['code']] or r.get('slug') != '-'.join(r['town'].lower().split()) or r.get('notApplicable') or r.get('dataUnavailable') for r in rows): raise ValueError('tourism_municipal_identity_changed')


def move_value(key, dim, n):
    a, p, f = (n[k] for k in ('arrivals', 'presences', 'foreignPresences'))
    return {ARRIVALS: a, PRESENCES: p, STAY: p / a, FOREIGN: f / p * 100 if dim == 'nativeRatio' else round(f / p * 100, 1)}[key]


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; identity(engine, metric)
    path = MOVE if key in MOVEMENT else CAP
    s, ref = frozen(engine, path)
    population = engine._catalog['metrics']['population'] if key in CAPACITY else None
    # Fingerprint mutable cached inputs on every access; expensive full-panel checks once per exact catalog state.
    signature = fingerprint([metric, population])
    cache = getattr(engine, '_tourism_validation', {})
    if key in CAPACITY:
        demo, _ = frozen(engine, DEMO); posas, _ = frozen(engine, POSAS)
        identity(engine, population)
        if population['meta']['year'] != '2026' or population['meta']['unit'] != 'number': raise ValueError('tourism_resident_basis_changed')
        for row in population['rows']:
            stocks = [n for n in posas['posas']['towns'][row['town']] if n['year'] == 2026]
            if len(stocks) != 1: raise ValueError('tourism_resident_basis_changed')
            close(row['value'], stocks[0]['population'])
        if s['population']['sha256'] != HASHES[DEMO][0] or demo['benchmarks']['population']['year'] != '2026': raise ValueError('tourism_resident_basis_changed')
    if cache.get(key) != signature:
        candidate = copy.deepcopy(metric)
        try:
            if key in MOVEMENT:
                movement.apply_movement_history(candidate, s)
            else:
                capacity.validate_snapshot(metric, s, population)
                if key == BEDS: capacity.apply_capacity_history(candidate, s)
        except RuntimeError as exc:
            raise ValueError('tourism_native_panel_or_history_changed') from exc
        # Existing source series can be partial; every published point must agree, with no inferred missing year.
        for holder, full in zip([*metric['rows'], metric['aggregate']], [*candidate['rows'], candidate['aggregate']]):
            series = holder.get('series')
            if series:
                native = full['series']
                if len(series['years']) != len(series['values']) or len(set(series['years'])) != len(series['years']): raise ValueError('tourism_public_series_changed')
                for y, v in zip(series['years'], series['values']):
                    if y not in native['years']: raise ValueError('tourism_public_series_changed')
                    close(v, native['values'][native['years'].index(y)])
                for field in ('sourceSnapshot', 'sourceUrl'):
                    if field in series and series[field] != native[field]: raise ValueError('tourism_public_series_changed')
        if key in (BED_RATE, STRUCTURE_RATE):
            close(metric['aggregate']['value'], sum(r[5 if key == STRUCTURE_RATE else 4] for r in s['records'] if r[0] in engine.codes) / sum(r['value'] for r in population['rows']) * 1000)
        cache[key] = signature; engine._tourism_validation = cache
    return s, ref


def available_periods(engine, key, dim, row):
    if not history_available(key): raise ValueError('tourism_historical_resident_ratio_not_frozen')
    s, _ = validated(engine, key)
    return [str(y) for y in s['municipalMovementHistory' if key in MOVEMENT else 'municipalBedsHistory']['years']]


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; row = metric['rows'][index]; ctx = context(metric, key, dim)
    if period != metric['meta']['year'] and not history_available(key): raise ValueError('tourism_period_not_frozen')
    s, ref = validated(engine, key); code = row['code']; num = den = scale = None; extra = {}
    pointer = f'/metrics/{key}/rows/{index}/value'; refs = []
    warnings = ['tourism_frozen_extraction_not_new_live_acquisition', 'tourism_numerical_rank_not_destination_quality']
    if key in MOVEMENT:
        h = s['municipalMovementHistory']
        if period not in h['countsByYear']: raise ValueError('tourism_period_not_frozen')
        n = h['countsByYear'][period][code]; value = move_value(key, dim, n)
        base = '/municipalMovementHistory/countsByYear/' + period + '/' + code
        source = h['sources'][period]['url']; extra.update(recordPointer=base, sourceFileSha256=h['sources'][period]['sha256'], sourceFileBytes=h['sources'][period]['bytes'])
        if key == STAY: num, den, scale = n['presences'], n['arrivals'], 1
        if key == FOREIGN and dim == 'nativeRatio': num, den, scale = n['foreignPresences'], n['presences'], 100
        if num is not None: extra.update(numeratorPointer=base + ('/foreignPresences' if key == FOREIGN else '/presences'), denominatorPointer=base + ('/presences' if key == FOREIGN else '/arrivals'))
        warnings += ['tourism_existing_presences_operations_preserved'] if key == PRESENCES else []
        warnings += ['tourism_movement_net_of_rentals_provisional', 'tourism_arrivals_not_unique_people']
        if key == FOREIGN: warnings += ['tourism_public_foreign_share_one_decimal_and_versilia_rounded_weighting', *(['tourism_native_foreign_ratio_distinct_from_public_value'] if dim == 'nativeRatio' else [])]
    else:
        source = s['source']['archiveUrl']; record_index = next(i for i, n in enumerate(s['records']) if n[0] == code); n = s['records'][record_index]
        base = f'/records/{record_index}'; extra.update(recordPointer=base, archiveMember=s['source']['archiveMember'], archiveSha256=s['source']['archiveSha256'], workbookSha256=s['source']['workbookSha256'])
        if key == BEDS:
            h = s['municipalBedsHistory']
            if int(period) not in h['years']: raise ValueError('tourism_period_not_frozen')
            value = h['valuesByCode'][code][h['years'].index(int(period))]; extra.update(valuePointer='/municipalBedsHistory/valuesByCode/' + code + '/' + str(h['years'].index(int(period))))
        else:
            pop_index = next(i for i, r in enumerate(engine._catalog['metrics']['population']['rows']) if r['code'] == code)
            den = engine._catalog['metrics']['population']['rows'][pop_index]['value']; num = n[5 if key == STRUCTURE_RATE else 4]; scale = 1000; value = num / den * scale
            _, pref = frozen(engine, POSAS)
            refs.append(dict(pref, kind='denominator_snapshot', recordPointer='/posas/towns/' + row['town'], period='2026-01-01', sourceUrl='https://demo.istat.it/'))
            extra.update(numeratorPointer=base + ('/5' if key == STRUCTURE_RATE else '/4'), denominatorSnapshot=POSAS, denominatorPointer='/posas/towns/' + row['town'])
            sm = metric['meta'].get('sourceMeta', {})
            if sm.get('snapshot') != CAP or sm.get('populationSnapshot') != DEMO: raise ValueError('tourism_resident_basis_changed')
            warnings += ['tourism_capacity_2024_residents_2026_distinct', 'tourism_posas_2026_estimate']
        warnings += ['tourism_capacity_2025_scope_expansion_excluded', 'tourism_native_7899_municipal_records_not_new_workbook_replay']
    if dim == 'total' and period == metric['meta']['year']: close(row['value'], value)
    elif dim == 'nativeRatio':
        # The catalog has no unrounded cell: point explicitly to the source components.
        pointer = f'/metrics/{key}/rows/{index}'
    else:
        series = row.get('series')
        if series and int(period) in series['years']: pointer = f'/metrics/{key}/rows/{index}/series/values/{series["years"].index(int(period))}'
        else: pointer = f'/metrics/{key}/rows/{index}'
    ev = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer), dict(ref, kind='source_snapshot', sourceUrl=source, **extra), *refs]
    result = dict(ctx, metric=key, dimension=dim, geography=code, period=period, value=value, source=source, evidence=ev, provenance=ev, notApplicable=False, dataUnavailable=False)
    if num is not None: result.update(numerator=num, denominator=den, scale=scale, numeratorPeriod=period, denominatorPeriod='2026-01-01' if key in (BED_RATE, STRUCTURE_RATE) else period)
    return result, warnings


def benchmark(engine, key, scope, municipal):
    if scope not in scopes(key, municipal['dimension']) or municipal['period'] != ('2025' if key in MOVEMENT else '2024'): raise ValueError('tourism_benchmark_scope_or_period_not_reviewed')
    s, ref = validated(engine, key); b = s['benchmarks'][key]; meta = engine._catalog['metrics'][key]['meta']['benchmark']; path = MOVE if key in MOVEMENT else CAP
    if meta.get('sourceSnapshot') != path or meta.get('year') != b['year'] or meta.get('url') != s['sourceUrl'] or b['unit'] != municipal['unit']: raise ValueError('tourism_benchmark_definition_changed')
    close(meta[scope], b[scope]); ev = [dict(ref, kind='benchmark_snapshot', valuePointer='/benchmarks/' + key + '/' + scope, method='frozen published regional benchmark; native regional components not embedded' if key in MOVEMENT else 'native 7899 municipality panel, province/national totals excluded from sums; Tuscany 273; ratios use population 2026')]
    if key in (BED_RATE, STRUCTURE_RATE):
        _, dref = frozen(engine, DEMO); ev.append(dict(dref, kind='denominator_snapshot', valuePointer='/benchmarks/population/' + scope, period='2026-01-01'))
    return dict({k: municipal[k] for k in ('metric', 'dimension', 'unit', 'population', 'definition', 'method', 'frequency', 'periodBasis', 'adapter', 'period')}, geography=scope, value=b[scope], source=s['sourceUrl'], evidence=ev, provenance=ev, notApplicable=False, dataUnavailable=False)
