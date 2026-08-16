#!/usr/bin/env python3
"""Extract NIC Toscana annual averages for 2016-2024 from the official accessible table.

Source: Ufficio regionale di statistica della Regione Toscana, elaboration on
Istat consumer-price data. The source table publishes monthly NIC indices with
base 2015=100. We average the 12 monthly values for each year and rebase the
annual series to 2016=100 for comparison with municipal income growth.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SOURCE = (
    'https://www.regione.toscana.it/documents/10180/12588189/'
    'Tabella%2Baccessibile%2BIndice%2Bprezzi%2Bal%2Bconsumo%2BIta%2BTos%2BNord-Ovest%2BNord-Est%2BCentro%2BSud%2BIsole%2BGen16-Dic24.html/'
    '4b90be0a-136a-7d8c-e4a5-a87904a8f617?t=1740506039965'
)
UA = {'User-Agent': 'Mozilla/5.0 (compatible; OsservatorioVersilia/1.0)'}


class TableParser(HTMLParser):
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


def fetch() -> str:
    request = urllib.request.Request(SOURCE, headers=UA)
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode('utf-8', errors='replace')


def number(value: str) -> float:
    return float(value.strip().replace('.', '').replace(',', '.'))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('/tmp/nic-toscana-2016-2024.json'))
    args = parser.parse_args()

    table = TableParser()
    table.feed(fetch())
    header = next((row for row in table.rows if row and row[0].strip().lower() == 'mese' and 'Toscana' in row), None)
    if header is None:
        raise RuntimeError('header tabella NIC Toscana non trovato')
    toscana_index = header.index('Toscana')
    monthly: dict[int, list[float]] = {year: [] for year in range(2016, 2025)}
    raw_rows = []
    for row in table.rows:
        if len(row) <= toscana_index:
            continue
        match = re.search(r'(20(?:1[6-9]|2[0-4]))$', row[0])
        if not match:
            continue
        year = int(match.group(1))
        value = number(row[toscana_index])
        monthly[year].append(value)
        raw_rows.append({'month': row[0], 'toscana': value})
    incomplete = {year: len(values) for year, values in monthly.items() if len(values) != 12}
    if incomplete:
        raise RuntimeError(f'annualità NIC incomplete: {incomplete}')

    annual = {year: sum(values) / 12 for year, values in monthly.items()}
    annual_rates = {
        year: (annual[year] / annual[year - 1] - 1.0) * 100.0
        for year in range(2017, 2025)
    }
    # Official Regione Toscana release reports +1.1% for 2024/2023.
    if abs(annual_rates[2024] - 1.1) > 0.15:
        raise RuntimeError(f'controllo 2024/2023 fallito: {annual_rates[2024]:.3f}% anziché circa 1,1%')
    base = annual[2016]
    indexed = {year: annual[year] / base * 100.0 for year in annual}

    snapshot = {
        'schemaVersion': 2,
        'source': 'Regione Toscana - Ufficio regionale di statistica su dati Istat',
        'sourceUrl': SOURCE,
        'indicator': 'Indice dei prezzi al consumo per l’intera collettività (NIC), indice generale',
        'territory': {'label': 'Toscana', 'level': 'region'},
        'sourceBase': '2015=100',
        'comparisonBase': '2016=100',
        'years': list(range(2016, 2025)),
        'annualAverageSourceIndex': [round(annual[year], 4) for year in range(2016, 2025)],
        'comparisonIndex': [round(indexed[year], 4) for year in range(2016, 2025)],
        'annualRatesPercent': {str(year): round(annual_rates[year], 3) for year in range(2017, 2025)},
        'monthlyRows': raw_rows,
        'coverage': '2016-2024 complete',
        'note': (
            'Riferimento regionale Toscana, non Provincia di Lucca e non Comune di Lucca. '
            'Le medie annue sono calcolate sui 12 indici mensili ufficiali pubblicati nella tabella accessibile.'
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('NIC Toscana annual averages: ' + ', '.join(f'{year}={annual[year]:.3f}' for year in range(2016, 2025)))
    print('NIC Toscana comparison index 2016=100: ' + ', '.join(f'{year}={indexed[year]:.2f}' for year in range(2016, 2025)))
    print(f'2024/2023={annual_rates[2024]:.3f}% · snapshot={args.out}')


if __name__ == '__main__':
    main()
