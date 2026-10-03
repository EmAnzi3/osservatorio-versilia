#!/usr/bin/env python3
"""Accredited RSA stock at 2025-12-31, including native duplicate evidence."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'data/source-snapshots/a3-toscana-rsa-accredited-benchmark-2025.json'
URL = 'https://www.regione.toscana.it/documents/d/guest/elenco-strutture-del-sistema-sociale-integrato-accreditate-al-31-dicembre-2025'
PDF_SHA = '239e6f23dd97242d37fa088cec769d6aaefc1496346a9a424d2d993965e004cf'
RECORDS_SHA = '2de57ccb1a4a5d8d0c844db13bce46e1d7c02c0614cecf9b0026054ed48ad042'
KIND = 'RSA - Residenza Sanitaria Assistenziale'
CODES = {'046018', '046033', '046005', '046024', '046028', '046013', '046030'}


def digest(records):
    return hashlib.sha256(json.dumps(records, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def validate_snapshot(metric, snapshot):
    source = snapshot['source']
    pdf = base64.b64decode(source['pdfBase64'], validate=True)
    if (snapshot.get('profileId') != 'regione-toscana-rsa'
            or snapshot.get('sourceUrl') != URL
            or snapshot.get('referenceDate') != '2025-12-31'
            or source.get('sha256') != PDF_SHA
            or hashlib.sha256(pdf).hexdigest() != PDF_SHA
            or len(pdf) != 167606 or not pdf.startswith(b'%PDF')):
        raise RuntimeError('RSA: historical native source mismatch')
    records = snapshot['records']
    if (not isinstance(records, list) or len(records) != 337
            or snapshot.get('recordsSha256') != RECORDS_SHA
            or digest(records) != RECORDS_SHA):
        raise RuntimeError('RSA: complete native panel fingerprint mismatch')
    structures = {}
    for row in records:
        if (not isinstance(row, list) or len(row) != 6
                or any(not isinstance(row[i], str) or not row[i].strip() for i in (0,1,2,4))
                or row[1] != KIND or (row[3] is not None and not isinstance(row[3], str))
                or isinstance(row[5], bool) or not isinstance(row[5], int) or not 1 <= row[5] <= 22
                or dt.datetime.strptime(row[4], '%d/%m/%Y').date() > dt.date(2025,12,31)):
            raise RuntimeError('RSA: native structure/date/type mismatch')
        key = (row[0], row[2])
        if key in structures and structures[key][:5] != row[:5]:
            raise RuntimeError('RSA: ambiguous structure identity')
        structures[key] = row
    if len(structures) != 336:
        raise RuntimeError('RSA: regional structure deduplication mismatch')
    if snapshot['raw'] != {'nativeRsaRows':337, 'uniqueStructures':336, 'exactDuplicateRows':1}:
        raise RuntimeError('RSA: native aggregate components mismatch')
    if any(isinstance(v, bool) or not isinstance(v, int) for v in snapshot['raw'].values()):
        raise RuntimeError('RSA: invalid aggregate component')
    if metric['meta']['year'] != '2025' or metric['meta']['unit'] != 'count':
        raise RuntimeError('RSA: public period/unit mismatch')
    rows = metric['rows']
    if len(rows) != 7 or {r['code'] for r in rows} != CODES:
        raise RuntimeError('RSA: municipal perimeter mismatch')
    for row in rows:
        expected = sum(town == row['town'] for town, name in structures)
        if (isinstance(row['value'], bool) or not isinstance(row['value'], int)
                or row['value'] != expected):
            raise RuntimeError('RSA: public municipal reconciliation mismatch')
    bench = snapshot['benchmarks']['accreditedRsaCount']
    if (bench.get('year') != '2025' or bench.get('unit') != 'count'
            or isinstance(bench.get('tuscany'), bool) or bench.get('tuscany') != len(structures)
            or not isinstance(bench.get('tuscany'), int) or bench.get('italy') is not None):
        raise RuntimeError('RSA: regional/national benchmark mismatch')
    if snapshot.get('qualityGate', {}).get('status') != 'PASS' or snapshot['qualityGate'].get('errors') != []:
        raise RuntimeError('RSA: candidate quality gate mismatch')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    snapshot = json.loads(FROZEN.read_text())
    site = json.loads((ROOT / 'data/site-data.json').read_text())
    from materialize_salute_v140 import rsa_metric
    metric = site['metrics'].get('accreditedRsaCount') or rsa_metric(site['metrics']['population']['rows'])
    validate_snapshot(metric, snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))+'\n')
    print(json.dumps({'status':'ACQUIRED_CANDIDATE', 'publicReconciliation':'7/7',
                      'nativeRsaRows':337, 'uniqueStructures':336, 'exactDuplicateRows':1,
                      'benchmarks':snapshot['benchmarks']}))


if __name__ == '__main__':
    main()
