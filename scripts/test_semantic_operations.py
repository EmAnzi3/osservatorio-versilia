#!/usr/bin/env python3
"""Regression checks for A6 operation-specific comparability decisions."""
import copy
import json
from pathlib import Path

from semantic_operations import assess, coverage_matrix

ROOT = Path(__file__).resolve().parents[1]


def obs(value=10, **changes):
    item = dict(metric='population', dimension='total', geography='046018', period='2026',
                unit='number', population='residents', definition='resident population',
                method='registry', frequency='annual', source='https://demo.istat.it/',
                evidence='fixture: methodological definition', value=value)
    item.update(changes)
    return item


def reject(op, rows, needle, **policy):
    report = assess(op, rows, policy=policy)
    assert not report['eligible'] and any(needle in r for r in report['reasons']), report


def main():
    pair = [obs(), obs(20, geography='046005')]
    assert assess('compare', pair)['eligible']
    for field in ('metric', 'dimension', 'unit', 'population', 'definition', 'method', 'frequency', 'period'):
        other = copy.deepcopy(pair)
        other[1][field] = 'different'
        reject('compare', other, f'incompatible:{field}')
    reject('compare', [obs(), obs(evidence='')], 'context_missing')
    reject('compare', [obs(), obs()], 'duplicate_observation')
    reject('compare', [obs(), obs(float('nan'), geography='046005')], 'invalid_value')
    reject('compare', [obs(), obs(True, geography='046005')], 'invalid_value')
    partial = [obs(), obs(None, geography='046005'), obs(20, geography='046006')]
    reject('compare', partial, 'partial_coverage_requires_opt_in')
    result = assess('compare', partial, policy={'allowPartial': True})
    assert result['eligible'] and result['coverage']['excludedIndices'] == [1]
    for period in ('2024/25', '2026-09', '2026-09-30', 'LR 35/2015 + DCR 47/2020'):
        reject('compare', [obs(period=period), obs(20, geography='046005', period='2024')], 'incompatible:period')
    change = [obs(10, period='2024'), obs(20, period='2026')]
    reject('absolute_change', change, 'explicit_unique_period_order_required')
    assert assess('absolute_change', change, policy={'periodOrder': ['2024', '2026']})['eligible']
    reject('relative_change', [obs(0, period='2024'), obs(period='2026')], 'zero_baseline', periodOrder=['2024', '2026'])
    reject('percentage_points', change, 'percentage_unit_required', periodOrder=['2024', '2026'])
    assert assess('percentage_points', [obs(50, unit='percent', period='2024'), obs(55, unit='percent')], policy={'periodOrder':['2024','2026']})['eligible']
    reject('benchmark_gap', pair, 'explicit_benchmark_comparability_required')
    assert assess('benchmark_gap', pair, policy={'benchmarkComparabilityEvidence': 'fixture: same definition'})['eligible']
    reject('weighted_ratio', pair, 'ratio_components_required', disjointPopulationEvidence='fixture')
    ratios = [obs(50, unit='percent', numerator=5, denominator=10, scale=100), obs(75, geography='046005', unit='percent', numerator=15, denominator=20, scale=100)]
    assert assess('weighted_ratio', ratios, policy={'disjointPopulationEvidence':'fixture: disjoint municipalities'})['eligible']
    bad = copy.deepcopy(ratios); bad[0]['numerator'] = 6
    reject('weighted_ratio', bad, 'ratio_components_inconsistent', disjointPopulationEvidence='fixture')
    reject('anomaly', pair + [obs(30, geography='046006')], 'reference_distribution_required')
    trend = change + [obs(30, period='2027')]
    reject('trend', trend, 'explicit_increasing_time_axis_required', periodOrder=['2024','2026','2027'])
    assert assess('trend', trend, policy={'periodOrder':['2024','2026','2027'],'timeAxis':[0,2,3]})['eligible']
    correlation = [obs(i, geography=str(i)) for i in (1,2,3)] + [obs(i*10, metric='income', unit='currency', definition='taxable mean income', population='taxpayers', geography=str(i)) for i in (3,1,2)]
    policy = dict(axis='municipalities', method='spearman', pairComparabilityEvidence='fixture: same municipal coverage and year; distinct universes disclosed')
    result = assess('correlation', correlation, policy=policy)
    assert result['eligible'] and 'association_not_causation' in result['warnings']
    constant = copy.deepcopy(correlation)
    for row in constant[:3]: row['value'] = 1
    reject('correlation', constant, 'constant_variable', **policy)
    bad = copy.deepcopy(correlation); bad[-1]['period'] = '2025'
    reject('correlation', bad, 'paired_period_mismatch', **policy)
    bad = copy.deepcopy(correlation); bad[-1]['frequency'] = 'monthly'
    reject('correlation', bad, 'paired_frequency_mismatch', **policy)
    temporal = [obs(i, period=str(2020+i)) for i in (1,2,3)] + [obs(i*10, metric='income', unit='currency', period=str(2020+i), geography='046005') for i in (1,2,3)]
    reject('correlation', temporal, 'paired_geography_mismatch', axis='periods', method='pearson', pairComparabilityEvidence='fixture')
    reject('anomaly', pair + [obs(30, geography='046006')], 'explicit_anomaly_rule_required', referenceDistributionEvidence='fixture')
    reject('correlation', correlation[:-1], 'insufficient_observations', **policy)
    for path in (ROOT/'data/site-data.json', ROOT/'dist/data/site-data.json'):
        if path.exists():
            catalog = json.loads(path.read_text())
            matrix = coverage_matrix(catalog)
            assert len(matrix) == len(catalog['metrics'])
            assert {x['metric'] for x in matrix} == set(catalog['metrics'])
            assert all(set(x['operations']) == set(json.loads((ROOT/'ci/semantic-operations-contract.json').read_text())['operations']) for x in matrix)
            # A real accepted comparison and a refused cross-period pairing.
            population = catalog['metrics']['population']
            selected = [r for r in population['rows'] if r.get('value') is not None][:2]
            descriptors = [obs(r['value'], geography=r['code'], period=str(population['meta']['year']),
                               source=population['sourceUrl'], evidence='catalog: population current rows; shared POSAS definition') for r in selected]
            assert assess('compare', descriptors)['eligible']
            income_period = str(catalog['metrics']['income']['meta']['year'])
            mismatch = copy.deepcopy(descriptors)
            mismatch[1]['period'] = income_period
            if income_period != descriptors[0]['period']:
                reject('compare', mismatch, 'incompatible:period')
            print(f'A6 operations coverage: {path.relative_to(ROOT)} · {len(matrix)} indicators; context readiness never inferred')
    print('A6 operations/comparability regressions PASS')


if __name__ == '__main__':
    main()
