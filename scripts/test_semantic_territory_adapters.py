"""Independent fixed input references and adversarial territory queries."""
import copy
import math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_territory_adapters as t

# Regional GIS frozen references; these inputs do not call the adapter to compute expectations.
REFERENCE = {'Camaiore': {'areaHa': 8481.788129,
              'unionHa': 2437.267928,
              'categoryHa': {'parksReserves': 2437.267928,
                             'anpil': 0.0,
                             'natura2000': 910.647655,
                             'zsc': 53.678761,
                             'zps': 886.184101,
                             'ramsar': 0.0},
              'areaKm2': 84.817881,
              'fullKm': 315.932266,
              'managedKm': 204.809871,
              'density': 3.724831,
              'features': {'area': 2, 'line': 37, 'point': 4},
              'featuresTotal': 43},
 'Forte dei Marmi': {'areaHa': 925.501256,
                     'unionHa': 4.976994,
                     'categoryHa': {'parksReserves': 0.0,
                                    'anpil': 4.976994,
                                    'natura2000': 0.0,
                                    'zsc': 0.0,
                                    'zps': 0.0,
                                    'ramsar': 0.0},
                     'areaKm2': 9.255013,
                     'fullKm': 11.894496,
                     'managedKm': 11.609746,
                     'density': 1.285195,
                     'features': {'area': 0, 'line': 5, 'point': 0},
                     'featuresTotal': 5},
 'Massarosa': {'areaHa': 6791.045102,
               'unionHa': 2269.048072,
               'categoryHa': {'parksReserves': 2266.619294,
                              'anpil': 0.0,
                              'natura2000': 1568.073761,
                              'zsc': 1568.073761,
                              'zps': 1568.073761,
                              'ramsar': 1621.820966},
               'areaKm2': 67.910451,
               'fullKm': 245.761627,
               'managedKm': 192.01491,
               'density': 3.618907,
               'features': {'area': 0, 'line': 11, 'point': 0},
               'featuresTotal': 11},
 'Pietrasanta': {'areaHa': 4222.817031,
                 'unionHa': 88.106278,
                 'categoryHa': {'parksReserves': 32.506783,
                                'anpil': 55.598807,
                                'natura2000': 55.599493,
                                'zsc': 0.0,
                                'zps': 55.599493,
                                'ramsar': 0.0},
                 'areaKm2': 42.22817,
                 'fullKm': 127.916492,
                 'managedKm': 99.736904,
                 'density': 3.029174,
                 'features': {'area': 2, 'line': 54, 'point': 8},
                 'featuresTotal': 64},
 'Seravezza': {'areaHa': 3952.01718,
               'unionHa': 3017.770599,
               'categoryHa': {'parksReserves': 2979.308619,
                              'anpil': 0.0,
                              'natura2000': 1853.221299,
                              'zsc': 1644.458826,
                              'zps': 1053.994633,
                              'ramsar': 0.0},
               'areaKm2': 39.520172,
               'fullKm': 130.65877,
               'managedKm': 49.446972,
               'density': 3.306129,
               'features': {'area': 0, 'line': 73, 'point': 2},
               'featuresTotal': 75},
 'Stazzema': {'areaHa': 8026.530963,
              'unionHa': 8020.193966,
              'categoryHa': {'parksReserves': 8020.193966,
                             'anpil': 0.0,
                             'natura2000': 4501.383058,
                             'zsc': 4245.077861,
                             'zps': 3371.282035,
                             'ramsar': 0.0},
              'areaKm2': 80.26531,
              'fullKm': 293.038677,
              'managedKm': 130.315069,
              'density': 3.650876,
              'features': {'area': 0, 'line': 67, 'point': 23},
              'featuresTotal': 90},
 'Viareggio': {'areaHa': 3275.359664,
               'unionHa': 1303.035971,
               'categoryHa': {'parksReserves': 1280.98641,
                              'anpil': 0.0,
                              'natura2000': 750.727778,
                              'zsc': 750.727778,
                              'zps': 750.727778,
                              'ramsar': 786.329095},
               'areaKm2': 32.753597,
               'fullKm': 75.058846,
               'managedKm': 57.108279,
               'density': 2.291621,
               'features': {'area': 0, 'line': 10, 'point': 0},
               'featuresTotal': 10}}

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 if not all(k in e._catalog['metrics'] and str(e._catalog['metrics'][k]['meta']['year'])==t.LABELS[k] for k in t.KEYS):return
 for key in t.KEYS:
  for dim in t.dimensions(key):
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    town=next(x['name'] for x in e._catalog['towns'] if x['code']==o['geography']);n=REFERENCE[town]
    if key=='protectedNaturalAreas':
     c='total' if dim=='total' else dim.split(':')[1];h=n['unionHa'] if c=='total' else n['categoryHa'][c]
     expected=h if dim.startswith('hectares:') else h/n['areaHa']*100
    elif key=='managedReticulumLength':expected=n['fullKm'] if dim in ('total','view:full') else n['managedKm'] if dim=='view:managed' else n['fullKm']/n['areaKm2']
    else:expected=n['featuresTotal'] if dim=='total' else n['features'][dim.split(':')[1]]
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(o,expected)
    assert o['period']==t.PERIODS[key] and all(len(x['sha256'])==64 for x in o['provenance']);count+=1
   r=e.query(request('weighted_ratio',key,dimension=dim))
   if t.weighted(key,dim):
    assert r['status']=='computed',r
    if key=='protectedNaturalAreas':
     c='total' if dim=='total' else dim.split(':')[1]
     num=sum(n['unionHa'] if c=='total' else n['categoryHa'][c] for n in REFERENCE.values());den=sum(n['areaHa'] for n in REFERENCE.values());expected=num/den*100
    else:expected=sum(n['fullKm'] for n in REFERENCE.values())/sum(n['areaKm2'] for n in REFERENCE.values())
    assert math.isclose(r['result']['value'],expected,rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'verified_ratio_adapter_required')
  for op in ('series','trend','absolute_change','relative_change','percentage_points'):rejected(e,request(op,key,towns=['046018']),'territory_history_not_frozen')
  rejected(e,request('compare',key,periods=['2026']),'territory_period_not_frozen')
  rejected(e,request('compare',key,dimension='part:unknown'),'dimension_adapter_not_implemented')
  reason='territory_regional_count_not_comparable' if key=='hydraulicWorksCensusElements' else 'territory_benchmark_not_reviewed'
  rejected(e,dict(request('benchmark_gap',key,towns=['046018']),benchmark='tuscany'),reason)
 assert sum(n['featuresTotal'] for n in REFERENCE.values())==298
 assert sum(REFERENCE['Massarosa']['categoryHa'].values())>REFERENCE['Massarosa']['unionHa']
 for mode,reason in [('area','territory_invalid_native_components'),('cohort','territory_native_cohort_changed'),('date','territory_native_reference_changed'),('union','territory_catalog_source_mismatch'),('hierarchy','territory_protection_hierarchy_changed'),('network','territory_invalid_native_components'),('density','territory_catalog_source_mismatch'),('features','territory_invalid_native_components'),('identity','territory_row_identity_changed')]:
  key='managedReticulumLength' if mode in ('network','density') else 'hydraulicWorksCensusElements' if mode in ('features','identity') else 'protectedNaturalAreas'
  f=QueryEngine(path,layer='effective');p=t.GIS if key=='hydraulicWorksCensusElements' else t.TERRITORY;s,ref=f.file(p);s=copy.deepcopy(s)
  if mode=='area':s['protectedNaturalAreas']['municipalities']['Camaiore']['municipalAreaHa']=0
  elif mode=='cohort':s['protectedNaturalAreas']['municipalities'].pop('Massarosa')
  elif mode=='date':s['protectedNaturalAreas']['referenceLabel']='2027'
  elif mode=='union':s['protectedNaturalAreas']['versilia']['totalUnionHa']+=1
  elif mode=='hierarchy':s['protectedNaturalAreas']['municipalities']['Camaiore']['categoriesHa']['zsc']=1000
  elif mode=='network':s['reticulum']['municipalities']['Camaiore']['managedNetworkKm']=999
  elif mode=='density':s['reticulum']['municipalities']['Camaiore']['fullNetworkDensity']=99
  elif mode=='features':s['hydraulicWorks']['byTown']['Camaiore']['line']['types']['argine']+=1
  else:s['boundaries']['byTown']['Camaiore']['istatCode']='046018'
  f.files[p]=(s,ref);rejected(f,request('compare',key),reason)
 for key in t.KEYS:
  f=QueryEngine(path,layer='effective');f._catalog['metrics'][key]['rows'][0]['value']=None
  rejected(f,request('compare',key),'partial_coverage_requires_opt_in')
  assert len(f.query(dict(request('compare',key),allowPartial=True))['excluded'])==1
 print(f'A6 territory PASS: {count} fixed-reference observations; union/category distinction, source-feature overlap, native density and pooled area ratios, adversarial guards')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
