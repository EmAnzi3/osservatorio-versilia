#!/usr/bin/env python3
"""Contratto pubblico e metodologico della release v1.29.0."""
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
    site=load(ROOT/'data/site-data.json'); registry=load(ROOT/'data/source-registry.json'); state=load(ROOT/'data/source-monitor-state.json')
    snap=load(ROOT/'data/source-snapshots/bonifica-rischio-v126.json'); gis=load(ROOT/'data/source-snapshots/bonifica-rischio-v126-gis.json'); status=load(ROOT/'data/source-snapshots/bonifica-rischio-v126-status.json')
    assert site['version']==VERSION and site['updated']==UPDATED
    assert len(site['towns'])==EXPECTED_TOWNS and len(site['themes'])==EXPECTED_THEMES and len(site['metrics'])==EXPECTED_METRICS
    assert registry['expectedMetricCount']==EXPECTED_METRICS and registry['expectedInlineMetricCount']==EXPECTED_INLINE and registry['expectedExternalMetricCount']==EXPECTED_EXTERNAL
    refs=[k for theme in site['themes'].values() for k in theme['metrics']]; assert Counter(refs)==Counter({k:1 for k in site['metrics']})
    for theme in site['themes'].values(): assert Counter(k for s in theme['sections'] for k in s['metrics'])==Counter(theme['metrics'])
    lavoro=site['themes']['lavoro']; gender=next(s for s in lavoro['sections'] if s['key']=='genere'); assert gender['label']=='Serie storiche 15–64'; assert gender['metrics']==['femaleEmploymentRate','maleEmploymentRate','employmentGenderGap']; assert '2021–2023' in gender['description'] and '2024' in gender['description']
    age_method=site['metrics']['ageDistribution']['method']; disclosure=' '.join(str(age_method.get(k,'')) for k in ('formula','caveat','detail')); assert '1° gennaio 2026' in disclosure and 'singola età' in disclosure and '31 dicembre 2024' not in disclosure and '1° gennaio 2025' not in disclosure and 'età media' in age_method['formula']
    assert not [x for x in formatted_strings(site) if 'ogni 1,000' in x[1]]

    keys=('pabProgrammedInterventionLength','pabProgrammedInterventions','pabProgrammedMaintenanceValue','managedReticulumLength','hydraulicWorksCensusElements','pabInterventionsInProgress','pabInterventionsCompleted','pabInProgressOperationalGrossValue','pabCompletedOperationalGrossValue')
    terr=next(s for s in site['themes']['ambiente']['sections'] if s['key']=='territorio'); assert all(k in terr['metrics'] for k in keys)
    expected={
      'pabProgrammedInterventionLength':({'Massarosa':317.413,'Viareggio':101.693,'Camaiore':270.094,'Pietrasanta':174.004,'Seravezza':50.704,'Forte dei Marmi':18.410,'Stazzema':71.776},1004.094,'2026'),
      'pabProgrammedInterventions':({'Massarosa':464,'Viareggio':102,'Camaiore':341,'Pietrasanta':182,'Seravezza':52,'Forte dei Marmi':27,'Stazzema':91},1259,'2026'),
      'pabProgrammedMaintenanceValue':({'Massarosa':1998372.37,'Viareggio':454075.17,'Camaiore':1060763.74,'Pietrasanta':821438.02,'Seravezza':370837.00,'Forte dei Marmi':98194.06,'Stazzema':392752.72},5196433.08,'2026'),
      'managedReticulumLength':({'Massarosa':192.01491,'Viareggio':57.108279,'Camaiore':204.809871,'Pietrasanta':99.736904,'Seravezza':49.446972,'Forte dei Marmi':11.609746,'Stazzema':130.315069},745.041751,'2025'),
      'hydraulicWorksCensusElements':({'Massarosa':11,'Viareggio':10,'Camaiore':43,'Pietrasanta':64,'Seravezza':75,'Forte dei Marmi':5,'Stazzema':90},265,'2021'),
      'pabInterventionsInProgress':({'Massarosa':6,'Viareggio':0,'Camaiore':91,'Pietrasanta':43,'Seravezza':26,'Forte dei Marmi':0,'Stazzema':56},222,'2026'),
      'pabInterventionsCompleted':({'Massarosa':1,'Viareggio':0,'Camaiore':150,'Pietrasanta':68,'Seravezza':7,'Forte dei Marmi':13,'Stazzema':9},248,'2026'),
      'pabInProgressOperationalGrossValue':({'Massarosa':9024.94,'Viareggio':0.0,'Camaiore':246984.54,'Pietrasanta':132058.98,'Seravezza':102166.89,'Forte dei Marmi':0.0,'Stazzema':154272.8},644508.15,'2026'),
      'pabCompletedOperationalGrossValue':({'Massarosa':12003.72,'Viareggio':0.0,'Camaiore':329096.89,'Pietrasanta':205685.93,'Seravezza':67506.08,'Forte dei Marmi':19604.17,'Stazzema':60084.34},693981.13,'2026')}
    for k,(vals,total,period) in expected.items():
        m=site['metrics'][k]; got={r['town']:r['value'] for r in m['rows']}; assert got==vals; assert abs(m['aggregate']['value']-total)<1e-6; assert state['metrics'][k]['publishedPeriod']==period; assert k in registry['metricOverrides']
    assert site['metrics']['pabProgrammedInterventionLength']['meta']['unit']=='km'
    assert site['metrics']['managedReticulumLength']['meta']['unit']=='km'
    assert site['metrics']['pabInProgressOperationalGrossValue']['meta']['unit']=='currency2'
    assert site['metrics']['pabCompletedOperationalGrossValue']['meta']['unit']=='currency2'
    assert next(r for r in site['metrics']['pabProgrammedInterventionLength']['rows'] if r['town']=='Massarosa')['formatted']=='317,41 km'
    assert next(r for r in site['metrics']['managedReticulumLength']['rows'] if r['town']=='Massarosa')['formatted']=='192,01 km'
    assert next(r for r in site['metrics']['pabInterventionsInProgress']['rows'] if r['town']=='Viareggio')['formatted']=='0'
    assert next(r for r in site['metrics']['pabCompletedOperationalGrossValue']['rows'] if r['town']=='Camaiore')['formatted']=='€ 329.096,89'
    text=' '.join([site['metrics']['pabProgrammedInterventionLength']['meta']['description'],site['metrics']['pabProgrammedInterventionLength']['method']['caveat']]); assert 'km-intervento' in text and 'reticolo fisico' in text
    ret_text=' '.join(site['metrics']['managedReticulumLength']['method'][k] for k in ('formula','caveat')); assert 'COMPLR79' in ret_text and 'RETGESLR79' in ret_text and 'LENGTH' in ret_text
    works_text=' '.join([site['metrics']['hydraulicWorksCensusElements']['meta']['description'],site['metrics']['hydraulicWorksCensusElements']['meta']['sourceMeta']['note'],site['metrics']['hydraulicWorksCensusElements']['method']['caveat']]); assert 'feature' in works_text and 'cantieri' in works_text
    status_value_text=' '.join([site['metrics']['pabInProgressOperationalGrossValue']['meta']['description'],site['metrics']['pabInProgressOperationalGrossValue']['method']['caveat']]); assert 'importo_lordo' in status_value_text and 'non coincide' in status_value_text and 'pagata' in status_value_text

    assert snap['portalExports']['rowsTotal']==1265 and snap['portalExports']['metresTotal']==1004094 and snap['portalExports']['amountCsvTotal']==4165255
    assert snap['published']['pabProgrammedInterventions']['total']==1259 and snap['published']['pabProgrammedMaintenanceValue']['total']==5196433.08
    assert gis['sources']['istatBoundaries']['sha256']=='b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6'
    assert gis['sources']['reticulum']['sha256']=='68d6bb2986c056e1c041009a21e3b9eb89de81d02830d412354c5770d7d9b122'
    assert gis['sources']['hydraulicWorks']['sha256']=='532b29090ce6fd09f06cf87a1f074b173eeddb57cb3ee1a92560e74ef17bb560'
    assert gis['managedReticulum']['sourceFeaturesAfterFilter']==26133 and gis['managedReticulum']['aggregateSevenTowns']['km']==745.041751
    assert gis['hydraulicWorks']['sourceFeatureCounts']=={'area':82,'line':2572,'point':1012} and gis['hydraulicWorks']['aggregateSevenTowns']['uniqueSourceFeaturesTotal']==265
    assert status['matching']['matchedRows']==1265 and status['matching']['uniqueWfsFeatureIds']==1265
    assert status['punctualLayer']['sharedIdsWithCbPmoLineare']==251
    assert status['aggregateSevenTowns']['in_corso']=={'features':222,'grossAmountEur':644508.15,'activityMetres':152551.88}
    assert status['aggregateSevenTowns']['completato']=={'features':248,'grossAmountEur':693981.13,'activityMetres':228653.36}
    assert status['economicField']['sumGrossAmountEur']==4165243.17 and status['economicField']['pabA1ApprovedProgrammedAmountEur']==5196433.08
    assert status['geometry']['publishPhysicalUniqueKm'] is False and status['geometry']['featuresWithoutGeometry']==49
    assert not any(k in site['metrics'] for k in ('maintainedPhysicalKm','maintainedReticulumShare'))

    app0=(ROOT/'assets/app-parts/00.txt').read_text(encoding='utf-8'); app5=(ROOT/'assets/app-parts/05.txt').read_text(encoding='utf-8')
    assert "case 'km'" in app0 and "case 'kmIntervention'" in app0 and '2026.09.01-v1.27.0' in app5 and '177 indicatori complessivi' in app5 and '2026.08.31-v1.26.0' in app5
    chart=(ROOT/'assets/app-parts/03.txt').read_text(encoding='utf-8'); assert 'part.count === null || part.count === undefined' in chart
    readme=(ROOT/'README.md').read_text(encoding='utf-8'); assert '**v1.29.0** — 3 settembre 2026' in readme and '181 indicatori' in readme and '177 con valori incorporati' in readme
    print(f'Release {VERSION} verificata: {EXPECTED_METRICS} indicatori; stato lavori, reticolo gestito e opere idrauliche verificati senza proxy.')
if __name__=='__main__': main()
