"""RGS municipal employers: stock, age, net flows and published training measures."""
import hashlib
import json
import math
from semantic_operations import finite
import acquire_a3_benchmark_rgs_staff_per_resident as staff_contract

KEYS = ('municipalEmployeesPer1000', 'municipalStaffAgeStructure',
        'municipalStaffTraining', 'municipalStaffTurnover')
STAFF, AGE, TRAINING, TURNOVER = KEYS
ADMIN = 'data/source-snapshots/rgs-amministrazione-2024.json'
TRAIN = 'data/source-snapshots/rgs-formazione-2024.json'
BENCH = 'data/source-snapshots/a3-rgs-staff-benchmark-2024.json'
PUBLIC = 'https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dati-pubblicati'
TRAIN_URL = 'https://contoannuale.rgs.mef.gov.it/web/sicosito/assenze-e-turnover/formazione-acc'
AGE_FIELDS = ('age55plus', 'age40to54', 'under40')
AGE_LABELS = ('55+', '40–54', '<40')
TRAIN_FIELDS = ('meanTotalRgs', 'totalDays', 'meanMen', 'meanWomen')
TRAIN_LABELS = ('Media totale RGS', 'Giornate complessive', 'Media uomini', 'Media donne')
HASHES = {
    ADMIN: ('66faf69a8d3ba3c5aeaf3015cdc468ffd59fe0814f5c35b98592cd61c0ffa403', '331a95c8e05ee98f7e05c78a0c3cf16b4f2e8c83b91af568bf7344d76b75c457'),
    TRAIN: ('59b9c99d5baa8c7806aa58078563b9beef0976e056ceb45fb85b4e9a0446bce3', 'fe38702d039edd611ab5670e37334a3ef04206a89b8a93d6dd2a0e07cf64bb5e'),
    BENCH: ('7400aebb58e4288f45a2e3f9c265c6102b341a9f3203bc64e89fe40f6612d558', '815a4145f3137834dec6e4513b0e5db112d25f72975c2f9e29b9bedc5a5c7bb3'),
}


def fingerprint(s):
    return hashlib.sha256(json.dumps(s, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def frozen(engine, path):
    s, ref = engine.file(path)
    if (ref.get('sha256'), fingerprint(s)) != HASHES[path]:
        raise ValueError('rgs_frozen_input_changed')
    return s, ref


def close(actual, expected, tolerance=1e-9):
    if expected is None:
        if actual is not None: raise ValueError('rgs_public_native_mismatch')
    elif not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError('rgs_public_native_mismatch')


def dimensions(key):
    if key == AGE: return ['total', *('age:' + a for a in AGE_FIELDS)]
    if key == TRAINING: return ['total', *('measure:' + f for f in TRAIN_FIELDS), 'days:men', 'days:women']
    if key == TURNOVER: return ['total', 'headcount', 'hires', 'cessations']
    return ['total', 'staff', 'residents']


def selected(key, dim):
    if key == AGE: return AGE_FIELDS[0] if dim == 'total' else dim[4:]
    if key == TRAINING: return TRAIN_FIELDS[0] if dim == 'total' else dim[8:] if dim.startswith('measure:') else dim
    return dim


def weighted(key, dim): return key != TRAINING and (key == AGE or dim == 'total')
def scopes(key, dim): return ['tuscany'] if key == STAFF and dim == 'total' else ['versilia'] if key == TRAINING else []
def operations(key, dim): return ['compare', 'rank', *(['weighted_ratio'] if weighted(key, dim) else []), *(['benchmark_gap'] if scopes(key, dim) else [])]


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('rgs_history_or_temporal_continuity_not_frozen')
    if op == 'correlation': raise ValueError('rgs_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('rgs_peer_anomaly_not_reviewed')
    if op == 'weighted_ratio' and not weighted(key, dim): raise ValueError('rgs_measure_not_component_ratio')
    if op == 'benchmark_gap' and not scopes(key, dim): raise ValueError('rgs_benchmark_dimension_not_reviewed')


def context(metric, key, dim):
    units = {STAFF: 'per1000', AGE: 'percent', TRAINING: 'decimal', TURNOVER: 'percent'}
    url = staff_contract.URL if key == STAFF else TRAIN_URL if key == TRAINING else PUBLIC
    meta = metric['meta']
    if dim not in dimensions(key) or meta.get('unit') != units[key] or meta.get('year') != '2024' or metric.get('sourceUrl') != url:
        raise ValueError('rgs_definition_changed')
    if key in (AGE, TRAINING) and meta.get('compositeType') != 'securityMeasures': raise ValueError('rgs_definition_changed')
    field = selected(key, dim)
    unit = 'number' if key == STAFF and dim != 'total' or key == TURNOVER and dim != 'total' or key == TRAINING and (field == 'totalDays' or field.startswith('days:')) else units[key]
    definitions = {
        STAFF: 'municipal employer staff 31 December 2024 / residents 1 January 2024 × 1000' if dim == 'total' else 'municipal employer stock' if dim == 'staff' else 'Istat residents 1 January 2024',
        AGE: 'RGS age band ' + field + ' / total municipal employer staff × 100; no midpoint mean age',
        TURNOVER: 'net hires minus net cessations, excluding inter-administration transfers, / end-year staff × 100' if dim == 'total' else 'native net employment flow ' + dim + '; transfers excluded',
        TRAINING: 'published RGS training ' + field + '; meanTotalRgs=(meanMen+meanWomen)/2 in frozen payload; no totalDays/headcount reinterpretation',
    }
    return dict(unit=unit, population='employees of distinct municipal employers; unions excluded' if key != TRAINING else 'RGS municipal employer training records; published gender means and training days distinct', definition=definitions[key], method='frozen native reconciliation; numerical ordering is not administrative quality', frequency='annual', periodBasis='reference 2024; stock at 31 December, resident denominator at 1 January' if key == STAFF else 'RGS reference year 2024', adapter='rgs/' + key + '/' + field + '/v1')


def identity(engine, metric, row, admin):
    names = {t['code']: t['name'] for t in engine._catalog['towns']}
    if len(metric['rows']) != len(names) or {r['code'] for r in metric['rows']} != set(names) or set(admin['towns']) != set(names.values()) or row.get('town') != names[row['code']] or row.get('slug') != '-'.join(row['town'].lower().split()) or row.get('notApplicable') or row.get('dataUnavailable'):
        raise ValueError('rgs_municipal_employer_identity_changed')
    return admin['towns'][row['town']]


def staff_panel(engine):
    s, ref = frozen(engine, BENCH)
    metric = engine._catalog['metrics'][STAFF]
    sig = fingerprint(metric)
    if getattr(engine, '_rgs_staff_validation', None) != sig:
        try:
            staff_contract.validate_snapshot(metric, s)
        except RuntimeError as exc:
            raise ValueError('rgs_native_staff_panel_or_components_changed') from exc
        engine._rgs_staff_validation = sig
    return s, ref


def training_values(n):
    close(n['menDays'] + n['womenDays'], n['totalDays'])
    close(n['meanTotalRgs'], (n['meanMen'] + n['meanWomen']) / 2)
    return {**{f: n[f] for f in TRAIN_FIELDS}, 'days:men': n['menDays'], 'days:women': n['womenDays']}


def observation(engine, key, index, dim, period, historical):
    if period != '2024': raise ValueError('rgs_period_not_frozen')
    metric = engine._catalog['metrics'][key]; row = metric['rows'][index]; ctx = context(metric, key, dim)
    admin, ref = frozen(engine, ADMIN); n = identity(engine, metric, row, admin)
    pointer = f'/metrics/{key}/rows/{index}/'; base = '/towns/' + row['town']; refs = []; extra = {'institutionCode': n['institutionCode']}
    field = selected(key, dim); num = den = scale = None
    warnings = ['rgs_frozen_extraction_not_new_live_acquisition', 'rgs_numerical_rank_not_administrative_quality']
    if key == STAFF:
        panel, pref = staff_panel(engine)
        employer = next(g for g in panel['geographies'] if g['Codice_ISTAT_Comune'] == row['code'])
        close(row['staffAt31Dec'], n['staffAt31Dec'])
        vals = {'total': n['staffAt31Dec'] / row['residentPopulation'] * 1000, 'staff': n['staffAt31Dec'], 'residents': row['residentPopulation']}
        value = vals[dim]; num, den, scale = (n['staffAt31Dec'], row['residentPopulation'], 1000) if dim == 'total' else (None, None, None)
        close(row['value'], vals['total']); pointer += {'total': 'value', 'staff': 'staffAt31Dec', 'residents': 'residentPopulation'}[dim]
        refs.append(dict(pref, kind='source_snapshot', sourceUrl=panel['source']['populationUrl'], archiveMember='P2_2024_it_Comuni.csv', municipalityCode=row['code'], populationField='Popolazione censita al 1° gennaio - Totale', employerBdapId=employer['Id_Ente']))
        extra.update(numeratorPointer=base + '/staffAt31Dec', denominatorSnapshot=BENCH, denominatorField='Popolazione censita al 1° gennaio - Totale')
        source = admin['sources']['occupationTurnover']; warnings += ['rgs_stock_2024_december_population_2024_january_distinct', 'rgs_outsourcing_and_joint_services_affect_staffing']
    elif key == AGE:
        close(row['staffAt31Dec'], n['staffAt31Dec']); close(sum(n['age'].values()), n['staffAt31Dec'])
        if [p.get('selectorLabel') for p in row['parts']] != list(AGE_LABELS): raise ValueError('rgs_public_parts_changed')
        for j, f in enumerate(AGE_FIELDS):
            part = row['parts'][j]
            if part.get('unit') != 'percent': raise ValueError('rgs_public_parts_changed')
            close(part['count'], n['age'][f]); close(part['value'], n['age'][f] / n['staffAt31Dec'] * 100)
        close(row['value'], row['parts'][0]['value']); j = AGE_FIELDS.index(field)
        num, den, scale = n['age'][field], n['staffAt31Dec'], 100; value = num / den * scale
        pointer += 'value' if dim == 'total' else f'parts/{j}/value'; extra.update(numeratorPointer=base + '/age/' + field, denominatorPointer=base + '/staffAt31Dec')
        source = admin['sources']['age']; warnings += ['rgs_age_classes_not_mean_age_or_staff_quality']
    elif key == TURNOVER:
        for f in ('netHires', 'netCessations', 'netTurnoverHeadcount'): close(row[f], n[f])
        close(n['netTurnoverHeadcount'], n['netHires'] - n['netCessations'])
        ratio = n['netTurnoverHeadcount'] / n['staffAt31Dec'] * 100; close(row['value'], ratio); close(n['netTurnoverRatePct'], ratio, 0.0002)
        vals = {'total': ratio, 'headcount': n['netTurnoverHeadcount'], 'hires': n['netHires'], 'cessations': n['netCessations']}; value = vals[dim]
        c = row.get('a3StaffTurnoverDimensions')
        if c is not None:
            if c.get('referenceYear') != 2024 or c.get('sourceSnapshot') != ADMIN or [v.get('key') for v in c['categories']] != ['hires', 'cessations']: raise ValueError('rgs_companion_changed')
            close(c['absolute'], n['netTurnoverHeadcount']); close(c['normalized'], n['netTurnoverRatePct'])
            for v, f in zip(c['categories'], ('netHires', 'netCessations')):
                if v.get('unit') != 'people': raise ValueError('rgs_companion_changed')
                close(v['value'], n[f])
        if dim == 'total': num, den, scale = n['netTurnoverHeadcount'], n['staffAt31Dec'], 100
        pointer += {'total': 'value', 'headcount': 'netTurnoverHeadcount', 'hires': 'netHires', 'cessations': 'netCessations'}[dim]
        extra.update(numeratorPointers=[base + '/netHires', base + '/netCessations'], denominatorPointer=base + '/staffAt31Dec'); source = admin['sources']['occupationTurnover']
        refs += [dict(ref, kind='source_snapshot', sourceUrl=admin['sources'][f]) for f in ('hires', 'cessations')]
        warnings += ['rgs_transfers_excluded_net_flows_not_gross_hiring', 'rgs_small_staff_one_person_large_percentage']
    else:
        training, tref = frozen(engine, TRAIN); t = training['towns'][row['town']]
        if t['institutionCode'] != n['institutionCode']: raise ValueError('rgs_municipal_employer_identity_changed')
        vals = training_values(t)
        if [p.get('selectorLabel') for p in row['parts']] != list(TRAIN_LABELS): raise ValueError('rgs_public_parts_changed')
        for j, f in enumerate(TRAIN_FIELDS):
            if row['parts'][j].get('unit') != ('number' if f == 'totalDays' else 'decimal'): raise ValueError('rgs_public_parts_changed')
            close(row['parts'][j]['value'], vals[f])
        close(row['value'], vals['meanTotalRgs'])
        c = row.get('a3TrainingGender')
        if c is not None:
            if c.get('referenceYear') != 2024 or c.get('sourceSnapshot') != TRAIN or [v.get('key') for v in c['gender']] != ['men', 'women']: raise ValueError('rgs_companion_changed')
            for v, f in zip(c['gender'], ('Men', 'Women')):
                close(v['days'], t[f.lower() + 'Days']); close(v['mean'], t['mean' + f])
        value = vals[field]; ref = tref; source = training['apiUrl']; extra['nativeField'] = {'days:men': 'menDays', 'days:women': 'womenDays'}.get(field, field)
        pointer += 'value' if dim == 'total' else f'parts/{TRAIN_FIELDS.index(field)}/value' if field in TRAIN_FIELDS else 'a3TrainingGender/gender/' + ('0' if field == 'days:men' else '1') + '/days'
        if field.startswith('days:') and c is None:
            # The source catalog lacks the companion; evidence points to the native cell.
            pointer = f'/metrics/{key}/rows/{index}'
        warnings += ['rgs_training_mean_not_total_days_per_staff', 'rgs_training_means_not_additive_or_quality_measure', 'rgs_training_2008_2024_available_not_acquired_history']
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer), dict(ref, kind='source_snapshot', recordPointer=base, **extra), *refs]
    result = dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value, source=source, evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=value is None)
    if num is not None: result.update(numerator=num, denominator=den, scale=scale, numeratorPeriod='2024-12-31' if key == STAFF else '2024', denominatorPeriod='2024-01-01' if key == STAFF else '2024-12-31')
    return result, warnings


def benchmark(engine, key, scope, municipal):
    if scope not in scopes(key, municipal['dimension']) or municipal['period'] != '2024': raise ValueError('rgs_benchmark_scope_or_period_not_reviewed')
    if key == STAFF:
        s, ref = staff_panel(engine); b = s['benchmarks'][STAFF]; meta = engine._catalog['metrics'][STAFF]['meta']['benchmark']; value = b[scope]
        if meta.get('sourceSnapshot') != BENCH or meta.get('year') != '2024' or meta.get('url') != staff_contract.URL: raise ValueError('rgs_benchmark_definition_changed')
        close(meta[scope], value); ev = [dict(ref, kind='benchmark_snapshot', valuePointer='/benchmarks/' + STAFF + '/' + scope, componentPointer='/raw/' + scope, coverage='273/273; 271 RGS employers + 2 explicit PIAO zeros')]; source = staff_contract.URL
    else:
        s, ref = frozen(engine, TRAIN); vals = training_values(s['versilia']); value = vals[selected(key, municipal['dimension'])]
        aggregate = engine._catalog['metrics'][TRAINING]['aggregate']
        close(aggregate['value'], vals['meanTotalRgs'])
        if [p.get('selectorLabel') for p in aggregate['parts']] != list(TRAIN_LABELS): raise ValueError('rgs_public_parts_changed')
        for j, field in enumerate(TRAIN_FIELDS):
            if aggregate['parts'][j].get('unit') != ('number' if field == 'totalDays' else 'decimal'): raise ValueError('rgs_public_parts_changed')
            close(aggregate['parts'][j]['value'], vals[field])
        if set(s['versilia']['institutionCodes']) != {n['institutionCode'] for n in s['towns'].values()}: raise ValueError('rgs_joint_training_cohort_changed')
        field = selected(key, municipal['dimension'])
        ev = [dict(ref, kind='benchmark_snapshot', recordPointer='/versilia', nativeField={'days:men': 'menDays', 'days:women': 'womenDays'}.get(field, field), aggregation='published joint seven-institution RGS API query, not mean of municipal means')]; source = s['apiUrl']
    return dict({k: municipal[k] for k in ('metric', 'dimension', 'unit', 'population', 'definition', 'method', 'frequency', 'periodBasis', 'adapter', 'period')}, geography=scope, value=value, source=source, evidence=ev, provenance=ev, notApplicable=False, dataUnavailable=False)
