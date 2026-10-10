"""Frozen INVALSI school-location observations; no pooling or inferred continuity."""
import base64
import gzip
import hashlib
import json
import re

from semantic_query_library_adapters import TOWNS, fingerprint
from semantic_operations import finite

KEYS = ('invalsiResults', 'invalsiCompetence', 'invalsiImplicitDispersion', 'invalsiAcademicExcellence')
BLOCKS = dict(zip(KEYS, ('results', 'competence', 'implicitDispersion', 'academicExcellence')))
DEFAULTS = dict(zip(KEYS, ('g5-italiano', 'g5-inglese-reading', 'g8', 'g8')))
UNITS = dict(zip(KEYS, ('invalsi_score', 'percent', 'percent', 'percent')))
RESULT_VIEWS = ('g2-italiano', 'g2-matematica', 'g5-italiano', 'g5-matematica',
                'g5-inglese-reading', 'g5-inglese-listening', 'g8-italiano', 'g8-matematica',
                'g8-inglese-reading', 'g8-inglese-listening', 'g10-italiano', 'g10-matematica',
                'g13-italiano', 'g13-matematica', 'g13-inglese-reading', 'g13-inglese-listening')
VIEWS = dict(zip(KEYS, (RESULT_VIEWS, RESULT_VIEWS[4:], ('g8', 'g13'), ('g8', 'g13'))))
LEVELS = {v: (('Pre-A1', 'A1') if v.startswith('g5-') else
              ('Pre-A1', 'A1', 'A2') if v.startswith('g8-inglese') else
              ('Non ancora B1', 'B1', 'B2') if v.startswith('g13-inglese') else
              tuple('Livello '+str(i) for i in range(1, 6))) for v in VIEWS[KEYS[1]]}
DIRECTORY = 'data/source-snapshots/invalsi-v138-b64'
PART_HASHES = ('d4581ad9dd7f7211a8efc16055a3fd5e1702a34c9773cb94bb912680b326f344',
               '040aa9ff1a19788d8672cfee9c80efbeeda553ccf1a506bc9f69c6e8dee53c7a',
               '1df9c03c6f8788c940d8a1ba71aa8302d38b883f32950ff662314496c1d183b3',
               'cf6bdc1d92cf66fc415d49d0e8a329acf32e36b48c19031ecc7fe40cd0c087d7',
               '92b832d8345e5146e3aa1cd9c0e01f1f4293e8c682ee354aa732413355ec3c15')
PAYLOAD_SHA = 'bee5b0021704b2053277aa19df35d77ed0aa4b9e2cfc4dfa3d64c16a61c1fd65'
FINGERPRINT = 'e3b6fbe41f8dd4090b85a5ddc74904137c1c65f4597e63e2f8a7d29924b16b46'
NOTES = ['invalsi_comune_plesso_not_student_residence', 'invalsi_aggregation_totale_same_grade_subject_academic_year',
         'invalsi_missing_or_suppressed_cells_not_zero_or_absence_of_schools',
         'invalsi_2019_20_tests_not_conducted_gap_preserved',
         'invalsi_participation_and_coverage_percentages_not_valid_student_denominators',
         'invalsi_published_precision_retained_no_versilia_mean',
         'invalsi_numeric_rank_not_school_quality_or_policy_priority']


def equal(actual, expected):
    if actual != expected or (expected is not None and not finite(actual)):
        raise ValueError("invalsi_public_native_value_changed")


def frozen(engine):
    parts = [dict(path=f'{DIRECTORY}/part-{i:02}.b64', sha256=h) for i, h in enumerate(PART_HASHES)]
    reference = dict(kind='reconstructed_source_snapshot', path=DIRECTORY, sha256=PAYLOAD_SHA,
                     sha256Basis='decoded_json_bytes', encoding='concatenate_ascii_base64_gzip_json', parts=parts)
    if not hasattr(engine, '_invalsi_payload'):
        bodies = [(engine.root/p['path']).read_bytes() for p in parts]
        if any(hashlib.sha256(b).hexdigest() != p['sha256'] for b, p in zip(bodies, parts)):
            raise ValueError('invalsi_frozen_fragment_changed')
        raw = gzip.decompress(base64.b64decode(b''.join(b.strip() for b in bodies), validate=True))
        if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA:
            raise ValueError('invalsi_frozen_payload_changed')
        engine._invalsi_payload = json.loads(raw), reference
    native, ref = engine._invalsi_payload
    if ref != reference or fingerprint(native) != FINGERPRINT:
        raise ValueError('invalsi_frozen_payload_changed')
    return native, ref


def token(key, period):
    p = str(period)
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}', p) or int(p[-2:]) != (int(p[:4])+1) % 100:
        raise ValueError('invalsi_academic_year_required')
    return p


def order(period): return int(period[:4])
def scopes(key, dim): return ['tuscany', 'italy']


def dimensions(key):
    out = ['total'] + ['view:'+v for v in VIEWS[key]]
    if key == KEYS[1]:
        out += ['view:'+v+'|level:level-'+str(i+1) for v in VIEWS[key] for i in range(len(LEVELS[v]))]
    return out


def resolve(key, dim):
    if dim not in dimensions(key): raise ValueError('invalsi_dimension_not_reviewed')
    v = DEFAULTS[key] if dim == 'total' else dim.split('|')[0][5:]
    level = int(dim.split('|level:level-')[1])-1 if '|level:' in dim else None
    return v, level


def operations(key, dim):
    return ['compare', 'rank', 'benchmark_gap'] + ([] if '|level:' in dim else ['series'])


def selection_guard(key, dim, op):
    if op == 'weighted_ratio': raise ValueError('invalsi_valid_student_denominators_unavailable')
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('invalsi_temporal_continuity_not_reviewed')
    if op == 'correlation': raise ValueError('invalsi_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('invalsi_peer_anomaly_not_reviewed')
    if op == 'series' and '|level:' in dim: raise ValueError('invalsi_level_history_not_published_in_catalog')


def context(metric, key, dim):
    v, level = resolve(key, dim); meta = metric['meta']
    if (meta.get('key') != key or meta.get('unit') != UNITS[key] or meta.get('year') != '2024-25'
            or meta.get('defaultView') != DEFAULTS[key] or meta.get('compositeType') != 'invalsiProfile'
            or meta.get('academicYearSeries') is not True or meta.get('comparisonReference') != 'aggregate'
            or meta.get('aggregateLabel') != 'Toscana' or meta.get('allowPartialHistory') is not True):
        raise ValueError('invalsi_definition_changed')
    return dict(unit=UNITS[key], population='tested students by municipality of school location, official Totale aggregation',
                definition=BLOCKS[key]+'/'+v+('/'+LEVELS[v][level] if level is not None else '/published value'),
                method='direct official municipal aggregate; grade, subject and academic year kept distinct; no pooling',
                frequency='academic_year', periodBasis='academic year label; no 2019-20; grade10 excludes 2020-21',
                grade=int(v.split('-')[0][1:]), subject=v.split('-', 1)[1] if '-' in v else None,
                levelLabel=LEVELS[v][level] if level is not None else None,
                nativeComponentsAvailable=False, adapter='invalsi/'+key+'/'+v+'/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    native, ref = frozen(engine); block = native[BLOCKS[key]]; views = block['views']
    url = native['sources']['results' if key in KEYS[:2] else 'dispersionExcellence']['page']
    if metric.get('sourceUrl') != url or block['unit'] != UNITS[key]:
        raise ValueError('invalsi_source_definition_changed')
    if ({t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS or len(metric['rows']) != 7
            or {r.get('code') for r in metric['rows']} != set(TOWNS)):
        raise ValueError('invalsi_municipal_identity_changed')
    definitions = []
    for v in views:
        d = dict(key=v['key'], label=v['selectorLabel'], grade=v['grade'], gradeLabel=v['gradeLabel'],
                 subject=v['subject'], subjectLabel=v['subjectLabel'], academicYear=v['latestYear'],
                 coverage=v['currentCoverage'], years=v['years'])
        if key == KEYS[1]:
            if tuple(v['levelLabels']) != LEVELS[v['key']]: raise ValueError('invalsi_level_labels_changed')
            d['levelLabels'] = v['levelLabels']
        definitions.append(d)
    if metric.get('viewDefinitions') != definitions:
        raise ValueError('invalsi_view_definitions_changed')
    for row in metric['rows'] + [metric['aggregate'], metric['nationalBenchmark']]:
        if 'code' in row:
            name = TOWNS[row['code']]
            if (row.get('town') != name or row.get('slug') != '-'.join(name.lower().split())
                    or row.get('notApplicable') or row.get('dataUnavailable')):
                raise ValueError('invalsi_municipal_identity_changed')
            scope = name
        else:
            scope = 'tuscany' if row is metric['aggregate'] else 'italy'
            if row.get('label') != ('Toscana' if scope == 'tuscany' else 'Italia'):
                raise ValueError('invalsi_official_benchmark_changed')
        histories = {}; level_views = {}; parts = []
        for v in views:
            record = v['municipalities'][scope] if scope in TOWNS.values() else v[scope]
            vals = record['values']; years = v['years']
            histories[v['key']] = dict(years=[int(p[:4])+1 for p in years], values=vals, periodLabels=years)
            part = dict(key=v['key'], label=v['selectorLabel'], value=vals[-1], unit=UNITS[key],
                        grade=v['grade'], gradeLabel=v['gradeLabel'], subject=v['subject'], subjectLabel=v['subjectLabel'],
                        academicYear=v['latestYear'], coverage=v['currentCoverage'])
            if key == KEYS[1]:
                lev = record['levels'][-1]
                part.update(levelLabels=v['levelLabels'], levels=None if lev is None else
                            [dict(key='level-'+str(i+1), label=l, value=lev[i]) for i,l in enumerate(v['levelLabels'])])
                level_views[v['key']] = dict(labels=v['levelLabels'], values=lev, academicYear=v['latestYear'])
            parts.append(part)
        # Formatting strings are presentation-only; every analytical field is checked.
        for p in row.get('parts', []):
            if p.get('value') is not None and not finite(p['value']):
                raise ValueError('invalsi_public_native_value_changed')
            if key == KEYS[1] and p.get('levels') is not None:
                if any(not finite(l.get('value')) for l in p['levels']):
                    raise ValueError('invalsi_public_native_value_changed')
        actual_parts = [{k:p.get(k) for k in expected} for p, expected in zip(row.get('parts', []), parts)]
        if len(row.get('parts', [])) != len(parts) or actual_parts != parts or row.get('seriesByView') != histories:
            raise ValueError('invalsi_public_native_views_changed')
        if key == KEYS[1] and row.get('invalsiLevelsByView') != level_views:
            raise ValueError('invalsi_public_native_levels_changed')
        default = next(p for p in parts if p['key'] == DEFAULTS[key])
        equal(row.get('value'), default['value'])
        if row.get('series') != histories[DEFAULTS[key]]:
            raise ValueError('invalsi_public_default_history_changed')
        if row.get('normalized') is not None or row.get('ratioComponents') is not None or row.get('benchmarkValue') is not None:
            raise ValueError('invalsi_unreviewed_components_changed')
    if metric.get('normalizedAggregate') is not None:
        raise ValueError('invalsi_unreviewed_components_changed')
    return native, ref


def available_periods(engine, key, dim, row):
    native, _ = validated(engine, key); v, level = resolve(key, dim)
    if level is not None: raise ValueError('invalsi_level_history_not_published_in_catalog')
    return next(x['years'] for x in native[BLOCKS[key]]['views'] if x['key'] == v)


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    native, ref = validated(engine, key); vkey, level = resolve(key, dim)
    vi = VIEWS[key].index(vkey); view = native[BLOCKS[key]]['views'][vi]
    if period not in view['years']: raise ValueError('invalsi_period_not_frozen')
    if level is not None and period != view['latestYear']:
        raise ValueError('invalsi_level_history_not_published_in_catalog')
    pi = view['years'].index(period); row = metric['rows'][index]; record = view['municipalities'][row['town']]
    suffix = f'values/{pi}' if level is None else f'levels/{pi}' + (f'/{level}' if record['levels'][pi] is not None else '')
    value = record['values'][pi] if level is None else (record['levels'][pi][level] if record['levels'][pi] is not None else None)
    public = f'/metrics/{key}/rows/{index}/seriesByView/{vkey}/values/{pi}'
    if level is not None:
        public = f'/metrics/{key}/rows/{index}/parts/{vi}/levels' + (f'/{level}/value' if value is not None else '')
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=public),
                dict(ref, recordPointer=f'/{BLOCKS[key]}/views/{vi}/municipalities/{row["town"]}/{suffix}')]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value,
                source=metric['sourceUrl'], evidence=evidence, provenance=evidence, notApplicable=False,
                dataUnavailable=value is None, missingReason='official_cell_missing_or_suppressed' if value is None else None), NOTES


def benchmark(engine, key, scope, municipal):
    if scope not in scopes(key, municipal['dimension']): raise ValueError('invalsi_benchmark_scope_not_reviewed')
    native, ref = validated(engine, key); vkey, level = resolve(key, municipal['dimension'])
    vi = VIEWS[key].index(vkey); view = native[BLOCKS[key]]['views'][vi]; pi = view['years'].index(municipal['period'])
    record = view[scope]; value = record['values'][pi] if level is None else record['levels'][pi][level]
    field = 'aggregate' if scope == 'tuscany' else 'nationalBenchmark'
    public = f'/metrics/{key}/{field}/seriesByView/{vkey}/values/{pi}' if level is None else f'/metrics/{key}/{field}/parts/{vi}/levels/{level}/value'
    suffix = f'values/{pi}' if level is None else f'levels/{pi}/{level}'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=public),
                dict(ref, recordPointer=f'/{BLOCKS[key]}/views/{vi}/{scope}/{suffix}')]
    return dict(municipal, geography=scope, value=value, evidence=evidence, provenance=evidence,
                dataUnavailable=False, missingReason=None,
                benchmarkAggregation='official Totale aggregation for identical academic year, grade and subject; not Versilia mean')
