#!/usr/bin/env python3
"""Validazione dati degli approfondimenti Demografia Lotto A v2."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data' / 'data-audit-lotto-a.json').read_text(encoding='utf-8'))
SNAPSHOT = json.loads((ROOT / 'data' / 'source-snapshots' / 'istat-demography-lotto-a-2026-08.json').read_text(encoding='utf-8'))

EXPECTED_TOWNS = {'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio'}
EXPECTED_AGE_LABELS = [
    '0–14 anni', '15–19 anni', '20–34 anni', '35–49 anni',
    '50–64 anni', '65–79 anni', '80–84 anni', '85 anni e oltre',
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Questa fase non crea nuove card demografiche; il totale riflette il catalogo corrente.
    require(len(SITE['metrics']) == 149, f"Conteggio metriche inatteso: {len(SITE['metrics'])}")

    age = SITE['metrics']['ageDistribution']
    require(age['meta']['year'] == '2026', 'ageDistribution non riallineata al 2026')
    require('85 anni e oltre' in age['meta']['description'], 'Descrizione ageDistribution non espone 85+')
    require('intera Versilia' in age['meta']['description'], 'Descrizione ageDistribution non espone la piramide Versilia')
    require({row['town'] for row in age['rows']} == EXPECTED_TOWNS, 'Copertura ageDistribution non 7/7')

    total_versilia = 0
    for row in age['rows']:
        town = row['town']
        detail = sorted(SNAPSHOT['posas']['ageSex2026'][town], key=lambda item: int(item['age']))
        total = sum(int(item['total']) for item in detail)
        total_versilia += total
        count8084 = sum(int(item['total']) for item in detail if 80 <= int(item['age']) <= 84)
        count85 = sum(int(item['total']) for item in detail if int(item['age']) >= 85)

        require(len(row['parts']) == 8, f'{town}: fasce principali non 8')
        require([part['label'] for part in row['parts']] == EXPECTED_AGE_LABELS, f'{town}: etichette fasce inattese')
        require(sum(int(part['count']) for part in row['parts']) == total, f'{town}: fasce non esaustive')
        require(row['parts'][-2]['count'] == count8084, f'{town}: 80–84 incoerente')
        require(row['parts'][-1]['count'] == count85, f'{town}: 85+ incoerente')
        require('seniorAgeDetail' not in row and 'age85PlusDetail' not in row, f'{town}: dettaglio 85+ duplicato ancora presente')

        pyramid = row['ageSexPyramid']
        require(pyramid['year'] == 2026, f'{town}: piramide anno errato')
        require(len(pyramid['displayBands']) == 21, f'{town}: piramide deve avere 20 quinquenni + 100+')
        require(pyramid['displayBands'][0]['label'] == '0–4', f'{town}: prima fascia piramide errata')
        require(pyramid['displayBands'][-1]['label'] == '100+', f'{town}: ultima fascia piramide errata')
        require(sum(item['men'] + item['women'] for item in pyramid['displayBands']) == total,
                f'{town}: piramide non ricostruisce la popolazione')

    aggregate = age['aggregate']
    require(len(aggregate['parts']) == 8, 'Versilia: fasce aggregate non 8')
    require([part['label'] for part in aggregate['parts']] == EXPECTED_AGE_LABELS, 'Versilia: etichette fasce inattese')
    versilia_pyramid = aggregate.get('ageSexPyramid', {})
    require(versilia_pyramid.get('year') == 2026, 'Versilia: piramide anno errato o assente')
    require(len(versilia_pyramid.get('displayBands', [])) == 21, 'Versilia: piramide non ha 21 classi')
    require(versilia_pyramid['displayBands'][0]['label'] == '0–4', 'Versilia: prima fascia piramide errata')
    require(versilia_pyramid['displayBands'][-1]['label'] == '100+', 'Versilia: ultima fascia piramide errata')
    require(sum(item['men'] + item['women'] for item in versilia_pyramid['displayBands']) == total_versilia,
            'Versilia: piramide aggregata non ricostruisce la somma dei sette comuni')

    # Non deve esistere un secondo pannello che ripropone dati già pubblicati
    # negli indicatori naturale / mobilità interna / mobilità estera.
    change = SITE['metrics']['populationChange']
    require('detailLabel' not in change['meta'], 'populationChange conserva un detailLabel duplicato')
    require('componentDetail' not in change.get('method', {}), 'populationChange conserva metodo duplicato')
    require(all('changeComponents' not in row for row in change['rows']), 'Componenti variazione duplicate ancora materializzate')

    decisions = {candidate.get('key'): candidate.get('implementationStatus') for candidate in AUDIT.get('candidates', [])}
    require(decisions.get('share80Plus') == 'public_distribution_split_80_84_85_plus_2026', 'Audit 80–84/85+ non aggiornato')
    require(decisions.get('populationAgeSexDetail') == 'public_pyramid_2026_towns_and_versilia', 'Audit piramide Versilia non aggiornato')
    require(AUDIT.get('demographyV2', {}).get('populationAgeSexPyramid') == 'public_town_and_versilia_native_tooltip',
            'Audit demographyV2 non registra la piramide Versilia')
    require(AUDIT.get('demographyV2', {}).get('populationChangeComponents') == 'not_added_duplicate_existing_metrics',
            'Audit componenti variazione deve segnare il dato come duplicato non aggiunto')

    print('Demografia Lotto A v2 dati OK: 85+ nella distribuzione, piramide comuni + Versilia, componenti variazione non duplicate.')


if __name__ == '__main__':
    main()
