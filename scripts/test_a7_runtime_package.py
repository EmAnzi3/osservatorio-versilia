"""Package boundary regressions, called by the existing static transport gate."""
import gzip
import json
import shutil
from pathlib import Path
from unittest.mock import patch

from a7_runtime_package import decode, loader_source, package_runtime, verify_package
from build_a7_query_runtime import digest, build
from a7_query_workbench import QueryWorkbench


def hashes(folder):
    return {p.relative_to(folder).as_posix(): digest(p.read_bytes())
            for p in folder.rglob('*') if p.is_file()}


def verify_package_boundaries(catalog, runtime, root):
    destination = root/'nested'/'package'
    descriptor = package_runtime(runtime, catalog, destination)
    assert verify_package(destination, catalog) == descriptor
    second = root/'another-location'/'package'
    assert package_runtime(runtime, catalog, second) == descriptor
    assert hashes(destination) == hashes(second), 'package_location_changed_bytes'
    original = hashes(destination)
    rejected = []

    def reject(name, source, expected=None, output=None):
        output = output or root/('rejected-'+name)
        try:
            package_runtime(source, catalog, output)
        except (ValueError, OSError) as error:
            if expected:
                assert expected in str(error), (name, error)
        else:
            raise AssertionError('invalid_package_accepted:'+name)
        if output != destination:
            assert not output.exists(), 'partial_package_exposed:'+name
        assert hashes(destination) == original, 'previous_package_changed:'+name
        assert not list(root.glob('.a7-package-*')), 'staging_not_removed:'+name
        rejected.append(name)

    reject('existing-output', runtime, 'package_output_already_exists', destination)
    with patch('a7_runtime_package.os.rename', side_effect=OSError('simulated_commit_failure')):
        reject('commit-interrupted', runtime, 'simulated_commit_failure')

    broken = root/'broken-runtime'
    release = json.loads((runtime/'release.json').read_text())
    detail_ref = release['metrics'][0]['detail']
    detail = json.loads(gzip.decompress((runtime/detail_ref['path']).read_bytes()))
    shard_ref = next(ref for v in detail['views'] for ref in v['shards'].values())

    def reset():
        if broken.exists():
            shutil.rmtree(broken)
        shutil.copytree(runtime, broken)

    for name, ref in [('missing-detail', detail_ref), ('missing-shard', shard_ref)]:
        reset()
        (broken/ref['path']).unlink()
        reject(name, broken, 'missing_or_unsafe_artifact')
    reset()
    (broken/shard_ref['path']).write_bytes(b'corrupt')
    reject('corrupt-shard', broken, 'artifact_integrity_mismatch')
    reset()
    (broken/'orphan.json.gz').write_bytes(b'orphan from another release')
    reject('mixed-release-files', broken, 'unreferenced_runtime_artifact')
    reset()
    (broken/shard_ref['path']).unlink()
    (broken/shard_ref['path']).symlink_to(runtime/shard_ref['path'])
    reject('symlink-shard', broken, 'unsafe_runtime_artifact')

    for name, key, value, reason in [
        ('incompatible-schema', 'schemaVersion', 2, 'incompatible_artifact_schema'),
        ('boolean-schema', 'schemaVersion', True, 'incompatible_artifact_schema'),
        ('different-reader', 'readerSha256', '0'*64, 'runtime_producer_mismatch'),
        ('different-catalog', 'catalogSha256', '0'*64, 'runtime_producer_mismatch'),
    ]:
        reset()
        changed = dict(release, **{key:value})
        (broken/'release.json').write_text(json.dumps(changed))
        reject(name, broken, reason)
    for name, field, value, reason in [
        ('decompressed-size', 'rawBytes', 1, 'artifact_integrity_mismatch'),
        ('decompressed-hash', 'rawSha256', '0'*64, 'artifact_integrity_mismatch'),
        ('reference-path', 'path', '../release.json', 'invalid_artifact_reference'),
    ]:
        reset()
        changed = json.loads(json.dumps(release))
        changed['metrics'][0]['detail'][field] = value
        (broken/'release.json').write_text(json.dumps(changed))
        reject(name, broken, reason)
    alias = root/'runtime-alias'
    alias.symlink_to(runtime, target_is_directory=True)
    reject('overlapping-alias', runtime, 'overlapping_package_directories', alias/'rejected')
    reset()
    measurement = json.loads((broken/'measurement.json').read_text())
    measurement['maxShardRawBytes'] += 1
    (broken/'measurement.json').write_text(json.dumps(measurement))
    reject('false-measurement', broken, 'runtime_measurement_mismatch')

    # Native producer headers are supplied by A6 itself. Build well-formed
    # adversarial graphs with metadata alone altered, leaving source, adapters
    # and numerical observations untouched. Hashes and measurements remain valid.
    for field, missing in [('adapterImplementationSha256',False),('policySha256',False),
                           ('eligibilitySha256',False),('engineVersion',False),
                           ('adapterImplementationSha256',True)]:
        wb = QueryWorkbench(catalog)
        native = wb.engine.query
        def incompatible(request):
            response = native(request)
            if missing:
                response.pop(field, None)
            else:
                response[field] = 'incompatible' if field == 'engineVersion' else '0'*64
            return response
        wb.engine.query = incompatible
        tainted = root/('tainted-'+field+('-missing' if missing else ''))
        with patch('build_a7_query_runtime.QueryWorkbench',return_value=wb):
            build(catalog,tainted,metrics=['population'],max_views=1,profiles=('current',))
        reject('native-producer-'+field+('-missing' if missing else ''), tainted,
               'runtime_response_producer_mismatch')

    # Tampering the outer descriptor does not bless an altered embedding anchor.
    tampered = root/'tampered-package'
    shutil.copytree(destination, tampered)
    entrypoint = tampered/descriptor['entrypoint']
    entrypoint.write_bytes(entrypoint.read_bytes()+b'\n// changed anchor module')
    receipt = json.loads((tampered/'package.json').read_text())
    receipt['files'][descriptor['entrypoint']] = digest(entrypoint.read_bytes())
    (tampered/'package.json').write_text(json.dumps(receipt))
    try:
        verify_package(tampered, catalog)
    except ValueError as error:
        assert 'packaged_anchor_mismatch' in str(error)
    else:
        raise AssertionError('untrusted_descriptor_blessed_anchor')
    rejected.append('descriptor-cannot-bless-anchor')
    for invalid in (b'{"x":1,"x":2}', b'{"x":NaN}'):
        try:
            decode(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('ambiguous_json_accepted')
    assert (destination/descriptor['entrypoint']).read_bytes() == loader_source(descriptor['releaseSha256'])
    return dict(descriptor=descriptor, destination=destination, rejected=rejected,
                unchangedInput=hashes(runtime))


def verify_packaged_browser(page, base, package, plan, expected):
    destination, descriptor = package['destination'], package['descriptor']
    # This folder is intentionally nested: the loader must work under a Pages
    # project prefix and never resolve requests against the site's root.
    prefix = base+'nested/package/'
    module_url = prefix+descriptor['entrypoint']
    release_url = prefix+'runtime/'+descriptor['releaseSha256']+'/release.json'
    seen = []
    page.on('request', lambda request: seen.append(request.url) if request.url.startswith(prefix) else None)
    page.evaluate('''async url => {window.packaged = await import(url)}''', module_url)
    assert seen == [module_url], 'eager_packaged_payload_fetch'
    page.evaluate('''async () => {window.session = await packaged.openPackagedRuntime()}''')
    assert seen == [module_url, release_url]
    result = page.evaluate('''async plan => session.run(plan)''', plan)
    assert result == dict(expected, resolution='resolved')
    assert len([url for url in seen if url.endswith('.json.gz')]) == 2
    root = page.evaluate('''async () => session.discover()''')
    metric = plan['steps'][0]['request']['selectors'][0]['metric']
    summary = next(m for m in root['metrics'] if m['metric'] == metric)
    payload = destination/'runtime'/descriptor['releaseSha256']
    detail = json.loads(gzip.decompress((payload/summary['detail']['path']).read_bytes()))
    dimension = plan['steps'][0]['request']['selectors'][0]['dimension']
    shard = next(v for v in detail['views'] if v['dimension'] == dimension)['shards']['current']
    failures = []
    # Each attempt opens a fresh session of the SAME pinned release, avoiding a
    # previously loaded block masking a missing or incompatible artifact.
    for name, url, status, body, during_run in [
        ('missing-release',release_url,404,b'',False),
        ('corrupt-release',release_url,200,b'{}',False),
        ('oversize-release',release_url,200,b' '*(2*1024*1024+1),False),
        ('missing-detail',prefix+'runtime/'+descriptor['releaseSha256']+'/'+summary['detail']['path'],404,b'',True),
        ('corrupt-shard',prefix+'runtime/'+descriptor['releaseSha256']+'/'+shard['path'],200,b'corrupt',True),
    ]:
        def fail(route):
            route.fulfill(status=status, body=body, content_type='application/octet-stream')
        page.route(url, fail)
        failure = page.evaluate('''async ({plan,duringRun}) => {
          try {
            const fresh = await packaged.openPackagedRuntime();
            if(duringRun) await fresh.run(plan);
            return null;
          } catch(error) {return String(error.message)}
        }''', dict(plan=plan,duringRun=during_run))
        page.unroute(url, fail)
        assert failure, 'packaged_browser_accepted_failure:'+name
        # No alternate release, retry URL, source service or fallback number.
        recovered = page.evaluate('''async plan => {
          const fresh = await packaged.openPackagedRuntime();
          return fresh.run(plan);
        }''', plan)
        assert recovered == dict(expected, resolution='resolved')
        failures.append(dict(case=name,error=failure,retry='same_release_PASS'))
    assert all('/runtime/'+descriptor['releaseSha256']+'/' in url
               or url == module_url for url in seen)
    return dict(status='PASS', failures=failures, selectiveInitialBlocks=2,
                releaseSha256=descriptor['releaseSha256'])
