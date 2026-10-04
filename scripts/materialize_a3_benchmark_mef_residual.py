#!/usr/bin/env python3
from __future__ import annotations
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'data/site-data.json'; SNAP=ROOT/'data/source-snapshots/a3-mef-taxpayers-benchmark-2024.json'; LOCAL=ROOT/'data/source-snapshots/mef-income-lotto-a-2024.json'
REF='data/source-snapshots/a3-mef-taxpayers-benchmark-2024.json'; KEY='taxpayersAdultPopulationRate'
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def close(a,b,label,tol=1e-10):
 if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=tol): raise RuntimeError(f'{label}: {a} != {b}')
def main():
 site=load(SITE); snap=load(SNAP); local=load(LOCAL)
 gate=snap.get('qualityGate') or {}
 if gate.get('status')!='PASS' or gate.get('publicReconciliation')!='7/7 PASS': raise RuntimeError('MEF taxpayer gate non PASS')
 b=snap['benchmarks'][KEY]
 for scope in ('tuscany','italy'):
  raw=b['raw'][scope]; expected=float(raw['taxpayers'])/float(raw['adultPopulation2026'])*100; close(b[scope],expected,f'{scope}/formula')
 m=site['metrics'][KEY]
 if m['meta'].get('unit')!='per100': raise RuntimeError('taxpayersAdultPopulationRate unità inattesa')
 rows={r['town']:r for r in m.get('rows',[])}
 if set(rows)!=set(local['towns']) or len(rows)!=7: raise RuntimeError('taxpayersAdultPopulationRate perimetro non 7/7')
 for town,d in local['towns'].items():
  expected=float(d['taxpayers'])/float(d['adultPopulation2026'])*100; close(rows[town]['value'],expected,town)
 m['meta']['benchmark']={'year':b['year'],'tuscany':float(b['tuscany']),'italy':float(b['italy']),'source':'Dipartimento delle Finanze — MEF / Istat POSAS','url':m.get('sourceUrl') or snap['source']['mef'],'sourceSnapshot':REF,'note':'Contribuenti MEF rapportati ai residenti 18+ Istat; Toscana e Italia calcolate come rapporto tra numeratore e denominatore aggregati.'}
 SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('A3 benchmark MEF contribuenti/adulti: 1 metrica Toscana/Italia materializzata; gate 1/1 × 7/7 PASS.')
if __name__=='__main__': main()
