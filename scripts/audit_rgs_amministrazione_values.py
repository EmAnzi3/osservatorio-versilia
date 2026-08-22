#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

TOWNS = ['Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta', 'Seravezza', 'Stazzema', 'Viareggio']
URLS = {
    'turnover': 'https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Occupazione-e-Turnover---Dati-analitici-per-Ente.csv',
    'age': 'https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Anzianita---Dati-analitici-per-Ente.csv',
    'hires': 'https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Assunzioni---Dati-Analitici-per-Causale-Assunzione.csv',
    'cessations': 'https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Cessazioni---Dati-analitici-per-Causale-Cessazione.csv',
}
UA = 'Mozilla/5.0 (compatible; OsservatorioVersilia/1.0; +https://osservatorioversilia.it)'


def norm(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r'[^A-Z0-9]+', ' ', text.upper()).strip()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=180) as response:
        body = response.read()
        if response.status != 200 or len(body) < 100:
            raise RuntimeError(f'{url}: HTTP {response.status}, {len(body)} bytes')
        return body


def parse(body: bytes) -> list[dict[str, str]]:
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
    lines = text.splitlines()
    if lines and lines[0].upper().startswith('SEP='):
        delim = lines.pop(0)[4:5] or ';'
        text = '\n'.join(lines)
    else:
        delim = ';'
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def number(value) -> float:
    raw = str(value or '').strip().replace('\u00a0', '').replace(' ', '')
    if not raw:
        return 0.0
    if ',' in raw and '.' not in raw:
        raw = raw.replace(',', '.')
    return float(raw)


def rows_for(rows: list[dict[str, str]], town: str) -> list[dict[str, str]]:
    target = norm(f'COMUNE DI {town}')
    out = []
    for row in rows:
        if norm(row.get('Descrizione Tipo Istituzione', '')) != 'COMUNI':
            continue
        if norm(row.get('Descrizione Ente', '')) == target:
            out.append(row)
    return out


def staff_total(rows: list[dict[str, str]]) -> float:
    fields = [
        'Numero Dipendenti Donne Tempo Pieno',
        'Numero Dipendenti Uomini Tempo Pieno',
        'Numero Dipendenti Donne Part time Inf. 50%',
        'Numero Dipendenti Uomini Part time Inf. 50%',
        'Numero Dipendenti Donne Part time Sup. 50%',
        'Numero Dipendenti Uomini Part time Sup. 50%',
    ]
    return sum(number(row.get(field)) for row in rows for field in fields)


def turnover_gross(rows: list[dict[str, str]], kind: str) -> float:
    fields = (
        ['Numero Dipendenti Donne Assunte', 'Numero Dipendenti Uomini Assunti']
        if kind == 'hires'
        else ['Numero Dipendenti Donne Cessate', 'Numero Dipendenti Uomini Cessati']
    )
    return sum(number(row.get(field)) for row in rows for field in fields)


def flow_summary(rows: list[dict[str, str]]) -> dict:
    by_cause = defaultdict(float)
    for row in rows:
        label = str(row.get('Descrizione Causale', '')).strip()
        by_cause[label] += number(row.get('Donne')) + number(row.get('Uomini'))
    gross = sum(by_cause.values())
    transfers = sum(value for label, value in by_cause.items() if 'PASSAGGI' in norm(label) and 'AMMINISTRAZ' in norm(label))
    return {
        'gross': gross,
        'transfersBetweenAdministrations': transfers,
        'netOfTransfers': gross - transfers,
        'causes': {label: value for label, value in sorted(by_cause.items()) if value != 0},
    }


def age_summary(rows: list[dict[str, str]]) -> dict:
    bands = defaultdict(float)
    for row in rows:
        band = str(row.get('Descrizione Fascia Eta', '')).strip()
        bands[band] += number(row.get('Numero Dipendenti Donne')) + number(row.get('Numero Dipendenti Uomini'))
    total = sum(bands.values())
    over55 = 0.0
    for label, value in bands.items():
        n = norm(label)
        if any(token in n for token in ('55 A 59', '60 A 64', '65 A 67', '68 A 99')):
            over55 += value
    return {
        'total': total,
        'bands': dict(sorted(bands.items())),
        'over55': over55,
        'over55SharePct': round(over55 / total * 100, 4) if total else None,
    }


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        bodies = dict(zip(URLS, pool.map(fetch, URLS.values())))
    datasets = {key: parse(body) for key, body in bodies.items()}
    report = {
        'schemaVersion': 1,
        'referenceYear': 2024,
        'source': 'RGS OpenBDAP / Conto Annuale',
        'sourceUrls': URLS,
        'towns': {},
    }
    for town in TOWNS:
        trows = rows_for(datasets['turnover'], town)
        arows = rows_for(datasets['age'], town)
        hrows = rows_for(datasets['hires'], town)
        crows = rows_for(datasets['cessations'], town)
        if not all((trows, arows, hrows, crows)):
            raise RuntimeError(f'{town}: dataset incompleto: turnover={len(trows)}, age={len(arows)}, hires={len(hrows)}, cessations={len(crows)}')
        staff = staff_total(trows)
        age = age_summary(arows)
        hires = flow_summary(hrows)
        cess = flow_summary(crows)
        gross_hires = turnover_gross(trows, 'hires')
        gross_cess = turnover_gross(trows, 'cessations')
        if abs(gross_hires - hires['gross']) > 0.001:
            raise RuntimeError(f'{town}: assunzioni per causale {hires["gross"]} != totale turnover {gross_hires}')
        if abs(gross_cess - cess['gross']) > 0.001:
            raise RuntimeError(f'{town}: cessazioni per causale {cess["gross"]} != totale turnover {gross_cess}')
        if abs(staff - age['total']) > 0.001:
            raise RuntimeError(f'{town}: personale turnover {staff} != personale età {age["total"]}')
        net_turnover = hires['netOfTransfers'] - cess['netOfTransfers']
        report['towns'][town] = {
            'institutionCode': trows[0].get('Codice Istituzione'),
            'staffAt31Dec': staff,
            'grossHires': gross_hires,
            'grossCessations': gross_cess,
            'hires': hires,
            'cessations': cess,
            'netTurnoverHeadcount': net_turnover,
            'netTurnoverRatePct': round(net_turnover / staff * 100, 4) if staff else None,
            'age': age,
        }
    print('RGS_ADMIN_VALUES_BEGIN')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('RGS_ADMIN_VALUES_END')
    print('Valori RGS 2024 verificati 7/7; totali turnover, causali ed età riconciliati.')


if __name__ == '__main__':
    main()
