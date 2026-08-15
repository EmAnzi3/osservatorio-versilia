#!/usr/bin/env python3
"""Audit and extract the municipal MEF income series from official ZIP files.

The script deliberately downloads each tax-year dataset independently so that a
schema or definition change cannot be hidden by a pre-joined third-party file.
It extracts exactly the current Observatorio definition:

    Reddito complessivo - Ammontare / Reddito complessivo - Frequenza

for the seven municipalities.  It writes a compact JSON snapshot suitable for
review/materialisation; it does not modify site-data.json by itself.
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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path('/tmp/mef-income-history.json')
URL = (
    'https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
    'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.zip'
)
TOWNS = [
    'Camaiore',
    'Forte dei Marmi',
    'Massarosa',
    'Pietrasanta',
    'Seravezza',
    'Stazzema',
    'Viareggio',
]


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("’", "'").replace('`', "'").lower().strip()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError('unknown', b'', 0, 1, 'Unable to decode MEF CSV')


def number(value: str) -> float:
    text = (value or '').strip().replace('\u00a0', '').replace(' ', '')
    if not text or text in {'-', 'n.d.', 'nd'}:
        raise ValueError(f'Valore numerico mancante: {value!r}')
    # MEF normally exports plain integer/decimal strings.  Keep a guarded
    # Italian-format fallback for older datasets.
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    return float(text)


def choose_header(headers: list[str], *, kind: str) -> str:
    normalized = {header: norm(header) for header in headers}
    base = [h for h, n in normalized.items() if 'reddito complessivo' in n]
    if kind == 'amount':
        candidates = [h for h in base if any(token in normalized[h] for token in ('ammontare', 'importo'))]
    else:
        candidates = [h for h in base if any(token in normalized[h] for token in ('frequenza', 'numero'))]
    if len(candidates) != 1:
        raise RuntimeError(
            f'Impossibile individuare univocamente Reddito complessivo/{kind}: '
            f'{candidates}; tutte le colonne reddito complessivo={base}'
        )
    return candidates[0]


def choose_town_header(headers: list[str]) -> str:
    normalized = {header: norm(header) for header in headers}
    preferred = [
        h for h, n in normalized.items()
        if n in {'denominazione comune', 'denominazione del comune', 'comune'}
    ]
    if preferred:
        return preferred[0]
    candidates = [h for h, n in normalized.items() if 'comune' in n and 'codice' not in n]
    if len(candidates) == 1:
        return candidates[0]
    raise RuntimeError(f'Colonna Comune non individuata: {candidates}')


def choose_province_header(headers: list[str]) -> str | None:
    normalized = {header: norm(header) for header in headers}
    candidates = [h for h, n in normalized.items() if n in {'sigla provincia', 'provincia'}]
    return candidates[0] if candidates else None


def read_year(year: int) -> dict:
    url = URL.format(year=year)
    request = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-audit/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if len(members) != 1:
            raise RuntimeError(f'{year}: atteso un solo CSV/TXT nello ZIP, trovati {members}')
        member = members[0]
        text = decode(archive.read(member))

    sample = text[:10000]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=';,\t|').delimiter
    except csv.Error:
        delimiter = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    town_h = choose_town_header(headers)
    province_h = choose_province_header(headers)
    amount_h = choose_header(headers, kind='amount')
    freq_h = choose_header(headers, kind='frequency')

    wanted = {norm(town): town for town in TOWNS}
    found: dict[str, dict] = {}
    for row in reader:
        row_name = norm(row.get(town_h, ''))
        town = wanted.get(row_name)
        if not town:
            continue
        if province_h:
            province = norm(row.get(province_h, ''))
            if province not in {'lu', 'lucca'}:
                continue
        amount = number(row.get(amount_h, ''))
        frequency = int(round(number(row.get(freq_h, ''))))
        if frequency <= 0:
            raise RuntimeError(f'{year} {town}: frequenza non positiva')
        found[town] = {
            'amount': amount,
            'frequency': frequency,
            'average': round(amount / frequency, 2),
        }

    missing = [town for town in TOWNS if town not in found]
    if missing:
        raise RuntimeError(f'{year}: Comuni mancanti {missing}')
    return {
        'year': year,
        'url': url,
        'archiveMember': member,
        'delimiter': delimiter,
        'headers': {
            'town': town_h,
            'province': province_h,
            'amount': amount_h,
            'frequency': freq_h,
        },
        'towns': found,
    }


def current_income() -> dict[str, dict[int, float]]:
    data = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
    output: dict[str, dict[int, float]] = {}
    for row in data['metrics']['income']['rows']:
        years = [int(year) for year in row['series']['years']]
        output[row['town']] = {year: float(value) for year, value in zip(years, row['series']['values'])}
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=2011)
    parser.add_argument('--end', type=int, default=2024)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    years = [read_year(year) for year in range(args.start, args.end + 1)]
    current = current_income()
    towns = {}
    for town in TOWNS:
        values = {str(item['year']): item['towns'][town] for item in years}
        towns[town] = values

    checks = []
    for tax_year in (2023, 2024):
        if tax_year < args.start or tax_year > args.end:
            continue
        for town in TOWNS:
            extracted = towns[town][str(tax_year)]['average']
            existing = current.get(town, {}).get(tax_year)
            if existing is None:
                checks.append({'town': town, 'year': tax_year, 'status': 'no-current-value'})
                continue
            delta = round(extracted - existing, 2)
            checks.append({
                'town': town,
                'year': tax_year,
                'extracted': extracted,
                'current': existing,
                'delta': delta,
                'status': 'match' if abs(delta) <= 0.02 else 'mismatch',
            })

    snapshot = {
        'schemaVersion': 1,
        'source': 'Dipartimento delle Finanze - MEF',
        'definition': 'Reddito complessivo - Ammontare / Reddito complessivo - Frequenza',
        'taxYears': [item['year'] for item in years],
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
        'checksAgainstCurrentSite': checks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    mismatches = [check for check in checks if check.get('status') == 'mismatch']
    print(f'MEF income audit: {args.start}-{args.end}, {len(TOWNS)} comuni, {len(years)} annualità')
    for town in TOWNS:
        series = ', '.join(f"{year}:{towns[town][str(year)]['average']:.2f}" for year in range(args.start, args.end + 1))
        print(f'{town}: {series}')
    print('Schema columns:')
    for item in years:
        h = item['headers']
        print(f"{item['year']}: amount={h['amount']!r}; frequency={h['frequency']!r}")
    print(f'Checks 2023/2024: {len(checks) - len(mismatches)} ok, {len(mismatches)} mismatch')
    if mismatches:
        print(json.dumps(mismatches, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    print(f'Snapshot: {args.out}')


if __name__ == '__main__':
    main()
