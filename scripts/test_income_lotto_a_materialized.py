#!/usr/bin/env python3
"""Validazione del primo stadio della tranche Redditi / fiscalità del Lotto A.

Questo test resta compatibile con la v2: valida il nucleo MEF/pensioni anche
quando il secondo stadio ha già aggiunto altri indicatori e dettagli pubblici.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data/site-data.json').read_text(encoding='utf-8'))
REGISTRY = json.loads((ROOT / 'data/source-registry.json').read_text(encoding='utf-8'))
MONITOR = json.loads((ROOT / 'data/source-monitor-state.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data/data-audit-lotto-a.json').read_text(encoding='utf-8'))
SNAPSHOT = json.loads((ROOT / 'data/source-snapshots/mef-income-lotto-a-2024.json').read_text(encoding='utf-8'))

EXPECTED_TOWNS = {
    'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta',
    'Seravezza', 'Stazzema', 'Viareggio',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(SITE['version'] == 'v1.15.0', 'Versione v1.15.0 non applicata')
    require(SITE['updated'] == '20 agosto 2026', 'Data aggiornamento inattesa')
    require(len(SITE['metrics']) >= 130, f"Metriche inferiori al nucleo v1: {len(SITE['metrics'])}")
    external = [
        key for key, metric in SITE['metrics'].items()
        if metric.get('dataStorage', {}).get('type') == 'external-climate'
    ]
    require(len(external) == 4, f'Indicatori climatici esterni inattesi: {external}')
    require(REGISTRY['expectedMetricCount'] == len(SITE['metrics']), 'Registry total count incoerente')
    require(REGISTRY['expectedInlineMetricCount'] == len(SITE['metrics']) - 4, 'Registry inline count incoerente')
    require(REGISTRY['expectedExternalMetricCount'] == 4, 'Registry external count inatteso')

    metric = SITE['metrics']['pensionIncomeShare']
    require(metric['meta']['theme'] == 'economia', 'Tema pensioni errato')
    require(metric['meta']['unit'] == 'percent', 'Unità pensioni errata')
    require(metric['meta']['year'] == '2024', 'Anno pensioni errato')
    require(metric['method']['coverage'] == '7/7', 'Copertura pensioni non 7/7')
    require(len(metric['rows']) == 7, 'Righe pensioni non 7')
    require({row['town'] for row in metric['rows']} == EXPECTED_TOWNS, 'Comuni pensioni inattesi')
    for row in metric['rows']:
        require(row['series']['years'] == [2024], f"Serie pensioni inattesa: {row['town']}")
        require(row['series']['values'] == [row['value']], f"Serie/valore pensioni incoerente: {row['town']}")
        detail = SNAPSHOT['towns'][row['town']]
        expected = detail['pensionIncome']['amountEuro'] / detail['totalIncome']['amountEuro'] * 100
        require(abs(row['value'] - expected) < 1e-10, f"Formula pensioni errata: {row['town']}")

    massarosa = SNAPSHOT['towns']['Massarosa']
    require(massarosa['pensionIncome']['frequency'] == 5530, 'Frequenza pensione Massarosa inattesa')
    require(massarosa['pensionIncome']['amountEuro'] == 111076251, 'Ammontare pensioni Massarosa inatteso')
    require(massarosa['totalIncome']['amountEuro'] == 369561101, 'Reddito complessivo Massarosa inatteso')

    require(SNAPSHOT['coverage'] == '7/7', 'Snapshot redditi non 7/7')
    require(set(SNAPSHOT['towns']) == EXPECTED_TOWNS, 'Snapshot redditi comuni inattesi')
    for town, detail in SNAPSHOT['towns'].items():
        require(len(detail['incomeSources']) == 7, f'{town}: fonti reddito incomplete')
        require(len(detail['incomeBands']) == 8, f'{town}: fasce reddito incomplete')
        require(detail['taxpayers'] is not None, f'{town}: contribuenti mancanti')
        require(detail['totalIncome']['frequency'] is not None, f'{town}: frequenza reddito complessivo mancante')
        require(detail['totalIncome']['amountEuro'] is not None, f'{town}: ammontare reddito complessivo mancante')

    stazzema_ordinary = next(
        item for item in SNAPSHOT['towns']['Stazzema']['incomeSources']
        if item['key'] == 'entrepreneurOrdinary'
    )
    require(stazzema_ordinary['frequency'] is None and stazzema_ordinary['amountEuro'] is None,
            'Stazzema: cella MEF vuota trasformata in zero')
    camaiore_top = next(
        item for item in SNAPSHOT['towns']['Camaiore']['incomeBands']
        if item['key'] == 'over120k'
    )
    require(camaiore_top['frequency'] is None and camaiore_top['amountEuro'] is None,
            'Camaiore: fascia >120k vuota trasformata in zero')

    distribution = SITE['metrics']['incomeDistribution']
    require(distribution['meta']['detailDataset']['key'] == 'incomeBandsFull2024', 'Link dataset fasce assente')
    require('incomeSourcesAndBands2024' in SITE.get('detailDatasets', {}), 'Dataset editoriale redditi assente')
    require('incomeSourceAndBandsDetail' not in SITE['metrics'], 'Dataset dettaglio non deve diventare una card')
    require('incomeBandsFull2024' not in SITE['metrics'], 'Fasce complete non devono diventare una card')

    require(REGISTRY['metricOverrides']['pensionIncomeShare']['profile'] == 'mef-irpef-annual',
            'Profilo fonte pensioni inatteso')
    print('Nucleo Redditi Lotto A v1 verificato: pensioni 7/7, fonti e 8 fasce MEF preservate senza falsi zeri.')


if __name__ == '__main__':
    main()
