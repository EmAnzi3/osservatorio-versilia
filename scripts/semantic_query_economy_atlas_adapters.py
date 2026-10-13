"""Exact frozen ATECO rows and territorial totals; no hierarchy pooling."""
import base64
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from semantic_query_library_adapters import TOWNS, fingerprint

ROOT = Path(__file__).resolve().parents[1]
KEYS = ('economyActivityAtlas',)
PUBLIC_HASH = '85e540a37d121924b93ae9428bfff6a32cff32d8b7ffd214be154b0da17c89a2'
FILES = {'metadata.json': '0a98bd33d959e0ef6576fec6547ecaaa2be5ac5c2fb43925a6d71e4781dfc93b', 'atlas-00.b64': '676cda3d36a33f92d7b9367f3136da22ca5e512a363cabeca3f9006cbd542550', 'atlas-01.b64': 'a95c66c11d2f0157ad72f638d8900af1400037d5157b52b43c1208b68995dca5', 'atlas-02.b64': '37749d7c6b283518b88c0273ff27606c44fb73502eb3374a442a7074fee39e29', 'atlas-03.b64': '9e250808c909415e27a8e98697431b2ec48c7f162f30776c6c0a996b94e1bb81', 'atlas-04.b64': '1df5848c8e3c0eb00f172e10dee6b0c0b9394ae768eba096f80c3f64b4231295', 'atlas-05.b64': '79866c7a42b1500a7147bfd2af908bad50e1d672106ebea9cb82cd4a4ee0d36f', 'atlas-06.b64': '86203e202cfda93c476255385103b2975600c6fce76ec54acaed94636c05984c', 'atlas-07.b64': 'ab875f28adf073e567ab332a79b695ef9608b45b4e7329f50adc84b01c9eff01', 'atlas-08.b64': '12eb46c5b97d7f660f8dfba5d83c6bd81992afa34b67ba49cd24c7a0e340ae7c', 'atlas-09.b64': 'a4183edb8518b531ea924e6ab9ae3b629bcaab5aec4580ffd9b743ad65d41244', 'ateco-taxonomy-00.b64': 'e280ff179c210456a0a72f73b7b8cdf1c918275ec2168768e53c7eff45c42085', 'ateco-taxonomy-01.b64': 'b93d4770f3c9ae315df4cfc7094cf33fbe0671b0ceb3b8bae73c6f90bf4b36c7', 'ateco-taxonomy-02.b64': '65fbeca3e02f8530d7e6caa0c941975ff8f726035bf9d51b1237018ad736c759', 'ateco-taxonomy-03.b64': '9f52215a8bb4a8a23c6cdc75bc110d33ceced61b9fdb28fa84f86de622726c5b', 'ateco-taxonomy-04.b64': 'f4d815363384a7bfd738eca2b4abb6c0d5681431fa64d210e71d27b56f4b160f'}
NOTES = ['atlas_register_local_units_not_enterprises_jobs_or_istat_asia',
         'atlas_exact_category_row_not_exhaustive_hierarchy_branch_total',
         'atlas_ateco2007_update2022_no_ateco2025_conversion',
         'atlas_null_not_zero_no_imputation_or_descendant_substitution',
         'atlas_compact_normalized_replay_not_original_register_files',
         'atlas_2014_2025_series_continuity_not_certified_for_changes',
         'atlas_territorial_total_reconciled_no_ateco_hierarchy_sum',
         'atlas_artisan_count_only_2025_not_historical_series',
         'atlas_numerical_rank_not_economic_strength_or_policy_priority']


def freeze(value):
    if isinstance(value,dict):return MappingProxyType({k:freeze(v) for k,v in value.items()})
    if isinstance(value,list):return tuple(freeze(v) for v in value)
    return value


@lru_cache(maxsize=1)
def decoded(bodies):
    # Bytes are immutable cache keys; the returned trees are recursively immutable.
    raw=json.loads(gzip.decompress(base64.b64decode(b''.join(x.strip() for x in bodies[1:11]))))
    taxonomy=json.loads(gzip.decompress(base64.b64decode(b''.join(x.strip() for x in bodies[11:]))))
    return freeze(raw),freeze(taxonomy)


def payload():
    bodies=[]
    for name,sha in FILES.items():
        body=(ROOT/'data/economy-atlas'/name).read_bytes()
        if hashlib.sha256(body).hexdigest()!=sha:raise ValueError('atlas_frozen_file_bytes_changed')
        bodies.append(body)
    return decoded(tuple(bodies))


def token(key,period):
    if str(period) not in tuple(str(y) for y in range(2014,2026)):
        raise ValueError('atlas_only_2014_2025_frozen')
    return str(period)


def dimensions(key):
    data,_=payload()
    return ['territoryTotal']+[f'ateco:{r[0]}|{m}' for r in data['c'] for m in ('active','artisan')]


def resolve(dim):
    if dim=='territoryTotal':return None,'active'
    m=re.fullmatch(r'ateco:([A-Z] [0-9]{2,6})\|(active|artisan)',dim)
    if not m:raise ValueError('atlas_exact_category_and_measure_required')
    return m.groups()


def scopes(key,dim):return []
def operations(key,dim):return ['compare','rank']+([] if resolve(dim)[1]=='artisan' else ['series'])
def available_periods(engine,key,dim,row):return [str(y) for y in payload()[0]['y']]


def selection_guard(key,dim,op):
    if op in ('absolute_change','relative_change','percentage_points','trend'):
        raise ValueError('atlas_temporal_continuity_not_reviewed')
    if op=='series' and resolve(dim)[1]=='artisan':raise ValueError('atlas_artisan_only_2025_frozen')
    if op=='weighted_ratio':raise ValueError('atlas_hierarchy_and_scope_pooling_not_reviewed')
    if op=='benchmark_gap':raise ValueError('atlas_absolute_regional_volume_not_municipal_benchmark')
    if op=='anomaly':raise ValueError('atlas_peer_anomaly_not_reviewed')
    if op=='correlation':raise ValueError('atlas_pair_not_jointly_reviewed')


def context(metric,key,dim):
    if fingerprint(metric)!=PUBLIC_HASH:raise ValueError('atlas_public_definition_or_values_changed')
    code,measure=resolve(dim)
    return dict(unit='number',population='registered active local units in the frozen territorial total' if code is None else 'registered local units recorded directly at the exact ATECO code; not all descendants',
                definition='frozen territorial active-local-unit total' if code is None else f'exact ATECO {code} '+measure+' local-unit count',
                method='direct compact snapshot value; no hierarchy sums or imputation',
                frequency='annual_snapshot' if measure=='active' else 'single_year_snapshot',
                periodBasis='2014–2025 in ATECO2007 update2022; artisan only2025, classification continuity not attested',
                nativeComponentsAvailable=False,nativeRecordReplayAvailable=False,
                normalizedRecordReplayAvailable=True,adapter='economy_atlas/'+dim+'/v1')


def observation(engine,key,index,dim,period,historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim);data,taxonomy=payload()
    if len(engine._catalog['towns'])!=7 or {t['code']:t['name'] for t in engine._catalog['towns']}!=TOWNS:
        raise ValueError('atlas_municipal_identity_changed')
    row=metric['rows'][index];ti=next(i for i,t in enumerate(data['t']) if t[1]==row['town']);yi=data['y'].index(int(period))
    code,measure=resolve(dim)
    if measure=='artisan' and period!='2025':raise ValueError('atlas_artisan_only_2025_frozen')
    if code is None:value=data['tt'][ti][yi];pointer=f'/tt/{ti}/{yi}';label='Territorial active local units';region=data['rt'][yi]
    else:
        ri=next(i for i,r in enumerate(data['c']) if r[0]==code);record=data['c'][ri]
        value=record[3+ti][1] if measure=='artisan' else record[3+ti][0][yi]
        pointer=f'/c/{ri}/{3+ti}/'+('1' if measure=='artisan' else f'0/{yi}')
        digits=code.split()[1];pretty=digits if len(digits)==2 else digits[:2]+'.'+digits[2:] if len(digits)<=4 else digits[:2]+'.'+digits[2:4]+'.'+digits[4:]
        label=taxonomy[pretty];region=record[2] if measure=='artisan' else record[1][yi]
    refs=[dict(kind='source_snapshot',path='data/economy-atlas/'+n,sha256=sha,encoding='base64-gzip concatenated atlas chunks' if n.startswith('atlas-') else 'metadata or taxonomy',replayScope='compact normalized payload only') for n,sha in FILES.items()]
    refs[1].update(valuePointer=pointer,decodedScope='JSON obtained by concatenating atlas-00..09 then base64 and gzip decoding')
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=value,
                source=metric['sourceUrl'],categoryCode=code,categoryLabel=label,regionalContextValue=region,
                evidence=refs,provenance=refs,notApplicable=False,dataUnavailable=value is None,
                missingReason='atlas_direct_category_value_not_available' if value is None else None),NOTES[:]
