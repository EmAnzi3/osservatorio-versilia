"""Independent frozen-input checks for the review-only work/income composition."""
import argparse
import copy
import json
import math
from pathlib import Path

from a7_work_income_reading import ROOT, build, validate, focus, rows, chapters, chart, digest


def verify(catalog):
    model=build(catalog)
    assert model==build(catalog),'nonreproducible_work_model'
    def read(name):return json.loads((ROOT/'data/source-snapshots'/name).read_text())
    census=read('istat-lavoro-istruzione-eta-genere-2024.json')
    asia={r['code']:r['asia'] for r in read('agid-asia-agcom-2026-08.json')['towns']}
    mef=read('mef-income-lotto-a-2024.json')
    manifest=read('economia-prodotta-frame-sbs-v134.json')
    records=[]
    for part in manifest['parts']:
        value=read(part)
        records.extend(dict(zip(value['columns'],r)) for r in value['rows'])
    endpoints=read('a3-mef-real-income-benchmark-2024.json')
    nic=read('nic-italia-2016-2024.json')
    for code,town in model['towns'].items():
        def observed(cid):return focus(model,cid,code)['value']
        native=census['towns'][town]['labour']['25-64']['total']
        assert observed('census_employment_primary')==round(native['employed']/native['population']*100,1)
        a=asia[code]
        assert a['years'][0]==2018 and a['years'][-1]==2023
        assert math.isclose(observed('business_asia_cumulative'),(a['localUnits'][-1]/a['localUnits'][0]-1)*100,abs_tol=1e-10)
        assert observed('business_asia_employment')==a['employeesAverageAnnual'][-1]
        industry=next(r for r in records if r['year']==2023 and r['scope']=='industry' and r['code']==code)
        assert math.isclose(observed('business_frame_industry_va'),industry['valueAddedThousandEuro']/1000,abs_tol=1e-10)
        assert math.isclose(observed('business_frame_industry_wages'),industry['averageGrossRemunerationPerEmployeeThousandEuro']*1000,abs_tol=1e-8)
        s=mef['towns'][town]
        employment=next(x for x in s['incomeSources'] if x['key']=='employment')
        assert math.isclose(observed('mef_incomeSourceProfile_total'),employment['amountEuro']/employment['frequency'],abs_tol=1e-8)
        frequencies=[r['frequency'] for r in s['incomeBands']]
        known=sum(v for v in frequencies if v is not None)
        numerator=sum(v for v in frequencies[:3] if v is not None)
        assert math.isclose(observed('mef_incomeDistribution_total'),numerator/known*100,abs_tol=1e-10)
        distribution=focus(model,'mef_incomeDistribution_total',code)
        assert distribution['numerator']==numerator and distribution['denominator']==known
        coverage=next(e['bandCoverage'] for e in distribution['evidence'] if 'bandCoverage' in e)
        assert coverage['missingBandFrequencyCells']==sum(v is None for v in frequencies)
        services=rows(model,'business_frame_services_history',code)
        for o in services:
            raw=next(r for r in records if str(r['year'])==o['period'] and r['scope']=='services' and r['code']==code)
            assert math.isclose(o['value'],raw['valueAddedThousandEuro']/1000,abs_tol=1e-8)
        result=model['evidence']['business_frame_services_history:'+code]['response']['result']['value']
        assert math.isclose(result,services[-1]['value']-services[0]['value'],abs_tol=1e-8)
        real=rows(model,'real_income_total_series_046018',code)
        assert [o['period'] for o in real]==[str(y) for y in nic['years']]
        assert real[0]['value']==0
        native_endpoints=endpoints['municipalReconciliation'][code]
        expected=(native_endpoints['2024']['averageEuro']/native_endpoints['2016']['averageEuro']/(nic['comparisonIndex'][-1]/100)-1)*100
        assert math.isclose(real[-1]['value'],expected,abs_tol=.00011)
        text=''.join(body for _,_,body in chapters(model,code))
        assert town in text and 'non dimostrano' in text
        assert 'non il PIL comunale' in text and 'non reddito disponibile familiare' in text
        assert 'Non è una stima della povertà' in text
    # Preserve the negative ASIA observation; never force a positive bar width
    # by erasing its sign or narrating all municipalities as growing.
    signed=chart(model,'business_asia_cumulative','046030','Title','Scope','%')
    assert 'negative' in signed and 'diminuite' in chapters(model,'046030')[0][2]
    assert 'aumentate' in chapters(model,'046018')[0][2]
    for mutate in [lambda m:m['evidence']['census_employment_primary']['response']['observations'][0].update(value=0),
                   lambda m:m['evidence']['mef_incomeDistribution_total']['response']['observations'][0].update(denominator=0)]:
        changed=copy.deepcopy(model);mutate(changed)
        try:validate(changed)
        except ValueError as e:assert str(e)=='work_evidence_integrity_mismatch'
        else:raise AssertionError('altered_work_evidence_accepted')
    changed=copy.deepcopy(model);changed['evidence']['business_asia_cumulative']['response']['observations'].pop()
    changed['evidenceSha256']=digest(changed['evidence'])
    try:validate(changed)
    except ValueError as e:assert str(e).startswith('work_coverage_mismatch')
    else:raise AssertionError('partial_territory_set_accepted')
    changed=copy.deepcopy(model);changed['evidence']['business_asia_cumulative']['response']['observations'][0]['period']='2025'
    changed['evidenceSha256']=digest(changed['evidence'])
    try:validate(changed)
    except ValueError as e:assert str(e).startswith('work_incomparable_rows')
    else:raise AssertionError('mixed_periods_accepted')
    print(json.dumps(dict(status='PASS',requests=len(model['evidence']),towns=len(model['towns']),
        independentFrozenInputs=['employment','ASIA','Frame SBS','MEF','NIC'],scope='frozen inputs and original A6 verifier; intermediate real-income history is catalog replay, not native archive replay')))
    return model


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);a=p.parse_args();verify(a.catalog)
