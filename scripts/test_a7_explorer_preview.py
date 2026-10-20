#!/usr/bin/env python3
"""Exercise the guided preview through native controls, not a second UI engine."""
import functools
import http.server
import json
import threading
import tempfile
from pathlib import Path

from build_a7_explorer_preview import build


def verify_explorer(catalog, runtime, output, samples):
    source_page = Path(catalog).resolve().parent.parent/'chiedi/index.html'
    before = source_page.read_bytes()
    receipt = build(Path(catalog).resolve().parent.parent, runtime, output)
    assert not receipt['publicIntegration']
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
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
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

                    def select(entry):
                        request = entry['request']; selector = request['selectors'][0]
                        page.select_option('#explorer-theme', summaries[selector['metric']]['theme'])
                        page.select_option('#explorer-metric', selector['metric'])
                        page.wait_for_function("()=>document.querySelector('#explorer-view').options.length>0")
                        page.select_option('#explorer-view', selector['dimension'])
                        page.select_option('#explorer-operation', request['operation'])
                        if len(selector['towns']) == 1:
                            page.select_option('#explorer-town', selector['towns'][0])
                        assert not page.is_visible('#explorer-result')

                    partial = None; checked = 0; categories = 0
                    for entry in samples:
                        select(entry)
                        page.click('#explorer-run')
                        page.wait_for_function("()=>!document.querySelector('#explorer-consent').hidden || !document.querySelector('#explorer-result').hidden")
                        if page.is_visible('#explorer-consent'):
                            assert not page.is_visible('#explorer-result')
                            partial = entry
                            page.click('#explorer-accept')
                        page.wait_for_selector('#explorer-result:not([hidden])')
                        evidence = json.loads(page.locator('[data-explorer-evidence]').text_content())
                        assert evidence['steps'][0]['response'] == entry['response'], 'ui_changed_native_response'
                        assert evidence['plan']['steps'][0]['request'] == entry['request'], 'ui_changed_selection'
                        if any(o.get('unit') == 'category_code' for o in entry['response']['observations']):
                            categories += 1
                            assert page.locator('#explorer-result .explorer-bar-row').count() == 0
                            for o in entry['response']['observations'][:20]:
                                assert o['categoryLabel'] in page.locator('#explorer-result tbody').text_content()
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), 'preview_overflow'
                        checked += 1
                    assert checked and categories and partial
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
                    assert not outside, outside
                    assert not errors, errors
                    assert page.evaluate("!localStorage.length && !sessionStorage.length")
                    assert page.locator('#explorer-form select').evaluate_all("els=>els.every(e=>getComputedStyle(e).backgroundColor==='rgb(255, 255, 255)')")
                    results.append(dict(width=width, nativeSelections=checked, categorySelections=categories,
                                        faultsAndSameReleaseRecoveries=len(fault_checks), staleSelectionRevoked=True))
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown();server.server_close()
    return dict(status='PASS', scope=receipt['scope'], browser=results)
