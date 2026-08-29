#!/usr/bin/env python3
from pathlib import Path
import re

p=Path('scripts/materialize_ambiente_acqua_v124.py')
s=p.read_text(encoding='utf-8')
s=s.replace('import csv, hashlib, io, json, re, sys, time','import base64, csv, gzip, hashlib, io, json, re, sys, time',1)
new='''def fetch_sisbon():
    fallback=ROOT/"data/source-snapshots/ambiente-acqua-v124-sisbon.json.gz.b64"
    raw=gzip.decompress(base64.b64decode(fallback.read_text(encoding="utf-8").strip()))
    compact=json.loads(raw.decode("utf-8"))
    procedures=[]
    for item in compact:
        code,ident,name,address,contamination,procedure_state,state_code,status_code=item
        procedures.append({
          "townCode":code,"id":ident,"name":name,"address":address,
          "contamination":contamination,"procedureState":procedure_state,
          "stateCode":state_code,"status":"closed" if status_code=="c" else "active",
          "lat":None,"lon":None
        })
    ids=[x["id"] for x in procedures]
    if len(procedures)!=152 or len(set(ids))!=152:
        raise RuntimeError(f"SISBON attesi 152 univoci, trovati {len(procedures)}/{len(set(ids))}")
    counts={}
    for c in TOWNS:
        xs=[x for x in procedures if x["townCode"]==c]
        counts[c]=[sum(x["status"]=="active" for x in xs),sum(x["status"]=="closed" for x in xs)]
    if counts!=EXPECTED_SISBON:
        raise RuntimeError(f"Conteggi SISBON inattesi: {counts}")
    return procedures, "e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb"
'''
pattern=r'def fetch_sisbon\(\):.*?\ndef build_snapshot'
if not re.search(pattern,s,flags=re.S):
    raise SystemExit('fetch_sisbon block not found')
s=re.sub(pattern,new+'\ndef build_snapshot',s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
