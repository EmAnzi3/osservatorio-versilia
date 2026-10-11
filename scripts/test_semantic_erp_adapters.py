"""Fixed accounting transcriptions, independent pooling and hostile edits."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_erp_adapters as erp

# Reviewed balances: issued/arrears euro pairs and public two-decimal rates.
CELLS = {
 '046005': ([(3582792.37,247063.23),(3854507.54,267712.42),(4132419.89,296554.22),(4402239.72,308511.54),(4721245.44,348067.19)], [6.90,6.95,7.18,7.01,7.37]),
 '046013': ([(2949206.99,172475.09),(3192864.58,194717.67),(3429308.68,225193.13),(3459825.27,246056.52),(3911358.57,272869.37)], [5.85,6.10,6.57,7.11,6.98]),
 '046018': ([(1656939.53,62971.17),(1755764.28,61148.91),(1860507.25,64950.49),(3164988.55,64990.36),(2078965.36,72398.09)], [3.80,3.48,3.49,2.05,3.48]),
 '046024': ([(5363800.69,412828.20),(5709770.82,417031.70),(6081755.16,447394.65),(6136480.16,463131.42),(6812489.99,478114.18)], [7.70,7.30,7.36,7.55,7.02]),
 '046028': ([(4117358.99,216108.44),(4409130.00,208201.92),(4709525.63,211210.84),(4720359.45,219836.25),(5346600.17,235874.51)], [5.25,4.72,4.48,4.66,4.41]),
 '046030': ([(825116.56,28883.37),(887449.32,28598.67),(947137.77,35187.95),(1259681.08,36132.36),(1036145.57,41967.92)], [3.50,3.22,3.72,2.87,4.05]),
 '046033': ([(20275358.16,2333819.91),(21713625.62,2401763.10),(23257105.59,2558637.44),(23303630.28,2712346.75),(26379101.73,2855639.38)], [11.51,11.06,11.00,11.64,10.83]),
}
TOTALS = [(38770573.29,3474149.41),(41523112.16,3579174.39),(44417759.97,3839128.72),(46447204.51,4051005.20),(50285906.83,4304930.64)]


def query(op='compare', **selectors):
    return dict(operation=op, selectors=[dict(metric='erpArrears', **selectors)])


def regressions(path):
    e = QueryEngine(path, layer='effective')
    for dim in erp.dimensions('erpArrears'):
        for j, year in enumerate(erp.YEARS):
            r = e.query(query(dimension=dim, periods=[str(year)])); assert r['status'] == 'computed', r
            for o in r['observations']:
                amounts, rates = CELLS[o['geography']]; issued, arrears = amounts[j]
                assert math.isclose(o['value'], rates[j] if dim == 'total' else arrears/issued*100, abs_tol=1e-9)
                assert o['period'] == str(year) and o['unit'] == 'percent'
                assert pointer(e.catalog, o['provenance'][0]['valuePointer']) == rates[j]
                assert o['provenance'][1]['nativeComponents'] == dict(numerator=arrears,denominator=issued,scale=100)
                assert o['provenance'][1]['sourceDocument']['year'] == year
                assert 'not replayed' in o['provenance'][1]['replayScope']
            r = e.query(query('rank',dimension=dim,periods=[str(year)])); assert r['status']=='computed',r
            expected={c: rates[j] if dim=='total' else amounts[j][1]/amounts[j][0]*100 for c,(amounts,rates) in CELLS.items()}
            assert [x['geography'] for x in r['result']['ranking']] == sorted(expected,key=lambda c:(-expected[c],c))
        for code,(amounts,rates) in CELLS.items():
            r=e.query(query('series',dimension=dim,towns=[code])); assert r['status']=='computed',r
            assert [o['period'] for o in r['observations']]==[str(y) for y in erp.YEARS]
        for op in ('absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(op,dimension=dim,towns=['046018'],periods=['2023','2024']),'erp_accounting_continuity_not_attested_for_temporal_analysis')
        rejected(e,query('anomaly',dimension=dim),'erp_peer_anomaly_not_reviewed')
        rejected(e,dict(query('benchmark_gap',dimension=dim,towns=['046018']),benchmark='tuscany'),'erp_geographic_benchmark_not_frozen')
        rejected(e,query(dimension=dim,periods=['2019']),'erp_period_not_frozen')
        for pair in ([dict(metric='erpArrears',dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric='erpArrears',dimension=dim)]):
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'erp_pair_not_jointly_reviewed')
    for j,year in enumerate(erp.YEARS):
        r=e.query(query('weighted_ratio',dimension='nativeRatio',periods=[str(year)])); assert r['status']=='computed',r
        issued,arrears=TOTALS[j]
        assert math.isclose(r['result']['value'],arrears/issued*100,abs_tol=1e-9)
        assert math.isclose(r['result']['numerator'],arrears,abs_tol=1e-8) and math.isclose(r['result']['denominator'],issued,abs_tol=1e-8)
        assert 'ERP Lucca' in r['policy']['disjointPopulationEvidence']['method']
    r=e.query(query('weighted_ratio',dimension='nativeRatio',towns=['046005','046018'],periods=['2023'])); assert r['status']=='computed',r
    assert math.isclose(r['result']['value'], (308511.54+64990.36)/(4402239.72+3164988.55)*100,abs_tol=1e-9)
    rejected(e,query('weighted_ratio'),'erp_native_ratio_dimension_required')
    mutations=[lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='number'),lambda m:m['meta'].update(polarity='negative'),lambda m:m['meta'].update(benchmark={'tuscany':1}),lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['method'].update(formula='different'),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(code='046018'),lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0]['accounting'].update(issued=0),lambda m:m['rows'][0]['accountingSeries']['arrears'].__setitem__(0,1),lambda m:m['rows'][0]['series']['values'].__setitem__(0,1),lambda m:m['aggregate'].update(value=999),lambda m:m['aggregate']['accounting'].update(arrears=1),lambda m:m['history'].update(years=[2024])]
    for mutate in mutations:
        g=QueryEngine(path,layer='effective');mutate(g._catalog['metrics']['erpArrears']);assert g.query(query())['status']=='not_computable'
    for field in ('path','sha256'):
        g=QueryEngine(path,layer='effective');_,ref=g.file(erp.PATH);ref[field]='changed';assert g.query(query())['status']=='not_computable'
    g=QueryEngine(path,layer='effective');snap,_=g.file(erp.PATH);snap['rows']['046018']['values'][3]['issued']=0;assert g.query(query())['status']=='not_computable'
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown';assert g.query(query())['status']=='not_computable'
    assert CELLS['046018'][0][3][0]==3164988.55 and CELLS['046018'][1][3]==2.05
    print('ERP adapters PASS: 35 fixed public cells, 70 fixed euro components, five pooled ratios, series and adversarial guards')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
