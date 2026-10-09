"""Frozen municipal category lookup; numeric codes never become quantities."""
import hashlib
import json

KEYS = ('territorialClassification',)
NATIVE = 'data/source-snapshots/territorio-ucs-v136.json'
URL = 'https://www.istat.it/comunicato-stampa/geografie-funzionali-per-lanalisi-territoriale/'
FILE_SHA = '22211f2d42aa8a23957c05ec03f35038e6ebf58f89ba18b46e39e61a1a35697a'
STRUCTURE_SHA = '621307d00dc707043566f4c28dcacfd8321fb936f07de4f7d8cb3aae6849d895'
FIELDS = ('degurba', 'littoral', 'coastalZone')

def dimensions(key):
    return ['total', *('part:'+f for f in FIELDS)]

def field(dimension):
    return 'degurba' if dimension == 'total' else dimension[5:]

def operations(key, dimension):
    return ['compare']

def selection_guard(key, dimension, operation):
    if operation != 'compare':
        raise ValueError('classification_category_arithmetic_or_association_not_supported')

def context(metric, key, dimension):
    meta = metric['meta']
    if dimension not in dimensions(key) or meta.get('unit') != 'number' or str(meta.get('year')) != '2021' or meta.get('compositeType') != key or metric.get('sourceUrl') != URL:
        raise ValueError('classification_definition_or_reference_changed')
    f = field(dimension)
    return dict(unit='category_code', population='seven canonical municipalities; official frozen municipal classification',
        definition={'degurba':'DEGURBA named municipal category; code is not a cardinal amount', 'littoral':'official littoral membership; distinct from coastal-zone membership', 'coastalZone':'official coastal-zone membership; does not imply a municipal coastline'}[f],
        method='Istat frozen categorical attributes; label-preserving lookup only, no ranking or cardinal transformations',
        frequency='snapshot', periodBasis='reference 2021; functional-geographies publication 2026-03-17, not a 2026 reclassification',
        adapter='classification/'+f+'/v1')

def observation(engine, key, index, dimension, period, historical):
    metric = engine._catalog['metrics'][key]
    row = metric['rows'][index]
    ctx = context(metric, key, dimension)
    if period != '2021':
        raise ValueError('classification_period_not_frozen')
    snap, ref = engine.file(NATIVE)
    structure = hashlib.sha256(json.dumps(snap, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    if ref.get('sha256') != FILE_SHA or structure != STRUCTURE_SHA:
        raise ValueError('classification_frozen_input_changed')
    towns = {t['code']:t['name'] for t in engine._catalog['towns']}
    rows = metric['rows']
    if len(rows) != 7 or {r['code'] for r in rows} != set(towns) or set(snap['classifications']) != set(towns.values()) or towns.get(row['code']) != row['town'] or row.get('slug') != '-'.join(row['town'].lower().split()) or row.get('notApplicable') or row.get('dataUnavailable'):
        raise ValueError('classification_identity_or_availability_changed')
    native = snap['classifications'][row['town']]
    expected = {f:native[f] for f in (*FIELDS, 'degurbaLabel')}
    if row.get('classification') != expected or any(type(row['classification'].get(f)) is not bool for f in ('littoral','coastalZone')) or type(row.get('value')) is not int or row['value'] != native['degurba'] or type(row['classification']['degurba']) is not int or row.get('series') is not None:
        raise ValueError('classification_public_native_mismatch')
    f = field(dimension)
    source_value = native[f]
    # 0/1 encode membership for the existing finite-value compare contract;
    # the source boolean and its label are retained and arithmetic is refused.
    value = source_value if f == 'degurba' else int(source_value)
    label = native['degurbaLabel'] if f == 'degurba' else ('sì' if source_value else 'no')
    pointer = f'/metrics/{key}/rows/{index}/'+('value' if dimension == 'total' else 'classification/'+f)
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer),
        dict(ref, kind='source_snapshot', recordPointer='/classifications/'+row['town']+'/'+f)]
    return dict(ctx, metric=key, dimension=dimension, geography=row['code'], period=period, value=value,
        sourceValue=source_value, categoryLabel=label, valueEncoding='official DEGURBA category code' if f == 'degurba' else 'false=0, true=1; membership code, not measured zero/one',
        source=URL, evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=False), [
        'classification_codes_not_amounts_no_mean_rank_or_changes', 'classification_littoral_not_coastal_zone',
        'classification_reference_2021_not_publication_2026', 'classification_frozen_categories_no_new_geographic_or_microdata_validation']
