#!/usr/bin/env python3
"""Valida la materializzazione completa dei quattro candidati Redditi Lotto A."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data/site-data.json').read_text(encoding='utf-8'))
SNAPSHOT = json.loads((ROOT / 'data/source-snapshots/mef-income-lotto-a-2024.json').read_text(encoding='utf-8'))
DEMO = json.loads((ROOT / 'data/source-snapshots/istat-demography-lotto-a-2026-08.json').read_text(encoding='utf-8'))
REGISTRY = json.loads((ROOT / 'data/source-registry.json').read_text(encoding='utf-8'))
MONITOR = json.loads((ROOT / 'data/source-monitor-state.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data/data-audit-lotto-a.json').read_text(encoding='utf-8'))

TOWNS = {'Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio'}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def adults(town: str) -> int:
    return sum(int(row['total']) for row in DEMO['posas']['ageSex2026'][town] if 18 <= int(row['age']) <= 120)


def main() -> None:
    require(SITE['version'] == 'v1.15.0', 'Versione dati inattesa')
    require(len(SITE['metrics']) == 132, f"Metriche inattese: {len(SITE['metrics'])}")
    require(REGISTRY['expectedMetricCount'] == 132, 'Registry totale inatteso')
    require(REGISTRY['expectedInlineMetricCount'] == 128, 'Registry inline inatteso')
    require(REGISTRY['expectedExternalMetricCount'] == 4, 'Registry external inatteso')

    # 1. Reddito per fonte: un solo composito, non una card per ogni fonte.
    source_metric = SITE['metrics']['incomeSourceProfile']
    require(source_metric['meta']['compositeType'] == 'securityMeasures', 'Renderer composito fonti inatteso')
    require(len(source_metric['rows']) == 7, 'Fonti reddito non 7/7')
    for row in source_metric['rows']:
        require(len(row['parts']) == 7, f"{row['town']}: fonti incomplete")
        employment = row['parts'][0]
        detail = SNAPSHOT['towns'][row['town']]
        raw = next(item for item in detail['incomeSources'] if item['key'] == 'employment')
        expected = raw['amountEuro'] / raw['frequency']
        require(abs(employment['value'] - expected) < 1e-9, f"{row['town']}: media lavoro dipendente errata")
    stazzema_ordinary = next(part for part in next(row for row in source_metric['rows'] if row['town']=='Stazzema')['parts'] if part['label']=='Impresa · contabilità ordinaria')
    require(stazzema_ordinary['value'] is None and stazzema_ordinary['count'] is None,
            'Stazzema: cella impresa ordinaria vuota trasformata in zero')

    # 2. Distribuzione: 8 fasce visibili e n.d. preservati.
    distribution = SITE['metrics']['incomeDistribution']
    for row in distribution['rows']:
        require(len(row.get('detailParts', [])) == 8, f"{row['town']}: dettaglio 8 fasce assente")
        total = SNAPSHOT['towns'][row['town']]['totalIncome']['frequency']
        for part, raw in zip(row['detailParts'], SNAPSHOT['towns'][row['town']]['incomeBands']):
            if raw['frequency'] is None:
                require(part['value'] is None and part['count'] is None, f"{row['town']}/{part['label']}: n.d. perso")
            else:
                require(part['count'] == raw['frequency'], f"{row['town']}/{part['label']}: conteggio errato")
                require(abs(part['value'] - raw['frequency']/total*100) < 1e-9, f"{row['town']}/{part['label']}: quota errata")

    # 3. Peso pensioni resta pubblicato.
    pension = SITE['metrics']['pensionIncomeShare']
    require(len(pension['rows']) == 7 and pension['method']['coverage'] == '7/7', 'Peso pensioni non valido')

    # 4. Contribuenti ogni 100 maggiorenni: formula MEF / Istat 18+.
    taxpayers = SITE['metrics']['taxpayersAdultPopulationRate']
    require(taxpayers['meta']['unit'] == 'per100', 'Unità contribuenti/maggiorenni inattesa')
    require(len(taxpayers['rows']) == 7, 'Contribuenti/maggiorenni non 7/7')
    for row in taxpayers['rows']:
        town = row['town']
        expected_adults = adults(town)
        raw_taxpayers = SNAPSHOT['towns'][town]['taxpayers']
        expected = raw_taxpayers / expected_adults * 100
        require(row['adultPopulation2026'] == expected_adults, f'{town}: popolazione 18+ errata')
        require(abs(row['value'] - expected) < 1e-9, f'{town}: rapporto contribuenti/maggiorenni errato')
        require(SNAPSHOT['towns'][town]['adultPopulation2026'] == expected_adults, f'{town}: snapshot 18+ assente')

    economy = SITE['themes']['economia']
    redditi = next(section for section in economy['sections'] if section['key'] == 'redditi')
    require(redditi['metrics'] == [
        'income','incomeDistribution','incomeSourceProfile','pensionIncomeShare',
        'taxpayersAdultPopulationRate','incomeVsInflation'
    ], f"Ordine sezione Redditi inatteso: {redditi['metrics']}")

    mef_metrics = MONITOR['sources']['https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php']['metrics']
    istat_metrics = MONITOR['sources']['https://demo.istat.it/']['metrics']
    require('incomeSourceProfile' in mef_metrics, 'Fonti reddito non monitorate')
    require('taxpayersAdultPopulationRate' in mef_metrics and 'taxpayersAdultPopulationRate' in istat_metrics,
            'Indicatore contribuenti non monitorato su entrambe le fonti')

    decisions = {item['key']: item.get('implementationStatus') for item in AUDIT['candidates']}
    require(decisions['taxpayersAdultPopulationRate'] == 'draft_materialized', 'Contribuenti ancora VERIFY')
    require(decisions['incomeSourceAndBandsDetail'] == 'visible_composite_and_8_band_detail', 'Fonti/fasce non marcate visibili')

    print('Redditi Lotto A v2 OK: fonti, 8 fasce, pensioni e contribuenti/maggiorenni tutti materializzati con semantica verificata.')


if __name__ == '__main__':
    main()
