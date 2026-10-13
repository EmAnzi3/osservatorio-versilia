"""Independent rational arithmetic and provenance checks, without engine calculators.

Checks every supplied response; it does not certify unexecuted queries or live
sources. Source-native reconciliation remains in the profile-specific suites.
"""
from collections import Counter
import base64
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import re


def rational(value):
    return Fraction(str(value))


def close(actual, expected):
    return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(
        actual, float(expected), rel_tol=1e-12, abs_tol=1e-9)


def correlation(xs, ys, method):
    if method == 'spearman':
        def ranked(values):
            return [Fraction(2 * sum(x < v for x in values) +
                             sum(x == v for x in values) + 1, 2) for v in values]
        xs, ys = ranked(xs), ranked(ys)
    else:
        xs, ys = list(map(rational, xs)), list(map(rational, ys))
    n = len(xs)
    cross = n * sum(x*y for x, y in zip(xs, ys)) - sum(xs)*sum(ys)
    dx = n*sum(x*x for x in xs)-sum(xs)**2
    dy = n*sum(y*y for y in ys)-sum(ys)**2
    return None if dx == 0 or dy == 0 else float(cross) / math.sqrt(float(dx*dy))


class MethodologicalVerifier:
    def __init__(self, catalog_path, root):
        self.root = Path(root)
        self.catalog_path = Path(catalog_path).resolve()
        self.bytes = {}
        self.json = {}

    def file(self, path):
        path = Path(path)
        path = path if path.is_absolute() else self.root / path
        if path not in self.bytes:
            self.bytes[path] = path.read_bytes()
        return path, self.bytes[path]

    def provenance(self, observation):
        errors = []
        for field in ('metric','dimension','geography','period','unit','population',
                      'definition','method','frequency','source','adapter'):
            if not observation.get(field): errors.append('descriptor_missing:'+field)
        if not observation.get('provenance'): errors.append('provenance_missing')
        for ref in observation.get('provenance', []):
            if not re.fullmatch('[0-9a-f]{64}', ref.get('sha256', '')):
                errors.append('provenance_hash_invalid')
            if not ref.get('path'): continue
            try:
                if ref.get('sha256Basis') == 'decoded_json_bytes':
                    if ref.get('encoding') != 'concatenate_ascii_base64_gzip_json' or not ref.get('parts'):
                        raise ValueError('Unknown decoded hash scope')
                    path = self.root / ref['path']
                    parts = []
                    for part in ref['parts']:
                        _, encoded = self.file(part['path'])
                        if hashlib.sha256(encoded).hexdigest() != part['sha256']:
                            errors.append('provenance_fragment_hash_mismatch:'+part['path'])
                        parts.append(encoded.strip())
                    body = gzip.decompress(base64.b64decode(b''.join(parts), validate=True))
                else:
                    path, body = self.file(ref['path'])
                if hashlib.sha256(body).hexdigest() != ref['sha256']:
                    errors.append('provenance_bytes_mismatch:'+ref['path'])
                # Decoded compact pointers have a separate scope, not JSON file bytes.
                if ref.get('valuePointer') and not ref.get('decodedScope') and (
                        path.suffix == '.json' or ref.get('sha256Basis') == 'decoded_json_bytes'):
                    if path not in self.json: self.json[path] = json.loads(body)
                    value = self.json[path]
                    for part in ref['valuePointer'].strip('/').split('/'):
                        part = part.replace('~1','/').replace('~0','~')
                        value = value[int(part)] if isinstance(value, list) else value[part]
            except (OSError, KeyError, IndexError, ValueError, TypeError):
                errors.append('provenance_reference_unresolved:'+str(ref.get('path')))
        return errors

    def verify(self, response):
        errors = []
        if response['status'] == 'not_computable':
            if not response.get('reasons') or response.get('result') is not None:
                errors.append('refusal_without_reason_or_with_result')
            return errors
        if response['status'] != 'computed': return ['unknown_response_status']
        if response.get('reasons'): errors.append('computed_with_refusal_reasons')
        obs = response['observations']
        for o in obs: errors.extend(self.provenance(o))
        usable = [o for o in obs if o.get('value') is not None and
                  not o.get('dataUnavailable') and not o.get('notApplicable')]
        op = response['query']['operation']; result = response['result']
        def check(actual, expected, name):
            if not close(actual, expected): errors.append('independent_arithmetic:'+name)
        if op in ('lookup','compare','series'):
            if result['observations'] != usable: errors.append('usable_observations_changed')
        elif op == 'rank':
            wanted = sorted(usable, key=lambda o:(-o['value'],o['geography']))
            for item, o in zip(result['ranking'], wanted):
                if item != dict(geography=o['geography'],value=o['value'],
                                rank=1+sum(v['value'] > o['value'] for v in usable)):
                    errors.append('independent_rank')
            if len(result['ranking']) != len(wanted): errors.append('rank_coverage')
        elif op in ('absolute_change','percentage_points','relative_change'):
            start, end = [rational(o['value']) for o in usable]
            check(result['value'], (end-start)/start*100 if op=='relative_change' else end-start, op)
        elif op == 'benchmark_gap':
            check(result['value'], rational(usable[0]['value'])-rational(usable[1]['value']), op)
        elif op == 'weighted_ratio':
            n=sum(rational(o['numerator']) for o in usable)
            d=sum(rational(o['denominator']) for o in usable)
            check(result['numerator'],n,'numerator');check(result['denominator'],d,'denominator')
            if d <= 0: errors.append('nonpositive_pooled_denominator')
            else: check(result['value'],n/d*rational(usable[0]['scale']),op)
            if result['geographies'] != [o['geography'] for o in usable]: errors.append('pooling_perimeter')
        elif op == 'trend':
            xs=list(map(rational,result['timeAxis']));ys=[rational(o['value']) for o in usable];n=len(xs)
            slope=(n*sum(x*y for x,y in zip(xs,ys))-sum(xs)*sum(ys))/(n*sum(x*x for x in xs)-sum(xs)**2)
            check(result['slope'],slope,op)
            if result['forecast'] is not False: errors.append('trend_presented_as_forecast')
        elif op == 'correlation':
            pairs=result['pairs'];xs=[p['x']['value'] for p in pairs];ys=[p['y']['value'] for p in pairs]
            check(result['coefficient'],correlation(xs,ys,result['method']),op)
            keys=[p['key'] for p in pairs]
            if len(set(keys)) != result['n'] or keys != result['pairedKeys']: errors.append('pair_sample')
            influence=result['leaveOneOut']
            if len(influence) != (len(keys) if len(keys)>=4 else 0): errors.append('influence_sample')
            if len({i['excludedKey'] for i in influence}) != len(influence): errors.append('duplicate_influence_key')
            for p in pairs:
                field='geography' if result['axis']=='municipalities' else 'period'
                if p['x'][field] != p['y'][field] or p['x']['period'] != p['y']['period']:
                    errors.append('pair_alignment')
            for item in influence:
                i=keys.index(item['excludedKey'])
                wanted=correlation(xs[:i]+xs[i+1:],ys[:i]+ys[i+1:],result['method'])
                if wanted is None:
                    if item['coefficient'] is not None: errors.append('constant_leave_one_out')
                else: check(item['coefficient'],wanted,'leave_one_out')
            for warning in ('association_not_causation','ecological_inference',
                            'inspect_outliers_and_shared_denominators','small_sample_no_inferential_claim'):
                if warning not in response['warnings']: errors.append('correlation_warning_missing:'+warning)
            if result['pValue'] is not None or result['confidenceInterval'] is not None:
                errors.append('unreviewed_statistical_inference')
        elif op == 'anomaly':
            xs=sorted(rational(o['value']) for o in usable)
            def q(p):
                z=(len(xs)-1)*p;i=z.numerator//z.denominator
                return xs[i] if z.denominator==1 else xs[i]*(i+1-z)+xs[i+1]*(z-i)
            q1,q3=q(Fraction(1,4)),q(Fraction(3,4));iqr=q3-q1
            for name,value in [('q1',q1),('q3',q3),('iqr',iqr),
                               ('lowerFence',q1-Fraction(3,2)*iqr),('upperFence',q3+Fraction(3,2)*iqr)]:
                check(result[name],value,name)
            if result['n'] != len(xs) or len(xs)<4 or iqr<=0: errors.append('anomaly_sample_or_variability')
            for item,o in zip(result['observations'],usable):
                v=rational(o['value'])
                classification='below_fence' if v<q1-Fraction(3,2)*iqr else 'above_fence' if v>q3+Fraction(3,2)*iqr else 'within_fences'
                if item != dict(geography=o['geography'],value=o['value'],classification=classification):
                    errors.append('anomaly_classification')
        else: errors.append('operation_without_independent_check:'+op)
        return sorted(set(errors))

    def suite(self, cases):
        rows=[dict(id=c['id'],errors=self.verify(c['actual']),operation=c['actual']['query']['operation']) for c in cases]
        return dict(status='FAIL' if any(r['errors'] for r in rows) else 'PASS',
                    checkedResponses=len(rows),operations=dict(Counter(r['operation'] for r in rows)),results=rows,
                    scope='Executed responses only; native source reconciliation belongs to adapter suites; no live-source certification')
