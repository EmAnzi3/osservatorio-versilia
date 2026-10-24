#!/usr/bin/env python3
"""General structured discovery/execution over A6; no language or policy inference."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from semantic_query_engine import ROOT, QueryEngine

MAX_STEPS = 32
MAX_PLAN_BYTES = 100_000


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_plan(plan):
    """Validate the bounded envelope without executing a component."""
    if not isinstance(plan, dict) or set(plan) != {'schemaVersion', 'steps'}:
        raise ValueError('invalid_plan_fields')
    if type(plan['schemaVersion']) is not int or plan['schemaVersion'] != 1:
        raise ValueError('unsupported_plan_schema')
    steps = plan['steps']
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError('plan_step_budget')
    serialized = encode(plan)
    if len(serialized.encode()) > MAX_PLAN_BYTES:
        raise ValueError('plan_byte_budget')
    ids = set()
    for step in steps:
        if not isinstance(step, dict) or set(step) != {'id', 'request'}:
            raise ValueError('invalid_step_fields')
        sid = step['id']
        if not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', sid) or sid in ids:
            raise ValueError('invalid_or_duplicate_step_id')
        ids.add(sid)
        if not isinstance(step['request'], dict):
            raise ValueError('structured_request_required')
    return serialized


class QueryWorkbench:
    """A6 alone decides eligibility. Discovery is a declaration, never a permit."""

    def __init__(self, catalog_path, *, repository_root=ROOT):
        self.engine = QueryEngine(catalog_path, repository_root=repository_root, layer='effective')

    def discover(self, metric=None):
        catalog = self.engine.catalog
        if metric is not None and metric not in catalog['metrics']:
            raise ValueError('unknown_metric')
        coverage = self.engine.coverage()
        entries = []
        for row in coverage:
            if metric is not None and row['metric'] != metric:
                continue
            meta = catalog['metrics'][row['metric']]['meta']
            entry = dict(metric=row['metric'], label=meta['label'], theme=meta['theme'],
                         declaration=copy.deepcopy(row['engine']))
            if metric is None:
                # Summary does not ship thousands of contexts on every discovery.
                entry = dict(metric=entry['metric'], label=entry['label'], theme=entry['theme'],
                             status=row['engine']['status'],
                             dimensionCount=len(row['engine'].get('dimensions', [])))
            entries.append(entry)
        return dict(schemaVersion=1, catalogSha256=self.engine.catalog_hash,
                    engineSha256=self.engine.module_hash,
                    workbenchSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    status='declarations_query_preconditions_apply',
                    towns=[dict(code=t['code'], name=t['name']) for t in catalog['towns']],
                    metrics=entries)

    def run(self, plan):
        """Execute independent evidence components. Never infer their relationship.

        An aggregate is an explicit A6 request, not a sum of step outputs.
        Correlation is one A6 request with two selectors and its own guards.
        """
        serialized = validate_plan(plan)
        # Validate the entire envelope before executing the first component.
        output = []
        for step in plan['steps']:
            response = self.engine.query(copy.deepcopy(step['request']))
            output.append(dict(id=step['id'], response=response))
        computed = sum(s['response']['status'] == 'computed' for s in output)
        return dict(schemaVersion=1, plan=copy.deepcopy(plan),
                    planSha256=hashlib.sha256(serialized.encode()).hexdigest(),
                    workbenchSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    catalogSha256=self.engine.catalog_hash,
                    status=('computed_components' if computed == len(output) else
                            'mixed_components' if computed else 'refused_components'),
                    interpretationStatus='not_assessed',
                    steps=output)

    def availability(self, metric, dimension, town):
        """Probe native current and declared history, never infer years from labels.

        Non-computable responses retain observations, missing flags and reasons.
        A refused series is not proof that the source has no historical data.
        """
        detail = self.discover(metric)['metrics'][0]['declaration']
        allowed = detail.get('operationsByDimension', {}).get(dimension, [])
        selector = dict(metric=metric, dimension=dimension, towns=[town])
        operation = 'lookup' if 'lookup' in allowed else 'observe'
        current = self.engine.query(dict(operation=operation, selectors=[selector]))
        historical = (self.engine.query(dict(operation='series', selectors=[selector]))
                      if 'series' in allowed else None)
        return dict(schemaVersion=1, catalogSha256=self.engine.catalog_hash,
                    selection=selector, current=current, history=historical,
                    historyStatus='query_executed' if historical is not None else 'not_declared',
                    defaultPeriodIsLatestVerified=False,
                    note='native default reference; historical refusal is not source unavailability')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--discover', action='store_true')
    mode.add_argument('--plan', type=Path)
    mode.add_argument('--availability', action='store_true')
    parser.add_argument('--metric')
    parser.add_argument('--dimension')
    parser.add_argument('--town')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.availability and not all((args.metric, args.dimension, args.town)):
        parser.error('--availability requires --metric, --dimension and --town')
    if args.metric and not (args.discover or args.availability):
        parser.error('--metric requires --discover or --availability')
    if (args.dimension or args.town) and not args.availability:
        parser.error('--dimension and --town require --availability')
    workbench = QueryWorkbench(args.catalog)
    result = (workbench.availability(args.metric, args.dimension, args.town) if args.availability
              else workbench.discover(args.metric) if args.discover
              else workbench.run(json.loads(args.plan.read_text())))
    body = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(body, encoding='utf-8')
    else:
        print(body, end='')


if __name__ == '__main__':
    main()
