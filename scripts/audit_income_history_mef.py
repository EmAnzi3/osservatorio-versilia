#!/usr/bin/env python3
"""Extract and audit municipal MEF average income, tax years 2011-2024."""
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
URL = (
    'https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/'
    'Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_{year}.zip'
)
TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
MISSING = {'', '-', 'n.d.', 'nd'}


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(ch for ch in value if not unicodedata.combining(ch)).lower().strip()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def stem(header: str) -> str:
    # Older MEF files append "in euro" only to amount columns.
    return re.sub(
        r' (ammontare(?: in euro)?|importo(?: in euro)?|frequenza|numero)$',
        '', norm(header),
    )


def decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise RuntimeError('encoding CSV MEF non riconosciuto')


def clean(value: str) -> str:
    return (value or '').strip().replace('\u00a0', '').replace(' ', '').lower()


def number(value: str) -> float:
    text = clean(value)
    if text in MISSING:
        raise ValueError(f'valore mancante {value!r}')
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    return float(text)


def paired_class_value(amount_raw: str, frequency_raw: str, *, year: int, town: str, label: str) -> tuple[float, int]:
    amount_missing = clean(amount_raw) in MISSING
    frequency_missing = clean(frequency_raw) in MISSING
    if amount_missing and frequency_missing:
        return 0.0, 0
    if amount_missing != frequency_missing:
        raise RuntimeError(f'{year} {town} {label}: coppia incompleta {amount_raw!r}/{frequency_raw!r}')
    amount = number(amount_raw)
    frequency = int(round(number(frequency_raw)))
    # The official <=0 income class can legitimately have a negative amount.
    if frequency < 0:
        raise RuntimeError(f'{year} {town} {label}: frequenza negativa')
    return amount, frequency


def town_header(headers: list[str]) -> str:
    normalized = {h: norm(h) for h in headers}
    exact = [h for h, n in normalized.items() if n in {'denominazione comune', 'denominazione del comune', 'comune'}]
    if exact:
        return exact[0]
    candidates = [h for h, n in normalized.items() if 'comune' in n and 'codice' not in n]
    if len(candidates) != 1:
        raise RuntimeError(f'colonna comune ambigua: {candidates}')
    return candidates[0]


def province_header(headers: list[str]) -> str | None:
    normalized = {h: norm(h) for h in headers}
    candidates = [h for h, n in normalized.items() if n in {'sigla provincia', 'provincia'}]
    return candidates[0] if candidates else None


def income_columns(headers: list[str]) -> tuple[str | None, str | None, list[str], list[str]]:
    normalized = {h: norm(h) for h in headers}
    direct_amount_names = {
        'reddito complessivo ammontare', 'reddito complessivo ammontare in euro',
        'reddito complessivo importo', 'reddito complessivo importo in euro',
    }
    direct_amount = [h for h, n in normalized.items() if n in direct_amount_names]
    direct_frequency = [h for h, n in normalized.items() if n in {'reddito complessivo frequenza', 'reddito complessivo numero'}]
    class_amount = [
        h for h, n in normalized.items()
        if n.startswith('reddito complessivo ') and (' ammontare' in n or ' importo' in n) and h not in direct_amount
    ]
    class_frequency = [
        h for h, n in normalized.items()
        if n.startswith('reddito complessivo ') and (' frequenza' in n or ' numero' in n) and h not in direct_frequency
    ]
    if len(direct_amount) > 1 or len(direct_frequency) > 1:
        raise RuntimeError('totale reddito complessivo ambiguo')
    if bool(direct_amount) != bool(direct_frequency):
        raise RuntimeError('totale reddito complessivo incompleto')
    if not (direct_amount and direct_frequency) and not (class_amount and class_frequency):
        raise RuntimeError('reddito complessivo non ricostruibile')
    if class_amount or class_frequency:
        amount_stems = {stem(h) for h in class_amount}
        frequency_stems = {stem(h) for h in class_frequency}
        if amount_stems != frequency_stems:
            raise RuntimeError(
                f'classi non allineate; solo ammontare={sorted(amount_stems-frequency_stems)}; '
                f'solo frequenza={sorted(frequency_stems-amount_stems)}'
            )
    return (
        direct_amount[0] if direct_amount else None,
        direct_frequency[0] if direct_frequency else None,
        class_amount,
        class_frequency,
    )


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
    town_h = town_header(headers)
    province_h = province_header(headers)
    try:
        direct_amount_h, direct_frequency_h, class_amount_h, class_frequency_h = income_columns(headers)
    except Exception as exc:
        income_headers = [h for h in headers if 'reddito complessivo' in norm(h)]
        raise RuntimeError(f'{year}: {exc}; colonne={income_headers}') from exc

    frequency_by_stem = {stem(h): h for h in class_frequency_h}
    wanted = {norm(town): town for town in TOWNS}
    found: dict[str, dict] = {}
    equivalence_checks = []
    for row in reader:
        town = wanted.get(norm(row.get(town_h, '')))
        if not town:
            continue
        if province_h and norm(row.get(province_h, '')) not in {'lu', 'lucca'}:
            continue
        class_amount = class_frequency = None
        if class_amount_h:
            class_amount = 0.0
            class_frequency = 0
            for amount_h in class_amount_h:
                label = stem(amount_h)
                amount_part, frequency_part = paired_class_value(
                    row.get(amount_h, ''), row.get(frequency_by_stem[label], ''),
                    year=year, town=town, label=label,
                )
                class_amount += amount_part
                class_frequency += frequency_part
        if direct_amount_h and direct_frequency_h:
            amount = number(row.get(direct_amount_h, ''))
            frequency = int(round(number(row.get(direct_frequency_h, ''))))
            method = 'direct-total'
            if class_amount_h:
                amount_delta = round(amount - class_amount, 6)
                frequency_delta = frequency - class_frequency
                equivalence_checks.append({'town': town, 'amountDelta': amount_delta, 'frequencyDelta': frequency_delta})
                if abs(amount_delta) > 0.01 or frequency_delta != 0:
                    raise RuntimeError(f'{year} {town}: totale != somma classi ({amount_delta}; {frequency_delta})')
        else:
            amount = class_amount
            frequency = class_frequency
            method = 'sum-income-classes'
        if amount is None or not frequency or frequency <= 0:
            raise RuntimeError(f'{year} {town}: totale non valido')
        found[town] = {'amount': amount, 'frequency': frequency, 'average': round(amount / frequency, 2)}
    missing = [town for town in TOWNS if town not in found]
    if missing:
        raise RuntimeError(f'{year}: comuni mancanti {missing}')
    return {
        'year': year, 'url': url, 'archiveMember': member, 'delimiter': delimiter,
        'method': 'direct-total' if direct_amount_h else 'sum-income-classes',
        'headers': {
            'town': town_h, 'province': province_h,
            'directAmount': direct_amount_h, 'directFrequency': direct_frequency_h,
            'classAmounts': class_amount_h, 'classFrequencies': class_frequency_h,
        },
        'equivalenceChecks': equivalence_checks, 'towns': found,
    }


def current_income() -> dict[str, dict[int, float]]:
    data = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
    output = {}
    for row in data['metrics']['income']['rows']:
        output[row['town']] = {int(y): float(v) for y, v in zip(row['series']['years'], row['series']['values'])}
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=2011)
    parser.add_argument('--end', type=int, default=2024)
    parser.add_argument('--out', type=Path, default=Path('/tmp/mef-income-history.json'))
    args = parser.parse_args()
    years = [read_year(year) for year in range(args.start, args.end + 1)]
    current = current_income()
    towns = {town: {str(item['year']): item['towns'][town] for item in years} for town in TOWNS}
    checks = []
    for year in (2023, 2024):
        if args.start <= year <= args.end:
            for town in TOWNS:
                extracted = towns[town][str(year)]['average']
                existing = current.get(town, {}).get(year)
                delta = None if existing is None else round(extracted - existing, 2)
                status = 'no-current-value' if existing is None else ('match' if abs(delta) <= 0.02 else 'mismatch')
                checks.append({'town': town, 'year': year, 'extracted': extracted, 'current': existing, 'delta': delta, 'status': status})
    snapshot = {
        'schemaVersion': 7,
        'source': 'Dipartimento delle Finanze - MEF',
        'definition': 'Reddito complessivo - Ammontare / Reddito complessivo - Frequenza',
        'taxYears': [item['year'] for item in years],
        'schemaByYear': {
            str(item['year']): {key: item[key] for key in ('url', 'archiveMember', 'delimiter', 'method', 'headers', 'equivalenceChecks')}
            for item in years
        },
        'towns': towns,
        'checksAgainstCurrentSite': checks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    mismatches = [check for check in checks if check['status'] == 'mismatch']
    methods = ', '.join(f"{item['year']}={item['method']}" for item in years)
    print(f'MEF income audit: {args.start}-{args.end}; {methods}')
    for town in TOWNS:
        values = ', '.join(f"{year}:{towns[town][str(year)]['average']:.2f}" for year in range(args.start, args.end + 1))
        print(f'{town}: {values}')
    print(f'Checks existing 2023/2024: {len(checks)-len(mismatches)} ok, {len(mismatches)} mismatch; snapshot={args.out}')
    if mismatches:
        print(json.dumps(mismatches, ensure_ascii=False, indent=2))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
