#!/usr/bin/env python3
"""Independent numeric references, guarded queries, and actual catalog adapters."""
import copy
import json
import math
import tempfile
from fractions import Fraction
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT, SNAPSHOT, calculate, coefficient, ranks
from semantic_query_adapters import CENSUS, CENSUS_PATH, CENSUS_BENCHMARK, MEF_BENCHMARK, AGE_BANDS


def request(operation, metric='population', **selection):
    return {'operation':operation,'selectors':[dict(metric=metric,**selection)]}


def rejected(engine, query, reason):
    report = engine.query(query)
    assert report['status']=='not_computable' and any(reason in r for r in report['reasons']),report
    assert report['result'] is None
    return report


def regressions():
    assert ranks([1,2,2,4])==[1,2.5,2.5,4]
    assert math.isclose(coefficient([1,2,3],[1,4,9],'pearson'),4*math.sqrt(3)/7,rel_tol=1e-12)
    assert math.isclose(coefficient([1,2,2,4],[4,1,1,3],'spearman'),-1/3,abs_tol=1e-12)
    assert coefficient([1,1,1],[1,2,3],'pearson') is None
    assert math.isclose(coefficient([1e200,2e200,3e200],[3e200,2e200,1e200],'pearson'),-1,abs_tol=1e-12)
    rows=[dict(value=v,geography=str(i),period=p,unit='number') for i,(v,p) in enumerate([(1,'2019'),(3,'2020'),(9,'2023')])]
    assert math.isclose(calculate('trend',rows,{'timeAxis':[2019,2020,2023]})['slope'],2,abs_tol=1e-12)
    rank=calculate('rank',[dict(value=v,geography=str(i)) for i,v in enumerate([9,5,5,1])],{})
    assert [r['rank'] for r in rank['ranking']]==[1,2,2,4]
    assert calculate('relative_change',[{'value':50,'period':'2020','unit':'number'},{'value':55,'period':'2021','unit':'number'}],{})['value']==10

    engine=QueryEngine(ROOT/'data/site-data.json')
    q=request('absolute_change',towns=['046018'],periods=['2019','2026'])
    report=engine.query(q)
    assert report['status']=='computed' and report['result']['value']==86,report
    assert report==engine.query(q) # no runtime timestamp/randomness in results
    q['selectors'][0]['periods'][0]='2020'
    assert report['query']['selectors'][0]['periods'][0]=='2019'
    assert all(len(o['provenance'][0]['sha256'])==64 for o in report['observations'])
    assert report['observations'][0]['source'].endswith('POSAS_2019_it_046_Lucca.zip')
    assert report['observations'][0]['provenance'][0]['valuePointer']=='/metrics/population/rows/0/series/values/0'
    assert report['catalogPath']=='data/site-data.json'
    other=engine.catalog;other['metrics']['population']['rows'][0]['value']=1
    assert engine.catalog['metrics']['population']['rows'][0]['value']!=1
    report['observations'][0]['provenance'][1]['status']['posas_2026']='mutated'
    assert engine.query(request('absolute_change',towns=['046018'],periods=['2019','2026']))['observations'][0]['provenance'][1]['status']['posas_2026']!='mutated'
    income=engine.query(request('absolute_change','income',towns=['046018'],periods=['2011','2024']))
    assert income['status']=='computed' and math.isclose(income['result']['value'],5174.99,abs_tol=1e-8)
    assert 'raw_income_archive_not_verified_by_adapter' in income['warnings']
    rejected(engine,request('compare','fuelPrices'),'adapter_not_implemented')
    rejected(engine,request('compare',dimension='women'),'dimension_adapter_not_implemented')
    rejected(engine,request('series',towns=['046018'],periods=['2024/25']),'unsupported_annual_period')
    rejected(engine,request('series',towns=['046018'],periods=['2026','2019']),'ordered_periods')
    rejected(engine,request('series',towns=['046018'],periods=['2025','2025']),'duplicate_period')
    rejected(engine,request('compare',towns=['unknown']),'unknown_or_duplicate_geography')
    rejected(engine,request('compare',towns=['046018','046018']),'unknown_or_duplicate_geography')
    rejected(engine,request('series',towns=['046018'],periods=['2018']),'period_not_available')
    rejected(engine,request('percentage_points',towns=['046018'],periods=['2019','2026']),'percentage_unit_required')
    rejected(engine,dict(request('compare'),allowPartial='yes'),'allowPartial_must_be_boolean')
    rejected(engine,dict(request('compare'),method='ignored'),'fields_not_applicable')
    rejected(engine,dict(request('compare'),definition='injected'),'invalid_query_fields')
    corr={'operation':'correlation','selectors':[{'metric':'population'},{'metric':'income'}],
          'axis':'municipalities','method':'pearson','purpose':'Technical alignment regression, no territorial policy inference'}
    rejected(engine,corr,'paired_period_mismatch')
    for s in corr['selectors']:s['periods']=['2024']
    r=engine.query(corr)
    assert r['status']=='computed' and r['result']['n']==7,r
    assert r['pairCoverage']=={'requested':7,'paired':7,'excludedKeys':[]}
    assert len(r['result']['leaveOneOut'])==7 and r['result']['pValue'] is None
    assert 'association_not_causation' in r['warnings']
    bad=copy.deepcopy(corr);bad.pop('purpose');rejected(engine,bad,'selection_purpose')
    bad=copy.deepcopy(corr);bad['method']='unknown';rejected(engine,bad,'correlation_method')

    with tempfile.TemporaryDirectory(prefix='a6-query-') as temporary:
        root=Path(temporary)
        snapshot=root/SNAPSHOT;snapshot.parent.mkdir(parents=True)
        snapshot.write_bytes((ROOT/SNAPSHOT).read_bytes())
        path=root/'catalog.json'
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][0]=0
        path.write_text(json.dumps(canonical))
        altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('absolute_change',towns=['046018'],periods=['2019','2026']),'snapshot_mismatch')
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['income']['rows'][0]['series']['values'][0]=0
        path.write_text(json.dumps(canonical))
        altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('relative_change','income',towns=['046018'],periods=['2011','2024']),'zero_baseline')
        canonical=copy.deepcopy(engine.catalog)
        # The shared eligibility guard refuses implicit exclusion of missing values.
        canonical['metrics']['population']['rows'][0]['value']=None
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('compare'),'partial_coverage_requires_opt_in')
        partial=altered.query(dict(request('compare'),allowPartial=True))
        assert partial['status']=='computed' and len(partial['excluded'])==1
        assert partial['coverage']['requested']==7 and partial['coverage']['usable']==6
        historical=altered.query(request('series',towns=['046018'],periods=['2024','2026']))
        assert historical['status']=='computed' and historical['coverage']['usable']==2
        # Non-overlapping variables retain the exact keys excluded from pairing.
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][5]=None # 2024
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        partial=altered.query(dict(corr,allowPartial=True))
        assert partial['status']=='computed' and partial['result']['n']==6,partial
        assert partial['pairCoverage']['excludedKeys']==['046018']
        assert any(x.get('pairingKey')=='046018' for x in partial['excluded'])
        canonical=copy.deepcopy(engine.catalog)
        for row in canonical['metrics']['income']['rows']:
            row['value']=123
            row['series']['values'][-1]=123
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,corr,'constant_variable')
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][5]=None
        # A selected observation with no corresponding catalog series is refused,
        # rather than treated as an implicit null or silently narrowed selection.
        canonical['metrics']['population']['rows'][0]['series']['years'].pop()
        canonical['metrics']['population']['rows'][0]['series']['values'].pop()
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('series',towns=['046018'],periods=['2026']),'period_not_available')


def ratio_regressions():
    # Unequal denominators: 110/1100*100 = 10; the mean of 20% and 9% is 14.5%.
    rows=[dict(value=20,numerator=20,denominator=100,scale=100,unit='percent',geography='a',period='2023'),
          dict(value=9,numerator=90,denominator=1000,scale=100,unit='percent',geography='b',period='2023')]
    assert calculate('weighted_ratio',rows,{})['value']==10
    assert calculate('percentage_points',[dict(value=50,unit='percent',period='2021'),dict(value=55,unit='percent',period='2023')],{})['value']==5
    engine=QueryEngine(ROOT/'data/site-data.json')
    weighted=request('weighted_ratio','femaleEmploymentRate')
    r=engine.query(weighted)
    assert r['status']=='computed' and math.isclose(r['result']['value'],float(Fraction(27717,50153)*100),abs_tol=1e-12),r
    assert r['result']['numerator']==27717 and r['result']['denominator']==50153
    assert len(r['result']['geographies'])==7 and 'disjointPopulationEvidence' in r['policy']
    pp=engine.query(request('percentage_points','femaleEmploymentRate',towns=['046018'],periods=['2021','2023']))
    # Use the frozen municipal counts as a separate arithmetic reference.
    source=json.loads((ROOT/CENSUS_PATH).read_text())
    raw=next(x for x in source['raw']['2023'] if x['code']=='046018')
    expected=float((Fraction(3937,6976)-Fraction(3731,6989))*100)
    assert pp['status']=='computed' and pp['result']['unit']=='percentage_points'
    assert math.isclose(pp['result']['value'],expected,abs_tol=1e-12)
    gap=dict(request('benchmark_gap','femaleEmploymentRate',towns=['046018']),benchmark='tuscany')
    r=engine.query(gap)
    expected=float(Fraction(raw['P103'],raw['female1564'])*100-Fraction(707029,1136557)*100)
    assert r['status']=='computed' and math.isclose(r['result']['value'],expected,abs_tol=1e-12),r
    assert r['result']['unit']=='percentage_points'
    assert r['observations'][0]['evidence'][1]['path']==CENSUS_PATH
    assert r['observations'][1]['evidence'][0]['path']==CENSUS_BENCHMARK
    assert r['observations'][1]['geography']=='tuscany'
    assert len(r['adapterImplementationSha256'])==64
    rejected(engine,dict(gap,benchmark='unknown'),'benchmark_scope_not_supported')
    rejected(engine,dict(request('compare'),benchmark='tuscany'),'fields_not_applicable')
    rejected(engine,dict(request('benchmark_gap','femaleEmploymentRate'),benchmark='tuscany'),'one_municipality')
    rejected(engine,dict(request('benchmark_gap','femaleEmploymentRate',towns=['046018'],periods=['2021']),benchmark='tuscany'),'period_unit_or_quality')
    rejected(engine,dict(request('benchmark_gap','population',towns=['046018']),benchmark='italy'),'benchmark_adapter_not_implemented')
    rejected(engine,request('weighted_ratio','income'),'verified_ratio_adapter_required')
    rejected(engine,request('weighted_ratio','femaleEmploymentRate',towns=['046018','046018']),'duplicate_geography')
    rejected(engine,request('percentage_points','housingStockPer1000',towns=['046018'],periods=['2021','2023']),'percentage_unit_required')
    rejected(engine,dict(weighted,disjointPopulationEvidence='injected'),'invalid_query_fields')
    with tempfile.TemporaryDirectory(prefix='a6-ratios-') as temporary:
        root=Path(temporary)
        for relative in [CENSUS_PATH,CENSUS_BENCHMARK,MEF_BENCHMARK]:
            dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/relative).read_bytes())
        path=root/'catalog.json'
        catalog=engine.catalog
        catalog['metrics']['femaleEmploymentRate']['rows'][0]['value']=None
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,weighted,'partial_coverage_requires_opt_in')
        partial=altered.query(dict(weighted,allowPartial=True))
        assert partial['status']=='computed' and partial['coverage']['usable']==6
        assert len(partial['result']['geographies'])==6 and '046018' not in partial['result']['geographies']
        assert partial['result']['denominator']==50153-raw['female1564']
        rejected(altered,dict(gap,allowPartial=True),'explicit_benchmark_comparability_required')
        catalog=engine.catalog
        catalog['metrics']['femaleEmploymentRate']['rows'][0]['value']+=1
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,weighted,'source_ratio_reconciliation_failed')
        catalog=engine.catalog;path.write_text(json.dumps(catalog))
        snapshot=json.loads((root/CENSUS_PATH).read_text())
        snapshot['raw']['2023'][0]['female1564']=0
        (root/CENSUS_PATH).write_text(json.dumps(snapshot));altered=QueryEngine(path,repository_root=root)
        rejected(altered,weighted,'invalid_source_ratio_components')
        (root/CENSUS_PATH).write_bytes((ROOT/CENSUS_PATH).read_bytes())
        benchmark=json.loads((root/CENSUS_BENCHMARK).read_text())
        benchmark['benchmarks']['femaleEmploymentRate']['tuscany']+=1
        (root/CENSUS_BENCHMARK).write_text(json.dumps(benchmark));altered=QueryEngine(path,repository_root=root)
        rejected(altered,gap,'source_ratio_reconciliation_failed')
        (root/CENSUS_BENCHMARK).write_bytes((ROOT/CENSUS_BENCHMARK).read_bytes())
        catalog['metrics']['femaleEmploymentRate']['meta']['benchmark']={'year':2021,'sourceSnapshot':CENSUS_BENCHMARK,'tuscany':0,'italy':0,'source':'Istat','url':'https://www.istat.it/notizia/dati-per-sezioni-di-censimento/'}
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,gap,'published_benchmark_context_mismatch')
        catalog=engine.catalog;path.write_text(json.dumps(catalog))
        mef=json.loads((root/MEF_BENCHMARK).read_text())
        mef['source']['amountHeader']='Reddito complessivo - Ammontare in euro'
        (root/MEF_BENCHMARK).write_text(json.dumps(mef));altered=QueryEngine(path,repository_root=root)
        rejected(altered,dict(request('benchmark_gap','income',towns=['046018']),benchmark='italy'),'benchmark_mef_definition_changed')



def anomaly_request(metric='income', **selection):
    return dict(request('anomaly',metric,**selection),rule='tukey_1_5_iqr',
                reference='selected_municipalities',purpose='Descriptive technical peer screening; no policy priority')


def age_anomaly_regressions():
    engine=QueryEngine(ROOT/'data/site-data.json')
    for dimension in AGE_BANDS:
        q=request('weighted_ratio','ageDistribution',dimension=dimension,periods=['2026'])
        result=engine.query(q)
        assert result['status']=='computed',result
        source=json.loads((ROOT/SNAPSHOT).read_text())['posas']['ageSex2026']
        _,lo,hi=AGE_BANDS[dimension]
        numerator=sum(x['total'] for rows in source.values() for x in rows if lo<=x['age']<=hi)
        denominator=sum(x['total'] for rows in source.values() for x in rows)
        assert result['result']['numerator']==numerator and result['result']['denominator']==denominator
        assert math.isclose(result['result']['value'],float(Fraction(numerator,denominator)*100),abs_tol=1e-12)
        assert all('/parts/' in x['evidence'][0]['valuePointer'] for x in result['observations'])
    r=engine.query(request('compare','ageDistribution',dimension='age:0-14',towns=['046018','046005']))
    massarosa=next(o for o in r['observations'] if o['geography']=='046018')
    assert massarosa['numerator']==2213 and massarosa['denominator']==21782
    assert math.isclose(massarosa['value'],float(Fraction(2213,21782)*100),abs_tol=1e-12)
    rejected(engine,request('compare','ageDistribution'),'explicit_age_band_required')
    rejected(engine,request('compare','ageDistribution',dimension='age:80+'),'explicit_age_band_required')
    rejected(engine,request('series','ageDistribution',dimension='age:0-14',towns=['046018']),'historical_dimension_not_available')
    rejected(engine,request('compare','ageDistribution',dimension='age:0-14',periods=['2025']),'current_period_mismatch')
    corr={'operation':'correlation','selectors':[{'metric':'ageDistribution','dimension':'age:0-14'},
        {'metric':'ageDistribution','dimension':'age:85+'}], 'method':'spearman','axis':'municipalities',
        'purpose':'Technical pairing of two dimensions; same denominator, compositional relation'}
    c=engine.query(corr)
    assert c['status']=='computed' and c['result']['n']==7,c
    assert 'compositional_age_shares_share_denominator' in c['warnings']
    assert all(pair['x']['dimension']=='age:0-14' and pair['y']['dimension']=='age:85+' for pair in c['result']['pairs'])
    # Independent quartile reference: [0,1,2,3,4,5,100] -> Q1=1.5 Q3=4.5.
    rows=[dict(value=v,geography=str(i),unit='number') for i,v in enumerate([0,1,2,3,4,5,100])]
    a=calculate('anomaly',rows,{})
    assert (a['q1'],a['q3'],a['iqr'],a['lowerFence'],a['upperFence'])==(1.5,4.5,3,-3,9)
    assert a['observations'][-1]['classification']=='above_fence'
    # Exact fence values are inside: [0,1,2,7] has upper fence 7.
    a=calculate('anomaly',[dict(value=v,geography=str(i),unit='number') for i,v in enumerate([0,1,2,7])],{})
    assert a['q1']==.75 and a['q3']==3.25 and a['upperFence']==7
    assert a['observations'][-1]['classification']=='within_fences'
    a=engine.query(anomaly_request())
    assert a['status']=='computed' and a['result']['n']==7,a
    assert a==engine.query(anomaly_request())
    assert a['policy']['referenceDistributionEvidence']['catalogSha256']==engine.catalog_hash
    assert 'reference_selection_changes_fences' in a['warnings']
    rejected(engine,request('anomaly','income'),'supported_anomaly_rule_and_reference')
    rejected(engine,dict(anomaly_request(),rule='zscore'),'supported_anomaly_rule_and_reference')
    rejected(engine,dict(anomaly_request(),reference='italy'),'supported_anomaly_rule_and_reference')
    rejected(engine,dict(anomaly_request(),purpose=''),'explicit_anomaly_purpose')
    rejected(engine,anomaly_request(towns=['046018','046005','046024']),'four_usable')
    rejected(engine,dict(request('rank','income'),rule='tukey_1_5_iqr'),'fields_not_applicable')
    rejected(engine,dict(anomaly_request(),referenceDistributionEvidence='caller evidence'),'invalid_query_fields')
    with tempfile.TemporaryDirectory(prefix='a6-age-anomaly-') as temporary:
        root=Path(temporary);snapshot=root/SNAPSHOT;snapshot.parent.mkdir(parents=True)
        snapshot.write_bytes((ROOT/SNAPSHOT).read_bytes());path=root/'catalog.json'
        catalog=engine.catalog
        catalog['metrics']['ageDistribution']['rows'][0]['parts'][0]['value']=None
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        q=request('weighted_ratio','ageDistribution',dimension='age:0-14')
        rejected(altered,q,'partial_coverage_requires_opt_in')
        a=altered.query(dict(q,allowPartial=True))
        assert a['status']=='computed' and len(a['result']['geographies'])==6
        assert '046018' not in a['result']['geographies']
        # An explicit current year must preserve the carrier's n.a. flag.
        catalog=engine.catalog;catalog['metrics']['ageDistribution']['rows'][0]['notApplicable']=True
        catalog['metrics']['ageDistribution']['rows'][0]['value']=None
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('compare','ageDistribution',dimension='age:0-14',periods=['2026']),'partial_coverage_requires_opt_in')
        catalog=engine.catalog;catalog['metrics']['ageDistribution']['rows'][0]['parts'][0]['count']+=1
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,q,'age_band_count_mismatch')
        catalog=engine.catalog;path.write_text(json.dumps(catalog))
        raw=json.loads(snapshot.read_text());raw['posas']['ageSex2026']['Massarosa'][0]['women']+=1
        snapshot.write_text(json.dumps(raw));altered=QueryEngine(path,repository_root=root)
        rejected(altered,q,'age_snapshot_invalid_counts')
        snapshot.write_bytes((ROOT/SNAPSHOT).read_bytes())
        raw=json.loads(snapshot.read_text());raw['posas']['ageSex2026']['Massarosa'].pop()
        snapshot.write_text(json.dumps(raw));altered=QueryEngine(path,repository_root=root)
        rejected(altered,q,'age_snapshot_non_exhaustive')
        catalog=engine.catalog
        catalog['metrics']['income']['rows'][0]['value']=None
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,anomaly_request(),'partial_coverage_requires_opt_in')
        a=altered.query(dict(anomaly_request(),allowPartial=True))
        assert a['status']=='computed' and a['result']['n']==6 and len(a['excluded'])==1
        for row in catalog['metrics']['income']['rows']:row['value']=1
        path.write_text(json.dumps(catalog));altered=QueryEngine(path,repository_root=root)
        rejected(altered,anomaly_request(),'zero_interquartile_range')
        # A future raw point cannot inherit an attestation scoped to 2021/2023.
        snap=root/CENSUS_PATH
        source=json.loads((ROOT/CENSUS_PATH).read_text())
        for item in source['acceptedIndicators']:item['years']=[2021]
        snap.write_text(json.dumps(source));path.write_text(json.dumps(engine.catalog))
        altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('compare','femaleEmploymentRate'),'census_comparability_not_attested')


def audit(path, layer):
    engine=QueryEngine(path,layer=layer)
    matrix=engine.coverage()
    assert len(matrix)==len(engine.catalog['metrics'])
    assert {r['metric'] for r in matrix}==set(engine.catalog['metrics'])
    adapters=[r['metric'] for r in matrix if r['engine']['status']=='adapter_present_query_preconditions_apply']
    expected={'population','income','femaleEmploymentRate','maleEmploymentRate','housingStockPer1000','nonOccupiedHomesPer1000','ageDistribution','earlyChildhoodPotentialCapacityRate','tourismPresences','tourismIntensity'}
    if engine.catalog['metrics']['elderlyHomeCare']['meta'].get('demographicSource'):expected.add('elderlyHomeCare')
    from semantic_query_ars_adapters import KEYS, LEGACY_ONLY
    catalog=engine.catalog
    expected.update(k for k in KEYS if k in catalog['metrics'] and ((k in LEGACY_ONLY and all(isinstance(r.get('series'),dict) and r['series'].get('sourceSnapshot')=='data/source-snapshots/ars-a3-5-legacy-history.json' for r in catalog['metrics'][k]['rows'])) or catalog['metrics'][k]['meta'].get('demographicSource')))
    import semantic_query_business_adapters as business
    expected.update(k for k in business.KEYS if k in catalog['metrics'] and (k not in business.FRAME_FIELDS or all(isinstance(r.get('economicScopes'),dict) for r in catalog['metrics'][k]['rows'])))
    import semantic_query_finance_adapters as finance
    expected.update(k for k in finance.KEYS if k in catalog["metrics"])
    import semantic_query_distinct_finance_adapters as distinct
    expected.update(k for k in distinct.KEYS if k in catalog["metrics"])
    import semantic_query_census_adapters as census
    expected.update(k for k in census.KEYS if k in catalog["metrics"])
    import semantic_query_coast_adapters as coast
    import semantic_query_bathing_adapters as bathing
    import semantic_query_maritime_adapters as maritime
    import semantic_query_extractive_adapters as extractive
    import semantic_query_remediation_adapters as remediation
    import semantic_query_pab_adapters as pab
    import semantic_query_climate_adapters as climate
    import semantic_query_classification_adapters as classification
    import semantic_query_water_quality_adapters as water_quality
    import semantic_query_agriculture_profile_adapters as profiles
    expected.update(k for k in classification.KEYS if k in catalog['metrics'])
    expected.update(k for k in water_quality.KEYS if k in catalog['metrics'])
    expected.update(k for k in profiles.KEYS if k in catalog['metrics'])
    expected.update(k for k in climate.KEYS if k in catalog['metrics'])
    expected.update(k for k in coast.KEYS if k in catalog['metrics'] and str(catalog['metrics'][k]['meta']['year'])==coast.LABELS[k])
    expected.update(k for k in bathing.KEYS if k in catalog['metrics'])
    expected.update(k for k in maritime.KEYS if k in catalog['metrics'])
    expected.update(k for k in pab.KEYS if k in catalog['metrics'])
    expected.update(k for k in remediation.KEYS if k in catalog['metrics'])
    expected.update(k for k in extractive.KEYS if k in catalog['metrics'])
    import semantic_query_fragility_adapters as fragility
    for k in fragility.KEYS:
        if k in catalog['metrics']:
            try:fragility.context(catalog['metrics'][k],k,'total');expected.add(k)
            except ValueError:pass
    import semantic_query_hazard_adapters as hazard
    expected.update(k for k in hazard.KEYS if k in catalog['metrics'] and all('populationBase' in r for r in catalog['metrics'][k]['rows']))
    import semantic_query_territory_adapters as territory
    expected.update(k for k in territory.KEYS if k in catalog['metrics'] and str(catalog['metrics'][k]['meta']['year'])==territory.LABELS[k])
    import semantic_query_soil_adapters as soil
    expected.update(k for k in soil.KEYS if k in catalog["metrics"] and all(isinstance(r.get("coverSeries" if k=="landCoverProfile" else "seriesByView"),dict) for r in catalog["metrics"][k]["rows"]))
    import semantic_query_geography_adapters as geography
    expected.update(k for k in geography.KEYS if k in catalog["metrics"])
    import semantic_query_agriculture_adapters as agriculture
    expected.update(k for k in agriculture.KEYS if k in catalog["metrics"])
    import semantic_query_environment_adapters as environment
    expected.update(k for k in environment.KEYS if k in catalog["metrics"])
    import semantic_query_commuting_adapters as commuting
    expected.update(k for k in commuting.KEYS if k in catalog["metrics"])
    import semantic_query_demography_school_adapters as demography
    expected.update(k for k in demography.KEYS if k in catalog["metrics"])
    import semantic_query_tourism_adapters as tourism
    expected.update(k for k in tourism.KEYS if k in catalog["metrics"])
    import semantic_query_rgs_adapters as rgs
    expected.update(k for k in rgs.KEYS if k in catalog["metrics"])
    import semantic_query_mef_adapters as mef
    expected.update(k for k in mef.KEYS if k in catalog["metrics"])
    assert set(adapters)==expected
    assert all('reason' in r['engine'] for r in matrix if r['metric'] not in adapters)
    for key in adapters:
        dimensions=next(x for x in matrix if x['metric']==key)['engine']['dimensions']
        query=request('lookup' if key in water_quality.KEYS else 'compare',key,dimension=dimensions[0])
        if key in (*coast.KEYS,*bathing.KEYS,*maritime.KEYS) or key==extractive.KEYS[1]:
            rejected(engine,query,'partial_coverage_requires_opt_in')
            query['allowPartial']=True
        report=engine.query(query)
        assert report['status']=='computed',report
        assert report['coverage']['requested']==(70 if key in water_quality.KEYS else 7)
        if key in (*coast.KEYS,*bathing.KEYS,*maritime.KEYS):assert report['coverage']['usable']==4 and len(report['excluded'])==3
        if key in CENSUS:
            for year in ['2021','2023']:
                r=engine.query(request('weighted_ratio',key,periods=[year]))
                assert r['status']=='computed' and len(r['result']['geographies'])==7,r
        if key in CENSUS or key=='income':
            for scope in ['tuscany','italy']:
                r=engine.query(dict(request('benchmark_gap',key,towns=['046018']),benchmark=scope))
                assert r['status']=='computed',r
    print(f'A6.4 query audit {layer}: {len(matrix)} indicators, {len(adapters)} adapters; remaining exclusions explicit')


def main():
    regressions()
    ratio_regressions()
    age_anomaly_regressions()
    audit(ROOT/'data/site-data.json','source')
    if (ROOT/'dist/data/site-data.json').exists():
        audit(ROOT/'dist/data/site-data.json','effective')
    engine=QueryEngine(ROOT/'data/site-data.json')
    examples=json.loads((ROOT/'ci/semantic-query-examples.json').read_text())['examples']
    for example in examples:
        report=engine.query(example['query'])
        expected='not_computable' if example['id']=='associazione_periodi_correnti_rifiutata' else 'computed'
        assert report['status']==expected,(example['id'],report)
    print('A6.4 deterministic query engine regression PASS')


if __name__=='__main__':
    main()
