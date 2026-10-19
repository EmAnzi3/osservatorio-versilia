#!/usr/bin/env python3
"""Conservative linkage and complete canonical accessibility inventory checks."""
import argparse
from collections import Counter
from pathlib import Path

from audit_a7_accessibility import audit, path_pattern, structural_path
from semantic_query_engine import SUPPORTED


def verify(catalog):
    report = audit(catalog, Path(catalog).parent/'source-registry.json')
    rows = report['acquisition']
    assert len(rows) == report['acquisitionSummary']['pairCount']
    assert len({(r['metricId'], r['dimension']) for r in rows}) == len(rows)
    assert len({v['metric'] for v in report['views']}) == report['acquisitionSummary']['publicMetricCount']
    for view in report['views']:
        assert {r['operation'] for r in view['operations']} == set(SUPPORTED)
        assert all(r['publicGeneralExplorer'] == 'not_presented' for r in view['operations'])
        # No runtime supplied: no declaration masquerades as materialization.
        assert all(r['static'] in ('not_inspected', 'not_admitted') for r in view['operations'])
    assert all(not r['accessEvidencePaths'] for r in rows)
    assert all(r['linkage'] == ('acquired_access_not_proven' if r['state'] == 'ACQUIRED' else 'not_acquired') for r in rows)
    assert structural_path(dict(evidence='structured:rows.0.sexDimension')) == 'rows/*/sexDimension'
    assert structural_path(dict(evidence='structured:rows.0.parts.15.series')) == 'rows/*/parts/15/series'
    assert path_pattern('/metrics/m/rows/0/parts/1/value') == path_pattern('/metrics/m/rows/6/parts/1/value')
    assert path_pattern('/metrics/m/rows/0/parts/1/value') != path_pattern('/metrics/m/rows/0/parts/2/value')
    assert path_pattern('/metrics/m/rows/0/totals/2024') != path_pattern('/metrics/m/rows/0/totals/2025')
    for evidence in ('structured:companion:history:x:rows.0.series', 'structured:rows.*.a / rows.*.b × 100', 'structured:route:page.html:data', 'text mentioning sex'):
        assert structural_path(dict(evidence=evidence)) is None
    totals = Counter()
    for counts in report['independentExpectations'].values():
        totals.update(counts)
    # Counts derived from original expectations, not hardcoded release totals.
    from semantic_question_suite import QUESTIONS
    import json
    assert sum(totals.values()) == len(json.loads(QUESTIONS.read_text())['questions'])
    assert all(op in report['independentExpectations'] for op in ('rank', 'benchmark_gap', 'absolute_change', 'relative_change', 'weighted_ratio', 'correlation'))
    print('A7 accessibility: A3 pairs, A6 view/operation inventory and independent workbench expectations PASS')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--catalog', type=Path, required=True)
    verify(p.parse_args().catalog)
