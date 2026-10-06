"""Demographic and school carriers with explicit native periods and denominators."""
import math
import re
from urllib.parse import urlparse

from semantic_operations import finite

DEPENDENCY = 'dependencyIndices'
FOREIGN = 'foreignResidents'
CHANGE = 'populationChange'
NATURAL = 'naturalDemographicDynamics'
MOBILITY = ('internalResidentialMobility', 'foreignResidentialMobility', 'totalResidentialMobility')
STUDENTS = ('schoolStudents', 'studentsPerClass', 'primaryFullTimeShare')
BUILDINGS = ('schoolBuildingSafetyDocs', 'schoolBuildingAccessibility', 'schoolBuildingFacilities', 'schoolBuildingAge', 'schoolBuildingTransport')
SITES = 'schoolSites'
KEYS = (DEPENDENCY, FOREIGN, CHANGE, NATURAL, *MOBILITY, SITES, *STUDENTS, *BUILDINGS)
DEMO = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
RCS = 'data/source-snapshots/istat-rcs-demography-2025.json'
RCS_HISTORY = 'data/source-snapshots/a3-simple-rcs-history-2024-2025.json'
INTERNAL = 'data/source-snapshots/composite-indicators-v1.9.0.json'
LIA = 'data/source-snapshots/lia-v1.4.0.json'
BUILDING = 'data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json'
DEMO_BENCH = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
MOB_BENCH = 'data/source-snapshots/a3-istat-demography-mobility-benchmark-2024.json'
MIM_BENCH = 'data/source-snapshots/a3-mim-benchmark-2024-25.json'
BUILDING_BENCH = 'data/source-snapshots/a3-mim-building-benchmark-2024-25.json'
CANONICAL = 'data/site-data.json'
SNAPSHOTS = (DEMO, RCS, RCS_HISTORY, INTERNAL, LIA, BUILDING, DEMO_BENCH, MOB_BENCH, MIM_BENCH, BUILDING_BENCH, CANONICAL)
PERIODS = ('prima del 1800', 'tra il 1800 e il 1899', 'tra il 1900 e il 1933', 'tra il 1934 e il 1949', 'tra il 1950 e il 1970', 'tra il 1971 e il 1975', 'tra il 1976 e il 1992', 'tra il 1997 e il 2008', 'tra il 2009 e il 2017')
PERIOD_IDS = ('before1800', '1800-1899', '1900-1933', '1934-1949', '1950-1970', '1971-1975', '1976-1992', '1997-2008', '2009-2017')
PERIOD_LABELS = ('Prima del 1800', '1800–1899', '1900–1933', '1934–1949', '1950–1970', '1971–1975', '1976–1992', '1997–2008', '2009–2017')
BUILDING_SPECS = {
    BUILDINGS[0]: (('fullOccupancy', 'agibilita', 'Agibilità'), ('cpi', 'cpi', 'CPI'), ('scia', 'sciaAntincendio', 'SCIA'), ('renewal', 'rinnovoAntincendio', 'Rinnovo')),
    BUILDINGS[1]: (('yes', 'accessibilita', 'Con accorgimenti'), ('no', 'accessibilita', 'Senza'), ('undefined', 'accessibilita', 'Non definito')),
    BUILDINGS[2]: (('canteen', 'mensa', 'Mensa'), ('gym', 'palestra', 'Palestra')),
    BUILDINGS[3]: (('builtBy1970', 'periodoCostruzione', 'Entro 1970'), *((i, 'periodoCostruzione', l) for i, l in zip(PERIOD_IDS, PERIOD_LABELS)), ('undefined', 'periodoCostruzione', 'Non definito')),
    BUILDINGS[4]: (('schoolBus', 'scuolabus', 'Scuolabus'), ('urban', 'tplUrbano', 'TPL urbano'), ('interurban', 'tplInterurbano', 'TPL interurbano')),
}
NAT_LABELS = ('Saldo naturale', 'Natalità', 'Mortalità')
DEP_LABELS = ('Strutturale', 'Anziani')


def dimensions(key):
    if key == DEPENDENCY:
        return ['total', 'part:structural', 'part:elderly', *(f'part:{p}|sex:{s}' for p in ('structural', 'elderly') for s in ('men', 'women'))]
    if key == FOREIGN: return ['total', 'count', 'sex:men', 'sex:women']
    if key == NATURAL: return ['total', 'part:balance', 'part:births', 'part:deaths']
    if key in MOBILITY: return ['total', 'part:arrivals', 'part:departures', 'part:balance']
    if key in BUILDINGS: return ['total', *('part:' + p[0] for p in BUILDING_SPECS[key])]
    if key == SITES: return ['total', 'normalized']
    return ['total']


def part(key, dimension):
    if dimension not in dimensions(key): raise ValueError('demography_school_dimension_not_reviewed')
    if dimension != 'total': return dimension.removeprefix('part:').split('|')[0]
    if key == DEPENDENCY: return 'structural'
    if key == NATURAL or key in MOBILITY: return 'balance'
    if key in BUILDINGS: return BUILDING_SPECS[key][0][0]
    return 'total'


def token(key, value):
    value = str(value)
    if key == CHANGE:
        value = value.replace('–', '-')
        if not re.fullmatch(r'2019-20[0-9]{2}', value) or not 2019 <= int(value[-4:]) <= 2026:
            raise ValueError('demography_cumulative_2019_interval_required')
    elif key in (*STUDENTS, *BUILDINGS):
        value = value.removeprefix('a.s. ')
        if not re.fullmatch(r'[0-9]{4}/[0-9]{2}', value) or int(value[-2:]) != (int(value[:4]) + 1) % 100:
            raise ValueError('demography_school_native_school_year_required')
    elif not re.fullmatch(r'[0-9]{4}', value): raise ValueError('demography_annual_period_required')
    return value


def order(value):
    return int(value[-4:] if value.startswith('2019-') else value[:4])


def weighted(key, dimension):
    return key in (DEPENDENCY, CHANGE, NATURAL, *MOBILITY, 'studentsPerClass', 'primaryFullTimeShare', *BUILDINGS) or (key == FOREIGN and dimension == 'total')


def benchmark_scopes(key, dimension):
    p = part(key, dimension)
    if key == SITES or key == 'schoolStudents' or (key == FOREIGN and dimension != 'total') or '|sex:' in dimension: return []
    if key in (BUILDINGS[0], BUILDINGS[2], BUILDINGS[4]) and p != BUILDING_SPECS[key][0][0]: return []
    return ['tuscany', 'italy']


def close(actual, expected, tolerance=1e-7):
    # A published null stays missing, even when a frozen source has a value.
    if actual is not None and (not finite(actual) or not finite(expected) or not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance)):
        raise ValueError('demography_school_catalog_source_mismatch')


def required_close(actual, expected):
    number(actual)
    close(actual, expected)


def number(value):
    if not finite(value): raise ValueError('demography_school_nonfinite_component')
    return value


def ratio(n, d, scale):
    number(n); number(d)
    if d < 0: raise ValueError('demography_school_negative_denominator')
    return n / d * scale if d else None


def one(records, year):
    matches = [r for r in records if str(r['year']) == year]
    if len(matches) != 1: raise ValueError('demography_school_source_period_not_unique')
    return matches[0]


def context(metric, key, dimension):
    p = part(key, dimension)
    expected_unit = 'per100' if key == DEPENDENCY else 'per1000' if key in (NATURAL, *MOBILITY) else 'percent' if key in (FOREIGN, CHANGE, 'primaryFullTimeShare', *BUILDINGS) else 'people' if key == 'schoolStudents' else 'number' if key == SITES else 'studentsPerClass'
    host = urlparse(metric.get('sourceUrl', '')).hostname
    if host != ('dati.istruzione.it' if key in (SITES, *STUDENTS, *BUILDINGS) else 'demo.istat.it') or metric['meta']['unit'] != expected_unit:
        raise ValueError('demography_school_catalog_context_changed')
    if key in (*STUDENTS, *BUILDINGS) and token(key, metric['meta']['year']) != '2024/25': raise ValueError('demography_school_year_not_frozen')
    unit = 'people' if key == FOREIGN and dimension != 'total' else 'per1000' if key == SITES and dimension == 'normalized' else expected_unit
    definition = f'{key}/{p}'
    population = 'resident population; native reference dates and components explicit'
    basis = 'calendar year; resident stocks at January 1 or annual demographic events explicitly distinguished'
    if key == DEPENDENCY:
        definition = ('residents age 0–14 plus 65+' if p == 'structural' else 'residents age 65+') + ' / residents age 15–64 * 100; same sex group'
        population = 'residents in specified age bands and sex ' + (dimension.split('|sex:')[1] if '|sex:' in dimension else 'total') + ' at January 1'
        basis = 'resident stock at January 1 of reference year'
    elif key == CHANGE:
        definition = '(January 1 endpoint population - January 1 2019 population) / January 1 2019 population * 100'
        basis = 'cumulative interval anchored at January 1 2019; not annual growth'
    elif key == FOREIGN:
        definition = 'non-Italian citizens at January 1 / all residents * 100' if dimension == 'total' else 'non-Italian citizens at January 1, total or specified sex count'
        population = 'RCS residents by citizenship; not foreign-born residents'
        basis = 'resident citizenship stock at January 1 of reference year'
    elif key == NATURAL:
        definition = f'{p} annual events / arithmetic mean January 1 and December 31 residents * 1000'
        basis = 'calendar-year demographic events; mean January 1 and December 31 residents'
    elif key in MOBILITY:
        definition = f'{key} {p} residence-registration events / mean resident population * 1000'
        basis = 'calendar-year residence-transfer events; mean January 1 and December 31 residents'
    elif key in STUDENTS:
        population = 'pupils in state and private schools located in the municipality; not resident children'
        definition = 'located-school pupil count' if key == 'schoolStudents' else 'located-school pupils / classes' if key == 'studentsPerClass' else 'primary full-time pupils / all primary pupils * 100'
        basis = 'native school year 2024/25; not calendar year 2024 or 2025'
    elif key in BUILDINGS:
        field = next(s[1] for s in BUILDING_SPECS[key] if s[0] == p)
        population = f'unique MIM school buildings; {field} defined responses, or all responses for undefined share'
        definition = f'{field}/{p} count / corresponding response denominator * 100'
        basis = 'native school year 2024/25; frozen MIM data as of 2025-08-06'
    elif key == SITES:
        definition = 'published active school-site count' if dimension == 'total' else 'published school sites per 1000 residents; denominator date/components not frozen'
        population = 'school sites; distinct from MIM school buildings and pupils'
        basis = 'stock labelled 2025; exact stock date and normalized denominator date not attested'
    return dict(unit=unit, population=population, definition=definition, method=definition, frequency='annual', periodBasis=basis, adapter=f'demography-school/{key}/{dimension}/v1')


def carrier(row, key, dimension):
    p = part(key, dimension)
    if key == FOREIGN:
        if dimension.startswith('sex:'):
            groups = row.get('sexDimension', {}).get('groups', [])
            if len(groups) != 2 or {g.get('key') for g in groups} != {'men', 'women'}: raise ValueError('demography_foreign_sex_groups_changed')
            i = next(i for i, g in enumerate(groups) if 'sex:' + g['key'] == dimension)
            return groups[i], f'/sexDimension/groups/{i}', None
        if dimension == 'count': return dict(value=row.get('count'), series=row.get('componentSeries', {}).get('count')), '/count', None
        return row, '', None
    if key == SITES and dimension == 'normalized': return row.get('normalized', {}), '/normalized', None
    if key == DEPENDENCY and '|sex:' in dimension:
        sex = dimension.split('|sex:')[1]; groups = row.get('sexDimension', {}).get('groups', [])
        if len(groups) != 2 or {g.get('key') for g in groups} != {'men', 'women'}: raise ValueError('demography_dependency_sex_groups_changed')
        i = next(i for i, g in enumerate(groups) if g['key'] == sex); indices = groups[i].get('indices', [])
        if len(indices) != 2 or [v.get('key') for v in indices] != ['structural', 'elderly']: raise ValueError('demography_dependency_sex_indices_changed')
        j = 0 if p == 'structural' else 1
        return indices[j], f'/sexDimension/groups/{i}/indices/{j}', None
    if key in (DEPENDENCY, NATURAL, *MOBILITY, *BUILDINGS):
        i = (0 if p == 'structural' else 1) if key == DEPENDENCY else ('balance', 'births', 'deaths').index(p) if key == NATURAL else ('arrivals', 'departures', 'balance').index(p) if key in MOBILITY else [s[0] for s in BUILDING_SPECS[key]].index(p)
        parts = row.get('parts', [])
        expected_length = 2 if key == DEPENDENCY else 3 if key in (NATURAL, *MOBILITY) else len(BUILDING_SPECS[key])
        if len(parts) != expected_length: raise ValueError('demography_school_parts_missing_or_duplicate')
        selected = parts[i]; label = selected.get('selectorLabel', selected.get('label'))
        expected_label = DEP_LABELS[i] if key == DEPENDENCY else NAT_LABELS[i] if key == NATURAL else BUILDING_SPECS[key][i][2] if key in BUILDINGS else {MOBILITY[0]: ('Iscritti da altri Comuni', 'Cancellati verso altri Comuni', 'Saldo migratorio interno'), MOBILITY[1]: ('Iscritti dall’estero', 'Cancellati per l’estero', 'Saldo migratorio con l’estero'), MOBILITY[2]: ('Iscritti per trasferimento', 'Cancellati per trasferimento', 'Saldo complessivo dei trasferimenti')}[key][i]
        if expected_label is not None and label != expected_label: raise ValueError('demography_school_part_definition_changed')
        return selected, f'/parts/{i}', label
    return row, '', None


def available_periods(engine, key, dimension, row):
    selection_guard(key, dimension, 'series')
    if key == FOREIGN and dimension == 'count': series = row.get('componentSeries', {}).get('count')
    elif key in (DEPENDENCY, NATURAL, *MOBILITY) and dimension != 'total':
        _, _, label = carrier(row, key, dimension); series = row.get('componentSeries', {}).get(label)
    else: series = row.get('series')
    if not isinstance(series, dict): raise ValueError('demography_school_series_not_available')
    years = list(map(str, series.get('years', [])))
    if not years or len(years) != len(set(years)) or len(years) != len(series.get('values', [])): raise ValueError('demography_school_series_periods_changed')
    return sorted(('2019-' + y if key == CHANGE else token(key, y) for y in years), key=order)


def selection_guard(key, dimension, operation):
    if operation in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        if key in (SITES, *STUDENTS, *BUILDINGS): raise ValueError('demography_school_history_not_frozen')
        if '|sex:' in dimension or (key == FOREIGN and dimension.startswith('sex:')): raise ValueError('demography_sex_history_not_frozen')
        if key == CHANGE and operation == 'trend': raise ValueError('demography_cumulative_trend_not_annual_growth')


def selected_value(row, key, dimension, period, current, historical):
    selected, suffix, label = carrier(row, key, dimension)
    if not historical:
        if period != current: raise ValueError('demography_school_current_period_mismatch')
        return (row.get('value') if dimension == 'total' else selected.get('value')), ('/value' if dimension == 'total' else suffix if key == FOREIGN and dimension == 'count' else suffix + '/value'), '/meta/year'
    if key == FOREIGN and dimension == 'count': series = row.get('componentSeries', {}).get('count'); sp = '/componentSeries/count'
    elif key in (DEPENDENCY, NATURAL, *MOBILITY) and dimension != 'total':
        series = row.get('componentSeries', {}).get(label); sp = '/componentSeries/' + label.replace('~', '~0').replace('/', '~1')
    else: series = row.get('series'); sp = '/series'
    if not isinstance(series, dict): raise ValueError('demography_school_series_not_available')
    years = list(map(str, series['years']))
    if len(years) != len(set(years)) or len(years) != len(series['values']): raise ValueError('demography_school_series_periods_changed')
    native = period[-4:] if key == CHANGE else period
    if native not in years: raise ValueError('demography_school_period_not_available')
    i = years.index(native)
    return series['values'][i], f'{sp}/values/{i}', f'{sp}/years/{i}'


def status_components(statuses, p, age=False):
    if not isinstance(statuses, dict) or any(not finite(v) or v < 0 or int(v) != v for v in statuses.values()): raise ValueError('demography_school_status_counts_invalid')
    unknown = sum(v for k, v in statuses.items() if k.upper() in ('NON DEFINITO', '', '-'))
    total = math.fsum(statuses.values()); defined = total - unknown
    if age:
        reviewed = (*PERIODS, 'tra il 1993 e il 1996', 'dal 2018 in poi')
        if any(k not in reviewed and k.upper() not in ('NON DEFINITO', '', '-') for k in statuses): raise ValueError('demography_school_age_category_not_reviewed')
        n = sum(statuses.get(k, 0) for k in PERIODS[:5]) if p == 'builtBy1970' else unknown if p == 'undefined' else statuses.get(PERIODS[PERIOD_IDS.index(p)], 0)
    else:
        if set(statuses) - {'SI', 'NO', 'IN PARTE', 'NON DEFINITO', '', '-'}: raise ValueError('demography_school_response_category_not_reviewed')
        n = unknown if p == 'undefined' else statuses.get('NO' if p == 'no' else 'SI', 0)
    return n, total if p == 'undefined' else defined, unknown, total


def observation(engine, key, index, dimension, period, historical):
    metric = engine._catalog['metrics'][key]; row = metric['rows'][index]; p = part(key, dimension)
    identities, identity_ref = engine.file(CANONICAL)
    identities = [r for r in identities['metrics'][key]['rows'] if r['code'] == row['code']]
    if len(identities) != 1 or identities[0]['town'] != row['town']: raise ValueError('demography_school_geography_changed')
    ctx = context(metric, key, dimension); current = token(key, metric['meta']['year'])
    selected, _, _ = carrier(row, key, dimension)
    if ('unit' in selected and selected['unit'] != ctx['unit']) or (key in (DEPENDENCY, *BUILDINGS) and selected.get('unit') != ctx['unit']) or (key==SITES and dimension=='normalized' and selected.get('unit')!='per1000'): raise ValueError('demography_school_component_unit_changed')
    value, suffix, pp = selected_value(row, key, dimension, period, current, historical)
    rp = f'/metrics/{key}/rows/{index}'; vp = rp + suffix
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=vp, periodPointer=f'/metrics/{key}/meta/year' if pp == '/meta/year' else rp + pp)]
    evidence.append(dict(identity_ref, kind='geography_identity_snapshot', recordPointer=f'/metrics/{key}/rows', code=row['code'], town=row['town']))
    notes = []; components = {}; dates = {}; source = metric['sourceUrl']
    def frozen(path, pointer, **extra):
        snap, ref = engine.file(path); evidence.append(dict(ref, kind='source_snapshot', recordPointer=pointer, **extra)); return snap
    if key in (DEPENDENCY, NATURAL, CHANGE, *MOBILITY):
        demo = frozen(DEMO, f'/posas/towns/{row["town"]}' if key in (DEPENDENCY, CHANGE) else f'/p02/towns/{row["town"]}')
        year = period[-4:] if key == CHANGE else period
        if key == DEPENDENCY:
            if '|sex:' in dimension:
                if period != '2026': raise ValueError('demography_sex_history_not_frozen')
                sex = dimension.split('|sex:')[1]; raw = demo['posas']['ageSex2026'][row['town']]
                if len({r['age'] for r in raw}) != len(raw) or any(r['men'] + r['women'] != r['total'] for r in raw): raise ValueError('demography_age_sex_partition_changed')
                bands = [sum(number(r[sex]) for r in raw if lo <= int(r['age']) <= hi) for lo, hi in ((0, 14), (15, 64), (65, 200))]
                group = next(g for g in row['sexDimension']['groups'] if g['key'] == sex)
                if group.get('populationBands') != dict(zip(('age0to14', 'age15to64', 'age65plus'), bands)): raise ValueError('demography_dependency_sex_components_changed')
                a, d, old = bands
                evidence[-1]['recordPointer'] = f'/posas/ageSex2026/{row["town"]}'
            else:
                raw = one(demo['posas']['towns'][row['town']], period); a, d, old = (number(raw[k]) for k in ('age0to14', 'age15to64', 'age65plus'))
                close(a + d + old, raw['population'])
            n = a + old if p == 'structural' else old; scale = 100
            dates = dict(numeratorReferenceDate=period + '-01-01', denominatorReferenceDate=period + '-01-01')
            notes += ['working_age_is_not_employed_population_or_fiscal_capacity', 'age_partition_and_shared_working_age_denominator']
        elif key == CHANGE:
            raw = one(demo['posas']['towns'][row['town']], year); base = one(demo['posas']['towns'][row['town']], '2019')
            n, d, scale = number(raw['population']) - number(base['population']), number(base['population']), 100
            dates = dict(baselineReferenceDate='2019-01-01', endpointReferenceDate=year + '-01-01', denominatorReferenceDate='2019-01-01')
            notes.append('cumulative_fixed_2019_baseline_not_year_on_year_growth')
        else:
            raw = one(demo['p02']['towns'][row['town']], period); d = number(raw['meanPopulation']); scale = 1000
            close(d, (number(raw['populationJan1']) + number(raw['populationDec31'])) / 2)
            dates = dict(numeratorPeriod=period, denominatorStartDate=period + '-01-01', denominatorEndDate=period + '-12-31', denominatorBasis='arithmetic mean of frozen January 1 and December 31 populations')
            if key == NATURAL:
                close(raw['naturalBalance'], raw['births'] - raw['deaths']); n = number(raw[dict(balance='naturalBalance', births='births', deaths='deaths')[p]])
                notes += ['births_minus_deaths_not_total_population_change', 'population_change_also_contains_migration_and_statistical_adjustments']
                if raw.get('informationFlag'): notes.append('istat_demographic_information_flag:' + raw['informationFlag'])
            else:
                canonical = frozen(CANONICAL, f'/metrics/{key}/rows', limitation='published event counts or normalized history; original foreign-transfer records not frozen')
                cr = next(r for r in canonical['metrics'][key]['rows'] if r['code'] == row['code'])
                i = ('arrivals', 'departures', 'balance').index(p)
                if key == MOBILITY[0]:
                    internal = frozen(INTERNAL, f'/raw/{row["town"]}/internalResidentialMobility')
                    flow = one(internal['raw'][row['town']]['internalResidentialMobility'], period)
                    n = [number(flow['registeredIn']), number(flow['registeredOut']), flow['registeredIn'] - flow['registeredOut']][i]
                elif period == current:
                    n = number(cr['parts'][i]['count'])
                    notes.append('published_foreign_transfer_counts_not_original_archive_reconciliation')
                    if key == MOBILITY[2]:
                        other = [next(r for r in canonical['metrics'][k]['rows'] if r['code'] == row['code']) for k in MOBILITY[:2]]
                        close(n, sum(r['parts'][i]['count'] for r in other))
                else:
                    cs = cr['componentSeries'][cr['parts'][i]['label']]; j = list(map(str, cs['years'])).index(period)
                    expected = cs['values'][j]; n = None
                    if key == MOBILITY[2]:
                        values=[]
                        for k in MOBILITY[:2]:
                            other=next(r for r in canonical['metrics'][k]['rows'] if r['code']==row['code'])
                            series=other['componentSeries'][other['parts'][i]['label']]
                            values.append(series['values'][list(map(str,series['years'])).index(period)])
                        required_close(expected, math.fsum(values))
                    notes.append('published_mobility_history_no_frozen_event_numerator_no_weighting')
                if period == current: required_close(row['parts'][i].get('count'), n)
                if key == MOBILITY[2]: notes.append('total_transfers_internal_plus_foreign_not_all_demographic_balance_entries')
                notes += ['residence_registration_events_not_unique_people_or_non_italian_citizens', 'gross_municipal_transfer_flows_include_moves_within_selected_towns']
        if n is not None: components = dict(numerator=n, denominator=d, scale=scale); expected = ratio(n, d, scale)
    elif key == FOREIGN:
        hist = frozen(RCS_HISTORY, f'/towns/{row["town"]}'); raw = hist['towns'][row['town']]
        if raw['code'] != row['code'] or len(raw['years']) != len(set(raw['years'])): raise ValueError('demography_rcs_geography_or_period_changed')
        j = list(map(str, raw['years'])).index(period); n, d = number(raw['foreignCitizens'][j]), number(raw['population'][j])
        if dimension.startswith('sex:') and period != '2025': raise ValueError('demography_sex_history_not_frozen')
        if dimension.startswith('sex:') or period == '2025':
            rcs = frozen(RCS, f'/towns/{row["town"]}/citizenship'); rr = rcs['towns'][row['town']]; records = rr['citizenship']
            if rr['code'] != row['code'] or len({r['code'] for r in records}) != len(records) or any(r['men'] + r['women'] != r['total'] for r in records): raise ValueError('demography_rcs_native_partition_changed')
            close(sum(r['total'] for r in records), rr['citizenshipTotal']); close(rr['citizenshipTotal'], n)
            if dimension.startswith('sex:'):
                if period != '2025': raise ValueError('demography_sex_history_not_frozen')
                expected = sum(number(r[dimension.removeprefix('sex:')]) for r in records)
                close(row['sexDimension'].get('total'), n); close(next(g for g in row['sexDimension']['groups'] if 'sex:' + g['key'] == dimension).get('count'), expected)
        if dimension == 'total': expected = ratio(n, d, 100); components = dict(numerator=n, denominator=d, scale=100)
        elif dimension == 'count': expected = n
        if period == current: required_close(row.get('count'), n); required_close(row.get('population'), d)
        dates = dict(numeratorReferenceDate=period + '-01-01', denominatorReferenceDate=period + '-01-01')
        notes += ['citizenship_not_country_of_birth_or_residential_transfer_origin', 'sex_counts_not_shares_without_sex_specific_resident_denominators', 'country_breakdowns_not_adapted_no_citizenship_birth_country_cross_tab']
    elif key in STUDENTS:
        lia = frozen(LIA, '/raw/mim2024_25', archiveManifest=engine.file(LIA)[0]['sources']['mimSchool2024_25'])
        files = lia['sources']['mimSchool2024_25']['files']
        if not files or any(not re.fullmatch(r'[0-9a-f]{64}', f.get('sha256','')) or not isinstance(f.get('bytes'),int) or f['bytes'] <= 0 or not f.get('url','').startswith('https://dati.istruzione.it/') for f in files): raise ValueError('demography_mim_archive_manifest_changed')
        matches = [r for r in lia['raw']['mim2024_25'] if r['code'] == row['code']]
        if len(matches) != 1 or matches[0]['town'] != row['town']: raise ValueError('demography_mim_geography_changed')
        raw = matches[0]
        if key == 'schoolStudents': expected = number(raw['students'])
        else:
            n, d, scale = (raw['students'], raw['classes'], 1) if key == 'studentsPerClass' else (raw['full_time_students'], raw['primary_students'], 100)
            expected = ratio(n, d, scale); components = dict(numerator=n, denominator=d, scale=scale)
            a3 = row.get('a3SchoolComponents')
            if a3 is not None and (a3.get('referenceYear') != 'a.s. 2024/25' or a3.get('sourceSnapshot') != LIA): raise ValueError('demography_mim_component_reference_changed')
            if a3 is not None:
                for field, actual in (('numerator', n), ('denominator', d), ('scale', scale)): required_close(a3.get(field), actual)
        dates = dict(numeratorPeriod='2024/25', denominatorPeriod='2024/25')
        notes += ['located_school_pupils_not_resident_children_or_service_coverage', 'school_year_not_calendar_year', 'classes_not_buildings_or_sites', 'full_time_classification_not_service_quality_or_parental_employment_effect']
    elif key in BUILDINGS:
        snap = frozen(BUILDING, f'/towns/{row["town"]}'); raw = snap['towns'][row['town']]
        if snap['schoolYear'] != period or snap['dataAsOf'] != '2025-08-06': raise ValueError('demography_mim_building_reference_changed')
        close(sum(r['buildings'] for r in snap['towns'].values()), snap['uniqueBuildingsVersilia'])
        field = next(s[1] for s in BUILDING_SPECS[key] if s[0] == p)
        n, d, unknown, total = status_components(raw[field], p, key == BUILDINGS[3])
        close(total, raw['buildings']); required_close(row.get('buildings'), total)
        selected, _, _ = carrier(row, key, dimension)
        for name, actual in (('count', n), ('defined', d), ('unknown', unknown)): required_close(selected.get(name), actual)
        expected = ratio(n, d, 100); components = dict(numerator=n, denominator=d, scale=100)
        dates = dict(numeratorPeriod=period, denominatorPeriod=period, sourceDataAsOf=snap['dataAsOf'], undefinedResponses=unknown, totalBuildings=total)
        notes += ['undefined_responses_not_no_or_zero', 'response_denominator_varies_by_field', 'declared_building_attributes_not_certification_quality_capacity_or_pupil_access']
        if key == BUILDINGS[0]: notes.append('cpi_scia_renewal_separate_no_unverified_or_combination')
        if key == BUILDINGS[3]: notes.append('building_construction_age_not_structural_risk')
    else:
        canonical = frozen(CANONICAL, f'/metrics/{key}/rows', limitation='published school-site carrier; original records and normalized denominator date not frozen')
        cm = canonical['metrics'][key]
        if cm['meta']['year'] != metric['meta']['year'] or cm['sourceUrl'] != source: raise ValueError('demography_school_site_reference_changed')
        cr = next(r for r in cm['rows'] if r['code'] == row['code']); expected = cr['normalized']['value'] if dimension == 'normalized' else cr['value']
        notes += ['school_sites_not_unique_buildings_or_pupil_capacity', 'school_site_stock_and_normalized_denominator_dates_not_attested']
    close(value, expected)
    if period == current:
        selected, _, _ = carrier(row, key, dimension); close(selected.get('value'), expected)
        if dimension == 'total': close(row.get('value'), expected)
    return dict(ctx, **components, **dates, metric=key, dimension=dimension, geography=row['code'], period=period, value=value, source=source, evidence=evidence, provenance=evidence,
                notApplicable=bool(row.get('notApplicable')) if not historical else False, dataUnavailable=value is None or (bool(row.get('dataUnavailable')) if not historical else False)), notes


def benchmark(engine, key, scope, municipal):
    dimension = municipal['dimension']; p = part(key, dimension); period = municipal['period']
    if scope not in benchmark_scopes(key, dimension): raise ValueError('demography_school_benchmark_dimension_not_frozen_or_absolute_volume_not_comparable')
    path = MOB_BENCH if key in MOBILITY else MIM_BENCH if key in STUDENTS else BUILDING_BENCH if key in BUILDINGS else DEMO_BENCH
    snap, ref = engine.file(path); source = engine._catalog['metrics'][key]['sourceUrl']
    if key in BUILDINGS:
        if period != snap['schoolYear']: raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['raw'][key][scope]; n, d, unknown, total = status_components(raw['statuses'], p, key == BUILDINGS[3]); close(total, raw['buildings']); scale = 100
        source = snap['sources'][key]; pointer = f'/raw/{key}/{scope}'
    elif key in STUDENTS:
        if period != snap['schoolYear']: raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['raw'][scope]; n, d, scale = (raw['schoolStudents'], raw['classes'], 1) if key == 'studentsPerClass' else (raw['fullTimeStudents'], raw['primaryStudents'], 100)
        pointer = f'/raw/{scope}'
    elif key in MOBILITY:
        if period != '2024': raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['components'][scope]; d = raw['meanPopulation']; close(d, (raw['jan1'] + raw['dec31']) / 2); scale = 1000
        inbound, outbound = (raw['internalIn'], raw['internalOut']) if key == MOBILITY[0] else (raw['foreignIn'], raw['foreignOut']) if key == MOBILITY[1] else (raw['internalIn'] + raw['foreignIn'], raw['internalOut'] + raw['foreignOut'])
        n = dict(arrivals=inbound, departures=outbound, balance=inbound - outbound)[p]; pointer = f'/components/{scope}'
    elif key == FOREIGN:
        if period != '2025': raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['rcs']['scopes'][scope]; n, d, scale = raw['foreign'], raw['population'], 100; pointer = f'/rcs/scopes/{scope}'
    elif key == CHANGE:
        if period != '2019-2026': raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['components'][scope][CHANGE]; n, d, scale = raw['end2026'] - raw['start2019'], raw['start2019'], 100; pointer = f'/components/{scope}/{CHANGE}'
    elif key == DEPENDENCY:
        if period != '2026': raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['components'][scope]['ageDistribution']; n = raw['age65plus'] + (raw['age0_14'] if p == 'structural' else 0); d, scale = raw['age15_64'], 100; pointer = f'/components/{scope}/ageDistribution'
    else:
        if period != '2025': raise ValueError('demography_school_benchmark_period_not_available')
        raw = snap['components'][scope][NATURAL]; close(raw['naturalBalance'], raw['births'] - raw['deaths']); n = raw[dict(balance='naturalBalance', births='births', deaths='deaths')[p]]; d, scale = raw['meanPopulation'], 1000; pointer = f'/components/{scope}/{NATURAL}'
    value = ratio(n, d, scale)
    default = dimension == 'total' or p == ('structural' if key == DEPENDENCY else 'balance' if key in (NATURAL, *MOBILITY) else BUILDING_SPECS[key][0][0] if key in BUILDINGS else 'total')
    if default:
        close(snap['benchmarks'][key][scope], value)
        bm = engine._catalog['metrics'][key]['meta'].get('benchmark', {})
        close(bm.get(scope), value)
        if str(bm.get('year')).replace('–', '-') != period: raise ValueError('demography_school_public_benchmark_reference_changed')
    evidence = [dict(ref, kind='benchmark_source_snapshot', recordPointer=pointer, sourceUrl=source)]
    return dict(context(engine._catalog['metrics'][key], key, dimension), metric=key, dimension=dimension, geography=scope, period=period, value=value, numerator=n, denominator=d, scale=scale, source=source, evidence=evidence, provenance=evidence)


def correlation_guard(observations, axis):
    if any(o['metric'] == SITES for o in observations): raise ValueError('demography_school_site_observation_dates_not_attested_for_pairing')
    if axis == 'periods' and any(o['metric'] == CHANGE for o in observations): raise ValueError('demography_overlapping_cumulative_windows_not_temporal_correlation')
