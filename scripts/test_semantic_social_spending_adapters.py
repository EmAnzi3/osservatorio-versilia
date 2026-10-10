"""Independent transcribed records, rounding replay and social expenditure guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_social_spending_adapters as social

# Transcribed from the native Istat municipal rows, not from engine responses.
CURRENT = {'046005': 135.76, '046013': 278.55, '046018': 97.69, '046024': 132.29,
           '046028': 132.23, '046030': 84.70, '046033': 180.39}
CAM_HISTORY = [148.42, 152.68, 167.73, 142.79, 139.83, 131.00, 150.58, 151.93, 135.76]
SHARES = {
    '046005': [44.6439137863446,21.9935752113551,0,15.9528731721388,0,9.62606509663533,7.78357273352614],
    '046013': [50.5824662743041,24.9366523123594,.0363619363250549,17.1547304281878,2.36352586112857,1.91248201382793,3.0137811738672],
    '046018': [29.0223559206672,50.1473148174642,0,14.5271501607305,.929858820759076,2.76626314774778,2.60705713263118],
    '046024': [44.9802566666207,19.6792423187686,.678444960240535,21.5928370516009,8.12710802071686,1.60556323552709,3.33654774652544],
    '046028': [23.214352052316,33.1380254722376,0,20.5606742414692,0,10.8592875982858,12.2276606356915],
    '046030': [26.3352480930876,53.0295648186437,0,12.1190781312054,0,5.77989952629144,2.73620943077181],
    '046033': [45.6709656576869,11.5978285883979,0,9.80539474106536,5.26104411462913,9.75950460842587,17.9052622897949],
}


def query(key, op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective'); catalog = e.catalog
    native, _ = e.file(social.NATIVE)
    r = e.query(query(social.SPENDING)); assert r['status'] == 'computed', r
    for o in r['observations']: assert o['value'] == CURRENT[o['geography']]
    h = e.query(query(social.SPENDING, 'series', towns=['046005']))
    assert h['status'] == 'computed' and [o['value'] for o in h['observations']] == CAM_HISTORY
    histories = gaps = parts = 0
    for code, name in social.TOWNS.items():
        h = e.query(query(social.SPENDING, 'series', towns=[code])); assert h['status'] == 'computed', h
        assert [o['period'] for o in h['observations']] == list(map(str, range(2014,2023)))
        for o in h['observations']:
            pub, src = o['provenance']; original = pointer(native, src['recordPointer'])
            assert o['value'] == round(original, 2) == pointer(catalog, pub['valuePointer'])
            assert src['nativeValue'] == original and src['publishedDecimals'] == 2 and src['transformation']
            assert o['unit'] == 'eurPerResident' and not o['dataUnavailable']
            assert not o['nativeComponentsAvailable'] and 'denominator' not in o
            histories += 1
        for scope, fixed in [('tuscany',167),('italy',150)]:
            gap = e.query(dict(query(social.SPENDING,'benchmark_gap',towns=[code]), benchmark=scope))
            assert gap['status'] == 'computed', gap
            assert gap['observations'][1]['value'] == fixed
            assert math.isclose(gap['result']['value'], CURRENT[code]-fixed, abs_tol=1e-9)
            assert gap['result']['unit'] == 'eurPerResident'
            bench, _ = e.file(social.BENCHMARK)
            assert pointer(bench, gap['observations'][1]['provenance'][0]['recordPointer']) == fixed
            assert pointer(catalog, gap['observations'][1]['provenance'][1]['valuePointer']) == fixed
            gaps += 1
    for i, part in enumerate(social.PARTS):
        r = e.query(query(social.COMPOSITION, dimension='part:'+part)); assert r['status'] == 'computed', r
        for o in r['observations']:
            assert o['value'] == SHARES[o['geography']][i] and o['unit'] == 'percent'
            assert pointer(catalog,o['provenance'][0]['valuePointer']) == o['value']
            assert pointer(native,o['provenance'][1]['recordPointer']) == o['value']
            assert not o['dataUnavailable'] and not o['notApplicable']
            assert not o['nativeComponentsAvailable'] and 'denominator' not in o
            parts += 1
        ranked = e.query(query(social.COMPOSITION,'rank',dimension='part:'+part)); assert ranked['status'] == 'computed'
        expected = sorted(SHARES,key=lambda c:(-SHARES[c][i],c))
        assert [x['geography'] for x in ranked['result']['ranking']] == expected
    alias = e.query(query(social.COMPOSITION)); assert alias['status'] == 'computed'
    assert [o['value'] for o in alias['observations']] == [SHARES[c][0] for c in sorted(SHARES)]
    assert 'social_total_alias_families_minors_not_sum' in alias['warnings']
    assert 'social_summary_eur_per_resident_not_area_percent' in alias['warnings']
    for key in social.KEYS:
        for op, reason in [('weighted_ratio','social_native_denominators_unavailable'),
                          ('anomaly','social_peer_anomaly_not_reviewed')]: rejected(e,query(key,op),reason)
        for op in ('absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(key,op,towns=['046005']), 'social_temporal_operations_not_reviewed')
        for periods in (['2013'],['2023'],['2026']): rejected(e,query(key,periods=periods),'social_period_not_frozen')
        for dim in ('numerator','denominator','summary','part:unknown','age:65plus','sex:women'):
            rejected(e,query(key,dimension=dim),'dimension_adapter_not_implemented')
        for selectors in ([{'metric':key},{'metric':'population'}],[{'metric':'population'},{'metric':key}],
                          [{'metric':key},{'metric':social.COMPOSITION if key==social.SPENDING else social.SPENDING}]):
            rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'), 'social_pair_not_jointly_reviewed')
        mutations = [lambda m: m['meta'].update(year='2023'),lambda m:m['meta'].update(unit='number'),
                     lambda m:m['meta'].update(polarity='higher'), lambda m:m.update(sourceUrl='https://example.com'),
                     lambda m:m['rows'][0].update(value=999),lambda m:m['rows'][0].update(benchmarkValue=999),
                     lambda m:m['rows'][0].update(town='Camaiore'),lambda m:m['rows'][0].update(code='046005'),
                     lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0].update(notApplicable=True),
                     lambda m:m['rows'][0].update(ratioComponents={'numerator':1,'denominator':100}),
                     lambda m:m['aggregate'].update(value=999),lambda m:m['aggregate'].update(label='Versilia'),
                     lambda m:m['method'].update(formula='excludes early childhood'),lambda m:m['method'].update(coverage='5/7')]
        if key == social.SPENDING:
            mutations += [lambda m:m['rows'][0]['series']['values'].__setitem__(0,999),lambda m:m['method'].update(caveat='excludes early childhood')]
        else:
            mutations += [lambda m:m['rows'][0]['parts'][2].update(value=None),lambda m:m['rows'][0]['parts'][2].update(value=False),lambda m:m['rows'][0]['parts'].reverse(),
                          lambda m:m['rows'][0]['parts'][0].update(unit='eurPerResident'),lambda m:m['rows'][0]['parts'][0].update(selectorLabel='Altro'),
                          lambda m:m['rows'][0].update(summaryValue=999),lambda m:m['meta'].update(summaryUnit='percent'),
                          lambda m:m['meta'].update(benchmark={'tuscany':167}),lambda m:m['rows'][0].update(series={'years':[2022],'values':[100]}),
                          lambda m:m['aggregate']['parts'][0].update(value=100),lambda m:m['aggregate'].update(summaryValue=100)]
        for mutation in mutations:
            g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed'
            mutation(g._catalog['metrics'][key]);assert g.query(query(key))['status']=='not_computable'
    rejected(e,query(social.COMPOSITION,'series',towns=['046005']),'social_area_history_not_published')
    rejected(e,query(social.COMPOSITION,periods=['2021']),'social_period_not_frozen')
    rejected(e,dict(query(social.COMPOSITION,'benchmark_gap',towns=['046005']),benchmark='tuscany'),'social_area_benchmark_not_available')
    rejected(e,dict(query(social.SPENDING,'benchmark_gap',towns=['046005'],periods=['2021']),benchmark='tuscany'),'social_benchmark_scope_or_period_not_reviewed')
    rejected(e,dict(query(social.SPENDING,'benchmark_gap',towns=['046005']),benchmark='versilia'),'social_benchmark_scope_or_period_not_reviewed')
    for field,value in [('year','2021'),('tuscany',999),('italy',999),('unit','percent'),('sourceSnapshot','other.json')]:
        g=QueryEngine(path,layer='effective');g._catalog['metrics'][social.SPENDING]['meta']['benchmark'][field]=value
        assert g.query(dict(query(social.SPENDING,'benchmark_gap',towns=['046005']),benchmark='tuscany'))['status']=='not_computable'
    for p in (social.NATIVE,social.BENCHMARK):
        q=dict(query(social.SPENDING,'benchmark_gap',towns=['046005']),benchmark='tuscany')
        g=QueryEngine(path,layer='effective');assert g.query(q)['status']=='computed'
        g.file(p)[0]['unexpectedMutation']=True;rejected(g,q,'social_frozen_input_changed')
        g=QueryEngine(path,layer='effective');g.file(p)[1]['sha256']='0'*64;rejected(g,q,'social_frozen_input_changed')
        g=QueryEngine(path,layer='effective');g.file(p)[1]['path']='other.json';rejected(g,q,'social_frozen_input_changed')
    print(f'Social spending PASS: seven fixed municipal indices, nine fixed Camaiore history cells, {parts} fixed area shares, two official benchmarks; replay {histories} historical cells and {gaps} municipal gaps; provenance, rounding, zero, alias, summaries and adversarial guards')


if __name__ == '__main__': regressions(ROOT/'dist/data/site-data.json')
