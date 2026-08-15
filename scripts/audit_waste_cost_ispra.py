#!/usr/bin/env python3
"""Audit ISPRA 2024 municipal CTOTab waste-service costs for Versilia."""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = 'https://www.catasto-rifiuti.isprambiente.it/index.php'
TOWNS = {
    'Camaiore': '09046005',
    'Forte dei Marmi': '09046013',
    'Massarosa': '09046018',
    'Pietrasanta': '09046024',
    'Seravezza': '09046028',
    'Stazzema': '09046030',
    'Viareggio': '09046033',
}
UA = {'User-Agent': 'OsservatorioVersilia-data-audit/1.0'}


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(ch for ch in value if not unicodedata.combining(ch)).lower().strip()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def parse_number(value: str) -> float | None:
    text = html.unescape(value or '').strip().replace('\xa0', '').replace(' ', '')
    if not text or text in {'-', 'n.d.', 'nd'}:
        return None
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return None


class Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'table':
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in {'td', 'th'} and self.row is not None:
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append(' ')

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {'td', 'th'} and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r'\s+', ' ', ''.join(self.cell)).strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None and self.table is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            if self.table:
                self.tables.append(self.table)
            self.table = None


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode('utf-8', errors='replace')


def source_url(town: str, code: str) -> str:
    params = {
        'comune': code,
        'comuned': town,
        'nomeprov': 'Lucca',
        'p': '1',
        'pg': 'detcosticomuneproc',
        'prov': '046',
        'reg1': 'Toscana',
        'regid2': '09',
    }
    return BASE + '?' + urllib.parse.urlencode(params)


def extract_2024(town: str, text: str) -> dict:
    parser = Tables()
    parser.feed(text)
    diagnostic_rows = []
    for table in parser.tables:
        normalized_rows = [[norm(cell) for cell in row] for row in table]
        if not any('ctotab' in cell for row in normalized_rows for cell in row):
            continue
        for row in table:
            if len(row) < 5:
                continue
            if norm(row[0]) == norm(town) and row[1].strip() == '2024':
                municipality_count = int(round(parse_number(row[2]) or 0))
                if municipality_count != 1:
                    raise RuntimeError(f'{town}: riga 2024 non comunale, numero comuni={municipality_count}')
                ctot = parse_number(row[-1])
                if ctot is None or not 20 <= ctot <= 1000:
                    raise RuntimeError(f'{town}: CTOTab 2024 non valido nella riga {row}')
                population = parse_number(row[3])
                return {
                    'ctotPerResident': round(ctot, 2),
                    'population': int(round(population)) if population is not None else None,
                    'municipalityCount': municipality_count,
                    'rawRow': row,
                }
            if row and ('2024' in row or norm(town) in norm(row[0])):
                diagnostic_rows.append(row)
    raise RuntimeError(f'{town}: riga comunale CTOTab 2024 non trovata; contesto={diagnostic_rows[:8]}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('/tmp/ispra-waste-cost.json'))
    args = parser.parse_args()
    towns = {}
    for town, code in TOWNS.items():
        url = source_url(town, code)
        result = extract_2024(town, fetch(url))
        result['sourceUrl'] = url
        towns[town] = result
        print(f"{town}: CTOTab={result['ctotPerResident']:.2f} €/ab · nComuni={result['municipalityCount']}")
    snapshot = {
        'schemaVersion': 2,
        'year': 2024,
        'source': 'ISPRA - Catasto Nazionale Rifiuti',
        'definition': 'CTOTab - costi totali di gestione del servizio di igiene urbana, euro/abitante/anno',
        'coverage': f'{len(towns)}/7',
        'towns': towns,
        'note': 'Sono ammesse solo righe riferite al singolo Comune (Numero di comuni = 1); nessuna aggregazione viene attribuita al Comune.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if len(towns) != 7:
        raise SystemExit(2)
    print(f'ISPRA CTOTab audit OK: {len(towns)}/7; snapshot={args.out}')


if __name__ == '__main__':
    main()
