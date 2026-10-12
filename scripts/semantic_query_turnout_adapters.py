"""Frozen election records: exact consultations, electorate and questions explicit."""
import base64
import gzip
import hashlib
import json
import math
import re
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('voterTurnout',)
FAMILIES = ('politiche_camera','europee','regionali_toscana','referendum')
CURRENT = 'referendum-20260322-q1'
PUBLIC_HASH = 'd6a0dc624c2960248085f0f9334d210de1e42f227d4345fb241d8726c2e370cb'
PART_HASHES = ('97a4dece82ff4d5768592564069f53e71555343eba4f164e1f3645c5973b91bc',
               'c4ebe9821a8811038e26e3be0fa5671fc90188d60447bff1143dfac1d9a63cb2',
               '68d45acefdb12367159f6916ca4e5f6a29a574fc0c2f5c4530e40c38dd4a221d',
               '5da818bbb8b9eac838a6601fb5c151f78310384749c885fd65da5cd52ab103ad')
PAYLOAD_SHA = '686876cefec01de09b5205b332cc9f2544508d0cae070f39ca28542a354219b8'
OBJECT_HASH = 'c43d08c7bce6b93ab8da1296f7d28b0f0a6bfda6b9c127eb68b9e30faaa93369'
NOTES = ['turnout_electors_not_resident_population_or_valid_votes',
         'turnout_same_consultation_question_and_electoral_universe_required',
         'turnout_normalized_archive_replay_not_original_DAIT_files',
         'turnout_municipal_latest_different_dates_and_province_context_excluded',
         'turnout_irregular_history_not_annual_series_or_continuity_attestation',
         'turnout_sex_only_when_both_native_components_complete_no_imputation',
         'turnout_numerical_rank_not_civic_quality_or_policy_priority']


def dimensions(key):
    return ['total','nativeRatio'] + ['family:'+f+suffix for f in FAMILIES for suffix in
        ('','|nativeRatio','|sex:men','|sex:women','|sex:men|nativeRatio','|sex:women|nativeRatio')]


def resolve(dim):
    if dim not in dimensions(KEYS[0]): raise ValueError('turnout_dimension_not_reviewed')
    family='referendum' if dim in ('total','nativeRatio') else dim.split('|')[0][7:]
    sex='male' if '|sex:men' in dim else 'female' if '|sex:women' in dim else ''
    return family,sex,'nativeRatio' in dim


def token(key, period):
    p=str(period)
    if p=='2026': return CURRENT
    if not re.fullmatch(r'(politiche_camera|europee|regionali_toscana)-[0-9]{8}|referendum-[0-9]{8}-q[0-9]+(?:,00)?',p):
        raise ValueError('turnout_explicit_consultation_id_required')
    return p


def order(period):
    # Quesiti are identities, not fractions of a calendar year.
    return (period.split('-')[1], period)


def scopes(key, dim): return []


def sex_complete(event):
    # The normalized 1990 regional record marks mfComplete=true but female
    # denominators are zero and rates null; never interpret these as real zeros.
    return all(type(r[p+'Electors']) is int and r[p+'Electors']>0
               and type(r[p+'Voters']) is int and r[p+'Turnout'] is not None
               for r in event['municipalities'] for p in ('male','female'))


def operations(key, dim):
    family,sex,native=resolve(dim)
    return ['compare','rank'] + (['weighted_ratio'] if native else []) + (['series'] if family!='referendum' else [])


def selection_guard(key, dim, op):
    family,sex,native=resolve(dim)
    if op=='series' and family=='referendum': raise ValueError('turnout_referendum_questions_not_a_single_series')
    if op in ('absolute_change','relative_change','percentage_points','trend'):
        raise ValueError('turnout_electoral_universe_continuity_not_attested')
    if op=='weighted_ratio' and not native: raise ValueError('turnout_native_ratio_dimension_required')
    if op=='benchmark_gap': raise ValueError('turnout_geographic_benchmark_not_reviewed')
    if op=='anomaly': raise ValueError('turnout_peer_anomaly_not_reviewed')
    if op=='correlation': raise ValueError('turnout_pair_not_jointly_reviewed')


def context(metric, key, dim):
    family,sex,native=resolve(dim)
    if key not in KEYS or fingerprint(metric)!=PUBLIC_HASH: raise ValueError('turnout_public_definition_or_values_changed')
    return dict(unit='percent',population=f'{family} electorate registered for selected consultation; '+(sex or 'all sexes'),
                definition='voters / registered electors × 100; same consultation, question and sex',
                method='exact native count ratio' if native or dim=='total' else 'normalized archive rate rounded to four decimals',
                frequency='irregular_electoral_consultation',periodBasis='exact archive consultation ID and canonical date token; not necessarily full voting interval; question kept separate',
                nativeComponentsAvailable=native,nativeRecordReplayAvailable=False,
                normalizedRecordReplayAvailable=True,adapter='turnout/'+dim+'/v1')


def frozen(engine):
    parts=[dict(path=f'data/affluenza/archive-v2-{i:02d}.b64',sha256=h) for i,h in enumerate(PART_HASHES)]
    reference=dict(kind='reconstructed_source_snapshot',path='data/affluenza/archive-v2',sha256=PAYLOAD_SHA,
                   sha256Basis='decoded_json_bytes',encoding='concatenate_ascii_base64_gzip_json',parts=parts,
                   replayScope='normalized municipal election aggregates; original DAIT files and voter records not replayed')
    if not hasattr(engine,'_turnout_payload'):
        bodies=[(engine.root/p['path']).read_bytes() for p in parts]
        if any(hashlib.sha256(b).hexdigest()!=p['sha256'] for b,p in zip(bodies,parts)):
            raise ValueError('turnout_frozen_fragment_changed')
        raw=gzip.decompress(base64.b64decode(b''.join(b.strip() for b in bodies),validate=True))
        if hashlib.sha256(raw).hexdigest()!=PAYLOAD_SHA: raise ValueError('turnout_frozen_payload_changed')
        engine._turnout_payload=json.loads(raw),reference.copy()
    snap,ref=engine._turnout_payload
    if ref!=reference or fingerprint(snap)!=OBJECT_HASH: raise ValueError('turnout_frozen_payload_changed')
    return snap,ref


def validated(engine,key):
    snap,ref=frozen(engine)
    towns=engine._catalog['towns']
    if len(towns)!=7 or {t['code']:t['name'] for t in towns}!=TOWNS:
        raise ValueError('turnout_municipal_identity_changed')
    public=engine._catalog['metrics'][key];context(public,key,'total')
    for family in FAMILIES:
        events=snap['families'][family]['events']
        ids=[e['id'] for e in events]
        if len(set(ids))!=len(ids): raise ValueError('turnout_duplicate_consultation')
        for e in events:
            rows=e['municipalities']
            if len(rows)!=7 or {r['code']:r['name'] for r in rows}!=TOWNS:
                raise ValueError('turnout_archive_identity_changed')
            for r in rows:
                n,d=r['voters'],r['electors']
                if type(n) is not int or type(d) is not int or not 0<=n<=d or d<=0 or round(n/d*100,4)!=r['turnout']:
                    raise ValueError('turnout_count_ratio_not_reconciled')
                if sex_complete(e):
                    for prefix in ['male','female']:
                        n,d=r[prefix+'Voters'],r[prefix+'Electors']
                        if type(n) is not int or type(d) is not int or not 0<=n<=d or d<=0 or round(n/d*100,4)!=r[prefix+'Turnout']:
                            raise ValueError('turnout_sex_components_not_reconciled')
                    if r['maleVoters']+r['femaleVoters']!=r['voters'] or r['maleElectors']+r['femaleElectors']!=r['electors']:
                        raise ValueError('turnout_sex_partition_not_reconciled')
            aggregate=e['versilia'];n=sum(r['voters'] for r in rows);d=sum(r['electors'] for r in rows)
            if aggregate['voters']!=n or aggregate['electors']!=d or aggregate['turnout']!=round(n/d*100,4):
                raise ValueError('turnout_aggregate_not_reconciled')
            if sex_complete(e):
                for prefix in ['male','female']:
                    n=sum(r[prefix+'Voters'] for r in rows);d=sum(r[prefix+'Electors'] for r in rows)
                    if aggregate[prefix+'Turnout']!=round(n/d*100,4):
                        raise ValueError('turnout_sex_aggregate_not_reconciled')
    current=snap['families']['referendum']['events'][-1]
    if current['id']!=CURRENT: raise ValueError('turnout_current_consultation_changed')
    native={r['code']:r for r in current['municipalities']}
    for r in public['rows']:
        cell=native[r['code']]
        if not math.isclose(r['value'],cell['voters']/cell['electors']*100,rel_tol=0,abs_tol=1e-12):
            raise ValueError('turnout_current_catalog_not_reconciled')
    if not math.isclose(public['aggregate']['value'],current['versilia']['voters']/current['versilia']['electors']*100,rel_tol=0,abs_tol=1e-12):
        raise ValueError('turnout_current_catalog_not_reconciled')
    return snap,ref


def available_periods(engine,key,dim,row):
    snap,_=validated(engine,key);family,_,_=resolve(dim)
    return [e['id'] for e in snap['families'][family]['events']]


def default_period(engine,key,dim):
    return CURRENT if dim in ('total','nativeRatio') else available_periods(engine,key,dim,None)[-1]


def observation(engine,key,index,dim,period,historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    snap,ref=validated(engine,key);family,sex,native=resolve(dim)
    events=snap['families'][family]['events']
    matches=[(i,e) for i,e in enumerate(events) if e['id']==period]
    if not matches or (dim in ('total','nativeRatio') and period!=CURRENT):
        raise ValueError('turnout_consultation_not_available_in_selected_family')
    j,event=matches[0];code=metric['rows'][index]['code']
    k=next(i for i,r in enumerate(event['municipalities']) if r['code']==code);r=event['municipalities'][k]
    missing=bool(sex and not sex_complete(event))
    n=r[sex+'Voters'] if sex else r['voters'];d=r[sex+'Electors'] if sex else r['electors']
    field=sex+'Turnout' if sex else 'turnout'
    value=None if missing else n/d*100 if native or dim=='total' else r[field]
    pointer=f'/families/{family}/events/{j}/municipalities/{k}'
    catalog_evidence=dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                          definitionPointer=f'/metrics/{key}',carrierIsCurrentAlias=dim in ('total','nativeRatio'))
    if dim=='total':catalog_evidence['valuePointer']=f'/metrics/{key}/rows/{index}/value'
    evidence=[catalog_evidence,dict(ref,recordPointer=pointer,valuePointer=pointer+'/'+field,
                  valueRole='four-decimal archive rate; native query ratio derived from components' if native else 'published observation',
                  numeratorPointer=pointer+'/'+(sex+'Voters' if sex else 'voters'),
                  denominatorPointer=pointer+'/'+(sex+'Electors' if sex else 'electors'))]
    result=dict(ctx,metric=key,dimension=dim,geography=code,period=period,value=value,
                consultationId=event['id'],date=event['date'],questionId=event['questionId'],question=event['question'],
                sexComponentsComplete=sex_complete(event),sourceSexCompletenessFlag=event['versilia']['mfComplete'],
                source=metric['sourceUrl'],evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=missing,missingReason='official_sex_components_incomplete' if missing else None)
    if native and not missing:result.update(numerator=n,denominator=d,scale=100,numeratorPeriod=period,denominatorPeriod=period)
    return result,NOTES[:]
