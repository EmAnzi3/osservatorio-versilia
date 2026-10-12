"""Frozen PNRR municipal implementing-body portfolio, amounts and ReGiS phase."""
from decimal import Decimal
import math
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('pnrrFunding', 'pnrrConcluded')
PERIOD = '2026-09-25'
POPULATION_PERIOD = '2026-01-01'
PATH = 'data/source-snapshots/pnrr-toscana-2026-09-25.json'
HASH = '0be700265929fe6690d82081e81e598d96ac6e55f2c26a8df3743729e40454c8'
OBJECT_HASH = '1e130c5ecd519eb183e0fbdcb579ae465f2be39568a2f888dfdb5a4606e00d86'
PUBLIC_HASHES = {'pnrrFunding': ['0220b2e81f50901e54693415d3920cd3f033202cbc5622e328a683b15bcb03bc', 'd9eb037b5626f4a6ef4521b287da9c70dc162245f7365a0b76d7301d639dbec2'], 'pnrrConcluded': ['05834ad91083c9a25e6add31555bf8cffb99197258e09812810a0db0abe09647']}
POPULATION_HASHES = {'b2cd8cee0508f9e673b305ae9f8e3f621f797a6eb002efd5c8013f04e198c8f0', '16958a4cc90899505ccbb62b022227321d1a18c2c4f37412bb6cebe4361a8ce7'}
NOTES = ['pnrr_municipal_implementing_body_not_all_projects_located_in_town',
         'pnrr_funding_not_paid_spent_total_cost_or_annual_flow',
         'pnrr_regis_macro_phase_5_not_completed_testing_or_service_opening',
         'pnrr_snapshot_20260925_population_20260101_distinct_dates',
         'pnrr_selected_normalized_records_not_full_original_csv_replay',
         'pnrr_old_snapshot_perTown_comparisons_not_current_catalog_values',
         'pnrr_numeric_rank_not_effectiveness_or_policy_priority']


def token(key, period):
    if str(period) not in ('2026', PERIOD): raise ValueError('pnrr_period_not_frozen')
    return PERIOD


def dimensions(key):
    return ['total', 'nativeRatio'] + (['fundingEuro'] if key == 'pnrrFunding' else ['concludedProjects', 'selectedProjects'])


def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank'] + (['weighted_ratio'] if dim == 'nativeRatio' else [])


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('pnrr_portfolio_history_not_frozen')
    if op == 'weighted_ratio' and dim != 'nativeRatio': raise ValueError('pnrr_native_ratio_dimension_required')
    if op == 'benchmark_gap': raise ValueError('pnrr_geographic_benchmark_not_reviewed')
    if op == 'anomaly': raise ValueError('pnrr_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('pnrr_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('pnrr_dimension_not_reviewed')
    if fingerprint(metric) not in PUBLIC_HASHES[key]: raise ValueError('pnrr_public_definition_or_values_changed')
    funding = key == 'pnrrFunding'; ratio = dim in ('total', 'nativeRatio')
    return dict(unit=('currency_per_resident' if ratio else 'currency') if funding else ('percent' if ratio else 'count'),
                population='PNRR or PNRR-PNC, pure PNC excluded; municipal implementing body; globally unique id_progetto',
                definition=('assigned PNRR amount / resident population' if ratio else 'assigned PNRR euro amount') if funding else ('ReGiS macro-phase 5 projects / selected projects × 100' if ratio else dim),
                method='decimal sum of frozen selected records; ReGiS macro-phase, not monitoring phase or effective closing date',
                frequency='portfolio_snapshot', periodBasis='25 September 2026 portfolio; 1 January 2026 residents for funding ratio',
                nativeComponentsAvailable=dim == 'nativeRatio', nativeRecordReplayAvailable=False,
                normalizedRecordReplayAvailable=True, adapter='pnrr/'+key+'/'+dim+'/v1')


def validated(engine):
    snap, ref = engine.file(PATH)
    if ref != dict(path=PATH, sha256=HASH) or fingerprint(snap) != OBJECT_HASH:
        raise ValueError('pnrr_frozen_input_changed')
    if len(engine._catalog['towns']) != 7 or {t['code']:t['name'] for t in engine._catalog['towns']} != TOWNS:
        raise ValueError('pnrr_municipal_identity_changed')
    population = engine._catalog['metrics']['population']
    if fingerprint(population) not in POPULATION_HASHES:
        raise ValueError('pnrr_resident_denominator_changed')
    pop = {r['code']:r for r in population['rows']}
    out = {c:dict(funding=Decimal(0),projects=0,concluded=0,indices=[]) for c in TOWNS}
    ids = set()
    for j,r in enumerate(snap['records']):
        matching=[c for c,t in TOWNS.items() if r['soggetto_attuatore']=='COMUNE DI '+t.upper()]
        if len(matching)!=1:raise ValueError('pnrr_portfolio_scope_not_reconciled')
        code=matching[0];identity=r['id_progetto']
        if (code not in TOWNS or identity in ids or not identity or r['area'] not in ('PNRR','PNRR-PNC')
            or r['forma_giuridica_soggetto_attuatore'] != 'Comune'
            or r['data_elaborazione'] != PERIOD):
            raise ValueError('pnrr_portfolio_scope_not_reconciled')
        ids.add(identity); amount=Decimal(r['importo_finanziato_pnrr'])
        if not amount.is_finite() or amount<0 or amount != amount.quantize(Decimal('0.01')):
            raise ValueError('pnrr_funding_component_invalid')
        s=out[code];s['funding']+=amount;s['projects']+=1
        s['concluded']+=r['fase_avanzamento_da_regis']=='5. conclusione';s['indices'].append(j)
    deep=engine._catalog['pnrrDeepDive']; towns={r['code']:r for r in deep['towns']}
    if set(towns)!=set(TOWNS) or deep['snapshotDate']!=PERIOD:
        raise ValueError('pnrr_public_components_not_reconciled')
    for key in KEYS: context(engine._catalog['metrics'][key],key,'total')
    for c,s in out.items():
        p=pop[c]['value']; t=towns[c]
        if type(p) not in (int,float) or p<=0 or int(p)!=p: raise ValueError('pnrr_resident_denominator_changed')
        s['residents']=p
        if (not s['projects'] or t['projects']!=s['projects'] or t['concluded']!=s['concluded']
            or Decimal(str(t['funding'])) != s['funding']): raise ValueError('pnrr_public_components_not_reconciled')
        for key in KEYS:
            row=next(r for r in engine._catalog['metrics'][key]['rows'] if r['code']==c)
            expected=float(s['funding'])/p if key=='pnrrFunding' else s['concluded']/s['projects']*100
            if not math.isclose(row['value'],expected,rel_tol=0,abs_tol=1e-10):
                raise ValueError('pnrr_public_components_not_reconciled')
    projects=sum(s['projects'] for s in out.values());concluded=sum(s['concluded'] for s in out.values())
    funding=sum((s['funding'] for s in out.values()),Decimal(0));residents=sum(s['residents'] for s in out.values())
    if (deep['totals']['projects']!=projects or deep['totals']['concluded']!=concluded
        or Decimal(str(deep['totals']['funding']))!=funding):raise ValueError('pnrr_aggregate_not_reconciled')
    for key,value in [('pnrrFunding',float(funding)/residents),('pnrrConcluded',concluded/projects*100)]:
        if not math.isclose(engine._catalog['metrics'][key]['aggregate']['value'],value,rel_tol=0,abs_tol=1e-10):
            raise ValueError('pnrr_aggregate_not_reconciled')
    return snap,ref,out


def observation(engine,key,index,dim,period,historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    if period!=PERIOD:raise ValueError('pnrr_period_not_frozen')
    snap,ref,rows=validated(engine);row=metric['rows'][index];code=row['code'];s=rows[code]
    funding=key=='pnrrFunding';ratio=dim in ('total','nativeRatio')
    n=float(s['funding']) if funding else s['concluded'];d=s['residents'] if funding else s['projects'];scale=1 if funding else 100
    value=row['value'] if ratio else float(s['funding']) if funding else s['concluded'] if dim=='concludedProjects' else s['projects']
    j=next(i for i,r in enumerate(engine._catalog['pnrrDeepDive']['towns']) if r['code']==code)
    field='funding' if funding else 'concluded' if dim=='concludedProjects' else 'projects'
    value_pointer=f'/metrics/{key}/rows/{index}/value' if ratio else f'/pnrrDeepDive/towns/{j}/{field}'
    pi=next(i for i,r in enumerate(engine._catalog['metrics']['population']['rows']) if r['code']==code)
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=value_pointer),
              dict(ref,kind='source_snapshot',recordPointers=[f'/records/{i}' for i in s['indices']],
                   componentField='importo_finanziato_pnrr' if funding else 'fase_avanzamento_da_regis',
                   selectionField='id_progetto',municipalAssignmentField='soggetto_attuatore',
                   sourceLocalizationCodes=[snap['records'][i]['codistat'] for i in s['indices']],sourceDocumentSha256=snap['sourceSnapshotSha256'],
                   replayScope='selected normalized 101 project records; full 45364-row CSV not frozen',
                   nativeComponents=dict(numerator=n,denominator=d,scale=scale)),
              dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                   numeratorPointer=f'/pnrrDeepDive/towns/{j}/'+('funding' if funding else 'concluded'),
                   denominatorPointer=f'/metrics/population/rows/{pi}/value' if funding else f'/pnrrDeepDive/towns/{j}/projects')]
    result=dict(ctx,metric=key,dimension=dim,geography=code,period=period,value=value,
                source=snap['url'],evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False,missingReason=None)
    if dim=='nativeRatio':result.update(numerator=n,denominator=d,scale=scale,numeratorPeriod=PERIOD,
                                       denominatorPeriod=POPULATION_PERIOD if funding else PERIOD)
    return result,NOTES[:]
