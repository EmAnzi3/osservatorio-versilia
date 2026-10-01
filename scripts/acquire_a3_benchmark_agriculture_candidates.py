#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/'data/source-snapshots/istat-agricoltura-territorio-2020.json'
BASE='https://esploradati.istat.it/SDMXWS/rest'
TUSCANY_PREFIXES={'045','046','047','048','049','050','051','052','053','100'}
TOWNS={'046005','046013','046018','046024','046028','046030','046033'}
def num(v:Any)->float:
    s=str(v or '').strip().replace(' ','').replace(',','.')
    return float(s) if s else 0.0
def code(row):
    raw=str(row.get('REF_AREA') or '').strip()
    digits=''.join(re.findall(r'\\d',raw))
    if 1<=len(digits)<=6:
        return digits.zfill(6)
    hits=re.findall(r'(?<!\\d)(\\d{6})(?!\\d)',raw)
    return hits[0] if len(hits)==1 else ''
def fetch(flow:str,keys:list[str]):
    errors=[]
    for key in keys:
        urls=[f'{BASE}/data/IT1,{flow},1.0/{key}/all',f'{BASE}/data/{flow}/{key}/IT1']
        for url in urls:
            try:
                r=requests.get(url,params={'startPeriod':'2020','endPeriod':'2020','format':'csvfile'},timeout=300,headers={'User-Agent':'OsservatorioVersilia-A3-agriculture/1.0','Accept':'application/vnd.sdmx.data+csv;version=1.0.0'}); r.raise_for_status()
                text=r.content.decode('utf-8-sig',errors='replace'); rows=list(csv.DictReader(io.StringIO(text)))
                if rows and 'REF_AREA' in rows[0] and 'OBS_VALUE' in rows[0]: return rows,r.url
                errors.append(f'{url}: schema {list(rows[0]) if rows else []}')
            except Exception as exc: errors.append(f'{url}: {type(exc).__name__}: {exc}')
    raise RuntimeError(' | '.join(errors[-8:]))
def unique_by(rows,indicator_field='INDICATOR'):
    out={}
    for r in rows:
        c=code(r)
        if not re.fullmatch(r'\d{6}',c): continue
        ind=str(r.get(indicator_field) or '').strip()
        if not ind: continue
        key=(c,ind); value=num(r.get('OBS_VALUE'))
        if key in out and not math.isclose(out[key],value,abs_tol=1e-9): raise RuntimeError(f'duplicato {key}: {out[key]} != {value}')
        out[key]=value
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    snap=json.loads(SNAP.read_text(encoding='utf-8'))['towns']
    surf,surf_url=fetch('DF_DCAT_CENSAGRIC2020_SURF_ALL',['A..HO+ARU+FUAA'])
    irr,irr_url=fetch('DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS',['A..IA'])
    loc,loc_url=fetch('DF_DCAT_CENSAGRIC2020_UA_CROPS_2',['A..ARU.ALL.TOT','A..ARU.ALL'])
    s=unique_by(surf); i=unique_by(irr); l={}
    for r in loc:
        c=code(r)
        if not re.fullmatch(r'\d{6}',c): continue
        ind=str(r.get('INDICATOR') or '').strip(); crop=str(r.get('TYPE_OF_CROP') or r.get('CROP') or '').strip()
        if ind!='ARU' or (crop and crop!='ALL'): continue
        key=(c,'ARU'); value=num(r.get('OBS_VALUE'))
        if key in l and not math.isclose(l[key],value,abs_tol=1e-9): raise RuntimeError(f'localized duplicate {c}')
        l[key]=value
    codes={c for c,_ in s}&{c for c,_ in i}&{c for c,_ in l}; required_s={'HO','ARU','FUAA'}
    complete={c for c in codes if all((c,k) in s for k in required_s) and (c,'IA') in i and (c,'ARU') in l}
    if not 7500<=len(complete)<=8000: raise RuntimeError(f'copertura nazionale inattesa {len(complete)}')
    tus={c for c in complete if c[:3] in TUSCANY_PREFIXES}
    if not 260<=len(tus)<=280: raise RuntimeError(f'copertura Toscana inattesa {len(tus)}')
    errors=[]
    for c in TOWNS:
        r=snap[c]; checks={'farms':s.get((c,'HO')),'sauCenterHa':s.get((c,'ARU')),'farmsWithSau':s.get((c,'FUAA')),'sauLocalizedHa':l.get((c,'ARU')),'irrigatedAreaHa':i.get((c,'IA'))}
        for k,v in checks.items():
            if v is None or not math.isclose(float(v),float(r[k]),abs_tol=.02): errors.append(f'{c}/{k}: {v} != {r[k]}')
    def scope(cs:set[str]):
        farms=sum(s[(c,'HO')] for c in cs); center=sum(s[(c,'ARU')] for c in cs); fsau=sum(s[(c,'FUAA')] for c in cs); localized=sum(l[(c,'ARU')] for c in cs); irrig=sum(i[(c,'IA')] for c in cs)
        return {'municipalities':len(cs),'farms':farms,'sauCenterHa':center,'farmsWithSau':fsau,'sauLocalizedHa':localized,'irrigatedAreaHa':irrig,'averageFarmSizeHa':center/fsau}
    scopes={'tuscany':scope(tus),'italy':scope(complete)}
    benchmarks={
      'agriculturalFarms':{'year':2020,'unit':'number','tuscany':scopes['tuscany']['farms'],'italy':scopes['italy']['farms']},
      'agriculturalUsedArea':{'year':2020,'unit':'hectares','tuscany':scopes['tuscany']['sauLocalizedHa'],'italy':scopes['italy']['sauLocalizedHa']},
      'averageAgriculturalFarmSize':{'year':2020,'unit':'hectaresPerFarm','tuscany':scopes['tuscany']['averageFarmSizeHa'],'italy':scopes['italy']['averageFarmSizeHa']},
      'irrigatedAgriculturalArea':{'year':2020,'unit':'hectares','tuscany':scopes['tuscany']['irrigatedAreaHa'],'italy':scopes['italy']['irrigatedAreaHa']}
    }
    gate={'status':'PASS' if not errors else 'FAIL','publicSnapshotReconciliation':'4 metrics × 7/7 PASS' if not errors else 'FAIL','municipalityCountItaly':len(complete),'municipalityCountTuscany':len(tus),'errors':errors}
    payload={'schemaVersion':1,'publisher':'Istat — 7° Censimento generale dell’agricoltura 2020','profileId':'istat-agriculture-census-2020','referenceYear':2020,'status':'ACQUIRED_CANDIDATE' if not errors else 'CANDIDATE_REJECTED','sources':{'surface':surf_url,'localizedSau':loc_url,'irrigation':irr_url},'method':'Toscana/Italia ottenute sommando i conteggi/ettari comunali omogenei. Dimensione media = Σ SAU aziende con centro / Σ aziende con SAU; nessuna media semplice.','benchmarks':benchmarks,'scopes':scopes,'qualityGate':gate,'notYetMaterialized':{'cropProfile':'richiede gate esplicito sulla componente selezionata','agriculturalRenewalAndLeadership':'worker SDMX Agricoltura II separato','agriculturalDiversificationAndModernization':'worker SDMX Agricoltura II separato'}}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':payload['status'],'metrics':list(benchmarks),'gate':gate},ensure_ascii=False))
if __name__=='__main__': main()
