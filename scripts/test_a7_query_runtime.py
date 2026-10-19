#!/usr/bin/env python3
"""Static transport parity, real browser loading and adversarial trust-boundary checks."""
import argparse
import copy
import functools
import gzip
import hashlib
import http.server
import json
import tempfile
import threading
from pathlib import Path

from a7_query_workbench import QueryWorkbench, encode
from build_a7_query_runtime import build, digest, recipes, PROFILES
from build_territorial_dossier_evidence import portable_evidence
from semantic_query_engine import ROOT


def verify(catalog, output=None):
    workbench = QueryWorkbench(catalog)
    # Representative transport gate, not another canonical indicator inventory.
    # Pick a carrier for each distinct declared operation signature; all-catalog
    # sizing is a separate CLI execution, not an exhaustive numerical audit.
    signatures = set()
    chosen = set()
    for row in workbench.engine.coverage():
        declaration = row['engine']
        signature = tuple(sorted({tuple(ops) for ops in declaration.get('operationsByDimension', {}).values()}))
        if signature not in signatures:
            signatures.add(signature); chosen.add(row['metric'])
    chosen.update(('population', 'territorialClassification', 'economyActivityAtlas'))
    with tempfile.TemporaryDirectory(prefix='a7-runtime-') as folder:
        root = Path(folder)
        release, measurement = build(catalog, root/'one', metrics=sorted(chosen), max_views=2, profiles=PROFILES)
        copied_catalog = root/'catalog-copy.json'
        copied_catalog.write_bytes(Path(catalog).read_bytes())
        again, _ = build(copied_catalog, root/'two', metrics=sorted(chosen), max_views=2, profiles=PROFILES)
        assert release == again
        # Ranking never widens the default envelope; exact selections only.
        assert not any(p == 'ranking' for p, _ in recipes('x', 'total', ['rank'], ['046018']))
        assert not list(recipes('x', 'category', ['compare'], ['046018'], ['ranking']))
        assert measurement['profiles']['ranking'] > 0
        first = {p.relative_to(root/'one').as_posix(): digest(p.read_bytes())
                 for p in (root/'one').rglob('*') if p.is_file()}
        second = {p.relative_to(root/'two').as_posix(): digest(p.read_bytes())
                  for p in (root/'two').rglob('*') if p.is_file()}
        assert first == second, 'nonreproducible release artifacts'
        assert 'seconds' not in json.loads((root/'one'/'measurement.json').read_text())
        checks = 0
        samples = []
        partial = None
        for metric in release['metrics']:
            detail = json.loads(gzip.decompress((root/'one'/metric['detail']['path']).read_bytes()))
            expected = workbench.discover(metric['metric'])['metrics'][0]['declaration']
            assert detail['declaration'] == expected
            assert [v['dimension'] for v in detail['views']] == expected['dimensions'][:2]
            for view in detail['views']:
                for profile, ref in view['shards'].items():
                    packed = (root/'one'/ref['path']).read_bytes()
                    raw = gzip.decompress(packed)
                    assert digest(packed) == ref['sha256'] and len(packed) == ref['bytes']
                    assert digest(raw) == ref['rawSha256'] and len(raw) == ref['rawBytes']
                    shard = json.loads(raw)
                    for entry in shard['entries']:
                        assert entry['response'] == portable_evidence(workbench.engine.query(entry['request'])), 'native response changed'
                        checks += 1
                        response = entry['response']
                        if 'partial_coverage_requires_opt_in' in response.get('reasons', []):
                            partial = entry
                    # A browser probe for every carrier/profile on its first view;
                    # Python transport parity above covers every generated request.
                    if view is detail['views'][0]:
                        samples.append(shard['entries'][0])
        assert partial is not None, 'missing-data fixture no longer representative'
        request = dict(operation='observe', selectors=[dict(metric='population', dimension='total', towns=[sorted(workbench.engine.codes)[0]])])
        point_plan = dict(schemaVersion=1, steps=[dict(id='point', request=request)])
        expected_point = portable_evidence(workbench.run(point_plan))
        release_text = (root/'one'/'release.json').read_text()

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(root)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    results = []
                    for width in (1440, 390):
                        page = browser.new_page(viewport=dict(width=width, height=844))
                        page.goto(f'http://127.0.0.1:{server.server_port}/one/release.json')
                        result = page.evaluate('''async ({module,text,anchor,plan,samples,partial}) => {
                          const {openRuntime} = await import(URL.createObjectURL(new Blob([module],{type:'text/javascript'})));
                          let fetches=0;
                          const fetcher=async (...args)=>{fetches++;return fetch(...args)};
                          const begin=performance.now();
                          const runtime=await openRuntime(text,anchor,location.origin+'/one/',{fetcher});
                          if(fetches!==0)throw Error('eager_payload_fetch');
                          const point=await runtime.run(plan);const pointMs=performance.now()-begin;
                          const repeat=await runtime.run(plan);if(fetches!==2)throw Error('cache_or_selectivity');
                          point.steps[0].response.observations[0].value=-999;
                          const immutable=await runtime.run(plan);
                          const parity=[];
                          for(const entry of samples){
                            const p={schemaVersion:1,steps:[{id:'s',request:entry.request}]};
                            const r=await runtime.run(p,{approvedPartial:true});
                            if(r.resolution!=='resolved'||JSON.stringify(r.steps[0].response)!==JSON.stringify(entry.response))throw Error('browser_native_parity');
                            parity.push(r.steps[0].response.status);
                          }
                          const partialPlan={schemaVersion:1,steps:[{id:'p',request:partial.request}]};
                          const protectedPartial=await runtime.run(partialPlan);
                          const acceptedPartial=await runtime.run(partialPlan,{approvedPartial:true});
                          const outside=structuredClone(plan);outside.steps[0].request.selectors[0].periods=['9999'];
                          const unmaterialized=await runtime.run(outside);
                          const beforeInvalid=fetches;
                          let invalid=false;try{await runtime.run({schemaVersion:1,steps:[plan.steps[0],plan.steps[0]]})}catch{invalid=true}
                          if(!invalid||fetches!==beforeInvalid)throw Error('invalid_plan_fetched');
                          let corrupted=false;try{await openRuntime(text+' ',anchor,location.origin+'/one/')}catch{corrupted=true}
                          if(!corrupted)throw Error('corrupt_release_accepted');
                          let external=false;try{await openRuntime(text,anchor,'https://example.invalid/')}catch{external=true}
                          if(!external)throw Error('external_base_accepted');
                          const corrupt=await openRuntime(text,anchor,location.origin+'/one/',{fetcher:async()=>new Response(new Uint8Array([1,2,3]))});
                          let shardCorrupt=false;try{await corrupt.run(plan)}catch{shardCorrupt=true}
                          if(!shardCorrupt)throw Error('corrupt_shard_accepted');
                          return {repeat,immutable,parity,protectedPartial,acceptedPartial,unmaterialized,fetches,pointMs};
                        }''', dict(module=(ROOT/'experiments/a7-query-runtime/reader.mjs').read_text(),
                                   text=release_text, anchor=digest(release_text.encode()), plan=point_plan,
                                   samples=samples, partial=partial))
                        assert result['repeat'] == dict(expected_point, resolution='resolved')
                        assert result['immutable'] == result['repeat']
                        assert result['protectedPartial']['resolution'] == 'needs_confirmation'
                        assert 'steps' not in result['protectedPartial']
                        assert result['acceptedPartial']['steps'][0]['response'] == partial['response']
                        assert result['acceptedPartial']['steps'][0]['response']['status'] == 'not_computable'
                        assert result['unmaterialized']['resolution'] == 'not_materialized'
                        results.append(dict(width=width, browserRequests=len(samples), pointMs=result['pointMs']))
                        page.close()
                finally:
                    browser.close()
        finally:
            server.shutdown(); server.server_close()
    report = dict(status='PASS', catalogSha256=workbench.engine.catalog_hash,
                  metrics=len(chosen), transportParityRequests=checks, browser=results,
                  measurement=measurement,
                  limits='Representative transport/browser gate; full-catalog sizing separate. Viewports are not physical mobile hardware or WAN measurements. Native A6 independent numerical suite remains authoritative.')
    if output:
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    print(json.dumps(verify(args.catalog, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
