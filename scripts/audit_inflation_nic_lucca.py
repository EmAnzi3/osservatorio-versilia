#!/usr/bin/env python3
"""Probe NIC annual-average all-items for Provincia di Lucca from official Istat SDMX.

The provincial series is a secondary audit only: the economy draft uses the
validated Toscana NIC series. If every known official provincial dataflow is
explicitly unavailable (HTTP 404), record that state in the audit artifact
instead of turning source unavailability into a CI failure. Partial or malformed
data still fail hard.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://esploradati.istat.it/SDMXWS/rest/data'
FLOWS = ['167_742', '167_742_DF_DCSP_NIC2B2015_1', '167_742_DF_DCSP_NIC2B2015_2']
KEY = 'A.ITI12.40.4.00'


def fetch(flow: str, start: int, end: int) -> tuple[str, bytes, str]:
    query = urllib.parse.urlencode({'startPeriod': start, 'endPeriod': end})
    url = f'{BASE}/IT1,{flow}/{KEY}?{query}'
    headers = {
        'User-Agent': 'OsservatorioVersilia-data-audit/1.0',
        'Accept': 'application/vnd.sdmx.data+csv;version=1.0.0, text/csv',
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return url, response.read(), response.headers.get('Content-Type', '')


def parse_csv(payload: bytes) -> list[dict]:
    text = payload.decode('utf-8-sig', errors='replace')
    dialect = csv.Sniffer().sniff(text[:5000], delimiters=',;\t')
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    out = []
    for row in rows:
        time = row.get('TIME_PERIOD') or row.get('TIME') or row.get('time_period')
        value = row.get('OBS_VALUE') or row.get('Value') or row.get('value')
        if time is None or value in (None, ''):
            continue
        try:
            out.append({'year': int(str(time)[:4]), 'value': float(str(value).replace(',', '.'))})
        except ValueError:
            continue
    return out


def write_result(path: Path, result: dict) -> None:
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=int, default=2016)
    p.add_argument('--end', type=int, default=2024)
    p.add_argument('--out', type=Path, default=Path('/tmp/nic-lucca-2016-2024.json'))
    args = p.parse_args()
    errors = []
    observations = []
    used_url = None
    content_type = None
    for flow in FLOWS:
        try:
            url, payload, ctype = fetch(flow, args.start, args.end)
            observations = parse_csv(payload) if payload else []
            if observations:
                used_url, content_type = url, ctype
                break
            errors.append(f'{flow}: risposta senza osservazioni CSV ({ctype}, {len(payload)} bytes)')
        except Exception as exc:
            errors.append(f'{flow}: {type(exc).__name__}: {exc}')

    expected = list(range(args.start, args.end + 1))
    by_year = {item['year']: item['value'] for item in observations}
    missing = [year for year in expected if year not in by_year]

    all_known_flows_not_found = (
        not observations
        and len(errors) == len(FLOWS)
        and all('HTTP Error 404' in error for error in errors)
    )
    if missing and all_known_flows_not_found:
        result = {
            'schemaVersion': 1,
            'status': 'unavailable',
            'source': 'Istat - IstatData / SDMX',
            'dataflowsTried': FLOWS,
            'seriesKey': KEY,
            'territory': {'label': 'Provincia di Lucca', 'code': 'ITI12', 'level': 'province'},
            'indicator': 'NIC - indice generale, media annua',
            'requestedYears': expected,
            'reason': 'Tutti i dataflow provinciali Istat noti rispondono HTTP 404; nessun dato provinciale viene usato nel draft.',
            'errorsTried': errors,
        }
        write_result(args.out, result)
        return

    if missing:
        raise RuntimeError(f'NIC Lucca incompleto; mancanti {missing}; errori={errors}')

    values = [by_year[year] for year in expected]
    base = values[0]
    comparison = [round(value / base * 100, 4) for value in values]
    result = {
        'schemaVersion': 1,
        'status': 'ok',
        'source': 'Istat - IstatData / SDMX',
        'dataflow': '167_742',
        'seriesKey': KEY,
        'territory': {'label': 'Provincia di Lucca', 'code': 'ITI12', 'level': 'province'},
        'indicator': 'NIC - indice generale, media annua',
        'sourceBase': '2015=100',
        'comparisonBase': f'{args.start}=100',
        'years': expected,
        'sourceIndex': values,
        'comparisonIndex': comparison,
        'sourceUrl': used_url,
        'contentType': content_type,
        'errorsTried': errors,
    }
    write_result(args.out, result)


if __name__ == '__main__':
    main()
