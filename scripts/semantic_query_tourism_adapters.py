"""Frozen tourism movement and capacity, with public precision and resident dates."""
from a6_pins import Pin as _pin
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
CAP = capacity.latest_snapshot()
CAP_YEAR = int(CAP[-9:-5])
# From 2025 the Istat scope includes private non-business accommodation: no history across the break.
CAP_HISTORY = CAP_YEAR == 2024
CAP_RECORDS = len(json.loads((capacity.ROOT / CAP).read_text(encoding='utf-8'))['records'])
DEMO = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
POSAS = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
MOVE_LANDING = 'https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0'
UNITS = dict(zip(KEYS, ('number', 'number', 'nights', 'percent', 'number', 'per1000', 'per1000')))
HASHES = {
 MOVE: (_pin('tourism#1'), _pin('tourism#2')),
 CAP: (_pin('tourism#3'), _pin('tourism#4')),
 DEMO: (_pin('tourism#5'), _pin('tourism#6')),
 POSAS: (_pin('tourism#7'), _pin('tourism#8')),
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
def history_available(key): return key in MOVEMENT or key == BEDS and CAP_HISTORY
def operations(key, dim): return [*(['absolute_change', 'relative_change', 'trend', 'correlation', 'anomaly'] if key == PRESENCES else []), 'compare', 'rank', *(['series'] if history_available(key) else []), *(['weighted_ratio'] if weighted(key, dim) else []), *(['benchmark_gap'] if scopes(key, dim) else [])]


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend') and key != PRESENCES: raise ValueError('tourism_temporal_continuity_not_reviewed')
    if op == 'series' and not history_available(key): raise ValueError('tourism_historical_resident_ratio_not_frozen')
    if op == 'correlation' and key != PRESENCES: raise ValueError('tourism_pair_not_jointly_reviewed')
    if op == 'anomaly' and key != PRESENCES: raise ValueError('tourism_peer_anomaly_not_reviewed')
    if op == 'weighted_ratio' and not weighted(key, dim): raise ValueError('tourism_native_ratio_dimension_required')
    if op == 'benchmark_gap' and not scopes(key, dim): raise ValueError('tourism_benchmark_dimension_not_reviewed')


def context(metric, key, dim):
    year = '2025' if key in MOVEMENT else str(CAP_YEAR)
    if dim not in dimensions(key) or metric['meta'].get('year') != year or metric['meta'].get('unit') != UNITS[key] or metric.get('sourceUrl') != (MOVE_LANDING if key in MOVEMENT else capacity.LANDING): raise ValueError('tourism_definition_changed')
    definitions = {ARRIVALS: 'registered accommodation arrivals, not unique tourists', PRESENCES: 'registered accommodation nights', STAY: 'registered nights / registered arrivals', FOREIGN: 'foreign-resident nights / all registered nights × 100; ' + ('native unrounded ratio distinct from public rounded percentage' if dim == 'nativeRatio' else 'public municipal percentage rounded to one decimal'), BEDS: f'hotel + non-hotel beds, Istat {CAP_YEAR} scope', BED_RATE: f'Istat beds {CAP_YEAR} / Istat estimated residents 1 January 2026 × 1000', STRUCTURE_RATE: f'Istat accommodation structures {CAP_YEAR} / Istat estimated residents 1 January 2026 × 1000'}
    return dict(unit=UNITS[key], population='registered accommodation movement net of rentals; foreign means residence abroad, not citizenship' if key in MOVEMENT else ('Istat hotel and non-hotel capacity 2024; private non-business accommodation expansion 2025 excluded' if CAP_HISTORY else f'Istat hotel, non-hotel and private non-business accommodation capacity {CAP_YEAR}; not comparable with 2024 and earlier'), definition=definitions[key], method='frozen source extraction and public reconciliation; numerical rank is not destination quality', frequency='annual', periodBasis='regional reference year; provisional until Istat publication' if key in MOVEMENT else f'capacity reference {CAP_YEAR}; resident denominator estimated 1 January 2026' if key != BEDS else ('Istat capacity annual reference; 2025 scope excluded' if CAP_HISTORY else f'Istat capacity reference {CAP_YEAR}; widened scope, no series'), adapter='tourism/' + key + '/' + dim + '/v1')


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
        if key == BEDS and not CAP_HISTORY:
            if period != str(CAP_YEAR): raise ValueError('tourism_period_not_frozen')
            value = n[4]; extra.update(valuePointer=base + '/4')
        elif key == BEDS:
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
            warnings += [f'tourism_capacity_{CAP_YEAR}_residents_2026_distinct', 'tourism_posas_2026_estimate']
        warnings += ['tourism_capacity_2025_scope_expansion_excluded' if CAP_HISTORY else f'tourism_capacity_{CAP_YEAR}_scope_includes_private_non_business_not_comparable', f'tourism_native_{CAP_RECORDS}_municipal_records_not_new_workbook_replay']
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
    if scope not in scopes(key, municipal['dimension']) or municipal['period'] != ('2025' if key in MOVEMENT else str(CAP_YEAR)): raise ValueError('tourism_benchmark_scope_or_period_not_reviewed')
    s, ref = validated(engine, key); b = s['benchmarks'][key]; meta = engine._catalog['metrics'][key]['meta']['benchmark']; path = MOVE if key in MOVEMENT else CAP
    if meta.get('sourceSnapshot') != path or meta.get('year') != b['year'] or meta.get('url') != s['sourceUrl'] or b['unit'] != municipal['unit']: raise ValueError('tourism_benchmark_definition_changed')
    close(meta[scope], b[scope]); ev = [dict(ref, kind='benchmark_snapshot', valuePointer='/benchmarks/' + key + '/' + scope, method='frozen published regional benchmark; native regional components not embedded' if key in MOVEMENT else f'native {CAP_RECORDS} municipality panel, province/national totals excluded from sums; Tuscany 273; ratios use population 2026')]
    if key in (BED_RATE, STRUCTURE_RATE):
        _, dref = frozen(engine, DEMO); ev.append(dict(dref, kind='denominator_snapshot', valuePointer='/benchmarks/population/' + scope, period='2026-01-01'))
    return dict({k: municipal[k] for k in ('metric', 'dimension', 'unit', 'population', 'definition', 'method', 'frequency', 'periodBasis', 'adapter', 'period')}, geography=scope, value=b[scope], source=s['sourceUrl'], evidence=ev, provenance=ev, notApplicable=False, dataUnavailable=False)
