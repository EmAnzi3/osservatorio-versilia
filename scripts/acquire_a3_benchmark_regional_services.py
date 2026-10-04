#!/usr/bin/env python3
"""Official aggregate rows, with exact reconciliation of the municipal components."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re
from pathlib import Path
from pypdf import PdfReader
from acquire_a3_benchmark_istat_fragility_2022 import download

ROOT = Path(__file__).resolve().parents[1]
WATER_DATA = 'https://esploradati.istat.it/SDMXWS/rest/data/IT1,12_60_DF_DCCV_CONSACQUA_2,1.0/all?startPeriod=2018&endPeriod=2018'
WATER_TABLE = 'https://www.istat.it/storage/ASI/2021/capitoli/C02.pdf'

def loss(immessa, erogata):
    if immessa <= 0 or erogata < 0 or erogata > immessa: raise RuntimeError('Invalid water volumes')
    return (immessa-erogata)/immessa*100

def acquire_water(data, pdf):
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    rows = {}
    for row in reader:
        if row['FREQ'] != 'A' or row['TIME_PERIOD'] != '2018' or row['DATA_TYPE'] not in ('ACQ_IMM','ACQ_EROG'): raise RuntimeError('Water series mismatch')
        key = (row['REF_AREA'],row['DATA_TYPE'])
        if key in rows: raise RuntimeError('Water duplicate observation')
        value = float(row['OBS_VALUE'])
        if not math.isfinite(value) or value < 0: raise RuntimeError('Water missing/invalid volume')
        rows[key] = value
    pages = [p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages]
    tables = [p for p in pages if 'Tavola 2.17 ' in p and '2018 - PER REGIONE' in p]
    if len(tables) != 1: raise RuntimeError('Water official regional table not unique')
    text = tables[0].split('2018 - PER PROVINCIA')[0]
    aggregates = {}
    for scope,label in [('tuscany','Toscana'),('italy','ITALIA')]:
        found = re.findall(r'^'+label+r'\s+([\d.]+)\s+([\d.]+)\s+(\d+,\d+)\s*$',text,re.M)
        if len(found) != 1: raise RuntimeError('Water aggregate row not unique')
        im, er, pct = found[0]
        im, er, pct = int(im.replace('.','')),int(er.replace('.','')),float(pct.replace(',','.'))
        if abs(loss(im,er)-pct) > .051: raise RuntimeError('Water official percentage/volumes mismatch')
        aggregates[scope] = {'immessa':im,'erogata':er,'lossPercent':pct}
    if rows.get(('IT','ACQ_IMM')) != aggregates['italy']['immessa'] or rows.get(('IT','ACQ_EROG')) != aggregates['italy']['erogata']: raise RuntimeError('Water national table/SDMX mismatch')
    local = json.loads((ROOT/'data/source-snapshots/ambiente-acqua-v124-data.json').read_text())['waterNetworkLosses']['towns']
    if len(local) != 7: raise RuntimeError('Water public scope not 7/7')
    proof = {}
    for code,item in local.items():
        item = item['2018']
        for field,dt in [('immessa','ACQ_IMM'),('erogata','ACQ_EROG')]:
            if rows.get((code,dt)) != item[field]: raise RuntimeError('Water municipal volume mismatch')
        proof[code] = {'immessa':item['immessa'],'erogata':item['erogata'],'value':loss(item['immessa'],item['erogata'])}
    return {'schemaVersion':1,'publisher':'Istat — Censimento delle acque per uso civile','sourceProfileId':'istat-water-irregular','sourceUrl':WATER_TABLE,
        'sources':{'municipalData':WATER_DATA,'officialAggregateTable':WATER_TABLE,'csvSha256':hashlib.sha256(data).hexdigest(),'pdfSha256':hashlib.sha256(pdf).hexdigest(),'table':'ASI 2021, Tavola 2.17, righe Toscana e ITALIA, anno 2018'},
        'raw':aggregates,'municipalReconciliation':proof,'qualityGate':{'status':'PASS','errors':[],'publicReconciliation':'7/7 exact municipal volume pairs','nationalReconciliation':'Official table = SDMX national volume pair'},
        'benchmarks':{'waterNetworkLosses':{'year':'2018','unit':'percent','tuscany':aggregates['tuscany']['lossPercent'],'italy':aggregates['italy']['lossPercent']}},
        'scope':{'note':'Perdite totali sulle reti comunali di distribuzione nel 2018. Percentuali ufficiali Istat arrotondate a un decimale, verificate sui volumi regionali/nazionali; non è una media delle percentuali comunali.'}}

def number(raw,label):
    if not re.fullmatch(r'\d+',raw.strip()): raise RuntimeError(f'Infancy missing/invalid {label}')
    return int(raw)

def acquire_infancy(data):
    local = json.loads((ROOT/'data/source-snapshots/welfare-prima-infanzia-2026-08.json').read_text())
    source = local['sources']['earlyChildhoodPotentialCapacityRate']
    reader = csv.DictReader(io.StringIO(data.decode('cp1252')),delimiter=';')
    required = {'Anno educativo','CODICE ISTAT','Zone','Totale 3-36 mesi','Totale Ricettività potenziale'}
    if not required.issubset(reader.fieldnames or []): raise RuntimeError('Infancy schema mismatch')
    records = list(reader)
    municipal = {}; regional = []
    for row in records:
        code = row['CODICE ISTAT'].strip()
        if code:
            if row['Anno educativo'] != '2024-25' or not code.isdigit(): raise RuntimeError('Infancy year/code mismatch')
            code = code.zfill(6)
            if code in municipal: raise RuntimeError('Infancy duplicate municipality')
            municipal[code] = row
        elif row['Zone'].strip() == 'Toscana': regional.append(row)
    if len(municipal) != 273 or len(regional) != 1: raise RuntimeError('Infancy official municipal/regional scope mismatch')
    row = regional[0]
    capacity = number(row['Totale Ricettività potenziale'],'Tuscany capacity')
    children = number(row['Totale 3-36 mesi'],'Tuscany children 3-36 months')
    if children <= 0: raise RuntimeError('Infancy regional denominator not positive')
    proof = {}
    for town,item in local['towns'].items():
        code = item['istatCode']; r = municipal[code]; raw = item['earlyChildhood']
        cap = number(r['Totale Ricettività potenziale'],town+' capacity'); den = number(r['Totale 3-36 mesi'],town+' children')
        if cap != raw['potentialCapacity'] or den != raw['children3to36Months'] or den <= 0: raise RuntimeError('Infancy municipal components mismatch')
        proof[code] = {'town':town,'capacity':cap,'children3to36Months':den,'value':cap/den*100}
    if len(proof) != 7: raise RuntimeError('Infancy public reconciliation not 7/7')
    # Regional totals are explicit: do not sum municipal and Union rows,
    # and do not turn blank municipal component cells into zero.
    return {'schemaVersion':1,'publisher':'Regione Toscana — Servizi educativi per la prima infanzia','sourceProfileId':'regione-toscana-early-childhood','sourceUrl':source['url'],
        'sources':{'data':source['url'],'landing':source['datasetPage'],'csvSha256':hashlib.sha256(data).hexdigest(),'encoding':'cp1252','delimiter':';'},
        'raw':{'tuscany':{'capacity':capacity,'children3to36Months':children}},'municipalReconciliation':proof,'qualityGate':{'status':'PASS','errors':[],'publicReconciliation':'7/7 exact capacity and denominator pairs','regionalRow':'unique explicit Tuscany total; 273 municipal rows; Union rows not summed'},
        'benchmarks':{'earlyChildhoodPotentialCapacityRate':{'year':'2024/25','unit':'percent','tuscany':capacity/children*100,'italy':None}},
        'scope':{'note':'Totale regionale esplicito 2024/25: 28.077 posti potenziali / 59.052 bambini di 3–36 mesi × 100. Include nidi e servizi integrativi; non è l’Indicatore di Lisbona. Italia non disponibile nella fonte regionale; celle vuote e righe delle Unioni non sono trasformate in zero né sommate due volte.'}}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--water-csv',type=Path); parser.add_argument('--water-pdf',type=Path); parser.add_argument('--infancy-csv',type=Path)
    args=parser.parse_args()
    wc=args.water_csv.read_bytes() if args.water_csv else download(WATER_DATA,'application/vnd.sdmx.data+csv;version=1.0.0')
    wp=args.water_pdf.read_bytes() if args.water_pdf else download(WATER_TABLE,'application/pdf')
    infancy_url=json.loads((ROOT/'data/source-snapshots/welfare-prima-infanzia-2026-08.json').read_text())['sources']['earlyChildhoodPotentialCapacityRate']['url']
    ic=args.infancy_csv.read_bytes() if args.infancy_csv else download(infancy_url,'text/csv')
    payload={'water':acquire_water(wc,wp),'infancy':acquire_infancy(ic)}
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print('Candidates PASS: water (Tuscany/Italy 2018), infancy capacity rate (Tuscany 2024/25); 7/7 components reconciled. Not ACQUIRED until publication gate.')

if __name__=='__main__': main()
