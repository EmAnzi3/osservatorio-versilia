"""Independent frozen-input checks for the review-only work/income composition."""
import argparse
import copy
import json
import math
from pathlib import Path

from a7_work_income_reading import ROOT, build, validate, focus, rows, chapters, chart, digest


def verify_work_artifacts(bundle, folder, release):
    import hashlib
    import fitz
    from a7_work_income_reading import write_reports, number
    from a7_public_release import WORK_PDF_FILES
    import tempfile
    model=json.loads((folder/'work.json').read_text())
    validate(model)
    question=next(q for q in bundle['questions'] if q['id']=='lavoro-centrale')
    assert model['requiredCaseRefs']==question['requiredCaseRefs']+question['contextCaseRefs']
    assert model['incomePlanCoverage']['notComposed']==['mef_pensionIncomeShare_history']
    assert len(model['evidence'])==21 and len(model['townReadings'])==7
    assert model['repositoryCommit']==release['repositoryCommit']
    assert model['bundleSha256']==release['bundleSha256']
    for code,filename in WORK_PDF_FILES.items():
        view=model['townReadings'][code]
        assert view['chapters']==[dict(id=k,title=t,html=h) for k,t,h in chapters(model,code)]
        assert view['focusCode']==code and view['territory']==model['towns'][code]
        pdf=(folder/filename).read_bytes()
        assert hashlib.sha256(pdf).hexdigest()==release['workPdfs'][code]['sha256']
        doc=fitz.open(stream=pdf,filetype='pdf')
        assert len(doc)==6
        text=''.join(page.get_text() for page in doc)
        assert model['towns'][code] in text and model['repositoryCommit'] in text
        assert 'non esaurisce il dossier' in text
        for cid,decimals in [('census_employment_primary',1),('business_asia_cumulative',1),('business_asia_employment',2),('business_frame_industry_va',2),('business_frame_industry_wages',0),('mef_incomeSourceProfile_total',0)]:
            assert number(focus(model,cid,code)['value'],decimals) in text
        for o in rows(model,'business_frame_services_history',code):assert number(o['value'],2) in text
        for o in rows(model,'real_income_total_series_046018',code):assert number(o['value'])+'%' in text
        for page in doc:
            assert 'Pagina' in page.get_text() and 'osservatorioversilia.it' in page.get_text()
            for word in page.get_text('words'):
                assert word[0]>=0 and word[1]>=0 and word[2]<=page.rect.width and word[3]<=page.rect.height
        doc.close()
    with tempfile.TemporaryDirectory(prefix='work-pdf-replay-') as tmp:
        write_reports(model, tmp, WORK_PDF_FILES)
        for filename in WORK_PDF_FILES.values():assert (Path(tmp)/filename).read_bytes()==(folder/filename).read_bytes()


def verify_work_browser(page,bundle,folder,output,width):
    import hashlib
    model=json.loads((folder/'work.json').read_text())
    assert page.locator('#comune-lavoro option').count()==8
    assert page.locator('[data-work-pdf]').is_visible()
    page.locator('.edu-navigation a[data-chapter="redditi"]').click()
    assert page.locator('#lavoro-redditi [data-work-income-context]').is_hidden()
    assert page.locator('#lavoro-redditi svg').is_hidden()
    page.locator('#lavoro-redditi [data-work-income-accept]').click()
    assert page.locator('#lavoro-redditi [data-work-income-context]').is_visible()
    for code,view in model['townReadings'].items():
        page.select_option('#comune-lavoro',code)
        assert page.locator('#comune-lavoro').input_value()==code
        assert view['territory'].upper() in page.locator('#risposta .edu-kicker').inner_text()
        assert page.locator('.edu-navigation a').count()==6
        for chapter in view['chapters']:
            page.locator('.edu-navigation a[data-chapter="'+chapter['id']+'"]').click()
            panel=page.locator('#lavoro-'+chapter['id'])
            assert panel.is_visible() and page.locator('.edu-panel:visible').count()==1
            assert panel.locator('.work-content').evaluate('(e,html)=>{const d=document.createElement("div");d.innerHTML=html;return e.innerHTML===d.innerHTML;}',chapter['html'])
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            for figure in panel.locator('figure[data-work-case]').all():
                cid=figure.get_attribute('data-work-case');observations=rows(model,cid)
                expected={o['geography']:o['value'] for o in observations}
                signed=any(v<0 for v in expected.values() if v is not None)
                maximum=100 if cid=='census_employment_primary' else max([abs(v) for v in expected.values() if v is not None]+[1])
                assert figure.locator('li').count()==7
                assert figure.locator('li.focus').get_attribute('data-geography')==code
                for row in figure.locator('li').all():
                    value=expected[row.get_attribute('data-geography')]
                    if value is None:assert row.locator('.bar').count()==0;continue
                    # CSSOM serializes percentages with fewer decimals (49.03715260%
                    # becomes 49.0372%). Check the authored value without that
                    # conversion, then the actual layout within one 1/64px unit.
                    bar=row.locator('.bar').evaluate('''(e)=>({value:Number(e.dataset.value),width:Number(e.getAttribute("style").match(/width:([0-9.]+)%/)[1]),left:Number(e.getAttribute("style").match(/left:([0-9.]+)%/)[1]),renderedWidth:e.getBoundingClientRect().width,trackWidth:e.parentElement.getBoundingClientRect().width})''')
                    assert bar['value']==value
                    extent=(50 if signed else 100)*abs(value)/maximum
                    assert math.isclose(bar['width'],extent,abs_tol=.00001)
                    assert math.isclose(bar['left'],(50-extent if value<0 else 50) if signed else 0,abs_tol=.00001)
                    assert math.isclose(bar['renderedWidth'],bar['trackWidth']*extent/100,abs_tol=.02)
            if chapter['id']=='attivita':
                negative=panel.locator('.bar.negative')
                assert negative.count()==1 and float(negative.get_attribute('data-value'))<0
            if chapter['id']=='redditi':assert panel.locator('svg circle').count()==9
            if code in ('046018','046030'):page.screenshot(path=str(Path(output)/f'work-{code}-{chapter["id"]}-{width}.png'),full_page=True)
        with page.expect_download() as got:page.locator('[data-work-pdf]').click()
        downloaded=Path(got.value.path()).read_bytes()
        assert downloaded==(folder/f'work-{code}.pdf').read_bytes()
        assert hashlib.sha256(downloaded).hexdigest()==json.loads((folder/'release.mjs').read_text().removeprefix('export default ').strip().removesuffix(';'))['workPdfs'][code]['sha256']
    page.select_option('#comune-lavoro','046018')
    page.locator('.edu-navigation a[data-chapter="sintesi"]').click()


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
