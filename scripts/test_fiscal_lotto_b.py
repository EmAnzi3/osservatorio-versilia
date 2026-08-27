#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

from finalize_catalog_release import EXPECTED_EXTERNAL, EXPECTED_INLINE, EXPECTED_METRICS

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data' / 'site-data.json'
REGISTRY = ROOT / 'data' / 'source-registry.json'
SNAPSHOT = ROOT / 'data' / 'source-snapshots' / 'fiscal-lotto-b-2025.json'
KEY = 'fiscalRecoveryActivity'

EXPECTED_TOTALS = {
    'Massarosa': 687088.75,
    'Viareggio': 3125634.70,
    'Camaiore': 4929520.42,
    'Pietrasanta': 3032379.43,
    'Seravezza': 1084109.15,
    'Forte dei Marmi': 1814328.18,
    'Stazzema': 184724.85,
}
EXPECTED_DAIT = {
    'Massarosa': 0.0,
    'Viareggio': 82.5,
    'Camaiore': 0.0,
    'Pietrasanta': 165.0,
    'Seravezza': 0.0,
    'Forte dei Marmi': 0.0,
    'Stazzema': 0.0,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(a: float, b: float, tolerance: float = 0.011) -> bool:
    return math.isclose(float(a), float(b), abs_tol=tolerance)


def main() -> None:
    site = json.loads(SITE.read_text(encoding='utf-8'))
    registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
    snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))

    # Il lotto Fiscalità B resta invariato; il gate segue il contratto globale corrente.
    require(len(site['metrics']) == EXPECTED_METRICS, f"Conteggio metriche inatteso: {len(site['metrics'])}")
    require(registry['expectedMetricCount'] == EXPECTED_METRICS, 'Registry totale non riallineato')
    require(registry['expectedInlineMetricCount'] == EXPECTED_INLINE, 'Inline count non riallineato')
    require(registry['expectedExternalMetricCount'] == EXPECTED_EXTERNAL, 'External count non riallineato')

    metric = site['metrics'].get(KEY)
    require(metric is not None, 'Indicatore Fiscalità Lotto B assente')
    require(metric['meta']['compositeType'] == 'securityMeasures', 'Il Lotto B deve restare una sola card con selettore')
    require(len(metric['rows']) == 7, 'Copertura comunale diversa da 7/7')
    require('Non è un tasso di evasione fiscale' in metric['meta']['description'], 'Disclaimer evasione fiscale assente')

    rows = {row['town']: row for row in metric['rows']}
    require(set(rows) == set(EXPECTED_TOTALS), f'Comuni inattesi: {set(rows)}')
    for town, expected in EXPECTED_TOTALS.items():
        row = rows[town]
        require(len(row['parts']) == 3, f'{town}: selettore deve avere esattamente tre letture')
        require(close(row['parts'][1]['value'], expected), f'{town}: totale SIOPE errato {row["parts"][1]["value"]}')
        require(close(row['parts'][2]['value'], EXPECTED_DAIT[town]), f'{town}: contributo DAIT errato')
        raw = snapshot['towns'][town]
        require(close(sum(raw['breakdownEuro'].values()), expected), f'{town}: breakdown SIOPE non torna')
        require(close(row['parts'][0]['value'], expected / raw['populationIstat']), f'{town}: valore per residente errato')
        require(raw['siopeMonth'] == '2025/12', f'{town}: SIOPE non consolidato a dicembre')

    total = sum(EXPECTED_TOTALS.values())
    population = sum(snapshot['towns'][town]['populationIstat'] for town in EXPECTED_TOTALS)
    require(close(metric['aggregate']['parts'][0]['value'], total / population), 'Aggregato Versilia €/residente errato')
    require(close(metric['aggregate']['parts'][1]['value'], total), 'Aggregato Versilia totale errato')
    require(close(metric['aggregate']['parts'][2]['value'], 247.5), 'Aggregato DAIT Versilia errato')

    section = next(section for section in site['themes']['economia']['sections'] if section.get('key') == 'costi-fiscalita')
    require(section['metrics'].count(KEY) == 1, 'Indicatore non presente una sola volta nella sezione Costi e fiscalità')
    require(site['themes']['economia']['metrics'].count(KEY) == 1, 'Indicatore duplicato nel tema Economia')
    require(registry['metricOverrides'][KEY]['profile'] == 'siope-monthly', 'Profilo SIOPE non registrato')
    require(registry['sourceProfileByUrl'][snapshot['daitUrl']] == 'dait-fiscal-assessment-annual', 'Profilo DAIT non registrato')

    print(
        f'Fiscalità Lotto B verificata: 1 card, 3 letture, SIOPE 7/7 e DAIT 2/7 beneficiari; '
        f'catalogo {EXPECTED_METRICS} = {EXPECTED_INLINE}+{EXPECTED_EXTERNAL}.'
    )


if __name__ == '__main__':
    main()
