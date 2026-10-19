#!/usr/bin/env python3
"""Derived A3 acquisition, A6 declarations, A7 execution and actual static access.

No dimension-name matching, new indicator inventory or permission inference.
An evidence path witness proves access to that path, not the entire A3 dimension.
"""
import argparse
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from a7_query_workbench import QueryWorkbench, encode
from build_a7_query_runtime import PROFILES, READER, recipes
from build_territorial_dossier_evidence import portable_evidence
from enrichment_audit_matrix import build_matrix, validate_matrix
from semantic_question_suite import QUESTIONS, check_expected
from semantic_query_engine import SUPPORTED


def sha(body):
    return hashlib.sha256(body).hexdigest()


def read_artifact(folder, ref):
    if not re.fullmatch(r'[a-f0-9]{64}', ref['sha256']) or ref['path'] != ref['sha256'] + '.json.gz':
        raise ValueError('invalid_runtime_reference')
    packed = (folder / ref['path']).read_bytes()
    if len(packed) != ref['bytes'] or sha(packed) != ref['sha256']:
        raise ValueError('runtime_integrity')
    raw = gzip.decompress(packed)
    if len(raw) != ref['rawBytes'] or sha(raw) != ref['rawSha256']:
        raise ValueError('runtime_integrity')
    return json.loads(raw)


def path_pattern(pointer):
    # A3 structural detectors use one representative row; A6 uses exact rows.
    return '/'.join('*' if p.isdigit() else p for p in pointer.strip('/').split('/'))


def structural_path(row):
    evidence = row['evidence']
    # Only unambiguous same-payload paths. Route, companion and formula evidence
    # need a semantic linkage contract; never invent one by matching labels.
    match = re.fullmatch(r'structured:((?:[A-Za-z_][\w]*|\d+|\*)(?:\.(?:[A-Za-z_][\w]*|\d+|\*))*)', evidence)
    return path_pattern(match[1].replace('.', '/')) if match else None


def audit(catalog, registry, runtime=None):
    catalog, registry = Path(catalog), Path(registry)
    wb = QueryWorkbench(catalog)
    acquisition = build_matrix(json.loads(catalog.read_text()), json.loads(registry.read_text()))
    validate_matrix(acquisition, require_complete=True)
    declarations = {r['metric']: r['engine'] for r in wb.engine.coverage()}
    towns = sorted(wb.engine.codes)
    cases = json.loads(QUESTIONS.read_text())['questions']
    operation_proofs = defaultdict(Counter)
    # These are the original independent A6 expectations, never a routing table.
    for case in cases:
        response = wb.run(dict(schemaVersion=1, steps=[dict(id='probe', request=case['query'])]))['steps'][0]['response']
        errors = check_expected(response, case['expected'])
        if errors:
            raise AssertionError((case['id'], errors))
        operation_proofs[case['query']['operation']][response['status']] += 1

    actual = {}
    root = None
    witnesses = defaultdict(set)
    if runtime:
        runtime = Path(runtime)
        root = json.loads((runtime/'release.json').read_text())
        if (root['schemaVersion'] != 1 or root['kind'] != 'a7-selective-query-runtime'
                or root['catalogSha256'] != wb.engine.catalog_hash or root['engineSha256'] != wb.engine.module_hash
                or root['workbenchSha256'] != sha((Path(__file__).parent/'a7_query_workbench.py').read_bytes())
                or root['readerSha256'] != sha(READER.read_bytes())
                or root['builderSha256'] != sha((Path(__file__).parent/'build_a7_query_runtime.py').read_bytes())):
            raise ValueError('runtime_candidate_mismatch')
        for summary in root['metrics']:
            metric = summary['metric']
            detail = read_artifact(runtime, summary['detail'])
            if detail['metric'] != metric or detail['declaration'] != declarations[metric]:
                raise ValueError('runtime_declaration_mismatch')
            for view in detail['views']:
                for profile, ref in view['shards'].items():
                    shard = read_artifact(runtime, ref)
                    if (shard['metric'], shard['dimension'], shard['profile']) != (metric, view['dimension'], profile):
                        raise ValueError('runtime_selection_mismatch')
                    for entry in shard['entries']:
                        # Actual contents, not a promise inferred from a profile name.
                        response = portable_evidence(wb.engine.query(entry['request']))
                        if entry['response'] != response:
                            raise ValueError('runtime_native_parity_mismatch')
                        actual[encode(entry['request'])] = dict(profile=profile, status=response['status'],
                                                               reasons=response.get('reasons', []))
                        for observation in response.get('observations', []):
                            for evidence in observation.get('evidence', []):
                                if evidence.get('kind') == 'catalog_snapshot':
                                    for key, pointer in evidence.items():
                                        if key.endswith('Pointer') and isinstance(pointer, str):
                                            witnesses[metric].add(path_pattern(pointer))

    views, counts = [], Counter()
    for metric, declaration in sorted(declarations.items()):
        for dimension in declaration.get('dimensions', []):
            allowed = declaration['operationsByDimension'][dimension]
            generated = defaultdict(list)
            # Include all supported profiles, but do not materialize extra ones.
            for profile, request in recipes(metric, dimension, allowed, towns, PROFILES):
                generated[request['operation']].append(request)
            operations = []
            for operation in SUPPORTED:
                admitted = operation in allowed
                requests = generated[operation]
                entries = [actual[encode(q)] for q in requests if encode(q) in actual]
                state = ('not_inspected' if runtime is None else
                         'materialized' if requests and len(entries) == len(requests) else
                         'partly_materialized' if entries else 'not_materialized') if admitted else 'not_admitted'
                counts[state] += 1
                operations.append(dict(operation=operation, engine='conditional' if admitted else 'not_admitted',
                                       workbench='delegates_to_A6', static=state,
                                       requestScope='native_default_profiles_only' if requests else 'requires_explicit_request',
                                       transportedResponses=dict(Counter(e['status'] for e in entries)),
                                       publicGeneralExplorer='not_presented'))
            views.append(dict(metric=metric, dimension=dimension,
                              context=declaration['contextsByDimension'][dimension],
                              benchmarkScopes=declaration['benchmarkScopesByDimension'][dimension], operations=operations))

    rows = []
    for row in acquisition['rows']:
        result = dict(row)
        candidate = structural_path(row)
        prefix = f'metrics/{row["metricId"]}/' + candidate if candidate else None
        paths = sorted(p for p in witnesses[row['metricId']] if prefix and (p == prefix or p.startswith(prefix+'/')))
        result.update(accessEvidencePaths=paths, linkage=(
            'not_acquired' if row['state'] != 'ACQUIRED' else
            'catalog_path_witness_only' if paths else 'acquired_access_not_proven'),
            a6MetricRef=row['metricId'])
        rows.append(result)
    return dict(schemaVersion=1, catalogSha256=wb.engine.catalog_hash,
                registrySha256=sha(registry.read_bytes()),
                runtimeReleaseSha256=sha((runtime/'release.json').read_bytes()) if runtime else None,
                acquisitionSummary=acquisition['summary'], acquisition=rows, views=views,
                operationSummary=dict(counts), independentExpectations={k: dict(v) for k, v in sorted(operation_proofs.items())},
                linkageSummary=dict(Counter(r['linkage'] for r in rows)),
                limits=['Declarations are conditional, not permission for every selection.',
                        'A3 path witnesses do not prove full dimensional coverage; unlinked evidence remains explicitly unresolved.',
                        'Not admitted is an A6 boundary, not a claim that source data is absent.',
                        'Existing editorial public pilots are separate from the general explorer.',
                        'No source acquisition, causal interpretation or automatic policy ranking.'])


def markdown(report):
    lines = ['# A7 — accessibilità derivata', '',
             f'Catalogo SHA256: `{report["catalogSha256"]}`', '',
             '## Acquisizione A3', '',
             '| Stato | Coppie |', '| --- | ---: |']
    lines += [f'| {k.removeprefix("state_")} | {v} |' for k, v in report['acquisitionSummary'].items() if k.startswith('state_')]
    lines += ['', '## Operazioni per vista', '', '| Stato trasporto | Coppie vista/operazione |', '| --- | ---: |']
    lines += [f'| {k} | {v} |' for k, v in report['operationSummary'].items()]
    lines += ['', '## Prove indipendenti originali attraverso il workbench', '',
              '| Operazione | computed | not_computable |', '| --- | ---: | ---: |']
    lines += [f'| {k} | {v.get("computed", 0)} | {v.get("not_computable", 0)} |' for k, v in report['independentExpectations'].items()]
    lines += ['', '## Collegamento delle evidenze', '',
              'Il report JSON conserva tutte le coppie A3 e tutte le viste/operazioni A6, con contesti e benchmark.',
              'Un puntatore raggiunto attesta quel percorso: non certifica tutta una dimensione A3.',
              '**`acquired_access_not_proven` è un debito di collegamento da risolvere, non dato assente o fonte indisponibile.**', '']
    lines += [f'- {k}: {v}' for k, v in report['linkageSummary'].items()]
    lines += ['', *['- '+x for x in report['limits']], '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--runtime', type=Path)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    report = audit(args.catalog, args.registry, args.runtime)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'accessibility.json').write_text(encode(report)+'\n')
    (args.output_dir/'accessibility.md').write_text(markdown(report))
    print(encode({k: v for k, v in report.items() if k not in ('acquisition', 'views')}))


if __name__ == '__main__':
    main()
