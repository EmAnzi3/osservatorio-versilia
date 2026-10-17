"""Subchecks of the existing A7 Full gate, not a new release workflow."""
import copy
import hashlib
import json
from bs4 import BeautifulSoup
from a7_education_editorial import build_reading, write_report


def verify_education_artifacts(bundle, folder, release, output):
    model=json.loads((folder/'education.json').read_text())
    territorial=model['territorialCases']
    cases=dict(bundle['cases'],**territorial)
    assert model==build_reading(bundle,release['repositoryCommit'],territorial)
    from pathlib import Path
    from a7_education_editorial import NAMES
    root=Path(__file__).parents[1]
    raw=json.loads((root/'data/source-snapshots/lia-v1.4.0.json').read_text())['raw']['mim2024_25']
    buildings=json.loads((root/'data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json').read_text())['towns']
    # Independent source components, not the seven percentages printed by the UI.
    assert set(territorial)=={'school_students','school_class_size','school_full_time','school_access_defined'}
    for cid,case in territorial.items():
        assert set(case['query']['selectors'][0]['towns'])==set(NAMES)
        assert {o['geography'] for o in case['response']['observations']}==set(NAMES)
        assert len(case['response']['observations'])==7
        for o in case['response']['observations']:
            record=next(r for r in raw if r['code']==o['geography'])
            access=buildings[NAMES[o['geography']]]['accessibilita']
            expected_value={'school_students':record['students'],
                'school_class_size':record['students']/record['classes'],
                'school_full_time':record['full_time_students']/record['primary_students']*100,
                'school_access_defined':access.get('SI',0)/(access.get('SI',0)+access.get('NO',0))*100}[cid]
            assert abs(o['value']-expected_value)<1e-10
        for o in bundle['cases'][cid]['response']['observations']:
            assert next(r for r in case['response']['observations'] if r['geography']==o['geography'])==o
    # Independent frozen anchors already justified in the A6 cases/references;
    # these are regression expectations, not the values used for rendering.
    expected={'child_weighted':29.292929292929294,'school_students':1282,
              'school_class_size':17.805555555555557,'school_full_time':55.287817938420346,
              'school_access_defined':100.0,'invalsi_invalsiImplicitDispersion_g8_current':14.4444}
    for cid,value in expected.items():
        f=next(f for f in bundle['cases'][cid]['facts'] if f.get('geography')=='046018')
        assert abs(f['value']-value)<1e-10
    doc=BeautifulSoup(model['overview']+''.join(c['html'] for c in model['chapters']),'html.parser')
    for el in doc.select('[data-evidence-case]'):
        case=cases[el['data-evidence-case']]
        fact=next(f for f in case['facts'] if f['responsePointer']==el['data-evidence-pointer'])
        bar=el.select_one('.edu-bar')
        if bar:assert float(bar['data-value'])==fact['value']
    for binding in model['bindings']:
        fact=next(f for f in cases[binding['caseId']]['facts'] if f['responsePointer']==binding['pointer'])
        assert fact['value']==binding['value']
    bad=copy.deepcopy(territorial)
    next(f for f in bad['school_full_time']['facts'] if f.get('geography')=='046018')['value']=40
    try:build_reading(bundle,release['repositoryCommit'],bad)
    except ValueError as e:assert 'narrative_needs_review' in str(e)
    else:raise AssertionError('stale narrative accepted')
    bad=copy.deepcopy(territorial)
    bad['school_full_time']['facts']=bad['school_full_time']['facts'][:2]
    try:build_reading(bundle,release['repositoryCommit'],bad)
    except ValueError as e:assert 'coverage_incomplete' in str(e)
    else:raise AssertionError('two-town editorial regression accepted')
    assert (folder/'education.pdf').read_bytes().startswith(b'%PDF-')
    from pypdf import PdfReader
    pdf=PdfReader(folder/'education.pdf')
    import unicodedata
    text=unicodedata.normalize('NFKC','\n'.join(page.extract_text() for page in pdf.pages))
    for term in ['29,3','55,3','1.282','46,5','Prima infanzia','Tempo e organizzazione','Spazi e accessibilità','Apprendimenti e giovani','Dalle evidenze alle scelte','Confine della domanda']:
        assert term in text, 'PDF missing '+term
    assert 6 <= len(pdf.pages) <= 9
    assert len(pdf.pages)==len([page for page in pdf.pages if len(page.extract_text())>150]), 'blank report page'
    # Same editorial HTML / data => reproducible PDF, not merely valid magic bytes.
    css=(__import__('pathlib').Path(__file__).parents[1]/'experiments/a7-dossier-preview/education.css').read_text()
    again=output/'education-reproduced.pdf';write_report(model,css,again)
    assert again.read_bytes()==(folder/'education.pdf').read_bytes(),'non-reproducible educational report'
    (output/'education-evidence.json').write_text(json.dumps(dict(status='PASS',anchors=expected,territorialObservationsReconciled=28,originalObservationsPreserved=8,reportSha256=hashlib.sha256(again.read_bytes()).hexdigest(),modelSha256=release['educationSha256'],caseRefs=model['requiredCaseRefs']),indent=2)+'\n')


def verify_education_browser(page,bundle,folder,output,width):
    model=json.loads((folder/'education.json').read_text())
    cases=dict(bundle['cases'],**model['territorialCases'])
    assert page.locator('.edu-navigation').is_visible()
    assert page.locator('.edu-panel:visible').count()==1
    assert page.locator('#educazione-sintesi').is_visible()
    assert page.locator('.edu-findings>div').count()==3
    assert page.locator('#risposta .edu-chart:visible').count()==1
    assert page.locator('#risposta a[href*="github.com"]:visible').count()==0
    assert not page.locator('#esporta-risposta').is_visible()
    for chapter in ['nidi','scuola','spazi','apprendimenti','decisioni','sintesi']:
        page.locator('.edu-navigation a[data-chapter="'+chapter+'"]').click()
        assert page.locator('.edu-panel:visible').count()==1
        assert page.locator('#educazione-'+chapter).is_visible()
        assert page.locator('.edu-navigation a[aria-current="page"]').get_attribute('data-chapter')==chapter
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        for chart in page.locator('.edu-panel:visible .edu-chart').all():
            cid=chart.get_attribute('data-education-case');canonical=[f for f in cases[cid]['facts'] if f['kind']=='observation']
            rows=chart.locator('.edu-bars li');assert rows.count()==len(canonical)
            assert rows.count()==7
            for row in rows.all():
                f=next(f for f in canonical if f['responsePointer']==row.get_attribute('data-evidence-pointer'))
                if f['value'] is None:
                    assert row.locator('.edu-bar').count()==0 and 'Non disponibile' in row.inner_text()
                else:
                    bar=row.locator('.edu-bar');assert float(bar.get_attribute('data-value'))==f['value']
                    maximum=float(bar.get_attribute('data-maximum'))
                    actual=bar.evaluate('(e)=>parseFloat(e.style.width)');assert abs(actual-100*f['value']/maximum)<0.001  # CSSOM rounds serialized percentages; data-value remains exact
        page.screenshot(path=str(output/f'education-{chapter}-{width}.png'),full_page=True)
    page.locator('.edu-tools a').nth(1).click();assert page.locator('#educazione-nidi').is_visible()
    page.locator('.edu-navigation a[data-chapter="sintesi"]').click()
    with page.expect_download() as got:page.locator('[data-education-pdf]').click()
    assert __import__('pathlib').Path(got.value.path()).read_bytes()==(folder/'education.pdf').read_bytes()
    assert got.value.suggested_filename=='Massarosa-offerta-educativa.pdf'
