#!/usr/bin/env python3
"""Probe official MEF 2025 TARI documents for Forte dei Marmi and Pietrasanta.

This is deliberately conservative: it records document text and only promotes a
3-person tariff candidate when a recognisable domestic-tariff row can be parsed.
Unresolved municipalities remain n.d.; the script never guesses from another year.
"""
from __future__ import annotations

import argparse, io, json, re, urllib.parse, urllib.request
from pathlib import Path
from pypdf import PdfReader

BASE='https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/'
RESULT=BASE+'risultato.htm?DOWNLOAD=Procedi&annosel=2025&cc={code}&lista=1&pagina=sceltaregione.htm&r=2&tipo_trib=tutti'
TOWNS={'Forte dei Marmi':'D730','Pietrasanta':'G628'}
UA={'User-Agent':'OsservatorioVersilia-data-audit/1.0'}


def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()


def extract(pdf:bytes)->str:
    reader=PdfReader(io.BytesIO(pdf));chunks=[]
    for page in reader.pages:
        try:chunks.append(page.extract_text(extraction_mode='layout') or '')
        except TypeError:chunks.append(page.extract_text() or '')
    return '\n'.join(chunks)


def pdf_links(html:str,page_url:str)->list[str]:
    hrefs=re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',html,flags=re.I)
    out=[]
    for href in hrefs:
        url=urllib.parse.urljoin(page_url,href.replace('&amp;','&'))
        if url not in out:out.append(url)
    return out


def parse_it(v:str)->float:
    return float(v.replace('.','').replace(',','.'))


def candidate(text:str)->dict|None:
    # Restrict the search to a domestic-tariff section and require an explicit
    # 3-person/component row. Two values must follow the occupancy marker.
    clean=text.replace('\xa0',' ')
    anchors=[m.start() for m in re.finditer(r'utenze\s+domestiche|tariffe\s+utenze\s+domestiche',clean,flags=re.I)]
    sections=[]
    for pos in anchors:
        sections.append(clean[pos:pos+7000])
    if not sections:sections=[clean]
    patterns=[
        r'(?im)^\s*3\s+(?:componenti?|comp\.?|occupanti)?\s*([0-9]+[,.][0-9]+)\s+([0-9]+[,.][0-9]+)\s*$',
        r'(?im)^\s*(?:3\s+componenti?|3\s+occupanti|nucleo\s+3).*?([0-9]+[,.][0-9]+).*?([0-9]+[,.][0-9]+)\s*$',
    ]
    for section in sections:
        for pattern in patterns:
            m=re.search(pattern,section)
            if not m:continue
            fixed=parse_it(m.group(1));variable=parse_it(m.group(2))
            # Domestic fixed rate is €/m2 and variable normally €/year. Guard
            # against accidentally parsing Ka/Kb coefficients or totals.
            if 0.05 <= fixed <= 10 and 10 <= variable <= 1000:
                return {'fixedPerSqm':fixed,'variablePerYear':variable,'matchedLine':m.group(0).strip()}
    return None


def contexts(text:str)->list[str]:
    lines=[re.sub(r'\s+',' ',line).strip() for line in text.splitlines()]
    keep=[]
    for i,line in enumerate(lines):
        low=line.lower()
        if ('domestic' in low or 'component' in low or 'occupant' in low or 'tariff' in low) and line:
            start=max(0,i-2);end=min(len(lines),i+6)
            block=' | '.join(x for x in lines[start:end] if x)
            if block and block not in keep:keep.append(block)
    return keep[:30]


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('/tmp/tari-2025-missing.json'));args=p.parse_args()
    towns={}
    for town,code in TOWNS.items():
        page=RESULT.format(code=code);html=fetch(page).decode('utf-8',errors='replace');docs=pdf_links(html,page)
        result={'sourcePage':page,'documents':[],'candidate':None}
        for doc in docs:
            try:
                text=extract(fetch(doc));cand=candidate(text)
                result['documents'].append({'url':doc,'candidate':cand,'contexts':contexts(text)})
                if cand and result['candidate'] is None:
                    result['candidate']={**cand,'sourcePdf':doc}
            except Exception as exc:
                result['documents'].append({'url':doc,'error':f'{type(exc).__name__}: {exc}'})
        towns[town]=result
        print(f'{town}: documents={len(docs)} candidate={result["candidate"]}')
        if result['candidate'] is None:
            for doc in result['documents']:
                for block in doc.get('contexts',[])[:8]:print('  ',block[:1000])
    snap={'schemaVersion':1,'year':2025,'source':'Dipartimento delle Finanze - MEF / documenti TARI comunali','towns':towns}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'TARI missing-source audit complete; snapshot={args.out}')

if __name__=='__main__':main()
