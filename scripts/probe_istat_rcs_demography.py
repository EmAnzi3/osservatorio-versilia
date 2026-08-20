#!/usr/bin/env python3
"""Probe strutturale dei download Istat RCS 2025 (cittadinanza / paese di nascita).

Non materializza dati nel catalogo: salva soltanto schema, parsing e righe campione
per i sette Comuni dell'Osservatorio, così da chiudere la tranche senza assumere
nomi di colonna o convenzioni non verificate.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'audit-artifacts' / 'istat-rcs-demography-2025.json'

TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
SOURCES = {
    'citizenship': 'https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip',
    'birthCountry': 'https://demo.istat.it/data/rcs/Dati_RCS_nascita_2025.zip',
}


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-probe/1.0'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def decode(raw: bytes) -> tuple[str, str]:
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError('Codifica RCS non riconosciuta')


def parse_archive(url: str) -> dict:
    body = download(url)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if not members:
            raise RuntimeError(f'Nessun CSV/TXT in {url}')
        member = max(members, key=lambda name: archive.getinfo(name).file_size)
        text, encoding = decode(archive.read(member))

    first = next((line for line in text.splitlines() if line.strip()), '')
    delimiter = ';' if first.count(';') >= first.count(',') else ','
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if len(rows) < 2:
        raise RuntimeError(f'RCS troppo corto: {url}')

    # Alcuni download Demo hanno una riga titolo prima dell'header: scegliamo la
    # prima riga con almeno 4 celle e un contenuto riconducibile a Comune/Territorio.
    header_index = None
    for idx, row in enumerate(rows[:12]):
        joined = ' '.join(cell.strip().lower() for cell in row)
        if len(row) >= 4 and any(token in joined for token in ('comune', 'territorio', 'cittadin', 'nascita')):
            header_index = idx
            break
    if header_index is None:
        header_index = 0

    header = [cell.strip() for cell in rows[header_index]]
    data_rows = rows[header_index + 1:]
    width = len(header)
    normalized = []
    town_samples = {town: [] for town in TOWNS}

    for raw_row in data_rows:
        if not any(str(cell).strip() for cell in raw_row):
            continue
        padded = (raw_row + [''] * width)[:width]
        record = dict(zip(header, padded, strict=False))
        normalized.append(record)
        searchable = ' | '.join(str(value) for value in padded).lower()
        for town in TOWNS:
            if town.lower() in searchable and len(town_samples[town]) < 5:
                town_samples[town].append(record)

    return {
        'url': url,
        'archiveBytes': len(body),
        'archiveMember': member,
        'encoding': encoding,
        'delimiter': delimiter,
        'headerIndex': header_index,
        'headerCount': len(header),
        'headers': header,
        'rowCount': len(normalized),
        'townSampleCounts': {town: len(items) for town, items in town_samples.items()},
        'townSamples': town_samples,
        'firstRows': normalized[:5],
    }


def main() -> None:
    payload = {
        'schemaVersion': 1,
        'generatedAt': '2026-08-20',
        'publisher': 'Istat',
        'dataset': 'RCS — popolazione residente per cittadinanza o paese di nascita',
        'sources': {key: parse_archive(url) for key, url in SOURCES.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        key: {
            'headers': value['headers'],
            'rowCount': value['rowCount'],
            'townSampleCounts': value['townSampleCounts'],
        }
        for key, value in payload['sources'].items()
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
