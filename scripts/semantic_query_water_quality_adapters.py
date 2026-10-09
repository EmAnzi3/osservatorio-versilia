"""GAIA locality/parameter lookup; reported bounds are never exact amounts."""
import hashlib
import json

from semantic_operations import reported_measurement

KEYS = ('drinkingWaterQuality',)
NATIVE = 'data/source-snapshots/ambiente-acqua-v124-data.json'
URL = 'https://www.gaia-spa.it/analisiweb_v2/'
PERIOD = '2° semestre 2025'
FILE_SHA = '7ae5d8961e39e1d7f5dac60cfbb6e7e9c48ec9e89828dcc34816218d7e44d679'
STRUCTURE_SHA = '870cde2674be112734acdc29fb90d7fb738d55f152088f680f28422165e117a4'


def dimensions(key):
    return ['parameter:'+str(i) for i in range(17)]


def context(metric, key, dimension):
    meta = metric['meta']
    if dimension not in dimensions(key):
        raise ValueError('water_quality_explicit_parameter_required')
    if meta.get('unit') != 'number' or meta.get('year') != PERIOD or meta.get('compositeType') != key or metric.get('sourceUrl') != URL or meta.get('sourceMeta',{}).get('snapshot') != NATIVE or metric.get('method',{}).get('snapshot') != NATIVE:
        raise ValueError('water_quality_definition_or_reference_changed')
    p = metric['parameterDefinitions'][int(dimension.split(':')[1])]
    return dict(unit=p['unit'], population='GAIA served areas/localities; not municipal resident populations',
        definition='GAIA published locality mean: '+p['name'],
        method='verbatim frozen GAIA locality/parameter lookup; no concentration aggregation, substitution or compliance assessment',
        frequency='semester_snapshot', adapter='water-quality/locality-parameter/v1')


def select(engine, selector, operation):
    if operation != 'lookup':
        raise ValueError('water_quality_arithmetic_or_association_not_supported')
    key = selector['metric']
    dimension = selector.get('dimension','total')
    metric = engine._catalog['metrics'][key]
    ctx = context(metric,key,dimension)
    periods = selector.get('periods',[PERIOD])
    if periods != [PERIOD]:
        raise ValueError('water_quality_period_not_frozen')
    towns = selector.get('towns',sorted(engine.codes))
    if not isinstance(towns,list) or not towns or any(not isinstance(c,str) or c not in engine.codes for c in towns) or len(towns) != len(set(towns)):
        raise ValueError('unknown_or_duplicate_geography')
    snap, ref = engine.file(NATIVE)
    structure = hashlib.sha256(json.dumps(snap,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if ref.get('sha256') != FILE_SHA or structure != STRUCTURE_SHA:
        raise ValueError('water_quality_frozen_input_changed')
    native = snap['drinkingWaterQuality']
    if metric.get('parameterDefinitions') != native['parameterDefinitions']:
        raise ValueError('water_quality_parameter_definition_changed')
    canonical = {t['code']:t['name'] for t in engine._catalog['towns']}
    rows = metric['rows']
    if len(rows) != len(canonical) or {r['code'] for r in rows} != set(canonical):
        raise ValueError('water_quality_municipal_identity_changed')
    # Validate the full public/native mapping on every access, including cache.
    # Primary counts attest detail coverage only; they never enter observations.
    for row in rows:
        expected = [l for l in native['localities'] if l['townCode'] == row['code']]
        if row.get('town') != canonical[row['code']] or row.get('slug') != '-'.join(row['town'].lower().split()) or row.get('notApplicable') or row.get('dataUnavailable'):
            raise ValueError('water_quality_municipal_identity_changed')
        if row.get('localities') != expected or type(row.get('value')) is not int or row['value'] != len(expected) or row.get('series') is not None:
            raise ValueError('water_quality_public_native_mismatch')
    identities = [l['sampleCode']+'/'+l['sampleCode2'] for l in native['localities']]
    if len(identities) != len(set(identities)):
        raise ValueError('water_quality_duplicate_locality')
    selected = selector.get('localities')
    allowed = {identities[i] for i,l in enumerate(native['localities']) if l['townCode'] in towns}
    if selected is not None and (not isinstance(selected,list) or not selected or any(not isinstance(i,str) or i not in allowed for i in selected) or len(selected) != len(set(selected))):
        raise ValueError('water_quality_unknown_duplicate_or_out_of_scope_locality')
    p = int(dimension.split(':')[1])
    parameter = native['parameterDefinitions'][p]
    result = []
    for index,l in enumerate(native['localities']):
        identity = identities[index]
        if l['townCode'] not in towns or selected is not None and identity not in selected:
            continue
        if l['period'] != '2° Semestre 2025' or len(l['values']) != len(native['parameterDefinitions']):
            raise ValueError('water_quality_native_period_or_axis_changed')
        raw = l['values'][p]
        qualifier, number = reported_measurement(raw)
        ri = next(i for i,r in enumerate(rows) if r['code'] == l['townCode'])
        li = next(i for i,x in enumerate(rows[ri]['localities']) if x['sampleCode']+'/'+x['sampleCode2'] == identity)
        evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{ri}/localities/{li}/values/{p}',parameterPointer=f'/metrics/{key}/parameterDefinitions/{p}'),
            dict(ref,kind='source_snapshot',recordPointer=f'/drinkingWaterQuality/localities/{index}/values/{p}',parameterPointer=f'/drinkingWaterQuality/parameterDefinitions/{p}')]
        result.append(dict(ctx,metric=key,dimension=dimension,geography=l['townCode'],period=PERIOD,
            locality=identity,localityName=l['name'],localityTitle=l['title'],sampleCode=l['sampleCode'],sampleCode2=l['sampleCode2'],
            parameter=parameter['name'],referenceText=parameter['reference'],sourcePeriod=l['period'],
            value=raw,sourceValue=raw,valueKind='source_reported_measurement',reportedQualifier=qualifier,reportedNumber=number,
            source=l['url'],evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False))
    return result,['water_quality_locality_means_not_municipal_means',
        'water_quality_censored_values_not_exact_no_substitution',
        'water_quality_frozen_reference_text_not_compliance_or_potability_assessment',
        'water_quality_frozen_snapshot_not_live_or_new_laboratory_validation']
