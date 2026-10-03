#!/usr/bin/env python3
"""Reconcile FEE's named 2026 beach localities; do not split slash names."""
from __future__ import annotations
import argparse, hashlib, json, re
from html.parser import HTMLParser
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb'

class Listing(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_region=False; self.region=''; self.in_item=False; self.item=''; self.rows=[]
    def handle_starttag(self, tag, attrs):
        if tag=='div' and dict(attrs).get('class')=='regione': self.in_region=True; self.region=''
        if tag=='li': self.in_item=True; self.item=''
    def handle_endtag(self, tag):
        if tag=='div': self.in_region=False
        if tag=='li':
            text=' '.join(self.item.split())
            if self.region and ' - ' in text: self.rows.append((self.region.strip(),text))
            self.in_item=False
    def handle_data(self, text):
        if self.in_region: self.region+=text
        if self.in_item: self.item+=text

def localities(text):
    result=[]; start=0; depth=0
    for index,char in enumerate(text):
        if char=='(': depth+=1
        elif char==')':
            depth-=1
            if depth<0: raise RuntimeError('Unbalanced locality parentheses')
        elif char==',' and depth==0:
            result.append(text[start:index].strip()); start=index+1
    if depth: raise RuntimeError('Unbalanced locality parentheses')
    result.append(text[start:].strip())
    if any(not name for name in result): raise RuntimeError('Empty locality; no inference allowed')
    return result

def normalize(text): return ' '.join(text.split()).casefold()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    response=requests.get(URL,timeout=90);response.raise_for_status()
    if not re.search(r"Bandiere blu dell.anno\s*2026", response.text, re.I): raise RuntimeError('2026 listing not verified')
    listing=Listing();listing.feed(response.text)
    if not listing.rows: raise RuntimeError('FEE listing empty')
    records=[];seen=set()
    for region,text in listing.rows:
        town,names=text.split(' - ',1)
        key=(region,normalize(town))
        if key in seen:raise RuntimeError(f'Duplicate FEE town: {key}')
        seen.add(key)
        names=localities(names)
        records.append({'region':region.removeprefix('Regione '),'town':town,'localities':names,
            'revoked':any('REVOCAT' in name.upper() for name in names)})
    public=json.loads((ROOT/'data/site-data.json').read_text())['metrics']['blueFlagBeaches']
    if public['meta']['unit']!='number' or public['meta']['year']!='2026':raise RuntimeError('FEE public contract mismatch')
    if len(public['rows'])!=7 or len({x['code'] for x in public['rows']})!=7:raise RuntimeError('FEE public perimeter mismatch')
    reconciliation={}
    for row in public['rows']:
        matches=[x for x in records if x['region']=='Toscana' and normalize(x['town'])==normalize(row['town'])]
        if row.get('notApplicable') is True:
            if row.get('value') is not None or matches:raise RuntimeError('FEE n.a. mismatch')
            reconciliation[row['code']]={'notApplicable':True};continue
        if len(matches)!=1 or matches[0]['revoked']:raise RuntimeError('FEE coastal town missing/revoked')
        source=matches[0]['localities'];expected=row.get('coastDetail',{}).get('localities2026') or []
        if len(source)!=row['value'] or {normalize(x) for x in source}!={normalize(x) for x in expected}:
            raise RuntimeError(f"FEE {row['town']}: locality names/count mismatch")
        reconciliation[row['code']]={'localities':source,'value':len(source)}
    active=[x for x in records if not x['revoked']]
    totals={'tuscany':sum(len(x['localities']) for x in active if x['region']=='Toscana'),
        'italy':sum(len(x['localities']) for x in active)}
    payload={'schemaVersion':2,'profileId':'fee-blue-flag-annual','publisher':'FEE Italia — Programma Bandiera Blu',
        'sourceUrl':URL,'sourceSha256':hashlib.sha256(response.content).hexdigest(),'status':'ACQUIRED_CANDIDATE',
        'scope':{'year':2026,'listedMunicipalities':len(records),'activeMunicipalities':len(active),
            'note':'Elenco nazionale FEE spiagge, incluse acque interne; località separate da virgole esterne alle parentesi, barre conservate; riconoscimenti revocati esclusi.'},
        'benchmarks':{'blueFlagBeaches':{'year':'2026','unit':'number',**totals}},'records':records,
        'municipalReconciliation':reconciliation,'qualityGate':{'status':'PASS','publicReconciliation':'4 coastal + 3 n.a. PASS',
            'regionalNationalControl':'Complete official FEE region/locality listing; revoked entries excluded','errors':[]}}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':payload['status'],'benchmarks':payload['benchmarks'],'scope':payload['scope']}))

if __name__=='__main__':main()
