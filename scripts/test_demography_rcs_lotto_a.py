#!/usr/bin/env python3
"""Validazione del dettaglio Istat RCS 2025 collegato ai residenti stranieri."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data' / 'data-audit-lotto-a.json').read_text(encoding='utf-8'))
SNAPSHOT = json.loads((ROOT / 'data' / 'source-snapshots' / 'istat-rcs-demography-2025.json').read_text(encoding='utf-8'))

EXPECTED_TOWNS = {'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio'}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_top(items: list[dict], label: str) -> None:
    require(1 <= len(items) <= 8, f'{label}: top vuota o troppo lunga')
    require(all(item['label'].lower() != 'italia' for item in items), f'{label}: Italia inclusa')
    require(items == sorted(items, key=lambda item: (-item['count'], item['label'])), f'{label}: top non ordinata')


def main() -> None:
    metric = SITE['metrics']['foreignResidents']
    require(metric['meta']['year'] == '2025', 'foreignResidents deve restare 2025')
    require('ranking aggregato Versilia' in metric['meta']['description'], 'Descrizione RCS aggregata non visibile')
    require(SNAPSHOT['coverage'] == '7/7', 'Snapshot RCS non 7/7')
    require(set(SNAPSHOT['towns']) == EXPECTED_TOWNS, 'Town snapshot RCS inattese')
    require('aggregate' in SNAPSHOT and 'Versilia' in SNAPSHOT['aggregate'], 'Snapshot RCS senza aggregato Versilia')

    rows = {row['town']: row for row in metric['rows']}
    require(set(rows) == EXPECTED_TOWNS, 'foreignResidents non 7/7')
    for town in EXPECTED_TOWNS:
        row = rows[town]
        detail = row.get('foreignOrigins')
        require(detail is not None, f'{town}: foreignOrigins assente')
        snap = SNAPSHOT['towns'][town]
        require(detail['citizenshipTotal'] == row['count'], f'{town}: totale cittadinanze non coincide con residenti stranieri')
        require(detail['citizenshipTotal'] == snap['citizenshipTotal'], f'{town}: totale cittadinanze snapshot incoerente')
        require(detail['foreignBornTotal'] == snap['foreignBornTotal'], f'{town}: totale nati estero snapshot incoerente')
        assert_top(detail['citizenshipTop'], f'{town}: cittadinanze')
        assert_top(detail['birthCountryTop'], f'{town}: paesi nascita')
        require(all(item['total'] > 0 for item in snap['citizenship']), f'{town}: cittadinanze con zero nello snapshot')
        require(all(item['total'] > 0 for item in snap['birthCountry']), f'{town}: paesi nascita con zero nello snapshot')

    aggregate = metric['aggregate'].get('foreignOrigins')
    require(aggregate is not None, 'foreignResidents senza dettaglio aggregato Versilia')
    require(aggregate['scope'] == 'Versilia', 'Aggregato RCS con scope inatteso')
    require(aggregate['citizenshipTotal'] == sum(SNAPSHOT['towns'][town]['citizenshipTotal'] for town in EXPECTED_TOWNS),
            'Aggregato cittadinanze Versilia non somma i sette comuni')
    require(aggregate['foreignBornTotal'] == sum(SNAPSHOT['towns'][town]['foreignBornTotal'] for town in EXPECTED_TOWNS),
            'Aggregato nati estero Versilia non somma i sette comuni')
    require(aggregate['citizenshipTotal'] == metric['aggregate']['count'],
            'Aggregato cittadinanze Versilia non coincide con residenti stranieri aggregati')
    assert_top(aggregate['citizenshipTop'], 'Versilia: cittadinanze')
    assert_top(aggregate['birthCountryTop'], 'Versilia: paesi nascita')
    snap_aggregate = SNAPSHOT['aggregate']['Versilia']
    require(snap_aggregate['citizenshipTotal'] == aggregate['citizenshipTotal'], 'Snapshot aggregato cittadinanze incoerente')
    require(snap_aggregate['foreignBornTotal'] == aggregate['foreignBornTotal'], 'Snapshot aggregato nati estero incoerente')

    decisions = {candidate.get('key'): candidate.get('implementationStatus') for candidate in AUDIT.get('candidates', [])}
    require(decisions.get('citizenshipBirthCountryDetail') == 'public_town_and_versilia_detail_2025', 'Audit RCS non promosso a dettaglio pubblico completo')
    require(AUDIT.get('demographyV2', {}).get('foreignCitizenshipBirthCountry') == 'public_compare_and_town_detail_2025', 'Stato demographyV2 RCS errato')

    print('RCS Demografia OK: cittadinanze e paesi di nascita 2025 leggibili nei comuni e come aggregato Versilia senza nuove card.')


if __name__ == '__main__':
    main()
