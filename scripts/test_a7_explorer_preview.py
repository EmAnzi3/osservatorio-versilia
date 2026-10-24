#!/usr/bin/env python3
"""Exercise the guided preview through native controls, not a second UI engine."""
import functools
import gzip
from unittest.mock import patch
import http.server
import json
import threading
import tempfile
from pathlib import Path

from build_a7_explorer_preview import build


def verify_association_interface(catalog, runtime, expected, output, *, dist=None):
    """Same page and original requests; no fixture pair list in the UI."""
    import hashlib
    from playwright.sync_api import sync_playwright
    from a7_query_workbench import encode
    from a7_query_workbench import QueryWorkbench
    from build_a7_query_runtime import build as build_runtime
    from build_territorial_dossier_evidence import portable_evidence
    from semantic_question_suite import QUESTIONS, check_expected
    import copy
    output = Path(output)
    dist = Path(dist) if dist is not None else Path(catalog).resolve().parent.parent
    # Separate UI cases must not widen the original bounded-cache transport fixture.
    plan=copy.deepcopy(expected['plan'])
    hostile=copy.deepcopy(plan['steps'][0]['request'])
    hostile['purpose']='Verifica testuale <img src=x onerror="window.injected=true">'
    reverse=copy.deepcopy(plan['steps'][0]['request']);reverse['selectors'].reverse()
    plan['steps'] += [dict(id='textual-purpose',request=hostile),dict(id='reversed-pair',request=reverse)]
    temporal=next(c for c in json.loads(QUESTIONS.read_text())['questions'] if c['id']=='business_cumulative_correlation_refused')
    workbench=QueryWorkbench(catalog)
    assert not check_expected(workbench.engine.query(temporal['query']),temporal['expected'])
    plan['steps'].append(dict(id='period-axis-refusal',request=copy.deepcopy(temporal['query'])))
    metrics=sorted({s['metric'] for step in plan['steps'] for s in step['request']['selectors']
                    if s['metric'] in workbench.engine.catalog['metrics']})
    runtime=output/'ui-runtime'
    build_runtime(catalog,runtime,metrics=metrics,
                  max_views=1,profiles=('current',),association_plan=plan)
    expected=portable_evidence(workbench.run(plan))
    try:
        build(dist, runtime, output/'forbidden', public=True, associations=True)
    except ValueError as error:
        assert str(error) == 'association_interface_preview_only'
    else:
        raise AssertionError('association_preview_published_implicitly')
    assert not (output/'forbidden').exists()
    default = build(dist, runtime, output/'default')
    assert default['interfaceVersion'] == 6 and not any('associations.' in p for p in default['files'])
    receipt = build(dist, runtime, output/'guided', associations=True)
    assert receipt['interfaceVersion'] == 7 and receipt['associationInterface'] == 'explicit_plan_preview_only'
    assert any(p.endswith('associations.mjs') for p in receipt['files'])
    root = json.loads((Path(runtime)/'release.json').read_text())
    entries = root['associationPlan']['entries']
    requests = expected['plan']['steps']
    by_id = {s['id']:s['response'] for s in expected['steps']}
    def choose(page, index):
        step=requests[index];request=step['request']
        for name,value in [('left',encode(request['selectors'][0])),('right',encode(request['selectors'][1])),
                           ('axis',request.get('axis','')),('method',request.get('method','')),('scope',step['id'])]:
            page.select_option('#association-'+name,value=value)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(output)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                for width in (1440,390,320):
                    page=browser.new_page(viewport=dict(width=width,height=900))
                    fetched=[];page.on('request',lambda r:fetched.append(r.url) if r.url.endswith('.json.gz') else None)
                    page.goto(f'http://127.0.0.1:{server.server_port}/guided/chiedi/')
                    page.wait_for_selector('#association-run:enabled')
                    assert not fetched,'association_eager_response_fetch'
                    page.click('#association-mode-measure')
                    assert page.locator('#explorer-form').is_visible() and page.locator('#association-explorer').is_hidden()
                    assert page.locator('#explorer-form').count()==1
                    page.click('#association-mode-pair')
                    assert page.locator('#explorer-form').is_hidden() and page.locator('#association-explorer').is_visible()
                    for index,step in enumerate(requests):
                        choose(page,index);before=len(fetched);page.click('#association-run')
                        page.wait_for_selector('#association-result:not([hidden]), #association-consent:not([hidden])')
                        if page.locator('#association-consent').is_visible():
                            assert page.locator('#association-result').is_hidden()
                            assert page.locator('[data-association-value]').count()==0
                            page.click('#association-accept')
                        page.wait_for_selector('#association-result:not([hidden])')
                        original=json.loads(page.locator('[data-association-evidence]').text_content())
                        response=by_id[step['id']]
                        assert original['steps'][0]['response']==response
                        assert original['plan']['steps']==[step]
                        if response['status']=='computed':
                            assert float(page.locator('[data-association-value="coefficient"]').text_content().replace(',','.'))==response['result']['coefficient'],'association_coefficient_precision_changed'
                            assert page.locator('[data-association-value="coefficient"]').evaluate('cell=>{const r=document.createRange();r.selectNodeContents(cell);return r.getClientRects().length===1}'),'association_coefficient_split'
                            assert page.locator('#association-result svg').evaluate('svg=>Array.from(svg.querySelectorAll("text")).every(t=>{const b=t.getBBox(),v=svg.viewBox.baseVal;return b.x>=0&&b.y>=0&&b.x+b.width<=v.width&&b.y+b.height<=v.height})'),'association_chart_label_clipped'
                            assert page.locator('#association-result svg circle').count()==response['result']['n']
                            assert page.locator('#association-result tbody tr').count()==min(20,response['result']['n'])
                            if response['result']['n']>20:
                                page.click('#association-next')
                                assert page.locator('#association-result tbody tr').first.get_attribute('data-pair-key')==response['result']['pairs'][20]['key']
                                page.click('#association-previous')
                        else:
                            assert not page.locator('#association-result svg').count()
                            assert not page.locator('[data-association-value="coefficient"]').count()
                        assert not page.locator('#association-explorer img').count(),'association_untrusted_html'
                        if index==7:assert len(fetched)==before,'association_cached_selection_refetched'
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'association_page_overflow'
                    # A missing block fails closed and retry keeps the same anchored release.
                    page.reload();page.wait_for_selector('#association-run:enabled')
                    missing=entries[0]['artifact']['path']
                    page.route('**/'+missing,lambda route:route.fulfill(status=404,body='missing'))
                    choose(page,0);page.click('#association-run');page.wait_for_selector('#association-retry:not([hidden])')
                    assert page.locator('#association-result').is_hidden()
                    page.unroute('**/'+missing);page.click('#association-retry');page.wait_for_selector('#association-run:enabled')
                    choose(page,0);page.click('#association-run');page.wait_for_selector('[data-association-evidence]',state='attached')
                    assert json.loads(page.locator('[data-association-evidence]').text_content())['steps'][0]['response']==by_id[requests[0]['id']]
                    # Changing controls revokes a pending request before it can render.
                    page.reload();page.wait_for_selector('#association-run:enabled');held=[]
                    page.route('**/'+missing,lambda route:held.append(route))
                    choose(page,0)
                    with page.expect_request(lambda r:r.url.endswith(missing)):page.click('#association-run')
                    page.select_option('#association-method',value='pearson')
                    assert held
                    held[0].continue_();page.unroute('**/'+missing)
                    assert page.locator('#association-result').is_hidden()
                    page.click('#association-run');page.wait_for_selector('[data-association-evidence]',state='attached')
                    actual=json.loads(page.locator('[data-association-evidence]').text_content())
                    assert actual['steps'][0]['response']==by_id[requests[1]['id']]
                    results.append(dict(width=width,status='PASS',requests=len(requests),initialResponseFetches=0))
                    page.screenshot(path=str(output/f'association-{width}.png'),full_page=True)
                    page.close()
            finally:browser.close()
    finally:server.shutdown();server.server_close()
    return dict(status='PASS',browser=results,scope='explicit-plan isolated preview; no public association UI or general pair coverage claim')


def assert_readable_values(page, numeric_rows):
    """A value must remain one readable token, even inside a scrolling table."""
    assert page.evaluate('''rows => rows.every(index => {
      const cell=document.querySelectorAll('#explorer-result tbody tr')[index]?.querySelector('[data-observation-value]');
      const text=cell?.firstChild;
      if(!text || text.nodeType!==Node.TEXT_NODE)return false;
      const range=document.createRange();range.selectNodeContents(text);
      return range.getClientRects().length===1;
    })''', numeric_rows), 'explorer_numeric_value_split_across_lines'


def verify_explorer(catalog, runtime, output, samples):
    source_page = Path(catalog).resolve().parent.parent/'chiedi/index.html'
    from a7_explorer_release import validate_explorer
    canonical_dist = source_page.parent.parent
    read = lambda path: (canonical_dist/path).read_bytes()
    public = validate_explorer(read)
    assert public['status'] == 'PASS'
    descriptor = json.loads(read('explorer-preview.json'))
    prefix = 'chiedi/'+descriptor['graph']
    selected = ['explorer-preview.json', prefix+'entry.mjs',
                prefix+'package/runtime/'+descriptor['releaseSha256']+'/release.json']
    manifest = json.loads(read(selected[-1]))
    runtime_prefix = selected[-1].rsplit('/',1)[0]+'/'
    detail_path = runtime_prefix+manifest['metrics'][0]['detail']['path']
    detail = json.loads(gzip.decompress(read(detail_path)))
    shard = next(r for v in detail['views'] for r in v['shards'].values())
    selected += [detail_path, runtime_prefix+shard['path']]
    from materialize_a7_public_explorer import commit_site
    with tempfile.TemporaryDirectory(prefix='a7-build-rollback-') as temporary:
        root = Path(temporary);dist=root/'dist';site=root/'new';backup=root/'previous'
        dist.mkdir();site.mkdir();(dist/'index.html').write_bytes(b'previous site')
        (site/'index.html').write_bytes(b'complete new site')
        import os
        rename = os.rename
        def interrupted(source, destination):
            if source == site:
                raise OSError('simulated_final_commit_failure')
            return rename(source,destination)
        with patch('materialize_a7_public_explorer.os.rename',side_effect=interrupted):
            try:
                commit_site(dist,site,backup)
            except OSError:
                pass
            else:
                raise AssertionError('interrupted_public_commit_accepted')
        assert (dist/'index.html').read_bytes() == b'previous site'
        assert not backup.exists() and (site/'index.html').read_bytes() == b'complete new site'
    for target in selected:
        def corrupt(path):
            return b'corrupt' if path == target else read(path)
        try:
            validate_explorer(corrupt)
        except (ValueError, KeyError, TypeError):
            pass
        else:
            raise AssertionError('public_explorer_corruption_accepted:'+target)
    before = source_page.read_bytes()
    receipt = build(Path(catalog).resolve().parent.parent, runtime, output)
    assert not receipt['publicIntegration']
    from bs4 import BeautifulSoup
    embedded = BeautifulSoup((output/'chiedi/index.html').read_text(), 'html.parser')
    assert len(embedded.select('#a7-explorer')) == 1, 'duplicate_explorer_controls'
    assert {p.name for p in (output/'chiedi/explorer-preview').iterdir()} == {receipt['graph'].split('/')[1]}, 'mixed_explorer_graphs'
    assert 'assets/pwa.js' not in (output/'chiedi/index.html').read_text()
    assert source_page.read_bytes() == before, 'preview_changed_public_dist'
    try:
        build(Path(catalog).resolve().parent.parent, runtime, output)
        raise AssertionError('existing_preview_overwritten')
    except ValueError as error:
        assert str(error) == 'preview_output_already_exists'
    with tempfile.TemporaryDirectory(prefix='a7-preview-broken-') as temporary:
        broken = Path(temporary)/'runtime';broken.mkdir()
        (broken/'release.json').write_text('{}')
        target = Path(temporary)/'failed'
        try:
            build(Path(catalog).resolve().parent.parent, broken, target)
            raise AssertionError('invalid_graph_published_preview')
        except ValueError:
            assert not target.exists(), 'partial_preview_exposed'
        assert not list(target.parent.glob('.a7-preview-*'))
    assert source_page.read_bytes() == before
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(output)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    results = []
    # The production worker must not substitute cached bytes on failed graph
    # requests. Test a real controlled page and cache, with the network offline.
    def verify_worker(browser):
        context = browser.new_context(service_workers='allow')
        page = context.new_page()
        base = f'http://127.0.0.1:{server.server_port}/'
        # output is an isolated preview, whose worker bytes are those from the
        # canonical dist. Explicit registration is QA only, never preview code.
        page.goto(base+'chiedi/')
        page.evaluate('''async () => {
          await navigator.serviceWorker.register('../service-worker.js',{scope:'../'});
          await navigator.serviceWorker.ready;
        }''')
        page.wait_for_function('()=>Boolean(navigator.serviceWorker.controller)')
        url = base+'chiedi/'+receipt['graph']+'entry.mjs'
        page.evaluate('''async url => {
          const response=await fetch(url,{cache:'no-store'});
          if(!response.ok)throw Error('missing_worker_test_resource');
          const names=(await caches.keys()).filter(k=>k.startsWith('ov-pwa-')&&k.endsWith('-runtime'));
          names.push('ov-pwa-explorer-test-runtime');
          for(const name of names){const cache=await caches.open(name);await cache.put(url,response.clone());}
        }''',url)
        context.set_offline(True)
        failed = page.evaluate('''async url => {try {await fetch(url);return false;}catch{return true;}}''',url)
        assert failed, 'worker_returned_cached_explorer_graph_offline'
        context.set_offline(False)
        assert page.evaluate('''async url => (await fetch(url)).ok''',url)
        context.close()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                verify_worker(browser)
                for width in (1440, 390):
                    context = browser.new_context(viewport=dict(width=width, height=1000), service_workers='block')
                    page = context.new_page()
                    errors = []; outside = []; fetched = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.on('request', lambda req: outside.append(req.url) if not req.url.startswith(f'http://127.0.0.1:{server.server_port}/') else fetched.append(req.url))
                    page.goto(f'http://127.0.0.1:{server.server_port}/chiedi/')
                    page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    assert not any(url.endswith('.json.gz') for url in fetched), 'eager_explorer_shards'
                    root = json.loads((Path(runtime)/'release.json').read_text())
                    summaries = {m['metric']:m for m in root['metrics']}
                    details = {m['metric']:json.loads(gzip.decompress((Path(runtime)/m['detail']['path']).read_bytes())) for m in root['metrics']}

                    def select(entry):
                        request = entry['request']; selector = request['selectors'][0]
                        page.select_option('#explorer-theme', summaries[selector['metric']]['theme'])
                        page.select_option('#explorer-metric', selector['metric'])
                        page.wait_for_function("()=>document.querySelector('#explorer-view').options.length>0")
                        page.select_option('#explorer-view', selector['dimension'])
                        trend_option = page.locator('#explorer-operation option[value=trend]')
                        selected_view = next(v for v in details[selector['metric']]['views'] if v['dimension'] == selector['dimension'])
                        if trend_option.count():
                            assert trend_option.evaluate('(option) => !option.disabled') == ('trends' in selected_view['shards']), 'trend_ui_scope_mismatch'
                        page.select_option('#explorer-operation', request['operation'])
                        if request['operation'] == 'benchmark_gap':
                            assert page.is_visible('#explorer-benchmark')
                            assert page.is_disabled('#explorer-run'), 'benchmark_reference_was_implicit'
                            page.select_option('#explorer-benchmark', request['benchmark'])
                        else:
                            assert not page.is_visible('#explorer-benchmark')
                        if request['operation'] in ('weighted_ratio','rank'):
                            assert not page.is_visible('#explorer-town-field')
                            assert page.is_disabled('#explorer-town')
                            assert 'tutti i sette Comuni' in page.locator('#explorer-reference').text_content()
                            if request['operation'] == 'rank':
                                assert 'dal valore maggiore al minore' in page.locator('#explorer-reference').text_content()
                        else:
                            assert page.is_visible('#explorer-town-field')
                        if len(selector['towns']) == 1:
                            page.select_option('#explorer-town', selector['towns'][0])
                        if request['operation'] in ('absolute_change','relative_change','percentage_points'):
                            for period in selector.get('periods', []):
                                assert str(period) in page.locator('#explorer-reference').text_content(), 'change_period_not_shown_before_execution'
                        if request['operation'] == 'trend':
                            assert 'intera serie nativa' in page.locator('#explorer-reference').text_content()
                            assert 'Nessuna previsione' in page.locator('#explorer-reference').text_content()
                        assert not page.is_visible('#explorer-result')

                    partial = None; checked = 0; categories = 0; benchmarks = 0; benchmark_refusals = 0
                    aggregations = 0; aggregation_refusals = 0; changes = {}; change_refusals = 0
                    rankings = 0; ranking_refusals = 0; ranking_ties = 0
                    trends = 0; trend_refusals = 0; trend_signs = set(); trend_units = set(); trend_pages = 0
                    for entry in samples:
                        select(entry)
                        page.click('#explorer-run')
                        page.wait_for_function("()=>!document.querySelector('#explorer-consent').hidden || !document.querySelector('#explorer-result').hidden")
                        if page.is_visible('#explorer-consent'):
                            assert not page.is_visible('#explorer-result')
                            partial = entry
                            if entry['request']['operation'] == 'benchmark_gap':
                                page.select_option('#explorer-benchmark', '')
                                assert not page.is_visible('#explorer-consent'), 'reference_retained_partial_consent'
                                page.select_option('#explorer-benchmark', entry['request']['benchmark'])
                                page.click('#explorer-run')
                                page.wait_for_selector('#explorer-consent:not([hidden])')
                            if entry['request']['operation'] == 'weighted_ratio':
                                page.select_option('#explorer-operation', 'observe')
                                assert not page.is_visible('#explorer-consent') and not page.is_visible('#explorer-result')
                                assert page.is_visible('#explorer-town-field')
                                page.select_option('#explorer-operation', 'weighted_ratio')
                                page.click('#explorer-run')
                                page.wait_for_selector('#explorer-consent:not([hidden])')
                            if entry['request']['operation'] == 'trend':
                                town = entry['request']['selectors'][0]['towns'][0]
                                page.select_option('#explorer-town',next(t['code'] for t in root['towns'] if t['code'] != town))
                                assert not page.is_visible('#explorer-consent') and not page.is_visible('#explorer-result'), 'trend_consent_survived_selection'
                                page.select_option('#explorer-town',town);page.click('#explorer-run')
                                page.wait_for_selector('#explorer-consent:not([hidden])')
                            page.click('#explorer-accept')
                        page.wait_for_selector('#explorer-result:not([hidden])')
                        evidence = json.loads(page.locator('[data-explorer-evidence]').text_content())
                        assert evidence['steps'][0]['response'] == entry['response'], 'ui_changed_native_response'
                        assert evidence['plan']['steps'][0]['request'] == entry['request'], 'ui_changed_selection'
                        op = entry['request']['operation']
                        if op == 'rank':
                            response = entry['response']; native = response.get('result')
                            if response['status'] == 'computed':
                                rankings += 1
                                assert page.locator('.explorer-ranking').count() == 1
                                rows = page.locator('#explorer-result tbody tr')
                                assert rows.count() == len(native['ranking'])
                                for index, item in enumerate(native['ranking']):
                                    row = rows.nth(index)
                                    assert row.get_attribute('data-ranking-geography') == item['geography']
                                    assert row.locator('[data-native-rank]').text_content() == str(item['rank'])
                                    expected = page.evaluate("text=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:15}).format(JSON.parse(text))",json.dumps(item['value']))
                                    assert row.locator('[data-observation-value]').text_content().startswith(expected)
                                    observation = next(o for o in response['observations'] if o['geography']==item['geography'])
                                    assert row.locator('td').nth(2).text_content() == str(observation['period'])
                                import re
                                assert not re.search(r'\b(count|meters|hectares|currency2|cubicMetres|eurliter|eurm2month|per10k|celsius)\b',
                                    ' '.join(rows.locator('[data-observation-value]').all_text_contents())), 'technical_unit_token_in_public_values'
                                chart = page.locator('.explorer-bar-row[data-ranking-geography]')
                                if chart.count():
                                    assert chart.evaluate_all("els=>els.map(e=>e.dataset.rankingGeography)") == [r['geography'] for r in native['ranking']]
                                ranking_ties += len({r['rank'] for r in native['ranking']}) < len(native['ranking'])
                            else:
                                ranking_refusals += 1
                                assert not page.locator('.explorer-ranking, [data-native-rank], .explorer-bar-row').count(), 'refusal_promoted_to_order'
                                assert 'Nessuna posizione numerica viene assegnata' in page.locator('#explorer-result').text_content()
                        if op == 'trend':
                            response = entry['response']; native = response.get('result'); shown = page.locator('.explorer-trend')
                            if response['status'] == 'computed':
                                trends += 1; trend_signs.add(native['slope'] > 0); trend_units.add(native['unit'])
                                assert shown.count() == 1
                                expected = page.evaluate("text=>{const x=JSON.parse(text);return new Intl.NumberFormat('it-IT',x!==0&&Math.abs(x)<.01?{maximumSignificantDigits:3}:{maximumFractionDigits:2}).format(x)}",json.dumps(native['slope']))
                                assert expected in shown.locator('[data-trend-value=slope]').text_content()
                                original = page.evaluate("text=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:21}).format(JSON.parse(text))",json.dumps(native['slope']))
                                assert original in shown.locator('[data-trend-original]').text_content(), 'trend_original_precision_lost'
                                method = shown.locator('details');method.locator('summary').click()
                                assert shown.locator('[data-trend-original]').is_visible()
                                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), 'expanded_trend_method_overflow'
                                method.locator('summary').click()
                                assert 'per anno' in shown.locator('[data-trend-value=slope]').text_content()
                                assert '/year' not in shown.text_content(), 'technical_trend_unit'
                                assert shown.locator('[data-trend-value=n]').text_content() == str(native['n'])
                                for observation in (response['observations'][0], response['observations'][-1]):
                                    assert str(observation['period']) in shown.locator('[data-trend-value=periods]').text_content()
                                assert ', '.join(map(str,native['timeAxis'])) in shown.locator('[data-trend-axis]').text_content()
                                assert 'non è una previsione' in shown.text_content() and 'non indica automaticamente' in shown.text_content()
                                if native['unit'] == 'percentage_points/year':
                                    assert 'punti percentuali per anno' in shown.locator('[data-trend-value=slope]').text_content()
                                    assert 'non in percentuale relativa' in shown.text_content()
                                chart = page.locator('.explorer-bar-row')
                                if chart.count():
                                    assert chart.locator(':scope > span:first-child').all_text_contents() == [str(o['period']) for o in response['observations'][:20]]
                                if len(response['observations']) > 20:
                                    page.get_by_role('button',name='Successive',exact=True).click()
                                    assert str(response['observations'][20]['period']) == page.locator('#explorer-result tbody tr').first.locator('td').nth(1).text_content()
                                    page.get_by_role('button',name='Precedenti',exact=True).click();trend_pages += 1
                            else:
                                trend_refusals += 1
                                assert shown.count() == 0 and not page.locator('.explorer-bar-row').count(), 'refusal_promoted_to_trend'
                                assert 'Nessuna tendenza stimata' in page.locator('#explorer-result').text_content()
                        if op in ('absolute_change','relative_change','percentage_points'):
                            native = entry['response']['result']; shown = page.locator('.explorer-change')
                            if entry['response']['status'] == 'computed':
                                changes[op] = changes.get(op, 0) + 1
                                assert shown.count() == 1
                                amounts = [entry['response']['observations'][0]['value'], entry['response']['observations'][1]['value'], native['value']]
                                # Playwright's Python value bridge serializes float 0.0 as -0;
                                # use integer zero for the presentation oracle, preserving native payloads.
                                for key, amount in zip(('start','end','change'), amounts):
                                    expected = page.evaluate("x=>new Intl.NumberFormat('it-IT',x!==0&&Math.abs(x)<.01?{maximumSignificantDigits:3}:{maximumFractionDigits:2}).format(x)",0 if amount == 0 else amount)
                                    assert expected in shown.locator('[data-change-value="'+key+'"]').text_content(), ('change_value_mismatch',entry['request'],key,amount,expected,shown.locator('[data-change-value="'+key+'"]').text_content())
                                for field in ('startPeriod','endPeriod'):
                                    assert str(native[field]) in shown.text_content()
                                assert 'non un tasso annuo' in shown.text_content()
                                if native['unit'] in ('percentage_points','percentagePoints'):
                                    assert 'punti percentuali' in shown.locator('[data-change-value="change"]').text_content()
                                if native['unit'] == 'percent_change':
                                    assert '%' in shown.locator('[data-change-value="change"]').text_content()
                            else:
                                change_refusals += 1
                                assert shown.count() == 0, 'refusal_promoted_to_change'

                        if entry['request']['operation'] == 'benchmark_gap':
                            r = entry['response']; native = r.get('result')
                            if r['status'] == 'computed':
                                benchmarks += 1
                                shown = page.locator('.explorer-benchmark')
                                assert shown.count() == 1, ('missing_benchmark_summary', entry['request'])
                                for key,field in [('municipal','municipalValue'),('reference','benchmarkValue'),('gap','value')]:
                                    # Compare visible numbers with native fields, not a recreated gap.
                                    # Parse the native JSON just as the product does. Playwright's
                                    # Python scalar bridge turns float 0.0 into JS -0.
                                    expected = page.evaluate("text=>{const x=JSON.parse(text);return new Intl.NumberFormat('it-IT',x!==0&&Math.abs(x)<.01?{maximumSignificantDigits:3}:{maximumFractionDigits:2}).format(x)}", json.dumps(native[field]))
                                    assert expected in shown.locator('[data-benchmark-value="'+key+'"]').text_content(), ('benchmark_value', key, entry['request'])
                                assert page.evaluate('x=>String(x)',native['period']) in shown.text_content(), ('benchmark_period', native, entry['request'])
                                for field in ('numeratorPeriod', 'denominatorPeriod'):
                                    if field in native:
                                        assert page.evaluate('x=>String(x)',native[field]) in shown.text_content(), ('benchmark_component_period', field, entry['request'])
                                if native['unit'] == 'percentage_points':
                                    assert 'punti percentuali' in shown.locator('[data-benchmark-value="gap"]').text_content()
                                    municipal = next(o for o in r['observations'] if o['geography'] == native['geography'])
                                    if municipal['unit'] == 'percent':
                                        assert '%' in shown.locator('[data-benchmark-value="municipal"]').text_content()
                            else:
                                benchmark_refusals += 1
                                assert page.locator('.explorer-benchmark').count() == 0, 'refusal_promoted_to_gap'
                            allowed = set(page.locator('#explorer-benchmark option').evaluate_all('(els)=>els.map(e=>e.value)'))
                            assert allowed <= {'', 'tuscany', 'italy'} and entry['request']['benchmark'] in allowed
                        if entry['request']['operation'] == 'weighted_ratio':
                            response = entry['response']; native = response.get('result')
                            shown = page.locator('.explorer-aggregation')
                            if response['status'] == 'computed':
                                aggregations += 1
                                assert shown.count() == 1, 'missing_full_area_result'
                                expected = page.evaluate("text=>{const x=JSON.parse(text);return new Intl.NumberFormat('it-IT',x!==0&&Math.abs(x)<.01?{maximumSignificantDigits:3}:{maximumFractionDigits:2}).format(x)}",json.dumps(native['value']))
                                assert expected in shown.locator('[data-aggregation-value]').text_content(), 'aggregation_summary_value'
                                assert sorted(native['geographies']) == sorted(t['code'] for t in root['towns'])
                                assert response['coverage']['requested'] == response['coverage']['usable'] == len(root['towns'])
                                for field in ('value','numerator','denominator','scale'):
                                    expected = page.evaluate("text=>new Intl.NumberFormat('it-IT',{maximumSignificantDigits:15}).format(JSON.parse(text))",json.dumps(native[field]))
                                    assert expected in shown.locator('[data-aggregation-component="'+field+'"]').text_content(), ('aggregation_component',field,entry['request'])
                                for field in ('period','numeratorPeriod','denominatorPeriod'):
                                    if field in native:
                                        assert str(native[field]) in shown.text_content(), ('aggregation_period',field,entry['request'])
                                assert 'Non è la media dei tassi comunali' in shown.text_content()
                            else:
                                aggregation_refusals += 1
                                assert shown.count() == 0, 'refusal_promoted_to_full_area_result'
                                assert 'Le eventuali osservazioni comunali non lo sostituiscono' in page.locator('#explorer-result').text_content()
                        ordered = entry['response']['observations']
                        if op == 'rank' and entry['response']['status'] == 'computed':
                            ordered = [next(o for o in ordered if o['geography']==r['geography']) for r in entry['response']['result']['ranking']]
                        numeric_rows = [i for i,o in enumerate(ordered[:20])
                                        if type(o.get('value')) in (int,float) and o.get('unit') != 'category_code'
                                        and not o.get('dataUnavailable') and not o.get('notApplicable')]
                        assert_readable_values(page, numeric_rows)
                        if width == 390 and checked == 0:
                            table = page.locator('.explorer-table-wrap')
                            assert table.evaluate('(e)=>e.scrollWidth>e.clientWidth'), 'mobile_table_cannot_scroll'
                            table.focus();page.keyboard.press('ArrowRight')
                            page.wait_for_function("()=>document.querySelector('.explorer-table-wrap').scrollLeft>0")
                            table.evaluate('(e)=>{e.scrollLeft=0}')
                        if any(o.get('unit') == 'category_code' for o in entry['response']['observations']):
                            categories += 1
                            assert page.locator('#explorer-result .explorer-bar-row').count() == 0
                            for o in entry['response']['observations'][:20]:
                                assert o['categoryLabel'] in page.locator('#explorer-result tbody').text_content()
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), 'preview_overflow'
                        if entry['request']['operation'] == 'benchmark_gap':
                            # Changing the reference, even to the empty choice, revokes evidence/consent.
                            page.select_option('#explorer-benchmark', '')
                            assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                            assert page.is_disabled('#explorer-run')
                            page.select_option('#explorer-benchmark', entry['request']['benchmark'])
                        if entry['request']['operation'] == 'weighted_ratio':
                            page.select_option('#explorer-operation','observe')
                            assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                            assert page.is_visible('#explorer-town-field')
                        checked += 1
                    assert checked and categories and partial and benchmarks and benchmark_refusals
                    assert aggregations and aggregation_refusals
                    assert rankings and ranking_refusals and ranking_ties, 'ranking_edge_cases_not_exercised'
                    assert trends and trend_refusals and len(trend_signs) == 2 and trend_pages, 'trend_edge_cases_not_exercised'
                    assert set(changes) == {'absolute_change','relative_change','percentage_points'} and change_refusals
                    select(partial);page.click('#explorer-run');page.wait_for_selector('#explorer-consent:not([hidden])')
                    page.click('#explorer-cancel');assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    # Filter revokes previous selection/results; no fabricated fallback view.
                    page.fill('#explorer-filter', 'NO_MATCH_VIEW_abcdef')
                    assert page.locator('#explorer-view option').count() == 0
                    assert page.is_disabled('#explorer-run')
                    page.fill('#explorer-filter', '')
                    # Network and integrity failures remove all results. Fresh opening retries
                    # the same embedded release, never another data source or cached answer.
                    point = next(e for e in samples if e['request']['operation'] == 'observe'
                                 and e['response']['status'] == 'computed')
                    fault_checks = []
                    for pattern, body in [('**/release.json', None), ('**/release.json', '{}'), ('**/*.json.gz', None), ('**/*.json.gz', 'corrupt')]:
                        context.route(pattern, lambda route, request, body=body: route.fulfill(status=404 if body is None else 200, body=body or 'missing'))
                        if 'release.json' in pattern:
                            page.reload();page.wait_for_selector('#explorer-retry:not([hidden])')
                        else:
                            page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                            selector = point['request']['selectors'][0]
                            page.select_option('#explorer-theme', summaries[selector['metric']]['theme'])
                            page.select_option('#explorer-metric', selector['metric'])
                            page.wait_for_selector('#explorer-retry:not([hidden])')
                        assert not page.is_visible('#explorer-result')
                        context.unroute(pattern)
                        page.click('#explorer-retry')
                        page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1 && !document.querySelector('#explorer-form fieldset').disabled")
                        select(point);page.click('#explorer-run');page.wait_for_selector('#explorer-result:not([hidden])')
                        assert json.loads(page.locator('[data-explorer-evidence]').text_content())['steps'][0]['response'] == point['response']
                        fault_checks.append(pattern+':'+str(body))
                    # A pending response must not reappear after changing the selection.
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(point)
                    held = []
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run')
                    page.wait_for_timeout(100)
                    assert held
                    page.select_option('#explorer-town', next(t['code'] for t in root['towns'] if t['code'] != point['request']['selectors'][0]['towns'][0]))
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz')
                    page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    trend = next(e for e in samples if e['request']['operation']=='trend' and e['response']['status']=='computed')
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(trend);held=[]
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run');page.wait_for_timeout(100)
                    assert held
                    other = next(t['code'] for t in root['towns'] if t['code'] != trend['request']['selectors'][0]['towns'][0])
                    page.select_option('#explorer-town', other)
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz');page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent'), 'stale_trend_restored'
                    # A late benchmark response cannot survive a reference change.
                    benchmark = next(e for e in samples if e['request']['operation'] == 'benchmark_gap'
                                     and e['response']['status'] == 'computed')
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(benchmark)
                    held = []
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run');page.wait_for_timeout(100)
                    assert held
                    page.select_option('#explorer-benchmark', '')
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz')
                    page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    assert page.is_disabled('#explorer-run')
                    # A full-area response arriving after a new operation is revoked.
                    aggregate = next(e for e in samples if e['request']['operation'] == 'weighted_ratio'
                                     and e['response']['status'] == 'computed')
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(aggregate);held=[]
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run');page.wait_for_timeout(100)
                    assert held
                    page.select_option('#explorer-operation','observe')
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz');page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    assert page.is_visible('#explorer-town-field')
                    ranking = next(e for e in samples if e['request']['operation']=='rank' and e['response']['status']=='computed')
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(ranking);held=[]
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run');page.wait_for_timeout(100)
                    assert held
                    page.select_option('#explorer-operation','compare')
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz');page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    temporal = next(e for e in samples if e['request']['operation']=='absolute_change' and e['request']['selectors'][0].get('periods'))
                    page.reload();page.wait_for_function("()=>document.querySelector('#explorer-theme').options.length>1")
                    select(temporal);held=[]
                    context.route('**/*.json.gz', lambda route, request: held.append(route))
                    page.click('#explorer-run');page.wait_for_timeout(100)
                    assert held
                    other = next(t['code'] for t in root['towns'] if t['code'] != temporal['request']['selectors'][0]['towns'][0])
                    page.select_option('#explorer-town', other)
                    for route in held: route.continue_()
                    context.unroute('**/*.json.gz');page.wait_for_load_state('networkidle')
                    assert not page.is_visible('#explorer-result') and not page.is_visible('#explorer-consent')
                    assert not outside, outside
                    assert not errors, errors
                    assert page.evaluate("!localStorage.length && !sessionStorage.length")
                    assert page.locator('#explorer-form select').evaluate_all("els=>els.every(e=>getComputedStyle(e).backgroundColor==='rgb(255, 255, 255)')")
                    results.append(dict(width=width, nativeSelections=checked, categorySelections=categories, benchmarkSelections=benchmarks, benchmarkRefusals=benchmark_refusals,
                                        aggregationSelections=aggregations, aggregationRefusals=aggregation_refusals,
                                        changeSelections=changes, changeRefusals=change_refusals,
                                        rankingSelections=rankings, rankingRefusals=ranking_refusals, rankingTies=ranking_ties,
                                        trendSelections=trends, trendRefusals=trend_refusals, trendUnits=sorted(trend_units), trendPaginationChecks=trend_pages,
                                        faultsAndSameReleaseRecoveries=len(fault_checks), staleSelectionRevoked=True))
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown();server.server_close()
    return dict(status='PASS', scope=receipt['scope'], browser=results,
                publicBuildRollback=True, publicArtifactCorruptionRejections=len(selected),
                productionWorkerOfflineFailClosed=True)
