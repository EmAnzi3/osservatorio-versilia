#!/usr/bin/env python3
"""Validate the complete native ACI 2024 panel and both municipal ratios.

Frozen workbook bytes and panel fingerprints preserve the retrieved source;
regional/national candidates require class/geographic totals and 7/7 proof.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, math, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data/site-data.json'
LANDING = 'https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/'
ARCHIVES = (
    'https://aci.gov.it//app/uploads/2025/06/Autoritratto-2024-Parco-Veicolare.zip',
    'https://aci.gov.it/app/uploads/2025/11/Autoritratto-2024-OD.zip',
)


def public_contract(site, metric_id, unit, formula_tokens):
    metric = site['metrics'][metric_id]
    meta, rows = metric['meta'], metric['rows']
    if (meta.get('unit') != unit or str(meta.get('year')) != '2024'
            or len(rows) != 7 or len({r.get('code') for r in rows}) != 7
            or any(not isinstance(r.get('code'), str) or len(r['code']) != 6
                   or not r['code'].isdigit() or isinstance(r.get('value'), bool)
                   or not isinstance(r.get('value'), (int, float))
                   or not math.isfinite(r['value']) for r in rows)):
        raise RuntimeError(f'{metric_id}: municipal public period/unit/value contract mismatch')
    source = str(meta.get('source', '')).casefold()
    formula = str(metric.get('method', {}).get('formula', '')).casefold()
    if ('aci' not in source or 'istat' not in source
            or not all(token.casefold() in formula for token in formula_tokens)):
        raise RuntimeError(f'{metric_id}: public source/formula mismatch')
    return rows


FROZEN = ROOT / 'data/source-snapshots/a3-aci-vehicle-benchmark-2024.json'
DEMO = ROOT / 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
PANEL_SHA = '82ee5df8a8002152d92747134da1a8a706a0ba6c23baea025c52750711dd56cb'
WORKBOOK_SHA = '700e7fbc0a1f3d68502aec979a11fc6d25f4c07ecc563fc356ee9d610b77dabc'
CODES = {'046018','046033','046005','046024','046028','046013','046030'}
HEADERS = ['REGIONE','PROVINCIA','COMUNE','EURO 0','EURO 1','EURO 2','EURO 3','EURO 4','EURO 5','EURO 5B','EURO 6','EURO 6A','EURO 6B','EURO 6C','EURO 6D','EURO 6E','Non contemplato','Non definito','Totale ']


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def validate_snapshot(metric, snapshot, population):
    from decimal import Decimal, ROUND_HALF_UP
    mid = metric['meta']['key']
    if mid not in ('motorization','pollutingCars'):
        raise RuntimeError('ACI: unsupported metric')
    public_contract({'metrics':{mid:metric}},mid,'per1000' if mid=='motorization' else 'percent',
                    ('autovetture','popolazione','1.000') if mid=='motorization' else ('euro 0','autovetture totali','100'))
    source=snapshot['source'];workbook=base64.b64decode(source['workbookBase64'],validate=True)
    if (snapshot.get('profileId')!='aci-istat-annual' or snapshot.get('referenceYear')!=2024
            or snapshot.get('sourceUrl')!=LANDING or source.get('archiveUrl')!=ARCHIVES[0]
            or source.get('archiveSha256')!='733dd5877d127d9e55a202ea444044e2b789c975c670a07204f8f966e352372c'
            or source.get('archiveBytes')!=8092741
            or source.get('archiveMember')!='Autoritratto2024_Parco_veicolare/Circolante_Copert_2024.xlsx'
            or source.get('sheet')!='4 AV per Comune ' or source.get('headers')!=HEADERS
            or source.get('workbookSha256')!=WORKBOOK_SHA or hashlib.sha256(workbook).hexdigest()!=WORKBOOK_SHA):
        raise RuntimeError('ACI: native source/year/schema mismatch')
    with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
        if archive.testzip() is not None:raise RuntimeError('ACI: workbook CRC mismatch')
    records=snapshot['records'];provinces=snapshot['provinceTotals'];regions=snapshot['regionTotals'];national=snapshot['officialNational']
    if (len(records)!=7997 or len(provinces)!=108 or len(regions)!=21
            or snapshot.get('panelSha256')!=PANEL_SHA
            or digest([records,provinces,regions,national])!=PANEL_SHA):
        raise RuntimeError('ACI: full native panel fingerprint mismatch')
    # Preserve published blanks; compare sums of observed cells to explicit native
    # totals. Neither unknown geography nor undefined Euro classes are discarded.
    def verify_counts(values):
        if len(values)!=16:raise RuntimeError('ACI: Euro partition shape mismatch')
        for value in values:
            if value is not None and (isinstance(value,bool) or not isinstance(value,int) or value<0):
                raise RuntimeError('ACI: missing/invalid native observation')
        if values[-1] is None or sum(x for x in values[:-1] if x is not None)!=values[-1]:
            raise RuntimeError('ACI: Euro classes do not conserve total')
    seen=set()
    for r in records:
        if len(r)!=20 or r[0] in seen or not isinstance(r[0],int) or any(not isinstance(x,str) or not x for x in r[1:4]):
            raise RuntimeError('ACI: duplicate/invalid native row identity')
        seen.add(r[0]);verify_counts(r[4:])
    def verify_aggregate(rows, expected):
        verify_counts(expected)
        for i,v in enumerate(expected):
            observed=[r[4+i] for r in rows if r[4+i] is not None]
            if (sum(observed) if observed else None)!=v:
                raise RuntimeError('ACI: native geographic aggregate mismatch')
    for key,values in provinces.items():
        reg,prov=key.split('|');verify_aggregate([r for r in records if r[1:3]==[reg,prov]],values)
    for reg,values in regions.items():verify_aggregate([r for r in records if r[1]==reg],values)
    verify_aggregate(records,national)
    demo_bytes=DEMO.read_bytes();demo=json.loads(demo_bytes)['benchmarks']['population'];pop=snapshot['population']
    if (pop.get('year')!='2026' or population['meta'].get('year')!='2026'
            or pop.get('sourceSnapshot')!='data/source-snapshots/a3-istat-demography-benchmark-2026.json'
            or pop.get('sha256')!=hashlib.sha256(demo_bytes).hexdigest() or demo['year']!='2026'
            or pop.get('scopes')!={s:demo[s] for s in ('tuscany','italy')}):
        raise RuntimeError('ACI: population provenance/period mismatch')
    for target,unit in [('motorization','per1000'),('pollutingCars','percent')]:
        bench=snapshot['benchmarks'][target]
        if bench.get('year')!='2024' or bench.get('unit')!=unit:raise RuntimeError('ACI: benchmark period/unit mismatch')
        for scope,counts in [('tuscany',regions['TOSCANA']),('italy',national)]:
            if any(x is None for x in counts[:4]):raise RuntimeError('ACI: native numerator missing')
            expected=counts[-1]/demo[scope]*1000 if target=='motorization' else sum(counts[:4])/counts[-1]*100
            actual=bench.get(scope)
            if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-10):
                raise RuntimeError('ACI: regional/national benchmark mismatch')
    rows=metric['rows'];proof=snapshot['municipalReconciliation'];poprows=population['rows']
    if set(proof)!=CODES or {r['code'] for r in rows}!=CODES or len(poprows)!=7 or {r['code'] for r in poprows}!=CODES:
        raise RuntimeError('ACI: municipal scope mismatch')
    for row in rows:
        p=proof[row['code']];native=[r for r in records if r[0]==p['nativeRow']]
        if len(native)!=1 or native[0][1:4]!=['TOSCANA','LUCCA',row['town'].upper()] or p['town']!=row['town']:
            raise RuntimeError('ACI: municipal native geography mismatch')
        counts=native[0][4:];denom=next(r['value'] for r in poprows if r['code']==row['code'])
        if isinstance(denom,bool) or not isinstance(denom,int) or denom<=0 or p['population']!=denom or isinstance(p['population'],bool):
            raise RuntimeError('ACI: municipal population mismatch')
        if any(x is None for x in counts[:4]):raise RuntimeError('ACI: municipal Euro numerator missing')
        value=Decimal(counts[-1])/Decimal(denom)*1000 if mid=='motorization' else Decimal(sum(counts[:4]))/Decimal(counts[-1])*100
        expected=value.quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)
        if Decimal(str(row['value']))!=expected:raise RuntimeError('ACI: 7/7 public value reconciliation mismatch')
    if snapshot.get('qualityGate')!={'status':'PASS','errors':[],'publicReconciliation':'2 metrics × 7/7 PASS'}:
        raise RuntimeError('ACI: quality gate mismatch')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();snapshot=json.loads(FROZEN.read_text());site=json.loads(SITE.read_text())
    for mid in ('motorization','pollutingCars'):validate_snapshot(site['metrics'][mid],snapshot,site['metrics']['population'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'status':'ACQUIRED_CANDIDATE','publicReconciliation':'2 metrics × 7/7 PASS','nativeRows':7997,'benchmarks':snapshot['benchmarks']}))


if __name__=='__main__':main()
