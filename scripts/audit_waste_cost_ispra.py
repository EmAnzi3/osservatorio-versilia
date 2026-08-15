#!/usr/bin/env python3
"""Audit ISPRA 2024 municipal waste-service costs for the seven Versilia towns."""
from __future__ import annotations

import argparse, csv, io, json, re, unicodedata, urllib.parse, urllib.request
from pathlib import Path

PAGE='https://www.catasto-rifiuti.isprambiente.it/index.php?pg=downloadcosticomune'
TOWNS={'Camaiore':'09046005','Forte dei Marmi':'09046013','Massarosa':'09046018','Pietrasanta':'09046024','Seravezza':'09046028','Stazzema':'09046030','Viareggio':'09046033'}
UA={'User-Agent':'OsservatorioVersilia-data-audit/1.0'}


def fetch(url: str) -> bytes:
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=90) as r: return r.read()


def decode(raw: bytes) -> str:
    for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
        try:return raw.decode(enc)
        except UnicodeDecodeError:pass
    raise RuntimeError('encoding ISPRA non riconosciuto')


def norm(v: str) -> str:
    v=unicodedata.normalize('NFKD',v or '')
    v=''.join(c for c in v if not unicodedata.combining(c)).lower().strip()
    return re.sub(r'[^a-z0-9]+',' ',v).strip()


def candidate_urls(html: str) -> list[str]:
    # Links may be anchors, form actions or JS window locations. Capture any URL-like
    # token containing csv/download and 2024, then resolve relative references.
    tokens=re.findall(r'''["']([^"']+)["']''',html)
    out=[]
    for token in tokens:
        low=token.lower()
        if '2024' not in low: continue
        if not any(x in low for x in ('.csv','download','costi')): continue
        url=urllib.parse.urljoin(PAGE,token.replace('&amp;','&'))
        if url not in out: out.append(url)
    return out


def parse_csv(raw: bytes) -> tuple[list[str],list[dict]]:
    text=decode(raw)
    sample=text[:12000]
    try: delim=csv.Sniffer().sniff(sample,delimiters=';,|\t').delimiter
    except csv.Error: delim=';'
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    return reader.fieldnames or [],list(reader)


def detect_kind(headers:list[str]) -> str|None:
    n=' | '.join(norm(h) for h in headers)
    if 'ctotab' in n or 'euro abitante' in n or 'euro ab' in n:return 'perResident'
    if 'ctotkg' in n or 'eurocent' in n or 'kg anno' in n:return 'perKg'
    return None


def field(headers:list[str],*needles:str)->str|None:
    for h in headers:
        n=norm(h)
        if any(norm(x)==n for x in needles):return h
    for h in headers:
        n=norm(h)
        if any(norm(x) in n for x in needles):return h
    return None


def parse_num(v:str)->float|None:
    s=(v or '').strip().replace('\u00a0','').replace(' ','')
    if not s or s in {'-','n.d.','nd'}:return None
    if ',' in s and '.' in s:s=s.replace('.','').replace(',','.')
    elif ',' in s:s=s.replace(',','.')
    try:return float(s)
    except ValueError:return None


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('/tmp/ispra-waste-cost.json'));args=p.parse_args()
    html=decode(fetch(PAGE));urls=candidate_urls(html)
    if not urls:
        # Preserve a compact diagnostic rather than guessing a hidden endpoint.
        snippets=[line.strip() for line in html.splitlines() if '2024' in line or 'csv' in line.lower()]
        raise RuntimeError('nessun URL download 2024 individuato; contesto='+repr(snippets[:30]))
    datasets={}
    diagnostics=[]
    for url in urls:
        try:
            raw=fetch(url);headers,rows=parse_csv(raw);kind=detect_kind(headers)
            diagnostics.append({'url':url,'headers':headers[:30],'rows':len(rows),'kind':kind})
            if kind and rows:datasets.setdefault(kind,(url,headers,rows))
        except Exception as exc:
            diagnostics.append({'url':url,'error':f'{type(exc).__name__}: {exc}'})
    if 'perResident' not in datasets:
        raise RuntimeError('dataset CTOTab 2024 non identificato: '+json.dumps(diagnostics,ensure_ascii=False)[:6000])
    towns={t:{'ctotPerResident':None,'ctotPerKg':None} for t in TOWNS}
    for kind,(url,headers,rows) in datasets.items():
        code_h=field(headers,'istat','codice istat','codice comune');town_h=field(headers,'comune','denominazione comune')
        datum_h=field(headers,'dato riferito a')
        value_h=field(headers,'ctotab') if kind=='perResident' else field(headers,'ctotkg')
        if value_h is None:
            # Last resort on descriptive labels.
            value_h=field(headers,'costo totale','costi totali')
        if not value_h:raise RuntimeError(f'{kind}: colonna CTOT non trovata in {headers}')
        for row in rows:
            rawcode=re.sub(r'\D','',str(row.get(code_h,''))) if code_h else ''
            name=norm(row.get(town_h,'')) if town_h else ''
            town=next((t for t,c in TOWNS.items() if rawcode.endswith(c)),None)
            if town is None:town=next((t for t in TOWNS if norm(t)==name),None)
            if not town:continue
            if datum_h and norm(row.get(datum_h,'')) not in {'comune',''}:
                raise RuntimeError(f'{town}: dato ISPRA non comunale ({row.get(datum_h)!r})')
            value=parse_num(row.get(value_h,''))
            towns[town]['ctotPerResident' if kind=='perResident' else 'ctotPerKg']=value
    coverage=sum(1 for t in TOWNS if towns[t]['ctotPerResident'] is not None)
    snap={'schemaVersion':1,'year':2024,'source':'ISPRA - Catasto Rifiuti','sourcePage':PAGE,
          'definition':'CTOTab - costo totale del servizio di igiene urbana, euro/abitante/anno',
          'coverage':f'{coverage}/7','datasets':{k:v[0] for k,v in datasets.items()},'towns':towns,'diagnostics':diagnostics}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for town,val in towns.items():print(f"{town}: CTOTab={val['ctotPerResident']} CTOTkg={val['ctotPerKg']}")
    if coverage<6:raise RuntimeError(f'copertura CTOTab insufficiente: {coverage}/7')
    print(f'ISPRA waste-cost audit: {coverage}/7; snapshot={args.out}')

if __name__=='__main__':main()
