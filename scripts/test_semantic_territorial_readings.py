#!/usr/bin/env python3
"""Independent references and fail-closed checks for A6 territorial pilots."""
import copy
import json
import math
import tempfile
from fractions import Fraction
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT
from semantic_query_adapters import AGE_BANDS, AGE_SNAPSHOT
from semantic_query_territorial_adapters import CHILD, DEMOGRAPHY, TOURISM, ARS
from semantic_territorial_readings import build_readings, markdown, query
from test_semantic_query_engine import rejected


def close(actual, expected):
    assert math.isclose(actual,float(expected),abs_tol=1e-10), (actual,expected)


def regressions(catalog_path):
    engine=QueryEngine(catalog_path,layer='effective')
    for dimension in AGE_BANDS:
        for scope in ('tuscany','italy'):
            r=engine.query(query('benchmark_gap','ageDistribution',dimension,towns=['046018'],benchmark=scope))
            assert r['status']=='computed',r
            assert r['observations'][1]['dimension']==dimension
            assert r['observations'][1]['evidence'][0]['path']==DEMOGRAPHY
    r=engine.query(query('benchmark_gap','ageDistribution','age:85+',towns=['046018'],benchmark='tuscany'))
    close(r['result']['value'],(Fraction(892,21782)-Fraction(183801,3659222))*100)
    # The primary benchmark is 20–34 and must not substitute for the 85+ band.
    assert r['result']['benchmarkValue']!=engine.catalog['metrics']['ageDistribution']['meta']['benchmark']['tuscany']
    for dimension,count in [('sex:men',10736),('sex:women',11046)]:
        r=engine.query(query('compare','population',dimension))
        assert r['status']=='computed',r
        assert next(o['value'] for o in r['observations'] if o['geography']=='046018')==count
        assert all('/sexDimension/groups/' in o['evidence'][0]['valuePointer'] for o in r['observations'])
        rejected(engine,query('series','population',dimension,towns=['046018']),'historical_dimension_not_available')
    child=engine.query(query('weighted_ratio','earlyChildhoodPotentialCapacityRate'))
    assert child['status']=='computed',child
    close(child['result']['value'],Fraction(1031,2217)*100)
    assert child['result']['period']=='2024/25'
    zeros=[o for o in child['observations'] if o['geography'] in ('046028','046030')]
    assert len(zeros)==2 and all(o['value']==0 and not o['dataUnavailable'] for o in zeros)
    rejected(engine,query('compare','earlyChildhoodPotentialCapacityRate',periods=['2024']),'educational_year_token_required')
    rejected(engine,query('series','earlyChildhoodPotentialCapacityRate',towns=['046018']),'historical_dimension_not_available')
    rejected(engine,query('benchmark_gap','earlyChildhoodPotentialCapacityRate',towns=['046018'],benchmark='italy'),'scope_not_available')
    gap=engine.query(query('benchmark_gap','earlyChildhoodPotentialCapacityRate',towns=['046018'],benchmark='tuscany'))
    close(gap['result']['value'],(Fraction(87,297)-Fraction(28077,59052))*100)
    change=engine.query(query('absolute_change','tourismPresences',towns=['046018'],periods=['2023','2025']))
    assert change['status']=='computed' and change['result']['value']==2791,change
    pressure=engine.query(query('weighted_ratio','tourismIntensity'))
    assert pressure['status']=='computed',pressure
    close(pressure['result']['value'],Fraction(2225932,158520))
    assert pressure['result']['numeratorPeriod']=='2025' and pressure['result']['denominatorPeriod']=='2026'
    assert 'tourism_flow_2025_resident_stock_2026' in pressure['warnings']
    rejected(engine,query('benchmark_gap','tourismIntensity',towns=['046018'],benchmark='italy'),'scope_or_period_not_available')
    for dimension,value in [('sex:total',30.085),('sex:men',21.8674),('sex:women',34.5972)]:
        r=engine.query(query('compare','elderlyHomeCare',dimension))
        assert r['status']=='computed',r
        obs=next(o for o in r['observations'] if o['geography']=='046018')
        assert obs['value']==value and 'numerator' not in obs and 'denominator' not in obs
        assert obs['evidence'][1]['reportedNumerator'] in (174,49,125)
        assert 'standardized_rate_not_crude_ratio' in r['warnings']
        for scope in ('tuscany','versilia'):
            r=engine.query(query('benchmark_gap','elderlyHomeCare',dimension,towns=['046018'],benchmark=scope))
            assert r['status']=='computed',r
        rejected(engine,query('weighted_ratio','elderlyHomeCare',dimension),'verified_ratio_adapter_required')
    rejected(engine,query('compare','elderlyHomeCare'),'dimension_adapter_not_implemented')
    rejected(engine,query('series','elderlyHomeCare','sex:total',towns=['046018']),'historical_dimension_not_available')
    home=engine.query(query('benchmark_gap','elderlyHomeCare','sex:total',towns=['046018'],benchmark='versilia'))
    close(home['result']['value'],30.085-22.1027)
    report=build_readings(engine)
    assert report['status']=='ready_for_methodological_review' and len(report['readings'])==len(engine.catalog['towns'])*3
    assert report==build_readings(engine)
    assert len({r['id'] for r in report['readings']})==len(report['readings'])
    for reading in report['readings']:
        assert reading['proposal']['approved'] is False and reading['proposal']['expectedEffect'] is None
        assert reading['hypothesis']['verified'] is False
        assert reading['proposal']['additionalDataRequired'] and reading['proposal']['outcomeIndicatorsRequired']
        assert all(o['observation']['geography']==reading['geography'] for o in reading['observations'])
        assert all(o['observation']['provenance'] for o in reading['observations'])
        if reading['pilot']!='tourism_services':
            assert reading['association']['status']=='not_computable'
            assert 'paired_period_mismatch' in reading['association']['reasons']
        else:assert reading['association']['status']=='not_requested'
    text=markdown(report);assert '2024/25' in text and '2026' in text and 'standardizzato' in text
    # No null is converted to zero; failure prevents a review-ready pilot.
    with tempfile.TemporaryDirectory(prefix='a6-territorial-') as temporary:
        root=Path(temporary);path=root/'catalog.json'
        for name in (AGE_SNAPSHOT,DEMOGRAPHY,CHILD,TOURISM,ARS):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        # Other unchanged adapters still read their versioned census evidence.
        from semantic_query_adapters import CENSUS_PATH,CENSUS_BENCHMARK
        for name in (CENSUS_PATH,CENSUS_BENCHMARK):
            (root/name).write_bytes((ROOT/name).read_bytes())
        data=engine.catalog;data['metrics']['earlyChildhoodPotentialCapacityRate']['rows'][0]['value']=None
        path.write_text(json.dumps(data));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('weighted_ratio','earlyChildhoodPotentialCapacityRate'),'partial_coverage_requires_opt_in')
        partial=altered.query(dict(query('weighted_ratio','earlyChildhoodPotentialCapacityRate'),allowPartial=True))
        assert partial['status']=='computed' and partial['result']['numerator']==1031-87
        assert partial['result']['denominator']==2217-297
        assert build_readings(altered)['status']=='not_ready'
        data=engine.catalog;path.write_text(json.dumps(data))
        demo=json.loads((root/DEMOGRAPHY).read_text());demo['components']['tuscany']['ageDistribution']['bands']['85+']+=1
        (root/DEMOGRAPHY).write_text(json.dumps(demo));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('benchmark_gap','ageDistribution','age:85+',towns=['046018'],benchmark='tuscany'),'bands_not_exhaustive')
        (root/DEMOGRAPHY).write_bytes((ROOT/DEMOGRAPHY).read_bytes())
        child=json.loads((root/CHILD).read_text());child['municipalReconciliation']['046018']['children3to36Months']=0
        (root/CHILD).write_text(json.dumps(child));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('compare','earlyChildhoodPotentialCapacityRate'),'child_components_mismatch')
        (root/CHILD).write_bytes((ROOT/CHILD).read_bytes())
        data['metrics']['elderlyHomeCare']['rows'][0]['parts'][0]['measurement']='raw'
        path.write_text(json.dumps(data));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('compare','elderlyHomeCare','sex:total'),'ars_measurement_changed')
        data=engine.catalog;data['metrics']['tourismIntensity']['rows'][0]['value']+=1
        path.write_text(json.dumps(data));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('compare','tourismIntensity'),'source_ratio_reconciliation_failed')
        data=engine.catalog;data['metrics']['population']['rows'][0]['sexDimension']['groups'][0]['count']+=1
        path.write_text(json.dumps(data));altered=QueryEngine(path,repository_root=root,layer='effective')
        rejected(altered,query('compare','population','sex:men'),'population_sex_count_mismatch')
    print('A6 territorial adapters and 3 × 7 pilot readings PASS; incompatible associations refused')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
