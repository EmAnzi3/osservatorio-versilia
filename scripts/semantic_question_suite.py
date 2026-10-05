#!/usr/bin/env python3
"""Versioned analytical questions with reviewed, independent expected results."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT

QUESTIONS = ROOT/'ci/semantic-verified-questions.json'


def pointer(value, path):
    for key in path.strip('/').split('/'):
        value=value[int(key)] if isinstance(value,list) else value[key.replace('~1','/').replace('~0','~')]
    return value


def check_expected(result, expected):
    errors=[]
    if result['status']!=expected['status']:errors.append('unexpected_status')
    for reason in expected.get('reasons',[]):
        if reason not in result['reasons']:errors.append('missing_reason:'+reason)
    for warning in expected.get('warnings',[]):
        if warning not in result['warnings']:errors.append('missing_warning:'+warning)
    for assertion in expected.get('checks',[]):
        try: actual=pointer(result,assertion['path'])
        except (KeyError,IndexError,TypeError):errors.append('missing_path:'+assertion['path']);continue
        if 'fraction' in assertion:
            wanted=float(Fraction(*assertion['fraction']))
            ok=type(actual) in (int,float) and math.isclose(actual,wanted,rel_tol=0,abs_tol=assertion.get('tolerance',1e-8))
        else:ok=actual==assertion['value']
        if not ok:errors.append('unexpected_value:'+assertion['path'])
    if result['status']=='computed':
        for observation in result['observations']:
            if not observation.get('source') or not observation.get('provenance'):errors.append('missing_provenance')
            if not any(e.get('valuePointer') and e.get('sha256') for e in observation['provenance']) and observation['geography'] not in ('tuscany','italy','versilia'):
                errors.append('missing_catalog_pointer')
    return sorted(set(errors))


def run_suite(engine, manifest_path=QUESTIONS):
    body=manifest_path.read_bytes();manifest=json.loads(body)
    if manifest.get('schemaVersion')!=1:raise ValueError('question_schema')
    cases=manifest['questions'];ids=[c['id'] for c in cases]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate_question_id')
    results=[]
    for case in cases:
        if not case.get('question') or not case.get('reference'):raise ValueError('question_or_reference_missing')
        expected=case['expected']
        if expected.get('status') not in ('computed','not_computable'):
            raise ValueError('invalid_expected_status')
        if not expected.get('checks' if expected['status']=='computed' else 'reasons'):
            raise ValueError('independent_checks_or_refusal_reasons_required')
        result=engine.query(case['query']);errors=check_expected(result,case['expected'])
        results.append(dict(id=case['id'],question=case['question'],reference=case['reference'],
            verdict='FAIL' if errors else 'PASS',errors=errors,expected=case['expected'],actual=result))
    return dict(schemaVersion=1,catalogSha256=engine.catalog_hash,manifestSha256=hashlib.sha256(body).hexdigest(),
        engineSha256=engine.module_hash,status='FAIL' if any(r['errors'] for r in results) else 'PASS',
        summary=dict(questions=len(results),passed=sum(not r['errors'] for r in results),
            computed=sum(r['actual']['status']=='computed' for r in results),
            refused=sum(r['actual']['status']=='not_computable' for r in results)),results=results)


def markdown(report):
    lines=['# A6 — domande con risultati verificati','',
        f"Catalogo `{report['catalogSha256']}`; manifest `{report['manifestSha256']}`. Esito: **{report['status']}**.",'',
        'Le aspettative sono versionate e controllate contro riferimenti aritmetici/record dichiarati; non vengono riscritte automaticamente con la risposta del motore. Le domande sono casi di prova riutilizzabili, non un interprete di linguaggio naturale.', '',
        '| ID e domanda | Esito | Risultato verificato / motivo | Riferimento indipendente |','|---|---|---|---|']
    for r in report['results']:
        a=r['actual'];checks=r['expected'].get('checks',[])
        answer='; '.join(c['path']+': '+str(pointer(a,c['path'])) for c in checks) if a['status']=='computed' else ', '.join(a['reasons'])
        lines.append('| '+' | '.join([r['id']+': '+r['question'],r['verdict'],answer,r['reference']])+' |')
    lines+=['','Il JSON conserva query, risultati, formula, fonti, periodi, copertura ed esclusioni. Un rifiuto atteso è una verifica riuscita del limite, non una capacità di risposta numerica. Nessuna conclusione causale o raccomandazione automatica.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,default=ROOT/'dist/data/site-data.json')
    p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    report=run_suite(QueryEngine(args.catalog,layer='effective'));args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'questions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (args.output_dir/'questions.md').write_text(markdown(report));print(report['summary'])
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
