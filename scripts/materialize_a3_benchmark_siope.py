#!/usr/bin/env python3
from __future__ import annotations
import json,math
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
SNAP=ROOT/"data/source-snapshots/a3-siope-benchmark-2025.json"
HISTORY=ROOT/"data/source-snapshots/siope-history-v1.6.0.json"
FISCAL=ROOT/"data/source-snapshots/fiscal-lotto-b-2025.json"
REF="data/source-snapshots/a3-siope-benchmark-2025.json"
TARGETS={
 "siopePayments":{"year":"2025","unit":"currency","url":"https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2025","note":"Pagamenti SIOPE 2025 per residente. Toscana ricostruita sull'intero perimetro dei 273 Comuni regionali; Italia n.d. in questo blocco."},
 "currentPayments":{"year":"2025","unit":"currency","url":"https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2025","note":"Pagamenti correnti (Titolo 1) SIOPE 2025 per residente, con lo stesso denominatore SIOPE del contratto pubblico."},
 "capitalPayments":{"year":"2025","unit":"currency","url":"https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_spe_sio_reg09_01_2025","note":"Pagamenti in conto capitale (Titolo 2) SIOPE 2025 per residente, con lo stesso denominatore SIOPE del contratto pubblico."},
 "fiscalRecoveryActivity":{"year":"2025","unit":"currency","url":"https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_ent_sio_reg09_01_2025","note":"Benchmark riferito alla componente predefinita degli incassi riscossi a seguito di attività di verifica e controllo, per residente."},
}

def load(p:Path)->dict[str,Any]:
 v=json.loads(p.read_text(encoding="utf-8"))
 if not isinstance(v,dict): raise RuntimeError(f"JSON non-oggetto: {p}")
 return v

def close(a:Any,b:Any,label:str,tol:float=.02)->None:
 av=float(a); bv=float(b)
 if not math.isfinite(av) or not math.isfinite(bv) or not math.isclose(av,bv,rel_tol=0.0,abs_tol=tol):
  raise RuntimeError(f"{label}: {a} != {b}")

def rows(metric:dict[str,Any],mid:str)->dict[str,dict[str,Any]]:
 out={str(r.get("town")):r for r in (metric.get("rows") or []) if isinstance(r,dict) and r.get("town")}
 if len(out)!=7: raise RuntimeError(f"{mid}: perimetro pubblico non 7/7")
 return out

def main()->None:
 site=load(SITE); snap=load(SNAP); hist=load(HISTORY); fiscal=load(FISCAL)
 if (snap.get("qualityGate") or {}).get("status")!="PASS" or (snap.get("qualityGate") or {}).get("publicReconciliation")!="4 metrics × 7/7 towns PASS":
  raise RuntimeError("Snapshot SIOPE benchmark senza gate PASS")
 metrics=site.get("metrics") or {}; specs=snap.get("benchmarks") or {}
 for mid in TARGETS:
  if not isinstance(metrics.get(mid),dict) or not isinstance(specs.get(mid),dict): raise RuntimeError(f"{mid}: contratto mancante")

 for mid in ("siopePayments","currentPayments","capitalPayments"):
  rr=rows(metrics[mid],mid)
  expected=(hist.get("validation_2025") or {}).get(mid) or {}
  if set(rr)!=set(expected): raise RuntimeError(f"{mid}: perimetro storico non riconciliato")
  for town,ev in expected.items(): close(rr[town].get("value"),ev.get("calculated_2025"),f"{mid}/{town}",.02)

 rr=rows(metrics["fiscalRecoveryActivity"],"fiscalRecoveryActivity")
 towns=fiscal.get("towns") or {}
 if set(rr)!=set(towns): raise RuntimeError("fiscalRecoveryActivity: perimetro snapshot non 7/7")
 for town,raw in towns.items():
  expected=float(raw["verificationControlReceiptsEuro"])/float(raw["populationIstat"])
  close(rr[town].get("value"),expected,f"fiscalRecoveryActivity/{town}",.02)
  parts=rr[town].get("parts") or []
  if not parts or str(parts[0].get("label"))!="Incassi da verifica e controllo per residente":
   raise RuntimeError(f"fiscalRecoveryActivity/{town}: componente predefinita inattesa")
  close(parts[0].get("value"),expected,f"fiscalRecoveryActivity/{town}/part0",.02)

 updated=0
 for mid,cfg in TARGETS.items():
  metric=metrics[mid]; meta=metric.get("meta") or {}; spec=specs[mid]
  if str(meta.get("year"))!=cfg["year"] or str(meta.get("unit"))!=cfg["unit"]:
   raise RuntimeError(f"{mid}: anno/unità pubblici inattesi {meta.get('year')}/{meta.get('unit')}")
  if str(spec.get("year"))!=cfg["year"] or str(spec.get("unit"))!=cfg["unit"]: raise RuntimeError(f"{mid}: benchmark anno/unità inattesi")
  tus=float(spec["tuscany"])
  if not math.isfinite(tus) or spec.get("italy") is not None: raise RuntimeError(f"{mid}: Toscana/Italia non conformi")
  payload={"year":cfg["year"],"tuscany":tus,"italy":None,"source":"RGS — OpenBDAP/SIOPE","url":cfg["url"],"sourceSnapshot":REF,"note":cfg["note"]}
  if mid=="fiscalRecoveryActivity": payload["part"]="Incassi da verifica e controllo per residente"
  meta["benchmark"]=payload; updated+=1
 SITE.write_text(json.dumps(site,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"A3 benchmark SIOPE: {updated} metriche Toscana materializzate; Italia n.d.; gate 4/4 × 7/7 PASS.")

if __name__=="__main__": main()
