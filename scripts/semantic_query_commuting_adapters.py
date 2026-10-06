"""Reviewed municipal commuting marginals, with explicit denominator dates.

No origin/destination pairs are frozen here. Pooled municipal retention must
never be described as retention within a selected multi-municipality territory.
"""
import math

from semantic_operations import finite

SNAPSHOT = 'data/source-snapshots/a3-istat-commuting-benchmark-2021.json'
DEMO = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
POSAS = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
CANONICAL = 'data/site-data.json'
SOURCE = 'https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/'
ARCHIVE = 'https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip'
P2 = 'https://demo.istat.it/data/p2/P2_2021_it_Comuni.zip'
KEYS = ('inboundCommuters', 'outboundCommuters', 'commuterBalance',
        'inboundCommutersRate', 'outboundCommutersRate', 'commuterBalanceRate', 'selfContainment')
RATIOS = KEYS[3:]
TUSCANY = {'045','046','047','048','049','050','051','052','053','100'}


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError('commuting_invalid_source_count')
    return value


def close(value, expected, tolerance=1e-8):
    if not finite(value) or not math.isclose(value, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError('commuting_component_or_value_mismatch')


def context(metric, key, dimension):
    if dimension != 'total': raise ValueError('commuting_dimension_not_frozen')
    unit = 'percent' if key == 'selfContainment' else 'per1000' if key in RATIOS else 'number' if key == 'inboundCommuters' else 'people'
    allowed = {SOURCE}
    if key == 'commuterBalanceRate': allowed.add('https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/')
    if metric['meta'].get('unit') != unit or str(metric['meta'].get('year')) != '2021' or metric.get('sourceUrl') not in allowed:
        raise ValueError('commuting_reference_or_definition_changed')
    denominator = '2021' if key in ('commuterBalanceRate', 'selfContainment') else '2026' if key in RATIOS else None
    definition = {
        'inboundCommuters':'workers commuting from another municipality',
        'outboundCommuters':'resident workers commuting to another municipality',
        'commuterBalance':'inbound minus outbound habitual work commuters',
        'inboundCommutersRate':'inbound work commuters 2021 / residents January 1 2026 * 1000',
        'outboundCommutersRate':'outbound work commuters 2021 / residents January 1 2026 * 1000',
        'commuterBalanceRate':'net work commuters 2021 / residents January 1 2021 * 1000',
        'selfContainment':'within own municipality / resident habitual work commuters * 100',
    }[key]
    population = 'resident habitual work commuters' if key == 'selfContainment' else f'resident population at January 1 {denominator}' if key in RATIOS else 'habitual work commuters by destination' if key == 'inboundCommuters' else 'resident habitual outbound work commuters' if key == 'outboundCommuters' else 'net habitual work commuter movements'
    return dict(unit=unit, population=population,
                definition=definition, method='Istat frozen municipal marginals; ratios from exact components',
                frequency='irregular', periodBasis='habitual work movements 2021' + (f'; denominator {denominator}' if denominator else ''),
                adapter=f'istat-commuting/{key}/v1')


def native(engine):
    if hasattr(engine, '_commuting_native'): return engine._commuting_native
    snap, ref = engine.file(SNAPSHOT)
    if snap.get('profileId') != 'istat-commuting-irregular' or snap.get('sourceUrl') != SOURCE or snap.get('resolvedDataUrl') != ARCHIVE or snap.get('qualityGate', {}).get('status') != 'PASS' or snap.get('matrixRows') != 523949:
        raise ValueError('commuting_source_gate_changed')
    records = snap['records']; by = {}
    for i, record in enumerate(records):
        if len(record) != 4 or record[0] in by or len(record[0]) != 6 or not record[0].isdigit(): raise ValueError('commuting_duplicate_or_invalid_geography')
        _, internal, outbound, inbound = record
        for count in record[1:]: integer(count)
        if internal + outbound <= 0: raise ValueError('commuting_resident_universe_missing')
        by[record[0]] = (i, record)
    if len(by) != 7904 or sum(r[2] for r in records) != sum(r[3] for r in records) or sum(r[1]+r[2] for r in records) != 19565808 or sum(c[:3] in TUSCANY for c in by) != 273:
        raise ValueError('commuting_native_coverage_or_conservation_changed')
    pop = snap['population2021']; populations = {}
    if pop.get('year') != '2021' or pop.get('sourceUrl') != P2: raise ValueError('commuting_population_reference_changed')
    for i, record in enumerate(pop['records']):
        code, men, women, total = record
        if code in populations or code not in by: raise ValueError('commuting_population_geography_changed')
        if integer(men)+integer(women) != integer(total): raise ValueError('commuting_population_partition_changed')
        populations[code] = (i, total)
    if set(populations) != set(by) or sum(r[1] for r in populations.values()) != 59236213 or sum(v[1] for c,v in populations.items() if c[:3] in TUSCANY) != 3692865:
        raise ValueError('commuting_population_coverage_changed')
    demo, demo_ref = engine.file(DEMO)
    if snap['population'].get('year') != '2026' or snap['population'].get('sha256') != demo_ref['sha256'] or demo['qualityGate']['status'] != 'PASS' or demo['benchmarks']['population']['year'] != '2026':
        raise ValueError('commuting_population_2026_provenance_changed')
    engine._commuting_native = (snap, ref, by, populations, demo, demo_ref)
    return engine._commuting_native


def components(key, internal, outbound, inbound, residents2021, residents2026):
    balance = inbound - outbound
    if key == 'selfContainment': return dict(numerator=internal, denominator=internal+outbound, scale=100)
    if key in RATIOS:
        numerator = balance if key == 'commuterBalanceRate' else inbound if key == 'inboundCommutersRate' else outbound
        return dict(numerator=numerator, denominator=residents2021 if key == 'commuterBalanceRate' else residents2026, scale=1000)
    return {}


def calculate(key, record, pop21, pop26):
    _, internal, outbound, inbound = record
    parts = components(key, internal, outbound, inbound, pop21, pop26)
    if parts:
        if parts['denominator'] <= 0: raise ValueError('commuting_positive_denominator_required')
        return parts['numerator']/parts['denominator']*parts['scale'], parts
    return inbound if key == 'inboundCommuters' else outbound if key == 'outboundCommuters' else inbound-outbound, parts


def warnings(key):
    notes = ['habitual_work_commuters_not_all_daily_trips_or_jobs', 'single_2021_snapshot_not_current_mobility',
             'municipal_marginals_do_not_identify_origin_destination_pairs', 'gross_municipal_flows_include_moves_within_selected_group',
             'commuting_is_not_transport_mode_capacity_quality_or_causal_policy_effect',
             'commuting_counts_and_ratios_share_components_and_population_size']
    if key in ('inboundCommutersRate','outboundCommutersRate'):
        notes += ['work_flow_2021_resident_stock_2026', 'posas_2026_source_label_is_estimate']
    if key in ('commuterBalance','commuterBalanceRate'): notes.append('net_balance_cancels_within_group_flows_gross_boundary_counts_not_recoverable')
    if key == 'commuterBalanceRate': notes.append('net_balance_2021_uses_resident_stock_2021_not_2026')
    if key == 'selfContainment': notes += ['ratio_from_exact_components_published_share_rounded_to_one_decimal', 'pooled_same_municipality_retention_not_retention_within_selected_group', 'outside_municipality_census_share_not_complement_of_work_matrix_retention']
    return notes


def observation(engine, key, index, dimension, period, historical):
    if period != '2021': raise ValueError('commuting_only_2021_frozen')
    metric = engine._catalog['metrics'][key]; row = metric['rows'][index]; ctx = context(metric,key,dimension)
    snap, ref, by, populations, _, _ = native(engine)
    canonical, canonical_ref = engine.file(CANONICAL); original = canonical['metrics'][key]
    if original['method'] != metric.get('method') or original['meta']['description'] != metric['meta'].get('description'):
        raise ValueError('commuting_formula_or_universe_changed')
    identities = [r for r in original['rows'] if r['code'] == row['code']]
    if len(identities) != 1 or identities[0]['town'] != row['town']: raise ValueError('commuting_geography_identity_changed')
    raw_index, record = by[row['code']]; pop_index, pop21 = populations[row['code']]
    posas, posas_ref = engine.file(POSAS)
    stock = [r for r in posas['posas']['towns'][row['town']] if str(r['year']) == '2026']
    if len(stock) != 1: raise ValueError('commuting_2026_population_not_unique')
    pop26 = integer(stock[0]['population'])
    expected, parts = calculate(key, record, pop21, pop26)
    published = row.get('value')
    if published is not None: close(published, expected, .0500000001 if key == 'selfContainment' else 1e-8)
    evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/value',periodPointer=f'/metrics/{key}/meta/year'),
                dict(ref,kind='source_snapshot',recordPointer=f'/records/{raw_index}',sourceUrl=ARCHIVE,archiveSha256=snap['archiveSha256']),
                dict(canonical_ref,kind='geography_identity_snapshot',recordPointer=f'/metrics/{key}/rows',code=row['code'],town=row['town'])]
    dates = {}
    if key in RATIOS:
        dates = dict(numeratorPeriod='2021',denominatorPeriod='2021' if key in ('commuterBalanceRate','selfContainment') else '2026')
        if key == 'commuterBalanceRate': evidence.append(dict(ref,kind='denominator_snapshot',recordPointer=f'/population2021/records/{pop_index}',sourceUrl=P2,archiveSha256=snap['population2021']['archiveSha256']))
        elif key != 'selfContainment': evidence.append(dict(posas_ref,kind='denominator_snapshot',recordPointer=f'/posas/towns/{row["town"]}',period='2026',sourceUrl='https://demo.istat.it/'))
    return dict(ctx,**parts,**dates,metric=key,dimension=dimension,geography=row['code'],period=period,
                value=expected if published is not None else None,publishedValue=published,source=ARCHIVE,
                evidence=evidence,provenance=evidence,notApplicable=bool(row.get('notApplicable')),
                dataUnavailable=published is None or bool(row.get('dataUnavailable'))), warnings(key)


def benchmark(engine, key, scope, municipal):
    if key not in RATIOS: raise ValueError('commuting_absolute_volume_benchmark_gap_not_supported')
    if scope not in ('tuscany','italy'): raise ValueError('benchmark_scope_not_supported')
    snap, ref, by, populations, demo, demo_ref = native(engine)
    records = [r for code,(_,r) in by.items() if scope == 'italy' or code[:3] in TUSCANY]
    record = [scope,*[sum(r[i] for r in records) for i in (1,2,3)]]
    pop21 = sum(v[1] for code,v in populations.items() if scope == 'italy' or code[:3] in TUSCANY)
    pop26 = integer(demo['benchmarks']['population'][scope])
    value, parts = calculate(key,record,pop21,pop26)
    spec = snap['benchmarks'][key]
    if spec.get('year') != '2021' or spec.get('unit') != municipal['unit']: raise ValueError('commuting_benchmark_reference_changed')
    close(spec[scope],value)
    published = engine._catalog['metrics'][key]['meta'].get('benchmark')
    if published:
        if published.get('sourceSnapshot') != SNAPSHOT or str(published.get('year')) != '2021': raise ValueError('commuting_published_benchmark_reference_changed')
        close(published[scope],value)
    evidence = [dict(ref,kind='benchmark_snapshot',recordPointer='/records',sourceUrl=ARCHIVE,archiveSha256=snap['archiveSha256'],scope=scope,
                     limitation='sum of municipal marginals; gross flows include within-region intermunicipal movements')]
    if key == 'commuterBalanceRate': evidence.append(dict(ref,kind='denominator_snapshot',recordPointer='/population2021/records',sourceUrl=P2,scope=scope))
    elif key != 'selfContainment': evidence.append(dict(demo_ref,kind='denominator_snapshot',recordPointer=f'/benchmarks/population/{scope}',period='2026'))
    return dict({k:municipal[k] for k in ('unit','population','definition','method','frequency','periodBasis','adapter','dimension','period','numeratorPeriod','denominatorPeriod')},
                **parts,metric=key,geography=scope,value=value,source=ARCHIVE,evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False)


def correlation_guard(observations, axis):
    selected = [o for o in observations if o['metric'] in KEYS]
    if not selected: return
    if axis == 'periods': raise ValueError('commuting_history_not_frozen')
    # Hybrids may be associated with each other, but not silently with a
    # contemporaneous 2021 indicator or the balance's 2021 denominator.
    dates = {o.get('denominatorPeriod') for o in selected if o['metric'] in RATIOS}
    if '2026' in dates and (dates != {'2026'} or any(o['metric'] not in ('inboundCommutersRate','outboundCommutersRate') for o in observations)):
        raise ValueError('commuting_hybrid_denominator_pair_not_aligned')
