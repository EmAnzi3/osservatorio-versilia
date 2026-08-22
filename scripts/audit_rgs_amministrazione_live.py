#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import http.cookiejar
import io
import json
import re
import unicodedata
import urllib.parse
import urllib.request

TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
PAGES = {
    'turnover': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34887/csv/5458/77e11303-b0f6-460a-b6b3-85e350300fac@rgs',
    'age': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34886/csv/5457/19df264e-df7a-4488-85e8-123cbfb03ac1@rgs',
    'hires': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34885/csv/5456/faf4a5f8-69cc-47b1-a0ce-91cb41f5a027@rgs',
    'cessations': 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34891/csv/5460/6a1de16e-ebd6-43f8-a813-f59d84d7b3b1@rgs',
}
UA = 'Mozilla/5.0 (compatible; OsservatorioVersilia/1.0; +https://osservatorioversilia.it)'


def norm(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r'[^A-Z0-9]+', ' ', text.upper()).strip()


def opener():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(op, url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with op.open(req, timeout=90) as response:
        return response.read(), dict(response.headers)


def form_fields(page: str) -> dict[str, str]:
    block_match = re.search(r'(<form[^>]+id="metadata-download-form".*?</form>)', page, re.I | re.S)
    if not block_match:
        raise RuntimeError('metadata-download-form non trovato')
    block = block_match.group(1)
    fields: dict[str, str] = {}
    for tag in re.findall(r'<input\b[^>]*>', block, re.I):
        name_m = re.search(r'name=["\']([^"\']+)["\']', tag, re.I)
        if not name_m:
            continue
        name = html.unescape(name_m.group(1))
        value_m = re.search(r'value=["\']([^"\']*)["\']', tag, re.I)
        value = html.unescape(value_m.group(1)) if value_m else ''
        typ_m = re.search(r'type=["\']([^"\']+)["\']', tag, re.I)
        typ = typ_m.group(1).lower() if typ_m else ''
        if typ in {'hidden', 'text'}:
            fields[name] = value
    fields['export_type'] = 'csv'
    fields['op'] = 'Scarica'
    fields.setdefault('mail', '')
    return fields


def export_csv(page_url: str) -> tuple[str, bytes, dict]:
    op = opener()
    page_body, _ = get(op, page_url)
    page = page_body.decode('utf-8', errors='replace')
    payload = urllib.parse.urlencode(form_fields(page)).encode('utf-8')
    request = urllib.request.Request(
        page_url,
        data=payload,
        headers={
            'User-Agent': UA,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': page_url,
            'X-Requested-With': 'XMLHttpRequest',
        },
    )
    with op.open(request, timeout=90) as response:
        result_body = response.read()
    result = json.loads(result_body.decode('utf-8'))
    export_url = str(result.get('URL') or result.get('url') or '')
    if not export_url:
        raise RuntimeError(f'URL export assente nella risposta: {result}')
    csv_body, csv_headers = get(op, export_url)
    if csv_body.lstrip().startswith(b'<'):
        raise RuntimeError(f'export CSV ha restituito HTML: {export_url}')
    return export_url, csv_body, csv_headers


def decode_csv(body: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode('utf-8', errors='replace')


def parse_csv(body: bytes) -> tuple[list[str], list[dict[str, str]], str]:
    text = decode_csv(body).replace('\x00', '')
    lines = text.splitlines()
    forced = None
    if lines and lines[0].upper().startswith('SEP='):
        forced = lines.pop(0)[4:5] or ';'
        text = '\n'.join(lines)
    sample = text[:50000]
    if forced:
        delim = forced
    else:
        try:
            delim = csv.Sniffer().sniff(sample, delimiters=';,|\t').delimiter
        except csv.Error:
            delim = ';' if sample.count(';') >= sample.count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rows = [dict(row) for row in reader]
    return list(reader.fieldnames or []), rows, delim


def town_match(row: dict[str, str], town: str) -> bool:
    needle = norm(f'COMUNE DI {town}')
    simple = norm(town)
    for key, value in row.items():
        k = norm(key)
        if 'ENTE' not in k and 'ISTITUZ' not in k and 'AMMINISTRAZ' not in k:
            continue
        v = norm(value)
        if v in {needle, simple, norm(f'COMUNE {town}')}:
            return True
    return False


def compact_row(row: dict[str, str]) -> dict[str, str]:
    keep = {}
    for key, value in row.items():
        if value is None or str(value).strip() == '':
            continue
        keep[key] = str(value).strip()
    return keep


def main():
    report = {'schemaVersion': 1, 'referenceYear': 2024, 'source': 'RGS OpenBDAP / Conto Annuale', 'datasets': {}}
    for name, page_url in PAGES.items():
        export_url, body, response_headers = export_csv(page_url)
        headers, rows, delim = parse_csv(body)
        towns = {}
        for town in TOWNS:
            matched = [row for row in rows if town_match(row, town)]
            towns[town] = {
                'rowCount': len(matched),
                'sample': compact_row(matched[0]) if matched else None,
            }
        report['datasets'][name] = {
            'pageUrl': page_url,
            'exportUrl': export_url,
            'bytes': len(body),
            'contentType': response_headers.get('Content-Type', ''),
            'delimiter': delim,
            'headers': headers,
            'totalRows': len(rows),
            'towns': towns,
        }
        missing = [town for town, item in towns.items() if item['rowCount'] == 0]
        if missing:
            raise RuntimeError(f'{name}: copertura incompleta, mancano {missing}')
    print('RGS_ADMIN_LIVE_AUDIT_BEGIN')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('RGS_ADMIN_LIVE_AUDIT_END')
    print('RGS OpenBDAP 2024: record comunali trovati 7/7 nei quattro dataset.')


if __name__ == '__main__':
    main()
