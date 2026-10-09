"""Fixed GAIA cells plus complete frozen replay and adversarial boundaries."""
import copy

from semantic_query_engine import QueryEngine, ROOT, NUMERICAL_SUPPORTED
from semantic_operations import assess, reported_measurement
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_water_quality_adapters as x

CASE_ROSSE = ['7.6','509.0','31','363.9','0.1','< 0,050','< 0,050','4.2','20.7','45.0','< 5,0','119','4.2','242','0.0560','0.49','26.6']
FIRST_NITRATES = {'046005':('07A01K01/0','5.0'), '046013':('20A01K05/0','24'),
    '046018':('28A02K01/0','4.2'), '046024':('35A01K01/0','2.9'),
    '046028':('42A05K11/0','4.6'), '046030':('44A15K01/0','1.6'), '046033':('49A01K03/0','5.4')}
COUNTS = {'046005':20,'046013':1,'046018':8,'046024':11,'046028':12,'046030':16,'046033':2}


def query(p=5, **selection):
    return dict(operation='lookup',selectors=[dict(metric=x.KEYS[0],dimension='parameter:'+str(p),**selection)])


def regressions(path):
    e = QueryEngine(path,layer='effective')
    for p,raw in enumerate(CASE_ROSSE):
        r = e.query(query(p,towns=['046018'],localities=['28A02K01/0']))
        assert r['status']=='computed' and r['interpretationLevel']=='source_lookup', r
        assert r['coverage']['requested']==r['coverage']['usable']==1
        assert r['observations'][0]['value']==raw and type(r['observations'][0]['value']) is str
        assert r['result']['observations']==r['observations']
    for code,(identity,raw) in FIRST_NITRATES.items():
        r = e.query(query(7,towns=[code],localities=[identity]))
        assert r['status']=='computed' and r['observations'][0]['value']==raw and r['observations'][0]['geography']==code, r
        r = e.query(query(7,towns=[code]));assert r['status']=='computed' and len(r['observations'])==COUNTS[code]
    replay = 0
    # This is public/native replay, not an independent reacquisition or fixed fixture.
    for p in range(17):
        r = e.query(query(p));assert r['status']=='computed' and len(r['observations'])==70, r
        assert r['coverage']==dict(requested=70,usable=70,excludedIndices=[])
        for o in r['observations']:
            assert o['period']==x.PERIOD and o['sourcePeriod']=='2° Semestre 2025'
            assert o['locality']==o['sampleCode']+'/'+o['sampleCode2']
            assert 'numerator' not in o and 'denominator' not in o and 'numericValue' not in o
            assert (o['reportedQualifier'],o['reportedNumber'])==reported_measurement(o['value'])
            for ev in o['provenance']:
                node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
                assert pointer(node,ev.get('valuePointer',ev.get('recordPointer')))==o['value']
                definition=pointer(node,ev['parameterPointer'])
                assert definition['name']==o['parameter'] and definition['unit']==o['unit'] and definition['reference']==o['referenceText']
            replay+=1
        for op in NUMERICAL_SUPPORTED:
            request=query(p);request['operation']=op
            if op=='correlation':request.update(selectors=request['selectors']+[dict(metric='population')],axis='municipalities',method='pearson',purpose='descriptive')
            rejected(e,request,'water_quality_arithmetic_or_association_not_supported')
    base=e.query(query())['observations'][0]
    assert assess('lookup',[base])['eligible']
    assert 'invalid_value:0' in assess('compare',[base,dict(base,geography='046033')])['reasons']
    for raw in ['< 0,050','> 9.5','0','0.0560']:
        o=copy.deepcopy(base);o.update(value=raw,sourceValue=raw);o['reportedQualifier'],o['reportedNumber']=reported_measurement(raw)
        assert assess('lookup',[o])['eligible']
    for raw in [0,False,None,'NaN','Infinity','n.d.','<','< 0,050 extra','<= 0.5','1e5']:
        o=copy.deepcopy(base);o.update(value=raw,sourceValue=raw)
        assert not assess('lookup',[o])['eligible']
    for f,v in [('reportedQualifier','exact'),('reportedNumber','0'),('valueKind','number'),('sourceValue',0),('locality','')]:
        o=copy.deepcopy(base);o[f]=v;assert not assess('lookup',[o])['eligible']
    assert 'duplicate_observation' in assess('lookup',[base,base])['reasons']
    rejected(e,dict(operation='lookup',selectors=[dict(metric=x.KEYS[0])]),'water_quality_explicit_parameter_required')
    rejected(e,query(periods=['2025']),'water_quality_period_not_frozen')
    rejected(e,query(periods=[x.PERIOD,x.PERIOD]),'water_quality_period_not_frozen')
    for localities in [[],['unknown'],['28A02K01/0']*2,['07A01K01/0']]:
        rejected(e,query(towns=['046018'],localities=localities),'water_quality_unknown_duplicate_or_out_of_scope_locality')
    for op in ['lookup','compare']:
        r=dict(operation=op,selectors=[dict(metric='population',localities=['28A02K01/0'])])
        rejected(e,r,'locality_selector_requires_water_quality_adapter')
    rejected(e,dict(operation='lookup',selectors=[dict(metric='population')]),'lookup_adapter_not_implemented')
    for mode in ['value','null','locality','name','url','qualifier','count','flag','row_identity','parameter','unit','year','native','hash']:
        g=QueryEngine(path,layer='effective');m=g._catalog['metrics'][x.KEYS[0]];row=m['rows'][0];l=row['localities'][0]
        reason='water_quality_public_native_mismatch'
        if mode=='value':l['values'][5]='0.025'
        elif mode=='null':l['values'][5]=None
        elif mode=='locality':l['sampleCode2']='1'
        elif mode=='name':l['name']='unknown'
        elif mode=='url':l['url']='https://example.org/'
        elif mode=='qualifier':l['values'][5]='0,050'
        elif mode=='count':row['value']+=1
        elif mode=='flag':row['notApplicable']=True;reason='water_quality_municipal_identity_changed'
        elif mode=='row_identity':row['town']='wrong';reason='water_quality_municipal_identity_changed'
        elif mode=='parameter':m['parameterDefinitions'][5]['unit']='µg/L';reason='water_quality_parameter_definition_changed'
        elif mode=='unit':m['meta']['unit']='percent';reason='water_quality_definition_or_reference_changed'
        elif mode=='year':m['meta']['year']='2026';reason='water_quality_definition_or_reference_changed'
        else:
            s,ref=g.file(x.NATIVE);s=copy.deepcopy(s);ref=copy.deepcopy(ref)
            if mode=='native':s['drinkingWaterQuality']['localities'][0]['values'][5]='0'
            else:ref['sha256']='0'*64
            g.files[x.NATIVE]=(s,ref);reason='water_quality_frozen_input_changed'
        rejected(g,query(),reason)
    g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
    g.file(x.NATIVE)[0]['release']='mutated';rejected(g,query(),'water_quality_frozen_input_changed')
    assert replay==1190
    print('A6 GAIA PASS: 24 fixed cells, 7 fixed locality counts, 1190 frozen-cell replay, qualifiers/provenance and refusal/adversarial boundaries')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
