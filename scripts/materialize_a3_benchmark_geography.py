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

def materialize_statistical_coastline(site):
 snapshot_path=ROOT/'data/source-snapshots/a3-istat-coastline-benchmark-2021.json'
 if not snapshot_path.exists(): return
 snap=load(snapshot_path)
 if snap.get('qualityGate',{}).get('status')!='PASS' or snap['qualityGate'].get('errors')!=[]:
  raise RuntimeError('Istat coastline benchmark gate non PASS')
 records=snap.get('records') or []
 if len(records)!=snap.get('scope',{}).get('municipalityRecords') or not records:
  raise RuntimeError('Istat coastline: incomplete official DBF records')
 if sum(r['region']==9 for r in records)!=snap['scope'].get('tuscanyRecords'):
  raise RuntimeError('Istat coastline: incomplete Tuscany records')
 codes=[r['code'] for r in records]
 if len(set(codes))!=len(codes): raise RuntimeError('Istat coastline: duplicate codes')
 for row in records:
  if isinstance(row['lengthKm'],bool) or not math.isfinite(float(row['lengthKm'])) or float(row['lengthKm'])<=0:
   raise RuntimeError('Istat coastline: invalid length')
 b=snap['benchmarks']['statisticalCoastlineLength']
 if b.get('unit')!='km' or str(b.get('year'))!='2021': raise RuntimeError('Istat coastline: incompatible contract')
 close(b['italy'],math.fsum(float(r['lengthKm']) for r in records),'Italy coastline')
 close(b['tuscany'],math.fsum(float(r['lengthKm']) for r in records if r['region']==9),'Tuscany coastline')
 by_code={r['code']:r for r in records}
 metric=site['metrics']['statisticalCoastlineLength']
 rows=metric.get('rows') or []
 expected_codes=set(snap.get('municipalReconciliation') or {})
 if len(rows)!=7 or len({r['code'] for r in rows})!=7 or {r['code'] for r in rows}!=expected_codes:
  raise RuntimeError('Istat coastline: public perimeter not 7/7')
 for row in rows:
  src=by_code.get(row['code'])
  evidence=snap['municipalReconciliation'][row['code']]
  if evidence.get('notApplicable'):
   if src is not None or row.get('value') is not None or row.get('notApplicable') is not True:
    raise RuntimeError('Istat coastline: n.a. must remain explicit')
  else:
   if src is None or src['region']!=9: raise RuntimeError('Istat coastline: municipal source absent')
   close(row['value'],src['lengthKm'],'Municipal coastline')
 metric['meta']['benchmark']={'year':'2021','tuscany':float(b['tuscany']),'italy':float(b['italy']),
  'source':snap['publisher'],'url':snap['sourceUrl'],
  'sourceSnapshot':str(snapshot_path.relative_to(ROOT)),
  'note':'Somma della linea litoranea statistica ufficiale Istat; 4 Comuni costieri riconciliati e 3 non applicabili. Non equivale alla costa ISPRA.'}
 print('A3 benchmark linea litoranea: Toscana/Italia da DBF completo; 4 costieri + 3 n.a. PASS.')

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
 materialize_statistical_coastline(site)
 SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('A3 benchmark geografia: 3 metriche Toscana/Italia materializzate; gate 3/3 × 7/7 PASS.')
if __name__=='__main__': main()
