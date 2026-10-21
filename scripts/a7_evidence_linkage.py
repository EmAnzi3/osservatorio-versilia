"""Path-only lineage from existing A3 contracts to actual A6/A7 responses.

Never equate observations by their numerical value, labels or dimension names.
Compound requirements are conjunctive. Unhandled formula bridges stay explicit.
"""
import base64
import gzip
import hashlib
import json
import re
import zlib
from collections import defaultdict
from pathlib import Path

from enrichment_companion_evidence import _load_contract, _relationship_for
from enrichment_route_evidence import load_declared_payload, _find_ratio_pair, _compact_schema_evidence, _storage


def path_pattern(pointer):
    parts = pointer.strip('/').split('/')
    row = (1 if parts[:1] == ['rows'] else
           3 if len(parts) > 3 and parts[0] == 'metrics' and parts[2] == 'rows' else None)
    return '/'.join('*' if i == row and p.isdigit() else p for i, p in enumerate(parts))


def pointer(parts):
    return '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def expand(value, tokens, prefix=()):
    if not tokens:
        return [pointer(prefix)]
    key, *rest = tokens
    if key == '*':
        keys = list(value) if isinstance(value, dict) else range(len(value)) if isinstance(value, list) else []
    else:
        keys = [key]
    paths = []
    for k in keys:
        if isinstance(value, dict) and k in value:
            paths.extend(expand(value[k], rest, (*prefix, k)))
        elif isinstance(value, list) and str(k).isdigit() and int(k) < len(value):
            paths.extend(expand(value[int(k)], rest, (*prefix, k)))
    return paths


PATH = r'[A-Za-z_][\w]*(?:(?:\.(?:[A-Za-z_][\w]*|\d+|\*))|(?:\[\d+\]))*'
TOKEN = re.compile(rf'\s*(sum(?=\s*\()|{PATH}|\d+(?:\.\d+)?|[()+/×=])')


def operands(expression):
    """Recognize a closed path-expression grammar, without evaluating formulas."""
    result, tokens, offset = [], [], 0
    while offset < len(expression):
        if not expression[offset:].strip():
            break
        hit = TOKEN.match(expression, offset)
        if not hit:
            return None
        tokens.append(hit[1])
        offset = hit.end()
    position = 0
    def primary():
        nonlocal position
        if position >= len(tokens):
            raise ValueError('operand_required')
        token = tokens[position]
        position += 1
        if token in ('sum', '('):
            if token == 'sum':
                if position >= len(tokens) or tokens[position] != '(':
                    raise ValueError('sum_parenthesis_required')
                position += 1
            expression_terms()
            if position >= len(tokens) or tokens[position] != ')':
                raise ValueError('closing_parenthesis_required')
            position += 1
        elif re.fullmatch(r'\d+(?:\.\d+)?', token) or token in ('true', 'false'):
            pass
        elif re.fullmatch(PATH, token):
            result.append(re.sub(r'\[(\d+)\]', r'.\1', token).split('.'))
        else:
            raise ValueError('unexpected_token')
    def expression_terms():
        nonlocal position
        primary()
        while position < len(tokens) and tokens[position] in ('+', '/', '×', '='):
            position += 1
            primary()
    try:
        expression_terms()
    except ValueError:
        return None
    return result if result and position == len(tokens) else None


class AcquisitionReferences:
    def __init__(self, catalog, root):
        self.catalog, self.root = catalog, Path(root)
        self.contract = _load_contract(self.root)
        self.payloads = {}

    def formula_components(self, metric, relationship):
        """Use existing semantic edges, never recover a formula from equal values."""
        kind = relationship['relationship']
        supported = ('ratio_formula','normalized_companion_formula','series_change_formula',
                     'parts_ratio_formula','part_count_average_population_formula',
                     'target_fields_ratio_formula','canonical_field_ratio_formula')
        if kind not in supported or metric not in self.catalog['metrics']:
            return None
        year = str(self.catalog['metrics'][metric]['meta'].get('year', ''))
        if kind not in ('series_change_formula','parts_ratio_formula') and not re.fullmatch(r'\d{4}', year):
            return None
        requirements = [dict(namespace='catalog', operand='target value', paths=[f'metrics/{metric}/rows/*/value'])]
        components = []
        def selected_year(mode):
            return None if mode == 'metric_current' else str(int(year)+1) if mode == 'target_next_year' else year
        def add_fields(key, tokens):
            if key not in self.catalog['metrics']:
                return False
            paths = expand(self.catalog['metrics'][key], tokens)
            if not paths:
                return False
            requirements.append(dict(namespace='catalog', operand=key+':'+'.'.join(tokens),
                paths=sorted({path_pattern(f'metrics/{key}/'+p) for p in paths})))
            return True
        if kind == 'ratio_formula':
            components = [(relationship[k+'MetricId'], selected_year(relationship.get(k+'YearMode','target_year')))
                          for k in ('numerator','denominator')]
        elif kind == 'normalized_companion_formula':
            den = relationship['denominatorMetricId']
            components = [(metric, year), (relationship['normalizedMetricId'], year),
                          (den, selected_year(relationship.get('denominatorYearMode','target_year')))]
        elif kind == 'series_change_formula':
            components = [(relationship['companionMetricId'], str(relationship[k])) for k in ('startYear','endYear')]
        elif kind in ('parts_ratio_formula','part_count_average_population_formula'):
            key = relationship['companionMetricId'] if kind == 'parts_ratio_formula' else metric
            labels = (relationship['numeratorParts']+relationship['denominatorParts'] if kind == 'parts_ratio_formula'
                      else [relationship['numeratorPartLabel']])
            selector = relationship.get('partSelectorField','selectorLabel')
            field = relationship.get('partValueField','count') if kind == 'parts_ratio_formula' else relationship.get('partCountField','count')
            if key not in self.catalog['metrics']:
                return None
            for label in labels:
                paths = []
                for i,row in enumerate(self.catalog['metrics'][key].get('rows',[])):
                    found = [j for j,p in enumerate(row.get('parts',[])) if p.get(selector)==label and field in p]
                    if len(found)!=1:
                        return None
                    paths.append(path_pattern(f'metrics/{key}/rows/{i}/parts/{found[0]}/{field}'))
                if not paths:
                    return None
                requirements.append(dict(namespace='catalog',operand=label+':'+field,paths=sorted(set(paths))))
            if kind == 'part_count_average_population_formula':
                if relationship['populationYearMode']!='target_and_next_average':
                    return None
                components=[(relationship['companionMetricId'], year),
                            (relationship['companionMetricId'], str(int(year)+1))]
        elif kind == 'target_fields_ratio_formula':
            for field in relationship['targetNumeratorFields']:
                if not add_fields(metric,['rows','*',field]):
                    return None
            if not add_fields(relationship['companionMetricId'],['rows','*',relationship['companionDenominatorField']]):
                return None
        elif kind == 'canonical_field_ratio_formula':
            declared='data/site-data.json'
            if 'canonical' not in self.payloads:
                self.payloads['canonical']=(json.loads((self.root/declared).read_text()),declared)
            payload,_=self.payloads['canonical'];spec=relationship['canonicalNumerator']
            paths=expand(payload,[*spec['collectionPath'],'*',*spec['valuePath']])
            if not paths:
                return None
            requirements.append(dict(namespace='storage:'+declared,operand='canonicalNumerator',paths=paths))
            components=[(relationship['denominatorMetricId'],selected_year(relationship.get('denominatorYearMode','target_year')))]
        for key, period in components:
            if period is not None and not re.fullmatch(r'\d{4}', period):
                return None
            payload = self.catalog['metrics'][key]
            paths = []
            for index, row in enumerate(payload.get('rows', [])):
                if (period is None or str(payload['meta'].get('year')) == period) and row.get('value') is not None:
                    suffix = 'value'
                else:
                    series = row.get('series', {})
                    years = [str(y) for y in series.get('years', [])]
                    if period not in years or len(years) != len(series.get('values', [])):
                        return None
                    suffix = f'series/values/{years.index(period)}'
                paths.append(path_pattern(f'metrics/{key}/rows/{index}/{suffix}'))
            if not paths:
                return None
            requirements.append(dict(namespace='catalog', operand=f'{key}@{period or "metric_current"}',
                                     paths=sorted(set(paths)), **({'period':period} if period else {})))
        return dict(status='resolved_paths', requirements=requirements,
                    componentSelections=[dict(metric=k, period=p) for k,p in components],
                    companionContract=dict(relationship), scope='declared_component_access_not_formula_recomputation')

    def resolve(self, row):
        if row['state'] != 'ACQUIRED':
            return dict(status='not_acquired', requirements=[])
        metric, evidence = row['metricId'], row['evidence']
        via = None
        if evidence.startswith('structured:companion:'):
            relationship = _relationship_for(self.contract, metric, row['dimension'])
            if not relationship:
                return dict(status='unresolved_companion_contract', requirements=[])
            via = dict(relationship)
            if 'formula' in relationship['relationship']:
                bridge = self.formula_components(metric, relationship)
                if bridge is not None:
                    return bridge
                return dict(status='formula_bridge_not_proven', requirements=[], companionContract=via)
            metric = relationship.get('companionMetricId')
            prefix = f'structured:companion:{relationship["relationship"]}:{metric}:'
            if not metric or not evidence.startswith(prefix):
                return dict(status='unresolved_companion_reference', requirements=[], companionContract=via)
            evidence = 'structured:' + evidence[len(prefix):]
        payload = self.catalog['metrics'][metric]
        namespace = 'catalog'
        prefix = ['metrics', metric]
        if evidence.startswith('structured:storage:'):
            declared, separator, expression = evidence[len('structured:storage:'):].partition(':')
            if not separator:
                return dict(status='unresolved_storage_reference', requirements=[])
            if metric not in self.payloads:
                self.payloads[metric] = load_declared_payload(payload, self.root)
            payload, actual_path = self.payloads[metric]
            if payload is None or actual_path != declared:
                return dict(status='unresolved_storage_reference', requirements=[])
            namespace, prefix = 'storage:' + declared, []
            if expression.startswith('compactSchema:'):
                storage=_storage(self.catalog['metrics'][metric])
                if expression != _compact_schema_evidence(payload,storage,row['dimension']):
                    return dict(status='unresolved_compact_schema',requirements=[])
                schema=storage['compactSchema']
                roles=('periodAxis','territoryAxis','categoryRows','territoryTotals','regionalTotals')
                requirements=[dict(namespace=namespace,operand=role,paths=[pointer([schema[role]])])
                              for role in roles if isinstance(schema.get(role),str) and schema[role] in payload]
                return dict(status='resolved_paths',requirements=requirements,storageContract=dict(schema),
                            scope='shared_compact_payload_roles_not_semantic_adapter_mapping')
            # A3's route detector spells a same-parent ratio as path.num/den.
            # Reuse that exact detector before resolving the relative operand.
            if (re.fullmatch(r'[A-Za-z_]\w*(?:\.(?:[A-Za-z_]\w*|\d+))+/[A-Za-z_]\w*', expression)
                    and expression == _find_ratio_pair(payload)):
                left,right=expression.split('/')
                expression=left+' / '+left.rsplit('.',1)[0]+'.'+right
        elif evidence.startswith('structured:'):
            expression = evidence[len('structured:'):]
        else:
            return dict(status='unresolved_evidence_format', requirements=[])
        terms = operands(expression)
        if terms is None:
            return dict(status='expression_bridge_not_proven', requirements=[], **({'companionContract': via} if via else {}))
        requirements, missing = [], []
        for tokens in terms:
            # A3's first municipal row is a representative structural witness.
            # Expand category/year wildcards, preserving their exact identities.
            if tokens[:1] == ['rows'] and len(tokens) > 1 and tokens[1].isdigit():
                tokens = ['rows', '*', *tokens[2:]]
            paths = sorted({path_pattern(pointer(prefix) + ('/' if prefix else '') + p)
                            for p in expand(payload, tokens)})
            if not paths:
                missing.append('.'.join(tokens))
            requirements.append(dict(namespace=namespace, operand='.'.join(tokens), paths=paths))
        return dict(status='resolved_paths' if not missing else 'unresolved_operand',
                    requirements=requirements, missingOperands=missing,
                    **({'companionContract': via} if via else {}))


class WitnessIndex:
    def __init__(self, catalog_hash, catalog, root, storage_payloads=None):
        self.catalog_hash, self.root = catalog_hash, Path(root).resolve()
        self.catalog = catalog
        self.paths = defaultdict(dict)
        self.storage_payloads = storage_payloads or {}
        self.verified_storage = {}

    def storage_namespace(self, evidence):
        path = evidence.get('path')
        sha = evidence.get('sha256')
        if not isinstance(path, str) or not isinstance(sha, str):
            return None
        # A changed part list must not reuse a verification for an earlier
        # envelope that happened to declare the same aggregate hash/path.
        key = (path, sha, json.dumps(evidence.get('parts'), sort_keys=True, separators=(',', ':')))
        if key in self.verified_storage:
            return self.verified_storage[key]
        namespace = None
        for declared, payload in self.storage_payloads.items():
            if path != declared and not path.startswith(declared.rstrip('/') + '/'):
                continue
            try:
                parts = evidence.get('parts')
                if parts:
                    encoded = []
                    for part in parts:
                        file = (self.root/part['path']).resolve()
                        file.relative_to(self.root)
                        body = file.read_bytes()
                        if hashlib.sha256(body).hexdigest() != part['sha256']:
                            raise ValueError('part_hash')
                        encoded.append(body.strip())
                    raw = gzip.decompress(base64.b64decode(b''.join(encoded), validate=True))
                else:
                    file = (self.root/path).resolve()
                    file.relative_to(self.root)
                    raw = file.read_bytes()
                # Python equality equates True with 1; JSON type identity is
                # part of the lineage, even when hashes of source bytes pass.
                canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
                if hashlib.sha256(raw).hexdigest() == sha and canonical(json.loads(raw)) == canonical(payload):
                    namespace = 'storage:' + declared
            except (OSError, ValueError, KeyError, TypeError, EOFError, zlib.error):
                pass
        self.verified_storage[key] = namespace
        return namespace

    def add(self, response, proof):
        # A refused operation may contain observations, but is not an admitted
        # workbench result. Preserve its refusal in the probe ledger separately.
        if response['status'] != 'computed':
            return
        for observation in response.get('observations', []):
            if observation.get('dataUnavailable') or observation.get('notApplicable') or observation.get('value') is None:
                continue
            for evidence in observation.get('evidence', []):
                namespace = ('catalog' if evidence.get('sha256') == self.catalog_hash else
                             self.storage_namespace(evidence))
                if namespace is None:
                    continue
                for role in ('valuePointer', 'numeratorPointer', 'denominatorPointer'):
                    p = evidence.get(role)
                    if isinstance(p, str) and p.startswith('/'):
                        document = (self.catalog if namespace == 'catalog' else
                                    self.storage_payloads[namespace.removeprefix('storage:')])
                        tokens = [part.replace('~1', '/').replace('~0', '~') for part in p.strip('/').split('/')]
                        if expand(document, tokens):
                            period = str(observation.get('period', ''))
                            self.paths[namespace].setdefault((path_pattern(p), period),
                                dict(proof=proof, role=role, period=period, geography=observation.get('geography')))

    def match(self, reference, inspected=True):
        if not inspected:
            return dict(status='not_inspected', matched=[], unmatched=[])
        matches, unmatched = [], []
        for requirement in reference['requirements']:
            for required in requirement['paths']:
                found = [(p, proof) for (p, period), proof in self.paths[requirement['namespace']].items()
                         if (p == required or p.startswith(required + '/'))
                         and ('period' not in requirement or requirement['period'] == period)]
                if found:
                    p, proof = min(found, key=lambda item:(item[0], item[1]['period'], item[1]['proof']))
                    matches.append(dict(required=required, namespace=requirement['namespace'], path=p, **proof))
                else:
                    unmatched.append(dict(namespace=requirement['namespace'], path=required,
                                          **({'period':requirement['period']} if 'period' in requirement else {})))
        state = ('not_acquired' if reference['status'] == 'not_acquired' else
                 'unresolved_acquisition_reference' if reference['status'] != 'resolved_paths' else
                 'all_required_paths_witnessed' if matches and not unmatched else
                 'some_required_paths_witnessed' if matches else 'no_path_witness_in_probe_scope')
        return dict(status=state, matched=matches, unmatched=unmatched,
                    scope='path_evidence_only_not_complete_dimension')


def lineage_requests(declarations, towns, references=()):
    """Finite native probe envelope; no guessed periods or inferred pairings."""
    for metric, declaration in sorted(declarations.items()):
        for dimension in declaration['dimensions']:
            operations = declaration['operationsByDimension'][dimension]
            selector = dict(metric=metric, dimension=dimension)
            if 'compare' in operations:
                yield dict(operation='compare', selectors=[dict(selector, towns=towns)])
            else:
                point = 'lookup' if 'lookup' in operations else 'observe' if 'observe' in operations else None
                if point:
                    for town in towns:
                        yield dict(operation=point, selectors=[dict(selector, towns=[town])])
            if 'series' in operations:
                yield dict(operation='series', selectors=[dict(selector, towns=towns[:1])])
            if 'weighted_ratio' in operations:
                yield dict(operation='weighted_ratio', selectors=[dict(selector, towns=towns)])
            if 'benchmark_gap' in operations:
                for scope in declaration['benchmarkScopesByDimension'][dimension]:
                    for town in towns:
                        yield dict(operation='benchmark_gap', selectors=[dict(selector, towns=[town])], benchmark=scope)
    for reference in references:
        for component in reference.get('componentSelections', []):
            metric, period = component['metric'], component['period']
            operations = declarations[metric]['operationsByDimension'].get('total', [])
            selector = dict(metric=metric, dimension='total', **({'periods':[period]} if period is not None else {}))
            if 'compare' in operations:
                yield dict(operation='compare', selectors=[dict(selector, towns=towns)])
            else:
                point = 'lookup' if 'lookup' in operations else 'observe' if 'observe' in operations else None
                if point:
                    for town in towns:
                        yield dict(operation=point, selectors=[dict(selector, towns=[town])])
