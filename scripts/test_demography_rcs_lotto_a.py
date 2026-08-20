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


def main() -> None:
    metric = SITE['metrics']['foreignResidents']
    require(metric['meta']['year'] == '2025', 'foreignResidents deve restare 2025')
    require('paesi esteri di nascita' in metric['meta']['description'].lower(), 'Descrizione RCS non visibile')
    require(SNAPSHOT['coverage'] == '7/7', 'Snapshot RCS non 7/7')
    require(set(SNAPSHOT['towns']) == EXPECTED_TOWNS, 'Town snapshot RCS inattese')

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
        require(1 <= len(detail['citizenshipTop']) <= 8, f'{town}: top cittadinanze vuota o troppo lunga')
        require(1 <= len(detail['birthCountryTop']) <= 8, f'{town}: top nascita vuota o troppo lunga')
        require(all(item['label'].lower() != 'italia' for item in detail['citizenshipTop']), f'{town}: Italia inclusa nelle cittadinanze straniere')
        require(all(item['label'].lower() != 'italia' for item in detail['birthCountryTop']), f'{town}: Italia inclusa nei paesi esteri di nascita')
        require(detail['citizenshipTop'] == sorted(detail['citizenshipTop'], key=lambda item: (-item['count'], item['label'])), f'{town}: top cittadinanze non ordinata')
        require(detail['birthCountryTop'] == sorted(detail['birthCountryTop'], key=lambda item: (-item['count'], item['label'])), f'{town}: top nascita non ordinata')
        require(all(item['total'] > 0 for item in snap['citizenship']), f'{town}: cittadinanze con zero nello snapshot')
        require(all(item['total'] > 0 for item in snap['birthCountry']), f'{town}: paesi nascita con zero nello snapshot')

    decisions = {candidate.get('key'): candidate.get('implementationStatus') for candidate in AUDIT.get('candidates', [])}
    require(decisions.get('citizenshipBirthCountryDetail') == 'public_town_detail_2025', 'Audit RCS non promosso a dettaglio pubblico')
    require(AUDIT.get('demographyV2', {}).get('foreignCitizenshipBirthCountry') == 'public_town_detail_2025', 'Stato demographyV2 RCS errato')

    print('RCS Demografia OK: cittadinanze e paesi di nascita 2025 leggibili 7/7 senza nuove card.')


if __name__ == '__main__':
    main()
