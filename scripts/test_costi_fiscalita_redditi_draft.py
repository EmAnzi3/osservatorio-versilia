#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/site-data.json').read_text(encoding='utf-8'));REG=json.loads((ROOT/'data/source-registry.json').read_text(encoding='utf-8'))
AUDIT=json.loads((ROOT/'data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json').read_text(encoding='utf-8'));VAL=json.loads((ROOT/'data/source-snapshots/costi-fiscalita-validated-2026-08.json').read_text(encoding='utf-8'))
APP00=(ROOT/'assets/app-parts/00.txt').read_text(encoding='utf-8');APP03=(ROOT/'assets/app-parts/03.txt').read_text(encoding='utf-8');APP05=(ROOT/'assets/app-parts/05.txt').read_text(encoding='utf-8');UX=(ROOT/'assets/ux-history.js').read_text(encoding='utf-8')

def rows(key):return {r['town']:r for r in DATA['metrics'][key]['rows']}
def close(a,b,tol=.011):return abs(float(a)-float(b))<=tol

def main():
    assert DATA['version']=='v1.12.0'
    assert REG['expectedMetricCount']==126 and REG['expectedInlineMetricCount']==122 and REG['expectedExternalMetricCount']==4
    for key in ['municipalIrpef','tariStandardHousehold','municipalImuStandard','fuelPrices','wasteServiceCost']:assert key in DATA['metrics']
    ir=DATA['metrics']['municipalIrpef']; assert ir['method']['coverage']=='7/7' and ir['meta']['unit']=='currency2';assert len(ir['rows'])==7
    for r in ir['rows']:
        expected=AUDIT['municipalIrpef']['towns'][r['town']]['amounts']; assert [round(p['value'],2) for p in r['parts']]==[round(float(expected[str(x)]),2) for x in [20000,30000,50000]]
    tr=rows('tariStandardHousehold'); assert DATA['metrics']['tariStandardHousehold']['method']['coverage']=='7/7'
    for town,v in VAL['tari']['towns'].items():assert close(tr[town]['value'],v['annualCost'])
    assert close(tr['Forte dei Marmi']['value'],475.73) and close(tr['Pietrasanta']['value'],356.11)
    im=rows('municipalImuStandard'); assert DATA['metrics']['municipalImuStandard']['method']['coverage']=='7/7'
    for town,v in VAL['imu']['towns'].items():assert close(im[town]['parts'][0]['value'],v['annualTax']) and close(im[town]['parts'][1]['value'],v['ratePercent'])
    fu=rows('fuelPrices'); assert DATA['metrics']['fuelPrices']['method']['coverage']=='6/7';assert fu['Stazzema']['parts'][0]['value'] is None and fu['Stazzema']['parts'][1]['value'] is None and fu['Stazzema']['stationCount']==0
    for town,v in VAL['fuel']['towns'].items():assert fu[town]['parts'][0]['value']==v['benzina'] and fu[town]['parts'][1]['value']==v['gasolio']
    wa=rows('wasteServiceCost'); assert DATA['metrics']['wasteServiceCost']['method']['coverage']=='7/7'
    for town,v in VAL['waste']['towns'].items():assert close(wa[town]['value'],v['ctotPerResident'])
    inc=DATA['metrics']['income']; assert inc['meta']['longHistoryYears']=='2011–2024'; assert inc['meta']['longHistoryLabel']=='Reddito imponibile medio · serie lunga'
    for r in inc['rows']:assert r['longSeries']['years']==VAL['incomeLongHistory']['years'] and len(r['longSeries']['values'])==14 and r['longSeries']['values']==VAL['incomeLongHistory']['towns'][r['town']]['values']
    ctx=DATA['incomeInflationContext']; assert ctx['years']==list(range(2016,2025)); assert close(ctx['incomeIndex'][-1],127.2465,.0002);assert close(ctx['priceIndex'][-1],121.5433,.0002);assert close(ctx['realIncomeIndex'][-1],104.6923,.0002)
    e=DATA['themes']['economia']; fiscal=next(x for x in e['sections'] if x['key']=='costi-fiscalita');assert fiscal['metrics']==['municipalIrpef','tariStandardHousehold','municipalImuStandard']
    m=DATA['themes']['mobilita'];assert 'fuelPrices' in m['metrics'];a=DATA['themes']['ambiente'];assert 'wasteServiceCost' in a['metrics']
    assert REG['metricOverrides']['tariStandardHousehold']['profile']=='mef-municipal-tax-annual';assert REG['metricOverrides']['municipalImuStandard']['profile']=='mef-municipal-tax-annual';assert REG['metricOverrides']['fuelPrices']['profile']=='mimit-fuel-daily';assert REG['metricOverrides']['wasteServiceCost']['profile']=='ispra-environment-annual'
    for token in ['tariStandardHousehold:','municipalImuStandard:','fuelPrices:','wasteServiceCost:',"case 'currency2'","case 'eurliter'","case 'eurPerResident'"]:assert token in APP00
    assert "themeKey === 'economia' ? incomeInflationMarkup(data)" in APP03 and 'row.displayValue === null' in APP03
    assert 'function incomeInflationMarkup(data)' in APP05 and 'row.longSeries' in APP05 and 'function historyMetric(metric)' in UX and 'selected.metric.meta.longHistoryNote' in UX
    draft=DATA['costsFiscalDraft'];assert draft['publishedInDraft']==['municipalIrpef','tariStandardHousehold','municipalImuStandard','fuelPrices','wasteServiceCost'];assert draft['notPublished']==['schoolMeals']
    print('Draft validato: 126 indicatori = 122 inline + 4 esterni; TARI 7/7, IMU 7/7, carburanti 6/7, rifiuti 7/7, storico imponibile 2011-2024, NIC Toscana 2016-2024')
if __name__=='__main__':main()
