"""Independent fixed election anchors, decoded replay and hostile query boundaries."""
import base64
import copy
import gzip
import json
import math
from pathlib import Path
import tempfile
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_turnout_adapters as a

CODES=tuple(sorted(a.TOWNS))
LATEST = {
 'politiche_camera':('politiche_camera-20220925',[(17525,26266),(4139,5824),(11598,17972),(12251,19136),(6360,10376),(1353,2436),(31615,48994)]),
 'europee':('europee-20240609',[(12776,27750),(2958,5885),(8626,19291),(9045,20352),(4498,10951),(1402,3290),(24395,50772)]),
 'regionali_toscana':('regionali_toscana-20251012',[(11840,28461),(2514,5903),(8152,19682),(8677,20916),(4629,11155),(1031,3460),(21775,52093)]),
 'referendum':('referendum-20260322-q1',[(16425,26237),(3556,5426),(11301,18033),(12145,18912),(6212,10274),(1347,2378),(30922,48892)])}
SEX = {
 'politiche_camera':[(8578,12580,8947,13686),(1985,2735,2154,3089),(5757,8764,5841,9208),(5914,9017,6337,10119),(3096,4926,3264,5450),(717,1206,636,1230),(15189,23194,16426,25800)],
 'europee':[(6238,13339,6538,14411),(1390,2739,1568,3146),(4273,9486,4353,9805),(4413,9593,4632,10759),(2203,5219,2295,5732),(718,1637,684,1653),(11609,24141,12786,26631)]}
MASS_HISTORY = {
 'politiche_camera':[(8862,9469),(9229,9766),(9814,10102),(10187,10601),(10776,11167),(11343,11748),(12172,12660),(12441,13133),(12956,13765),(13711,14631),(14275,15680),(14801,16314),(14691,16727),(14953,17387),(15214,17925),(14507,18171),(14044,18295),(13621,18118),(11598,17972)],
 'europee':[(12125,13122),(12771,14001),(12767,14864),(13338,16271),(13413,17009),(14249,17687),(14193,18725),(12826,18995),(12624,19053),(8626,19291)],
 'regionali_toscana':[(11112,11543),(12039,12577),(12438,13253),(13340,14231),(13743,15156),(14229,16502),(12412,17205),(11955,17938),(10217,18925),(8155,19259),(10958,19394),(8152,19682)]}


def query(dim='total',op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric='voterTurnout',dimension=dim,**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective')
    for family,(period,cells) in LATEST.items():
        for native in [False,True]:
            dim='family:'+family+('|nativeRatio' if native else '')
            r=e.query(query(dim));assert r['status']=='computed',r
            for i,o in enumerate(r['observations']):
                n,d=cells[i];expected=n/d*100 if native else round(n/d*100,4)
                assert o['geography']==CODES[i] and o['period']==period and o['value']==expected
                assert not o['nativeRecordReplayAvailable'] and o['normalizedRecordReplayAvailable']
                snap,ref=a.frozen(e);record=pointer(snap,o['evidence'][1]['recordPointer'])
                assert record['voters']==n and record['electors']==d
                assert o['evidence'][1]['valuePointer'].endswith('/turnout')
            ranking=e.query(query(dim,'rank'));assert ranking['status']=='computed'
            expected_order=sorted(CODES,key=lambda c:(-cells[CODES.index(c)][0]/cells[CODES.index(c)][1],c))
            assert [o['geography'] for o in ranking['result']['ranking']]==expected_order
            if native:
                pooled=e.query(query(dim,'weighted_ratio'));assert pooled['status']=='computed',pooled
                assert math.isclose(pooled['result']['value'],sum(n for n,d in cells)/sum(d for n,d in cells)*100,rel_tol=0,abs_tol=1e-12)
            else:rejected(e,query(dim,'weighted_ratio'),'turnout_native_ratio_dimension_required')
        if family in MASS_HISTORY:
            for native in [False,True]:
                dim='family:'+family+('|nativeRatio' if native else '')
                r=e.query(query(dim,'series',towns=['046018']));assert r['status']=='computed',r
                assert len(r['observations'])==len(MASS_HISTORY[family])
                for o,(n,d) in zip(r['observations'],MASS_HISTORY[family]):
                    assert o['value']==(n/d*100 if native else round(n/d*100,4))
        else:rejected(e,query('family:referendum','series',towns=['046018']),'turnout_referendum_questions_not_a_single_series')
    for dim in ['total','nativeRatio']:
        r=e.query(query(dim));assert r['status']=='computed'
        for o,(n,d) in zip(r['observations'],LATEST['referendum'][1]):assert o['value']==n/d*100
        assert e.query(query(dim,periods=['2026']))['observations'][0]['period']==a.CURRENT
        rejected(e,query(dim,periods=['referendum-20250608-q1']),'turnout_consultation_not_available_in_selected_family')
    partial=query('family:europee|sex:men','series',towns=['046018'])
    rejected(e,partial,'partial_coverage_requires_opt_in')
    r=e.query(dict(partial,allowPartial=True));assert r['status']=='computed'
    assert r['coverage']==dict(requested=10,usable=5,excludedIndices=[0,1,2,3,4])
    assert all(o['value'] is None for o in r['observations'][:5])
    assert r['observations'][-1]['value']==45.0453
    for family,cells in SEX.items():
        for sex,offset in [('men',0),('women',2)]:
            for native in [False,True]:
                dim='family:'+family+'|sex:'+sex+('|nativeRatio' if native else '')
                r=e.query(query(dim));assert r['status']=='computed',r
                for o,row in zip(r['observations'],cells):
                    n,d=row[offset:offset+2];assert o['value']==(n/d*100 if native else round(n/d*100,4))
                if native:
                    r=e.query(query(dim,'weighted_ratio'));assert r['status']=='computed',r
                    assert math.isclose(r['result']['value'],sum(row[offset] for row in cells)/sum(row[offset+1] for row in cells)*100,rel_tol=0,abs_tol=1e-12)
    for sex in ['men','women']:
        q=query('family:regionali_toscana|sex:'+sex,periods=['regionali_toscana-19900506'])
        r=e.query(q);assert r['status']=='not_computable' and len(r['observations'])==7
        assert all(o['value'] is None and o['dataUnavailable'] and o['missingReason']=='official_sex_components_incomplete' for o in r['observations'])
    for dim in a.dimensions('voterTurnout'):
        for op in ['absolute_change','relative_change','percentage_points','trend']:
            rejected(e,query(dim,op),'turnout_electoral_universe_continuity_not_attested')
        for op,reason in [('benchmark_gap','turnout_geographic_benchmark_not_reviewed'),('anomaly','turnout_peer_anomaly_not_reviewed')]:
            rejected(e,dict(query(dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
    for p in ['2025','2026-03-22','20260322','referendum-20250608','comunali-20260607']:
        rejected(e,query(periods=[p]),'turnout_explicit_consultation_id_required')
    rejected(e,query('family:europee',periods=['politiche_camera-20220925']),'turnout_consultation_not_available_in_selected_family')
    rejected(e,query('family:referendum',periods=['referendum-19871108-q1']),'turnout_consultation_not_available_in_selected_family')
    rejected(e,query('family:referendum',periods=['referendum-20250608-q1','referendum-20250608-q2']),'cross_section_requires_one_period')
    for dim in ['municipalLatest','province:lucca','politiche_senato','sex:men']:
        rejected(e,query(dim),'dimension_adapter_not_implemented')
    for selectors in [[dict(metric='voterTurnout'),dict(metric='population')],[dict(metric='population'),dict(metric='voterTurnout')]]:
        rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'),'turnout_pair_not_jointly_reviewed')
    # Independent decoder and all admitted supra-municipal rows, including nulls.
    body=b''.join((ROOT/f'data/affluenza/archive-v2-{i:02d}.b64').read_bytes().strip() for i in range(4))
    decoded=json.loads(gzip.decompress(base64.b64decode(body)));count=0
    for family,block in decoded['families'].items():
        for event in block['events']:
            complete=all(r['maleElectors'] and r['femaleElectors'] and r['maleTurnout'] is not None and r['femaleTurnout'] is not None for r in event['municipalities'])
            for k,row in enumerate(event['municipalities']):
                index=next(i for i,r in enumerate(e._catalog['metrics']['voterTurnout']['rows']) if r['code']==row['code'])
                for sex,prefix in [('', ''),('|sex:men','male'),('|sex:women','female')]:
                    for native in [False,True]:
                        dim='family:'+family+sex+('|nativeRatio' if native else '')
                        o,_=a.observation(e,'voterTurnout',index,dim,event['id'],True)
                        expected=None if prefix and not complete else row[prefix+'Voters' if prefix else 'voters']/row[prefix+'Electors' if prefix else 'electors']*100 if native else row[prefix+'Turnout' if prefix else 'turnout']
                        assert o['value']==expected;count+=1
    assert count==2982
    for mutation in [lambda m:m['meta'].update(year='2025'),lambda m:m['rows'][0].update(value=99),
                     lambda m:m['aggregate'].update(value=99),lambda m:m['dataStorage'].update(prefix='archive-'),
                     lambda m:m.update(sourceUrl='https://example.com')]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g._catalog['metrics']['voterTurnout']);rejected(g,query(),'turnout_public_definition_or_values_changed')
    for mutation in [lambda s:s['families']['referendum']['events'][-1]['municipalities'][0].update(voters=1),
                     lambda s:s['families']['referendum']['events'][-1].update(questionId='2'),
                     lambda s:s['families']['regionali_toscana']['events'][4]['municipalities'][0].update(femaleElectors=1),
                     lambda s:s['families']['europee']['events'].append(copy.deepcopy(s['families']['europee']['events'][0])),
                     lambda s:s['gate'].update(generated='2027-01-01')]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g._turnout_payload[0]);rejected(g,query(),'turnout_frozen_payload_changed')
    g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
    g._turnout_payload[1]['sha256']='0'*64;rejected(g,query(),'turnout_frozen_payload_changed')
    with tempfile.TemporaryDirectory() as directory:
        g=QueryEngine(path,layer='effective');g.root=Path(directory)
        for i in range(4):
            p=g.root/f'data/affluenza/archive-v2-{i:02d}.b64';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('invalid')
        rejected(g,query(),'turnout_frozen_fragment_changed')
    print('Turnout PASS: fixed 28 current pairs, 28 sex pairs, 41 historical pairs; independent 2982-cell normalized replay, pooled results, exact questions, missing 1990 sex and hostile cached inputs; original DAIT files not replayed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
