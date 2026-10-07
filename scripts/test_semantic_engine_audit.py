#!/usr/bin/env python3
"""Effective-catalog gate for coverage, typed links and reviewed questions."""
import copy
import json
import math
from pathlib import Path
import tempfile

from semantic_engine_audit import audit, connections
from semantic_engine_benchmark import percentile, summarize
from semantic_question_suite import QUESTIONS, check_expected, run_suite
from semantic_query_engine import QueryEngine, ROOT, SUPPORTED


def regressions(catalog_path):
    engine=QueryEngine(catalog_path,layer='effective');catalog=engine.catalog
    coverage=audit(engine);metrics={r['metric']:r for r in coverage['metrics']}
    assert len(metrics)==len(coverage['metrics'])==len(catalog['metrics'])
    assert set(metrics)==set(catalog['metrics'])
    assert coverage['summary']['withAdapter']+coverage['summary']['withoutAdapter']==len(metrics)
    for key,row in metrics.items():
        assert row['label']==catalog['metrics'][key]['meta']['label']
        assert row['carrierPresenceCertifiesQuery'] is False
        assert len(row['enrichment'])==9
        assert all(d['state'] in ('ACQUIRED','AVAILABLE_MISSING','SOURCE_UNAVAILABLE','NOT_APPLICABLE') for d in row['enrichment'])
        assert set(p['operation'] for p in row['probes'])==set(SUPPORTED)
        assert all(p.get('reasons') for p in row['probes'] if p['status'] in ('not_supported','not_computable','requires_selected_pair'))
        assert all(p.get('query') for p in row['probes'] if p['status'] in ('computed','not_computable'))
    grouped=[key for g in coverage['sourceProfiles'] for key in g['metrics']]
    assert len(grouped)==len(set(grouped))==len(metrics) and set(grouped)==set(metrics)
    backlog={key for g in coverage['adapterBacklog'] for key in g['withoutAdapter']}
    assert backlog=={key for key,row in metrics.items() if row['engine']['status']=='not_supported'}
    # A structured carrier must not make an unsupported metric queryable.
    fuel=metrics['fuelPrices'];assert fuel['engine']['status']=='not_supported'
    assert all(p['status']=='not_supported' for p in fuel['probes'])
    assert any(d['state']=='ACQUIRED' for d in fuel['enrichment'])
    graph=connections(engine,coverage)
    assert {n['metric'] for n in graph['nodes']}==set(metrics)
    assert len(graph['nodes'])==len(metrics)
    for kind in ('same_theme','same_source_profile'):
        grouped=[key for g in graph['groups'] if g['kind']==kind for key in g['members']]
        assert len(grouped)==len(set(grouped))==len(metrics) and set(grouped)==set(metrics)
    for edge in graph['edges']:
        assert edge['left'] in metrics and edge['right'] in metrics
        assert edge['permitsCausalClaim'] is False and edge['permitsAutomaticCorrelation'] is False
        assert all(o.get('source') and o.get('provenance') for r in edge['observations'] for o in r['observations'])
        if edge['kind']!='context':assert edge['verification']=='components_reconciled'
        else:
            assert edge['verification']=='observations_available_context_only'
            if edge['id'] in ('environment_cost_waste','agriculture_center_context','commuting_gross_context','workplace_resident_employment','education_employment','household_housing','finance_cash_accrual','finance_mission_mix','debt_interest_context','recovery_current_revenue','security_social_context','demography_natural_transfers','school_fulltime_canteen','school_access_transport'):
                assert edge['associationAttempt']['status']=='computed'
                assert edge['associationAttempt']['result']['n']==7
                assert 'association_not_causation' in edge['associationAttempt']['warnings']
                if edge['id']=='workplace_resident_employment':assert 'workplace_activity_not_resident_employment' in edge['associationAttempt']['warnings']
            else:
                assert edge['associationAttempt']['status']=='not_computable'
                expected='agriculture_localized_and_center_scopes_not_jointly_comparable' if edge['id']=='agriculture_mixed_scope' else 'commuting_hybrid_denominator_pair_not_aligned' if edge['id']=='commuting_hybrid_context' else 'demography_school_site_observation_dates_not_attested_for_pairing' if edge['id']=='school_sites_pupils' else 'paired_period_mismatch'
                assert expected in edge['associationAttempt']['reasons']
    assert all(g['permitsCalculation'] is False for g in graph['groups'])
    contract=json.loads((ROOT/'data/enrichment-companion-contract.json').read_text())
    assert len(graph['companionLinks'])==len(contract['relationships'])
    for index,link in enumerate(graph['companionLinks']):
        assert link['rule']==contract['relationships'][index]
        assert link['permitsCausalClaim'] is False and link['permitsAutomaticCalculation'] is False
        assert link['evidence'] or link['reasons']
        assert all(k in metrics for k in link['references'].values() if k not in link['unresolvedReferences'])
    suite=run_suite(engine);assert suite['status']=='PASS',[(r['id'],r['errors']) for r in suite['results'] if r['errors']]
    assert suite['summary']['computed']>0 and suite['summary']['refused']>0
    assert suite==run_suite(engine), 'Question results must be deterministic'
    # The acceptance checker must catch altered arithmetic, lost warnings and false refusal success.
    calculated=next(r for r in suite['results'] if r['id']=='female_weighted')
    altered=copy.deepcopy(calculated['actual']);altered['result']['value']+=1
    assert 'unexpected_value:/result/value' in check_expected(altered,calculated['expected'])
    associated=next(r for r in suite['results'] if r['id']=='aligned_association')
    altered=copy.deepcopy(associated['actual']);altered['warnings']=[]
    assert 'missing_warning:association_not_causation' in check_expected(altered,associated['expected'])
    refusal=next(r for r in suite['results'] if r['id']=='mismatched_association')
    altered=copy.deepcopy(refusal['actual']);altered['status']='computed';altered['reasons']=[]
    assert 'unexpected_status' in check_expected(altered,refusal['expected'])
    with tempfile.TemporaryDirectory(prefix='a6-question-gate-') as directory:
        p=Path(directory)/'questions.json';manifest=json.loads(QUESTIONS.read_text())
        manifest['questions'].append(copy.deepcopy(manifest['questions'][0]));p.write_text(json.dumps(manifest))
        try:run_suite(engine,p)
        except ValueError as exc:assert str(exc)=='duplicate_question_id'
        else:raise AssertionError('duplicate questions accepted')
        changed=copy.deepcopy(catalog)
        changed['metrics']['tourismPresences']['rows'][0]['value']+=1
        changed_path=Path(directory)/'site-data.json';changed_path.write_text(json.dumps(changed))
        changed_engine=QueryEngine(changed_path,layer='effective')
        changed_graph=connections(changed_engine,coverage)
        link=next(e for e in changed_graph['edges'] if e['id']=='tourism_numerator')
        assert link['verification']=='not_verified' and link['reasons'], 'Altered data must not certify formula links'
    assert math.isclose(percentile([0,10,20,30],.95),28.5,abs_tol=1e-12)
    stats=summarize([30,0,20,10]);assert stats['medianMs']==15 and math.isclose(stats['p95Ms'],28.5,abs_tol=1e-12)
    assert coverage['catalogSha256']==engine.catalog_hash
    assert not any(k in coverage for k in ('timestamp','generatedAt','runtimeSeconds'))
    print('A6 complete coverage, typed connections, independent question expectations and percentile regression PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
