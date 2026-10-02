#!/usr/bin/env python3
"""Historical pharmacy stock, validity intervals and the public population denominator."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
URL = 'https://www.dati.salute.gov.it/sites/default/files/opendata/FRM_FARMA_5_20251231.csv'
SOURCE_SHA = '427d930c0143a012cb4d65fb71a50fee946dba8a5105850e685dd417cc36db20'
DAY = dt.date(2025, 12, 31)
REGIONS = {'010','020','030','041','042','050','060','070','080','090','100','110','120','130','140','150','160','170','180','190','200'}
CODES = {'046018','046033','046005','046024','046028','046013','046030'}
FIELDS = ['cod_farmacia','localizzazione','cod_comune','cod_regione','codice_tipologia','data_inizio_validita','data_fine_validita']


def date(value):
    if not isinstance(value, str):
        raise RuntimeError('Pharmacies: invalid validity date')
    return None if value == '-' else dt.datetime.strptime(value, '%d/%m/%Y').date()


def is_active(start, end):
    first, last = date(start), date(end)
    if first is None or (last is not None and last < first):
        raise RuntimeError('Pharmacies: incomplete/inverted validity interval')
    return first <= DAY and (last is None or DAY <= last)


def digest(records):
    return hashlib.sha256(json.dumps(records, separators=(',', ':')).encode()).hexdigest()


def parse(body):
    if hashlib.sha256(body).hexdigest() != SOURCE_SHA:
        raise RuntimeError('Pharmacies: historical CSV fingerprint mismatch')
    reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';')
    if not set(FIELDS).issubset(reader.fieldnames or []):
        raise RuntimeError('Pharmacies: native headers missing')
    rows = list(reader)
    if len(rows) != 57805 or len({tuple(r.values()) for r in rows}) != len(rows):
        raise RuntimeError('Pharmacies: complete historical CSV coverage mismatch')
    records = [[r[f] for f in FIELDS] for r in rows if is_active(r[FIELDS[5]], r[FIELDS[6]])]
    verify_records(records)
    return records


def verify_records(records):
    seen = set()
    for row in records:
        if not isinstance(row, list) or len(row) != 7 or any(not isinstance(v, str) for v in row):
            raise RuntimeError('Pharmacies: invalid native record')
        ident, location, commune, region, kind, start, end = row
        if not re.fullmatch(r'\d+', ident) or ident in seen or location not in {'1','2'} or not re.fullmatch(r'\d{6}', commune) or region not in REGIONS or kind not in {'1','2','3','4'} or not is_active(start, end):
            raise RuntimeError('Pharmacies: duplicate, invalid or inactive record')
        seen.add(ident)
    if len(records) != 20730 or sum(r[3] == '090' for r in records) != 1270 or {r[3] for r in records} != REGIONS:
        raise RuntimeError('Pharmacies: complete national/regional stock mismatch')


def validate_snapshot(metric, snapshot, population):
    records = snapshot['records']
    verify_records(records)
    if snapshot.get('recordsSha256') != digest(records) or snapshot.get('sourceUrl') != URL or snapshot['source'].get('sha256') != SOURCE_SHA or snapshot.get('referenceDate') != DAY.isoformat():
        raise RuntimeError('Pharmacies: historical provenance mismatch')
    demo_bytes = DEMO.read_bytes()
    denominator = json.loads(demo_bytes)['benchmarks']['population']
    if snapshot['population'] != {'sourceSnapshot': str(DEMO.relative_to(ROOT)), 'sha256': hashlib.sha256(demo_bytes).hexdigest(), 'year': '2026'} or population['meta']['year'] != '2026':
        raise RuntimeError('Pharmacies: public population provenance mismatch')
    if metric['meta']['year'] != '2025' or metric['meta']['unit'] != 'per1000':
        raise RuntimeError('Pharmacies: public period/unit mismatch')
    rows = metric['rows']
    if len(rows) != 7 or {r['code'] for r in rows} != CODES:
        raise RuntimeError('Pharmacies: municipal perimeter mismatch')
    for row in rows:
        counts = sum(r[2] == row['code'] for r in records)
        pops = [r['value'] for r in population['rows'] if r['code'] == row['code']]
        if len(pops) != 1 or isinstance(pops[0], bool) or not isinstance(pops[0], int) or pops[0] <= 0:
            raise RuntimeError('Pharmacies: municipal population missing')
        value = row['value']
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not math.isclose(value, counts / pops[0] * 1000, rel_tol=0, abs_tol=.005000001):
            raise RuntimeError('Pharmacies: public numerator/denominator reconciliation mismatch')
    bench = snapshot['benchmarks']['pharmaciesPer1000']
    if bench.get('year') != '2025' or bench.get('unit') != 'per1000':
        raise RuntimeError('Pharmacies: benchmark period/unit mismatch')
    for scope in ('tuscany','italy'):
        expected = {'pharmacies': sum(scope == 'italy' or r[3] == '090' for r in records), 'population': denominator[scope]}
        raw = snapshot['raw'][scope]
        if raw != expected or any(isinstance(v,bool) or not isinstance(v,int) for v in raw.values()):
            raise RuntimeError('Pharmacies: aggregate components mismatch')
        value = bench[scope]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not math.isclose(value, expected['pharmacies']/expected['population']*1000, rel_tol=0, abs_tol=1e-12):
            raise RuntimeError('Pharmacies: aggregate ratio mismatch')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--csv', type=Path)
    args = parser.parse_args()
    body = args.csv.read_bytes() if args.csv else urllib.request.urlopen(URL, timeout=60).read()
    records = parse(body)
    demo_bytes = DEMO.read_bytes()
    population = json.loads(demo_bytes)['benchmarks']['population']
    raw = {scope: {'pharmacies': sum(scope == 'italy' or r[3] == '090' for r in records), 'population': population[scope]} for scope in ('tuscany','italy')}
    bench = {'year':'2025','unit':'per1000', **{scope: r['pharmacies']/r['population']*1000 for scope,r in raw.items()}}
    snapshot = {'schemaVersion':1,'profileId':'health-ministry-annual','publisher':'Ministero della Salute','status':'ACQUIRED_CANDIDATE','referenceDate':DAY.isoformat(),'sourceUrl':URL,'source':{'sha256':SOURCE_SHA,'bytes':len(body),'historicalRows':57805,'activeRows':20730,'recordFields':FIELDS,'validityRule':'data_inizio_validita <= 2025-12-31 <= data_fine_validita; fine - = intervallo aperto; inizio mancante rifiutato'},'records':records,'recordsSha256':digest(records),'raw':raw,'population':{'sourceSnapshot':str(DEMO.relative_to(ROOT)),'sha256':hashlib.sha256(demo_bytes).hexdigest(),'year':'2026'},'benchmarks':{'pharmaciesPer1000':bench},'qualityGate':{'status':'PASS','errors':[],'candidateMetrics':['pharmaciesPer1000'],'publicReconciliation':'7/7 at public two decimals'},'scope':{'note':'Farmacie aperte al 31 dicembre 2025 secondo intervalli nativi di validità, incluse ordinarie, succursali, dispensari e dispensari stagionali. Una sola sede valida per codice ministeriale, nessuna somma delle righe storiche. Denominatore pubblico: residenti al 1° gennaio 2026, applicato anche a Toscana/Italia. Il CSV 2026 non sostituisce la fotografia storica 2025.'}}
    site = json.loads((ROOT/'data/site-data.json').read_text())
    validate_snapshot(site['metrics']['pharmaciesPer1000'], snapshot, site['metrics']['population'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'status':'ACQUIRED_CANDIDATE','reconciliation':'7/7','activeRows':len(records),'benchmarks':bench}))


if __name__ == '__main__':
    main()
