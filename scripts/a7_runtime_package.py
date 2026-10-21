#!/usr/bin/env python3
"""Verify and atomically assemble an isolated A7 Pages artifact; never deploy it."""
import argparse
import gzip
import io
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from a7_query_workbench import QueryWorkbench, encode
from build_a7_query_runtime import PROFILES, READER, digest, recipes

ROOT_LIMIT = 2 * 1024 * 1024
PACKED_LIMIT = 8 * 1024 * 1024
RAW_LIMIT = 16 * 1024 * 1024
HASH = re.compile(r"[a-f0-9]{64}")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read_file(path, limit):
    require(path.is_file() and not path.is_symlink(), 'missing_or_unsafe_artifact')
    with path.open('rb') as handle:
        body = handle.read(limit + 1)
    require(len(body) <= limit, 'artifact_byte_budget')
    return body


def decode(body):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite_json_value')
    return json.loads(body.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)


def schema(value):
    require(isinstance(value, dict) and type(value.get('schemaVersion')) is int
            and value['schemaVersion'] == 1, 'incompatible_artifact_schema')


def verify_runtime(folder, catalog, *, include_reader=False):
    """Check the entire finite graph and its current producers, not source numerics.

    Declarations/recipes are derived from A6. No response is calculated here;
    the independent numerical and transport parity gates remain mandatory.
    """
    folder = Path(folder)
    require(folder.is_dir() and not folder.is_symlink(), 'unsafe_runtime_directory')
    release_bytes = read_file(folder/'release.json', ROOT_LIMIT)
    root = decode(release_bytes)
    schema(root)
    require(root.get('kind') == 'a7-selective-query-runtime', 'incompatible_runtime_kind')
    require(set(root) == {'schemaVersion','kind','catalogSha256','engineSha256','workbenchSha256',
            'builderSha256','readerSha256','envelope','scope','maxViewsPerMetric','towns','metrics'},
            'incompatible_runtime_fields')
    wb = QueryWorkbench(catalog)
    # A6's native early refusal exposes its complete producer/version header
    # without calculating observations. Derive this contract; never maintain a
    # second list of adapter, policy and eligibility fingerprints here.
    header = wb.engine.query({})
    producers = {key:value for key,value in header.items()
                 if key.endswith('Sha256') or key == 'engineVersion'}
    discovery = wb.discover()
    declarations = {r['metric']: r['engine'] for r in wb.engine.coverage()}
    for key, expected in dict(catalogSha256=wb.engine.catalog_hash,
                              engineSha256=wb.engine.module_hash,
                              workbenchSha256=digest((Path(__file__).parent/'a7_query_workbench.py').read_bytes()),
                              builderSha256=digest((Path(__file__).parent/'build_a7_query_runtime.py').read_bytes()),
                              readerSha256=digest(READER.read_bytes())).items():
        require(root.get(key) == expected, 'runtime_producer_mismatch:'+key)
    require(root.get('towns') == discovery['towns'], 'runtime_towns_mismatch')
    profiles = root.get('envelope', {}).get('profiles')
    require(isinstance(profiles, list) and profiles and len(set(profiles)) == len(profiles)
            and profiles == [p for p in PROFILES if p in profiles], 'invalid_runtime_profiles')
    require(encode(root['envelope']) == encode(dict(profiles=profiles, reference='native_default',
            comparison='all_seven_towns', history='one_town_native_series',
            ranking='all_seven_towns_descriptive_only' if 'ranking' in profiles else None,
            partialConsent=False, arbitraryRequests=False)), 'incompatible_runtime_envelope')
    limit = root.get('maxViewsPerMetric')
    require(limit is None or type(limit) is int and limit > 0, 'invalid_view_limit')
    require(root.get('scope') in ('all_metrics', 'explicit_subset'), 'invalid_runtime_scope')
    require(isinstance(root.get('metrics'), list) and root['metrics'], 'empty_runtime')
    summaries = {m['metric']: m for m in discovery['metrics']}
    ids = [m.get('metric') for m in root['metrics']]
    require(len(set(ids)) == len(ids) and set(ids) <= set(summaries), 'invalid_runtime_metrics')
    if root['scope'] == 'all_metrics':
        require(set(ids) == set(summaries) and limit is None, 'incomplete_full_runtime')
    towns = sorted(t['code'] for t in discovery['towns'])
    files = {'release.json': digest(release_bytes)}
    stats = dict(requests=0, views=0, rawBytes=0, gzipBytes=0,
                 maxShardRawBytes=0, maxShardGzipBytes=0, statuses=Counter(), profiles=Counter())

    def artifact(ref, *, shard=False):
        require(isinstance(ref, dict) and set(ref) == {'path','sha256','bytes','rawSha256','rawBytes'},
                'invalid_artifact_reference')
        require(isinstance(ref['sha256'], str) and HASH.fullmatch(ref['sha256'])
                and ref['path'] == ref['sha256']+'.json.gz'
                and isinstance(ref['rawSha256'], str) and HASH.fullmatch(ref['rawSha256'])
                and type(ref['bytes']) is int and 0 < ref['bytes'] <= PACKED_LIMIT
                and type(ref['rawBytes']) is int and 0 < ref['rawBytes'] <= RAW_LIMIT,
                'invalid_artifact_reference')
        packed = read_file(folder/ref['path'], ref['bytes'])
        require(len(packed) == ref['bytes'] and digest(packed) == ref['sha256'], 'artifact_integrity_mismatch')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as handle:
            raw = handle.read(ref['rawBytes']+1)
        require(len(raw) == ref['rawBytes'] and digest(raw) == ref['rawSha256'], 'artifact_integrity_mismatch')
        value = decode(raw)
        schema(value)
        files[ref['path']] = ref['sha256']
        stats['rawBytes'] += len(raw)
        stats['gzipBytes'] += len(packed)
        if shard:
            stats['maxShardRawBytes'] = max(stats['maxShardRawBytes'], len(raw))
            stats['maxShardGzipBytes'] = max(stats['maxShardGzipBytes'], len(packed))
        return value

    for summary in root['metrics']:
        metric = summary['metric']
        require(encode({k:v for k,v in summary.items() if k != 'detail'}) == encode(summaries[metric]), 'runtime_summary_mismatch')
        detail = artifact(summary['detail'])
        declaration = declarations[metric]
        require(set(detail) == {'schemaVersion','metric','declaration','views'}
                and detail['metric'] == metric and encode(detail['declaration']) == encode(declaration),
                'runtime_declaration_mismatch')
        dimensions = declaration.get('dimensions', [])[:limit]
        require(isinstance(detail['views'], list) and [v.get('dimension') for v in detail['views']] == dimensions,
                'runtime_views_mismatch')
        for view in detail['views']:
            dimension = view['dimension']
            operations = declaration['operationsByDimension'][dimension]
            require(set(view) == {'dimension','declaredOperations','shards'} and view['declaredOperations'] == operations,
                    'runtime_operations_mismatch')
            expected = {}
            for profile, request in recipes(metric, dimension, operations, towns, profiles):
                expected.setdefault(profile, []).append(request)
            require(isinstance(view['shards'], dict) and set(view['shards']) == set(expected), 'incomplete_runtime_graph')
            for profile, ref in view['shards'].items():
                shard = artifact(ref, shard=True)
                require(set(shard) == {'schemaVersion','metric','dimension','profile','entries'}
                        and (shard['metric'],shard['dimension'],shard['profile']) == (metric,dimension,profile),
                        'artifact_selection_mismatch')
                entries = shard['entries']
                require(isinstance(entries, list) and encode([e.get('request') for e in entries]) == encode(expected[profile]),
                        'runtime_request_scope_mismatch')
                for entry in entries:
                    response = entry.get('response')
                    require(set(entry) == {'request','response'} and isinstance(response, dict)
                            and encode(response.get('query')) == encode(entry['request'])
                            and response.get('catalogSha256') == root['catalogSha256']
                            and response.get('engineSha256') == root['engineSha256']
                            and response.get('status') in ('computed','not_computable'), 'runtime_response_identity_mismatch')
                    require(all(response.get(key) == value for key,value in producers.items()),
                            'runtime_response_producer_mismatch')
                    schema(response)
                    stats['requests'] += 1
                    stats['profiles'][profile] += 1
                    stats['statuses'][response['status']] += 1
            stats['views'] += 1
    measurement_bytes = read_file(folder/'measurement.json', ROOT_LIMIT)
    measurement = decode(measurement_bytes)
    expected_measurement = dict(stats, schemaVersion=1, catalogSha256=root['catalogSha256'],
        releaseSha256=digest(release_bytes), releaseBytes=len(release_bytes), metrics=len(ids), scope=root['scope'],
        limitation='transport/access measurement; not independent numerical certification')
    require(encode(measurement) == encode(expected_measurement), 'runtime_measurement_mismatch')
    files['measurement.json'] = digest(measurement_bytes)
    if include_reader:
        reader_bytes = read_file(folder/'reader.mjs', ROOT_LIMIT)
        require(digest(reader_bytes) == root['readerSha256'], 'packaged_reader_mismatch')
        files['reader.mjs'] = digest(reader_bytes)
    require({p.name for p in folder.iterdir()} == set(files), 'unreferenced_runtime_artifact')
    return root, dict(schemaVersion=1, releaseSha256=digest(release_bytes), files=files,
                      metrics=len(ids), views=stats['views'], requests=stats['requests'], scope=root['scope'])


def loader_source(release_hash):
    # These constants are part of the site artifact, never obtained from a query,
    # manifest field or caller-supplied base URL. The reader stays byte-identical.
    return READER.read_bytes() + ("\nconst expected = '"+release_hash+"';\n"
        + "const base = new URL('./runtime/'+expected+'/', import.meta.url);\n"
        + "export const releaseSha256 = expected;\n"
        + "export async function openPackagedRuntime() {\n"
        + "  if (base.origin !== location.origin) throw Error('same_origin_directory_required');\n"
        + "  const response = await fetch(new URL('release.json',base), {credentials:'omit',redirect:'error'});\n"
        + "  if (!response.ok || !response.body) throw Error('release_fetch_failed');\n"
        + "  const reader=response.body.getReader(); const chunks=[]; let size=0;\n"
        + "  try { while(true) { const {done,value}=await reader.read(); if(done)break;\n"
        + "    size+=value.length; if(size>2097152){await reader.cancel();throw Error('release_byte_budget');}\n"
        + "    chunks.push(value); } } finally {reader.releaseLock();}\n"
        + "  const bytes=new Uint8Array(size);let offset=0;\n"
        + "  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}\n"
        + "  return openRuntime(new TextDecoder('utf-8',{fatal:true}).decode(bytes),expected,base.href);\n"
        + "}\n").encode('utf-8')


def package_runtime(runtime_dir, catalog, output_dir):
    """Validate in private staging then rename once. Never replace a live package."""
    source, target = Path(runtime_dir).absolute(), Path(output_dir).absolute()
    require(not target.exists() and not target.is_symlink(), 'package_output_already_exists')
    require(source.is_dir() and not source.is_symlink(), 'unsafe_runtime_directory')
    canonical_source, canonical_target = source.resolve(), target.resolve()
    require(canonical_source != canonical_target and canonical_source not in canonical_target.parents
            and canonical_target not in canonical_source.parents,
            'overlapping_package_directories')
    target.parent.mkdir(parents=True, exist_ok=True)
    # Same parent => same filesystem for the single atomic directory rename.
    with tempfile.TemporaryDirectory(prefix='.a7-package-', dir=target.parent) as temporary:
        stage = Path(temporary)/'bundle'
        stage.mkdir()
        release_hash = digest(read_file(source/'release.json', ROOT_LIMIT))
        payload = stage/'runtime'/release_hash
        payload.mkdir(parents=True)
        for path in source.iterdir():
            require(path.is_file() and not path.is_symlink(), 'unsafe_runtime_artifact')
            # Check budgets before copying untrusted or accidentally large files.
            limit = PACKED_LIMIT if path.name.endswith('.json.gz') else ROOT_LIMIT
            (payload/path.name).write_bytes(read_file(path, limit))
        root, receipt = verify_runtime(payload, catalog)
        require(receipt['releaseSha256'] == release_hash, 'runtime_changed_during_staging')
        (payload/'reader.mjs').write_bytes(READER.read_bytes())
        require(digest((payload/'reader.mjs').read_bytes()) == root['readerSha256'], 'reader_changed_during_staging')
        module = loader_source(release_hash)
        entrypoint = 'a7-'+digest(module)+'.mjs'
        (stage/entrypoint).write_bytes(module)
        files = {p.relative_to(stage).as_posix(): digest(p.read_bytes()) for p in sorted(stage.rglob('*')) if p.is_file()}
        descriptor = dict(schemaVersion=1, kind='a7-atomic-runtime-package',
            releaseSha256=release_hash, entrypoint=entrypoint, catalogSha256=root['catalogSha256'], readerSha256=root['readerSha256'],
            packagerSha256=digest(Path(__file__).read_bytes()), files=files,
            scope=root['scope'], metrics=receipt['metrics'], views=receipt['views'], requests=receipt['requests'])
        descriptor_bytes = (encode(descriptor)+'\n').encode('utf-8')
        require(len(descriptor_bytes) <= PACKED_LIMIT, 'package_manifest_byte_budget')
        (stage/'package.json').write_bytes(descriptor_bytes)
        verify_package(stage, catalog)
        require(not target.exists() and not target.is_symlink(), 'package_output_already_exists')
        os.rename(stage, target)
    return descriptor



def verify_package(folder, catalog):
    """Validate a complete assembled artifact before handing it to Pages."""
    folder = Path(folder)
    require(folder.is_dir() and not folder.is_symlink(), 'unsafe_package_directory')
    descriptor = decode(read_file(folder/'package.json', PACKED_LIMIT))
    schema(descriptor)
    release_hash = descriptor.get('releaseSha256')
    require(isinstance(release_hash, str) and HASH.fullmatch(release_hash), 'invalid_packaged_release')
    require(not (folder/'runtime').is_symlink(), 'unsafe_package_directory')
    payload = folder/'runtime'/release_hash
    root, receipt = verify_runtime(payload, catalog, include_reader=True)
    require(receipt['releaseSha256'] == release_hash, 'packaged_release_mismatch')
    module = loader_source(release_hash)
    entrypoint = 'a7-'+digest(module)+'.mjs'
    require(read_file(folder/entrypoint, ROOT_LIMIT) == module, 'packaged_anchor_mismatch')
    expected_files = {'runtime/'+release_hash+'/'+n:h for n,h in receipt['files'].items()}
    expected_files[entrypoint] = digest(module)
    expected = dict(schemaVersion=1, kind='a7-atomic-runtime-package', releaseSha256=release_hash,
        entrypoint=entrypoint, catalogSha256=root['catalogSha256'], readerSha256=root['readerSha256'],
        packagerSha256=digest(Path(__file__).read_bytes()), files=expected_files,
        scope=root['scope'], metrics=receipt['metrics'], views=receipt['views'], requests=receipt['requests'])
    require(encode(descriptor) == encode(expected), 'package_descriptor_mismatch')
    allowed_directories = {'runtime', 'runtime/'+release_hash}
    for path in folder.rglob('*'):
        relative = path.relative_to(folder).as_posix()
        require(not path.is_symlink() and (relative in allowed_directories if path.is_dir()
                else relative in set(expected_files) | {'package.json'}), 'unexpected_package_member')
    return descriptor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package_runtime(args.runtime, args.catalog, args.output_dir), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
