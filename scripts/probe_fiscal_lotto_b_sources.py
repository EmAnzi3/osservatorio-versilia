#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

import requests
from pypdf import PdfReader

TOWNS = [
    'Massarosa', 'Viareggio', 'Camaiore', 'Pietrasanta',
    'Seravezza', 'Forte dei Marmi', 'Stazzema',
]

BDAP_DATASET = 'spd_rnd_ent_sio_reg09_01_2025'
BDAP_BASE = 'https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi'
DAIT_PDF = 'https://dait.interno.gov.it/documenti/com-fl-03-12-2025-all.pdf'
OUT = Path('reports/fiscal-lotto-b-probe.json')


def get(url: str) -> requests.Response:
    response = requests.get(
        url,
        timeout=120,
        headers={'User-Agent': 'OsservatorioVersilia/1.0 (+https://osservatorioversilia.it)'},
    )
    response.raise_for_status()
    return response


def decode_csv(content: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError('Codifica CSV OpenBDAP non riconosciuta')


def bdap_probe() -> dict:
    candidates = [
        f'{BDAP_BASE}/api/1/rest/dataset/{BDAP_DATASET}',
        f'{BDAP_BASE}/api/2/rest/dataset/{BDAP_DATASET}',
        f'{BDAP_BASE}/api/3/action/package_show?id={BDAP_DATASET}',
    ]
    attempts = []
    payload = None
    source_url = None
    for url in candidates:
        try:
            response = get(url)
            data = response.json()
            attempts.append({'url': url, 'status': response.status_code, 'ok': True})
            if isinstance(data, dict) and data.get('success') is True and isinstance(data.get('result'), dict):
                data = data['result']
            if isinstance(data, dict):
                payload = data
                source_url = url
                break
        except Exception as exc:  # pragma: no cover - live probe
            attempts.append({'url': url, 'ok': False, 'error': str(exc)})

    if payload is None:
        raise RuntimeError(f'OpenBDAP dataset metadata non raggiungibile: {attempts}')

    resources = payload.get('resources') or payload.get('resource') or []
    compact_resources = []
    csv_url = None
    for item in resources:
        if not isinstance(item, dict):
            continue
        compact_resources.append({
            key: item.get(key)
            for key in ('id', 'name', 'format', 'url', 'download_url', 'resource_type')
            if item.get(key) is not None
        })
        fmt = str(item.get('format') or '').lower()
        url = item.get('url') or item.get('download_url')
        if fmt == 'csv' and url and str(url).lower().endswith('.csv'):
            csv_url = str(url).replace('http://', 'https://', 1)

    if not csv_url:
        raise RuntimeError(f'Risorsa CSV OpenBDAP non individuata: {compact_resources}')

    csv_response = get(csv_url)
    text = decode_csv(csv_response.content)
    sample = text[:65536]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=';,\t|')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ';'
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []

    matching = {town: [] for town in TOWNS}
    for row in reader:
        flat = ' | '.join(str(value or '') for value in row.values())
        if 'verifica e controllo' not in flat.casefold():
            continue
        for town in TOWNS:
            if f'comune di {town}'.casefold() not in flat.casefold() and town.casefold() not in flat.casefold():
                continue
            compact = {
                key: value for key, value in row.items()
                if value not in (None, '') and (
                    key in {
                        'Descrizione Ente BDAP', 'Codice Ente BDAP', 'Anno/Mese calendario',
                        'Codice Gestionale Enti Locali', 'Descrizione CG', 'Importo cumulato',
                        'Popolazione ISTAT', 'Codice Titolo CG', 'Descrizione Titolo CG',
                    }
                    or 'Ente' in key or 'Gestionale' in key or 'Descrizione CG' in key
                    or 'Anno/Mese' in key or 'Importo' in key
                )
            }
            matching[town].append(compact)
            break

    return {
        'dataset': BDAP_DATASET,
        'metadataEndpoint': source_url,
        'attempts': attempts,
        'keys': sorted(payload.keys()),
        'title': payload.get('title') or payload.get('name'),
        'resources': compact_resources,
        'csvUrl': csv_url,
        'csvBytes': len(csv_response.content),
        'delimiter': delimiter,
        'headers': headers,
        'verificationControlRows': matching,
    }


def dait_probe() -> dict:
    response = get(DAIT_PDF)
    reader = PdfReader(io.BytesIO(response.content))
    page_texts = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(page_texts)
    normalized = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    hits = {}
    for town in TOWNS:
        town_hits = []
        needle = town.casefold()
        for idx, line in enumerate(lines):
            if needle in line.casefold():
                town_hits.append({
                    'line': line,
                    'context': lines[max(0, idx - 2): min(len(lines), idx + 3)],
                })
        hits[town] = town_hits
    return {
        'url': DAIT_PDF,
        'bytes': len(response.content),
        'pages': len(reader.pages),
        'firstPageLines': [
            line.strip() for line in re.sub(r'[ \t]+', ' ', page_texts[0]).splitlines() if line.strip()
        ][:80],
        'townHits': hits,
    }


def main() -> None:
    result = {'bdap': bdap_probe(), 'dait': dait_probe()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
