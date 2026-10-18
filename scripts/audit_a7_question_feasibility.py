#!/usr/bin/env python3
"""Measured acceptance examples, separate from runtime and source availability."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from a7_query_workbench import QueryWorkbench
from semantic_query_engine import ROOT

CASES = ROOT/'ci/a7-question-feasibility-cases.json'


def audit(catalog):
    w = QueryWorkbench(catalog)
    body = CASES.read_bytes()
    cases = json.loads(body)['questions']
    assert [c['id'] for c in cases] == list(range(1,31))
    results = []
    declarations_by_metric = {row['metric']:row['engine'] for row in w.engine.coverage()}
    metadata = {
        28: ['ci/semantic-operations-contract.json', 'scripts/semantic_operations.py'],
        30: ['segnala/index.html', 'assets/app-parts/05.txt', 'assets/app-parts/06.txt'],
    }
    for case in cases:
        declarations = {}
        for query in case['requests']:
            for selector in query['selectors']:
                metric = selector['metric']
                declarations[metric] = declarations_by_metric[metric]
                assert selector['dimension'] in declarations[metric]['dimensions'], (case['id'], selector)
                assert query['operation'] in declarations[metric]['operationsByDimension'][selector['dimension']], (case['id'], query)
        responses = [w.engine.query(q) for q in case['requests']]
        computed = sum(r['status']=='computed' for r in responses)
        refs = [dict(path=p, sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
                for p in metadata.get(case['id'], [])]
        failures = [dict(request=r['query'], reasons=r['reasons']) for r in responses if r['status']!='computed']
        # This is an editorial requirement mapping checked by executions, NOT a
        # classifier of arbitrary prose. No inference that all data are absent.
        complete = not case['unmetRequirements'] and not failures and bool(responses or refs)
        status = ('supported_after_clarification' if complete and case['clarifications'] else
                  'supported' if complete else 'partial' if computed or refs else 'not_determinable')
        results.append(dict(**case, status=status, computedComponents=computed,
            failures=failures, responses=responses, metadataEvidence=refs,
            declaredDimensions={k:v['dimensions'] for k,v in declarations.items()}))
    return dict(schemaVersion=1, catalogSha256=w.engine.catalog_hash,
        engineSha256=w.engine.module_hash, casesSha256=hashlib.sha256(body).hexdigest(),
        scope='30 reviewed acceptance examples; no natural-language comprehension score or complete source-field audit',
        summary=dict(Counter(r['status'] for r in results)), questions=results)


def markdown(report):
    lines=['# A7 — fattibilità misurata dei quesiti di accettazione', '',
           'Report derivato: le richieste sono eseguite sul catalogo indicato. Le mappature delle domande sono revisionate, non interpretate automaticamente.', '',
           'Le componenti calcolate non provano completezza della risposta. Un chiarimento deve essere risolto prima della risposta pubblica; gli esempi di selezione non sono default impliciti.', '',
           f"Catalogo SHA256: `{report['catalogSha256']}`", '',
           '| ID | Domanda | Stato | Componenti calcolate | Limiti / chiarimenti / rifiuti |',
           '| --- | --- | --- | ---: | --- |']
    for row in report['questions']:
        limits=row['unmetRequirements']+row['clarifications']+[str(f['reasons']) for f in row['failures']]
        lines.append('| '+ ' | '.join([str(row['id']), row['question'], row['status'],str(row['computedComponents']), '; '.join(limits) or 'Riferimenti e definizioni nella risposta strutturata.']).replace('\n',' ')+' |')
    lines.extend(['', '## Limiti della misura', '',
        'Nessuna percentuale unica di copertura: gli esempi non sono un campione statistico delle domande possibili. Fonte non esposta, capacità non implementata e dato non acquisito restano distinti. `data_access_or_data_gap` richiede audit degli snapshot prima di attribuire la lacuna alla fonte.', '',
        'Il JSON conserva richieste, risultati, rifiuti e provenance; i riferimenti agli indicatori sono casi di accettazione, mai un secondo catalogo o routing di domande autorizzate. Le verifiche numeriche indipendenti rimangono la suite A6 e le regressioni puntuali.', ''])
    return '\n'.join(lines)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--catalog',type=Path,required=True)
    p.add_argument('--output-dir',type=Path)
    args=p.parse_args()
    report=audit(args.catalog)
    if args.output_dir:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        (args.output_dir/'feasibility.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        (args.output_dir/'feasibility.md').write_text(markdown(report))
    print(json.dumps(report['summary']))
