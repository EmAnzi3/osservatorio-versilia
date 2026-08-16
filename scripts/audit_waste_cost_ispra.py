#!/usr/bin/env python3
"""Audit ISPRA 2024 CTOTab municipal waste-service costs for the seven towns.

The Catasto Rifiuti exposes the Tuscany municipal-cost table over paginated
regional pages. We scan the complete regional table and accept only rows where
"N. di comuni" is 1, so an aggregation can never be silently assigned to a
town.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL = (
    'https://www.catasto-rifiuti.isprambiente.it/index.php?'
    'aa=2024&p={page}&pg=costicomuneproc&reg1=Toscana&regid=09&regid2=09'
)
TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
UA = {'User-Agent': 'Mozilla/5.0 (compatible; OsservatorioVersilia/1.0)'}


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(ch for ch in value if not unicodedata.combining(ch)).lower().strip()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def number(value: str) -> float | None:
    text = (value or '').strip().replace('\xa0', '').replace(' ', '')
    if not text or text.lower() in {'-', 'n.d.', 'nd'}:
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
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'tr':
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
        elif tag == 'tr' and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def fetch(page: int) -> str:
    url = URL.format(page=page)
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode('utf-8', errors='replace')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('/tmp/ispra-waste-cost.json'))
    args = parser.parse_args()
    wanted = {norm(town): town for town in TOWNS}
    found: dict[str, dict] = {}
    scanned_pages = []
    for page in range(1, 16):
        text = fetch(page)
        table = Tables()
        table.feed(text)
        scanned_pages.append(URL.format(page=page))
        for row in table.rows:
            if len(row) < 5:
                continue
            town = wanted.get(norm(row[0]))
            if not town:
                continue
            municipality_count = number(row[2])
            if municipality_count is None or int(round(municipality_count)) != 1:
                raise RuntimeError(f'{town}: dato non comunale, N. comuni={row[2]!r}; row={row}')
            population = number(row[3])
            ctot = number(row[-1])
            if ctot is None or not 20 <= ctot <= 1000:
                raise RuntimeError(f'{town}: CTOTab non valido; row={row}')
            found[town] = {
                'ctotPerResident': round(ctot, 2),
                'population': int(round(population)) if population is not None else None,
                'municipalityCount': 1,
                'sourcePage': URL.format(page=page),
                'rawRow': row,
            }
        if len(found) == len(TOWNS):
            break
    missing = [town for town in TOWNS if town not in found]
    if missing:
        raise RuntimeError(f'Comuni ISPRA mancanti nel campione 2024: {missing}')
    snapshot = {
        'schemaVersion': 3,
        'year': 2024,
        'source': 'ISPRA - Catasto Nazionale Rifiuti',
        'definition': 'CTOTab - costi totali di gestione del servizio di igiene urbana, euro/abitante/anno',
        'coverage': '7/7',
        'towns': found,
        'scannedPages': scanned_pages,
        'note': 'Sono pubblicate esclusivamente righe comunali con N. di comuni = 1; le aggregazioni sono escluse.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for town in TOWNS:
        print(f"{town}: {found[town]['ctotPerResident']:.2f} €/ab")
    print(f'ISPRA waste-cost audit OK: 7/7 · snapshot={args.out}')


if __name__ == '__main__':
    main()
