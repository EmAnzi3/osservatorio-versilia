#!/usr/bin/env python3
"""Materializza il dettaglio Istat RCS 2025 per i sette Comuni.

Non crea una nuova card: arricchisce `foreignResidents` con un disclosure nelle
schede comunali e conserva nello snapshot tutte le cittadinanze straniere e i
paesi esteri di nascita con valore positivo.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'istat-rcs-demography-2025.json'

TOWNS = {
    '046005': 'Camaiore',
    '046013': 'Forte dei Marmi',
    '046018': 'Massarosa',
    '046024': 'Pietrasanta',
    '046028': 'Seravezza',
    '046030': 'Stazzema',
    '046033': 'Viareggio',
}
SOURCES = {
    'citizenship': 'https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip',
    'birthCountry': 'https://demo.istat.it/data/rcs/Dati_RCS_nascita_2025.zip',
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-materializer/1.0'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def parse_archive(url: str, kind: str) -> dict[str, list[dict]]:
    body = download(url)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(('.csv', '.txt'))]
        if not members:
            raise RuntimeError(f'RCS senza CSV/TXT: {url}')
        member = max(members, key=lambda name: archive.getinfo(name).file_size)
        raw = archive.read(member).decode('utf-8-sig')

    reader = csv.DictReader(io.StringIO(raw), delimiter=';')
    expected_label = 'Stato di cittadinanza' if kind == 'citizenship' else 'Stato di nascita'
    expected_code = 'Codice stato di cittadinanza' if kind == 'citizenship' else 'Codice stato di nascita'
    required = {'Anno', 'Codice Istat', 'Denominazione', expected_code, expected_label, 'Zona', 'Continente', 'Maschi', 'Femmine', 'Totale'}
    if not required.issubset(set(reader.fieldnames or [])):
        raise RuntimeError(f'Schema RCS {kind} inatteso: {reader.fieldnames}')

    result = {code: [] for code in TOWNS}
    for row in reader:
        code = str(row.get('Codice Istat', '')).strip()
        if code not in result:
            continue
        label = str(row.get(expected_label, '')).strip()
        state_code = str(row.get(expected_code, '')).strip()
        total = int(str(row.get('Totale', '0') or '0').strip() or 0)
        men = int(str(row.get('Maschi', '0') or '0').strip() or 0)
        women = int(str(row.get('Femmine', '0') or '0').strip() or 0)
        if men + women != total:
            raise RuntimeError(f'RCS {kind} totale incoerente: {code} {label}')
        # La riga Italia è utile per il controllo ma non per il dettaglio pubblico.
        result[code].append({
            'code': state_code,
            'label': label,
            'zone': str(row.get('Zona', '')).strip(),
            'continent': str(row.get('Continente', '')).strip(),
            'men': men,
            'women': women,
            'total': total,
        })

    if any(not items for items in result.values()):
        missing = [TOWNS[code] for code, items in result.items() if not items]
        raise RuntimeError(f'Copertura RCS {kind} non 7/7: {missing}')
    return result


def public_items(items: list[dict]) -> tuple[list[dict], int]:
    foreign = [item for item in items if item['code'] != '100' and item['label'].lower() != 'italia' and item['total'] > 0]
    foreign.sort(key=lambda item: (-item['total'], item['label']))
    total = sum(item['total'] for item in foreign)
    return foreign, total


def compact_top(items: list[dict], total: int, limit: int = 8) -> list[dict]:
    return [
        {
            'label': item['label'],
            'count': item['total'],
            'share': None if total <= 0 else item['total'] / total * 100,
            'men': item['men'],
            'women': item['women'],
            'zone': item['zone'],
            'continent': item['continent'],
        }
        for item in items[:limit]
    ]


def main() -> None:
    site = load(SITE_PATH)
    audit = load(AUDIT_PATH)
    citizenship_raw = parse_archive(SOURCES['citizenship'], 'citizenship')
    birth_raw = parse_archive(SOURCES['birthCountry'], 'birthCountry')

    metric = site['metrics']['foreignResidents']
    rows = {row['code']: row for row in metric['rows']}
    if set(rows) != set(TOWNS):
        raise RuntimeError('foreignResidents non copre esattamente i sette Comuni')

    snapshot_towns = {}
    for code, town in TOWNS.items():
        citizenship, citizenship_total = public_items(citizenship_raw[code])
        birth_country, birth_country_total = public_items(birth_raw[code])
        row = rows[code]
        if int(row['count']) != citizenship_total:
            raise RuntimeError(
                f'{town}: residenti stranieri canonici {row["count"]} != somma cittadinanze RCS {citizenship_total}'
            )
        row['foreignOrigins'] = {
            'year': 2025,
            'citizenshipTotal': citizenship_total,
            'foreignBornTotal': birth_country_total,
            'citizenshipTop': compact_top(citizenship, citizenship_total),
            'birthCountryTop': compact_top(birth_country, birth_country_total),
        }
        snapshot_towns[town] = {
            'code': code,
            'citizenshipTotal': citizenship_total,
            'foreignBornTotal': birth_country_total,
            'citizenship': citizenship,
            'birthCountry': birth_country,
        }

    metric['meta']['description'] = (
        'Quota e numero dei residenti con cittadinanza non italiana al 1° gennaio 2025. '
        'Nelle schede comunali è disponibile anche il dettaglio delle principali cittadinanze straniere e dei principali paesi esteri di nascita.'
    )
    metric['meta']['detailLabel'] = 'Principali cittadinanze e paesi di nascita'
    metric.setdefault('method', {})['originDetail'] = (
        'Istat RCS 2025 pubblica separatamente cittadinanza e paese di nascita; il loro incrocio non è disponibile. '
        'Le quote nel dettaglio sono calcolate rispettivamente sui residenti di cittadinanza straniera e sui residenti nati all’estero.'
    )

    snapshot = {
        'schemaVersion': 1,
        'generatedAt': '2026-08-20',
        'publisher': 'Istat',
        'dataset': 'RCS — popolazione residente per cittadinanza o paese di nascita',
        'reference': '1 gennaio 2025',
        'coverage': '7/7',
        'sources': SOURCES,
        'towns': snapshot_towns,
        'note': 'Cittadinanza e paese di nascita sono distribuzioni distinte; Istat non rilascia il loro incrocio nel dataset RCS.',
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save(SNAPSHOT_PATH, snapshot)

    for candidate in audit.get('candidates', []):
        if candidate.get('key') == 'citizenshipBirthCountryDetail':
            candidate['implementationStatus'] = 'public_town_detail_2025'
            candidate['snapshot'] = 'data/source-snapshots/istat-rcs-demography-2025.json'
    audit.setdefault('demographyV2', {})['foreignCitizenshipBirthCountry'] = 'public_town_detail_2025'

    save(SITE_PATH, site)
    save(AUDIT_PATH, audit)
    print('Istat RCS 2025 materializzato: cittadinanze e paesi di nascita 7/7, dettaglio pubblico collegato a foreignResidents.')


if __name__ == '__main__':
    main()
