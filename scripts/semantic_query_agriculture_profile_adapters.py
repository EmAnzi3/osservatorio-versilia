"""Frozen census profiles and regional organic share; no synthetic index."""
import hashlib,json,math
from semantic_operations import finite

KEYS=('agriculturalRenewalAndLeadership','agriculturalDiversificationAndModernization','organicAgriculturalAreaShare')
PARTS={KEYS[0]:('youngManagers','femaleHolders'),KEYS[1]:('connectedActivities','informatization','innovation')}
CENSUS='data/source-snapshots/istat-agricoltura-ii-2020.json'
ORGANIC='data/source-snapshots/toscana-indicatori-v1.5.0.json'
BENCHMARK='data/source-snapshots/a3-regione-toscana-indicators-benchmark-2024.json'
ISTAT='https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/'
REGION='https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali'
HASHES={CENSUS:('b3971eeeec4a040557d8f449b75f0367c8d9425d2acb94c9b690543f4c691575','c7f882cf8dbd43acfcb6f636a3782cd4066c59c697b2c970f674875c70387a08'),ORGANIC:('fecb17aa645878d58a4f22d3897f21c7dfa4b050d47f7d095bf269423bc51c77','83eb8bf4143efd70e21e90b0dbad4a236c448d5d930cc671de505eadf742e69a'),BENCHMARK:('79756910e1a13307fb0bde0ab9253777d19df7d1e259c630b3a1de6d9c72dd87','ec6175398eb795d58e39ec9979f79fafc4f2717fea670d61b026aabed64fa301')}
UNIVERSES={'youngManagers':'excludingCollectiveProperties','femaleHolders':'farmsWithHolder','connectedActivities':'generalFarms','informatization':'excludingCollectiveProperties','innovation':'excludingCollectiveProperties'}
PUBLIC_UNIVERSES={'youngManagers':'Aziende agricole escluse le proprietà collettive','femaleHolders':'Aziende con conduttore','connectedActivities':'Aziende agricole','informatization':'Aziende agricole escluse le proprietà collettive','innovation':'Aziende agricole escluse le proprietà collettive'}

def dimensions(key):return ['total',*('part:'+p for p in PARTS[key])] if key in PARTS else ['total']
def part(key,dim):return PARTS[key][0] if dim=='total' else dim[5:]
def weighted(key,dim):return key in PARTS and dim in dimensions(key)
def scopes(key,dim='total'):return ['tuscany'] if key==KEYS[2] else []
def operations(key,dim):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dim) else ['series','benchmark_gap'])]
def selection_guard(key,dim,op):
 if op=='correlation':raise ValueError('agriculture_profiles_pair_not_jointly_reviewed')
 if op in ('absolute_change','relative_change','trend','percentage_points') or (op=='series' and key in PARTS):raise ValueError('agriculture_profiles_temporal_change_not_reviewed')
 if op=='weighted_ratio' and key==KEYS[2]:raise ValueError('agriculture_profiles_no_organic_area_components')
 if op=='benchmark_gap' and key in PARTS:raise ValueError('agriculture_profiles_no_geographic_benchmark')
 if op=='anomaly':raise ValueError('agriculture_profiles_peer_anomaly_not_reviewed')

def close(a,b):
 if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-8):raise ValueError('agriculture_profiles_public_native_mismatch')
def frozen(engine,path):
 s,ref=engine.file(path);expected,structure=HASHES[path]
 if ref.get('sha256')!=expected or hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()!=structure:raise ValueError('agriculture_profiles_frozen_input_changed')
 return s,ref
def context(m,key,dim):
 if dim not in dimensions(key):raise ValueError('agriculture_profiles_dimension_not_reviewed')
 census=key in PARTS
 if m['meta'].get('unit')!='percent' or str(m['meta'].get('year'))!=('2020' if census else '2024') or m.get('sourceUrl')!=(ISTAT if census else REGION):raise ValueError('agriculture_profiles_definition_changed')
 if census and (m['meta'].get('compositeType')!='ratioProfile' or m.get('method',{}).get('snapshot')!=CENSUS):raise ValueError('agriculture_profiles_definition_changed')
 p=part(key,dim) if census else 'organicAreaShare'
 return dict(unit='percent',population=UNIVERSES[p]+'; holdings attributed to the frozen municipal census code' if census else 'agricultural utilized area in regional municipal indicator ind20; frozen published denominator not acquired',definition={'youngManagers':'holdings with farm manager aged up to 40, excluding collective properties','femaleHolders':'holdings with female holder, not female manager or distinct women','connectedActivities':'holdings with connected activities, not sum of overlapping activity subcategories','informatization':'informatized holdings, excluding collective properties','innovation':'holdings with innovation investment in 2018–2020, excluding collective properties'}[p]+'; separate numerator/denominator universe; no composite score' if census else 'published share of utilized agricultural area cultivated organically; not share of farms',method='frozen Istat census native counts, numerator/denominator*100' if census else 'Regione Toscana published percentages; no hectares reconstructed',frequency='census' if census else 'annual',periodBasis=('census 2020; investment activity 2018–2020' if p=='innovation' else 'census 2020') if census else 'annual 2018–2024; only 2024 geographic benchmark reviewed',adapter='agriculture-profiles/'+key+'/'+p+'/v1')
def observation(engine,key,index,dim,period,historical):
 m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dim);parts={};warnings=['agriculture_profiles_no_individual_holding_or_unique_person_replay','agriculture_profiles_not_policy_effect_or_synthetic_index','agriculture_profiles_overlapping_characteristics_not_additive','agriculture_profiles_manager_not_holder','agriculture_profiles_2020_census_not_current_conditions']
 town=next((t for t in engine._catalog['towns'] if t['code']==row['code']),None)
 if not town or row['town']!=town['name'] or row.get('slug')!='-'.join(town['name'].lower().split()) or row.get('notApplicable') or row.get('dataUnavailable') or len(m['rows'])!=7 or len({r['code'] for r in m['rows']})!=7:raise ValueError('agriculture_profiles_public_identity_changed')
 if key in PARTS:
  if period!='2020':raise ValueError('agriculture_profiles_census_period_not_frozen')
  s,ref=frozen(engine,CENSUS);p=part(key,dim);n=s['towns'][row['code']];v=n[p]
  if n['name']!=row['town'] or n['slug']!=row['slug'] or set(s['towns'])!=set(engine.codes):raise ValueError('agriculture_profiles_native_identity_changed')
  if v['universe']!=UNIVERSES[p] or type(v['numerator']) is not int or type(v['denominator']) is not int or not 0<=v['numerator']<=v['denominator'] or v['denominator']<=0:raise ValueError('agriculture_profiles_invalid_components')
  expected=v['numerator']/v['denominator']*100;close(v['value'],expected)
  if [x['key'] for x in row['parts']]!=list(PARTS[key]) or row.get('series') is not None:raise ValueError('agriculture_profiles_public_parts_changed')
  j=PARTS[key].index(p);public=row['parts'][j]
  if public.get('unit')!='percent' or public.get('universe')!=PUBLIC_UNIVERSES[p] or row.get('year')!=2020:raise ValueError('agriculture_profiles_public_parts_changed')
  close(public['numerator'],v['numerator']);close(public['denominator'],v['denominator']);close(public['value'],expected);close(row['value'],n[PARTS[key][0]]['value'])
  value=row['value'] if dim=='total' else public['value'];pointer=f'/metrics/{key}/rows/{index}/'+('value' if dim=='total' else f'parts/{j}/value');record='/towns/'+row['code']+'/'+p
  parts=dict(numerator=v['numerator'],denominator=v['denominator'],scale=100,numeratorPeriod='2020',denominatorPeriod='2020')
 else:
  s,ref=frozen(engine,ORGANIC);rs=s['indicators'][key]['rows'];n=next((r for r in rs if r['code']==row['code']),None)
  if not n or n['town']!=row['town'] or s['indicators'][key]['sourceCode']!='ind20' or set(r['code'] for r in rs)!=set(engine.codes):raise ValueError('agriculture_profiles_native_identity_changed')
  if row.get('series')!={'years':n['years'],'values':n['values']}:raise ValueError('agriculture_profiles_public_series_changed')
  close(row['value'],n['values'][-1])
  if not period.isdigit() or int(period) not in n['years']:raise ValueError('agriculture_profiles_organic_period_not_frozen')
  i=n['years'].index(int(period));value=n['values'][i];record=f'/indicators/{key}/rows/{rs.index(n)}/values/{i}';pointer=f'/metrics/{key}/rows/{index}/series/values/{i}'
  warnings+=['agriculture_profiles_no_organic_hectares_or_pooled_share','agriculture_profiles_municipal_median_not_territorial_share','agriculture_profiles_rounded_early_annual_values_no_temporal_change_review']
 evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record)]
 return dict(ctx,**parts,metric=key,dimension=dim,geography=row['code'],period=period,value=value,source=ISTAT if key in PARTS else REGION,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False),warnings
def benchmark(engine,key,scope,municipal):
 if key!=KEYS[2] or scope!='tuscany' or municipal['period']!='2024':raise ValueError('agriculture_profiles_benchmark_scope_or_period_not_reviewed')
 s,ref=frozen(engine,BENCHMARK);b=s['benchmarks'][key];meta=engine._catalog['metrics'][key]['meta']['benchmark']
 if b['year']!='2024' or b['unit']!='percent' or meta.get('sourceSnapshot')!=BENCHMARK or str(meta['year'])!='2024' or meta['url']!=REGION:raise ValueError('agriculture_profiles_benchmark_definition_changed')
 close(meta['tuscany'],b['tuscany']);close(s['publicRows'][key][next(t['name'] for t in engine._catalog['towns'] if t['code']==municipal['geography'])],municipal['value'])
 return dict({k:municipal[k] for k in ('metric','dimension','unit','population','definition','method','frequency','periodBasis','adapter','period')},geography=scope,value=b['tuscany'],source=REGION,evidence=[dict(ref,kind='benchmark_snapshot',valuePointer='/benchmarks/'+key+'/tuscany')],provenance=[dict(ref,kind='benchmark_snapshot',valuePointer='/benchmarks/'+key+'/tuscany')],notApplicable=False,dataUnavailable=False)
