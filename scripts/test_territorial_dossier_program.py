#!/usr/bin/env python3
"""Persistent editorial contract: plans, hostile inputs and reproduced readable output."""
import argparse
import copy
import json
from pathlib import Path
from territorial_dossier_editorial import validate_plans, render_questions, render_modules, render_demos
from build_territorial_dossier_evidence import build, render, summary, evidence_text, render_pilots
from semantic_query_engine import ROOT


def rejects(action, reason):
    try:
        action()
    except ValueError as error:
        assert reason in str(error), (reason, str(error))
    else:
        raise AssertionError('hostile plan accepted: ' + reason)


def structure():
    program = json.loads((ROOT/'ci/territorial-dossier-program.json').read_text())
    baseline = json.loads((ROOT/program['baselineQuestionsPath']).read_text())
    base_ids = {q['id'] for q in baseline['questions']}
    dossier_ids = [d['id'] for d in program['dossiers']]
    assert len(dossier_ids) == len(set(dossier_ids))
    cases = {c['id']: c for c in json.loads((ROOT/'ci/semantic-verified-questions.json').read_text())['questions']}
    known_primary = {'dossier_primary_'+m for d in program['dossiers'] for m in d['metricRefs']}
    evidence = {cid:dict(verification='PASS', response=dict(status=c['expected']['status'], observations=[]), query=c['query']) for cid,c in cases.items()}
    evidence.update({cid:dict(verification='PASS',response=dict(status='computed',observations=[]),query={}) for cid in known_primary})
    all_questions = [];all_modules = []
    for d in program['dossiers']:
        assert set(d['baselineQuestionRefs']) <= base_ids
        assert set(d['relatedDossiers']) <= set(dossier_ids)
        for m in d['modules']:
            assert set(m['relatedDossiers']) <= set(dossier_ids)
        plans = validate_plans(d,evidence)
        all_questions.extend(q['id'] for q in plans);all_modules.extend(m['id'] for m in d['modules'])
    assert len(all_questions) == len(set(all_questions))
    assert len(all_modules) == len(set(all_modules))
    d = copy.deepcopy(program['dossiers'][1])
    bad = copy.deepcopy(d);bad['secondaryQuestions'][0]['requiredCaseRefs']=['not-a-case']
    rejects(lambda:validate_plans(bad,evidence),'unknown_question_case')
    bad = copy.deepcopy(d);bad['secondaryQuestions'][0]['classification']='supported'
    rejects(lambda:validate_plans(bad,evidence),'supported_question_with_decision_gaps')
    bad = copy.deepcopy(d);bad['secondaryQuestions'][0]['requiredCaseRefs']=[]
    rejects(lambda:validate_plans(bad,evidence),'answer_without_required_evidence')
    bad = copy.deepcopy(d);bad['secondaryQuestions'][0]['requiredCaseRefs']=['census_primary_history_refused']
    rejects(lambda:validate_plans(bad,evidence),'required_case_not_computed')
    bad = copy.deepcopy(d);bad['secondaryQuestions'][0]['requiredCaseRefs']*=2
    rejects(lambda:validate_plans(bad,evidence),'duplicate_question_case')
    bad = copy.deepcopy(d);bad['modules'][0]['stage']='complete'
    rejects(lambda:validate_plans(bad,evidence),'module_maturity_overclaim')
    return program


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path);args=p.parse_args()
    program=structure()
    if args.catalog:
        report=build(args.catalog)
        assert report['status']=='PASS',report['failures']
        outputs={ROOT/'reports/territorial-dossiers/program-and-feasibility.md':render(report),
                 ROOT/'docs/dossiers/QUESTIONS.md':render_questions(report),
                 ROOT/'docs/dossiers/MODULES.md':render_modules(report)}
        outputs.update({ROOT/'docs/dossiers'/name:content for name,content in render_demos(report).items()})
        pilots_path=ROOT/'docs/dossiers/PILOTS.md'
        outputs[pilots_path]=render_pilots(report,pilots_path.read_text())
        for path,content in outputs.items():
            assert path.read_text()==content,'stale editorial output: '+str(path.relative_to(ROOT))
        assert json.loads((ROOT/'reports/territorial-dossiers/summary.json').read_text())==summary(report),'stale dossier summary'
        relocated=copy.deepcopy(report)
        catalog_paths={e['response']['catalogPath'] for e in report['evidence'].values()}
        def relocate(value):
            if isinstance(value,dict):
                if value.get('path') in catalog_paths and value.get('sha256')==report['catalogSha256']:
                    value['path']='/different/workspace/catalog.json'
                if value.get('catalogPath') in catalog_paths:value['catalogPath']='/different/workspace/catalog.json'
                for v in value.values():relocate(v)
            elif isinstance(value,list):
                for v in value:relocate(v)
        relocate(relocated)
        assert evidence_text(relocated)==evidence_text(report),'catalog location leaked into evidence hash'
        altered=copy.deepcopy(report)
        altered['evidence']['child_weighted']['response']['result']['denominator']+=1
        assert evidence_text(altered)!=evidence_text(report),'altered denominator omitted from evidence hash'
        assert render_pilots(altered,pilots_path.read_text())!=pilots_path.read_text(),'stale pilot aggregate undetected'
        stale=pilots_path.read_text().replace('| 046018 | 2024 | 73.4 |','| 046018 | 2024 | 0.0 |',1)
        assert stale!=pilots_path.read_text() and render_pilots(report,stale)!=stale,'stale pilot observation undetected'
        # Reject a silently stale comparison or an incorrect aggregation in readable prose.
        bad=copy.deepcopy(report);bad['evidence']['census_employment_primary']['response']['observations'][0]['value']=0
        rejects(lambda:render_demos(bad),'labour_narrative_direction_changed')
        bad=copy.deepcopy(report);bad['evidence']['child_weighted']['response']['result']['value']=sum(o['value'] for o in bad['evidence']['child_weighted']['response']['observations'])/7
        rejects(lambda:render_demos(bad),'capacity_aggregate_not_ratio_of_sums')
        bad=copy.deepcopy(report);bad['evidence']['school_class_size']['response']['observations'][0]['value']=None
        rejects(lambda:render_demos(bad),'ambiguous_or_missing_story_input')
        bad=copy.deepcopy(report);bad['evidence']['business_asia_cumulative']['verification']='FAIL'
        rejects(lambda:render_demos(bad),'unverified_story_input')
        print(json.dumps(dict(status='PASS',executedRequests=len(report['evidence']),computed=sum(e['response']['status']=='computed' for e in report['evidence'].values()),expectedRefusals=sum(e['response']['status']!='computed' for e in report['evidence'].values()),reproducedOutputs=len(outputs))))
    else:
        print(json.dumps(dict(status='PASS',scope='structure and hostile plans; no numeric replay',dossiers=len(program['dossiers']))))
    return 0
if __name__=='__main__':raise SystemExit(main())
