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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Questa fase non crea nuove card: il catalogo resta quello Demografia v1.14.
    require(len(SITE['metrics']) == 129, f"Conteggio metriche inatteso: {len(SITE['metrics'])}")

    age = SITE['metrics']['ageDistribution']
    require(age['meta']['year'] == '2026', 'ageDistribution non riallineata al 2026')
    require('85+' in age['meta']['description'], 'Descrizione ageDistribution non espone 85+')
    require({row['town'] for row in age['rows']} == EXPECTED_TOWNS, 'Copertura ageDistribution non 7/7')

    for row in age['rows']:
        town = row['town']
        detail = sorted(SNAPSHOT['posas']['ageSex2026'][town], key=lambda item: int(item['age']))
        total = sum(int(item['total']) for item in detail)
        count80 = sum(int(item['total']) for item in detail if int(item['age']) >= 80)
        count85 = sum(int(item['total']) for item in detail if int(item['age']) >= 85)

        require(len(row['parts']) == 7, f'{town}: fasce principali non 7')
        require(sum(int(part['count']) for part in row['parts']) == total, f'{town}: fasce non esaustive')
        senior = row['seniorAgeDetail']
        require(senior['year'] == 2026, f'{town}: anno senior errato')
        require(senior['age80Plus']['count'] == count80, f'{town}: 80+ incoerente')
        require(senior['age85Plus']['count'] == count85, f'{town}: 85+ incoerente')
        require(count85 <= count80, f'{town}: 85+ maggiore di 80+')
        require(abs(senior['age80Plus']['value'] - count80 / total * 100) < 1e-9, f'{town}: quota 80+ errata')
        require(abs(senior['age85Plus']['value'] - count85 / total * 100) < 1e-9, f'{town}: quota 85+ errata')

        pyramid = row['ageSexPyramid']
        require(pyramid['year'] == 2026, f'{town}: piramide anno errato')
        require(len(pyramid['displayBands']) == 21, f'{town}: piramide deve avere 20 quinquenni + 100+')
        require(pyramid['displayBands'][0]['label'] == '0–4', f'{town}: prima fascia piramide errata')
        require(pyramid['displayBands'][-1]['label'] == '100+', f'{town}: ultima fascia piramide errata')
        require(sum(item['men'] + item['women'] for item in pyramid['displayBands']) == total,
                f'{town}: piramide non ricostruisce la popolazione')

    change = SITE['metrics']['populationChange']
    require(change['meta']['detailLabel'] == 'Componenti della variazione demografica', 'Detail label variazione assente')
    for row in change['rows']:
        detail = row.get('changeComponents')
        require(detail is not None, f"{row['town']}: componenti variazione assenti")
        require(detail['year'] == 2024, f"{row['town']}: anno comune non 2024")
        require([part['label'] for part in detail['parts']] == [
            'Saldo naturale', 'Saldo migratorio interno', 'Saldo migratorio con l’estero'
        ], f"{row['town']}: componenti inattese")
        require(detail['series']['years'] == list(range(2019, 2025)), f"{row['town']}: serie componenti non 2019–2024")
        require(all(len(detail['series'][key]) == 6 for key in ('natural', 'internal', 'foreign')),
                f"{row['town']}: lunghezza serie componenti errata")

    decisions = {candidate.get('key'): candidate.get('implementationStatus') for candidate in AUDIT.get('candidates', [])}
    require(decisions.get('share80Plus') == 'public_detail_80_85_2026', 'Audit 80+/85+ non aggiornato')
    require(decisions.get('populationAgeSexDetail') == 'public_pyramid_2026', 'Audit piramide non aggiornato')
    require(AUDIT.get('demographyV2', {}).get('populationChangeComponents') == 'public_town_detail_2024',
            'Audit componenti variazione non aggiornato')

    print('Demografia Lotto A v2 dati OK: 80+/85+, piramide e componenti variazione sono pronti per il frontend.')


if __name__ == '__main__':
    main()
