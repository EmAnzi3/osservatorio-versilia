#!/usr/bin/env python3
"""Materialize a governed median on the official IFC geography."""
from __future__ import annotations
import json, math, re, statistics
from pathlib import Path
from acquire_a3_benchmark_istat_fragility_2022 import METRIC, TUSCANY_PREFIXES, LANDING

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/source-snapshots/a3-istat-accessibility-benchmark-2019.json'

def materialize(site, snapshot):
    gate = snapshot.get('qualityGate') or {}
    if gate.get('status') != 'PASS' or gate.get('errors') != []: raise RuntimeError('IFC quality gate not PASS')
    if snapshot.get('referenceYear') != 2019 or snapshot.get('releaseYear') != 2022 or snapshot.get('aggregation') != 'median-municipalities': raise RuntimeError('IFC reference/aggregation mismatch')
    if snapshot.get('sourceUrl') != LANDING: raise RuntimeError('IFC source URL mismatch')
    scope = snapshot.get('scope') or {}
    if scope.get('italyMunicipalities') != 7903 or scope.get('tuscanyMunicipalities') != 273 or scope.get('excludedMunicipality',{}).get('code') != '081025': raise RuntimeError('IFC official scope mismatch')
    records = {}
    for pair in snapshot.get('records') or []:
        if not isinstance(pair,list) or len(pair) != 2: raise RuntimeError('IFC invalid record')
        code, value = pair
        if not isinstance(code,str) or not re.fullmatch(r'\d{6}',code) or code in records: raise RuntimeError('IFC duplicate/invalid code')
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0: raise RuntimeError('IFC missing/invalid value')
        records[code] = float(value)
    if len(records) != 7903 or '081025' in records or sum(c[:3] in TUSCANY_PREFIXES for c in records) != 273: raise RuntimeError('IFC record scope mismatch')
    benchmark = snapshot['benchmarks'][METRIC]
    if benchmark.get('year') != '2019' or benchmark.get('unit') != 'minutes': raise RuntimeError('IFC year/unit mismatch')
    for scope_name, values in [('italy',list(records.values())),('tuscany',[v for c,v in records.items() if c[:3] in TUSCANY_PREFIXES])]:
        value = benchmark[scope_name]
        if isinstance(value,bool) or not math.isclose(value,statistics.median(values),rel_tol=0,abs_tol=1e-9): raise RuntimeError('IFC benchmark/records mismatch')
    metric = site['metrics'][METRIC]
    if metric['meta'].get('unit') != 'minutes' or metric['meta'].get('year') != '2019': raise RuntimeError('IFC public contract mismatch')
    local = json.loads((ROOT / 'data/source-snapshots/fragilita-comunale-v133.json').read_text())['istatByTown']
    expected = {t['code']:float(t['latest2022']['INDEX_ACCES_ESSENT_SERVICES']) for t in local.values()}
    rows = metric.get('rows') or []
    if len(rows) != 7 or len({r['code'] for r in rows}) != 7 or {r['code'] for r in rows} != set(expected): raise RuntimeError('IFC public rows not 7/7')
    for row in rows:
        code = row['code']; value = row.get('value')
        if isinstance(value,bool) or not isinstance(value,(int,float)) or code not in records or not math.isclose(value,records[code],abs_tol=1e-9,rel_tol=0) or not math.isclose(value,expected[code],abs_tol=1e-9,rel_tol=0): raise RuntimeError('IFC public/source mismatch')
    candidate = {'year':'2019','tuscany':benchmark['tuscany'],'italy':benchmark['italy'],'source':snapshot['publisher'],'url':LANDING,'sourceSnapshot':str(SNAPSHOT.relative_to(ROOT)),'note':scope['note']}
    existing = metric['meta'].get('benchmark')
    if existing and existing != candidate: raise RuntimeError('IFC existing benchmark conflict')
    metric['meta']['benchmark'] = candidate

def main():
    site_path = ROOT / 'data/site-data.json'
    site = json.loads(site_path.read_text())
    materialize(site,json.loads(SNAPSHOT.read_text()))
    site_path.write_text(json.dumps(site,ensure_ascii=False,indent=2)+'\n')
    print('A3 IFC accessibility materialized: Tuscany 33.2 / Italy 27.1 minutes; official scope and 7/7 PASS.')

if __name__ == '__main__': main()
