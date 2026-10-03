#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/'data/source-snapshots/toscana-indicatori-v1.5.0.json'
SERV=ROOT/'data/source-snapshots/regione-toscana-servizi-online-2018-2022.json'
URL='https://www.regione.toscana.it/documents/d/guest/indicatori-2024-1'
TARGETS={
 'youthOtherStatus':('ind05','percent','2024'),
 'foreignBornSoleProprietorShare':('ind10','percent','2024'),
 'emsResponseTimeP75':('ind14','minutes','2024'),
 'disability064Per1000':('ind16','per1000','2024'),
 'municipalOnlineServicesAdvanced':('ind18','percent','2022'),
 'innovationBusinessShare':('ind19','percent','2024'),
 'organicAgriculturalAreaShare':('ind20','percent','2024'),
}
TOWNS={'046005':'Camaiore','046013':'Forte dei Marmi','046018':'Massarosa','046024':'Pietrasanta','046028':'Seravezza','046030':'Stazzema','046033':'Viareggio'}

def norm(v:Any)->str:
 s=str(v or '').strip().casefold()
 s=s.replace('\ufeff','')
 return re.sub(r'\s+',' ',s)

def parse_num(v:Any)->float|None:
 if v is None: return None
 s=str(v).strip().replace('\u00a0','').replace(' ','')
 if not s or s.casefold() in {'na','n.d.','nd','null','-'}: return None
 s=s.replace('%','')
 if ',' in s and '.' in s:
  if s.rfind(',')>s.rfind('.'): s=s.replace('.','').replace(',','.')
  else: s=s.replace(',','')
 elif ',' in s: s=s.replace(',','.')
 try:
  x=float(s); return x if math.isfinite(x) else None
 except Exception: return None

def decode(blob:bytes)->str:
 for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
  try:
   t=blob.decode(enc)
   if '\n' in t: return t
  except UnicodeDecodeError: pass
 raise RuntimeError('CSV regionale non decodificabile')

def parse(blob:bytes):
 text=decode(blob)
 sample=text[:50000]
 try: delim=csv.Sniffer().sniff(sample,delimiters=';,|\t').delimiter
 except csv.Error: delim=';'
 rows=list(csv.DictReader(io.StringIO(text),delimiter=delim))
 if not rows: raise RuntimeError('CSV regionale vuoto')
 return rows,delim,list(rows[0].keys())

def is_tuscany_row(row:dict[str,str])->bool:
 vals=[norm(v) for v in row.values()]
 return any(v in {'toscana','regione toscana'} or v.startswith('toscana ') for v in vals)

def code_of_row(row:dict[str,str])->str:
 for k,v in row.items():
  nk=norm(k)
  if 'codistat' in nk.replace(' ','') or ('codice' in nk and ('istat' in nk or 'comune' in nk)):
   d=''.join(re.findall(r'\d',str(v or '')))
   if 1<=len(d)<=6: return d.zfill(6)
 for v in row.values():
  d=''.join(re.findall(r'\d',str(v or '')))
  if len(d)==6 and d.startswith('046'): return d
 return ''

def wide_value(row:dict[str,str],source_code:str)->float|None:
 target=source_code.casefold()
 for k,v in row.items():
  nk=re.sub(r'[^a-z0-9]+','',norm(k))
  if nk==target or nk.startswith(target+'_') or nk.endswith('_'+target):
   x=parse_num(v)
   if x is not None: return x
 return None

def long_value(rows:list[dict[str,str]],source_code:str)->float|None:
 hits=[]
 for row in rows:
  if not is_tuscany_row(row): continue
  vals=[norm(v) for v in row.values()]
  if source_code.casefold() not in vals: continue
  nums=[]
  for k,v in row.items():
   nk=norm(k)
   if any(token in nk for token in ('anno','codice','codistat','istat','id')): continue
   x=parse_num(v)
   if x is not None: nums.append((k,x))
  if len(nums)==1: hits.append(nums[0][1])
  else:
   preferred=[x for k,x in nums if any(t in norm(k) for t in ('valore','value','indicatore'))]
   if len(preferred)==1: hits.append(preferred[0])
 if len(hits)==1:return hits[0]
 return None

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
 r=requests.get(URL,timeout=180,headers={'User-Agent':'OsservatorioVersilia-A3-ToscanaIndicators/1.0'})
 r.raise_for_status(); rows,delim,headers=parse(r.content)
 regional=[row for row in rows if is_tuscany_row(row)]
 snap=json.loads(SNAP.read_text(encoding='utf-8')); serv=json.loads(SERV.read_text(encoding='utf-8'))
 benchmarks={}; errors=[]; municipal={}
 for metric,(src,unit,year) in TARGETS.items():
  value=None
  for row in regional:
   value=wide_value(row,src)
   if value is not None: break
  if value is None: value=long_value(rows,src)
  if value is None:
   errors.append(f'{metric}/{src}: valore Toscana non trovato')
  else:
   benchmarks[metric]={'sourceCode':src,'year':year,'unit':unit,'tuscany':value,'italy':None}
  # Reconcile 7 municipal current values where the same file exposes them.
  expected={}
  if metric=='municipalOnlineServicesAdvanced':
   for town,detail in (serv.get('towns') or {}).items():
    v=detail.get('2022')
    if v is not None: expected[town]=float(v)
  else:
   m=(snap.get('indicators') or {}).get(metric) or {}
   for item in m.get('rows') or []:
    years=item.get('years') or []; vals=item.get('values') or []
    if years and vals and len(years)==len(vals): expected[item['town']]=float(vals[-1])
  compared=0; mismatches=[]
  for row in rows:
   c=code_of_row(row)
   if c not in TOWNS: continue
   got=wide_value(row,src)
   if got is None: continue
   town=TOWNS[c]
   if town in expected:
    compared+=1
    if not math.isclose(got,expected[town],rel_tol=0,abs_tol=1e-8):
     mismatches.append(f'{town}: {got} != {expected[town]}')
  municipal[metric]={'expectedRows':len(expected),'comparedRows':compared,'mismatches':mismatches}
  # If wide municipal rows are present, they must reconcile completely; long-format source is allowed to skip this check here.
  if compared and (compared!=len(expected) or mismatches): errors.append(f'{metric}: municipal reconciliation {compared}/{len(expected)} mismatches={mismatches[:3]}')
 gate='PASS' if len(benchmarks)==len(TARGETS) and not errors else 'FAIL'
 payload={
  'schemaVersion':1,'publisher':'Regione Toscana — Indicatori comunali per le politiche locali',
  'profileId':'regione-toscana-indicatori-comunali','status':'ACQUIRED_CANDIDATE' if gate=='PASS' else 'CANDIDATE_REJECTED',
  'source':{'url':URL,'bytes':len(r.content),'delimiter':delim,'headers':headers},
  'regionalRowCount':len(regional),'benchmarks':benchmarks,'municipalReconciliation':municipal,
  'qualityGate':{'status':gate,'errors':errors},
  'note':'Italia resta n.d.: la fonte regionale rende disponibile il confronto Toscana, non un valore nazionale semanticamente omogeneo.',
 }
 p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':payload['status'],'regionalRows':len(regional),'benchmarks':benchmarks,'errors':errors},ensure_ascii=False))
if __name__=='__main__': main()
