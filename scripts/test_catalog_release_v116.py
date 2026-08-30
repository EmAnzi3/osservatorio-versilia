#!/usr/bin/env python3
"""Contratto pubblico e metodologico della release v1.26.0."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from finalize_catalog_release import EXPECTED_EXTERNAL,EXPECTED_INLINE,EXPECTED_METRICS,EXPECTED_THEMES,EXPECTED_TOWNS,UPDATED,VERSION
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def formatted_strings(value,path='root'):
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='formatted' and isinstance(item,str): yield path+'.formatted',item
            yield from formatted_strings(item,path+'.'+str(key))
    elif isinstance(value,list):
        for index,item in enumerate(value): yield from formatted_strings(item,f'{path}[{index}]')
def main():
    site=load(ROOT/'data/site-data.json'); registry=load(ROOT/'data/source-registry.json'); state=load(ROOT/'data/source-monitor-state.json'); snap=load(ROOT/'data/source-snapshots/bonifica-rischio-v126.json')
    assert site['version']==VERSION and site['updated']==UPDATED
    assert len(site['towns'])==EXPECTED_TOWNS and len(site['themes'])==EXPECTED_THEMES and len(site['metrics'])==EXPECTED_METRICS
    assert registry['expectedMetricCount']==EXPECTED_METRICS and registry['expectedInlineMetricCount']==EXPECTED_INLINE and registry['expectedExternalMetricCount']==EXPECTED_EXTERNAL
    refs=[k for theme in site['themes'].values() for k in theme['metrics']]; assert Counter(refs)==Counter({k:1 for k in site['metrics']})
    for theme in site['themes'].values(): assert Counter(k for s in theme['sections'] for k in s['metrics'])==Counter(theme['metrics'])
    lavoro=site['themes']['lavoro']; gender=next(s for s in lavoro['sections'] if s['key']=='genere'); assert gender['label']=='Serie storiche 15–64'; assert gender['metrics']==['femaleEmploymentRate','maleEmploymentRate','employmentGenderGap']; assert '2021–2023' in gender['description'] and '2024' in gender['description']
    age_method=site['metrics']['ageDistribution']['method']; disclosure=' '.join(str(age_method.get(k,'')) for k in ('formula','caveat','detail')); assert '1° gennaio 2026' in disclosure and 'singola età' in disclosure and '31 dicembre 2024' not in disclosure and '1° gennaio 2025' not in disclosure and 'età media' in age_method['formula']
    malformed=[x for x in formatted_strings(site) if 'ogni 1,000' in x[1]]; assert not malformed
    keys=('pabProgrammedInterventionLength','pabProgrammedInterventions','pabProgrammedMaintenanceValue')
    terr=next(s for s in site['themes']['ambiente']['sections'] if s['key']=='territorio'); assert all(k in terr['metrics'] for k in keys)
    expected={
      'pabProgrammedInterventionLength':({'Massarosa':317.413,'Viareggio':101.693,'Camaiore':270.094,'Pietrasanta':174.004,'Seravezza':50.704,'Forte dei Marmi':18.410,'Stazzema':71.776},1004.094),
      'pabProgrammedInterventions':({'Massarosa':464,'Viareggio':102,'Camaiore':341,'Pietrasanta':182,'Seravezza':52,'Forte dei Marmi':27,'Stazzema':91},1259),
      'pabProgrammedMaintenanceValue':({'Massarosa':1998372.37,'Viareggio':454075.17,'Camaiore':1060763.74,'Pietrasanta':821438.02,'Seravezza':370837.00,'Forte dei Marmi':98194.06,'Stazzema':392752.72},5196433.08)}
    for k,(vals,total) in expected.items():
        m=site['metrics'][k]; got={r['town']:r['value'] for r in m['rows']}; assert got==vals; assert abs(m['aggregate']['value']-total)<1e-6; assert state['metrics'][k]['publishedPeriod']=='2026'; assert k in registry['metricOverrides']
    assert site['metrics']['pabProgrammedInterventionLength']['meta']['unit']=='kmIntervention'
    text=' '.join([site['metrics']['pabProgrammedInterventionLength']['meta']['description'],site['metrics']['pabProgrammedInterventionLength']['method']['caveat']]); assert 'km-intervento' in text and 'reticolo fisico' in text
    assert snap['portalExports']['rowsTotal']==1265 and snap['portalExports']['metresTotal']==1004094 and snap['portalExports']['amountCsvTotal']==4165255
    assert snap['published']['pabProgrammedInterventions']['total']==1259 and snap['published']['pabProgrammedMaintenanceValue']['total']==5196433.08
    assert snap['sources']['reticolo']['crs']=='EPSG:3003' and snap['sources']['reticolo']['features']==215923 and snap['sources']['reticolo']['managementFilter']=={'COMPLR79':'Toscana Nord','RETGESLR79':'SI'}
    assert snap['sources']['istatBoundaries']['sha256']=='b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6' and not snap['sources']['istatBoundaries']['availableInDevelopmentSession']
    forbidden=('managedReticulumKm','maintainedPhysicalKm','maintainedReticulumShare','pabInterventionsInProgress','pabInterventionsCompleted','hydraulicWorksCount')
    assert not any(k in site['metrics'] for k in forbidden)
    app0=(ROOT/'assets/app-parts/00.txt').read_text(encoding='utf-8'); app5=(ROOT/'assets/app-parts/05.txt').read_text(encoding='utf-8'); assert "case 'kmIntervention'" in app0 and '2026.08.31-v1.26.0' in app5 and '169 indicatori complessivi' in app5 and '2026.08.30-v1.25.0' in app5
    chart=(ROOT/'assets/app-parts/03.txt').read_text(encoding='utf-8'); assert 'part.count === null || part.count === undefined' in chart
    readme=(ROOT/'README.md').read_text(encoding='utf-8'); assert '**v1.26.0** — 31 agosto 2026' in readme and '169 indicatori' in readme and '165 con valori incorporati' in readme
    print(f'Release {VERSION} verificata: {EXPECTED_METRICS} indicatori, Lotto 6 pubblicato senza proxy e candidati GIS/stato lavori correttamente rinviati.')
if __name__=='__main__': main()
