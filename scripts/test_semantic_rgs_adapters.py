"""Fixed frozen RGS references and adversarial methodological boundaries."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_rgs_adapters as r

# Independent fixed transcription of the frozen municipal extraction. No live claim.
# name, institution, staff, residents, hires, cessations, ages(55+,40–54,<40),
# training days(men,women), published means(men,women,total).
FIXED = {
 '046005': ('Camaiore','1348',188,31864,9,11,(76,87,25),(124,319),(1.4761904761904763,3.127450980392157,2.3018207282913163)),
 '046013': ('Forte dei Marmi','3135',138,6777,5,9,(66,49,23),(36,94),(0.5714285714285714,1.2876712328767124,0.9295499021526419)),
 '046018': ('Massarosa','4177',87,21865,2,3,(39,38,10),(89,178),(3.0689655172413794,3.1228070175438596,3.0958862673926193)),
 '046024': ('Pietrasanta','5461',168,22788,13,12,(65,77,26),(90,114),(1.2,1.2391304347826086,1.2195652173913043)),
 '046028': ('Seravezza','7010',63,12435,4,4,(23,30,10),(54,105),(1.8620689655172413793,3.0,2.4310344827586206)),
 '046030': ('Stazzema','7266',13,2903,1,2,(4,7,2),(6,5),(0.75,0.8333333333333334,0.7916666666666667)),
 '046033': ('Viareggio','7967',412,60755,41,22,(150,197,65),(36,28),(0.22929936305732485,0.11023622047244094,0.16976779176488288)),
}


def query(key, dim='total', op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, dimension=dim, **selection)])


def values(f):
    name, institution, staff, residents, hires, cessations, ages, days, means = f
    return {
        r.STAFF: {'total':staff/residents*1000,'staff':staff,'residents':residents},
        r.AGE: {'total':ages[0]/staff*100, **{'age:'+k:v/staff*100 for k,v in zip(r.AGE_FIELDS,ages)}},
        r.TRAINING: {'total':means[2], 'measure:meanTotalRgs':means[2], 'measure:totalDays':sum(days), 'measure:meanMen':means[0], 'measure:meanWomen':means[1], 'days:men':days[0], 'days:women':days[1]},
        r.TURNOVER: {'total':(hires-cessations)/staff*100,'headcount':hires-cessations,'hires':hires,'cessations':cessations},
    }


def regressions(path):
    e = QueryEngine(path, layer='effective'); checked=0
    for key in r.KEYS:
        for dim in r.dimensions(key):
            result=e.query(query(key,dim)); assert result['status']=='computed',result
            for o in result['observations']:
                f=FIXED[o['geography']]; expected=values(f)[key][dim]
                assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-9)
                assert o['period']=='2024' and o['source'] and o['provenance']
                if not (key==r.TRAINING and dim.startswith('days:') and 'a3TrainingGender' not in e._catalog['metrics'][key]['rows'][0]):
                    assert pointer(e._catalog,o['evidence'][0]['valuePointer'])==o['value']
                assert o['evidence'][1]['institutionCode']==f[1]
                if key==r.STAFF and dim=='total': assert (o['numeratorPeriod'],o['denominatorPeriod'])==('2024-12-31','2024-01-01')
                checked+=1
    total_staff=sum(f[2] for f in FIXED.values()); population=sum(f[3] for f in FIXED.values())
    pooled=[(r.STAFF,'total',total_staff,population,1000),(r.TURNOVER,'total',sum(f[4]-f[5] for f in FIXED.values()),total_staff,100)]
    pooled += [(r.AGE,'age:'+field,sum(f[6][i] for f in FIXED.values()),total_staff,100) for i,field in enumerate(r.AGE_FIELDS)]
    for key,dim,num,den,scale in pooled:
        q=e.query(query(key,dim,'weighted_ratio')); assert q['status']=='computed',q
        assert math.isclose(q['result']['value'],num/den*scale,abs_tol=1e-9)
    joint={'total':1.1697010400972936,'measure:meanTotalRgs':1.1697010400972936,'measure:totalDays':1278,'measure:meanMen':0.9775280898876404,'measure:meanWomen':1.3618739903069468,'days:men':435,'days:women':843}
    for dim,value in joint.items():
        q=e.query(dict(query(r.TRAINING,dim,'benchmark_gap',towns=['046005']),benchmark='versilia')); assert q['status']=='computed',q
        assert q['observations'][1]['value']==value
    q=e.query(dict(query(r.STAFF,op='benchmark_gap',towns=['046005']),benchmark='tuscany')); assert q['status']=='computed',q
    assert q['observations'][1]['value']==23255/3660530*1000
    assert e.query(query(r.TURNOVER))['observations'][4]['value']==0  # Seravezza native zero.
    for key in r.KEYS:
        for op in ('series','trend','relative_change','absolute_change','percentage_points'):
            rejected(e,query(key,op=op,towns=['046005']),'rgs_history_or_temporal_continuity_not_frozen')
        for pair in ([{'metric':key},{'metric':'population'}],[{'metric':'population'},{'metric':key}]):
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'rgs_pair_not_jointly_reviewed')
        rejected(e,query(key,op='anomaly'),'rgs_peer_anomaly_not_reviewed')
        rejected(e,query(key,periods=['2023']),'rgs_period_not_frozen')
    rejected(e,query(r.TRAINING,op='weighted_ratio'),'rgs_measure_not_component_ratio')
    rejected(e,dict(query(r.STAFF,op='benchmark_gap',towns=['046005']),benchmark='italy'),'rgs_benchmark_scope_or_period_not_reviewed')
    rejected(e,query(r.AGE,'meanAge'),'dimension_adapter_not_implemented')
    cases=[
      (r.STAFF, lambda g,row:row.update(residentPopulation=1)),
      (r.STAFF, lambda g,row:row.update(staffAt31Dec=True)),
      (r.STAFF, lambda g,row:g._catalog['metrics'][r.STAFF]['meta'].update(year='2025')),
      (r.AGE, lambda g,row:row.update(town='Viareggio')),
      (r.AGE, lambda g,row:row['parts'][0].update(count=0)),
      (r.AGE, lambda g,row:row['parts'][1].update(unit='number')),
      (r.TRAINING, lambda g,row:row.update(value=sum(FIXED['046005'][7])/188)),
      (r.TRAINING, lambda g,row:row['parts'][1].update(unit='decimal')),
      (r.TRAINING, lambda g,row:g._catalog['metrics'][r.TRAINING].update(sourceUrl='https://example.com/')),
      (r.TURNOVER, lambda g,row:row.update(netHires=None)),
      (r.TURNOVER, lambda g,row:row.update(netCessations=0)),
      (r.AGE, lambda g,row:g._catalog['metrics'][r.AGE]['rows'].append(dict(row))),
    ]
    for key,mutate in cases:
        g=QueryEngine(path,layer='effective');row=next(row for row in g._catalog['metrics'][key]['rows'] if row['code']=='046005');mutate(g,row)
        assert g.query(query(key))['status']=='not_computable'
    for key,native in ((r.AGE,r.ADMIN),(r.TRAINING,r.TRAIN),(r.STAFF,r.BENCH)):
        g=QueryEngine(path,layer='effective'); assert g.query(query(key))['status']=='computed'
        s,ref=g.file(native);s['referenceYear']=2025
        rejected(g,query(key),'rgs_frozen_input_changed')
        g=QueryEngine(path,layer='effective');g.file(native)[1]['sha256']='0'*64
        rejected(g,query(key),'rgs_frozen_input_changed')
    for key, field in ((r.TRAINING, 'a3TrainingGender'), (r.TURNOVER, 'a3StaffTurnoverDimensions')):
        g=QueryEngine(path,layer='effective');row=g._catalog['metrics'][key]['rows'][0]
        if field in row:
            row[field]['referenceYear']=2023
            rejected(g,query(key),'rgs_companion_changed')
    g=QueryEngine(path,layer='effective');g._catalog['metrics'][r.TRAINING]['aggregate']['parts'][2]['value']=99
    rejected(g,dict(query(r.TRAINING,op='benchmark_gap',towns=['046005']),benchmark='versilia'),'rgs_public_native_mismatch')
    print(f'RGS adapters PASS: {checked} fixed observations including aliases, five pooled ratios, eight published references; native zero/net negative retained; adversarial and methodology guards')


if __name__=='__main__': regressions(ROOT/'dist/data/site-data.json')
