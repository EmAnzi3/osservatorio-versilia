#!/usr/bin/env python3
"""Native periods, independently frozen arithmetic and fail-closed carriers."""
import copy
import json
import math
import tempfile
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT
import semantic_query_demography_school_adapters as d
from test_semantic_query_engine import rejected, request


def regressions(path):
    e=QueryEngine(path,layer='effective');catalog=e.catalog;observations=0
    for key in d.KEYS:
        for dimension in d.dimensions(key):
            for code in sorted(e.codes):
                selector=dict(metric=key,dimension=dimension,towns=[code])
                rows,_=e.select(selector,'compare');observations+=len(rows)
                assert rows[0]['geography']==code and rows[0]['dimension']==dimension
                assert all(len(p['sha256'])==64 for p in rows[0]['provenance'])
                current_only=key in (d.SITES,*d.STUDENTS,*d.BUILDINGS) or '|sex:' in dimension or dimension.startswith('sex:')
                if not current_only:
                    rows,_=e.select(selector,'series');observations+=len(rows)
                    assert len({r['period'] for r in rows})==len(rows)
                else:
                    rejected(e,request('series',key,dimension=dimension,towns=[code]),'history_not_frozen')
            for scope in d.benchmark_scopes(key,dimension):
                result=e.query(dict(request('benchmark_gap',key,dimension=dimension,towns=['046018']),benchmark=scope))
                assert result['status']=='computed',(key,dimension,scope,result['reasons'])
    # References transcribed from frozen source records, not adapter output.
    checks=[(d.DEPENDENCY,'total',(2213+5691)/13878*100),
            (d.DEPENDENCY,'part:elderly',5691/13878*100),
            (d.DEPENDENCY,'part:structural|sex:men',(1136+2585)/7015*100),
            (d.DEPENDENCY,'part:elderly|sex:women',3106/6863*100),
            (d.NATURAL,'total',-160/21794*1000),
            (d.NATURAL,'part:births',96/21794*1000),
            (d.MOBILITY[0],'total',63/21835.5*1000),
            (d.MOBILITY[1],'total',37/21835.5*1000),
            (d.MOBILITY[2],'total',100/21835.5*1000),
            (d.FOREIGN,'total',1030/21806*100),(d.FOREIGN,'count',1030),
            (d.FOREIGN,'sex:men',475),(d.FOREIGN,'sex:women',555),
            (d.CHANGE,'total',86/21696*100),
            ('schoolStudents','total',1282),('studentsPerClass','total',1282/72),
            ('primaryFullTimeShare','total',413/747*100),
            (d.BUILDINGS[0],'part:cpi',1/6*100),
            (d.BUILDINGS[1],'total',100),(d.BUILDINGS[1],'part:undefined',20),
            (d.BUILDINGS[2],'total',100),(d.BUILDINGS[2],'part:gym',7/15*100),
            (d.BUILDINGS[3],'total',75),(d.BUILDINGS[3],'part:undefined',7/15*100)]
    for key,dim,expected in checks:
        rows,_=e.select(dict(metric=key,dimension=dim,towns=['046018']),'compare')
        assert math.isclose(rows[0]['value'],expected,rel_tol=0,abs_tol=1e-8),(key,dim,rows[0])
    for dim in ('part:scia','part:renewal'):
        rows,notes=e.select(dict(metric=d.BUILDINGS[0],dimension=dim,towns=['046018']),'compare')
        assert rows[0]['value'] is None and rows[0]['denominator']==0 and rows[0]['undefinedResponses']==15
        assert 'undefined_responses_not_no_or_zero' in notes
    # Unequal class sizes: pooled pupils/classes, never the unweighted town mean.
    r=e.query(request('weighted_ratio','studentsPerClass'))
    raw=json.loads((ROOT/d.LIA).read_text())['raw']['mim2024_25']
    assert r['status']=='computed' and r['result']['numerator']==sum(x['students'] for x in raw)
    assert r['result']['denominator']==sum(x['classes'] for x in raw)
    rejected(e,request('compare','studentsPerClass',periods=['2024']),'native_school_year_required')
    rejected(e,request('compare',d.CHANGE,periods=['2026']),'cumulative_2019_interval_required')
    rejected(e,request('trend',d.CHANGE,towns=['046018']),'cumulative_trend_not_annual_growth')
    rejected(e,dict(request('benchmark_gap','schoolStudents',towns=['046018']),benchmark='tuscany'),'absolute_volume_not_comparable')
    rejected(e,request('weighted_ratio',d.MOBILITY[1],periods=['2023']),'ratio_components_required')
    corr=dict(operation='correlation',selectors=[dict(metric=d.FOREIGN),dict(metric=d.MOBILITY[1])],axis='municipalities',method='spearman',purpose='Different citizenship stocks and residence events')
    rejected(e,corr,'paired_period_mismatch')
    corr['selectors']=[dict(metric=d.SITES),dict(metric='schoolStudents')]
    rejected(e,corr,'observation_dates_not_attested_for_pairing')
    with tempfile.TemporaryDirectory(prefix='a6-demography-school-') as temporary:
        root=Path(temporary)
        for relative in d.SNAPSHOTS:
            dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/relative).read_bytes())
        path=root/'catalog.json'
        def changed(data):
            path.write_text(json.dumps(data));return QueryEngine(path,repository_root=root,layer='effective')
        for key in d.KEYS:
            data=copy.deepcopy(catalog);data['metrics'][key]['rows'][0]['value']+=1
            rejected(changed(data),request('compare',key),'catalog_source_mismatch')
        data=copy.deepcopy(catalog);data['metrics'][d.DEPENDENCY]['rows'][0]['town']='Viareggio'
        try:changed(data)
        except AssertionError as err:assert 'Town/code incoerenti' in str(err)
        else:raise AssertionError('incoherent geography admitted')
        data=copy.deepcopy(catalog);data['metrics'][d.MOBILITY[0]]['rows'][0]['parts'][0]['label']='Cittadini stranieri'
        rejected(changed(data),request('compare',d.MOBILITY[0],dimension='part:arrivals'),'part_definition_changed')
        data=copy.deepcopy(catalog);data['metrics']['studentsPerClass']['rows'][0]['a3SchoolComponents'].pop('denominator')
        rejected(changed(data),request('weighted_ratio','studentsPerClass'),'nonfinite_component')
        for key,dim,component in [(d.DEPENDENCY,'part:structural','parts'),(d.BUILDINGS[1],'total','parts'),(d.SITES,'normalized','normalized')]:
            data=copy.deepcopy(catalog);row=data['metrics'][key]['rows'][0]
            selected=row['parts'][0] if component=='parts' else row[component]
            selected['unit']='people'
            rejected(changed(data),request('compare',key,dimension=dim),'component_unit_changed')
        data=copy.deepcopy(catalog);data['metrics'][d.BUILDINGS[1]]['rows'][0]['parts'][0]['defined']=15
        rejected(changed(data),request('compare',d.BUILDINGS[1]),'catalog_source_mismatch')
        data=copy.deepcopy(catalog);data['metrics'][d.BUILDINGS[0]]['rows'][0]['parts'][2]['value']=0
        rejected(changed(data),request('compare',d.BUILDINGS[0],dimension='part:scia'),'catalog_source_mismatch')
        data=copy.deepcopy(catalog);data['metrics'][d.DEPENDENCY]['rows'][0]['value']=None
        rejected(changed(data),request('compare',d.DEPENDENCY),'partial_coverage_requires_opt_in')
        result=changed(data).query(dict(request('compare',d.DEPENDENCY),allowPartial=True))
        assert result['status']=='computed' and result['coverage']['usable']==6 and result['excluded'][0]['observation']['value'] is None
        frozen=root/d.BUILDING;snapshot=json.loads(frozen.read_text());snapshot['towns']['Massarosa']['accessibilita']['UNKNOWN_NEW']=1
        frozen.write_text(json.dumps(snapshot))
        rejected(changed(catalog),request('compare',d.BUILDINGS[1]),'response_category_not_reviewed')
    print(f'A6 demography/school: {observations} native observations, independent arithmetic, nulls, dates and adversarial cases PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
