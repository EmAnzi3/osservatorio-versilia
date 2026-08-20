#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'audit-artifacts' / 'demography-lucca-samples.json'
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
    'p02_2025': 'https://demo.istat.it/data/p2/P2_2025_it_046_Lucca.zip',
    'posas_2026': 'https://demo.istat.it/data/posas/POSAS_2026_it_046_Lucca.zip',
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'OsservatorioVersilia-data-audit/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def sniff(raw: bytes) -> str:
    sample = raw[:8192].decode('utf-8-sig', errors='replace')
    try:
        return csv.Sniffer().sniff(sample, delimiters=';,\t|').delimiter
    except csv.Error:
        counts = {s: sample.count(s) for s in (';', ',', '\t', '|')}
        return max(counts, key=counts.get)


def inspect_zip(url: str) -> dict:
    body = get(url)
    result = {'url': url, 'bytes': len(body), 'members': [], 'tables': []}
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        result['members'] = z.namelist()
        for name in z.namelist():
            if not name.lower().endswith(('.csv', '.txt')):
                continue
            raw = z.read(name)
            delim = sniff(raw)
            rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig', errors='replace')), delimiter=delim))
            prefix = rows[:5]
            samples = {}
            scanned = 0
            for row in rows:
                scanned += 1
                joined = '|'.join(row)
                for code, town in TOWNS.items():
                    if code in joined and code not in samples:
                        samples[code] = {'town': town, 'row': row}
                if len(samples) == len(TOWNS):
                    break
            result['tables'].append({
                'member': name,
                'delimiter': delim,
                'prefixRows': prefix,
                'samples': samples,
                'rowsScanned': scanned,
            })
    return result


def main() -> None:
    report = {key: inspect_zip(url) for key, url in SOURCES.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Campioni scritti in {OUT}')
    for key, source in report.items():
        coverages = [len(t['samples']) for t in source['tables']]
        print(key, 'coverage max', max(coverages or [0]), '/ 7')


if __name__ == '__main__':
    main()
