#!/usr/bin/env python3
"""Derived A6 coverage and typed connections; never a second metric inventory."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from enrichment_audit_matrix import build_matrix, validate_matrix
from enrichment_companion_evidence import companion_acquired_evidence
from semantic_query_engine import QueryEngine, ROOT, SUPPORTED, TEMPORAL
import semantic_query_business_adapters as business
import semantic_query_census_adapters as census
import semantic_query_distinct_finance_adapters as distinct
import semantic_query_demography_school_adapters as demography


def compact(result):
    return {k: result[k] for k in ('status', 'reasons', 'warnings', 'coverage') if k in result}


def probe_query(engine, key, dimension, operation, scope=None, catalog=None):
    selector = {'metric': key, 'dimension': dimension}
    query = {'operation': operation, 'selectors': [selector]}
    if operation in TEMPORAL:
        # This is a declared representative probe, not certification of every town/year.
        code = sorted(engine.codes)[0]
        selector['towns'] = [code]
        data=catalog if catalog is not None else engine.catalog
        row = next(r for r in data['metrics'][key]['rows'] if str(r['code']) == code)
        years = (row.get('series') or {}).get('years', [])
        if key in demography.KEYS:
            try:years=demography.available_periods(engine,key,dimension,row)
            except ValueError:years=[]
        elif key in distinct.KEYS:
            try:years=distinct.available_periods(engine,key,dimension,row)
            except ValueError:years=[]
        elif key in census.KEYS:
            try:years=census.available_periods(engine,key,dimension,row)
            except ValueError:years=[]
        elif key in business.KEYS and key!='microUnits':years=business.available_periods(engine,key,dimension,row)
        if operation in ('absolute_change', 'relative_change', 'percentage_points') and years:
            selector['periods'] = [str(years[0]), str(years[-1])]
    if operation == 'benchmark_gap':
        selector['towns'] = [sorted(engine.codes)[0]]
        query['benchmark'] = scope
    if operation == 'anomaly':
        query.update(rule='tukey_1_5_iqr', reference='selected_municipalities',
                     purpose='Coverage audit: descriptive selected peer group, no policy priority')
    return query


def audit(engine):
    catalog = engine.catalog
    registry_path = engine.path.with_name('source-registry.json')
    body = registry_path.read_bytes()
    enrichment = build_matrix(catalog, json.loads(body))
    validate_matrix(enrichment, require_complete=True)
    enrichment_rows = defaultdict(list)
    for row in enrichment['rows']:
        enrichment_rows[row['metricId']].append(row)
    metrics = []
    profiles = defaultdict(list)
    for entry in engine.coverage():
        key = entry['metric']; metric = catalog['metrics'][key]
        declared = entry['engine']; available = declared.get('operationsByDimension', {})
        probes = []
        for dimension, operations in available.items():
            for operation in SUPPORTED:
                if operation == 'correlation' and operation in operations:
                    probes.append(dict(dimension=dimension, operation=operation,
                        status='requires_selected_pair', reasons=['second_variable_and_purpose_required']))
                    continue
                if operation not in operations:
                    probes.append(dict(dimension=dimension, operation=operation,
                        status='not_supported', reasons=['operation_not_advertised_by_adapter']))
                    continue
                scopes = declared['benchmarkScopes'] if operation == 'benchmark_gap' else [None]
                for scope in scopes:
                    query = probe_query(engine, key, dimension, operation, scope, catalog)
                    result = engine.query(query)
                    probes.append(dict(dimension=dimension, operation=operation, query=query,
                        benchmarkScope=scope, **compact(result)))
        if not available:
            probes = [dict(dimension='unresolved', operation=o, status='not_supported',
                reasons=[declared['reason']]) for o in SUPPORTED]
        dims = [{k: r[k] for k in ('dimension','state','evidence','sourceReference','classificationOrigin') if k in r}
                for r in enrichment_rows[key]]
        profile = enrichment_rows[key][0]['sourceProfileId']
        rows = metric['rows']
        item = dict(metric=key, label=metric['meta']['label'], theme=metric['meta']['theme'],
            sourceProfileId=profile, sourceUrl=metric['sourceUrl'], period=str(metric['meta']['year']),
            primaryUnit=metric['meta'].get('unit', metric['meta'].get('summaryUnit')),
            publicRows=dict(total=len(rows), numeric=sum(type(r.get('value')) in (int,float) for r in rows),
                missing=sum(r.get('value') is None and not r.get('notApplicable') for r in rows),
                notApplicable=sum(bool(r.get('notApplicable')) for r in rows)),
            engine=declared, probes=probes, carriers=entry['carriers'], enrichment=dims,
            carrierPresenceCertifiesQuery=False)
        metrics.append(item); profiles[profile].append(item)
    groups = []
    for profile, items in sorted(profiles.items()):
        unsupported = [r for r in items if r['engine']['status'] == 'not_supported']
        acquired = sum(sum(d['state']=='ACQUIRED' for d in r['enrichment']) for r in unsupported)
        groups.append(dict(sourceProfileId=profile, metrics=[r['metric'] for r in items],
            withoutAdapter=[r['metric'] for r in unsupported], acquiredDimensionsWithoutMetricAdapter=acquired))
    backlog = sorted((g for g in groups if g['withoutAdapter']),
        key=lambda g: (-g['acquiredDimensionsWithoutMetricAdapter'], -len(g['withoutAdapter']), g['sourceProfileId']))
    states = Counter(p['status'] for r in metrics for p in r['probes'])
    return dict(schemaVersion=1, catalogSha256=engine.catalog_hash, engineSha256=engine.module_hash,
        auditImplementationSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sourceRegistrySha256=hashlib.sha256(body).hexdigest(),
        summary=dict(metrics=len(metrics), withAdapter=sum(bool(r['engine'].get('dimensions')) for r in metrics),
            withoutAdapter=sum(r['engine']['status']=='not_supported' for r in metrics),
            probes=dict(sorted(states.items())), sourceProfiles=len(groups)),
        metrics=metrics, sourceProfiles=groups, adapterBacklog=backlog,
        notes=['All IDs, themes, carrier paths and source profiles derived from canonical inputs',
            'ACQUIRED is A3 data availability, never automatic query certification',
            'Probes retain their exact town/period/scope: not exhaustive execution of every combination',
            'Correlation requires a selected pair; no indiscriminate pair mining',
            'Backlog order is adapter reuse opportunity from acquired dimensions, not policy priority or measured development cost'])


def connections(engine, coverage):
    """Grouping links are descriptive; formula links reconcile actual observations."""
    catalog=engine.catalog
    nodes = [{k:r[k] for k in ('metric','label','theme','sourceProfileId','period')} for r in coverage['metrics']]
    themes = defaultdict(list)
    for n in nodes: themes[n['theme']].append(n['metric'])
    groups = [dict(kind='same_theme', key=t, members=sorted(keys), permitsCalculation=False)
              for t, keys in sorted(themes.items())]
    groups += [dict(kind='same_source_profile', key=g['sourceProfileId'], members=g['metrics'],
                   permitsCalculation=False) for g in coverage['sourceProfiles']]
    recipes = [
        ('environment_residual_formula','wastePerResident','residualWaste','derived_product','Residual kg per resident is total kg per resident × (1 − separate collection share / 100); rounded published components, no independent causal evidence'),
        ('environment_cost_waste','wasteServiceCost','wastePerResident','context','2024 service cost and waste quantity per resident; distinct accounting scopes and potentially shared normalization, not TARI or efficiency'),
        ('environment_water_waste','waterNetworkLosses','wastePerResident','context','Water census 2018 and waste reporting 2024 are distinct periods and universes; no current environmental composite'),
        ('commuting_entry_numerator','inboundCommuters','inboundCommutersRate','shared_numerator','Habitual work commuters 2021 are the numerator; residents 2026 are a distinct denominator date'),
        ('commuting_exit_numerator','outboundCommuters','outboundCommutersRate','shared_numerator','Habitual work commuters 2021 are the numerator; municipal gross totals include moves within the selected group'),
        ('commuting_net_numerator','commuterBalance','commuterBalanceRate','shared_numerator','Net work balance 2021 is the numerator, with censused residents January 1 2021'),
        ('commuting_gross_context','inboundCommutersRate','outboundCommutersRate','context','Shared 2026 denominator and 2021 work flow universe; size and mechanical relationships are not independent causal effects'),
        ('commuting_hybrid_context','inboundCommutersRate','commuterBalanceRate','context','2026 and 2021 denominators are distinct despite the common 2021 numerator period'),
        ('commuting_retention_employment','selfContainment','employmentRate','context','Work retention 2021 and employment 2024 have different reference periods and universes'),
        ('demography_natural_transfers','naturalDemographicDynamics','totalResidentialMobility','context','Aligned calendar 2024 demographic events; distinct causes and statistical adjustments, no complete population accounting'),
        ('demography_citizenship_transfers','foreignResidents','foreignResidentialMobility','context','Citizenship stock 2025 and foreign transfers 2024 are distinct populations and periods'),
        ('school_fulltime_canteen','primaryFullTimeShare','schoolBuildingFacilities','context','Native 2024/25 pupils and building canteen declarations; no individual access, capacity or causal effect'),
        ('school_access_transport','schoolBuildingAccessibility','schoolBuildingTransport','context','Native 2024/25 building fields with different response denominators and missingness; no delivered pupil mobility'),
        ('school_sites_pupils','schoolSites','schoolStudents','context','Site stock exact date not attested; sites distinct from buildings and pupil locations'),
        ('debt_interest_context','financialDebtProfile','financialDebtProfile','context','Year-end D1 debt and interest share are distinct accounting dimensions; shared financing components, no causal claim'),
        ('recovery_current_revenue','fiscalRecoveryActivity','currentRevenueAccruedPerResident','context','Verification/control cash receipts and current accruals use distinct population bases; neither tax evasion nor office effectiveness'),
        ('works_capital_context','publicWorks','capitalExpenditureCommittedPerResident','context','Monitored project stock 2026 versus annual capital commitments 2025; no joint calculation across reference periods'),
        ('security_social_context','securityMissionExpenditurePerResident','socialMissionExpenditurePerResident','context','Mission commitments are resource classifications, not crime or delivered services'),
        ('finance_cash_balance','cashReceiptsPerResident','cashBalancePerResident','derived_difference','Annual December cash balance is receipts minus payments on the same next-January resident denominator'),
        ('finance_cash_accrual','cashReceiptsPerResident','currentRevenueAccruedPerResident','context','Cash receipts and current accruals have different accounting coverage and resident dates; descriptive only'),
        ('finance_mission_mix','educationMissionExpenditurePerResident','socialMissionExpenditurePerResident','context','Accounting commitments by mission share a population denominator; not service outputs'),
        ('census_gender_difference','maleEmploymentRate','employmentGenderGap','derived_difference','Resident employment gap is male minus female 15–64 rates in the same census year'),
        ('education_employment','diplomaPlus','employmentRate','context','Resident qualification and employment, 25–64 in 2024; association is not job matching or a policy effect'),
        ('household_housing','singleHouseholds','vacantHomes','context','Resident household composition and censused homes; not direct loneliness or vacant property availability'),
        ('asia_units_denominator','localUnits','employeesPerLocalUnit','ratio_component','ASIA units are the denominator of average employment per unit'),
        ('asia_employment_numerator','localEmployees','employeesPerLocalUnit','shared_numerator','ASIA annual average workplace employment is the numerator'),
        ('frame_turnover_numerator','businessTurnover','turnoverPerPersonEmployed','shared_numerator','Frame turnover in million euros converts to euros in the ratio numerator'),
        ('workplace_resident_employment','localEmployees','femaleEmploymentRate','context','Workplace employment and resident female employment are distinct universes; no individual matching'),
        ('business_tourism','localUnits','tourismPresences','context','Economic establishments and recorded tourist nights; periods and coverage must be explicit'),
        ('production_income','businessValueAdded','income','context','Workplace production and resident taxable income; neither municipal GDP nor a causal effect'),
        ('age_partition', 'population', 'ageDistribution', 'ratio_component', 'POSAS 2026 residents are the denominator of each explicit age band'),
        ('tourism_numerator', 'tourismPresences', 'tourismIntensity', 'shared_numerator', 'Nights 2025 are the numerator of intensity 2025/2026'),
        ('tourism_denominator', 'population', 'tourismIntensity', 'ratio_component', 'POSAS 2026 residents are the denominator of nights 2025'),
        ('ageing_care', 'ageDistribution', 'elderlyHomeCare', 'context', 'Demographic weight and delivered care; unmet need not observed'),
        ('work_childcare', 'femaleEmploymentRate', 'earlyChildhoodPotentialCapacityRate', 'context', 'Employment and potential educational supply; parental employment/access not observed'),
    ]
    edges = []
    for identity, left, right, kind, meaning in recipes:
        if left not in catalog['metrics'] or right not in catalog['metrics']: continue
        ld = 'age:85+' if left=='ageDistribution' else 'total'
        rd = 'age:85+' if right=='ageDistribution' else 'sex:total' if right=='elderlyHomeCare' else 'total'
        if identity=='debt_interest_context':ld,rd='part:debtPerResident','part:interestShare'
        qs = [{'metric':left,'dimension':ld}, {'metric':right,'dimension':rd}]
        if identity=='demography_natural_transfers':
            for q in qs:q['periods']=['2024']
        results = [engine.query({'operation':'compare','selectors':[s]}) for s in qs]
        verification = 'not_verified'; reasons = []
        if all(r['status']=='computed' for r in results):
            a = {o['geography']:o for o in results[0]['observations']}
            b = {o['geography']:o for o in results[1]['observations']}
            if kind!='context':
                component = 'numerator' if kind=='shared_numerator' else 'denominator'
                period_key = 'numeratorPeriod' if component=='numerator' else 'denominatorPeriod'
                import math
                assert set(a)==set(b)
                factor=1_000_000 if identity=='frame_turnover_numerator' else 1
                if identity=='environment_residual_formula':
                    share=engine.query({'operation':'compare','selectors':[{'metric':'recycling'}]})
                    results.append(share);p={o['geography']:o for o in share['observations']}
                    if share['status']=='computed' and set(a)==set(p) and all(a[c]['period']==b[c]['period']==p[c]['period'] and math.isclose(a[c]['value']*(1-p[c]['value']/100),b[c]['value'],rel_tol=0,abs_tol=1e-8) for c in a):verification='components_reconciled'
                    else:reasons=['formula_components_or_periods_not_reconciled']
                elif identity=='finance_cash_balance':
                    payments=engine.query({'operation':'compare','selectors':[{'metric':'siopePayments'}]})
                    results.append(payments);p={o['geography']:o for o in payments['observations']}
                    if payments['status']=='computed' and set(a)==set(p) and all(a[c]['period']==b[c]['period']==p[c]['period'] and a[c]['denominatorPeriod']==b[c]['denominatorPeriod']==p[c]['denominatorPeriod'] and math.isclose(a[c]['value']-p[c]['value'],b[c]['value'],rel_tol=0,abs_tol=1e-7) for c in a):verification='components_reconciled'
                    else:reasons=['formula_components_or_periods_not_reconciled']
                elif identity=='census_gender_difference':
                    female=engine.query({'operation':'compare','selectors':[{'metric':'femaleEmploymentRate'}]})
                    results.append(female)
                    f={o['geography']:o for o in female['observations']}
                    if female['status']=='computed' and set(a)==set(f) and all(a[c]['period']==b[c]['period']==f[c]['period'] and math.isclose(a[c]['value']-f[c]['value'],b[c]['value'],rel_tol=0,abs_tol=1e-8) for c in a):verification='components_reconciled'
                    else:reasons=['formula_components_or_periods_not_reconciled']
                elif not all(component in b[c] and math.isclose(a[c]['value']*factor, b[c][component], rel_tol=0, abs_tol=1e-8)
                    and a[c]['period']==b[c].get(period_key,b[c]['period']) for c in a):
                    reasons=['formula_components_or_periods_not_reconciled']
                else: verification='components_reconciled'
            else: verification='observations_available_context_only'
        else: reasons=sorted({reason for r in results for reason in r['reasons']})
        pair = engine.query(dict(operation='correlation', selectors=qs, method='spearman',
            axis='municipalities', purpose=meaning)) if kind=='context' else None
        edges.append(dict(id=identity, left=left, right=right, kind=kind, meaning=meaning,
            verification=verification, reasons=reasons, unitConversionFactor=1_000_000 if identity=='frame_turnover_numerator' else 1, permitsCausalClaim=False,
            permitsAutomaticCorrelation=False, observations=results,
            associationAttempt=pair, caveat='Context may be read side by side; joint calculations need coherent periods and universes'
            if kind=='context' else 'Mathematical dependence is not independent statistical evidence'))
    # Reuse the governed A3 relationship contract instead of reinventing its links.
    contract_path=engine.root/'data/enrichment-companion-contract.json'
    contract_body=contract_path.read_bytes();contract=json.loads(contract_body)
    companion_links=[]
    for index, rule in enumerate(contract['relationships']):
        target=rule['metricId'];dimensions=rule.get('dimensions',[rule.get('dimension')])
        references={k:v for k,v in rule.items() if k.endswith('MetricId') and k!='metricId'}
        evidence=[];reasons=[]
        unresolved=sorted({v for v in [target,*references.values()] if v not in catalog['metrics']})
        if unresolved:reasons=['catalog_reference_absent:'+v for v in unresolved]
        else:
            for dimension in dimensions:
                try:
                    proof=companion_acquired_evidence(metric_id=target,dimension=dimension,
                        catalog=catalog['metrics'],repo_root=engine.root)
                    if proof:evidence.append(dict(dimension=dimension,evidence=proof))
                    else:reasons.append('companion_evidence_not_available:'+str(dimension))
                except RuntimeError as exc:reasons.append('companion_verification_failed:'+str(exc))
        companion_links.append(dict(id='a3:'+str(index),metric=target,references=references,
            relationship=rule['relationship'],dimensions=dimensions,rule=rule,
            verification='a3_companion_evidence_verified' if not reasons else 'not_verified',
            evidence=evidence,reasons=reasons,unresolvedReferences=unresolved,
            rulePointer='/relationships/'+str(index),permitsCausalClaim=False,
            permitsAutomaticCalculation=False,
            caveat='A3 companion evidence does not certify A6 query support or joint temporal/statistical compatibility'))
    return dict(schemaVersion=1, catalogSha256=engine.catalog_hash, nodes=nodes, groups=groups, edges=edges,
        companionContractSha256=hashlib.sha256(contract_body).hexdigest(),companionLinks=companion_links,
        notes=['Group membership does not establish compatibility, correlation or causality',
            'Explicit recipes are analytical rules, not an alternative metric catalog',
            'No unreviewed causal edges or automatic search through all indicator pairs'])


def markdown(coverage, graph):
    s=coverage['summary']; lines=['# A6 — audit completo del motore','',
        f"Catalogo SHA-256 `{coverage['catalogSha256']}`; motore `{coverage['engineSha256']}`.",'',
        f"{s['metrics']} indicatori censiti; {s['withAdapter']} con adapter e {s['withoutAdapter']} senza adapter. {s['sourceProfiles']} profili fonte.",
        '', 'La presenza di dati A3 ACQUIRED non certifica interrogabilità. Ogni prova conserva la query esatta nel JSON. Le correlazioni richiedono una coppia scelta e motivata.', '',
        'Una prova può essere rifiutata anche con adapter presente: per esempio un trend con soli due punti non soddisfa il minimo di osservazioni. I conteggi sono derivati e vanno letti insieme alle query.','',
        '| Indicatore | Tema | Profilo fonte | Periodo | Adapter / motivo | Dimensioni abilitate | Prove calcolate / rifiutate | Dimensioni A3 acquisite |',
        '|---|---|---|---|---|---|---|---|']
    for r in coverage['metrics']:
        e=r['engine']; counts=Counter(p['status'] for p in r['probes'])
        lines.append('| '+' | '.join([r['metric'],r['theme'],r['sourceProfileId'],r['period'],e.get('adapter',e.get('reason','')),
            ', '.join(e.get('dimensions',[])).replace('|', '\\|') or '—',f"{counts['computed']} / {counts['not_computable']}",
            str(sum(d['state']=='ACQUIRED' for d in r['enrichment']))])+' |')
    lines+=['','## Collegamenti tipizzati','', '| Collegamento | Tipo | Verifica | Associazione |','|---|---|---|---|']
    for e in graph['edges']:
        pair=e['associationAttempt']; association=(pair['status']+': '+', '.join(pair['reasons'])) if pair else 'Non richiesta: dipendenza matematica'
        lines.append(f"| {e['left']} → {e['right']} | {e['kind']} | {e['verification']} | {association} |")
    lines+=['','## Collegamenti companion A3 già governati','',
        'Derivati dal contratto esistente e ricontrollati con il suo resolver. Una prova A3 non abilita automaticamente query A6 o confronti fra periodi.','',
        '| Indicatore | Riferimenti | Relazione | Dimensioni | Verifica / motivo |','|---|---|---|---|---|']
    for link in graph['companionLinks']:
        lines.append('| '+' | '.join([link['metric'],', '.join(k+'='+v for k,v in link['references'].items()),
            link['relationship'],', '.join(link['dimensions']),link['verification']+(': '+', '.join(link['reasons']) if link['reasons'] else '')])+' |')
    lines+=['','I gruppi per tema/fonte coprono tutti i nodi, senza generare migliaia di pseudo-relazioni. Nel JSON ogni collegamento esplicito conserva osservazioni, fonti, hash, componenti e periodi. Nessun collegamento causale.','',
        '## Opportunità di riuso degli adapter','', '| Profilo | Indicatori senza adapter | Dimensioni A3 già acquisite su questi indicatori |','|---|---|---|']
    for g in coverage['adapterBacklog']:lines.append(f"| {g['sourceProfileId']} | {len(g['withoutAdapter'])} | {g['acquiredDimensionsWithoutMetricAdapter']} |")
    lines+=['','Ordine diagnostico per riuso di dati acquisiti, non priorità politica o stima di costo. Le lacune di acquisizione A3 restano distinte dalle lacune del motore. Nessuna nuova acquisizione, UI o modifica dei dati.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,default=ROOT/'dist/data/site-data.json')
    p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    engine=QueryEngine(args.catalog,layer='effective'); coverage=audit(engine); graph=connections(engine,coverage)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in [('coverage',coverage),('connections',graph)]:
        (args.output_dir/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (args.output_dir/'audit.md').write_text(markdown(coverage,graph))
    print(json.dumps(coverage['summary']))


if __name__=='__main__':main()
