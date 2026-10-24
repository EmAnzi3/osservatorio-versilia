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
from build_a7_query_runtime import change_periods, CHANGE_OPERATIONS, build, digest, recipes, PROFILES
from build_territorial_dossier_evidence import portable_evidence
from semantic_query_engine import ROOT
from test_a7_runtime_package import verify_package_boundaries, verify_packaged_browser
from a7_runtime_package import package_runtime
from test_a7_explorer_preview import verify_explorer


def verify_empty_profile_maxima(catalog):
    for profile in ('ranking', 'benchmark', 'aggregation', 'changes', 'trends'):
        with tempfile.TemporaryDirectory(prefix='a7-empty-profile-') as folder:
            release, measurement = build(catalog, folder, metrics=['territorialClassification'],
                                         max_views=1, profiles=(profile,))
            detail = json.loads(gzip.decompress((Path(folder)/release['metrics'][0]['detail']['path']).read_bytes()))
            assert not any(view['shards'] for view in detail['views'])
            assert measurement['requests'] == 0
            assert measurement['maxShardRawBytes'] == measurement['maxShardGzipBytes'] == 0
            assert measurement['rawBytes'] > 0 and measurement['gzipBytes'] > 0
            with tempfile.TemporaryDirectory(prefix='a7-empty-package-') as packaged:
                descriptor = package_runtime(folder, catalog, Path(packaged)/'bundle')
                assert descriptor['requests'] == 0 and descriptor['views'] == 1


def verify_association_transport(catalog):
    """Exact selected pairs, original A6 refusals and the same atomic boundary."""
    from unittest.mock import patch
    from audit_a7_accessibility import replay_associations, read_artifact
    from a7_runtime_package import verify_runtime, verify_package
    from semantic_question_suite import QUESTIONS, check_expected
    wb = QueryWorkbench(catalog)
    case = next(c for c in json.loads(QUESTIONS.read_text())['questions'] if c['id'] == 'aligned_association')
    good = copy.deepcopy(case['query'])
    assert not check_expected(wb.engine.query(good), case['expected'])
    pearson = dict(copy.deepcopy(good), method='pearson')
    missing_purpose = copy.deepcopy(good); missing_purpose.pop('purpose')
    different_periods = copy.deepcopy(good)
    for selector in different_periods['selectors']: selector.pop('periods')
    unaligned = copy.deepcopy(good)
    unaligned['selectors'][0]['towns'] = sorted(wb.engine.codes)
    unaligned['selectors'][1]['towns'] = sorted(wb.engine.codes)[:-1]
    opted = dict(copy.deepcopy(good), allowPartial=True)
    unknown = copy.deepcopy(good); unknown['selectors'][0]['metric'] = 'not_a_metric'
    requests = [good, pearson, missing_purpose, different_periods, unaligned, opted, unknown, good]
    plan = dict(schemaVersion=1, steps=[dict(id=f'p{i}', request=r) for i, r in enumerate(requests)])
    expected = portable_evidence(wb.run(plan))
    assert expected['steps'][4]['response']['pairCoverage']['paired'] < expected['steps'][4]['response']['pairCoverage']['requested']
    assert expected['steps'][4]['response']['status'] == 'not_computable'
    assert expected['steps'][4]['response']['coverage']['usable'] == expected['steps'][4]['response']['coverage']['requested']
    assert expected['steps'][2]['response']['status'] == expected['steps'][3]['response']['status'] == 'not_computable'
    with tempfile.TemporaryDirectory(prefix='a7-associations-') as temporary:
        root = Path(temporary)
        options = dict(metrics=['population','income'], max_views=1, profiles=('current',))
        baseline, _ = build(catalog, root/'baseline', **options)
        release, measurement = build(catalog, root/'one', association_plan=plan, **options)
        copied = root/'catalog.json'; copied.write_bytes(Path(catalog).read_bytes())
        replay, _ = build(copied, root/'two', association_plan=plan, **options)
        assert release == replay
        assert {p.name:digest(p.read_bytes()) for p in (root/'one').iterdir()} == {p.name:digest(p.read_bytes()) for p in (root/'two').iterdir()}, 'association_build_not_reproducible'
        assert 'associationPlan' not in baseline
        assert baseline['metrics'] == release['metrics'], 'association_plan_changed_existing_profiles'
        assert measurement['profiles']['association'] == len(requests)
        for summary in baseline['metrics']:
            detail_ref = summary['detail']
            assert (root/'baseline'/detail_ref['path']).read_bytes() == (root/'one'/detail_ref['path']).read_bytes()
            detail = json.loads(gzip.decompress((root/'baseline'/detail_ref['path']).read_bytes()))
            for view in detail['views']:
                for ref in view['shards'].values():
                    assert (root/'baseline'/ref['path']).read_bytes() == (root/'one'/ref['path']).read_bytes()
        for step, entry in zip(expected['steps'], release['associationPlan']['entries']):
            shard = json.loads(gzip.decompress((root/'one'/entry['artifact']['path']).read_bytes()))
            assert shard['response'] == step['response']
        verify_runtime(root/'one', catalog)
        replayed = list(replay_associations(wb, root/'one', release))
        assert [step for step, _ in replayed] == plan['steps']
        assert [response for _, response in replayed] == [s['response'] for s in expected['steps']]
        def false_number(folder, ref):
            shard = read_artifact(folder, ref)
            if shard.get('kind') == 'a7-native-association' and shard['response'].get('result'):
                shard['response']['result']['coefficient'] += 0.01
            return shard
        with patch('audit_a7_accessibility.read_artifact', side_effect=false_number):
            try: list(replay_associations(wb, root/'one', release))
            except ValueError as error: assert str(error) == 'runtime_native_parity_mismatch'
            else: raise AssertionError('association_audit_accepted_changed_native_number')
        package = package_runtime(root/'one', catalog, root/'package')
        assert verify_package(root/'package', catalog) == package
        assert list(replay_associations(wb, root/'package/runtime'/package['releaseSha256'], release)) == replayed
        for name, bad in [('wrong-operation',dict(schemaVersion=1,steps=[dict(id='x',request={'operation':'compare'})])),
                          ('numeric-token',dict(schemaVersion=1,steps=[dict(id='x',request=dict(good,method=1.0))])),
                          ('too-many',dict(schemaVersion=1,steps=[dict(id=str(i),request=good) for i in range(33)]))]:
            try: build(catalog, root/name, association_plan=bad, **options)
            except ValueError: pass
            else: raise AssertionError('invalid_association_plan_accepted')
            assert not (root/name).exists(), 'invalid_plan_created_output'
        original = release['associationPlan']['entries'][0]['artifact']
        broken = copy.deepcopy(release); broken['associationPlan']['entries'][0]['requestSha256'] = '0'*64
        (root/'one/release.json').write_text(encode(broken))
        try: package_runtime(root/'one', catalog, root/'rejected-package')
        except ValueError as error: assert str(error) == 'association_request_scope_mismatch'
        else: raise AssertionError('unbound_association_accepted')
        assert not (root/'rejected-package').exists()
        (root/'one/release.json').write_text(encode(release))
        block = root/'one'/original['path']; saved = block.read_bytes(); block.unlink()
        try: package_runtime(root/'one', catalog, root/'missing-association-package')
        except ValueError as error: assert str(error) == 'missing_or_unsafe_artifact'
        else: raise AssertionError('missing_association_exposed_partial_package')
        assert not (root/'missing-association-package').exists()
        block.write_bytes(saved)
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1',0), functools.partial(Quiet,directory=str(root)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        from playwright.sync_api import sync_playwright
        browser_results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for width in (1440,390):
                        page = browser.new_page(viewport=dict(width=width,height=844))
                        page.goto(f'http://127.0.0.1:{server.server_port}/one/release.json')
                        result = page.evaluate(ASSOCIATION_BROWSER, dict(
                            module=Path(__file__).resolve().parents[1].joinpath('experiments/a7-query-runtime/reader.mjs').read_text(),
                            text=encode(release),anchor=digest(encode(release).encode()),plan=plan,
                            missing=original['path']))
                        assert result['all'] == dict(expected,resolution='resolved')
                        assert result['subsetAccepted']['steps'][0]['response'] == expected['steps'][4]['response']
                        assert result['subsetProtected']['resolution'] == result['optedProtected']['resolution'] == 'needs_confirmation'
                        assert all(r['resolution'] == 'not_materialized' for r in result['unmaterialized'])
                        assert result['initialFetches'] == 0 and result['repeatFetches'] == 0
                        assert result['failure'] == 'artifact_fetch_failed'
                        assert result['raced'] == dict(portable_evidence(wb.run(dict(schemaVersion=1,steps=[plan['steps'][0]]))),resolution='resolved')
                        browser_results.append(dict(width=width,status='PASS',initialFetches=0,requests=len(requests)))
                        page.close()
                finally: browser.close()
        finally: server.shutdown(); server.server_close()
    return dict(status='PASS',requests=len(requests),browser=browser_results,
                scope='explicit plan only; native parity and original independent Spearman anchor, no Cartesian coverage claim')


ASSOCIATION_BROWSER = r"""async ({module,text,anchor,plan,missing}) => {
  const {openRuntime} = await import(URL.createObjectURL(new Blob([module],{type:'text/javascript'})));
  let fetches=0;
  const fetcher=async (...args)=>{fetches++;return fetch(...args)};
  const runtime=await openRuntime(text,anchor,location.origin+'/one/',{fetcher});
  const initialFetches=fetches;
  const first=await runtime.run(plan,{approvedPartial:true});
  const coefficient=first.steps[0].response.result.coefficient;
  first.steps[0].response.result.coefficient=-999;
  const before=fetches;const all=await runtime.run(plan,{approvedPartial:true});const repeatFetches=fetches-before;
  if(all.steps[0].response.result.coefficient!==coefficient)throw Error('association_cache_mutated');
  const one=i=>({schemaVersion:1,steps:[plan.steps[i]]});
  const subsetProtected=await runtime.run(one(4));
  const subsetAccepted=await runtime.run(one(4),{approvedPartial:true});
  const optedProtected=await runtime.run(one(5));
  const unmaterialized=[];
  for(const change of [r=>r.purpose+=' changed',r=>r.method='kendall',r=>r.selectors[0].periods=['9999']]){
    const changed=structuredClone(one(0));change(changed.steps[0].request);unmaterialized.push(await runtime.run(changed));
  }
  const broken=await openRuntime(text,anchor,location.origin+'/one/',{fetcher:async url=>url.endsWith(missing)?new Response('',{status:404}):fetch(url)});
  let failure=null;try{await broken.run(one(0))}catch(error){failure=error.message}
  let enter,release;const reached=new Promise(r=>enter=r), barrier=new Promise(r=>release=r);
  const racing=await openRuntime(text,anchor,location.origin+'/one/',{fetcher:async(...args)=>{enter();await barrier;return fetch(...args)}});
  const mutable=structuredClone(one(0));const pending=racing.run(mutable);await reached;
  mutable.steps[0].request.method='changed';release();const raced=await pending;
  return {all,initialFetches,repeatFetches,subsetProtected,subsetAccepted,optedProtected,unmaterialized,failure,raced};
}"""


def verify(catalog, output=None):
    verify_empty_profile_maxima(catalog)
    associations = verify_association_transport(catalog)
    workbench = QueryWorkbench(catalog)
    # Representative transport gate, not another canonical indicator inventory.
    # Pick a carrier for each distinct declared operation signature; all-catalog
    # sizing is a separate CLI execution, not an exhaustive numerical audit.
    signatures = set()
    chosen = set()
    for row in workbench.engine.coverage():
        declaration = row['engine']
        signature = tuple(sorted({(tuple(ops), tuple(declaration['benchmarkScopesByDimension'][dim]))
                                  for dim, ops in declaration.get('operationsByDimension', {}).items()}))
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
        assert measurement['profiles']['benchmark'] > 0
        assert not list(recipes('x', 'total', ['benchmark_gap'], ['046018'], ['benchmark']))
        assert not list(recipes('x', 'total', ['compare'], ['046018'], ['benchmark'],
                                benchmark_scopes=['tuscany']))
        requests = list(recipes('x', 'total', ['benchmark_gap'], ['046018'], ['benchmark'],
                                benchmark_scopes=['versilia', 'tuscany', 'italy']))
        assert [q['benchmark'] for _, q in requests] == ['italy', 'tuscany']
        assert not any(p == 'benchmark' for p, _ in recipes('x', 'total', ['benchmark_gap'],
                          ['046018'], benchmark_scopes=['tuscany', 'italy']))
        assert not list(recipes('x', 'total', ['weighted_ratio'], ['046018']))
        assert not list(recipes('x', 'total', ['compare'], ['046018'], ['aggregation']))
        assert list(recipes('x', 'total', ['weighted_ratio'], ['046018'], ['aggregation'])) == [
            ('aggregation', dict(operation='weighted_ratio', selectors=[dict(metric='x', dimension='total', towns=['046018'])]))]
        assert measurement['profiles']['aggregation'] > 0
        assert measurement['profiles']['changes'] > 0
        assert measurement['profiles']['trends'] > 0
        assert not list(recipes('x', 'total', ['trend'], ['046018']))
        assert not list(recipes('x', 'total', ['series'], ['046018'], ['trends']))
        assert list(recipes('x', 'total', ['trend'], ['046018'], ['trends'])) == [
            ('trends', dict(operation='trend', selectors=[dict(metric='x', dimension='total', towns=['046018'])]))]
        assert not any(p == 'changes' for p, _ in recipes('x', 'total', CHANGE_OPERATIONS, ['046018']))
        assert not list(recipes('x', 'total', ['compare'], ['046018'], ['changes']))
        from types import SimpleNamespace
        # Missing endpoints must remain endpoints; never search for a usable value.
        calls = []
        def history(request):
            calls.append(request)
            return dict(observations=[dict(period='2010', value=None), dict(period='2015', value=5), dict(period='2020', value=None)])
        periods = change_periods(SimpleNamespace(engine=SimpleNamespace(query=history)), 'x', 'total', CHANGE_OPERATIONS, ['046018'])
        assert periods == {'046018': ['2010', '2020']}
        assert calls == [dict(operation='series', selectors=[dict(metric='x', dimension='total', towns=['046018'])])]
        for _, request in recipes('x', 'total', CHANGE_OPERATIONS, ['046018'], ['changes'], change_periods_by_town=periods):
            assert request['selectors'][0]['periods'] == ['2010', '2020']
            assert 'allowPartial' not in request
        first = {p.relative_to(root/'one').as_posix(): digest(p.read_bytes())
                 for p in (root/'one').rglob('*') if p.is_file()}
        second = {p.relative_to(root/'two').as_posix(): digest(p.read_bytes())
                  for p in (root/'two').rglob('*') if p.is_file()}
        assert first == second, 'nonreproducible release artifacts'
        assert 'seconds' not in json.loads((root/'one'/'measurement.json').read_text())
        checks = 0
        shard_refs = []
        samples = []
        partial = None
        for metric in release['metrics']:
            detail = json.loads(gzip.decompress((root/'one'/metric['detail']['path']).read_bytes()))
            expected = workbench.discover(metric['metric'])['metrics'][0]['declaration']
            assert detail['declaration'] == expected
            assert [v['dimension'] for v in detail['views']] == expected['dimensions'][:2]
            for view in detail['views']:
                for profile, ref in view['shards'].items():
                    shard_refs.append(ref)
                    packed = (root/'one'/ref['path']).read_bytes()
                    raw = gzip.decompress(packed)
                    assert digest(packed) == ref['sha256'] and len(packed) == ref['bytes']
                    assert digest(raw) == ref['rawSha256'] and len(raw) == ref['rawBytes']
                    shard = json.loads(raw)
                    for entry in shard['entries']:
                        assert entry['response'] == portable_evidence(workbench.engine.query(entry['request'])), 'native response changed'
                        if profile == 'benchmark':
                            q = entry['request']
                            assert q['benchmark'] in expected['benchmarkScopesByDimension'][view['dimension']]
                            assert q['benchmark'] in ('tuscany', 'italy')
                            assert len(q['selectors'][0]['towns']) == 1
                        if profile == 'changes':
                            selector = entry['request']['selectors'][0]
                            assert len(selector['towns']) == 1
                            expected_periods = change_periods(workbench, metric['metric'], view['dimension'], view['declaredOperations'], selector['towns'])
                            assert selector.get('periods') == expected_periods[selector['towns'][0]]
                            assert 'allowPartial' not in entry['request']
                        if profile == 'trends':
                            assert entry['request'] == dict(operation='trend', selectors=[dict(
                                metric=metric['metric'], dimension=view['dimension'],
                                towns=entry['request']['selectors'][0]['towns'])])
                            assert len(entry['request']['selectors'][0]['towns']) == 1
                            if entry['response']['status'] == 'computed':
                                assert entry['response']['result']['forecast'] is False
                                assert entry['response']['result']['method'] == 'OLS slope'
                        if profile == 'aggregation':
                            assert entry['request'] == dict(operation='weighted_ratio', selectors=[dict(
                                metric=metric['metric'], dimension=view['dimension'], towns=sorted(workbench.engine.codes))])
                            if entry['response']['status'] == 'computed':
                                assert sorted(entry['response']['result']['geographies']) == sorted(workbench.engine.codes)
                                assert entry['response']['coverage']['requested'] == entry['response']['coverage']['usable'] == len(workbench.engine.codes)
                        checks += 1
                        response = entry['response']
                        if 'partial_coverage_requires_opt_in' in response.get('reasons', []):
                            partial = entry
                    # A browser probe for every carrier/profile on its first view;
                    # Python transport parity above covers every generated request.
                    if view is detail['views'][0] or profile in ('ranking', 'aggregation', 'changes', 'trends'):
                        selected = (shard['entries'][::len(release['towns'])] if profile == 'benchmark'
                                    else [shard['entries'][0]])
                        if profile in ('benchmark', 'changes', 'trends'):
                            if profile in ('changes', 'trends'):
                                selected = []
                            # The first town can be complete while another is not.
                            # Exercise each native status/reason path, without a town whitelist.
                            paths = {(e['request']['operation'], e['response']['status'], tuple(e['response']['reasons'])) for e in selected}
                            for entry in shard['entries']:
                                path = (entry['request']['operation'], entry['response']['status'], tuple(entry['response']['reasons']))
                                if path not in paths:
                                    paths.add(path); selected.append(entry)
                        samples.extend(selected)
        assert measurement['maxShardRawBytes'] == max((r['rawBytes'] for r in shard_refs), default=0)
        assert measurement['maxShardGzipBytes'] == max((r['bytes'] for r in shard_refs), default=0)
        assert partial is not None, 'missing-data fixture no longer representative'
        request = dict(operation='observe', selectors=[dict(metric='population', dimension='total', towns=[sorted(workbench.engine.codes)[0]])])
        point_plan = dict(schemaVersion=1, steps=[dict(id='point', request=request)])
        expected_point = portable_evidence(workbench.run(point_plan))
        release_text = (root/'one'/'release.json').read_text()
        package = verify_package_boundaries(catalog, root/'one', root)
        assert package['unchangedInput'] == first, 'packaging_changed_runtime_input'
        explorer = verify_explorer(catalog, root/'one', root/'explorer-preview', samples)

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
                          // Pause the first real artifact load, then reuse caller state.
                          // The response, plan and digest must retain the original intent.
                          let entered, release;
                          const reached=new Promise(resolve=>{entered=resolve});
                          const barrier=new Promise(resolve=>{release=resolve});
                          let paused=false;
                          const racingRuntime=await openRuntime(text,anchor,location.origin+'/one/',{fetcher:async(...args)=>{
                            if(!paused){paused=true;entered();await barrier}
                            return fetch(...args);
                          }});
                          const mutablePlan=structuredClone(plan);
                          const pending=racingRuntime.run(mutablePlan);
                          await reached;
                          mutablePlan.steps[0].request={operation:'observe',selectors:[{metric:'caller_reused_state'}]};
                          release();
                          const raced=await pending;
                          if(raced.plan.steps[0].request.selectors[0].metric!==plan.steps[0].request.selectors[0].metric)throw Error('caller_mutation_changed_inflight_plan');
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
                          const benchmark=samples.find(e=>e.request.operation==='benchmark_gap');
                          if(!benchmark)throw Error('missing_benchmark_probe');
                          for(const change of ['scope','towns','period','consent']){
                            const request=structuredClone(benchmark.request);
                            if(change==='scope')request.benchmark='versilia';
                            if(change==='towns')request.selectors[0].towns=[];
                            if(change==='period')request.selectors[0].periods=['9999'];
                            if(change==='consent')request.allowPartial=true;
                            const r=await runtime.run({schemaVersion:1,steps:[{id:'outside',request}]},{approvedPartial:true});
                            if(r.resolution!=='not_materialized')throw Error('benchmark_scope_rewritten');
                          }
                          const aggregate=samples.find(e=>e.request.operation==='weighted_ratio');
                          if(!aggregate)throw Error('missing_aggregation_probe');
                          for(const change of ['subset','scope','period','consent']){
                            const request=structuredClone(aggregate.request);
                            if(change==='subset')request.selectors[0].towns=request.selectors[0].towns.slice(1);
                            if(change==='scope')request.selectors[0].towns=['versilia'];
                            if(change==='period')request.selectors[0].periods=['9999'];
                            if(change==='consent')request.allowPartial=true;
                            const r=await runtime.run({schemaVersion:1,steps:[{id:'outside',request}]},{approvedPartial:true});
                            if(r.resolution!=='not_materialized')throw Error('aggregation_scope_rewritten');
                          }
                          const temporal=samples.find(e=>e.request.selectors[0].periods?.length===2&&['absolute_change','relative_change','percentage_points'].includes(e.request.operation));
                          if(!temporal)throw Error('missing_change_probe');
                          for(const change of ['period','reverse','omit','towns','consent']){
                            const request=structuredClone(temporal.request);const s=request.selectors[0];
                            if(change==='period')s.periods=['9998','9999'];
                            if(change==='reverse')s.periods.reverse();
                            if(change==='omit')delete s.periods;
                            if(change==='towns')s.towns=[];
                            if(change==='consent')request.allowPartial=true;
                            const r=await runtime.run({schemaVersion:1,steps:[{id:'outside',request}]},{approvedPartial:true});
                            if(r.resolution!=='not_materialized')throw Error('change_scope_rewritten');
                          }
                          const trend=samples.find(e=>e.request.operation==='trend');
                          if(!trend)throw Error('missing_trend_probe');
                          for(const change of ['period','towns','consent','method']){
                            const request=structuredClone(trend.request);
                            if(change==='period')request.selectors[0].periods=['9999'];
                            if(change==='towns')request.selectors[0].towns=[];
                            if(change==='consent')request.allowPartial=true;
                            if(change==='method')request.method='OLS';
                            const r=await runtime.run({schemaVersion:1,steps:[{id:'outside',request}]},{approvedPartial:true});
                            if(r.resolution!=='not_materialized')throw Error('trend_scope_rewritten');
                          }
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
                          return {repeat,immutable,raced,parity,protectedPartial,acceptedPartial,unmaterialized,fetches,pointMs};
                        }''', dict(module=(ROOT/'experiments/a7-query-runtime/reader.mjs').read_text(),
                                   text=release_text, anchor=digest(release_text.encode()), plan=point_plan,
                                   samples=samples, partial=partial))
                        assert result['repeat'] == dict(expected_point, resolution='resolved')
                        assert result['immutable'] == result['repeat']
                        assert result['raced'] == dict(expected_point, resolution='resolved')
                        assert result['protectedPartial']['resolution'] == 'needs_confirmation'
                        assert 'steps' not in result['protectedPartial']
                        assert result['acceptedPartial']['steps'][0]['response'] == partial['response']
                        assert result['acceptedPartial']['steps'][0]['response']['status'] == 'not_computable'
                        assert result['unmaterialized']['resolution'] == 'not_materialized'
                        packaged_browser = verify_packaged_browser(page, f'http://127.0.0.1:{server.server_port}/',
                                                                    package, point_plan, expected_point)
                        results.append(dict(width=width, browserRequests=len(samples), pointMs=result['pointMs'],
                                            packagedBrowser=packaged_browser))
                        page.close()
                finally:
                    browser.close()
        finally:
            server.shutdown(); server.server_close()
    report = dict(status='PASS', associations=associations, catalogSha256=workbench.engine.catalog_hash,
                  metrics=len(chosen), transportParityRequests=checks, browser=results,
                  measurement=measurement, packageBoundaryRejections=package['rejected'],
                  packageReleaseSha256=package['descriptor']['releaseSha256'],
                  explorerPreview=explorer,
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
