"""Independent fixed series, fiscal endpoints, aggregate arithmetic and hostile edits."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_real_income_adapters as adapter

# Public four-decimal cumulative changes; not generated from adapter output.
CELLS = {
 '046018': ([0,-.9079,.1092,1.1005,.4212,3.4453,.9907,-.6398,3.4042], [0,.2812,2.5262,4.1628,3.2559,8.3863,14.3855,18.9535,25.0328]),
 '046033': ([0,3.2931,3.2713,3.1336,-.6365,2.9103,2.4613,.1191,3.3064], [0,4.5326,5.7647,6.2574,2.1684,7.8259,16.0511,19.862,24.9146]),
 '046005': ([0,-1.5067,.2877,.8486,.5991,5.8521,2.5329,2.0587,6.0365], [0,-.3248,2.709,3.9032,3.4388,10.9081,16.1323,22.1841,28.2158]),
 '046024': ([0,.6876,1.1797,1.4905,-.3505,5.1655,4.1144,2.8786,6.4776], [0,1.8959,3.6226,4.5646,2.4624,10.1888,17.9235,23.1657,28.7491]),
 '046028': ([0,-1.8507,-1.421,.5152,-.8872,2.5831,-1.7544,-2.4428,2.4001], [0,-.6729,.9591,3.5597,1.9105,7.483,11.2763,16.7949,23.8187]),
 '046013': ([0,2.8268,7.9619,7.1666,4.6568,15.2618,24.3036,15.5952,23.8343], [0,4.0607,10.5685,10.4126,7.6111,20.7673,40.7905,38.3899,49.7362]),
 '046030': ([0,-.2311,-1.113,.5324,-3.9583,.1196,-2.6198,-2.1476,3.8214], [0,.9662,1.2746,3.5774,-1.2472,4.9019,10.2961,17.1483,25.5374]),
}
ENDPOINTS = {
 '046018': [(268279801,15008),(348334163,15585)],
 '046033': [(852425856,41693),(1124081133,44014)],
 '046005': [(402128082,21714),(546269635,23006)],
 '046024': [(317696228,16206),(418823989,16594)],
 '046028': [(155811178,8796),(196783620,8972)],
 '046013': [(136521781,5079),(189490376,4708)],
 '046030': [(32308731,2060),(40598912,2062)],
}
TOTALS = {'tuscany': [(53904829164,2618841,276),(67730328839,2691349,273)],
          'italy': [(797504978906,39457256,7979),(1013394277109,40709947,7897)]}
PRICE_INDEX = [100,101.2,102.4144,103.0289,102.8228,104.7765,113.2634,119.7194,120.9166]


def query(op='compare', **sel): return dict(operation=op,selectors=[dict(metric='incomeVsInflation',**sel)])


def regressions(path):
    e=QueryEngine(path,layer='effective')
    for d,dim in enumerate(('total','nominal')):
        for j,y in enumerate(adapter.YEARS):
            r=e.query(query(dimension=dim,periods=[str(y)]));assert r['status']=='computed',r
            for o in r['observations']:
                code=o['geography'];assert o['value']==CELLS[code][d][j]
                assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['value']
                assert o['period']==str(y) and o['unit']=='percent'
                assert 'cumulative' in o['definition'] and 'national' in o['periodBasis']
                price=o['provenance'][1];assert price['path']==adapter.NIC and price['territory']=='italy'
                assert ('context only' in price['usage'])==(dim=='nominal')
                endpoint=[x for x in o['provenance'] if x['kind']=='income_endpoint_snapshot']
                assert bool(endpoint)==(y in (2016,2024))
                if endpoint:
                    a,f=ENDPOINTS[code][y==2024];assert endpoint[0]['components']==dict(amountEuro=a,frequency=f,averageEuro=round(a/f,2))
                    assert endpoint[0]['sourceDocument']['actualTaxYear']==y
                    assert 'not replayed' in endpoint[0]['replayScope']
            r=e.query(query('rank',dimension=dim,periods=[str(y)]));assert r['status']=='computed',r
            assert [x['geography'] for x in r['result']['ranking']]==sorted(CELLS,key=lambda c:(-CELLS[c][d][j],c))
            if y==2016:assert all(x['rank']==1 for x in r['result']['ranking'])
        for code,values in CELLS.items():
            r=e.query(query('series',dimension=dim,towns=[code]));assert r['status']=='computed',r
            assert [o['value'] for o in r['observations']]==values[d]
            assert [o['period'] for o in r['observations']]==list(map(str,adapter.YEARS))
        for op in ('absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(op,dimension=dim,towns=['046018'],periods=['2016','2024']),'real_income_cumulative_temporal_analysis_not_reviewed')
        rejected(e,query('weighted_ratio',dimension=dim),'real_income_growth_not_additive_no_pooling')
        rejected(e,query('anomaly',dimension=dim),'real_income_peer_anomaly_not_reviewed')
        rejected(e,query(dimension=dim,periods=['2025']),'real_income_period_not_frozen')
        for pair in ([dict(metric='incomeVsInflation',dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric='incomeVsInflation',dimension=dim)]):
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'real_income_pair_not_jointly_reviewed')
    for scope,ends in TOTALS.items():
        (a0,f0,n0),(a1,f1,n1)=ends; benchmark=((a1/f1)/(a0/f0)/1.209166-1)*100
        for code in CELLS:
            r=e.query(dict(query('benchmark_gap',towns=[code]),benchmark=scope));assert r['status']=='computed',r
            assert math.isclose(r['result']['value'],CELLS[code][0][-1]-benchmark,abs_tol=1e-9)
            obs=r['observations'][1];assert math.isclose(obs['value'],benchmark,abs_tol=1e-10)
            assert obs['provenance'][0]['components']==dict(zip(('2016','2024'),[dict(amountEuro=a,frequency=f,records=n) for a,f,n in ends]))
    rejected(e,dict(query('benchmark_gap',dimension='nominal',towns=['046018']),benchmark='tuscany'),'real_income_nominal_benchmark_not_reviewed')
    rejected(e,dict(query('benchmark_gap',towns=['046018'],periods=['2016']),benchmark='tuscany'),'real_income_benchmark_only_2024')
    for code,((a0,f0),(a1,f1)) in ENDPOINTS.items():
        expected=((round(a1/f1,2)/round(a0/f0,2))/1.209166-1)*100
        assert math.isclose(expected,CELLS[code][0][-1],abs_tol=.000051)
    # All 15,876 normalized endpoint records, including the unlocated national row.
    panel,_=e.file(adapter.PANEL)
    for j,year in enumerate(('2016','2024')):
        records=panel['records'][year];assert len(records)==TOTALS['italy'][j][2]
        assert len({r[0] for r in records})==len(records) and sum(r[0]=='0' for r in records)==1
        for scope in TOTALS:
            selected=[r for r in records if scope=='italy' or r[1]=='09']
            assert (sum(r[2] for r in selected),sum(r[3] for r in selected),len(selected))==TOTALS[scope][j]
    mutations=[lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='number'),lambda m:m['meta'].update(polarity='positive'),lambda m:m['method'].update(formula='different'),lambda m:m['meta']['benchmark'].update(tuscany=0),lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0]['nominalSeries']['values'].__setitem__(1,0),lambda m:m['rows'][0]['realSeries']['values'].__setitem__(2,0),lambda m:m['rows'][0]['series']['years'].__setitem__(0,2015),lambda m:m['inflationSeries']['values'].__setitem__(8,20),lambda m:m['aggregate'].update(value=0)]
    for mutate in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed';mutate(g._catalog['metrics']['incomeVsInflation']);assert g.query(query())['status']=='not_computable'
    for file in (adapter.NIC,adapter.PANEL):
        for field in ('path','sha256'):
            g=QueryEngine(path,layer='effective');g.query(query());_,ref=g.file(file);ref[field]='changed';assert g.query(query())['status']=='not_computable'
    g=QueryEngine(path,layer='effective');g.query(query());snap,_=g.file(adapter.PANEL);snap['records']['2024'][0][2]+=1;assert g.query(query())['status']=='not_computable'
    g=QueryEngine(path,layer='effective');g.query(query());snap,_=g.file(adapter.NIC);snap['comparisonIndex'][8]=100;assert g.query(query())['status']=='not_computable'
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown';assert g.query(query())['status']=='not_computable'
    print('Real income PASS: 126 fixed cumulative cells, 28 fixed fiscal components, 14 gaps, four aggregate totals, national NIC, 15876 normalized endpoint rows, ties/zero and hostile cached edits')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
