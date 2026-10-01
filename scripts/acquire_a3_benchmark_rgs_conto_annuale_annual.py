#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import audit_rgs_amministrazione_values as src

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/rgs-amministrazione-2024.json"

def groups(rows):
    out=defaultdict(list)
    for r in rows:
        if src.norm(r.get("Descrizione Tipo Istituzione",""))!="COMUNI": continue
        code=str(r.get("Codice Istituzione") or "").strip()
        if code: out[code].append(r)
    return out

def region_field(rows):
    target=src.norm("COMUNE DI CAMAIORE")
    sample=next((r for r in rows if src.norm(r.get("Descrizione Ente",""))==target),None)
    if not sample: raise RuntimeError("RGS: Camaiore assente")
    hits=[k for k,v in sample.items() if src.norm(v)=="TOSCANA"]
    if len(hits)!=1: raise RuntimeError(f"RGS: campo Toscana non univoco {hits}")
    return hits[0]

def scope_codes(turnover_rows,field,wanted_tuscany):
    result=set()
    for r in turnover_rows:
        if src.norm(r.get("Descrizione Tipo Istituzione",""))!="COMUNI": continue
        if wanted_tuscany and src.norm(r.get(field,""))!="TOSCANA": continue
        code=str(r.get("Codice Istituzione") or "").strip()
        if code: result.add(code)
    return result

def aggregate(codes,turn_g,age_g,hire_g,cess_g):
    staff=0.0; over55=0.0; net=0.0; valid=0
    for code in codes:
        tr=turn_g.get(code); ar=age_g.get(code); hr=hire_g.get(code); cr=cess_g.get(code)
        if not all((tr,ar,hr,cr)): continue
        s=src.staff_total(tr); age=src.age_summary(ar); hi=src.flow_summary(hr); ce=src.flow_summary(cr)
        if s<=0 or not math.isclose(s,age["total"],rel_tol=0.0,abs_tol=.001): continue
        staff+=s; over55+=age["over55"]; net+=hi["netOfTransfers"]-ce["netOfTransfers"]; valid+=1
    if valid<=0 or staff<=0: raise RuntimeError("RGS: aggregato vuoto")
    return {"municipalities":valid,"staff":staff,"over55":over55,"netTurnoverHeadcount":net,"age55plusShare":over55/staff*100,"turnoverRate":net/staff*100}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    with ThreadPoolExecutor(max_workers=4) as pool:
        bodies=dict(zip(src.URLS,pool.map(src.fetch,src.URLS.values())))
    ds={k:src.parse(v) for k,v in bodies.items()}
    rf=region_field(ds["turnover"])
    tg,ag,hg,cg=groups(ds["turnover"]),groups(ds["age"]),groups(ds["hires"]),groups(ds["cessations"])
    tus_codes=scope_codes(ds["turnover"],rf,True); ita_codes=scope_codes(ds["turnover"],rf,False)
    tus=aggregate(tus_codes,tg,ag,hg,cg); ita=aggregate(ita_codes,tg,ag,hg,cg)
    local=json.loads(LOCAL.read_text(encoding="utf-8"))["towns"]
    errors=[]
    by_name={}
    for code,rows in tg.items():
        if rows: by_name[src.norm(rows[0].get("Descrizione Ente",""))]=code
    for town,d in local.items():
        code=by_name.get(src.norm(f"COMUNE DI {town}"))
        if not code: errors.append(f"{town}: ente RGS assente"); continue
        tr,ar,hr,cr=tg[code],ag.get(code),hg.get(code),cg.get(code)
        if not all((tr,ar,hr,cr)): errors.append(f"{town}: dataset incompleto"); continue
        staff=src.staff_total(tr); age=src.age_summary(ar); hi=src.flow_summary(hr); ce=src.flow_summary(cr)
        rate=(hi["netOfTransfers"]-ce["netOfTransfers"])/staff*100 if staff else None
        if not math.isclose(staff,float(d["staffAt31Dec"]),abs_tol=.001): errors.append(f"{town}: staff mismatch")
        if not math.isclose(age["over55"],float(d["age"]["age55plus"]),abs_tol=.001): errors.append(f"{town}: age55+ mismatch")
        if rate is None or not math.isclose(rate,float(d["netTurnoverRatePct"]),abs_tol=.00011): errors.append(f"{town}: turnover mismatch {rate} != {d['netTurnoverRatePct']}")
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":1,"publisher":"Ragioneria Generale dello Stato — Conto Annuale/OpenBDAP","profileId":"rgs-conto-annuale-annual","referenceYear":2024,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sourceUrls":src.URLS,
      "benchmarks":{
        "municipalStaffAgeStructure":{"year":"2024","unit":"percent","defaultPart":"55 anni e più","formula":"dipendenti 55+ / personale al 31 dicembre × 100","tuscany":tus["age55plusShare"],"italy":ita["age55plusShare"]},
        "municipalStaffTurnover":{"year":"2024","unit":"percent","formula":"(assunti netti da passaggi - cessati netti da passaggi) / personale al 31 dicembre × 100","tuscany":tus["turnoverRate"],"italy":ita["turnoverRate"]},
      },
      "raw":{"tuscany":tus,"italy":ita},
      "qualityGate":{"status":gate,"publicSourceSnapshotReconciliation":"2 metrics × 7/7 towns PASS" if gate=="PASS" else "FAIL","regionField":rf,"errors":errors},
      "blocked":{
        "municipalEmployeesPer1000":"denominatore regionale/nazionale 2024 da certificare sullo stesso riferimento temporale del contratto pubblico",
        "municipalStaffTraining":"l'API formazione è verificata 7/7 ma serve una strategia aggregata Toscana/Italia distinta"
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(payload["benchmarks"]),"raw":payload["raw"],"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
