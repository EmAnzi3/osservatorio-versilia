#!/usr/bin/env python3
"""Extract municipal self-service petrol/diesel medians from MIMIT daily open data."""
from __future__ import annotations

import argparse, csv, io, json, re, statistics, unicodedata, urllib.request
from pathlib import Path

ANAG = 'https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv'
PRICES = 'https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv'
TOWNS = ['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']
FUELS = {'benzina': 'Benzina self', 'gasolio': 'Gasolio self'}
UA = {'User-Agent': 'OsservatorioVersilia-data-audit/1.0'}


def fetch(url: str) -> str:
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read()
    for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    raise RuntimeError('encoding MIMIT non riconosciuto')


def norm(v: str) -> str:
    v=unicodedata.normalize('NFKD',v or '')
    v=''.join(c for c in v if not unicodedata.combining(c)).lower().strip()
    return re.sub(r'[^a-z0-9]+',' ',v).strip()


def parse_export(text: str) -> tuple[str|None,list[dict]]:
    lines=text.splitlines()
    date=None
    for line in lines[:5]:
        m=re.search(r'(20\d{2}[-/]\d{2}[-/]\d{2}|\d{2}/\d{2}/20\d{2})',line)
        if m:
            date=m.group(1)
            if '/' in date:
                d,mn,y=date.split('/'); date=f'{y}-{mn}-{d}'
            break
    header_index=next((i for i,line in enumerate(lines) if 'idimpianto' in norm(line)),None)
    if header_index is None: raise RuntimeError('header idimpianto non trovato')
    reader=csv.DictReader(io.StringIO('\n'.join(lines[header_index:])),delimiter='|')
    return date,list(reader)


def find_field(row: dict,*names: str) -> str:
    mapping={norm(k):k for k in row}
    for name in names:
        if norm(name) in mapping: return mapping[norm(name)]
    for n,k in mapping.items():
        if any(norm(name) in n for name in names): return k
    raise RuntimeError(f'campo non trovato: {names}; disponibili={list(row)}')


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,default=Path('/tmp/mimit-fuel.json')); args=p.parse_args()
    anag_date,anag=parse_export(fetch(ANAG)); price_date,prices=parse_export(fetch(PRICES))
    if not anag or not prices: raise RuntimeError('dataset MIMIT vuoto')
    aid=find_field(anag[0],'idimpianto'); atown=find_field(anag[0],'Comune'); aprov=find_field(anag[0],'Provincia')
    pid=find_field(prices[0],'idimpianto'); pfuel=find_field(prices[0],'descCarburante'); pprice=find_field(prices[0],'prezzo'); pself=find_field(prices[0],'isSelf')
    wanted={norm(t):t for t in TOWNS}
    station_town={}
    for row in anag:
        town=wanted.get(norm(row.get(atown,'')))
        if not town: continue
        province=norm(row.get(aprov,''))
        if province not in {'lu','lucca'} and 'lucca' not in province: continue
        station_town[str(row.get(aid,'')).strip()]=town
    values={town:{fuel:[] for fuel in FUELS} for town in TOWNS}
    seen=set()
    for row in prices:
        station=str(row.get(pid,'')).strip(); town=station_town.get(station)
        if not town: continue
        if str(row.get(pself,'')).strip() not in {'1','1.0'}: continue
        fuel=norm(row.get(pfuel,''))
        if fuel not in FUELS: continue
        try: price=float(str(row.get(pprice,'')).strip().replace(',','.'))
        except ValueError: continue
        if not 0.5 <= price <= 5: continue
        key=(station,fuel)
        if key in seen: continue
        seen.add(key); values[town][fuel].append(price)
    towns={}; covered=0
    for town in TOWNS:
        fuels={}
        for fuel,label in FUELS.items():
            vals=values[town][fuel]
            fuels[fuel]={
                'label':label,
                'median':round(statistics.median(vals),3) if vals else None,
                'stationCount':len(vals),
                'min':round(min(vals),3) if vals else None,
                'max':round(max(vals),3) if vals else None,
            }
        available=all(fuels[f]['median'] is not None for f in FUELS)
        if available: covered+=1
        towns[town]={'available':available,'fuels':fuels}
        print(f"{town}: benzina={fuels['benzina']['median']} ({fuels['benzina']['stationCount']}), gasolio={fuels['gasolio']['median']} ({fuels['gasolio']['stationCount']})")
    # Stazzema is intentionally allowed to be n.d.; all other six must have both fuels.
    expected=[t for t in TOWNS if t!='Stazzema']
    missing=[t for t in expected if not towns[t]['available']]
    snapshot={
        'schemaVersion':1,'source':'MIMIT - Prezzi praticati e anagrafica impianti',
        'sourceUrls':{'anagrafica':ANAG,'prezzi':PRICES},
        'referenceDate':price_date or anag_date,'statistic':'mediana comunale impianti attivi, self-service',
        'coverage':f'{covered}/7','towns':towns,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if missing: raise RuntimeError(f'copertura insufficiente nei sei comuni attesi: {missing}')
    print(f'Fuel audit OK: {covered}/7; Stazzema n.d. ammesso; snapshot={args.out}')

if __name__=='__main__': main()
