#!/usr/bin/env python3
from __future__ import annotations
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'data/site-data.json'; SNAP=ROOT/'data/source-snapshots/a3-istat-geography-benchmark-2021.json'; MUNICIPAL=ROOT/'data/source-snapshots/biometria-comune-v135.json'
REF='data/source-snapshots/a3-istat-geography-benchmark-2021.json'
TARGETS={
 'municipalSurface':('squareKm','surfaceKm2'),
 'populationDensity':('peoplePerSquareKm',None),
 'altitudeProfile':('percent','from300Pct'),
}
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def close(a,b,label,tol=1e-8):
 if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=tol): raise RuntimeError(f'{label}: {a} != {b}')
def main():
 site=load(SITE); snap=load(SNAP); src=load(MUNICIPAL)
 gate=snap.get('qualityGate') or {}
 if gate.get('status')!='PASS' or gate.get('publicSnapshotReconciliation')!='7/7 PASS' or gate.get('municipalityCountItaly')!=7904 or gate.get('municipalityCountTuscany')!=273: raise RuntimeError('Geography benchmark gate non PASS')
 for metric_id,(unit,field) in TARGETS.items():
  m=site['metrics'][metric_id]
  if m['meta'].get('unit')!=unit: raise RuntimeError(f'{metric_id}: unità inattesa')
  rows={r['town']:r for r in m.get('rows',[])}
  if set(rows)!=set(src['municipalities']) or len(rows)!=7: raise RuntimeError(f'{metric_id}: perimetro non 7/7')
  for town,s in src['municipalities'].items():
   if metric_id=='populationDensity':
    pop=next(r for r in site['metrics']['population']['rows'] if r['town']==town)['value']; expected=float(pop)/float(s['surfaceKm2'])
   else: expected=float(s[field])
   close(rows[town]['value'],expected,f'{metric_id}/{town}',.11 if metric_id=='altitudeProfile' else 1e-8)
  b=snap['benchmarks'][metric_id]
  m['meta']['benchmark']={'year':str(b['year']),'tuscany':float(b['tuscany']),'italy':float(b['italy']),'source':'Istat — Principali statistiche geografiche sui comuni','url':m.get('sourceUrl') or snap['source']['altimetry'],'sourceSnapshot':REF,'note':'Toscana e Italia ricalcolate sul perimetro comunale ufficiale; rapporti e quote sono ottenuti su aggregati, non come media semplice.'}
 SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('A3 benchmark geografia: 3 metriche Toscana/Italia materializzate; gate 3/3 × 7/7 PASS.')
if __name__=='__main__': main()
