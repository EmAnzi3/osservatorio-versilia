#!/usr/bin/env python3
"""Experimental selective static transport of native A6 responses, not a second engine."""
import argparse
import gzip
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from a7_query_workbench import QueryWorkbench, encode
from build_territorial_dossier_evidence import portable_evidence

READER = Path(__file__).resolve().parents[1] / 'experiments/a7-query-runtime/reader.mjs'
DEFAULT_PROFILES = ('current', 'comparison', 'history')
PROFILES = (*DEFAULT_PROFILES, 'ranking')


def digest(body):
    return hashlib.sha256(body).hexdigest()


def recipes(metric, dimension, operations, towns, profiles=DEFAULT_PROFILES):
    """An explicit finite envelope, generated from declarations, never question IDs.

    Native default reference only. Missing periods, partial consent, arbitrary
    subsets, aggregates and associations are NOT silently reconstructed.
    """
    selector = dict(metric=metric, dimension=dimension)
    point = 'lookup' if 'lookup' in operations else 'observe' if 'observe' in operations else None
    if point and 'current' in profiles:
        for town in towns:
            yield 'current', dict(operation=point, selectors=[dict(selector, towns=[town])])
    if 'compare' in operations and 'comparison' in profiles:
        yield 'comparison', dict(operation='compare', selectors=[dict(selector, towns=towns)])
    if 'series' in operations and 'history' in profiles:
        for town in towns:
            yield 'history', dict(operation='series', selectors=[dict(selector, towns=[town])])
    if 'rank' in operations and 'ranking' in profiles:
        yield 'ranking', dict(operation='rank', selectors=[dict(selector, towns=towns)])


def build(catalog_path, output_dir, *, metrics=None, max_views=None, profiles=DEFAULT_PROFILES):
    started = time.perf_counter()
    if not profiles or len(set(profiles)) != len(profiles) or not set(profiles) <= set(PROFILES):
        raise ValueError('invalid_runtime_profiles')
    profiles = tuple(p for p in PROFILES if p in profiles)
    output_dir = Path(output_dir)
    # A new release must not retain stale content from an earlier catalog.
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('output_directory_must_be_empty')
    output_dir.mkdir(parents=True, exist_ok=True)
    workbench = QueryWorkbench(catalog_path)
    discovery = workbench.discover()
    known = {m['metric'] for m in discovery['metrics']}
    chosen = known if metrics is None else set(metrics)
    if not chosen or not chosen <= known:
        raise ValueError('unknown_or_empty_metric_scope')
    if max_views is not None and (type(max_views) is not int or max_views < 1):
        raise ValueError('invalid_view_limit')
    towns = sorted(t['code'] for t in discovery['towns'])
    stats = dict(requests=0, views=0, rawBytes=0, gzipBytes=0, maxShardRawBytes=0,
                 maxShardGzipBytes=0, statuses=Counter(), profiles=Counter())

    def store(value, *, shard=False):
        body = encode(value).encode('utf-8')
        packed = gzip.compress(body, mtime=0)
        if len(body) > 16 * 1024 * 1024 or len(packed) > 8 * 1024 * 1024:
            raise ValueError('runtime_artifact_byte_budget')
        key = digest(packed)
        (output_dir / (key+'.json.gz')).write_bytes(packed)
        stats['rawBytes'] += len(body)
        stats['gzipBytes'] += len(packed)
        if shard:
            stats['maxShardRawBytes'] = max(stats['maxShardRawBytes'], len(body))
            stats['maxShardGzipBytes'] = max(stats['maxShardGzipBytes'], len(packed))
        return dict(path=key+'.json.gz', sha256=key, bytes=len(packed),
                    rawSha256=digest(body), rawBytes=len(body))

    root = dict(schemaVersion=1, kind='a7-selective-query-runtime',
                catalogSha256=discovery['catalogSha256'], engineSha256=discovery['engineSha256'],
                workbenchSha256=discovery['workbenchSha256'],
                builderSha256=digest(Path(__file__).read_bytes()), readerSha256=digest(READER.read_bytes()),
                envelope=dict(profiles=list(profiles), reference='native_default',
                              comparison='all_seven_towns', history='one_town_native_series',
                              ranking='all_seven_towns_descriptive_only' if 'ranking' in profiles else None,
                              partialConsent=False, arbitraryRequests=False),
                scope='all_metrics' if metrics is None and max_views is None else 'explicit_subset',
                maxViewsPerMetric=max_views,
                towns=discovery['towns'], metrics=[])
    for summary in discovery['metrics']:
        metric = summary['metric']
        if metric not in chosen:
            continue
        detail = workbench.discover(metric)['metrics'][0]
        declaration = detail['declaration']
        views = []
        for dimension in declaration.get('dimensions', [])[:max_views]:
            operations = declaration.get('operationsByDimension', {}).get(dimension, [])
            groups = {p: [] for p in profiles}
            for profile, request in recipes(metric, dimension, operations, towns, profiles):
                # Reuse the approved catalog-location normalization: its SHA256
                # remains the identity; source snapshot paths/pointers are untouched.
                response = portable_evidence(workbench.engine.query(request))
                groups[profile].append(dict(request=request, response=response))
                stats['requests'] += 1
                stats['statuses'][response['status']] += 1
                stats['profiles'][profile] += 1
            views.append(dict(dimension=dimension, declaredOperations=operations,
                              shards={p: store(dict(schemaVersion=1, metric=metric, dimension=dimension,
                                                   profile=p, entries=entries), shard=True)
                                      for p, entries in groups.items() if entries}))
            stats['views'] += 1
        root['metrics'].append(dict(summary, detail=store(dict(schemaVersion=1, metric=metric,
                                                              declaration=declaration, views=views))))
    body = encode(root).encode('utf-8')
    if len(body) > 2 * 1024 * 1024:
        raise ValueError('runtime_release_byte_budget')
    (output_dir/'release.json').write_bytes(body)
    measurement = dict(stats, schemaVersion=1, catalogSha256=workbench.engine.catalog_hash,
                       releaseSha256=digest(body), releaseBytes=len(body),
                       metrics=len(root['metrics']),
                       scope=root['scope'], limitation='transport/access measurement; not independent numerical certification')
    (output_dir/'measurement.json').write_text(encode(measurement)+'\n', encoding='utf-8')
    # Timing is diagnostics returned to the caller/CLI, never a release artifact.
    return root, dict(measurement, seconds=time.perf_counter()-started)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--metric', action='append', help='Optional isolated measurement subset; omitted = entire effective catalog')
    p.add_argument('--max-views-per-metric', type=int, help='Explicit isolated measurement subset, never reported as full coverage')
    p.add_argument('--profile', action='append', choices=PROFILES,
                   help='Explicit transport profiles; omitted = original three, ranking is opt-in')
    args = p.parse_args()
    _, measurement = build(args.catalog, args.output_dir, metrics=args.metric, max_views=args.max_views_per_metric,
                           profiles=args.profile or DEFAULT_PROFILES)
    print(json.dumps(measurement, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
