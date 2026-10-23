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
from build_a7_query_runtime import change_periods, CHANGE_OPERATIONS, PROFILES, READER, recipes
from build_territorial_dossier_evidence import portable_evidence
from enrichment_audit_matrix import build_matrix, validate_matrix
from semantic_question_suite import QUESTIONS, check_expected
from semantic_query_engine import SUPPORTED
from a7_evidence_linkage import AcquisitionReferences, WitnessIndex, lineage_requests, path_pattern


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


def structural_path(row):
    evidence = row['evidence']
    # Only unambiguous same-payload paths. Route, companion and formula evidence
    # need a semantic linkage contract; never invent one by matching labels.
    match = re.fullmatch(r'structured:((?:[A-Za-z_][\w]*|\d+|\*)(?:\.(?:[A-Za-z_][\w]*|\d+|\*))*)', evidence)
    return path_pattern(match[1].replace('.', '/')) if match else None


def artifact_capabilities(site, catalog_hash):
    """Prepared UI scope is distinct from an actually published/live interface."""
    if site is None:
        return set(), None
    from a7_explorer_release import validate_explorer
    site = Path(site)
    proof = validate_explorer(lambda path: (site/path).read_bytes(), full=True)
    receipt = json.loads((site/'explorer-preview.json').read_text())
    folder = site/'chiedi'/receipt['graph']/'package/runtime'/receipt['releaseSha256']
    root = json.loads((folder/'release.json').read_text())
    if root['catalogSha256'] != catalog_hash:
        raise ValueError('interface_catalog_mismatch')
    capabilities = set()
    towns = sorted(t['code'] for t in root['towns'])
    for summary in root['metrics']:
        detail = read_artifact(folder, summary['detail'])
        for view in detail['views']:
            for profile, request in recipes(summary['metric'], view['dimension'], view['declaredOperations'], towns, root['envelope']['profiles'],
                                            benchmark_scopes=detail['declaration']['benchmarkScopesByDimension'][view['dimension']],
                                            change_periods_by_town=view.get('changePeriodsByTown')):
                if profile in view['shards'] and (profile in ('current', 'comparison', 'history', 'ranking')
                        or profile == 'benchmark' and receipt.get('interfaceVersion', 1) >= 2
                        or profile == 'aggregation' and receipt.get('interfaceVersion', 1) >= 3
                        or profile == 'changes' and receipt.get('interfaceVersion', 1) >= 4
                        or profile == 'trends' and receipt.get('interfaceVersion', 1) >= 6):
                    # Older interfaces cannot present these profiles. Transport alone proves no UI access.
                    capabilities.add((summary['metric'],view['dimension'],request['operation']))
    return capabilities, proof


def replay_associations(wb, runtime, root):
    """Verify the graph and replay only its explicit binary selections in A6."""
    if 'associationPlan' not in root:
        return
    from a7_runtime_package import verify_runtime
    verify_runtime(runtime, wb.engine.path, include_reader=(Path(runtime)/'reader.mjs').exists())
    index = root['associationPlan']
    for step, entry in zip(index['plan']['steps'], index['entries']):
        shard = read_artifact(runtime, entry['artifact'])
        response = portable_evidence(wb.engine.query(step['request']))
        if shard['response'] != response:
            raise ValueError('runtime_native_parity_mismatch')
        yield step, response


def audit(catalog, registry, runtime=None, *, site=None):
    catalog, registry = Path(catalog), Path(registry)
    wb = QueryWorkbench(catalog)
    acquisition = build_matrix(json.loads(catalog.read_text()), json.loads(registry.read_text()))
    validate_matrix(acquisition, require_complete=True)
    declarations = {r['metric']: r['engine'] for r in wb.engine.coverage()}
    towns = sorted(wb.engine.codes)
    resolver = AcquisitionReferences(wb.engine.catalog, wb.engine.root)
    references = [resolver.resolve(row) for row in acquisition['rows']]
    storage = {path: payload for payload, path in resolver.payloads.values() if path and payload is not None}
    native_index = WitnessIndex(wb.engine.catalog_hash, wb.engine.catalog, wb.engine.root, storage)
    static_index = WitnessIndex(wb.engine.catalog_hash, wb.engine.catalog, wb.engine.root, storage)
    probes = {}
    def probe(request):
        key = sha(encode(request).encode())
        if key in probes:
            return key
        response = wb.run(dict(schemaVersion=1, steps=[dict(id='probe', request=request)]))['steps'][0]['response']
        probes[key] = dict(request=request, origin='declaration_probe', status=response['status'], reasons=response.get('reasons', []),
                           responseSha256=sha(encode(portable_evidence(response)).encode()))
        native_index.add(response, key)
        return key
    cases = json.loads(QUESTIONS.read_text())['questions']
    operation_proofs = defaultdict(Counter)
    # These are the original independent A6 expectations, never a routing table.
    for case in cases:
        response = wb.run(dict(schemaVersion=1, steps=[dict(id='probe', request=case['query'])]))['steps'][0]['response']
        errors = check_expected(response, case['expected'])
        if errors:
            raise AssertionError((case['id'], errors))
        operation_proofs[case['query']['operation']][response['status']] += 1
        key = sha(encode(case['query']).encode())
        probes[key] = dict(request=case['query'], origin='original_independent_case', status=response['status'], reasons=response.get('reasons', []),
                           responseSha256=sha(encode(portable_evidence(response)).encode()))
        native_index.add(response, key)
    for request in lineage_requests(declarations, towns, references):
        probe(request)

    actual = {}
    association_selections = []
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
                        response = portable_evidence(wb.run(dict(schemaVersion=1,
                            steps=[dict(id='probe',request=entry['request'])]))['steps'][0]['response'])
                        if entry['response'] != response:
                            raise ValueError('runtime_native_parity_mismatch')
                        key = sha(encode(entry['request']).encode())
                        response_hash = sha(encode(response).encode())
                        if key in probes and probes[key]['responseSha256'] != response_hash:
                            raise ValueError('non_reproducible_native_response')
                        probes.setdefault(key,dict(request=entry['request'], origin='runtime_replay',status=response['status'],
                            reasons=response.get('reasons',[]),responseSha256=response_hash))
                        native_index.add(response,key)
                        actual[encode(entry['request'])] = dict(profile=profile, status=response['status'],
                                                               reasons=response.get('reasons', []),
                                                               responseSha256=response_hash)
                        static_index.add(response, sha(encode(entry['request']).encode()))
                        for observation in response.get('observations', []):
                            for evidence in observation.get('evidence', []):
                                if evidence.get('kind') == 'catalog_snapshot':
                                    for key, pointer in evidence.items():
                                        if key.endswith('Pointer') and isinstance(pointer, str):
                                            witnesses[metric].add(path_pattern(pointer))

        if 'associationPlan' in root:
            # A pair-specific transport proof never promotes all correlations of
            # either view, nor claims an interface control that does not exist.
            for step, response in replay_associations(wb, runtime, root):
                request = step['request']
                key = sha(encode(request).encode())
                response_hash = sha(encode(response).encode())
                if key in probes and probes[key]['responseSha256'] != response_hash:
                    raise ValueError('non_reproducible_native_response')
                probes.setdefault(key, dict(request=request, origin='explicit_association_plan',
                    status=response['status'], reasons=response.get('reasons', []), responseSha256=response_hash))
                native_index.add(response, key)
                static_index.add(response, key)
                actual[encode(request)] = dict(profile='association', status=response['status'],
                    reasons=response.get('reasons', []), responseSha256=response_hash)
                association_selections.append(dict(id=step['id'], request=request, requestSha256=key,
                    static='materialized_exact_request', nativeStatus=response['status'],
                    reasons=response.get('reasons', []), artifactGeneralExplorer='not_presented',
                    publicGeneralExplorer='publication_not_inspected'))
                for observation in response.get('observations', []):
                    for evidence in observation.get('evidence', []):
                        if evidence.get('kind') == 'catalog_snapshot':
                            for field, pointer in evidence.items():
                                if field.endswith('Pointer') and isinstance(pointer, str):
                                    witnesses[observation['metric']].add(path_pattern(pointer))

    interface, interface_proof = artifact_capabilities(site, wb.engine.catalog_hash)
    views, counts = [], Counter()
    for metric, declaration in sorted(declarations.items()):
        for dimension in declaration.get('dimensions', []):
            allowed = declaration['operationsByDimension'][dimension]
            generated = defaultdict(list)
            # Include all supported profiles, but do not materialize extra ones.
            for profile, request in recipes(metric, dimension, allowed, towns, PROFILES,
                                            benchmark_scopes=declaration['benchmarkScopesByDimension'][dimension],
                                            change_periods_by_town=change_periods(wb, metric, dimension, allowed, towns)):
                generated[request['operation']].append(request)
            trend_keys = [probe(q) for q in generated['trend']]
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
                                       **({'nativeScopeProbe': dict(
                                           scope='one_town_full_native_series_ols_no_forecast',
                                           proofs=trend_keys,
                                           statuses=dict(Counter(probes[k]['status'] for k in trend_keys)),
                                           reasons=dict(Counter(reason for k in trend_keys for reason in probes[k]['reasons'])))}
                                          if operation == 'trend' and admitted else {}),
                                       requestScope=('one_town_full_native_series_ols_no_forecast' if operation == 'trend'
                                                     else 'all_seven_towns_native_descriptive_order' if operation == 'rank'
                                                     else 'all_seven_towns_native_weighted_ratio' if operation == 'weighted_ratio'
                                                     else 'one_town_declared_tuscany_italy_native_default' if operation == 'benchmark_gap'
                                                     else 'one_town_first_last_native_series_periods' if operation in CHANGE_OPERATIONS
                                                     else 'native_default_profiles_only') if requests else 'requires_explicit_request',
                                       transportedResponses=dict(Counter(e['status'] for e in entries)),
                                       publicGeneralExplorer='publication_not_inspected',
                                       artifactGeneralExplorer=('not_inspected' if site is None else
                                           'not_admitted' if not admitted else
                                           'prepared_native_defaults' if (metric,dimension,operation) in interface else
                                           'not_materialized')))
            views.append(dict(metric=metric, dimension=dimension,
                              context=declaration['contextsByDimension'][dimension],
                              benchmarkScopes=declaration['benchmarkScopesByDimension'][dimension], operations=operations))

    rows = []
    for row, reference in zip(acquisition['rows'], references):
        result = dict(row)
        candidate = structural_path(row)
        prefix = f'metrics/{row["metricId"]}/' + candidate if candidate else None
        paths = sorted(p for p in witnesses[row['metricId']] if prefix and (p == prefix or p.startswith(prefix+'/')))
        result.update(accessEvidencePaths=paths, linkage=(
            'not_acquired' if row['state'] != 'ACQUIRED' else
            'catalog_path_witness_only' if paths else 'acquired_access_not_proven'),
            a6MetricRef=row['metricId'])
        result.update(acquisitionReference=reference,
                      workbenchAccess=native_index.match(reference),
                      staticAccess=static_index.match(reference, inspected=runtime is not None))
        if (result['staticAccess']['status'] == 'all_required_paths_witnessed'
                and result['workbenchAccess']['status'] != 'all_required_paths_witnessed'):
            raise AssertionError('static_witness_missing_from_workbench_replay')
        rows.append(result)
    return dict(schemaVersion=3, catalogSha256=wb.engine.catalog_hash,
                implementationSha256={name: sha((Path(__file__).parent/name).read_bytes()) for name in
                                      ('audit_a7_accessibility.py','a7_evidence_linkage.py','a7_query_workbench.py','semantic_query_engine.py')},
                companionContractSha256=sha((wb.engine.root/'data/enrichment-companion-contract.json').read_bytes()),
                registrySha256=sha(registry.read_bytes()),
                runtimeReleaseSha256=sha((runtime/'release.json').read_bytes()) if runtime else None,
                interfaceArtifact=interface_proof,
                interfaceSummary=dict(Counter(o['artifactGeneralExplorer'] for v in views for o in v['operations'])),
                acquisitionSummary=acquisition['summary'], acquisition=rows, views=views,
                operationSummary=dict(counts), independentExpectations={k: dict(v) for k, v in sorted(operation_proofs.items())},
                linkageSummary=dict(Counter(r['linkage'] for r in rows)),
                acquisitionReferenceSummary=dict(Counter(r['acquisitionReference']['status'] for r in rows)),
                workbenchAccessSummary=dict(Counter(r['workbenchAccess']['status'] for r in rows)),
                staticAccessSummary=dict(Counter(r['staticAccess']['status'] for r in rows)),
                nativeProbes=probes,
                associationSelections=association_selections,
                associationScope=('not_inspected' if runtime is None else
                                  'explicit_plan_only' if root.get('associationPlan') else 'not_materialized'),
                staticProbes={sha(k.encode()): dict(request=json.loads(k), **v) for k, v in actual.items()},
                trendProbeSummary=dict(Counter(probes[k]['status'] for v in views for o in v['operations']
                    for k in o.get('nativeScopeProbe', {}).get('proofs', []))),
                nativeProbeSummary=dict(Counter(p['status'] for p in probes.values())),
                limits=['Declarations are conditional, not permission for every selection.',
                        'A3 path witnesses do not prove full dimensional coverage; unlinked evidence remains explicitly unresolved.',
                        'Not admitted is an A6 boundary, not a claim that source data is absent.',
                        'Prepared interface controls do not attest publication or every browser combination; publication is not inspected by this offline audit.',
                        'Existing editorial public pilots are separate from the general explorer.',
                        'No source acquisition, causal interpretation or automatic policy ranking.',
                        'Trend scope probes cover one request per declared view and town, full native series, no partial opt-in or forecast; refusals are preserved. Other scopes and pairings remain unproven.',
                        'Native lineage probes are finite: declared current comparisons, first-town native history, weighted ratios and declared benchmarks, plus original independent cases.',
                        'When supplied, every transported response is also replayed through the workbench and included in the native ledger.',
                        'Path witnesses prove neither an entire A3 dimension nor semantic equivalence of companion formulas.',
                        'Legacy linkageSummary concerns only simple catalog paths in static responses; use separate workbenchAccess/staticAccess for resolved compound requirements.'])


def markdown(report):
    lines = ['# A7 — accessibilità derivata', '',
             f'Catalogo SHA256: `{report["catalogSha256"]}`', '',
             '## Acquisizione A3', '',
             '| Stato | Coppie |', '| --- | ---: |']
    lines += [f'| {k.removeprefix("state_")} | {v} |' for k, v in report['acquisitionSummary'].items() if k.startswith('state_')]
    lines += ['', '## Operazioni per vista', '', '| Stato trasporto | Coppie vista/operazione |', '| --- | ---: |']
    lines += [f'| {k} | {v} |' for k, v in report['operationSummary'].items()]
    lines += ['', '## Associazioni: selezioni esplicite', '',
              f'Perimetro trasporto: `{report.get("associationScope", "not_inspected")}`.',
              'Sono componenti del solo piano ispezionato, non tutte le coppie ammesse dal motore.',
              'Nessun controllo pubblico di associazione è attestato da questo trasporto.',
              '', '| Esito nativo | Componenti pianificate |', '| --- | ---: |']
    lines += [f'| {k} | {v} |' for k, v in Counter(
        row['nativeStatus'] for row in report.get('associationSelections', [])).items()]
    lines += ['', '## Prove indipendenti originali attraverso il workbench', '',
              '| Operazione | computed | not_computable |', '| --- | ---: | ---: |']
    lines += [f'| {k} | {v.get("computed", 0)} | {v.get("not_computable", 0)} |' for k, v in report['independentExpectations'].items()]
    lines += ['', '## Trend: perimetro nativo verificato', '',
              'Una richiesta per vista dichiarata e Comune, serie nativa completa; nessun consenso implicito o previsione.',
              'Le dichiarazioni restano condizionali. Gli esiti sono prove di accesso al motore, non di trasporto o interfaccia.',
              '', '| Esito | Richieste |', '| --- | ---: |']
    lines += [f'| {k} | {v} |' for k, v in report['trendProbeSummary'].items()]
    lines += ['', '## Collegamento delle evidenze', '',
              'Il report JSON conserva tutte le coppie A3 e tutte le viste/operazioni A6, con contesti e benchmark.',
              'Un puntatore raggiunto attesta quel percorso: non certifica tutta una dimensione A3.',
              '**`acquired_access_not_proven` è un debito di collegamento da risolvere, non dato assente o fonte indisponibile.**', '']
    lines += [f'- {k}: {v}' for k, v in report['linkageSummary'].items()]
    for title, field in [('Riferimenti A3 risolti', 'acquisitionReferenceSummary'),
                         ('Accesso osservato dal workbench', 'workbenchAccessSummary'),
                         ('Accesso osservato dal trasporto', 'staticAccessSummary')]:
        lines += ['', '## '+title, '', '| Stato | Coppie |', '| --- | ---: |']
        lines += [f'| {k} | {v} |' for k, v in report[field].items()]
    lines += ['', 'Le prove dei percorsi restano distinte dalla copertura semantica della dimensione.',
              'Tutti gli operandi di un riferimento composto devono avere una prova; i riferimenti non risolti rimangono tali.',
              'Il ledger nativeProbes conserva richieste, rifiuti e digest riproducibili delle risposte originali.']
    lines += ['', *['- '+x for x in report['limits']], '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--runtime', type=Path)
    p.add_argument('--site', type=Path, help='Optional complete generated site; never implies live publication')
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    report = audit(args.catalog, args.registry, args.runtime, site=args.site)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'accessibility.json').write_text(encode(report)+'\n')
    (args.output_dir/'accessibility.md').write_text(markdown(report))
    print(encode({k: v for k, v in report.items() if k not in ('acquisition', 'views', 'nativeProbes', 'staticProbes')}))


if __name__ == '__main__':
    main()
