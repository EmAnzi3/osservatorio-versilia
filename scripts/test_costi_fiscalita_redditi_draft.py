#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/site-data.json').read_text(encoding='utf-8'))
REG=json.loads((ROOT/'data/source-registry.json').read_text(encoding='utf-8'))
AUDIT=json.loads((ROOT/'data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json').read_text(encoding='utf-8'))
VAL=json.loads((ROOT/'data/source-snapshots/costi-fiscalita-validated-2026-08.json').read_text(encoding='utf-8'))
APP00=(ROOT/'assets/app-parts/00.txt').read_text(encoding='utf-8')
APP02=(ROOT/'assets/app-parts/02.txt').read_text(encoding='utf-8')
APP03=(ROOT/'assets/app-parts/03.txt').read_text(encoding='utf-8')
APP05=(ROOT/'assets/app-parts/05.txt').read_text(encoding='utf-8')
UX=(ROOT/'assets/ux-history.js').read_text(encoding='utf-8')
UXCORE=(ROOT/'assets/ux-history-core.js').read_text(encoding='utf-8')
VISUAL=(ROOT/'assets/visual-grammar.js').read_text(encoding='utf-8')


def rows(key): return {r['town']:r for r in DATA['metrics'][key]['rows']}
def close(a,b,tol=.011): return abs(float(a)-float(b))<=tol


def main():
    assert DATA['version']=='v1.17.0'
    assert REG['expectedMetricCount']==143 and REG['expectedInlineMetricCount']==139 and REG['expectedExternalMetricCount']==4
    for key in ['municipalIrpef','tariStandardHousehold','municipalImuStandard','fuelPrices','wasteServiceCost','incomeVsInflation']:
        assert key in DATA['metrics']

    ir=DATA['metrics']['municipalIrpef']
    assert ir['method']['coverage']=='7/7' and ir['meta']['unit']=='currency2' and len(ir['rows'])==7
    for r in ir['rows']:
        expected=AUDIT['municipalIrpef']['towns'][r['town']]['amounts']
        assert [round(p['value'],2) for p in r['parts']]==[round(float(expected[str(x)]),2) for x in [20000,30000,50000]]

    tr=rows('tariStandardHousehold')
    assert DATA['metrics']['tariStandardHousehold']['method']['coverage']=='7/7'
    for town,v in VAL['tari']['towns'].items(): assert close(tr[town]['value'],v['annualCost'])
    assert close(tr['Forte dei Marmi']['value'],475.73) and close(tr['Pietrasanta']['value'],356.11)

    im=rows('municipalImuStandard')
    imu_metric=DATA['metrics']['municipalImuStandard']
    assert imu_metric['method']['coverage']=='7/7' and 'compositeType' not in imu_metric['meta']
    for town,v in VAL['imu']['towns'].items():
        assert close(im[town]['value'],v['annualTax']) and close(im[town]['ratePercent'],v['ratePercent'])

    fu=rows('fuelPrices')
    assert DATA['metrics']['fuelPrices']['method']['coverage']=='6/7'
    assert fu['Stazzema']['parts'][0]['value'] is None and fu['Stazzema']['parts'][1]['value'] is None and fu['Stazzema']['stationCount']==0
    for town,v in VAL['fuel']['towns'].items():
        assert fu[town]['parts'][0]['value']==v['benzina'] and fu[town]['parts'][1]['value']==v['gasolio']

    wa=rows('wasteServiceCost')
    assert DATA['metrics']['wasteServiceCost']['method']['coverage']=='7/7'
    for town,v in VAL['waste']['towns'].items(): assert close(wa[town]['value'],v['ctotPerResident'])

    inc=DATA['metrics']['income']
    assert inc['meta']['longHistoryYears']=='2011–2024'
    assert inc['meta']['label']=='Reddito imponibile medio per dichiarante'
    assert 'Reddito complessivo medio dichiarato' in inc['meta']['description']
    for r in inc['rows']:
        assert r['series']['years']==VAL['incomeLongHistory']['years']
        assert r['series']['values']==VAL['incomeLongHistory']['towns'][r['town']]['values']
        assert close(r['value'],r['series']['values'][-1],.0001)

    dist=DATA['metrics']['incomeDistribution']
    assert dist['meta']['summaryLabel']=='Reddito complessivo medio dichiarato'
    assert dist['aggregate']['summaryLabel']=='Reddito complessivo medio Versilia'
    assert rows('incomeDistribution')['Forte dei Marmi']['summaryValue']==45765

    ctx=DATA['incomeInflationContext']
    assert ctx['years']==list(range(2016,2025))
    assert ctx['priceLabel']=='NIC Italia'
    assert close(ctx['priceIndex'][-1],120.9166,.0002)

    real=DATA['metrics']['incomeVsInflation']
    assert real['meta']['unit']=='percent' and real['method']['coverage']=='7/7 · 2016–2024'
    assert len(real['rows'])==7
    rr=rows('incomeVsInflation')
    for row in real['rows']:
        assert row['series']['years']==list(range(2016,2025))
        assert close(row['series']['values'][0],0,.0001)
        assert close(row['value'],row['series']['values'][-1],.0001)
        if 'nominalSeries' in row:
            assert row['nominalSeries']['years']==list(range(2016,2025))
            assert row['realSeries']['years']==list(range(2016,2025))
            assert close(row['nominalSeries']['values'][0],0,.0001)
            assert close(row['realSeries']['values'][0],0,.0001)
            assert close(row['realSeries']['values'][-1],row['value'],.0001)
    assert close(rr['Forte dei Marmi']['value'],23.83,.03)
    assert close(rr['Stazzema']['value'],3.82,.03)
    assert close(real['aggregate']['value'],5.23,.03)
    if 'historyPresentation' in real:
        assert 'rapporto' in real['historyPresentation']['note']
        assert 'distanza visiva' in real['historyPresentation']['note']

    e=DATA['themes']['economia']
    fiscal=next(x for x in e['sections'] if x['key']=='costi-fiscalita')
    assert fiscal['metrics']==['municipalIrpef','tariStandardHousehold','municipalImuStandard','fiscalRecoveryActivity']
    redditi=next(x for x in e['sections'] if x['key']=='redditi')
    assert redditi['metrics']==[
        'income','incomeDistribution','incomeSourceProfile','pensionIncomeShare',
        'taxpayersAdultPopulationRate','incomeVsInflation'
    ]
    assert 'incomeVsInflation' in e['metrics']
    assert 'metric-context-jump' not in APP02
    assert "themeKey === 'economia' ? incomeInflationMarkup(data)" not in APP03

    m=DATA['themes']['mobilita']; assert 'fuelPrices' in m['metrics']
    a=DATA['themes']['ambiente']; assert 'wasteServiceCost' in a['metrics']
    assert REG['metricOverrides']['incomeVsInflation']['profile']=='mef-istat-real-income-annual'

    for token in ['tariStandardHousehold:','municipalImuStandard:','fuelPrices:','wasteServiceCost:',"case 'currency2'","case 'eurliter'","case 'eurPerResident'"]:
        assert token in APP00
    assert 'function historyMetric(metric)' in UX
    assert 'number3' in UX and "unit === 'eurliter'" in UX
    assert "case 'eurliter'" in UXCORE and 'focusedFuel' in UXCORE and 'rawValue === null' in UX
    if 'historyPresentation' in real:
        assert 'Variazione reale:' in UXCORE and 'Reddito nominale:' in UXCORE and 'chart-tooltip-detail' in UXCORE
    assert "kind === 'eurliter'" in VISUAL and "kind: 'focused'" in VISUAL and 'scala adattata ai prezzi' in VISUAL

    state=DATA['costsFiscalDraft']
    assert state.get('status') in {'draft','published'}
    assert 'incomeVsInflation' in state['publishedInDraft']
    assert state['notPublished']==['schoolMeals']
    print(f"Economia validata ({DATA['version']}): 143 indicatori = 139 inline + 4 esterni; redditi/inflazione e fiscalità coerenti")

if __name__=='__main__': main()
