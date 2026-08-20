#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'audit-artifacts' / 'demography-rcs-samples.json'
TOWN_CODES = {'046005','046013','046018','046024','046028','046030','046033'}
SOURCES = {
    'citizenship_2025': 'https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip',
    'birth_country_2025': 'https://demo.istat.it/data/rcs/Dati_RCS_nascita_2025.zip',
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent':'OsservatorioVersilia-data-audit/1.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def sniff(text: str) -> str:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=';,\t|').delimiter
    except csv.Error:
        counts={s:sample.count(s) for s in (';',',','\t','|')}
        return max(counts,key=counts.get)


def main() -> None:
    report={}
    for key,url in SOURCES.items():
        body=get(url)
        entry={'url':url,'bytes':len(body),'members':[],'tables':[]}
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            entry['members']=z.namelist()
            for name in z.namelist():
                if not name.lower().endswith(('.csv','.txt')):
                    continue
                text=z.read(name).decode('utf-8-sig',errors='replace')
                delimiter=sniff(text)
                rows=list(csv.reader(io.StringIO(text),delimiter=delimiter))
                prefix=rows[:6]
                samples=[]
                found=set()
                for row in rows:
                    joined='|'.join(row)
                    matches=[code for code in TOWN_CODES if code in joined]
                    if not matches:
                        continue
                    for code in matches:
                        found.add(code)
                    if len(samples)<20:
                        samples.append(row)
                    if len(found)==7 and len(samples)>=20:
                        break
                entry['tables'].append({
                    'member':name,'delimiter':delimiter,'prefixRows':prefix,
                    'coverage':len(found),'townCodesFound':sorted(found),'samples':samples,
                })
        report[key]=entry
        print(key,'coverage max',max([t['coverage'] for t in entry['tables']] or [0]),'/ 7')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(OUT)

if __name__=='__main__':
    main()
