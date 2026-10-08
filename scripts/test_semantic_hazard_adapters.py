"""Fixed ISPRA inputs; independent arithmetic, scenario semantics and adversarial guards."""
import copy, math
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_hazard_adapters as h

REFERENCE = {'Camaiore': {'slug': 'camaiore',
              'municipalAreaKm2': 84.692,
              'flood': {'P3': {'areaKm2': 5.98, 'areaPct': 7.061, 'residents': 3980, 'residentsPct': 12.405},
                        'P2': {'areaKm2': 13.111, 'areaPct': 15.481, 'residents': 9523, 'residentsPct': 29.682},
                        'P1': {'areaKm2': 20.74, 'areaPct': 24.489, 'residents': 24119, 'residentsPct': 75.177}},
              'landslide': {'P4': {'areaKm2': 6.116, 'areaPct': 7.221, 'residents': 909, 'residentsPct': 2.857},
                            'P3': {'areaKm2': 20.329, 'areaPct': 24.003, 'residents': 4841, 'residentsPct': 15.213},
                            'P2': {'areaKm2': 29.647, 'areaPct': 35.006, 'residents': 1613, 'residentsPct': 5.069},
                            'P1': {'areaKm2': 5.178, 'areaPct': 6.114, 'residents': 1206, 'residentsPct': 3.79},
                            'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                            'P3+P4': {'areaKm2': 26.446, 'areaPct': 31.226, 'residents': 5750, 'residentsPct': 18.07}},
              'population2011': 32083,
              'population2021': 31821,
              'landslideP3P4History': [{'year': 2017, 'value': 20.82},
                                       {'year': 2020, 'value': 29.45},
                                       {'year': 2024, 'value': 31.23}]},
 'Forte dei Marmi': {'slug': 'forte-dei-marmi',
                     'municipalAreaKm2': 9.187,
                     'flood': {'P3': {'areaKm2': 0.66, 'areaPct': 7.184, 'residents': 277, 'residentsPct': 3.616},
                               'P2': {'areaKm2': 1.191, 'areaPct': 12.964, 'residents': 532, 'residentsPct': 6.945},
                               'P1': {'areaKm2': 9.179, 'areaPct': 99.913, 'residents': 7658, 'residentsPct': 99.974}},
                     'landslide': {'P4': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                                   'P3': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                                   'P2': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                                   'P1': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                                   'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                                   'P3+P4': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0}},
                     'population2011': 7660,
                     'population2021': 6943,
                     'landslideP3P4History': [{'year': 2017, 'value': 0.0},
                                              {'year': 2020, 'value': 0.0},
                                              {'year': 2024, 'value': 0.0}]},
 'Massarosa': {'slug': 'massarosa',
               'municipalAreaKm2': 68.246,
               'flood': {'P3': {'areaKm2': 35.512, 'areaPct': 52.035, 'residents': 4663, 'residentsPct': 20.882},
                         'P2': {'areaKm2': 41.367, 'areaPct': 60.615, 'residents': 16042, 'residentsPct': 71.841},
                         'P1': {'areaKm2': 42.021, 'areaPct': 61.573, 'residents': 16648, 'residentsPct': 74.554}},
               'landslide': {'P4': {'areaKm2': 2.382, 'areaPct': 3.49, 'residents': 152, 'residentsPct': 0.697},
                             'P3': {'areaKm2': 13.358, 'areaPct': 19.573, 'residents': 3382, 'residentsPct': 15.497},
                             'P2': {'areaKm2': 10.595, 'areaPct': 15.525, 'residents': 2267, 'residentsPct': 10.388},
                             'P1': {'areaKm2': 1.612, 'areaPct': 2.362, 'residents': 665, 'residentsPct': 3.047},
                             'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'P3+P4': {'areaKm2': 15.74, 'areaPct': 23.064, 'residents': 3534, 'residentsPct': 16.194}},
               'population2011': 22330,
               'population2021': 21823,
               'landslideP3P4History': [{'year': 2017, 'value': 18.23},
                                        {'year': 2020, 'value': 18.57},
                                        {'year': 2024, 'value': 23.06}]},
 'Pietrasanta': {'slug': 'pietrasanta',
                 'municipalAreaKm2': 42.269,
                 'flood': {'P3': {'areaKm2': 2.444, 'areaPct': 5.782, 'residents': 1295, 'residentsPct': 5.356},
                           'P2': {'areaKm2': 6.389, 'areaPct': 15.115, 'residents': 3559, 'residentsPct': 14.719},
                           'P1': {'areaKm2': 24.271, 'areaPct': 57.42, 'residents': 19442, 'residentsPct': 80.409}},
                 'landslide': {'P4': {'areaKm2': 1.215, 'areaPct': 2.874, 'residents': 232, 'residentsPct': 1.006},
                               'P3': {'areaKm2': 4.52, 'areaPct': 10.693, 'residents': 970, 'residentsPct': 4.205},
                               'P2': {'areaKm2': 9.184, 'areaPct': 21.728, 'residents': 1500, 'residentsPct': 6.503},
                               'P1': {'areaKm2': 1.761, 'areaPct': 4.166, 'residents': 462, 'residentsPct': 2.003},
                               'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                               'P3+P4': {'areaKm2': 5.735,
                                         'areaPct': 13.568,
                                         'residents': 1202,
                                         'residentsPct': 5.211}},
                 'population2011': 24179,
                 'population2021': 23066,
                 'landslideP3P4History': [{'year': 2017, 'value': 13.53},
                                          {'year': 2020, 'value': 13.47},
                                          {'year': 2024, 'value': 13.57}]},
 'Seravezza': {'slug': 'seravezza',
               'municipalAreaKm2': 39.468,
               'flood': {'P3': {'areaKm2': 0.01, 'areaPct': 0.025, 'residents': 2, 'residentsPct': 0.015},
                         'P2': {'areaKm2': 0.751, 'areaPct': 1.903, 'residents': 800, 'residentsPct': 6.043},
                         'P1': {'areaKm2': 6.148, 'areaPct': 15.577, 'residents': 10405, 'residentsPct': 78.599}},
               'landslide': {'P4': {'areaKm2': 1.208, 'areaPct': 3.061, 'residents': 125, 'residentsPct': 1.005},
                             'P3': {'areaKm2': 4.47, 'areaPct': 11.326, 'residents': 367, 'residentsPct': 2.95},
                             'P2': {'areaKm2': 21.448, 'areaPct': 54.343, 'residents': 2036, 'residentsPct': 16.365},
                             'P1': {'areaKm2': 6.212, 'areaPct': 15.739, 'residents': 147, 'residentsPct': 1.182},
                             'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'P3+P4': {'areaKm2': 5.678, 'areaPct': 14.386, 'residents': 492, 'residentsPct': 3.955}},
               'population2011': 13238,
               'population2021': 12441,
               'landslideP3P4History': [{'year': 2017, 'value': 13.97},
                                        {'year': 2020, 'value': 14.1},
                                        {'year': 2024, 'value': 14.39}]},
 'Stazzema': {'slug': 'stazzema',
              'municipalAreaKm2': 80.64,
              'flood': {'P3': {'areaKm2': 0.274, 'areaPct': 0.34, 'residents': 18, 'residentsPct': 0.542},
                        'P2': {'areaKm2': 0.282, 'areaPct': 0.35, 'residents': 18, 'residentsPct': 0.542},
                        'P1': {'areaKm2': 0.282, 'areaPct': 0.35, 'residents': 18, 'residentsPct': 0.542}},
              'landslide': {'P4': {'areaKm2': 6.007, 'areaPct': 7.449, 'residents': 217, 'residentsPct': 7.509},
                            'P3': {'areaKm2': 20.611, 'areaPct': 25.559, 'residents': 1383, 'residentsPct': 47.855},
                            'P2': {'areaKm2': 24.357, 'areaPct': 30.205, 'residents': 709, 'residentsPct': 24.533},
                            'P1': {'areaKm2': 29.666, 'areaPct': 36.788, 'residents': 581, 'residentsPct': 20.104},
                            'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                            'P3+P4': {'areaKm2': 26.617, 'areaPct': 33.007, 'residents': 1600, 'residentsPct': 55.363}},
              'population2011': 3318,
              'population2021': 2890,
              'landslideP3P4History': [{'year': 2017, 'value': 31.98},
                                       {'year': 2020, 'value': 32.08},
                                       {'year': 2024, 'value': 33.01}]},
 'Viareggio': {'slug': 'viareggio',
               'municipalAreaKm2': 32.726,
               'flood': {'P3': {'areaKm2': 9.232, 'areaPct': 28.21, 'residents': 1720, 'residentsPct': 2.781},
                         'P2': {'areaKm2': 13.037, 'areaPct': 39.837, 'residents': 9016, 'residentsPct': 14.576},
                         'P1': {'areaKm2': 32.477, 'areaPct': 99.239, 'residents': 61842, 'residentsPct': 99.976}},
               'landslide': {'P4': {'areaKm2': 0.486, 'areaPct': 1.485, 'residents': 6, 'residentsPct': 0.01},
                             'P3': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'P2': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'P1': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'AA': {'areaKm2': 0, 'areaPct': 0, 'residents': 0, 'residentsPct': 0},
                             'P3+P4': {'areaKm2': 0.486, 'areaPct': 1.485, 'residents': 6, 'residentsPct': 0.01}},
               'population2011': 61857,
               'population2021': 61045,
               'landslideP3P4History': [{'year': 2017, 'value': 0.0},
                                        {'year': 2020, 'value': 0.0},
                                        {'year': 2024, 'value': 1.48}]}}

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 if not all(k in e._catalog['metrics'] and all('populationBase' in r for r in e._catalog['metrics'][k]['rows']) for k in h.KEYS):return
 for key in h.KEYS:
  kind,source,year,pop,scenarios,default=h.SPECS[key]
  for dim in h.dimensions(key):
   field,scenario=h.field_scenario(key,dim)
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    town=next(t['name'] for t in e._catalog['towns'] if t['code']==o['geography']);n=REFERENCE[town]
    published=n['landslideP3P4History'][-1]['value'] if field=='history' else n[kind][scenario][field]
    expected=n[kind][scenario]['residents']/n[f'population{pop}']*100 if field=='residentsPct' else n[kind][scenario]['areaKm2']/n['municipalAreaKm2']*100 if field=='areaPct' else published
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(o,expected)
    assert o['publishedValue']==published and all(len(x['sha256'])==64 for x in o['provenance']);count+=1
    if h.weighted(key,dim):assert o['denominatorPeriod']==(str(pop) if field=='residentsPct' else '2024') and o['numeratorPeriod']==year
   r=e.query(request('weighted_ratio',key,dimension=dim))
   if h.weighted(key,dim):
    assert r['status']=='computed',r
    resident=field=='residentsPct';num=sum(n[kind][scenario]['residents' if resident else 'areaKm2'] for n in REFERENCE.values());den=sum(n[f'population{pop}' if resident else 'municipalAreaKm2'] for n in REFERENCE.values())
    assert math.isclose(r['result']['value'],num/den*100,rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'verified_ratio_adapter_required')
   rejected(e,request('trend',key,dimension=dim,towns=['046018']),'hazard_temporal_comparability_not_attested')
  rejected(e,request('series',key,towns=['046018']),'hazard_historical_dimension_not_frozen')
  rejected(e,request('compare',key,periods=['2025']),'hazard_period_or_dimension_not_frozen')
  rejected(e,request('compare',key,dimension='residentsPct:sum'),'dimension_adapter_not_implemented')
  rejected(e,dict(request('benchmark_gap',key,towns=['046018']),benchmark='tuscany'),'hazard_benchmark_not_frozen')
 for town,n in REFERENCE.items():
  code=next(t['code'] for t in e._catalog['towns'] if t['name']==town)
  r=e.query(request('series','landslideExposure',dimension=h.HISTORY,towns=[code]));assert r['status']=='computed',r
  assert [(int(o['period']),o['value']) for o in r['observations']]==[(x['year'],x['value']) for x in n['landslideP3P4History']];count+=3
 rejected(e,request('weighted_ratio','landslideExposure',dimension=h.HISTORY),'verified_ratio_adapter_required')
 rejected(e,request('compare','landslideExposure',dimension='areaPct:P3+P4',periods=['2017']),'hazard_period_or_dimension_not_frozen')
 for mode,reason in [('population','hazard_population_reference_changed'),('map','hazard_native_reference_changed'),('identity','hazard_row_identity_changed'),('negative','hazard_invalid_native_components'),('percent','hazard_catalog_source_mismatch'),('nested','hazard_nested_scenarios_changed'),('history','hazard_history_reference_changed')]:
  key='landslideExposure' if mode=='history' else 'floodExposure';f=QueryEngine(path,layer='effective');s,ref=f.file(h.NATIVE);s=copy.deepcopy(s)
  if mode=='population':f._catalog['metrics'][key]['rows'][0]['populationReference']=2026
  elif mode=='map':s['sources']['ispraFlood']['hazardReference']=2024
  elif mode=='identity':s['istatByTown']['Camaiore']['code']='046018'
  elif mode=='negative':s['hazardsByTown']['Camaiore']['flood']['P2']['residents']=-1
  elif mode=='percent':s['hazardsByTown']['Camaiore']['flood']['P2']['residentsPct']+=1
  elif mode=='nested':
   s['hazardsByTown']['Camaiore']['flood']['P3']=copy.deepcopy(s['hazardsByTown']['Camaiore']['flood']['P1'])
   a=s['hazardsByTown']['Camaiore']['flood']['P3'];row=next(r for r in f._catalog['metrics'][key]['rows'] if r['town']=='Camaiore');part=next(p for p in row['parts'] if p['key']=='P3');part.update(a,value=a['residentsPct'])
  else:s['hazardsByTown']['Camaiore']['landslideP3P4History'][0]['year']=2018
  f.files[h.NATIVE]=(s,ref);rejected(f,request('compare',key,dimension=h.HISTORY if mode=='history' else 'total'),reason)
 for key in h.KEYS:
  f=QueryEngine(path,layer='effective');f._catalog['metrics'][key]['rows'][0]['value']=None
  rejected(f,request('compare',key),'partial_coverage_requires_opt_in')
  assert len(f.query(dict(request('compare',key),allowPartial=True))['excluded'])==1
 print(f'A6 hazards PASS: {count} fixed-reference observations including history/aliases; census dates, native area/resident ratios, nested scenarios, source P3+P4, nulls and refusals')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
