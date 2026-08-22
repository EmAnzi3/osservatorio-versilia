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

TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
URLS = {
    'turnover': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34887/csv/5458/77e11303-b0f6-460a-b6b3-85e350300fac@rgs',
    'age': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34886/csv/5457/19df264e-df7a-4488-85e8-123cbfb03ac1@rgs',
    'hires': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34885/csv/5456/faf4a5f8-69cc-47b1-a0ce-91cb41f5a027@rgs',
    'cessations': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34891/csv/5460/6a1de16e-ebd6-43f8-a813-f59d84d7b3b1@rgs',
}


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', str(value or ''))
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r'[^A-Z0-9]+', ' ', value.upper()).strip()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        if response.status != 200 or len(body) < 100:
            raise RuntimeError(f'HTTP {response.status}, {len(body)} bytes')
        return body


def table(body: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = None
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            text = body.decode(enc)
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise RuntimeError('encoding CSV non riconosciuto')
    text = text.replace('\x00', '')
    first = text.splitlines()[0] if text.splitlines() else ''
    if first.upper().startswith('SEP='):
        delim = first[4:5]
        text = '\n'.join(text.splitlines()[1:])
    else:
        sample = text[:30000]
        try:
            delim = csv.Sniffer().sniff(sample, delimiters=';,|\t').delimiter
        except csv.Error:
            delim = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    return list(reader.fieldnames or []), [dict(row) for row in reader]


def num(value) -> float:
    raw = str(value or '').strip().replace('\u00a0', '').replace(' ', '')
    if not raw:
        return 0.0
    if ',' in raw and '.' not in raw:
        raw = raw.replace(',', '.')
    try:
        return float(raw)
    except ValueError:
        return 0.0


def town_for(value: str):
    n = norm(value)
    for town in TOWNS:
        t = norm(town)
        if n in {t, f'COMUNE DI {t}', f'COMUNE {t}'} or f'COMUNE DI {t}' in n:
            return town
    return None


def field(headers, *tokens):
    for h in headers:
        n = norm(h)
        if all(token in n for token in tokens):
            return h
    return None


def municipality_rows(headers, rows):
    entity = field(headers, 'DESCRIZIONE', 'ENTE')
    inst = field(headers, 'DESCRIZIONE', 'TIPO', 'ISTITUZIONE')
    if not entity:
        raise RuntimeError(f'campo ente non trovato: {headers}')
    out = {town: [] for town in TOWNS}
    for row in rows:
        if inst and norm(row.get(inst, '')) != 'COMUNI':
            continue
        town = town_for(row.get(entity, ''))
        if town:
            out[town].append(row)
    return out


def summarize_turnover(headers, rows):
    by = municipality_rows(headers, rows)
    staff_fields = [h for h in headers if norm(h).startswith('NUMERO DIPENDENTI') and any(x in norm(h) for x in ('TEMPO PIENO', 'PART TIME'))]
    hire_fields = [h for h in headers if 'ASSUNT' in norm(h) and norm(h).startswith('NUMERO DIPENDENTI')]
    cess_fields = [h for h in headers if 'CESSAT' in norm(h) and norm(h).startswith('NUMERO DIPENDENTI')]
    return {town: {
        'rows': len(items),
        'employees': round(sum(num(r.get(h)) for r in items for h in staff_fields), 4),
        'hiresTotal': round(sum(num(r.get(h)) for r in items for h in hire_fields), 4),
        'cessationsTotal': round(sum(num(r.get(h)) for r in items for h in cess_fields), 4),
    } for town, items in by.items()}


def summarize_age(headers, rows):
    by = municipality_rows(headers, rows)
    age = field(headers, 'DESCRIZIONE', 'FASCIA', 'ETA')
    women = field(headers, 'NUMERO', 'DIPENDENTI', 'DONNE')
    men = field(headers, 'NUMERO', 'DIPENDENTI', 'UOMINI')
    if not all((age, women, men)):
        raise RuntimeError('campi età non trovati')
    result = {}
    for town, items in by.items():
        bands = defaultdict(float)
        for r in items:
            bands[str(r.get(age, '')).strip()] += num(r.get(women)) + num(r.get(men))
        result[town] = {'rows': len(items), 'bands': {k: round(v, 4) for k, v in sorted(bands.items())}, 'employees': round(sum(bands.values()), 4)}
    return result


def summarize_flows(headers, rows, direction):
    by = municipality_rows(headers, rows)
    cause = field(headers, 'DESCRIZIONE', 'CAUSALE')
    women = field(headers, 'DONNE')
    men = field(headers, 'UOMINI')
    if not all((cause, women, men)):
        raise RuntimeError(f'campi {direction} non trovati')
    result = {}
    for town, items in by.items():
        causes = defaultdict(float)
        for r in items:
            causes[str(r.get(cause, '')).strip()] += num(r.get(women)) + num(r.get(men))
        transfers = sum(value for label, value in causes.items() if 'PASSAGGI' in norm(label) and 'ALTRA AMMINISTRAZIONE' in norm(label))
        total = sum(causes.values())
        result[town] = {
            'rows': len(items),
            'total': round(total, 4),
            'transfers': round(transfers, 4),
            'netOfTransfers': round(total - transfers, 4),
            'causes': {k: round(v, 4) for k, v in sorted(causes.items()) if v != 0},
        }
    return result


def main():
    loaded = {}
    meta = {}
    for key, url in URLS.items():
        body = fetch(url)
        headers, rows = table(body)
        loaded[key] = (headers, rows)
        meta[key] = {'url': url, 'bytes': len(body), 'rows': len(rows), 'headers': headers}

    summary = {
        'schemaVersion': 2,
        'referenceYear': 2024,
        'source': 'RGS OpenBDAP / Conto Annuale',
        'meta': meta,
        'turnover': summarize_turnover(*loaded['turnover']),
        'age': summarize_age(*loaded['age']),
        'hires': summarize_flows(*loaded['hires'], 'hires'),
        'cessations': summarize_flows(*loaded['cessations'], 'cessations'),
    }
    for dataset in ('turnover', 'age', 'hires', 'cessations'):
        missing = [town for town in TOWNS if not summary[dataset][town]['rows']]
        if missing:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            raise SystemExit(f'{dataset}: copertura incompleta, mancano {missing}')
    for town in TOWNS:
        emp_a = summary['turnover'][town]['employees']
        emp_b = summary['age'][town]['employees']
        if abs(emp_a - emp_b) > 0.01:
            print(f'WARN {town}: personale turnover={emp_a}, età={emp_b}', file=sys.stderr)
        hires = summary['hires'][town]['netOfTransfers']
        cess = summary['cessations'][town]['netOfTransfers']
        summary['turnover'][town]['hiresNetTransfers'] = hires
        summary['turnover'][town]['cessationsNetTransfers'] = cess
        summary['turnover'][town]['turnoverNetRatePct'] = round((hires - cess) / emp_a * 100, 4) if emp_a else None
    print('RGS_ADMIN_AUDIT_V2_BEGIN')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('RGS_ADMIN_AUDIT_V2_END')
    print('Audit RGS 2024: copertura 7/7 certificata sui quattro dataset OpenBDAP.')


if __name__ == '__main__':
    main()
