#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict

TOWNS = [
    'Camaiore',
    'Forte dei Marmi',
    'Massarosa',
    'Pietrasanta',
    'Seravezza',
    'Stazzema',
    'Viareggio',
]

BASE = 'https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/1/rest/dataset/'
DATASETS = {
    'occupazione_turnover': [
        BASE + 'spd_pca_oct_dip_ente_01_2024.csv',
        BASE + 'spd_pca_oct_dip_ente_01_2024',
    ],
    'anzianita': [
        BASE + 'spd_pca_anz_dip_ente_01_2024.csv',
        BASE + 'spd_pca_anz_dip_ente_01_2024',
    ],
    'assunzioni_causale': [
        BASE + 'spd_pca_ass_dip_dett_01_2024.csv',
        BASE + 'spd_pca_ass_dip_dett_01_2024',
    ],
    'cessazioni_causale': [
        BASE + 'spd_pca_ces_dip_dett_01_2024.csv',
        BASE + 'spd_pca_ces_dip_dett_01_2024',
    ],
}


def norm(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[^A-Z0-9]+', ' ', text.upper()).strip()
    return text


def download(urls: list[str]) -> tuple[str, bytes]:
    errors = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia/1.0 data-audit'})
            with urllib.request.urlopen(req, timeout=90) as response:
                body = response.read()
                ctype = response.headers.get('Content-Type', '')
                if response.status != 200:
                    raise RuntimeError(f'HTTP {response.status}')
                if len(body) < 100:
                    raise RuntimeError(f'payload troppo piccolo ({len(body)} bytes)')
                if 'html' in ctype.lower() and body.lstrip().startswith(b'<'):
                    raise RuntimeError(f'risposta HTML inattesa: {ctype}')
                return url, body
        except Exception as exc:
            errors.append(f'{url}: {exc}')
    raise RuntimeError(' | '.join(errors))


def decode(body: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode('utf-8', errors='replace')


def parse_csv(body: bytes) -> tuple[list[str], list[dict[str, str]], str]:
    text = decode(body).replace('\x00', '')
    lines = text.splitlines()
    if lines and lines[0].upper().startswith('SEP='):
        forced = lines.pop(0)[4:5] or ';'
        text = '\n'.join(lines)
    else:
        forced = ''
    sample = text[:20000]
    delimiter = forced
    if not delimiter:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=';,|\t').delimiter
        except csv.Error:
            delimiter = ';' if sample.count(';') >= sample.count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = [dict(row) for row in reader]
    return list(reader.fieldnames or []), rows, delimiter


def numeric(value: str):
    raw = str(value or '').strip().replace('\u00a0', '').replace(' ', '')
    if not raw or raw.lower() in {'nd', 'n.d.', 'na', 'n.a.', '-', 'null'}:
        return None
    if re.fullmatch(r'-?\d{1,3}(?:\.\d{3})+(?:,\d+)?', raw):
        raw = raw.replace('.', '').replace(',', '.')
    elif ',' in raw and '.' not in raw:
        raw = raw.replace(',', '.')
    try:
        return float(raw)
    except ValueError:
        return None


def find_entity_field(headers: list[str]) -> str | None:
    candidates = []
    for header in headers:
        n = norm(header)
        score = 0
        if 'DESCRIZIONE ENTE' in n or 'DENOMINAZIONE ENTE' in n:
            score = 100
        elif n == 'ENTE' or n == 'ISTITUZIONE':
            score = 90
        elif 'DESCRIZIONE ISTITUZIONE' in n:
            score = 80
        elif 'ENTE' in n and ('DESCR' in n or 'DENOM' in n):
            score = 70
        if score:
            candidates.append((score, header))
    return max(candidates, default=(0, None))[1]


def match_town(entity: str) -> str | None:
    e = norm(entity)
    for town in TOWNS:
        t = norm(town)
        if e == t or e == f'COMUNE DI {t}' or e == f'COMUNE {t}' or f'COMUNE DI {t}' in e:
            return town
    return None


def summarise(headers: list[str], rows: list[dict[str, str]]) -> dict:
    entity_field = find_entity_field(headers)
    by_town: dict[str, list[dict[str, str]]] = {town: [] for town in TOWNS}
    if entity_field:
        for row in rows:
            town = match_town(row.get(entity_field, ''))
            if town:
                by_town[town].append(row)

    result = {
        'headers': headers,
        'entityField': entity_field,
        'rowCount': len(rows),
        'coverage': [town for town, matched in by_town.items() if matched],
        'towns': {},
    }

    for town, matched in by_town.items():
        numeric_sums: dict[str, float] = defaultdict(float)
        numeric_nonempty: dict[str, int] = defaultdict(int)
        categorical: dict[str, set[str]] = defaultdict(set)
        for row in matched:
            for header in headers:
                value = row.get(header, '')
                number = numeric(value)
                header_norm = norm(header)
                if number is not None and any(token in header_norm for token in ('NUMERO', 'TOTALE', 'DIPENDENT', 'ASSUNT', 'CESSAT', 'GIORN', 'VALORE')):
                    numeric_sums[header] += number
                    numeric_nonempty[header] += 1
                elif value and any(token in header_norm for token in ('CAUSALE', 'FASCIA', 'ETA', 'CATEGORIA', 'MACROCATEGORIA', 'CONTRATTO')):
                    if len(categorical[header]) < 40:
                        categorical[header].add(str(value).strip())
        result['towns'][town] = {
            'rowCount': len(matched),
            'numericSums': {key: round(value, 6) for key, value in numeric_sums.items()},
            'numericCounts': dict(numeric_nonempty),
            'categories': {key: sorted(values) for key, values in categorical.items()},
            'sampleRows': matched[:3],
        }
    return result


def main() -> int:
    report = {
        'schemaVersion': 1,
        'referenceYear': 2024,
        'source': 'RGS OpenBDAP - Conto Annuale',
        'expectedTowns': TOWNS,
        'datasets': {},
    }
    failures = []
    for key, urls in DATASETS.items():
        try:
            resolved, body = download(urls)
            headers, rows, delimiter = parse_csv(body)
            summary = summarise(headers, rows)
            summary.update({'url': resolved, 'bytes': len(body), 'delimiter': delimiter})
            report['datasets'][key] = summary
            if len(summary['coverage']) != len(TOWNS):
                failures.append(f'{key}: copertura {len(summary["coverage"])}/7')
        except Exception as exc:
            report['datasets'][key] = {'error': str(exc), 'coverage': []}
            failures.append(f'{key}: {exc}')

    print('RGS_ADMIN_AUDIT_BEGIN')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('RGS_ADMIN_AUDIT_END')

    if failures:
        print('AUDIT FAIL:', ' || '.join(failures), file=sys.stderr)
        return 1
    print('Audit RGS completato: copertura grezza 7/7 su tutti i dataset.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
