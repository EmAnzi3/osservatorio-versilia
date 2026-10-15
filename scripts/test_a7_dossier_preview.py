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


def verify_public_page(bundle, release, dist, output):
    """Exercise the emitted public page and its shared runtime, not a mock shell."""
    from playwright.sync_api import sync_playwright
    from site_chrome import assert_navigation_contract
    from test_browser_quality_gate import wait_for_page
    from test_site_chrome_browser import open_page
    from bs4 import BeautifulSoup
    from a7_public_release import FILES, release_path
    dist=Path(dist);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    root=dist/'chiedi'
    document=BeautifulSoup((root/'index.html').read_text(),'html.parser')
    relative=release_path(str(document));folder=root/relative
    assert not any((root/name).exists() for name in FILES),'unversioned A7 assets emitted'
    assert document.select_one('script[src$="public.mjs"]')['src']==relative+'public.mjs'
    assert_navigation_contract(str(document.select_one('#site-header-mount')),str(document.select_one('#site-footer-mount')))
    assert document.select_one('link[rel="canonical"]')['href']=='https://osservatorioversilia.it/chiedi/'
    assert (dist/'sitemap.xml').read_text().count('https://osservatorioversilia.it/chiedi/')==1
    assert (folder/'bundle.json').read_bytes()==__import__('build_a7_static_pilot').encode(bundle).encode()
    assert (folder/'preview.mjs').read_bytes()==(ROOT/'experiments/a7-dossier-preview/preview.mjs').read_bytes()
    assert (folder/'reader.mjs').read_bytes()==(ROOT/'experiments/a7-static-pilot/reader.mjs').read_bytes()
    public_release=json.loads((folder/'release.mjs').read_text().removeprefix('export default ').strip().removesuffix(';'))
    assert all(public_release[k]==v for k,v in release.items())
    validate_repository_commit(bundle,public_release['repositoryCommit'])
    from validate_public_site import validate_a7
    asset_paths=['chiedi/index.html','chiedi/'+relative+'manifest.json']+['chiedi/'+relative+name for name in FILES]
    assets={path:(dist/path).read_text() for path in asset_paths}
    failures=[];validate_a7(assets.__getitem__,failures);assert not failures,failures
    for asset in ['chiedi/'+relative+name for name in (*FILES,'manifest.json')]:
        bad=dict(assets);bad[asset]+='altered'
        failures=[];validate_a7(bad.__getitem__,failures);assert failures,'public validator accepted corrupt '+asset
    missing=dict(assets);missing.pop('chiedi/'+relative+'public.css')
    failures=[];validate_a7(missing.__getitem__,failures);assert failures,'public validator accepted missing asset'
    overrides={};blocked=set()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def end_headers(self):
            if self.path.startswith('/chiedi/'):
                self.send_header('Cache-Control','max-age=3600')
            super().end_headers()
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if path in blocked:self.send_error(503);return
            if path in overrides:
                body=overrides[path].encode();self.send_response(200);self.send_header('Content-Type','text/html' if path.endswith('/') else self.guess_type(path));self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            else:super().do_GET()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(dist)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f'http://127.0.0.1:{server.server_port}/';report={'status':'PASS','viewports':[],'questions':[],'checks':[]}
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                for width,height in [(1280,900),(390,844)]:
                    page=browser.new_page(viewport={'width':width,'height':height});errors=[];external=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
                    page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else (external.append(route.request.url),route.abort())[-1])
                    open_page(page,origin,'chiedi/');wait_for_page(page);page.locator('#mostra:enabled').wait_for()
                    page.evaluate('scrollTo(0,0)')
                    assert page.locator('.site-header').is_visible() and page.locator('.site-footer').count()==1
                    page.locator('.global-search-trigger').click();page.locator('.search-overlay').wait_for()
                    page.keyboard.press('Escape');page.locator('.search-overlay').wait_for(state='hidden')
                    before=page.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])')
                    page.locator('#domanda-testo').fill('Come sta Massarosa?');page.locator('#verifica-testo').click()
                    assert page.locator('#chiarimento').is_visible() and page.locator('#risposta').is_hidden()
                    page.wait_for_function("() => {const r=document.querySelector('#titolo-chiarimento').getBoundingClientRect(),h=document.querySelector('.site-header').getBoundingClientRect();return r.top>=h.bottom && r.bottom<=innerHeight;}")
                    assert page.locator('#alternative button').count()==len(bundle['questions'])
                    for q in bundle['questions']:
                        page.locator('#domanda-testo').fill(q['question']);page.locator('#verifica-testo').click()
                        if page.locator('#consenso').is_visible():page.locator('#accetta').click()
                        assert page.locator('#risposta h2').inner_text()==q['question']
                        page.wait_for_function("() => {const r=document.querySelector('#risposta h2').getBoundingClientRect(),h=document.querySelector('.site-header').getBoundingClientRect();return r.top>=h.bottom && r.bottom<=innerHeight;}")
                        text=page.locator('#risposta').inner_text()
                        assert q['answerBoundary'] in text and q['interpretationLimit'] in text
                        for cid in q['requiredCaseRefs']+q['contextCaseRefs']:
                            for fact in bundle['cases'][cid]['facts']:assert fact['text'] in text
                        with page.expect_download() as got:page.locator('#esporta-risposta').click()
                        data=json.loads(Path(got.value.path()).read_text())
                        replay=page.evaluate('''async ({data,relative})=>{const {loadPilot}=await import('./'+relative+'reader.mjs');return(await loadPilot(await(await fetch('./'+relative+'bundle.json')).text(),data.answer.release)).resolve(data.request);}''',dict(data=data,relative=relative))
                        assert data['answer']==replay and data['repositoryCommit']==public_release['repositoryCommit']
                        assert data['answer']['components']==[dict(caseId=cid,**bundle['cases'][cid]) for cid in q['requiredCaseRefs']+q['contextCaseRefs']]
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'public page overflow'
                        report['questions'].append({'id':q['id'],'width':width,'status':'PASS'})
                    page.locator('#domanda-testo').fill('Quanti posti nido servono nel 2026?')
                    assert page.locator('#risposta').is_hidden() and page.locator('#esporta-risposta').count()==0
                    page.locator('#verifica-testo').click();assert page.locator('#chiarimento').is_visible()
                    assert page.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])')==before
                    assert not errors and not external,(errors,external)
                    wait_for_page(page)
                    page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_function('() => scrollY===0');page.screenshot(path=str(output/f'public-clarification-{width}.png'),full_page=True)
                    page.locator('#alternative button').first.click()
                    if page.locator('#consenso').is_visible():page.locator('#accetta').click()
                    wait_for_page(page)
                    page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_function('() => scrollY===0');page.screenshot(path=str(output/f'public-answer-{width}.png'),full_page=True)
                    report['viewports'].append({'width':width,'errors':errors,'externalRequests':external});page.close()
                for mode in ['unavailable','corrupt']:
                    page=browser.new_page()
                    # A worker may own this fetch before page-level routing.
                    # Alter the real HTTP response, not Playwright interception.
                    path='/chiedi/'+relative+'bundle.json'
                    if mode=='unavailable':blocked.add(path)
                    else:overrides[path]='{}'
                    page.goto(origin+'chiedi/');page.wait_for_function("() => document.querySelector('#stato').textContent.includes('non verificabili')")
                    assert page.locator('#mostra').is_disabled() and page.locator('#risposta').is_hidden()
                    page.locator('.global-search-trigger').click();page.locator('.search-overlay').wait_for()
                    page.close();overrides.clear();blocked.clear();report['checks'].append(mode+'_bundle_fail_closed_with_shell_available')
                page=browser.new_page(java_script_enabled=False);page.goto(origin+'chiedi/')
                assert page.locator('noscript a[href="'+relative+'answers.md"]').is_visible() and page.locator('#mostra').is_disabled()
                page.close();report['checks']+=['native_shell_search','twelve_lossless_public_exports','no_question_storage_or_external_request','no_javascript_text_fallback','same_original_reader_and_bundle']
                assert (dist/'service-worker.js').read_bytes()==(ROOT/'service-worker.js').read_bytes()
                context=browser.new_context()
                # Routing disables HTTP caching: exercise the actual HTTP cache.
                context.unroute('**/*')
                worker_external=[]
                context.on('request',lambda request:worker_external.append(request.url) if not request.url.startswith(origin) else None)
                page=context.new_page();page.goto(origin+'chiedi/')
                page.locator('#mostra:enabled').wait_for();page.wait_for_function('() => navigator.serviceWorker.controller !== null')
                # Real worker + HTTP fixture: old cached bytes must not win while online.
                for filename in ['bundle.json','release.mjs','reader.mjs','preview.mjs','public.mjs']:
                    url=relative+filename
                    page.evaluate('async url=>(await fetch(url)).text()',url)
                    marker='a7-fresh-network-'+filename;overrides['/chiedi/'+url]=marker
                    actual=page.evaluate('''async filename=>{
                        await fetch(filename);
                        const key=(await caches.keys()).find(k=>k.endsWith('-runtime'));
                        if(!key)throw new Error('runtime_cache_missing');
                        const cache=await caches.open(key);
                        await cache.put(new URL(filename,location.href),new Response('old-cached-evidence'));
                        return await(await fetch(filename)).text();
                    }''',url)
                    assert actual==marker,'A7 worker served stale online asset: '+filename+' '+repr(actual[:120])
                    overrides.clear()
                    assert page.evaluate('async url=>(await fetch(url)).text()',url)==(folder/filename).read_text()
                # The reader must reject mixed offline cache, never turn it into a result.
                page.evaluate('''async relative=>{
                    const keys=await caches.keys();
                    for(const key of keys.filter(k=>k.endsWith('-runtime'))){
                        const cache=await caches.open(key);await cache.put(new URL(relative+'bundle.json',location.href),new Response('{}'));
                    }
                }''',relative)
                context.set_offline(True)
                failure=page.evaluate('''async ({release,relative})=>{
                    const {loadPilot}=await import('./'+relative+'reader.mjs');
                    try{await loadPilot(await(await fetch('./'+relative+'bundle.json')).text(),release);return 'accepted';}
                    catch(error){return error.message;}
                }''',dict(release=public_release,relative=relative))
                assert failure=='bundle_integrity_mismatch',failure
                context.set_offline(False);assert not worker_external,worker_external;context.close()
                report['checks']+=['real_worker_five_assets_http_revalidation_and_network_first','http_cache_enabled_one_hour_ttl','mixed_offline_cache_refused','focused_headings_clear_of_sticky_header']
                # A cached old reader must not satisfy a missing module from a
                # different deployment. Only this HTTP fixture is incomplete;
                # candidate files and their immutable manifest stay untouched.
                context=browser.new_context();context.unroute('**/*');page=context.new_page()
                requested=[];context.on('request',lambda request:requested.append(request.url))
                page.goto(origin+'chiedi/');page.locator('#mostra:enabled').wait_for()
                page.wait_for_function('() => navigator.serviceWorker.controller !== null')
                for name in ['reader.mjs','preview.mjs','public.mjs','release.mjs','bundle.json']:
                    page.evaluate('async path=>(await fetch(path)).text()',relative+name)
                page.locator('#mostra').click()
                if page.locator('#consenso').is_visible():page.locator('#accetta').click()
                assert page.locator('#risposta').is_visible()
                next_relative='releases/'+hashlib.sha256((relative+'incomplete-next-release').encode()).hexdigest()+'/'
                overrides['/chiedi/']=(root/'index.html').read_text().replace(relative,next_relative)
                for name in FILES:
                    if name!='reader.mjs':overrides['/chiedi/'+next_relative+name]=(folder/name).read_text()
                blocked.add('/chiedi/'+next_relative+'reader.mjs')
                # Fresh next-release evidence is present, but its reader is not.
                assert page.evaluate('async path=>(await fetch(path)).text()',next_relative+'bundle.json')==(folder/'bundle.json').read_text()
                page.goto(origin+'chiedi/?a7-release-fixture=next')
                page.wait_for_function("() => document.querySelector('#stato').textContent.includes('non verificabili')")
                assert page.locator('#mostra').is_disabled() and page.locator('#verifica-testo').is_disabled()
                assert page.locator('#risposta').is_hidden() and page.locator('#risposta').inner_text()==''
                assert page.locator('#esporta-risposta').count()==0
                assert origin+'chiedi/'+next_relative+'reader.mjs' in requested
                old_reader=page.evaluate('''async path=>{const response=await caches.match(new URL(path,location.href));return response?await response.text():null;}''',relative+'reader.mjs')
                assert old_reader==(folder/'reader.mjs').read_text()
                assert all(url.startswith(origin) for url in requested),requested
                context.close();overrides.clear();blocked.clear()
                report['checks']+=['all_assets_bound_to_manifest_hash','old_cached_reader_not_used_for_new_release','partial_deployment_has_no_results']
                report['browser']=browser.version
            finally:browser.close()
    finally:server.shutdown();server.server_close();thread.join()
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
