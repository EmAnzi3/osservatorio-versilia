"""Reviewed water volumes and frozen ISPRA waste carriers; no invented weights."""
import math

from semantic_operations import finite

WATER = 'waterNetworkLosses'
WASTE = ('recycling', 'wastePerResident', 'residualWaste', 'wasteServiceCost')
KEYS = (WATER, *WASTE)
RATIOS = (WATER,)
CANONICAL = 'data/site-data.json'
WATER_PATH = 'data/source-snapshots/ambiente-acqua-v124-data.json'
WATER_BENCHMARK = 'data/source-snapshots/a3-istat-water-benchmark-2018.json'
WASTE_BENCHMARK = 'data/source-snapshots/a3-ispra-environment-benchmark-2024-v2.json'
COST_BENCHMARK = 'data/source-snapshots/a3-ispra-environment-benchmark-2024.json'
COST_PATH = 'data/source-snapshots/costi-fiscalita-validated-2026-08.json'
WATER_URL = 'https://esploradati.istat.it/'
WASTE_URL = 'https://www.catasto-rifiuti.isprambiente.it/index.php?pg=findComune'
COST_URL = 'https://www.catasto-rifiuti.isprambiente.it/index.php?pg=costicomuneproc&reg1=Toscana&regid=09&regid2=09'
UNITS = {WATER: 'percent', 'recycling': 'percent', 'wastePerResident': 'kg',
         'residualWaste': 'kg', 'wasteServiceCost': 'eurPerResident'}


def close(actual, expected, tolerance=1e-8):
    if not finite(actual) or not finite(expected) or not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError('environment_catalog_source_mismatch')


def context(metric, key, dimension):
    if dimension != 'total':
        raise ValueError('environment_dimension_not_reviewed')
    year = '2018' if key == WATER else '2024'
    source = WATER_URL if key == WATER else COST_URL if key == 'wasteServiceCost' else WASTE_URL
    if metric['meta'].get('unit') != UNITS[key] or str(metric['meta'].get('year')) != year or metric.get('sourceUrl') != source:
        raise ValueError('environment_definition_or_reference_changed')
    definitions = {
        WATER: '(water input - authorized delivered water) / water input * 100',
        'recycling': 'official municipal separate collection share of urban waste; published precision',
        'wastePerResident': 'official rounded municipal urban waste kg per resident; not visitor production',
        'residualWaste': 'published urban waste kg per resident * (1 - published separate collection share / 100)',
        'wasteServiceCost': 'official CTOTab euro per inhabitant; municipality count = 1; not household TARI',
    }
    if key == 'residualWaste' and metric.get('method', {}).get('formula') != 'rifiuto urbano totale pro capite × (1 - quota raccolta differenziata)':
        raise ValueError('environment_residual_formula_changed')
    return dict(unit=UNITS[key], population='municipal distribution network water volumes' if key == WATER else 'municipal urban waste accounting; resident normalization is not individual consumption',
                definition=definitions[key], method='Istat frozen municipal input/delivered volume pairs' if key == WATER else 'ISPRA frozen published municipal carrier; raw additive waste quantities not frozen',
                frequency='irregular' if key == WATER else 'annual',
                periodBasis='water census calendar year' if key == WATER else 'waste reporting calendar year; historical methodological continuity not independently attested',
                adapter='environment/' + key + '/v1')


def available_periods(engine, key, dimension, row):
    series = row.get('series')
    if not isinstance(series, dict):
        raise ValueError('environment_series_not_available')
    years = list(map(str, series.get('years', [])))
    if not years or len(years) != len(set(years)) or len(years) != len(series.get('values', [])):
        raise ValueError('environment_series_identity_changed')
    return sorted(years, key=int)


def selection_guard(key, operation):
    if key in WASTE and operation in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('environment_waste_historical_comparability_not_attested')


def correlation_guard(observations, axis):
    if axis == 'periods' and any(o['metric'] in WASTE for o in observations):
        raise ValueError('environment_waste_historical_comparability_not_attested')


def published(engine, key, row, period):
    source, ref = engine.file(CANONICAL)
    metric = source['metrics'][key]
    context(metric, key, 'total')
    found = [(i, r) for i, r in enumerate(metric['rows']) if r['code'] == row['code']]
    if len(found) != 1 or found[0][1]['town'] != row['town']:
        raise ValueError('environment_source_identity_changed')
    i, native = found[0]
    years = available_periods(engine, key, 'total', native)
    if period not in years:
        raise ValueError('environment_native_period_not_frozen')
    j = list(map(str, native['series']['years'])).index(period)
    value = native['series']['values'][j]
    if period == str(metric['meta']['year']) and native.get('value') is not None:
        close(native['value'], value)
    return value, dict(ref, kind='frozen_published_carrier',
                       valuePointer=f'/metrics/{key}/rows/{i}/series/values/{j}',
                       periodPointer=f'/metrics/{key}/rows/{i}/series/years/{j}',
                       limitation='Published precision; original municipal waste tonnages and resident denominator not frozen')


def observation(engine, key, index, dimension, period, historical):
    metric = engine._catalog['metrics'][key]
    row = metric['rows'][index]
    ctx = context(metric, key, dimension)
    pointer = f'/metrics/{key}/rows/{index}'
    if historical:
        if period not in available_periods(engine, key, dimension, row):
            raise ValueError('environment_period_not_available')
        j = list(map(str, row['series']['years'])).index(period)
        value = row['series']['values'][j]
        vp, pp = pointer + f'/series/values/{j}', pointer + f'/series/years/{j}'
    else:
        if period != str(metric['meta']['year']):
            raise ValueError('environment_current_period_mismatch')
        value = row.get('value')
        vp, pp = pointer + '/value', f'/metrics/{key}/meta/year'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=vp, periodPointer=pp)]
    parts = {}
    warnings = []
    if key == WATER:
        snap, ref = engine.file(WATER_PATH)
        if snap.get('schemaVersion') != 2 or snap['sources']['istat'].get('flow') != '12_60_DF_DCCV_CONSACQUA_2' or snap['sources']['istat'].get('url') != WATER_URL:
            raise ValueError('environment_water_source_changed')
        native = snap['waterNetworkLosses']['towns'].get(row['code'], {}).get(period)
        if native is None:
            raise ValueError('environment_water_period_not_frozen')
        input_, delivered = native['immessa'], native['erogata']
        if not finite(input_) or not finite(delivered) or input_ <= 0 or delivered < 0 or delivered > input_:
            raise ValueError('environment_invalid_water_volumes')
        expected = (input_ - delivered) / input_ * 100
        close(native['perditePct'], expected)
        parts = dict(numerator=input_ - delivered, denominator=input_, scale=100,
                     numeratorPeriod=period, denominatorPeriod=period)
        if period == str(metric['meta']['year']):
            for name, expected_component in [('immessa', input_), ('erogata', delivered), ('perditePct', expected)]:
                close(row.get('networkVolumes', {}).get(name), expected_component)
        evidence.append(dict(ref, kind='source_snapshot', recordPointer=f'/waterNetworkLosses/towns/{row["code"]}/{period}',
                             sourceUrl=WATER_URL, sourceSha256=snap['sources']['istat']['sha256']))
        warnings.extend(['water_census_snapshot_not_current_network_condition', 'water_loss_components_not_split_in_snapshot'])
        source = WATER_URL
    elif key == 'wasteServiceCost':
        snap, ref = engine.file(COST_PATH)
        raw = snap['waste']
        if period != str(raw['year']) or raw.get('sourceUrl') != COST_URL or raw.get('definition') != 'CTOTab - costi totali di gestione del servizio di igiene urbana, euro/abitante/anno' or 'N. di comuni = 1' not in raw.get('note', ''):
            raise ValueError('environment_cost_scope_or_period_changed')
        expected = raw['towns'][row['town']]['ctotPerResident']
        evidence.append(dict(ref, kind='source_snapshot', valuePointer=f'/waste/towns/{row["town"]}/ctotPerResident', periodPointer='/waste/year',
                             limitation='Official normalized CTOTab; original cost and population components not frozen'))
        source = COST_URL
        warnings.extend(['service_cost_not_household_tax_or_service_quality', 'cost_benchmark_is_reported_sample_not_full_territory_cost'])
    else:
        expected, native_ref = published(engine, key, row, period)
        evidence.append(native_ref)
        if key == 'residualWaste':
            waste, waste_ref = published(engine, 'wastePerResident', row, period)
            rd, rd_ref = published(engine, 'recycling', row, period)
            if not finite(waste) or waste < 0 or not finite(rd) or not 0 <= rd <= 100:
                raise ValueError('environment_invalid_residual_components')
            calculated = waste * (1 - rd / 100)
            close(expected, calculated)
            expected = calculated
            evidence.extend([waste_ref, rd_ref])
            warnings.append('residual_is_derived_from_rounded_values_not_measured_disposal_or_actual_recycling')
        source = WASTE_URL
        warnings.extend(['waste_raw_municipal_quantities_not_frozen_no_implicit_weighting',
                         'waste_resident_denominator_not_population_present_or_tourist_production',
                         'waste_historical_series_does_not_attest_methodological_continuity'])
        if key == 'recycling':
            warnings.append('separate_collection_not_actual_material_recycling')
    if not finite(expected) or expected < 0 or (key in (WATER, 'recycling') and expected > 100):
        raise ValueError('environment_invalid_source_value')
    if value is not None:
        close(value, expected)
    if historical and period == str(metric['meta']['year']) and row.get('value') is not None:
        close(row['value'], value)
    return dict(ctx, **parts, metric=key, dimension=dimension, geography=row['code'], period=period,
                value=value, source=source, evidence=evidence, provenance=evidence,
                notApplicable=bool(row.get('notApplicable')) if not historical else False,
                dataUnavailable=value is None or (bool(row.get('dataUnavailable')) if not historical else False)), warnings


def benchmark(engine, key, scope, municipal):
    if scope not in ('tuscany', 'italy'):
        raise ValueError('environment_benchmark_scope_not_supported')
    path = WATER_BENCHMARK if key == WATER else COST_BENCHMARK if key == 'wasteServiceCost' else WASTE_BENCHMARK
    snap, ref = engine.file(path)
    if snap.get('qualityGate', {}).get('status') != 'PASS' or snap['qualityGate'].get('errors'):
        raise ValueError('environment_benchmark_gate_changed')
    entry = snap['benchmarks'][key]
    expected_unit = 'percent' if key in (WATER, 'recycling') else 'currency' if key == 'wasteServiceCost' else 'kgPerResident'
    expected_profile = 'istat-water-irregular' if key == WATER else 'ispra-environment-annual'
    if entry.get('unit') != expected_unit or snap.get('sourceProfileId') != expected_profile:
        raise ValueError('environment_benchmark_definition_changed')
    if municipal['period'] != str(entry['year']):
        raise ValueError('environment_benchmark_period_not_frozen')
    value = entry[scope]
    if key == WATER:
        raw = snap['raw'][scope]
        if not all(finite(raw.get(k)) for k in ('immessa', 'erogata', 'lossPercent')) or raw['immessa'] <= 0 or not 0 <= raw['erogata'] <= raw['immessa']:
            raise ValueError('environment_invalid_benchmark_components')
        expected = (raw['immessa'] - raw['erogata']) / raw['immessa'] * 100
        close(value, raw['lossPercent'])
        close(value, expected, tolerance=0.05)
    elif key == 'wasteServiceCost':
        close(value, snap['components'][scope]['ctot'])
    else:
        raw = snap['components'][scope]
        ru, rd, population = raw['ruTonnes'], raw['rdTonnes'], raw['population']
        if not all(finite(v) for v in (ru, rd, population)) or ru <= 0 or rd < 0 or rd > ru or population <= 0:
            raise ValueError('environment_invalid_benchmark_components')
        expected = rd / ru * 100 if key == 'recycling' else (ru if key == 'wastePerResident' else ru - rd) * 1000 / population
        close(value, expected)
    meta = engine._catalog['metrics'][key]['meta'].get('benchmark', {})
    if meta.get('sourceSnapshot') != path or str(meta.get('year')) != municipal['period'] or meta.get('url') != snap['sourceUrl']:
        raise ValueError('environment_benchmark_reference_changed')
    close(meta.get(scope), value)
    evidence = [dict(ref, kind='benchmark_snapshot', valuePointer=f'/benchmarks/{key}/{scope}',
                     sourceUrl=snap['sourceUrl'], limitation='Official reported precision and scope; cost benchmarks refer to reporting samples' if key == 'wasteServiceCost' else 'Official rounded aggregate' if key == WATER else 'Ratio of frozen provincial quantity sums; municipal rounded residual is a distinct precision level')]
    return dict({k: municipal[k] for k in ('metric', 'dimension', 'unit', 'population', 'definition', 'method', 'frequency', 'periodBasis', 'adapter', 'period')},
                geography=scope, value=value, source=snap['sourceUrl'], evidence=evidence, provenance=evidence,
                notApplicable=False, dataUnavailable=False)
