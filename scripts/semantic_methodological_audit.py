#!/usr/bin/env python3
"""Reproducible A6 methodological evidence, never a DONE/merge certificate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from semantic_engine_audit import audit, connections
from semantic_methodological_checks import MethodologicalVerifier
from semantic_question_suite import run_suite
from semantic_query_engine import QueryEngine, ROOT
from semantic_territorial_readings import build_readings

ACCEPTANCE = ROOT / 'ci/a6-territorial-acceptance-questions.json'


def reading_review(readings, verifier):
    rows=[]
    for reading in readings['readings']:
        errors=[];facts=[]
        for item in reading['observations']:
            o=item['observation'];errors.extend(verifier.provenance(o))
            facts.append(dict(label=item['label'],value=o['value'],unit=o['unit'],period=o['period'],
                              universe=o['population'],source=o['source'],provenance=o['provenance']))
        for r in reading['calculations']:
            errors.extend(verifier.verify(r))
        association=reading['association']
        if association['status'] != 'not_requested': errors.extend(verifier.verify(association))
        if reading['status'] != 'ready_for_methodological_review': errors.append('reading_not_ready')
        if reading['proposal']['approved'] or reading['proposal']['expectedEffect'] is not None:
            errors.append('unapproved_policy_effect')
        values=[o['value'] for o in facts]
        pilot=reading['pilot']
        if reading['status']!='ready_for_methodological_review' or len(facts)!=len(reading['observations']) or len(values)<2:
            text='Lettura non disponibile: evidenze incomplete o incoerenti; nessuna sostituzione con zero o risultati precedenti.'
        elif pilot=='ageing_care':
            text=f"Gli 85+ sono il {values[0]:.2f}% dei residenti nel {facts[0]['period']}. Il tasso standardizzato di assistenza domiciliare ARS del {facts[1]['period']} è {values[1]:.4f} {facts[1]['unit']}. Periodi e popolazioni sono distinti; nessuna misura del bisogno insoddisfatto."
        elif pilot=='work_childcare':
            text=f"Occupazione femminile: {values[0]:.2f}% nel {facts[0]['period']}. Ricettività educativa potenziale: {values[1]:.2f}% nel {facts[1]['period']}. Sono contesti separati, senza una stima dell'effetto dei nidi sull'occupazione."
        elif pilot=='tourism_services':
            text=f"Pernottamenti registrati nel 2025: {values[0]:,.0f}. Intensità: {values[1]:.2f} notti 2025 per residente POSAS 2026. Il rapporto non misura persone uniche, picchi giornalieri o carichi reali dei servizi."
        elif pilot=='work_commuting':
            text=f"Nel 2021: {values[0]:,.0f} ingressi, {values[1]:,.0f} uscite e saldo {values[2]:+,.0f}. Autocontenimento nel proprio Comune: {values[3]:.2f}%. Margini del lavoro abituale, senza una matrice origine-destinazione o domanda attuale."
        else:
            text=f"Nel 2024/25 le scuole localizzate nel Comune registrano {values[0]:,.0f} alunni e {values[1]:.2f} alunni per classe. Tempo pieno primaria: {values[2]:.2f}%. Non sono quote di copertura dei bambini residenti o misure di qualità didattica."
        rows.append(dict(id=reading['id'],town=reading['town'],pilot=pilot,status='FAIL' if errors else 'PASS',
            errors=sorted(set(errors)),explanation=text,facts=facts,
            calculations=reading['calculations'],association=association,
            associationScope=reading['associationScope'],
            hypothesis=reading['hypothesis'],optionToEvaluate=reading['proposal'],
            missingData=reading['proposal']['additionalDataRequired'],
            monitoringIndicators=reading['proposal']['outcomeIndicatorsRequired']))
    groups=[]
    for group in readings['groupReadings']:
        comparisons=[];errors=[]
        if group['status']!='ready_for_methodological_review':errors.append('group_not_ready')
        for result in group['calculations']:
            errors.extend(verifier.verify(result))
            obs=result['observations']
            comparisons.append(dict(metric=result['query']['selectors'][0]['metric'],
                ratioOfSums=result['result'],
                municipalArithmeticMean=sum(o['value'] for o in obs)/len(obs) if obs and all(type(o.get('value')) in (int,float) for o in obs) else None,
                distinction='Arithmetic mean is shown as a diagnostic; only the ratio of sums is the declared pooled result',
                periods=sorted({o['period'] for o in obs}),
                componentPeriods=sorted({(str(o.get('numeratorPeriod')),str(o.get('denominatorPeriod'))) for o in obs})))
            if len(obs)!=7 or {o['geography'] for o in obs}!=set(group['geographies']):
                errors.append('incomplete_or_duplicate_group_coverage')
        groups.append(dict(pilot=group['pilot'],status='FAIL' if errors else 'PASS',errors=sorted(set(errors)),
                           original=group,pooledVsMean=comparisons))
    return dict(baselineSchemaVersion=readings['schemaVersion'],baselineReadingsPreserved=True,
                status='FAIL' if any(r['status']=='FAIL' for r in rows+groups) else 'PASS',
                readings=rows,groupReadings=groups,
                scope='All 35 baseline readings and both baseline group summaries; explanatory annotations are separate, no silent numerical replacement')


def acceptance_report(cases):
    manifest=json.loads(ACCEPTANCE.read_text())
    by_id={c['id']:c for c in cases};rows=[]
    ids=[q['id'] for q in manifest['questions']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate_territorial_question')
    for question in manifest['questions']:
        for field in ('problem','answerToday','unjustifiedConclusions','missingData','decisionValue','requestCaseIds'):
            if not question.get(field):raise ValueError('territorial_question_missing:'+field)
        if question['classification'] not in ('supported','partially_supported','not_determinable'):
            raise ValueError('territorial_question_classification')
        evidence=[by_id[id] for id in question['requestCaseIds']]
        observations=[o for c in evidence for o in c['actual']['observations']]
        rows.append(dict(question,
            verification='FAIL' if any(c['verdict']!='PASS' for c in evidence) else 'PASS',
            indicators=sorted({s['metric'] for c in evidence for s in c['actual']['query']['selectors']}),
            sources=sorted({o['source'] for o in observations}),
            observedPeriods=sorted({o['period'] for o in observations}),
            geographies=sorted({o['geography'] for o in observations}),
            requests=[dict(id=c['id'],query=c['actual']['query'],status=c['actual']['status'],
                           reasons=c['actual']['reasons'],formula=c['actual'].get('formula'),
                           result=c['actual']['result'],warnings=c['actual']['warnings']) for c in evidence],
            permittedOperations=sorted({c['actual']['query']['operation'] for c in evidence if c['actual']['status']=='computed'})))
    return dict(schemaVersion=1,manifestSha256=hashlib.sha256(ACCEPTANCE.read_bytes()).hexdigest(),
                status='FAIL' if any(q['verification']=='FAIL' for q in rows) else 'PASS',
                classifications=dict(Counter(q['classification'] for q in rows)),questions=rows,
                warning='PASS checks the evidence and declared boundary; not_determinable questions remain unresolved. Request examples keep their explicit geographical scope; a supported question is not a policy recommendation. Housing and finance are supplemental to the five baseline pilots.')


def build_audit(engine):
    verifier=MethodologicalVerifier(engine.path,engine.root)
    coverage=audit(engine,verifier)
    suite=run_suite(engine);independent=verifier.suite(suite['results'])
    readings=reading_review(build_readings(engine),verifier)
    questions=acceptance_report(suite['results'])
    graph=connections(engine,coverage)
    pairs=[]
    for edge in graph['edges']:
        response=edge['associationAttempt']
        if response is None:continue
        errors=verifier.verify(response)
        pairs.append(dict(id=edge['id'],status=response['status'],errors=errors,
                          query=response['query'],result=response['result'],warnings=response['warnings'],reasons=response['reasons']))
    probe_failures=[dict(metric=m['metric'],probe=p) for m in coverage['metrics'] for p in m['probes']
                    if p.get('independentVerification',{}).get('status')=='FAIL']
    residual=probe_failures+[p for p in pairs if p['errors']]
    ok=coverage['summary']['withoutAdapter']==0 and suite['status']==independent['status']==readings['status']==questions['status']=='PASS' and not residual
    return dict(schemaVersion=1,status='PASS' if ok else 'FAIL',administrativeStatus='A6_IN_PROGRESS_APPROVAL_AND_MERGE_REQUIRED',
        catalogSha256=engine.catalog_hash,engineSha256=engine.module_hash,
        verifierSha256=hashlib.sha256((ROOT/'scripts/semantic_methodological_checks.py').read_bytes()).hexdigest(),
        auditSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        coverage=coverage,baselineSuite=suite['summary'],independentChecks=independent,
        territorialReview=readings,acceptance=questions,selectedAssociations=pairs,unexpectedResiduals=residual,
        sourceFiles=[dict(path=str(p),sha256=hashlib.sha256(b).hexdigest()) for p,b in sorted(verifier.bytes.items())],
        limits=['Frozen inputs only; no current online-source availability certification',
                'All declared dimensions inventoried; probes keep their exact municipalities, years and scopes, not all possible query combinations',
                'Every baseline question response independently checked; profile suites provide native reconciliation and adversarial/cache coverage',
                'Descriptive ecological associations, sample and leave-one-out sensitivity; no causality, prediction or individual inference',
                'Missing or unsupported data remain explicit; no automatic administrative recommendations',
                'No new UI, acquisitions or A7 service; golden masters and budgets remain external mandatory gates'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--catalog',type=Path,default=ROOT/'dist/data/site-data.json')
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    report=build_audit(QueryEngine(args.catalog,layer='effective'))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    target=args.output_dir/'methodological-audit.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=report['status'],suite=report['baselineSuite'],coverage=report['coverage']['summary'],
                         readings=len(report['territorialReview']['readings']),groupReadings=len(report['territorialReview']['groupReadings']),
                         unexpectedResiduals=len(report['unexpectedResiduals']),reportSha256=hashlib.sha256(target.read_bytes()).hexdigest())))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
