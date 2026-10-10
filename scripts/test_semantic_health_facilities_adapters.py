"""Independent municipal records, native stock reconciliation and refusal guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_health_facilities_adapters as f

# Independently transcribed native municipal sites, POSAS and public rounded values.
COUNTS = {'046005':11,'046013':5,'046018':6,'046024':9,'046028':4,'046030':1,'046033':20}
POP = {'046005':31763,'046013':6550,'046018':21782,'046024':22678,'046028':12284,'046030':2783,'046033':60680}
RATES = {'046005':.35,'046013':.76,'046018':.28,'046024':.40,'046028':.33,'046030':.36,'046033':.33}
RSA = {'046005':5,'046013':0,'046018':0,'046024':2,'046028':2,'046030':0,'046033':4}


def query(key,op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric=key,**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective'); catalog=e.catalog
    for key, expected in ((f.PHARMACY,RATES),(f.RSA,RSA)):
        r=e.query(query(key)); assert r['status']=='computed',r
        for o in r['observations']:
            assert o['value']==expected[o['geography']] and o['period']=='2025'
            assert pointer(catalog,o['provenance'][0]['valuePointer'])==o['value']
            assert not o['notApplicable'] and not o['dataUnavailable']
            src=o['provenance'][1];snap,_=e.file(f.PATHS[key])
            records=pointer(snap,src['recordPointer'])
            code=o['geography']
            if key==f.PHARMACY:
                assert src['nativeCount']==COUNTS[code]==sum(x[2]==code for x in records)
                den=o['provenance'][2]; pop,_=e.file(f.POPULATION)
                assert den['nativeDenominator']==POP[code]==pointer(pop,den['recordPointer'])
                assert round(COUNTS[code]/POP[code]*1000,2)==o['value']
                assert den['denominatorDate']=='2026-01-01' and o['unit']=='per1000'
            else:
                unique={(x[0],x[2]) for x in records}
                assert src['nativeCount']==RSA[code]==sum(n.casefold()==f.TOWNS[code].casefold() for n,_ in unique)
                assert o['unit']=='count'
        ranked=e.query(query(key,'rank'));assert ranked['status']=='computed'
        assert [x['geography'] for x in ranked['result']['ranking']]==sorted(expected,key=lambda c:(-expected[c],c))
        for op in ('series','absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(key,op,towns=['046005']), 'health_facilities_single_snapshot_no_history')
        for op,reason in [('weighted_ratio','health_facilities_public_rounded_rate_no_reviewed_pooling'),('anomaly','health_facilities_peer_anomaly_not_reviewed')]:
            rejected(e,query(key,op),reason)
        for period in ('2024','2026'):
            rejected(e,query(key,periods=[period]),'health_facilities_period_not_frozen')
        for dim in ('normalized','numerator','denominator','age:65plus','sex:women'):
            rejected(e,query(key,dimension=dim),'dimension_adapter_not_implemented')
        for pair in ([dict(metric=key),dict(metric='population')],[dict(metric='population'),dict(metric=key)]):
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'health_facilities_pair_not_jointly_reviewed')
        mutations=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='percent'),lambda m:m['meta'].update(polarity='positive'),lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['rows'][0].update(value=999),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(benchmarkValue=999),lambda m:m['rows'][0].update(town='Unknown'),lambda m:m['rows'][0].update(slug='unknown'),lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0].update(notApplicable=True),lambda m:m['rows'][0].update(ratioComponents={'numerator':1}),lambda m:m['aggregate'].update(value=999),lambda m:m['aggregate'].update(label='Media Versilia'),lambda m:m['method'].update(formula='Other'),lambda m:m['meta']['benchmark'].update(tuscany=999)]
        if key==f.RSA:mutations += [lambda m:m['rows'][0]['series']['values'].__setitem__(0,False),lambda m:m['meta']['benchmark'].update(italy=336)]
        else:mutations += [lambda m:m['rows'][0].update(series={'years':[2024],'values':[.4]})]
        for mutation in mutations:
            g=QueryEngine(path,layer='effective');mutation(g._catalog['metrics'][key]);assert g.query(query(key))['status']=='not_computable'
    for scope,n,d in [('tuscany',1270,3659222),('italy',20730,58942828)]:
        for code in RATES:
            r=e.query(dict(query(f.PHARMACY,'benchmark_gap',towns=[code]),benchmark=scope));assert r['status']=='computed',r
            assert math.isclose(r['observations'][1]['value'],n/d*1000,abs_tol=1e-12)
            assert math.isclose(r['result']['value'],RATES[code]-n/d*1000,abs_tol=1e-12)
            assert 'health_pharmacies_public_two_decimals_benchmark_unrounded' in r['warnings']
    rejected(e,dict(query(f.RSA,'benchmark_gap',towns=['046005']),benchmark='tuscany'),'health_facilities_rsa_absolute_regional_stock_not_municipal_rate')
    rejected(e,dict(query(f.PHARMACY,'benchmark_gap',towns=['046005']),benchmark='versilia'),'health_facilities_benchmark_scope_not_reviewed')
    for path in f.HASHES:
        key=f.RSA if path in (f.RSA_FILE,f.RSA_LOCAL) else f.PHARMACY
        for field in ('sha256','path'):
            g=QueryEngine(e.path,layer='effective');data,ref=g.file(path);ref[field]='changed'
            assert g.query(query(key))['status']=='not_computable'
        g=QueryEngine(e.path,layer='effective');data,_=g.file(path);data['schemaVersion']=999
        assert g.query(query(key))['status']=='not_computable'
    for mutation in (lambda m:m['meta'].update(year='2025'),lambda m:m['rows'][0].update(value=1),lambda m:m['rows'][0].update(town='Stazzema')):
        g=QueryEngine(e.path,layer='effective')
        mutation(g._catalog['metrics']['population']);assert g.query(query(f.PHARMACY))['status']=='not_computable'
    print('Health facilities adapters PASS: 14 fixed municipal cells, 7 native pharmacy counts/denominators, 14 gaps, zero/tie/provenance and adversarial guards')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
