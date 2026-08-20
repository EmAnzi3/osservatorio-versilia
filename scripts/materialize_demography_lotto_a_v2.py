#!/usr/bin/env python3
"""Compatibilità delle serie storiche Istat per il materializzatore Demografia.

Riusa integralmente il materializzatore Lotto A, sostituendo soltanto il parser
CSV e la lettura P02 con una risoluzione semantica delle intestazioni. Istat ha
cambiato alcune etichette fra annualità (es. popolazione al 31 dicembre), ma il
significato statistico delle colonne resta lo stesso.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
import zipfile

import materialize_demography_lotto_a as base


def norm(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', text.lower().replace('°', '')).strip()


def read_csv_from_zip(url: str) -> tuple[list[str], list[list[str]], str]:
    body = base.download(url)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(('.csv', '.txt'))]
        if len(names) != 1:
            raise RuntimeError(f'Archivio inatteso {url}: {names}')
        raw = archive.read(names[0]).decode('utf-8-sig', errors='strict')
    rows = list(csv.reader(io.StringIO(raw), delimiter=';'))
    if len(rows) < 2:
        raise RuntimeError(f'CSV troppo corto: {url}')
    header_index = None
    for index, row in enumerate(rows[:10]):
        if any(norm(cell) == 'codice comune' for cell in row):
            header_index = index
            break
    if header_index is None:
        raise RuntimeError(f'Intestazione Codice comune non trovata: {url}')
    title = next((row[0].strip() for row in rows[:header_index] if row and row[0].strip()), '')
    header = [cell.strip() for cell in rows[header_index]]
    return header, rows[header_index + 1:], title


def field(rec: dict[str, str], *tokens: str, exclude: tuple[str, ...] = ()) -> str:
    required = [norm(token) for token in tokens]
    forbidden = [norm(token) for token in exclude]
    matches = []
    for key in rec:
        label = norm(key)
        if all(token in label for token in required) and not any(token in label for token in forbidden):
            matches.append(key)
    if len(matches) != 1:
        raise RuntimeError(
            f'Campo non univoco per {tokens}, exclude={exclude}: {matches}\n'
            f'Campi disponibili: {list(rec)}'
        )
    return rec[matches[0]]


def p2_snapshot() -> dict:
    out = {base.TOWNS[code]: [] for code in base.TOWNS}
    sources = []
    resolved_headers = {}
    for year in base.P2_YEARS:
        url = f'https://demo.istat.it/data/p2/P2_{year}_it_046_Lucca.zip'
        records, title = base.records_by_code(url)
        sources.append({'year': year, 'url': url, 'title': title})
        sample = next(iter(records.values()))
        resolved_headers[str(year)] = {
            'populationJan1': next(key for key in sample if sample[key] == field(sample, 'popolazione', 'gennaio', 'totale')),
            'populationDec31': next(key for key in sample if sample[key] == field(sample, 'popolazione', 'dicembre', 'totale')),
            'births': next(key for key in sample if sample[key] == field(sample, 'nati vivi', 'totale')),
            'deaths': next(key for key in sample if sample[key] == field(sample, 'morti', 'totale')),
            'naturalBalance': next(key for key in sample if sample[key] == field(sample, 'saldo naturale', 'totale')),
        }
        for code, town in base.TOWNS.items():
            r = records[code]
            jan1 = int(base.num(field(r, 'popolazione', 'gennaio', 'totale')))
            dec31 = int(base.num(field(r, 'popolazione', 'dicembre', 'totale')))
            births = int(base.num(field(r, 'nati vivi', 'totale')))
            deaths = int(base.num(field(r, 'morti', 'totale')))
            natural = int(base.num(field(r, 'saldo naturale', 'totale')))
            information = next((value.strip() for key, value in r.items() if norm(key) == 'informazioni'), '')
            if natural != births - deaths:
                raise RuntimeError(f'{town} {year}: saldo naturale {natural} != {births} - {deaths}')
            mean_population = (jan1 + dec31) / 2
            out[town].append({
                'year': year,
                'populationJan1': jan1,
                'populationDec31': dec31,
                'meanPopulation': mean_population,
                'births': births,
                'deaths': deaths,
                'naturalBalance': natural,
                'birthRatePer1000': base.round_clean(births / mean_population * 1000),
                'deathRatePer1000': base.round_clean(deaths / mean_population * 1000),
                'naturalBalanceRatePer1000': base.round_clean(natural / mean_population * 1000),
                'informationFlag': information,
            })
    return {'sources': sources, 'resolvedHeaders': resolved_headers, 'towns': out}


# Il resto della materializzazione, compresi schema, formule, temi, registro fonti
# e monitor, resta esattamente quello del materializzatore principale.
base.read_csv_from_zip = read_csv_from_zip
base.p2_snapshot = p2_snapshot

if __name__ == '__main__':
    base.main()
