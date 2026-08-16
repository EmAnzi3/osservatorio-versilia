#!/usr/bin/env python3
"""Extract the long municipal MEF taxable-income series, tax years 2011-2024.

This is intentionally distinct from the site's current headline "Reddito medio
dichiarato", which uses Reddito complessivo where that direct variable exists.
For a genuinely homogeneous long history we use the direct MEF pair:

  Reddito imponibile - Ammontare / Reddito imponibile - Frequenza

No income-class reconstruction is used.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

URL = (
    'https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
    'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.zip'
)
TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(ch for ch in value if not unicodedata.combining(ch)).lower().strip()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise RuntimeError('encoding CSV MEF non riconosciuto')


def number(value: str) -> float:
    text = (value or '').strip().replace('\u00a0', '').replace(' ', '')
    if not text or text.lower() in {'-', 'n.d.', 'nd'}:
        raise ValueError(f'valore numerico mancante: {value!r}')
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    return float(text)


def choose(headers: list[str], exact: set[str], contains: tuple[str, ...] = ()) -> str:
    normalized = {header: norm(header) for header in headers}
    direct = [header for header, value in normalized.items() if value in exact]
    if len(direct) == 1:
        return direct[0]
    fallback = [header for header, value in normalized.items() if all(token in value for token in contains)] if contains else []
    if len(fallback) == 1:
        return fallback[0]
    raise RuntimeError(f'colonna non univoca exact={exact}, contains={contains}: direct={direct}, fallback={fallback}')


def read_year(year: int) -> dict:
    url = URL.format(year=year)
    request = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-audit/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if len(members) != 1:
            raise RuntimeError(f'{year}: file archivio inattesi {members}')
        member = members[0]
        text = decode(archive.read(member))
    try:
        delimiter = csv.Sniffer().sniff(text[:10000], delimiters=';,\t|').delimiter
    except csv.Error:
        delimiter = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    town_h = choose(headers, {'denominazione comune', 'denominazione del comune', 'comune'}, ('comune',))
    province_h = next((h for h in headers if norm(h) in {'sigla provincia', 'provincia'}), None)
    amount_h = choose(
        headers,
        {'reddito imponibile ammontare', 'reddito imponibile ammontare in euro', 'reddito imponibile importo', 'reddito imponibile importo in euro'},
        ('reddito imponibile', 'ammontare'),
    )
    frequency_h = choose(
        headers,
        {'reddito imponibile frequenza', 'reddito imponibile numero'},
        ('reddito imponibile', 'frequenza'),
    )
    wanted = {norm(town): town for town in TOWNS}
    found = {}
    for row in reader:
        town = wanted.get(norm(row.get(town_h, '')))
        if not town:
            continue
        if province_h and norm(row.get(province_h, '')) not in {'lu', 'lucca'}:
            continue
        amount = number(row.get(amount_h, ''))
        frequency = int(round(number(row.get(frequency_h, ''))))
        if frequency <= 0:
            raise RuntimeError(f'{year} {town}: frequenza imponibile non positiva')
        found[town] = {
            'amount': amount,
            'frequency': frequency,
            'average': round(amount / frequency, 2),
        }
    missing = [town for town in TOWNS if town not in found]
    if missing:
        raise RuntimeError(f'{year}: comuni mancanti {missing}')
    return {
        'year': year,
        'url': url,
        'archiveMember': member,
        'delimiter': delimiter,
        'headers': {'town': town_h, 'province': province_h, 'amount': amount_h, 'frequency': frequency_h},
        'towns': found,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=2011)
    parser.add_argument('--end', type=int, default=2024)
    parser.add_argument('--out', type=Path, default=Path('/tmp/mef-taxable-income-history.json'))
    args = parser.parse_args()
    years = [read_year(year) for year in range(args.start, args.end + 1)]
    towns = {
        town: {str(item['year']): item['towns'][town] for item in years}
        for town in TOWNS
    }
    snapshot = {
        'schemaVersion': 1,
        'source': 'Dipartimento delle Finanze - MEF',
        'definition': 'Reddito imponibile - Ammontare / Reddito imponibile - Frequenza',
        'taxYears': [item['year'] for item in years],
        'coverage': '7/7',
        'schemaByYear': {
            str(item['year']): {
                'url': item['url'],
                'archiveMember': item['archiveMember'],
                'delimiter': item['delimiter'],
                'headers': item['headers'],
            }
            for item in years
        },
        'towns': towns,
        'note': (
            'Serie lunga omogenea distinta dal Reddito complessivo usato come dato principale corrente. '
            'Non vengono sommate le fasce di reddito complessivo per ricostruire anni mancanti.'
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'MEF taxable-income audit: {args.start}-{args.end}, 7/7')
    for town in TOWNS:
        values = ', '.join(f"{year}:{towns[town][str(year)]['average']:.2f}" for year in range(args.start, args.end + 1))
        print(f'{town}: {values}')
    print(f'Snapshot: {args.out}')


if __name__ == '__main__':
    main()
