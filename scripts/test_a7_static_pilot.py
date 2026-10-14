#!/usr/bin/env python3
"""Independent A6 expectations plus the static reader's refusal/integrity contract."""
import argparse
import functools
import gzip
import hashlib
import http.server
import json
import subprocess
import tempfile
import threading
from pathlib import Path

from build_a7_static_pilot import build, encode, render_answers, ROOT, PROGRAM, CASES
from build_territorial_dossier_evidence import portable_evidence
from semantic_query_engine import QueryEngine


def pointer(obj, path):
    for key in path.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def verify(catalog, output):
    bundle, release, measurement = build(catalog)
    again, second_release, _ = build(catalog)
    assert bundle == again and release == second_release, 'nonreproducible bundle'
    engine = QueryEngine(catalog, layer='effective')
    for cid, entry in bundle['cases'].items():
        raw = engine.query(entry['query'])
        assert entry['response'] == portable_evidence(raw), 'raw response altered: ' + cid
        for fact in entry['facts']:
            assert fact['value'] == pointer(raw, fact['responsePointer']), 'numeric anchor mismatch'
            assert fact['evidence'], 'uncited fact'
    canonical = {d['id']: d for d in json.loads(PROGRAM.read_text())['dossiers']}
    for q in bundle['questions']:
        d = canonical[q['dossierId']]
        p = d['centralPlan'] if q['id'] == d['centralPlan']['id'] else next(p for p in d['secondaryQuestions'] if p['id'] == q['id'])
        assert q['requiredCaseRefs'] == p['requiredCaseRefs']
        assert q['contextCaseRefs'] == p['contextCaseRefs']
        assert q['missingData'] == p['missingData']
        assert q['answerBoundary'] == p['answer']
    # Independent frozen source references already certified by A6, not constants
    # copied from this experiment's generated answer.
    source = json.loads((ROOT/'data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json').read_text())
    native = source['towns']['Massarosa']['labour']['25-64']['total']
    observed = bundle['cases']['census_employment_primary']['response']['observations'][0]['value']
    # The carrier is rounded; use the independently certified frozen case expectation.
    case = next(c for c in json.loads(CASES.read_text())['questions'] if c['id'] == 'census_employment_primary')
    assert observed == case['expected']['checks'][0]['value'] == 73.4
    assert round(native['employed']/native['population']*100, 1) == observed
    weighted = bundle['cases']['child_weighted']['response']['result']
    assert weighted['numerator'] == 1031 and weighted['denominator'] == 2217
    assert abs(weighted['value'] - 1031/2217*100) < 1e-9
    nominal = bundle['cases']['business_frame_services_history']['response']
    assert abs(nominal['result']['value'] - 71.917074) < 1e-9
    assert 'nominal_economic_values_not_real_growth' in nominal['warnings']
    output.mkdir(parents=True, exist_ok=True)
    (output/'bundle.json').write_text(encode(bundle), encoding='utf-8')
    (output/'release.json').write_text(encode(release), encoding='utf-8')
    (output/'answers.md').write_text(render_answers(bundle), encoding='utf-8')
    result = subprocess.run(['node', str(ROOT/'experiments/a7-static-pilot/test_reader.mjs'),
                             str(output/'bundle.json'), str(output/'release.json')], check=True, capture_output=True, text=True)
    node = json.loads(result.stdout)
    browser_reference = node.pop('browserReference')
    # Run the real browser ES module, served locally as static files. No product UI.
    from playwright.sync_api import sync_playwright
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(f'http://127.0.0.1:{server.server_port}/experiments/a7-static-pilot/scope.json')
                browser_result = page.evaluate('''async ({text, release}) => {
                    const {loadPilot} = await import('/experiments/a7-static-pilot/reader.mjs');
                    const begin = performance.now(); const pilot = await loadPilot(text, release);
                    const loadMilliseconds = performance.now() - begin;
                    const work = pilot.resolve({questionId:'lavoro-1'});
                    const early = pilot.resolve({caseId:'child_year_conversion'});
                    const partial = pilot.resolve({questionId:'infanzia-2'});
                    const accepted = pilot.resolve({questionId:'infanzia-2',approvedPartial:true});
                    return {loadMilliseconds, work, early, partial, accepted};
                }''', dict(text=encode(bundle), release=release))
                assert browser_result['work'] == browser_reference, 'browser/Node envelope differs'
                assert browser_result['early']['components'][0]['response'] == bundle['cases']['child_year_conversion']['response']
                assert browser_result['partial']['resolution'] == 'needs_confirmation'
                assert browser_result['accepted']['classification'] == 'partially_supported'
                browser_measurement = dict(environment=browser.version, loadMilliseconds=browser_result['loadMilliseconds'],
                                           scope='Local headless Chromium; not a mobile/network benchmark', status='PASS')
            finally:
                browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = dict(status='PASS', candidateTree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),
                  release=release, build=measurement, node=node, browser=browser_measurement,
                  gzipBytes=len(gzip.compress(encode(bundle).encode(), mtime=0)),
                  evidence='Canonical independent expectations + frozen sources; raw response replay; fact anchors; hostile reader inputs; exact browser/Node parity')
    (output/'verification.json').write_text(encode(report), encoding='utf-8')
    print(encode(report))


def main():
    p = argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output-dir',type=Path)
    args = p.parse_args()
    if args.output_dir:
        verify(args.catalog, args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix='ov-a7-pilot-') as path:
            verify(args.catalog, Path(path))


if __name__ == '__main__':
    main()
