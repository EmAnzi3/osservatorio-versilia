#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
import requests

API='https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action/package_search'
KNOWN={
 'entrata_toscana':'4dbef43d-72fa-4fe2-a716-45986be658f2',
 'spesa_toscana':'74533d22-b1c2-4d89-b1b9-b98e6c9713ff',
}
QUERIES=[
 '2025 SIOPE Movimenti cumulati mensili di Entrata',
 '2025 SIOPE Movimenti cumulati mensili di Spesa',
 '2025 SIOPE Movimenti cumulati',
]

def slim_package(p:dict[str,Any])->dict[str,Any]:
    return {
      'id':p.get('id'),'name':p.get('name'),'title':p.get('title'),
      'organization':(p.get('organization') or {}).get('title'),
      'resources':[{
        'id':r.get('id'),'name':r.get('name'),'format':r.get('format'),
        'url':r.get('url'),'datastore_active':r.get('datastore_active')
      } for r in (p.get('resources') or [])],
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    s=requests.Session(); s.headers['User-Agent']='OsservatorioVersilia-A3-SIOPE/1.0'
    results=[]; errors=[]
    seen=set()
    for q in QUERIES:
        try:
            r=s.get(API,params={'q':q,'rows':100},timeout=120); r.raise_for_status()
            body=r.json()
            for p in ((body.get('result') or {}).get('results') or []):
                pid=str(p.get('id') or '')
                if not pid or pid in seen: continue
                title=str(p.get('title') or '')
                if '2025' not in title or 'SIOPE' not in title.upper(): continue
                seen.add(pid); results.append(slim_package(p))
        except Exception as exc:
            errors.append(f'{q}: {type(exc).__name__}: {exc}')
    titles=[str(p.get('title') or '') for p in results]
    entrata=[p for p in results if 'Entrata' in str(p.get('title') or '')]
    spesa=[p for p in results if 'Spesa' in str(p.get('title') or '')]
    national=[p for p in results if any(token in str(p.get('title') or '').casefold() for token in ('italia','nazionale','totale'))]
    known_found={k:any(p.get('id')==v for p in results) for k,v in KNOWN.items()}
    payload={
      'schemaVersion':1,'profileId':'siope-monthly','referenceYear':2025,
      'status':'SOURCE_DIAGNOSTIC_READY',
      'catalogueApi':API,'queries':QUERIES,'errors':errors,
      'packageCount':len(results),'entrataCount':len(entrata),'spesaCount':len(spesa),
      'knownTuscanyResourcesFound':known_found,
      'nationalCandidates':national,
      'packages':results,
      'goal':'Individuare risorse nazionali oppure il set completo regionale 2025 per aggregare Toscana/Italia da movimenti SIOPE, senza mediare i sette Comuni.',
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':payload['status'],'packages':len(results),'entrata':len(entrata),'spesa':len(spesa),'national':len(national),'knownFound':known_found},ensure_ascii=False))
if __name__=='__main__': main()
