#!/usr/bin/env python3
"""Real browser acceptance of the isolated preview using the original A7 reader."""
import functools
import hashlib
import http.server
import json
import tempfile
import threading
from pathlib import Path
from build_a7_dossier_preview import preview


def verify_preview(bundle, release, output):
    from playwright.sync_api import sync_playwright
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','questions':[], 'viewports':[], 'checks':[]}
    with tempfile.TemporaryDirectory(prefix='a7-preview-') as tmp:
        folder=Path(tmp)
        # Main source/dossier links point to the integrated, byte-identical evidence
        # baseline, independent of a local commit's metadata/history.
        preview(folder,'ae1249784c6e3ba25a99da52cc35780049a88380',bundle=bundle,release=release)
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=tmp))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}/'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                try:
                    for width,height in [(1280,900),(390,844)]:
                        page=browser.new_page(viewport={'width':width,'height':height})
                        errors=[];external=[]
                        page.on('pageerror',lambda error:errors.append(str(error)))
                        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(url) else (external.append(route.request.url),route.abort())[-1])
                        page.goto(url);page.locator('#mostra:enabled').wait_for()
                        for q in bundle['questions']:
                            page.select_option('#dossier',q['dossierId']);page.select_option('#domanda',q['id'])
                            page.locator('#mostra').focus();page.keyboard.press('Enter')
                            ids=q['requiredCaseRefs']+q['contextCaseRefs']
                            partial=any(bundle['cases'][cid]['query'].get('allowPartial') or 'partial_coverage_requires_opt_in' in bundle['cases'][cid]['response']['reasons'] for cid in ids)
                            if partial:
                                assert page.locator('#consenso').is_visible()
                                assert page.locator('#risposta').is_hidden()
                                assert page.locator('#risposta').inner_text()==''
                                page.locator('#annulla').click();assert page.locator('#consenso').is_hidden()
                                page.locator('#mostra').click();page.locator('#accetta').click()
                            assert page.locator('#risposta h2').inner_text()==q['question']
                            assert page.locator('.badge').inner_text()=='Risposta parzialmente supportata'
                            text=page.locator('#risposta').inner_text()
                            for cid in ids:
                                for fact in bundle['cases'][cid]['facts']:
                                    assert fact['text'] in text, 'fact not faithfully shown'
                                    assert cid+fact['responsePointer'] in text
                            assert q['answerBoundary'] in text and q['interpretationLimit'] in text
                            for gap in q['missingData']:assert gap in text
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'horizontal overflow'
                            links=page.locator('#risposta a').evaluate_all('(links)=>links.map(a=>a.href)')
                            assert links and all(link.startswith('https://github.com/EmAnzi3/osservatorio-versilia/blob/ae1249784c6e3ba25a99da52cc35780049a88380/') for link in links)
                            page.locator('#risposta details').filter(has=page.locator('pre')).first.locator('summary').click()
                            assert page.locator('#risposta details pre').first.is_visible()
                            report['questions'].append({'questionId':q['id'],'width':width,'status':'PASS'})
                        # Consent is scoped to the selection, not remembered globally.
                        page.select_option('#dossier','infanzia');page.select_option('#domanda','infanzia-2');page.locator('#mostra').click()
                        assert page.locator('#consenso').is_visible()
                        page.select_option('#dossier','lavoro');assert page.locator('#consenso').is_hidden() and page.locator('#risposta').is_hidden()
                        assert page.evaluate('localStorage.length === 0 && sessionStorage.length === 0')
                        assert not errors and not external,(errors,external)
                        page.select_option('#domanda','lavoro-1');page.locator('#mostra').click()
                        page.screenshot(path=str(output/f'preview-{width}.png'),full_page=True)
                        report['viewports'].append({'width':width,'height':height,'overflow':False,'browserErrors':errors,'externalRequests':external})
                        page.close()
                    page=browser.new_page()
                    # Corruption must fail closed before a selection is enabled.
                    page.route('**/bundle.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
                    page.goto(url);page.wait_for_function("document.querySelector('#stato').textContent.includes('non verificabili')")
                    assert page.locator('#mostra').is_disabled() and page.locator('#risposta').is_hidden()
                    page.close();report['checks'].append('tampered_bundle_fail_closed')
                    # Trusted source text is still rendered as text, never as HTML.
                    altered=json.loads(json.dumps(bundle));altered['questions'][0]['question']='<img src=x onerror="window.injected=true">'
                    body=json.dumps(altered,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
                    trusted=dict(release,bundleSha256=hashlib.sha256(body.encode()).hexdigest(),bundleBytes=len(body.encode()))
                    preview(folder,'ae1249784c6e3ba25a99da52cc35780049a88380',bundle=altered,release=trusted)
                    page=browser.new_page();page.goto(url);page.locator('#mostra:enabled').wait_for();page.locator('#mostra').click()
                    assert page.locator('#risposta h2').inner_text()==altered['questions'][0]['question']
                    assert page.locator('img').count()==0 and page.evaluate('window.injected===undefined')
                    page.close();report['checks']+=['source_text_not_html','consent_resets_on_selection','no_question_storage','six_plans_same_values_sources_and_limits']
                    report['browser']=browser.version
                finally:browser.close()
        finally:server.shutdown();server.server_close();thread.join()
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
