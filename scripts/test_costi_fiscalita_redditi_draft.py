#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/site-data.json').read_text(encoding='utf-8'))
REG = json.loads((ROOT / 'data/source-registry.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json').read_text(encoding='utf-8'))
VAL = json.loads((ROOT / 'data/source-snapshots/costi-fiscalita-validated-2026-08.json').read_text(encoding='utf-8'))
NIC = json.loads((ROOT / 'data/source-snapshots/nic-italia-2016-2024.json').read_text(encoding='utf-8'))
APP00 = (ROOT / 'assets/app-parts/00.txt').read_text(encoding='utf-8')
APP02 = (ROOT / 'assets/app-parts/02.txt').read_text(encoding='utf-8')
APP03 = (ROOT / 'assets/app-parts/03.txt').read_text(encoding='utf-8')
APP05 = (ROOT / 'assets/app-parts/05.txt').read_text(encoding='utf-8')
UX = (ROOT / 'assets/ux-history.js').read_text(encoding='utf-8')
VISUAL = (ROOT / 'assets/visual-grammar.js').read_text(encoding='utf-8')


def rows(key):
    return {row['town']: row for row in DATA['metrics'][key]['rows']}


def close(a, b, tol=.011):
    return abs(float(a) - float(b)) <= tol


def main():
    assert DATA['version'] == 'v1.12.0'
    assert REG['expectedMetricCount'] == 126
    assert REG['expectedInlineMetricCount'] == 122
    assert REG['expectedExternalMetricCount'] == 4

    for key in ['municipalIrpef', 'tariStandardHousehold', 'municipalImuStandard', 'fuelPrices', 'wasteServiceCost']:
        assert key in DATA['metrics']

    irpef = DATA['metrics']['municipalIrpef']
    assert irpef['method']['coverage'] == '7/7'
    assert irpef['meta']['unit'] == 'currency2'
    assert len(irpef['rows']) == 7
    for current in irpef['rows']:
        expected = AUDIT['municipalIrpef']['towns'][current['town']]['amounts']
        assert [round(part['value'], 2) for part in current['parts']] == [round(float(expected[str(value)]), 2) for value in [20000, 30000, 50000]]

    tari = rows('tariStandardHousehold')
    assert DATA['metrics']['tariStandardHousehold']['method']['coverage'] == '7/7'
    for town, value in VAL['tari']['towns'].items():
        assert close(tari[town]['value'], value['annualCost'])
    assert close(tari['Forte dei Marmi']['value'], 475.73)
    assert close(tari['Pietrasanta']['value'], 356.11)

    imu_metric = DATA['metrics']['municipalImuStandard']
    imu = rows('municipalImuStandard')
    assert imu_metric['method']['coverage'] == '7/7'
    assert 'compositeType' not in imu_metric['meta']
    assert 'parts' not in imu_metric['aggregate']
    for town, value in VAL['imu']['towns'].items():
        assert close(imu[town]['value'], value['annualTax'])
        assert close(imu[town]['ratePercent'], value['ratePercent'])
        assert 'parts' not in imu[town]

    fuel = rows('fuelPrices')
    assert DATA['metrics']['fuelPrices']['method']['coverage'] == '6/7'
    assert fuel['Stazzema']['parts'][0]['value'] is None
    assert fuel['Stazzema']['parts'][1]['value'] is None
    assert fuel['Stazzema']['stationCount'] == 0
    for town, value in VAL['fuel']['towns'].items():
        assert fuel[town]['parts'][0]['value'] == value['benzina']
        assert fuel[town]['parts'][1]['value'] == value['gasolio']

    waste = rows('wasteServiceCost')
    assert DATA['metrics']['wasteServiceCost']['method']['coverage'] == '7/7'
    for town, value in VAL['waste']['towns'].items():
        assert close(waste[town]['value'], value['ctotPerResident'])

    income = DATA['metrics']['income']
    assert income['meta']['label'] == 'Reddito imponibile medio per dichiarante'
    assert income['meta']['shortLabel'] == 'Reddito imponibile medio'
    assert income['meta']['longHistoryYears'] == '2011–2024'
    assert income['meta']['longHistoryLabel'] == 'Reddito imponibile medio · serie storica'
    for current in income['rows']:
        expected_series = VAL['incomeLongHistory']['towns'][current['town']]['values']
        assert current['longSeries']['years'] == VAL['incomeLongHistory']['years']
        assert current['series']['years'] == VAL['incomeLongHistory']['years']
        assert current['longSeries']['values'] == expected_series
        assert current['series']['values'] == expected_series
        assert close(current['value'], expected_series[-1])
    assert close(income['aggregate']['value'], VAL['incomeLongHistory']['aggregate']['values'][-1])

    context = DATA['incomeInflationContext']
    assert context['years'] == list(range(2016, 2025))
    assert context['priceLabel'] == 'NIC Italia'
    assert close(context['incomeIndex'][-1], 127.2465, .0002)
    assert close(context['priceIndex'][-1], 120.9166, .0002)
    assert close(context['realIncomeIndex'][-1], 105.235, .0002)
    assert close(context['priceGrowthPercent'], 20.92, .001)
    assert close(context['realGrowthPercent'], 5.23, .001)
    assert NIC['territory']['level'] == 'national'

    economy = DATA['themes']['economia']
    fiscal = next(section for section in economy['sections'] if section['key'] == 'costi-fiscalita')
    assert fiscal['metrics'] == ['municipalIrpef', 'tariStandardHousehold', 'municipalImuStandard']
    assert 'fuelPrices' in DATA['themes']['mobilita']['metrics']
    assert 'wasteServiceCost' in DATA['themes']['ambiente']['metrics']

    assert REG['metricOverrides']['tariStandardHousehold']['profile'] == 'mef-municipal-tax-annual'
    assert REG['metricOverrides']['municipalImuStandard']['profile'] == 'mef-municipal-tax-annual'
    assert REG['metricOverrides']['fuelPrices']['profile'] == 'mimit-fuel-daily'
    assert REG['metricOverrides']['wasteServiceCost']['profile'] == 'ispra-environment-annual'
    assert REG['sourceProfileByUrl'][NIC['sourceUrl']] == 'istat-nic-national-annual'

    for token in ['tariStandardHousehold:', 'municipalImuStandard:', 'fuelPrices:', 'wasteServiceCost:', "case 'currency2'", "case 'eurliter'", "case 'eurPerResident'"]:
        assert token in APP00
    assert 'metric-context-jump' in APP02
    assert "themeKey === 'economia' ? incomeInflationMarkup(data)" in APP03
    assert 'row.displayValue === null' in APP03
    assert 'function incomeInflationMarkup(data)' in APP05
    assert 'NIC nazionale ISTAT' in APP05
    assert 'row.longSeries' in APP05
    assert 'function historyMetric(metric)' in UX
    assert 'selected.metric.meta.longHistoryNote' in UX
    assert "token === 'currency2'" in VISUAL
    assert "kind === 'eurliter'" in VISUAL
    assert "kind === 'eurperresident'" in VISUAL

    draft = DATA['costsFiscalDraft']
    assert draft['publishedInDraft'] == ['municipalIrpef', 'tariStandardHousehold', 'municipalImuStandard', 'fuelPrices', 'wasteServiceCost']
    assert draft['notPublished'] == ['schoolMeals']

    print('Draft validato: 126 indicatori = 122 inline + 4 esterni; unità assi corrette, IMU senza selettore aliquota, reddito imponibile omogeneo 2011-2024, NIC Italia 2016-2024')


if __name__ == '__main__':
    main()
