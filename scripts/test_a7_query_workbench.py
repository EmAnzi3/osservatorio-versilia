#!/usr/bin/env python3
"""Canonical independent expectations and generated variants, not curated answers."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

from a7_query_workbench import QueryWorkbench, MAX_STEPS
from semantic_query_engine import ROOT, QueryEngine
from semantic_question_suite import QUESTIONS, check_expected


def plan(requests):
    return dict(schemaVersion=1, steps=[dict(id=f's{i}', request=q) for i, q in enumerate(requests)])


def verify(catalog):
    workbench = QueryWorkbench(catalog)
    reference = QueryEngine(catalog, layer='effective')
    manifest = json.loads(QUESTIONS.read_text())
    cases = manifest['questions']
    counts = dict(computed=0, refused=0)
    # Every independently reviewed A6 expectation, including missing data,
    # correlations, null denominators and intentional refusals, survives A7.
    for offset in range(0, len(cases), MAX_STEPS):
        batch = cases[offset:offset + MAX_STEPS]
        request = plan([c['query'] for c in batch])
        before = copy.deepcopy(request)
        result = workbench.run(request)
        assert request == before
        assert result['interpretationStatus'] == 'not_assessed'
        for case, output in zip(batch, result['steps']):
            response = output['response']
            errors = check_expected(response, case['expected'])
            assert not errors, (case['id'], errors)
            counts['computed' if response['status'] == 'computed' else 'refused'] += 1
        assert result == workbench.run(request), 'unstable replay'
    print(f'A7 workbench: {len(cases)} independent expectations PASS', file=sys.stderr, flush=True)

    discovery = workbench.discover()
    catalog_data = reference.catalog
    assert {m['metric'] for m in discovery['metrics']} == set(catalog_data['metrics'])
    assert len(discovery['metrics']) == len(catalog_data['metrics'])
    declared = {c['metric']: c['engine'] for c in reference.coverage()}
    dimension_count = 0
    for entry in discovery['metrics']:
        key = entry['metric']
        detail = workbench.discover(key)['metrics'][0]
        assert detail['declaration'] == declared[key]
        assert entry['theme'] == catalog_data['metrics'][key]['meta']['theme']
        dimension_count += entry['dimensionCount']
    print(f'A7 workbench: {len(declared)} declarations PASS', file=sys.stderr, flush=True)
    # These requests are generated from the catalog, not looked up in a list
    # of supported user questions. One and two territories, per carrier.
    towns = sorted(reference.codes)
    variants = []
    for key, declaration in declared.items():
        dims = declaration.get('dimensions', [])
        if not dims:
            continue
        for codes in ([towns[0]], towns[-2:]):
            variants.append(dict(operation='compare', selectors=[dict(metric=key, dimension=dims[0], towns=codes)]))
    for offset in range(0, len(variants), MAX_STEPS):
        batch = variants[offset:offset + MAX_STEPS]
        result = workbench.run(plan(batch))
        for request, output in zip(batch, result['steps']):
            assert output['response'] == reference.query(request), 'A7 changed raw A6 response'

    # Do not turn seven values into an aggregate, or consent into a default.
    case_by_id = {c['id']: c for c in cases}
    for cid in ('female_weighted', 'aligned_association', 'female_benchmark'):
        request = case_by_id[cid]['query']
        assert workbench.run(plan([request]))['steps'][0]['response'] == reference.query(request)
    good = dict(operation='compare', selectors=[dict(metric='population', towns=towns[:2])])
    bad = dict(operation='compare', selectors=[dict(metric='nonexistent')])
    mixed = workbench.run(plan([good, bad]))
    assert mixed['status'] == 'mixed_components'
    assert mixed['steps'][1]['response']['reasons'] == ['unknown_metric']
    assert 'coverage' not in mixed['steps'][1]['response'], 'fabricated optional field'
    assert 'allowPartial' not in mixed['steps'][0]['response']['query']
    assert workbench.run(plan([bad]))['status'] == 'refused_components'
    changed = copy.deepcopy(good); changed['selectors'][0]['towns'] = towns[-2:]
    first = workbench.run(plan([good]))
    second = workbench.run(plan([changed]))
    assert first['planSha256'] != second['planSha256']
    assert second['steps'][0]['response']['observations'][0]['geography'] == towns[-2]
    first['steps'][0]['response']['observations'][0]['value'] = -999
    assert workbench.run(plan([good]))['steps'][0]['response'] == reference.query(good)
    discovery['metrics'].clear()
    assert len(workbench.discover()['metrics']) == len(catalog_data['metrics'])
    for invalid in (
        dict(schemaVersion=1, steps=[]),
        dict(schemaVersion=True, steps=plan([good])['steps']),
        dict(schemaVersion=1, steps=plan([good])['steps'] * 2),
        dict(schemaVersion=1, steps=[dict(id='x', request='a natural-language question')]),
        dict(schemaVersion=1, steps=[dict(id=str(i), request=good) for i in range(MAX_STEPS + 1)]),
        dict(schemaVersion=1, steps=plan([good])['steps'], allowPartial=True),
    ):
        try:
            workbench.run(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid plan accepted')
    return dict(status='PASS', catalogSha256=reference.catalog_hash,
                canonicalManifestSha256=hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
                indicators=len(catalog_data['metrics']), declaredDimensions=dimension_count,
                independentCases=len(cases), **counts, generatedTerritorialVariants=len(variants),
                scope='structured discovery and evidence plans; no free-language or policy interpretation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.catalog)
    body = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(body, encoding='utf-8')
    print(body, end='')


if __name__ == '__main__':
    main()
