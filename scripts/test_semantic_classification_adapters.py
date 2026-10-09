"""Independent fixed municipal categories, aliases, encoding and refusal gates."""
import copy
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_classification_adapters as x

FIXED = {'046005':(2,True,True), '046013':(2,True,True), '046018':(2,False,True),
    '046024':(2,True,True), '046028':(2,False,True), '046030':(3,False,False), '046033':(2,True,True)}

def regressions(path):
    e = QueryEngine(path, layer='effective')
    checked = 0
    for dim in x.dimensions(x.KEYS[0]):
        f = x.field(dim)
        result = e.query(request('compare', x.KEYS[0], dimension=dim))
        assert result['status'] == 'computed' and result['interpretationLevel']=='category_lookup', result
        assert result['result']['observations'] == result['observations']
        for o in result['observations']:
            expected = FIXED[o['geography']][x.FIELDS.index(f)]
            assert o['value'] == (expected if f == 'degurba' else int(expected))
            assert type(o['value']) is int and type(o['sourceValue']) is type(expected) and o['sourceValue'] == expected
            assert o['unit'] == 'category_code' and o['period'] == '2021'
            assert o['categoryLabel'] == (('Zone scarsamente popolate' if expected == 3 else 'Zone a densità intermedia di popolazione') if f == 'degurba' else ('sì' if expected else 'no'))
            for ev in o['provenance']:
                node = e._catalog if ev['kind'] == 'catalog_snapshot' else e.file(ev['path'])[0]
                for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:
                    node = node[int(p)] if isinstance(node,list) else node[p]
                assert node == expected and len(ev['sha256']) == 64
            checked += 1
        for op in ['rank','series','absolute_change','relative_change','percentage_points','trend','weighted_ratio','benchmark_gap','anomaly']:
            rejected(e, request(op,x.KEYS[0],dimension=dim), 'classification_category_arithmetic_or_association_not_supported')
        rejected(e, request('compare',x.KEYS[0],dimension=dim,periods=['2026']), 'classification_period_not_frozen')
        rejected(e, request('compare',x.KEYS[0],dimension=dim,towns=['046018']), 'insufficient_observations')
    for selectors in [[dict(metric=x.KEYS[0]),dict(metric='population')],[dict(metric='population'),dict(metric=x.KEYS[0])]]:
        rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='spearman',purpose='descriptive'),'classification_category_arithmetic_or_association_not_supported')
    for mode in ['value','label','boolean','null','identity','unit','year','series','flag','native','hash']:
        g = QueryEngine(path,layer='effective');m=g._catalog['metrics'][x.KEYS[0]];r=m['rows'][0];reason='classification_public_native_mismatch'
        if mode=='value':r['value']=None
        elif mode=='label':r['classification']['degurbaLabel']='new label'
        elif mode=='boolean':r['classification']['littoral']=1
        elif mode=='null':r['classification']['coastalZone']=None
        elif mode=='identity':r['town']='wrong';reason='classification_identity_or_availability_changed'
        elif mode=='unit':m['meta']['unit']='percent';reason='classification_definition_or_reference_changed'
        elif mode=='year':m['meta']['year']='2026';reason='classification_definition_or_reference_changed'
        elif mode=='series':r['series']={'years':[2021],'values':[2]}
        elif mode=='flag':r['dataUnavailable']=True;reason='classification_identity_or_availability_changed'
        else:
            s,ref=g.file(x.NATIVE);s=copy.deepcopy(s);ref=copy.deepcopy(ref)
            if mode=='native':s['classifications'][r['town']]['degurba']=3
            else:ref['sha256']='0'*64
            g.files[x.NATIVE]=(s,ref);reason='classification_frozen_input_changed'
        rejected(g,request('compare',x.KEYS[0]),reason)
    g=QueryEngine(path,layer='effective');assert g.query(request('compare',x.KEYS[0]))['status']=='computed'
    g.file(x.NATIVE)[0]['scope']='mutated';rejected(g,request('compare',x.KEYS[0]),'classification_frozen_input_changed')
    assert checked==28
    print('A6 classifications PASS: 28 fixed category observations including alias, boolean/label provenance and refusal/adversarial boundaries')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
