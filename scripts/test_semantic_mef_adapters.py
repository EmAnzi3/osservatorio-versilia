"""Fixed municipal components, separate frozen-history replay, adversarial boundaries."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_mef_adapters as m

# Fixed references transcribed from the versioned extraction, not reacquired live.
FIXED = {'046005': {'name': 'Camaiore',
            'taxpayers': 24408,
            'adults': 27833,
            'totalAmount': 598867041,
            'totalFrequency': 23579,
            'sources': {'buildings': (23027261, 10411),
                        'employment': (289610500, 12578),
                        'pension': (167316194, 8328),
                        'selfEmployment': (23526140, 375),
                        'entrepreneurOrdinary': (5125272, 92),
                        'entrepreneurSimplified': (23822193, 890),
                        'participation': (35375782, 1777)},
            'bands': {'le0': None,
                      '0to10k': 5719,
                      '10to15k': 2931,
                      '15to26k': 6828,
                      '26to55k': 6415,
                      '55to75k': 751,
                      '75to120k': 604,
                      'over120k': None}},
 '046013': {'name': 'Forte dei Marmi',
            'taxpayers': 5157,
            'adults': 5839,
            'totalAmount': 225345208,
            'totalFrequency': 4924,
            'sources': {'buildings': (20838890, 2446),
                        'employment': (87847722, 2105),
                        'pension': (45824668, 1964),
                        'selfEmployment': (18134848, 154),
                        'entrepreneurOrdinary': (2874338, 26),
                        'entrepreneurSimplified': (6361110, 204),
                        'participation': (14422243, 508)},
            'bands': {'le0': 0,
                      '0to10k': 1110,
                      '10to15k': 535,
                      '15to26k': 1120,
                      '26to55k': 1268,
                      '55to75k': 266,
                      '75to120k': 306,
                      'over120k': 319}},
 '046018': {'name': 'Massarosa',
            'taxpayers': 16404,
            'adults': 18938,
            'totalAmount': 369561101,
            'totalFrequency': 15934,
            'sources': {'buildings': (7415157, 7044),
                        'employment': (202735109, 9125),
                        'pension': (111076251, 5530),
                        'selfEmployment': (8990333, 130),
                        'entrepreneurOrdinary': (1530559, 27),
                        'entrepreneurSimplified': (12718876, 502),
                        'participation': (14909135, 831)},
            'bands': {'le0': 0,
                      '0to10k': 3584,
                      '10to15k': 1909,
                      '15to26k': 5055,
                      '26to55k': 4662,
                      '55to75k': 367,
                      '75to120k': 244,
                      'over120k': 113}},
 '046024': {'name': 'Pietrasanta',
            'taxpayers': 17673,
            'adults': 20041,
            'totalAmount': 457960925,
            'totalFrequency': 17066,
            'sources': {'buildings': (20386797, 7452),
                        'employment': (206292313, 8641),
                        'pension': (137002792, 6352),
                        'selfEmployment': (21048594, 324),
                        'entrepreneurOrdinary': (4172407, 61),
                        'entrepreneurSimplified': (16879061, 637),
                        'participation': (28089097, 1244)},
            'bands': {'le0': None,
                      '0to10k': 4156,
                      '10to15k': 2074,
                      '15to26k': 4713,
                      '26to55k': 4758,
                      '55to75k': 583,
                      '75to120k': 481,
                      'over120k': None}},
 '046028': {'name': 'Seravezza',
            'taxpayers': 9530,
            'adults': 10801,
            'totalAmount': 211041286,
            'totalFrequency': 9182,
            'sources': {'buildings': (7002788, 3795),
                        'employment': (103445668, 4887),
                        'pension': (67877930, 3456),
                        'selfEmployment': (5953679, 121),
                        'entrepreneurOrdinary': (1149216, 24),
                        'entrepreneurSimplified': (7516261, 276),
                        'participation': (10013752, 554)},
            'bands': {'le0': 0,
                      '0to10k': 2225,
                      '10to15k': 1168,
                      '15to26k': 2802,
                      '26to55k': 2540,
                      '55to75k': 228,
                      '75to120k': 147,
                      'over120k': 72}},
 '046030': {'name': 'Stazzema',
            'taxpayers': 2150,
            'adults': 2483,
            'totalAmount': 42149013,
            'totalFrequency': 2098,
            'sources': {'buildings': (495211, 916),
                        'employment': (23693613, 1140),
                        'pension': (14259777, 808),
                        'selfEmployment': (559217, 9),
                        'entrepreneurOrdinary': (None, None),
                        'entrepreneurSimplified': (837672, 50),
                        'participation': (1310584, 83)},
            'bands': {'le0': None,
                      '0to10k': 535,
                      '10to15k': 313,
                      '15to26k': 673,
                      '26to55k': 526,
                      '55to75k': 19,
                      '75to120k': 28,
                      'over120k': None}},
 '046033': {'name': 'Viareggio',
            'taxpayers': 46507,
            'adults': 53038,
            'totalAmount': 1207277614,
            'totalFrequency': 45173,
            'sources': {'buildings': (43254414, 20502),
                        'employment': (601347696, 25522),
                        'pension': (368024027, 15761),
                        'selfEmployment': (49737334, 730),
                        'entrepreneurOrdinary': (11813533, 114),
                        'entrepreneurSimplified': (38793176, 1315),
                        'participation': (48082990, 2533)},
            'bands': {'le0': 4,
                      '0to10k': 10273,
                      '10to15k': 5374,
                      '15to26k': 12306,
                      '26to55k': 13702,
                      '55to75k': 1574,
                      '75to120k': 1265,
                      'over120k': 675}}}


def query(key,dim='total',op='compare',**fields):
    return dict(operation=op,selectors=[dict(metric=key,dimension=dim,**fields)])


def regressions(path):
    e=QueryEngine(path,layer='effective');checked=0
    groups=[('le0','0to10k','10to15k'),('15to26k',),('26to55k',),('55to75k','75to120k','over120k')]
    for code,f in FIXED.items():
        for source,(amount,count) in f['sources'].items():
            # Single municipality compare needs two observations: inspect selected
            # observation independently inside a full-cohort query with opt-in.
            r=e.query(dict(query(m.PROFILE,'source:'+source),allowPartial=True));assert r['status']=='computed',r
            o=next(o for o in r['observations'] if o['geography']==code);expected=None if amount is None or count is None or count==0 else amount/count
            assert o['value'] is None if expected is None else math.isclose(o['value'],expected,abs_tol=1e-8)
            assert o['numerator']==amount and o['denominator']==count and o['scale']==1
            assert pointer(e._catalog,o['evidence'][0]['valuePointer'])==o['value']
            checked+=1
        for key,expected,num,den in [(m.PENSION,f['sources']['pension'][0]/f['totalAmount']*100,f['sources']['pension'][0],f['totalAmount']),(m.TAXPAYERS,f['taxpayers']/f['adults']*100,f['taxpayers'],f['adults'])]:
            r=e.query(query(key));assert r['status']=='computed',r;o=next(o for o in r['observations'] if o['geography']==code)
            assert math.isclose(o['value'],expected,abs_tol=1e-8) and o['numerator']==num and o['denominator']==den
            if key==m.TAXPAYERS:assert o['period']==m.HYBRID and o['numeratorPeriod']=='2024' and o['denominatorPeriod']=='2026-01-01'
            assert pointer(e._catalog,o['evidence'][0]['valuePointer'])==o['value']
            checked+=1
        known=sum(v for v in f['bands'].values() if v is not None)
        for dim,num,den in [(f'macro:{i}',sum(f['bands'][k] for k in keys if f['bands'][k] is not None),known) for i,keys in enumerate(groups)]+[('band:'+k,v,f['totalFrequency']) for k,v in f['bands'].items()]:
            r=e.query(dict(query(m.DISTRIBUTION,dim),allowPartial=True));assert r['status']=='computed',r;o=next(o for o in r['observations'] if o['geography']==code);expected=None if num is None else num/den*100
            assert o['value'] is None if expected is None else math.isclose(o['value'],expected,abs_tol=1e-8)
            assert o['numerator']==num and o['denominator']==den
            assert pointer(e._catalog,o['evidence'][0]['valuePointer'])==o['value']
            checked+=1
        for key,alias in [(m.PROFILE,'source:employment'),(m.DISTRIBUTION,'macro:0')]:
            a=e.query(query(key));b=e.query(query(key,alias));assert a['status']==b['status']=='computed';assert [o['value'] for o in a['observations']]==[o['value'] for o in b['observations']];checked+=1
    # Separate history replay: source components and public series, not new fixed
    # independent historical acquisitions. Null years remain absent from series.
    h=e.file(m.HISTORY)[0];history=0
    for key in (m.PROFILE,m.PENSION):
        for dim in m.dimensions(key):
            for code,f in FIXED.items():
                request=query(key,dim,op='series',towns=[code]);r=e.query(request)
                raw=h['towns'][f['name']]['countsByYear'];source='employment' if dim=='total' else dim[7:]
                expected=[]
                for year in ('2023','2024'):
                    n=raw[year]
                    if key==m.PENSION:value=n['pensionIncome']['amountEuro']/n['totalIncome']['amountEuro']*100
                    else:
                        x=next(x for x in n['incomeSources'] if x['key']==source);value=None if x['frequency'] in (None,0) or x['amountEuro'] is None else x['amountEuro']/x['frequency']
                    if value is not None:expected.append((year,value))
                if not expected:assert r['status']=='not_computable',r;continue
                assert r['status']=='computed',r
                assert [(o['period'],o['value']) for o in r['observations']]==expected
                history+=len(expected)
    # Pooled values use component sums, including hybrid-date denominators.
    for key,dim,num,den,scale in [(m.PROFILE,'source:employment',sum(f['sources']['employment'][0] for f in FIXED.values()),sum(f['sources']['employment'][1] for f in FIXED.values()),1),(m.PENSION,'total',sum(f['sources']['pension'][0] for f in FIXED.values()),sum(f['totalAmount'] for f in FIXED.values()),100),(m.TAXPAYERS,'total',sum(f['taxpayers'] for f in FIXED.values()),sum(f['adults'] for f in FIXED.values()),100)]:
        r=e.query(query(key,dim,op='weighted_ratio'));assert r['status']=='computed' and math.isclose(r['result']['value'],num/den*scale,abs_tol=1e-8),r
    fixed_bench={m.PROFILE:(23942.870922326307,24223.942872801104),m.PENSION:(30.97777568992456,30.224327018823598),m.TAXPAYERS:(89.35750687431118,85.07684720194473)}
    for key,values in fixed_bench.items():
        for scope,value in zip(('tuscany','italy'),values):
            r=e.query(dict(query(key,op='benchmark_gap',towns=['046018']),benchmark=scope));assert r['status']=='computed' and r['observations'][1]['value']==value,r
    for key in m.KEYS:
        for op in ('trend','absolute_change','relative_change','percentage_points','anomaly'):
            rejected(e,query(key,op=op),'mef_peer_anomaly_not_reviewed' if op=='anomaly' else 'mef_temporal_change_not_reviewed')
        rejected(e,dict(operation='correlation',selectors=[dict(metric='population'),dict(metric=key)],axis='municipalities',method='pearson',purpose='descriptive'),'mef_pair_not_jointly_reviewed')
    rejected(e,query(m.TAXPAYERS,periods=['2024']),'mef_hybrid_period_required')
    rejected(e,query(m.DISTRIBUTION,op='series',towns=['046018']),'mef_history_not_frozen')
    rejected(e,dict(query(m.PROFILE,'source:pension',op='benchmark_gap',towns=['046018']),benchmark='italy'),'mef_benchmark_dimension_not_reviewed')
    rejected(e,query(m.DISTRIBUTION,'band:le0'),'partial_coverage_requires_opt_in')
    rejected(e,query(m.PROFILE,'source:entrepreneurOrdinary'),'partial_coverage_requires_opt_in')
    # Public mutations and warmed native cache must fail closed.
    for mode in ('zero_for_null','band_denominator','identity','unit','year','part_unit','source_amount','scale','adult','benchmark','native','hash'):
        g=QueryEngine(path,layer='effective');key=m.DISTRIBUTION if mode in ('zero_for_null','band_denominator') else m.TAXPAYERS if mode=='adult' else m.PROFILE
        row=next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005');request=query(key)
        if mode=='zero_for_null':row['detailParts'][0]['value']=0;request=query(key,'band:le0')
        elif mode=='band_denominator':row['parts'][0]['value']=8650/23579*100
        elif mode=='identity':row['town']='Wrong'
        elif mode=='unit':g._catalog['metrics'][key]['meta']['unit']='percent'
        elif mode=='year':g._catalog['metrics'][key]['meta']['year']='2025'
        elif mode=='part_unit':row['parts'][0]['unit']='number'
        elif mode=='source_amount':row['parts'][0]['amountEuro']+=1
        elif mode=='scale':row['mefScaleComponents']['scale']=100
        elif mode=='adult':row['adultPopulation2026']+=1
        elif mode=='benchmark':g._catalog['metrics'][key]['meta']['benchmark']['part']='Pensione';request=dict(query(key,op='benchmark_gap',towns=['046005']),benchmark='italy')
        else:
            s,ref=g.file(m.CURRENT)
            if mode=='native':s['towns']['Camaiore']['taxpayers']+=1
            else:ref['sha256']='0'*64
        assert g.query(request)['status']=='not_computable',(mode,g.query(request))
    assert checked==161
    print(f'A6 MEF PASS: {checked} fixed current observations including aliases/nulls; {history} frozen historical observations replayed; three native pooled ratios, six benchmark references and adversarial/refusal boundaries')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
