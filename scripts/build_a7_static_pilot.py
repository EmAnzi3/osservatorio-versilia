#!/usr/bin/env python3
"""Experimental, offline precompute. Canonical plans/cases remain authoritative."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from semantic_query_engine import ROOT, QueryEngine
from semantic_question_suite import check_expected
from semantic_methodological_checks import MethodologicalVerifier
from build_territorial_dossier_evidence import portable_evidence
from territorial_dossier_editorial import number

SCOPE = ROOT / 'experiments/a7-static-pilot/scope.json'
PROGRAM = ROOT / 'ci/territorial-dossier-program.json'
CASES = ROOT / 'ci/semantic-verified-questions.json'
READER = ROOT / 'experiments/a7-static-pilot/reader.mjs'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def render_answers(bundle):
    lines = ['# A7 — risposte dimostrative controllate', '',
             'Prova offline sulle domande curate. Tutte le domande di questo lotto rimangono parzialmente supportate.',
             'Le componenti con copertura parziale sono mostrate qui per revisione: nel lettore richiedono consenso esplicito.',
             'Catalogo: `' + bundle['catalogSha256'] + '`. Valori testuali arrotondati; il JSON conserva precisione e risposta A6.', '']
    for q in bundle['questions']:
        lines += ['## ' + q['question'], '', '**Classificazione:** ' + q['classification'],
                  '', q['answerBoundary'], '', 'Approfondimento: `' + q['dossierPath'] + '`.', '']
        for cid in q['requiredCaseRefs'] + q['contextCaseRefs']:
            case = bundle['cases'][cid]
            lines += ['### Richiesta `' + cid + '`', '',
                      'Operazione: `' + case['query']['operation'] + '`. Periodi e perimetri restano quelli delle osservazioni seguenti.', '']
            for fact in case['facts']:
                lines += ['- ' + fact['text'] + ' Anchor: `' + cid + fact['responsePointer'] + '`.']
                if fact['kind'] == 'observation':
                    lines += ['  Universo: ' + fact['population'] + '. Fonte: ' + fact['source'] + '.']
                for e in fact['evidence']:
                    if e.get('kind') != 'catalog_snapshot':
                        point = e.get('recordPointer') or e.get('valuePointer') or e.get('jsonPointer') or ''
                        lines += ['  Snapshot: `' + e.get('path', '') + '`; hash `' + e.get('sha256', '') + '`; puntatore `' + point + '`.']
            lines += ['', 'Avvertenze A6: ' + ', '.join(case['response']['warnings']), '']
        lines += ['**Dati mancanti per decidere:**', ''] + ['- ' + gap for gap in q['missingData']]
        lines += ['', q['interpretationLimit'], '']
    return '\n'.join(lines).rstrip() + '\n'


def facts(case_id, response, catalog):
    """Every numeric sentence points to the exact raw A6 value and its evidence."""
    if response['status'] != 'computed':
        return []
    towns = {t['code']: t['name'] for t in catalog['towns']}
    unit_names = {'percent': '%', 'millionCurrency': 'milioni €', 'currency': '€',
                  'studentsPerClass': 'alunni/classe', 'students': 'alunni',
                  'localUnits': 'unità locali', 'people': 'persone/addetti secondo definizione'}
    def display(value, unit):
        decimals = 1 if unit in ('percent', 'studentsPerClass') else 0 if value is not None and float(value).is_integer() else 2
        return number(value, decimals)
    rows = []
    for i, o in enumerate(response['observations']):
        label = catalog['metrics'][o['metric']]['meta']['label']
        text = f"{label} — {towns.get(o['geography'], o['geography'])}, {o['period']}: {display(o['value'], o['unit'])} {unit_names.get(o['unit'], o['unit'])}."
        rows.append(dict(kind='observation', caseId=case_id, responsePointer=f'/observations/{i}/value',
                         text=text, value=o['value'], unit=o['unit'], geography=o['geography'],
                         period=o['period'], dimension=o['dimension'], population=o['population'],
                         definition=o['definition'], method=o['method'], source=o['source'],
                         evidence=o['evidence'], provenance=o['provenance']))
    result = response['result']
    if isinstance(result, dict) and 'value' in result:
        unit = result['unit']
        periods = result.get('period') or f"{result.get('startPeriod')}–{result.get('endPeriod')}"
        operation = response['query']['operation']
        description = {'weighted_ratio': 'Rapporto fra somme, non media delle percentuali comunali',
                       'absolute_change': 'Variazione assoluta nominale' if 'nominal_economic_values_not_real_growth' in response['warnings'] else 'Variazione assoluta'}.get(operation, operation)
        rows.append(dict(kind='result', caseId=case_id, responsePointer='/result/value',
                         text=f"{description}, {periods}: {display(result['value'], unit)} {unit_names.get(unit, unit)}.",
                         value=result['value'], unit=unit, period=periods,
                         geographies=list(dict.fromkeys(o['geography'] for o in response['observations'])),
                         evidence=[e for o in response['observations'] for e in o['evidence']],
                         formula=response.get('formula'), aggregation=result.get('aggregation')))
    return rows


def build(catalog_path):
    start = time.perf_counter()
    scope = json.loads(SCOPE.read_text())
    if scope['schemaVersion'] != 1 or not scope['dossierRefs'] or not set(scope['dossierRefs']) <= {'lavoro', 'infanzia'}:
        raise ValueError('unsupported_pilot_scope')
    program = json.loads(PROGRAM.read_text())
    canonical_cases = {c['id']: c for c in json.loads(CASES.read_text())['questions']}
    dossiers = {d['id']: d for d in program['dossiers']}
    if len(set(scope['dossierRefs'])) != len(scope['dossierRefs']):
        raise ValueError('duplicate_dossier_ref')
    plans = []
    for did in scope['dossierRefs']:
        d = dossiers[did]
        for plan in [dict(d['centralPlan'], question=d['centralQuestion'], classification=d['classification'])] + d['secondaryQuestions']:
            if plan['classification'] not in ('supported', 'partially_supported', 'not_determinable'):
                raise ValueError('invalid_classification')
            refs = plan['requiredCaseRefs'] + plan['contextCaseRefs']
            if len(set(refs)) != len(refs) or not plan['answer']:
                raise ValueError('invalid_plan')
            if plan['classification'] == 'supported' and plan['missingData']:
                raise ValueError('supported_with_missing_data')
            plans.append(dict(id=plan['id'], dossierId=did, question=plan['question'],
                              classification=plan['classification'], answerBoundary=plan['answer'],
                              missingData=plan['missingData'], requiredCaseRefs=plan['requiredCaseRefs'],
                              contextCaseRefs=plan['contextCaseRefs'],
                              interpretationLimit=d['interpretationLimit'],
                              dossierPath='docs/dossiers/' + ('MASSAROSA_LAVORO.md' if did == 'lavoro' else 'MASSAROSA_INFANZIA_SCUOLA.md')))
    ids = list(dict.fromkeys(c for q in plans for c in q['requiredCaseRefs'] + q['contextCaseRefs']))
    if set(ids) & set(scope['refusalCaseRefs']) or len(set(scope['refusalCaseRefs'])) != len(scope['refusalCaseRefs']):
        raise ValueError('duplicate_refusal_case')
    engine = QueryEngine(catalog_path, layer='effective')
    verifier = MethodologicalVerifier(catalog_path, ROOT)
    responses = {}
    for cid in ids + scope['refusalCaseRefs']:
        case = canonical_cases[cid]
        response = engine.query(case['query'])
        errors = check_expected(response, case['expected']) + verifier.verify(response)
        if errors:
            raise ValueError('unverified_case:' + cid + ':' + ','.join(errors))
        if cid in scope['refusalCaseRefs'] and response['status'] != 'not_computable':
            raise ValueError('expected_refusal_not_refused:' + cid)
        responses[cid] = dict(query=case['query'], response=response,
                              facts=facts(cid, response, engine.catalog), reference=case['reference'])
    for q in plans:
        for cid in q['requiredCaseRefs']:
            r = responses[cid]['response']
            if r['status'] != 'computed':
                raise ValueError('required_case_not_computed:' + cid)
            if q['classification'] == 'supported' and any(o['value'] is None for o in r['observations']):
                raise ValueError('supported_with_missing_observations')
    # Portable paths are hash-qualified only for the catalog proven to match.
    # Source snapshot paths/pointers and all returned keys remain intact.
    bundle = portable_evidence(dict(schemaVersion=1, pilot='massarosa-work-and-education',
        catalogSha256=engine.catalog_hash, engineSha256=engine.module_hash,
        programSha256=sha(PROGRAM), casesSha256=sha(CASES), scopeSha256=sha(SCOPE),
        builderSha256=sha(Path(__file__)), readerSha256=sha(READER),
        questions=plans, cases=responses, refusalCaseRefs=scope['refusalCaseRefs'],
        limits=['Exact curated questions and fixed requests only; no general natural-language interpretation.',
                'Frozen evidence only; no current source-availability assertion.',
                'Partial coverage requires explicit consent; partial questions remain partial.',
                'Different populations and periods are displayed separately; no causal or individual inference.']))
    text = encode(bundle)
    manifest = {k: bundle[k] for k in ['schemaVersion', 'catalogSha256', 'engineSha256', 'programSha256', 'casesSha256', 'scopeSha256', 'builderSha256', 'readerSha256']}
    manifest.update(bundleSha256=hashlib.sha256(text.encode()).hexdigest(), bundleBytes=len(text.encode()))
    measurement = dict(buildSeconds=time.perf_counter()-start, questions=len(plans), cases=len(responses),
                       computed=sum(c['response']['status']=='computed' for c in responses.values()),
                       refused=sum(c['response']['status']=='not_computable' for c in responses.values()),
                       bundleBytes=manifest['bundleBytes'], bundleSha256=manifest['bundleSha256'],
                       environment='Python offline build; not mobile/browser latency')
    return bundle, manifest, measurement


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    bundle, manifest, measurement = build(args.catalog)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in [('bundle.json', bundle), ('release.json', manifest), ('build-measurement.json', measurement)]:
        (args.output_dir/name).write_text(encode(value), encoding='utf-8')
    (args.output_dir/'answers.md').write_text(render_answers(bundle), encoding='utf-8')
    print(encode(measurement))


if __name__ == '__main__':
    main()
