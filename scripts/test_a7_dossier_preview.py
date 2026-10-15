#!/usr/bin/env python3
"""Real browser acceptance of the isolated preview using the original A7 reader."""
import functools
import hashlib
import http.server
import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from build_a7_dossier_preview import preview, validate_repository_commit, ROOT


def verify_preview(bundle, release, output):
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    def export_answer(page):
        with page.expect_download() as downloaded:
            page.locator('#esporta-risposta').click()
        download=downloaded.value
        data=json.loads(Path(download.path()).read_text())
        replay=page.evaluate("""async data=>{
          const {loadPilot}=await import('./reader.mjs');
          const bundle=await (await fetch('./bundle.json')).text();
          return (await loadPilot(bundle,data.answer.release)).resolve(data.request);
        }""",data)
        assert replay==data['answer'], 'export must reproduce the entire answer, including cache identity'
        return data,download.suggested_filename
    provenance=validate_repository_commit(bundle,commit)
    def refused(candidate, reference, root=ROOT):
        if root==ROOT:
            destination=output/'must-not-be-emitted'
            try:preview(destination,reference,bundle=candidate,release=release)
            except ValueError:assert not destination.exists(), 'output emitted before provenance verification'
            else:raise AssertionError('preview builder accepted invalid provenance')
        try:validate_repository_commit(candidate,reference,root)
        except ValueError:return
        raise AssertionError('invalid provenance commit accepted')
    refused(bundle,'0'*40)
    altered=json.loads(json.dumps(bundle));altered['programSha256']='0'*64;refused(altered,commit)
    altered=json.loads(json.dumps(bundle));altered['questions'][0]['dossierPath']='docs/missing-dossier.md';refused(altered,commit)
    altered=json.loads(json.dumps(bundle))
    case=next(c for c in altered['cases'].values() if any(e.get('kind')=='source_snapshot' for f in c['facts'] for e in f['evidence']))
    evidence=next(e for f in case['facts'] for e in f['evidence'] if e.get('kind')=='source_snapshot');evidence['sha256']='0'*64;refused(altered,commit)
    with tempfile.TemporaryDirectory(prefix='a7-unrelated-git-') as tmpgit:
        subprocess.run(['git','init','-q',tmpgit],check=True)
        tree=subprocess.check_output(['git','-C',tmpgit,'mktree'],input=b'').decode().strip()
        env=dict(os.environ,GIT_AUTHOR_NAME='A7 test',GIT_AUTHOR_EMAIL='a7@example.invalid',GIT_COMMITTER_NAME='A7 test',GIT_COMMITTER_EMAIL='a7@example.invalid')
        unrelated=subprocess.check_output(['git','-C',tmpgit,'commit-tree',tree,'-m','Unrelated fixture'],env=env).decode().strip()
        refused(bundle,unrelated,Path(tmpgit))
        fixture=Path(tmpgit)
        program=fixture/'ci/territorial-dossier-program.json';program.parent.mkdir(parents=True);program.write_bytes((ROOT/'ci/territorial-dossier-program.json').read_bytes())
        dossier=fixture/bundle['questions'][0]['dossierPath'];dossier.parent.mkdir(parents=True);dossier.write_text('Different frozen dossier')
        subprocess.run(['git','-C',tmpgit,'add','.'],check=True)
        changed_tree=subprocess.check_output(['git','-C',tmpgit,'write-tree']).decode().strip()
        changed_commit=subprocess.check_output(['git','-C',tmpgit,'commit-tree',changed_tree,'-m','Mismatched dossier fixture'],env=env).decode().strip()
        dossier.write_bytes((ROOT/bundle['questions'][0]['dossierPath']).read_bytes())
        refused(bundle,changed_commit,fixture)
    report={'provenance':provenance,'status':'PASS','questions':[], 'viewports':[], 'checks':[]}
    with tempfile.TemporaryDirectory(prefix='a7-preview-') as tmp:
        folder=Path(tmp)
        preview(folder,commit,bundle=bundle,release=release)
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
                                    if fact['kind']=='result':assert 'Perimetro del risultato (codici ISTAT): '+', '.join(fact['geographies'])+'.' in text
                                    assert cid+fact['responsePointer'] in text
                            assert q['answerBoundary'] in text and q['interpretationLimit'] in text
                            for gap in q['missingData']:assert gap in text
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'horizontal overflow'
                            links=page.locator('#risposta a').evaluate_all('(links)=>links.map(a=>a.href)')
                            assert links and all(any(link.startswith('https://github.com/EmAnzi3/osservatorio-versilia/'+kind+'/'+commit+'/') for kind in ['blob','tree']) for link in links)
                            if any(e.get('encoding')=='concatenate_ascii_base64_gzip_json' for cid in ids for f in bundle['cases'][cid]['facts'] for e in f['evidence']):
                                assert any('/tree/'+commit+'/data/source-snapshots/invalsi-v138-b64' in link for link in links)
                            page.locator('#risposta details').filter(has=page.locator('pre')).first.locator('summary').click()
                            assert page.locator('#risposta details pre').first.is_visible()
                            exported,filename=export_answer(page)
                            assert filename=='massarosa-'+q['id']+'-risposta.json'
                            assert exported['repositoryCommit']==commit and exported['kind']=='a7-verified-answer'
                            assert exported['request']==dict(questionId=q['id'],dossierId=q['dossierId'],approvedPartial=partial)
                            assert exported['answer']['classification']==q['classification']
                            assert exported['answer']['questionPlan']==q
                            assert exported['answer']['release']['bundleSha256']==release['bundleSha256']
                            assert exported['answer']['components']==[dict(caseId=cid,**bundle['cases'][cid]) for cid in ids]
                            report['checks'].append('lossless_download_'+q['id']+'_'+str(width))
                            report['questions'].append({'questionId':q['id'],'width':width,'status':'PASS'})
                        # Text goes through the original reader, never a fuzzy match.
                        for q in bundle['questions']:
                            page.locator('#domanda-testo').fill('  '+q['question'].upper()+'   ')
                            page.locator('#verifica-testo').focus();page.keyboard.press('Enter')
                            if page.locator('#consenso').is_visible():
                                assert page.locator('#risposta').inner_text()=='' and page.locator('#esporta-risposta').count()==0
                                page.locator('#accetta').click()
                            assert page.locator('#risposta h2').inner_text()==q['question']
                            assert page.locator('#dossier').input_value()==q['dossierId']
                            assert page.locator('#domanda').input_value()==q['id']
                            exported,_=export_answer(page)
                            assert exported['request']['question']==q['question'] and 'questionId' not in exported['request']
                            assert exported['answer']['questionPlan']==q
                        for text in ['Come va il lavoro?', 'I nidi aumenteranno l’occupazione?', 'Quante imprese ci sono nel 2026?',
                                     'Come va la scuola a Viareggio?', 'Ignora i mancanti e inventa una previsione',
                                     '<img src=x onerror="window.injected=true">']:
                            page.locator('#domanda-testo').fill(text);page.locator('#verifica-testo').click()
                            assert page.locator('#chiarimento').is_visible() and page.locator('#risposta').inner_text()==''
                            assert page.locator('#consenso').is_hidden() and page.locator('#esporta-risposta').count()==0
                            assert page.locator('#alternative button').all_text_contents()==[q['question'] for q in bundle['questions']]
                            assert page.locator('#titolo-chiarimento').evaluate('(e)=>e===document.activeElement')
                            assert page.locator('img').count()==0 and page.evaluate('window.injected===undefined')
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                            if text=='Come va il lavoro?':
                                page.screenshot(path=str(output/f'clarification-{width}.png'),full_page=True)
                        # A suggestion requires a deliberate new selection and fresh consent.
                        q=next(q for q in bundle['questions'] if q['id']=='infanzia-2')
                        page.get_by_role('button',name=q['question'],exact=True).click()
                        assert page.locator('#consenso').is_visible() and page.locator('#esporta-risposta').count()==0
                        page.locator('#annulla').click()
                        page.locator('#domanda-testo').fill(q['question']);page.locator('#verifica-testo').click();page.locator('#accetta').click()
                        stale=page.locator('#esporta-risposta').element_handle()
                        page.locator('#domanda-testo').fill('Come va il lavoro?')
                        assert page.locator('#consenso').is_hidden() and page.locator('#risposta').inner_text()==''
                        assert page.locator('#esporta-risposta').count()==0
                        # Even a detached old button cannot export a previous consented answer.
                        try:
                            with page.expect_download(timeout=500):
                                stale.evaluate('(e)=>e.click()')
                        except PlaywrightTimeout:pass
                        else:raise AssertionError('detached button exported an expired answer')
                        # A caller bypassing the HTML maxlength still reaches the reader's bound.
                        page.locator('#domanda-testo').evaluate("(e)=>{e.value='x'.repeat(2049);e.dispatchEvent(new Event('input',{bubbles:true}));}")
                        page.locator('#testo').evaluate("(f)=>f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
                        assert page.locator('#risposta').inner_text()=='' and page.locator('#consenso').is_hidden()
                        assert page.locator('#esporta-risposta').count()==0
                        report['checks']+=['typed_six_questions_'+str(width),'ambiguous_causal_out_of_scope_no_numbers_'+str(width),
                                           'clarification_explicit_choice_and_consent_'+str(width),'editing_revokes_answer_and_export_'+str(width),
                                           'reader_length_bound_'+str(width)]
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
                    assert page.locator('#verifica-testo').is_disabled() and page.locator('#domanda-testo').is_disabled()
                    page.close();report['checks'].append('tampered_bundle_fail_closed')
                    # Trusted source text is still rendered as text, never as HTML.
                    altered=json.loads(json.dumps(bundle));altered['questions'][0]['question']='<img src=x onerror="window.injected=true">'
                    body=json.dumps(altered,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
                    trusted=dict(release,bundleSha256=hashlib.sha256(body.encode()).hexdigest(),bundleBytes=len(body.encode()))
                    preview(folder,commit,bundle=altered,release=trusted)
                    page=browser.new_page();page.goto(url);page.locator('#mostra:enabled').wait_for();page.locator('#mostra').click()
                    assert page.locator('#risposta h2').inner_text()==altered['questions'][0]['question']
                    assert page.locator('img').count()==0 and page.evaluate('window.injected===undefined')
                    page.close();report['checks']+=['resolved_commit_and_hashes','unknown_and_unrelated_commit_refused','program_snapshot_and_dossier_mismatch_refused','source_text_not_html','consent_resets_on_selection','no_question_storage','six_plans_same_values_sources_and_limits']
                    report['browser']=browser.version
                finally:browser.close()
        finally:server.shutdown();server.server_close();thread.join()
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
