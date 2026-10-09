#!/usr/bin/env python3
"""A6.2–3 eligibility guards; deliberately not the A6.4 calculation engine."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'ci/semantic-operations-contract.json'


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def reported_measurement(value):
    """Split a preserved source string; never substitute its bound as a value."""
    match = re.fullmatch(r'\s*([<>]?)\s*([+-]?\d+(?:[.,]\d+)?)\s*', value) if isinstance(value,str) else None
    if not match:
        raise ValueError('invalid_source_reported_measurement')
    return ({'':'exact','<':'less_than','>':'greater_than'}[match[1]], match[2])


def assess(operation, observations, *, policy=None):
    """Check explicit, source-evidenced observation descriptors without inference.

    Descriptor: metric, dimension, geography, period (opaque token), unit,
    population, definition, method, frequency, value, source, evidence.
    Evidence is a reviewable reference supporting methodological compatibility,
    not merely a reachable website. Geography is a canonical municipality code.
    """
    contract = json.loads(CONTRACT.read_text())
    if operation not in contract['operations']:
        raise ValueError(f'Unknown operation: {operation}')
    policy = policy or {}
    reasons, warnings, excluded = [], [], []
    spec = contract['operations'][operation]
    required = contract['descriptorFields'] + spec.get('descriptorFields',[])
    valid = []
    for index, obs in enumerate(observations):
        missing = [key for key in required if obs.get(key) is None or str(obs[key]).strip() == '']
        if missing:
            reasons.append(f'context_missing:{index}:{",".join(missing)}')
        if obs.get('notApplicable') or obs.get('dataUnavailable') or obs.get('value') is None:
            excluded.append(index)
        elif spec.get('valueDomain') == 'source_reported_measurement':
            try:
                qualifier, number = reported_measurement(obs['value'])
                if obs.get('valueKind') != 'source_reported_measurement' or obs.get('sourceValue') != obs['value'] or obs.get('reportedQualifier') != qualifier or obs.get('reportedNumber') != number:
                    raise ValueError('measurement_descriptor_mismatch')
                valid.append(obs)
            except ValueError:
                reasons.append(f'invalid_reported_measurement:{index}')
        elif not finite(obs['value']):
            reasons.append(f'invalid_value:{index}')
        else:
            valid.append(obs)
    if excluded:
        warnings.append('partial_coverage')
        if not policy.get('allowPartial'):
            reasons.append('partial_coverage_requires_opt_in')
    spec = contract['operations'][operation]
    if len(valid) < spec['minimumObservations']:
        reasons.append('insufficient_observations')
    for field in spec['equalFields']:
        if len({str(o.get(field)) for o in valid}) > 1:
            reasons.append(f'incompatible:{field}')
    identities = [(str(o.get('metric')), str(o.get('dimension')), str(o.get('geography')), str(o.get('period')), str(o.get('locality')) if operation == 'lookup' else None) for o in valid]
    if len(identities) != len(set(identities)):
        reasons.append('duplicate_observation')
    if operation in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        order = policy.get('periodOrder', [])
        periods = [str(o.get('period')) for o in valid]
        if len(periods) != len(set(periods)) or list(map(str, order)) != periods:
            reasons.append('explicit_unique_period_order_required')
        if operation in ('absolute_change', 'relative_change', 'percentage_points') and len(valid) != 2:
            reasons.append('exactly_two_observations_required')
        if operation == 'relative_change' and valid and valid[0]['value'] == 0:
            reasons.append('zero_baseline')
        if operation == 'percentage_points' and any(o.get('unit') != 'percent' for o in valid):
            reasons.append('percentage_unit_required')
        if operation == 'trend':
            axis = policy.get('timeAxis', [])
            if len(axis) != len(valid) or not all(finite(x) for x in axis) or any(b <= a for a, b in zip(axis, axis[1:])):
                reasons.append('explicit_increasing_time_axis_required')
    if operation == 'weighted_ratio':
        for i, obs in enumerate(valid):
            n, d, scale = obs.get('numerator'), obs.get('denominator'), obs.get('scale')
            if not finite(n) or not finite(d) or d <= 0 or not finite(scale) or scale <= 0:
                reasons.append(f'ratio_components_required:{i}')
            elif not math.isclose(n / d * scale, obs['value'], rel_tol=1e-6, abs_tol=1e-6):
                reasons.append(f'ratio_components_inconsistent:{i}')
        if len({str(o.get('scale')) for o in valid}) > 1:
            reasons.append('incompatible:scale')
        warnings.append('disjoint_populations_must_be_attested')
        if not policy.get('disjointPopulationEvidence'):
            reasons.append('disjoint_population_evidence_required')
    if operation == 'benchmark_gap':
        if len(valid) != 2 or not policy.get('benchmarkComparabilityEvidence'):
            reasons.append('explicit_benchmark_comparability_required')
    if operation == 'correlation':
        warnings.extend(['association_not_causation', 'ecological_inference', 'inspect_outliers_and_shared_denominators'])
        axis = policy.get('axis')
        if axis not in ('municipalities', 'periods'):
            reasons.append('explicit_analysis_axis_required')
        if policy.get('method') not in ('pearson', 'spearman'):
            reasons.append('explicit_correlation_method_required')
        groups = {}
        for obs in valid:
            groups.setdefault((obs.get('metric'), obs.get('dimension')), []).append(obs)
        if len(groups) != 2:
            reasons.append('exactly_two_selected_variables_required')
        paired = []
        for group in groups.values():
            for field in ('unit', 'population', 'definition', 'method', 'frequency') + (('period',) if axis == 'municipalities' else ('geography',)):
                if len({str(o.get(field)) for o in group}) > 1:
                    reasons.append(f'within_variable_incompatible:{field}')
            keys = [str(o.get('geography' if axis == 'municipalities' else 'period')) for o in group]
            if len(keys) != len(set(keys)):
                reasons.append('duplicate_pairing_key')
            paired.append(dict(zip(keys, group)))
        if len(paired) == 2:
            common = set(paired[0]) & set(paired[1])
            if set(paired[0]) != set(paired[1]) and not policy.get('allowPartial'):
                reasons.append('unaligned_pairing_keys')
            if set(paired[0]) != set(paired[1]):
                warnings.append('partial_pair_coverage')
            if len(common) < 3:
                reasons.append('insufficient_pairs')
            if len(common) < 10:
                warnings.append('small_sample_no_inferential_claim')
            for key in common:
                if axis == 'periods' and str(paired[0][key].get('geography')) != str(paired[1][key].get('geography')):
                    reasons.append('paired_geography_mismatch')
                if str(paired[0][key].get('frequency')) != str(paired[1][key].get('frequency')):
                    reasons.append('paired_frequency_mismatch')
                if str(paired[0][key].get('period')) != str(paired[1][key].get('period')):
                    reasons.append('paired_period_mismatch')
            for group in paired:
                if len({group[k]['value'] for k in common}) < 2:
                    reasons.append('constant_variable')
            if not policy.get('pairComparabilityEvidence'):
                reasons.append('pair_comparability_evidence_required')
            warnings.append('common_trends_and_autocorrelation' if axis == 'periods' else 'seven_towns_are_not_independent_sample_by_default')
    if operation in ('rank', 'anomaly'):
        warnings.append('rank_is_not_quality_or_policy_priority')
    if operation == 'anomaly':
        if not policy.get('referenceDistributionEvidence'):
            reasons.append('reference_distribution_required')
        if not policy.get('anomalyRule'):
            reasons.append('explicit_anomaly_rule_required')
    return {'eligible': not reasons, 'reasons': sorted(set(reasons)), 'warnings': sorted(set(warnings)),
            'coverage': {'requested': len(observations), 'usable': len(valid), 'excludedIndices': excluded},
            'operation': operation, 'formula': spec['formula'], 'observations': observations, 'policy': policy}


def coverage_matrix(catalog):
    """Discover every carrier; presence is not methodological/query readiness."""
    result = []
    def walk(node, path):
        if isinstance(node, dict):
            if 'years' in node and 'values' in node:
                yield {'path': path, 'kind': 'series', 'status': 'input_present' if node['years'] else 'empty_input'}
            for key, value in node.items():
                if 'benchmark' in key.lower() or key in ('benchmark', 'sexDimension', 'a3LabourDimensions', 'accountingSeries', 'parts', 'detailParts', 'ratioComponents', 'sourceBackedComponents', 'censusRatioComponents', 'normalized'):
                    yield {'path': f'{path}.{key}', 'kind': key, 'status': 'requires_adapter_and_context'}
                yield from walk(value, f'{path}.{key}')
        elif isinstance(node, list):
            for i, value in enumerate(node):
                yield from walk(value, f'{path}[{i}]')
    for key, metric in sorted(catalog['metrics'].items()):
        carriers = list(walk(metric, f'metrics.{key}'))
        result.append({'metric': key, 'primaryPeriod': str(metric['meta'].get('year')), 'primaryUnit': metric['meta'].get('unit', metric['meta'].get('summaryUnit')),
                       'operations': {name: 'requires_explicit_context' for name in json.loads(CONTRACT.read_text())['operations']},
                       'carriers': carriers})
    return result
