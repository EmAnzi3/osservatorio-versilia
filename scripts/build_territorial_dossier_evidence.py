#!/usr/bin/env python3
"""Resolve editorial references and replay existing independent A6 expectations."""
import argparse
import hashlib
import json
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT, operations, benchmark_scopes, dimensions
from semantic_question_suite import check_expected
from semantic_methodological_checks import MethodologicalVerifier
from territorial_dossier_editorial import validate_plans, render_questions, render_modules, render_demos

def build(catalog):
    program_path=ROOT/'ci/territorial-dossier-program.json'
    program=json.loads(program_path.read_text())
    baseline=json.loads((ROOT/program['baselineQuestionsPath']).read_text())
    cases=json.loads((ROOT/'ci/semantic-verified-questions.json').read_text())['questions']
    engine=QueryEngine(catalog,layer='effective');verifier=MethodologicalVerifier(catalog,ROOT)
    ids=[d['id'] for d in program['dossiers']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate_dossier')
    report=[];evidence={};failures=[]
    for d in program['dossiers']:
        if not set(d['relatedDossiers'])<=set(ids):raise ValueError('unknown_relation')
        if len(d['metricRefs'])!=len(set(d['metricRefs'])):raise ValueError('duplicate_metric_reference')
        if any(q['classification'] not in ('supported','partially_supported','not_determinable') for q in d['secondaryQuestions']):raise ValueError('unknown_question_classification')
        chosen=[]
        for metric in d['metricRefs']:
            if metric not in engine.catalog['metrics']:raise ValueError('unknown_metric:'+metric)
            candidates=[c for c in cases if c['query']['selectors'][0]['metric']==metric]
            if not candidates:
                query={'operation':'compare','selectors':[{'metric':metric,'dimension':dimensions(metric)[0]}]}
                response=engine.query(query);errors=verifier.verify(response)
                if response['status']!='computed':errors.append('primary_view_unexpected_refusal')
                published={r['code']:r['value'] for r in engine.catalog['metrics'][metric]['rows']}
                anchors={};anchor_paths={}
                for row in engine.catalog['metrics'][metric]['rows']:
                    # ARS cards display two decimals; native standardized totals retain precision.
                    parts={p['key']:p for p in row.get('parts',[]) if 'key' in p}
                    key=next((k for k in ('totale|totale','totale') if k in parts),None)
                    part=parts.get(key,{}) if key else {}
                    native=part.get('value') if part.get('measurement')=='standardized' else None
                    native_path='parts/'+key+'/value' if native is not None else 'value'
                    if metric=='chronicTotal':
                        series=row['series'];period=str(engine.catalog['metrics'][metric]['meta']['year'])
                        index=series['years'].index(period)
                        native=series['values'][index];native_path='series/values/'+str(index)
                    anchors[row['code']]=native if native is not None else row['value']
                    anchor_paths[row['code']]=native_path
                    if native is not None and row['value']!=round(native,2):
                        errors.append('native_total_card_rounding_mismatch:'+row['code'])
                if response['status']=='computed':
                    for o in response['observations']:
                        if o['geography'] not in anchors or o['value']!=anchors[o['geography']]:
                            errors.append('primary_view_not_equal_to_published_anchor:'+o['geography'])
                cid='dossier_primary_'+metric
                selector=query['selectors'][0];context=engine.context(metric,selector['dimension'])
                evidence[cid]=dict(id=cid,query=query,reference='Effective Public Catalog rows, with exact native standardized total and separate two-decimal card reconciliation where applicable. Native source reconciliation remains in approved A6 profile suites.',expected={'publishedRows':published,'nativeAnchors':anchors,'anchorPaths':anchor_paths},response=response,verification='FAIL' if errors else 'PASS',errors=errors,selectedViewCapabilities=dict(operations=operations(metric,selector['dimension'],context['unit']),benchmarkScopes=benchmark_scopes(metric,selector['dimension']),context=context))
                if errors:failures.append(dict(id=cid,errors=errors))
                chosen.append(cid);continue
            for op in ('compare','series','weighted_ratio','benchmark_gap'):
                options=[c for c in candidates if c['query']['operation']==op and c['expected']['status']=='computed']
                if not options:continue
                # Prefer an already reviewed request including Massarosa; never alter a frozen expectation.
                options.sort(key=lambda c:(not ('046018' in c['query']['selectors'][0].get('towns',[])), bool(c['query']['selectors'][0].get('periods'))))
                chosen.append(options[0]['id'])
            refused=next((c for c in candidates if c['expected']['status']=='not_computable'),None)
            if refused:chosen.append(refused['id'])
        # Editorially relevant complements: distinct universes, not extra cases for volume.
        complements={'lavoro':['atlas_territory_2025','business_frame_services_history'],
                     'abitazione':['omi_rentMean_046018'],
                     'mobilita':['tpl_scheduledTplTripsPer1000_total_046018']}
        chosen.extend(complements.get(d['id'],[]))
        for plan in [d['centralPlan']]+d['secondaryQuestions']:
            chosen.extend(plan['requiredCaseRefs']+plan['contextCaseRefs'])
        for module in d['modules']:
            chosen.extend(module['availableCaseRefs'])
        rows=[]
        for cid in dict.fromkeys(chosen):
            if cid not in evidence:
                case=next(c for c in cases if c['id']==cid);response=engine.query(case['query'])
                errors=check_expected(response,case['expected'])+verifier.verify(response)
                if errors:failures.append(dict(id=cid,errors=errors))
                selector=response['query']['selectors'][0]
                context=engine.context(selector['metric'],selector.get('dimension','total')) if response['status']=='computed' else None
                evidence[cid]=dict(id=cid,query=case['query'],reference=case['reference'],expected=case['expected'],response=response,
                    verification='FAIL' if errors else 'PASS',errors=errors,
                    selectedViewCapabilities=dict(operations=operations(selector['metric'],selector.get('dimension','total'),context['unit']),benchmarkScopes=benchmark_scopes(selector['metric'],selector.get('dimension','total')),context=context) if context else None)
            rows.append(evidence[cid])
        obs=[o for r in rows for o in r['response']['observations']]
        plans=validate_plans(d,evidence)
        report.append(dict(**d,questionEvidence=plans,evidenceCaseIds=list(dict.fromkeys(chosen)),
            sources=sorted({o['source'] for o in obs}),observedPeriods=sorted({o['period'] for o in obs}),
            observedUnits=sorted({o['unit'] for o in obs}),observedGeographies=sorted({o['geography'] for o in obs}),
            feasibility=dict(existing='Consultazioni e calcoli con esiti e limiti nelle richieste selezionate.',composition=d['composition'],additionalData=d['missingData']),
            answerBoundary='Un PASS delle richieste di contesto non rende determinabile la domanda decisionale centrale. I perimetri territoriali/temporali eseguiti restano quelli espliciti delle query.'))
    return dict(schemaVersion=2,townNames={t['code']:t['name'] for t in engine.catalog['towns']},status='FAIL' if failures else 'PASS',catalogSha256=engine.catalog_hash,engineSha256=engine.module_hash,
        programSha256=hashlib.sha256(program_path.read_bytes()).hexdigest(),baselineQuestionsPreserved=baseline,
        dossiers=report,evidence=evidence,failures=failures,
        limits=['No new acquisitions, adapters, political rankings or causal evaluation.','Periods and units belong to each selected observation; no automatic cross-period joining.',
                'External methodological references are not data acquired by the observatory.','A6 closure attested after PR428 merge and post-merge verification; dossier program remains a separate proposal.'])

def render(report):
    def cell(value):
        return str(value).replace('|',r'\|').replace('\n',' ')
    lines=['# Programma dei dossier territoriali — evidenze verificate','',f"Esito **{report['status']}**; catalogo `{report['catalogSha256']}`; motore `{report['engineSha256']}`.",'',
        'Le 20 domande A6 originarie sono riusate per riferimento, senza riscriverle. Le domande centrali orientano un programma amministrativo: i risultati di contesto non risolvono automaticamente bisogni, efficacia o causalità.','',
        '| Dossier | Stadio | Capacità esistenti | Nuova composizione | Dati ulteriori |','|---|---|---|---|---|']
    for d in report['dossiers']:
        lines.append('| '+' | '.join(map(cell,[d['title'],d['pilotTier'],str(len(d['evidenceCaseIds']))+' richieste verificate','Contesti e calcoli separati, periodi espliciti','; '.join(d['missingData'])]))+' |')
    for d in report['dossiers']:
        lines+=['',f"## {d['title']}",'',d['centralQuestion']+' **Risposta parziale**.', '',
            '**Problema:** '+d['decisionProblem'],'', '**Domande secondarie:**']
        lines += ['- '+q['question']+' — '+q['classification']+'; '+q['answer'] for q in d['secondaryQuestions']]
        lines+=['','**Valore conoscitivo:** '+d['knowledgeValue'],'','**Composizione:** '+d['composition'],'',
                '**Interpretazione da approfondire:** '+d['possibleInterpretation'],'',
                '**Competenze:** '+d['competences'],'','**Opzioni da approfondire, non approvate:** '+d['optionsToInvestigate'],'',
                '**Monitoraggio:** '+d['monitoring'],'','**Lacune:** '+'; '.join(d['missingData']), '',
                '**Relazioni:** '+', '.join(d['relatedDossiers']), '',
                '| Richiesta | Operazione / vista | Periodi / unità | Risposta | Verifica |','|---|---|---|---|---|']
        for cid in d['evidenceCaseIds']:
            e=report['evidence'][cid];r=e['response'];s=r['query']['selectors'][0];obs=r['observations']
            values='; '.join(o['geography']+': '+str(o.get('value')) for o in obs[:7]) if r['status']=='computed' else ', '.join(r['reasons'])
            periods=', '.join(sorted({o['period'] for o in obs}));units=', '.join(sorted({o['unit'] for o in obs}))
            lines.append('| '+' | '.join(map(cell,[cid,r['query']['operation']+' / '+s['metric']+' / '+s.get('dimension','total'),periods+' / '+units,values,e['verification']]))+' |')
        lines+=['', '**Fonti effettivamente lette:** '+'; '.join(d['sources']), '', d['answerBoundary'], '', d['interpretationLimit']]
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    report=build(a.catalog);a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (a.output_dir/'program-and-feasibility.md').write_text(render(report))
    (a.output_dir/'QUESTIONS.md').write_text(render_questions(report))
    (a.output_dir/'MODULES.md').write_text(render_modules(report))
    for name,content in render_demos(report).items():
        (a.output_dir/name).write_text(content)
    print(json.dumps(dict(status=report['status'],dossiers=len(report['dossiers']),executedRequests=len(report['evidence']),failures=report['failures'])))
    return 1 if report['failures'] else 0
if __name__=='__main__':raise SystemExit(main())
