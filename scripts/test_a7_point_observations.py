#!/usr/bin/env python3
"""Point reads: independent A6 anchors, native selectors, missing and old guards."""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from a7_query_workbench import QueryWorkbench
from semantic_operations import assess
from semantic_question_suite import QUESTIONS, check_expected


def verify(catalog):
    w = QueryWorkbench(catalog)
    e = w.engine
    anchors = 0
    statuses = Counter()
    refusal_reasons = Counter()
    # Independently reviewed fixed compare expectations, not expected = actual.
    for case in json.loads(QUESTIONS.read_text())['questions']:
        q, expected = case['query'], case['expected']
        if q['operation'] != 'compare' or expected.get('status') != 'computed':
            continue
        response = e.query(q)
        assert not check_expected(response, expected), case['id']
        if response['interpretationLevel'] == 'category_lookup':
            continue  # Preserved and exercised below; not numeric point anchors.
        for obs in response['result']['observations']:
            if 'locality' in obs:
                continue
            selector = dict(metric=obs['metric'], dimension=obs['dimension'], towns=[obs['geography']])
            if 'periods' in q['selectors'][0]:
                selector['periods'] = [obs['period']]
            request = dict(operation='observe', selectors=[selector])
            point = e.query(request)
            assert point['status'] == 'computed', (case['id'], point['reasons'])
            assert point['result']['observations'] == [obs], case['id']
            # Compare was independently checked by the canonical suite; retain
            # exact source pointers, components and values, not just formatting.
            assert point['interpretationLevel'] == 'observation'
            assert point == e.query(request)
            anchors += 1
    print(f'Point parity with reviewed compare observations: {anchors}', flush=True)
    # Every declared numeric view, one explicit town; also seven towns for each
    # first numeric view. This is access coverage, not independent numeric QA.
    towns = sorted(e.codes)
    views = 0
    for entry in e.coverage():
        d = entry['engine']
        numeric = [dim for dim, ops in d.get('operationsByDimension', {}).items() if 'observe' in ops]
        for dim in numeric:
            point = e.query(dict(operation='observe', selectors=[dict(metric=entry['metric'], dimension=dim, towns=[towns[0]])]))
            statuses[point['status']] += 1
            refusal_reasons.update(point['reasons'])
            assert len(point['observations']) <= 1
            assert 'insufficient_observations' not in point['reasons'] or not point['observations'] or point['observations'][0]['value'] is None or point['observations'][0]['notApplicable'] or point['observations'][0]['dataUnavailable']
            views += 1
        if numeric:
            for town in towns:
                point = e.query(dict(operation='observe', selectors=[dict(metric=entry['metric'], dimension=numeric[0], towns=[town])]))
                assert len(point['observations']) <= 1
    q = dict(operation='observe', selectors=[dict(metric='population', dimension='total', towns=['046018'])])
    p = e.query(q)
    assert p['status'] == 'computed'
    # Independent POSAS record anchor (native frozen snapshot).
    native = json.loads((e.root/'data/source-snapshots/istat-demography-lotto-a-2026-08.json').read_text())
    obs = p['result']['observations'][0]
    records = native['posas']['towns']['Massarosa']
    assert obs['value'] == next(r['population'] for r in records if str(r['year']) == obs['period'])
    changed = copy.deepcopy(q); changed['operation'] = 'compare'
    assert 'insufficient_observations' in e.query(changed)['reasons']
    for update in (dict(periods=['2999']), dict(dimension='invented'), dict(towns=['046018','046018'])):
        bad_query = copy.deepcopy(q); bad_query['selectors'][0].update(update)
        assert e.query(bad_query)['status'] != 'computed'
    plan = dict(schemaVersion=1, steps=[dict(id='point',request=q)])
    assert w.run(plan)['steps'][0]['response'] == p
    for selector, reason in (
        (dict(metric='population'), 'observe_requires_one_explicit_municipality'),
        (dict(metric='population', towns=towns[:2]), 'observe_requires_one_explicit_municipality'),
        (dict(metric='population', towns=['046018'], periods=['2025','2026']), 'observe_requires_one_period'),
        (dict(metric='population', towns=['Versilia']), 'unknown_or_duplicate_geography'),
        (dict(metric='economyActivityAtlas', towns=['046018']), 'atlas_explicit_view_required'),
    ):
        out = e.query(dict(operation='observe', selectors=[selector]))
        assert out['status'] != 'computed' and reason in out['reasons'], out['reasons']
    zero = dict(obs, value=0)
    assert assess('observe', [zero])['eligible']
    for missing in (dict(obs, value=None), dict(obs, dataUnavailable=True), dict(obs, notApplicable=True)):
        assert not assess('observe', [missing], policy={'allowPartial':True})['eligible']
    assert not assess('observe', [obs,obs])['eligible']
    # Encoded classes/memberships remain category lookups, not numeric readings.
    categorical = w.discover('territorialClassification')['metrics'][0]['declaration']
    for dimension in categorical['dimensions']:
        assert 'observe' not in categorical['operationsByDimension'][dimension]
        selector = dict(metric='territorialClassification', dimension=dimension, towns=['046018'])
        refused = e.query(dict(operation='observe', selectors=[selector]))
        assert refused['status'] != 'computed'
        assert 'classification_category_arithmetic_or_association_not_supported' in refused['reasons']
        assert not refused['observations']
        compared = e.query(dict(operation='compare', selectors=[dict(selector, towns=towns)]))
        assert compared['status'] == 'computed' and compared['interpretationLevel'] == 'category_lookup'
        assert all(o['categoryLabel'] for o in compared['result']['observations'])
        assert not assess('observe', [compared['result']['observations'][0]])['eligible']
        availability = w.availability('territorialClassification', dimension, '046018')
        assert availability['current'] == refused
    bad = dict(obs); del bad['source']
    assert not assess('observe', [bad])['eligible']
    availability = w.availability('population', 'total', '046018')
    assert availability['current'] == p
    assert availability['history']['status'] == 'computed'
    assert availability['defaultPeriodIsLatestVerified'] is False
    availability['current']['observations'].clear()
    assert w.availability('population','total','046018')['current'] == p
    return dict(reviewedObservationParity=anchors, numericViewsProbed=views,
                oneTownViewStatuses=dict(statuses), refusalReasons=dict(refusal_reasons),
                limitations='view probes are not new independent numerical anchors; one town per view and seven towns per first numeric view, not all combinations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.catalog), indent=2))
