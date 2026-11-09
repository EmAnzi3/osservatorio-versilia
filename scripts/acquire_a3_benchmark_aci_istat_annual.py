#!/usr/bin/env python3
"""Validate the complete native ACI panel (Autoritratto) and both municipal ratios.

Frozen workbook bytes and panel fingerprints preserve the retrieved source;
regional/national candidates require class/geographic totals and 7/7 proof.
The 2024 edition keeps its pinned archive; later editions are built by
`update_source_data.py aci-vehicles --year AAAA` with `build_snapshot`.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, math, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data/site-data.json'
LANDING = 'https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/'
ARCHIVES = (
    'https://aci.gov.it//app/uploads/2025/06/Autoritratto-2024-Parco-Veicolare.zip',
    'https://aci.gov.it/app/uploads/2025/11/Autoritratto-2024-OD.zip',
)


def public_contract(site, metric_id, unit, formula_tokens, year=2024):
    metric = site['metrics'][metric_id]
    meta, rows = metric['meta'], metric['rows']
    if (meta.get('unit') != unit or str(meta.get('year')) != str(year)
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


SNAPSHOT_PREFIX = 'a3-aci-vehicle-benchmark-'
FROZEN = ROOT / f'data/source-snapshots/{SNAPSHOT_PREFIX}2024.json'
DEMO = ROOT / 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
PANEL_SHA = '82ee5df8a8002152d92747134da1a8a706a0ba6c23baea025c52750711dd56cb'
WORKBOOK_SHA = '700e7fbc0a1f3d68502aec979a11fc6d25f4c07ecc563fc356ee9d610b77dabc'
CODES = {'046018','046033','046005','046024','046028','046013','046030'}
HEADERS = ['REGIONE','PROVINCIA','COMUNE','EURO 0','EURO 1','EURO 2','EURO 3','EURO 4','EURO 5','EURO 5B','EURO 6','EURO 6A','EURO 6B','EURO 6C','EURO 6D','EURO 6E','Non contemplato','Non definito','Totale ']


SHEET = '4 AV per Comune '


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def latest_snapshot():
    """Path (relative to ROOT) of the newest frozen ACI panel."""
    found = sorted(ROOT.glob(f'data/source-snapshots/{SNAPSHOT_PREFIX}*.json'), key=lambda p: int(re.search(r'(\d{4})\.json$', p.name).group(1)))
    return str(found[-1].relative_to(ROOT)).replace('\\', '/')


def parse_panel(ws):
    """Municipal rows, province/region totals and national total of the native sheet."""
    rows = list(ws.iter_rows(values_only=True))
    if [str(x) if x is not None else None for x in rows[2][:19]] != HEADERS:
        raise RuntimeError('ACI: municipal sheet headers mismatch')
    records, provinces, regions, national = [], {}, {}, None
    region = province = None
    for n, raw in enumerate(rows[3:], start=4):
        r = list(raw[:19]) + [None] * (19 - len(raw[:19]))
        if all(v is None for v in r):
            continue
        counts = r[3:19]
        if r[0] == 'TOTALE':
            national = counts
            continue
        if r[0] is not None:
            region = r[0]
        if r[1] == 'Totale':
            regions[region] = counts
            continue
        if r[1] is not None:
            province = r[1]
        if r[2] == 'Totale':
            provinces[f'{region}|{province}'] = counts
            continue
        records.append([n, region, province, r[2], *counts])
    if national is None:
        raise RuntimeError('ACI: national total missing')
    return records, provinces, regions, national


def build_snapshot(archive, site, year, archive_url):
    """Frozen snapshot for edition `year` from the Autoritratto «Parco veicolare» archive bytes."""
    from decimal import Decimal, ROUND_HALF_UP
    from openpyxl import load_workbook
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members = [n for n in z.namelist() if n.rsplit('/', 1)[-1] == f'Circolante_Copert_{year}.xlsx']
        if len(members) != 1:
            raise RuntimeError(f'ACI: Circolante_Copert_{year}.xlsx missing')
        workbook = z.read(members[0])
    ws = load_workbook(io.BytesIO(workbook), read_only=True, data_only=True)[SHEET]
    records, provinces, regions, national = parse_panel(ws)
    demo_bytes = DEMO.read_bytes(); demo = json.loads(demo_bytes)['benchmarks']['population']
    population = site['metrics']['population']
    pop = {r['code']: r['value'] for r in population['rows']}
    proof = {}
    for row in site['metrics']['motorization']['rows']:
        native = [r for r in records if r[1:4] == ['TOSCANA', 'LUCCA', row['town'].upper()]]
        if len(native) != 1:
            raise RuntimeError(f"ACI: {row['town']} not found once in the native panel")
        proof[row['code']] = {'nativeRow': native[0][0], 'town': row['town'], 'population': pop[row['code']]}
    bench = {}
    for target, unit in (('motorization', 'per1000'), ('pollutingCars', 'percent')):
        bench[target] = {'year': str(year), 'unit': unit}
        for scope, counts in (('tuscany', regions['TOSCANA']), ('italy', national)):
            bench[target][scope] = counts[-1] / demo[scope] * 1000 if target == 'motorization' else sum(counts[:4]) / counts[-1] * 100
    return {
        'schemaVersion': 1, 'profileId': 'aci-istat-annual', 'status': 'ACQUIRED_CANDIDATE', 'referenceYear': year,
        'publisher': f'ACI / Istat — Autoritratto {year} e popolazione {demo["year"]}', 'sourceUrl': LANDING,
        'source': {'archiveUrl': archive_url, 'archiveSha256': hashlib.sha256(archive).hexdigest(), 'archiveBytes': len(archive),
                   'archiveMember': members[0], 'workbookSha256': hashlib.sha256(workbook).hexdigest(), 'sheet': SHEET,
                   'headers': HEADERS, 'workbookBase64': base64.b64encode(workbook).decode()},
        'records': records, 'provinceTotals': provinces, 'regionTotals': regions, 'officialNational': national,
        'panelSha256': digest([records, provinces, regions, national]),
        'population': {'year': demo['year'], 'sourceSnapshot': str(DEMO.relative_to(ROOT)).replace('\\', '/'),
                       'sha256': hashlib.sha256(demo_bytes).hexdigest(), 'scopes': {s: demo[s] for s in ('tuscany', 'italy')}},
        'municipalReconciliation': proof, 'benchmarks': bench,
        'scope': {'note': f'Parco autovetture ACI {year}: pannello nativo integrale di {format(len(records), ",").replace(",", ".")} righe di localizzazione, incluse le righe non definite/estere pubblicate; totali provinciali/regionali/nazionale esclusi dalla somma e riconciliati per ogni classe Euro. Celle vuote conservate null; nessun valore imputato. Quota inquinante = somma Euro 0–3 / totale autovetture × 100. Motorizzazione = autovetture {year} / popolazione pubblica al 1° gennaio {demo["year"]} × 1.000, stesso denominatore temporale per Comuni/Toscana/Italia. Entrambe le metriche riconciliate 7/7 al decimale pubblico.'},
        'qualityGate': {'status': 'PASS', 'errors': [], 'publicReconciliation': '2 metrics × 7/7 PASS'},
    }


def validate_snapshot(metric, snapshot, population):
    from decimal import Decimal, ROUND_HALF_UP
    mid = metric['meta']['key']
    if mid not in ('motorization','pollutingCars'):
        raise RuntimeError('ACI: unsupported metric')
    year=snapshot.get('referenceYear')
    if isinstance(year,bool) or not isinstance(year,int) or year<2024:raise RuntimeError('ACI: native source/year/schema mismatch')
    public_contract({'metrics':{mid:metric}},mid,'per1000' if mid=='motorization' else 'percent',
                    ('autovetture','popolazione','1.000') if mid=='motorization' else ('euro 0','autovetture totali','100'),year)
    source=snapshot['source'];workbook=base64.b64decode(source['workbookBase64'],validate=True)
    pinned=year==2024
    if (snapshot.get('profileId')!='aci-istat-annual'
            or snapshot.get('sourceUrl')!=LANDING
            or (pinned and (source.get('archiveUrl')!=ARCHIVES[0]
                or source.get('archiveSha256')!='733dd5877d127d9e55a202ea444044e2b789c975c670a07204f8f966e352372c'
                or source.get('archiveBytes')!=8092741
                or source.get('archiveMember')!='Autoritratto2024_Parco_veicolare/Circolante_Copert_2024.xlsx'
                or source.get('workbookSha256')!=WORKBOOK_SHA))
            or (not pinned and (not str(source.get('archiveUrl','')).startswith('https://aci.gov.it/')
                or str(source.get('archiveMember','')).rsplit('/',1)[-1]!=f'Circolante_Copert_{year}.xlsx'))
            or source.get('sheet')!=SHEET or source.get('headers')!=HEADERS
            or hashlib.sha256(workbook).hexdigest()!=source.get('workbookSha256')):
        raise RuntimeError('ACI: native source/year/schema mismatch')
    with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
        if archive.testzip() is not None:raise RuntimeError('ACI: workbook CRC mismatch')
    records=snapshot['records'];provinces=snapshot['provinceTotals'];regions=snapshot['regionTotals'];national=snapshot['officialNational']
    expected_panel=PANEL_SHA if pinned else snapshot.get('panelSha256')
    if ((pinned and len(records)!=7997) or len(records)<7900 or len(provinces)!=108 or len(regions)!=21
            or snapshot.get('panelSha256')!=expected_panel
            or digest([records,provinces,regions,national])!=expected_panel):
        raise RuntimeError('ACI: full native panel fingerprint mismatch')
    if not pinned:
        from openpyxl import load_workbook
        if digest(list(parse_panel(load_workbook(io.BytesIO(workbook),read_only=True,data_only=True)[SHEET])))!=expected_panel:
            raise RuntimeError('ACI: frozen workbook does not reproduce the panel')
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
        if bench.get('year')!=str(year) or bench.get('unit')!=unit:raise RuntimeError('ACI: benchmark period/unit mismatch')
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
    args=parser.parse_args();snapshot=json.loads((ROOT/latest_snapshot()).read_text());site=json.loads(SITE.read_text())
    for mid in ('motorization','pollutingCars'):validate_snapshot(site['metrics'][mid],snapshot,site['metrics']['population'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'status':'ACQUIRED_CANDIDATE','publicReconciliation':'2 metrics × 7/7 PASS','nativeRows':len(snapshot['records']),'benchmarks':snapshot['benchmarks']}))


if __name__=='__main__':main()
