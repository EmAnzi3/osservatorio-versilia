#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import audit_rgs_amministrazione_values as src

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/rgs-amministrazione-2024.json"
ANAGRAFE_ENTE_URL=(
    "https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/"
    "36378/csv/1686/c5638e9f-8613-4e6d-9e92-25412f464f85@rgs"
)

def groups(rows):
    out=defaultdict(list)
    for r in rows:
        if src.norm(r.get("Descrizione Tipo Istituzione",""))!="COMUNI": continue
        code=str(r.get("Codice Istituzione") or "").strip()
        if code: out[code].append(r)
    return out

TUSCANY_PROVINCES={"AR","FI","GR","LI","LU","MS","PI","PO","PT","SI","AREZZO","FIRENZE","GROSSETO","LIVORNO","LUCCA","MASSA CARRARA","PISA","PRATO","PISTOIA","SIENA"}

def clean_code(value):
    raw=str(value or "").strip()
    if raw.endswith(".0") and raw[:-2].isdigit(): raw=raw[:-2]
    return raw

def anagrafe_region_map():
    rows=src.parse(src.fetch(ANAGRAFE_ENTE_URL))
    if not rows: raise RuntimeError("RGS: Anagrafe Ente BDAP vuota")
    keys=list(rows[0])
    by_norm={src.norm(k):k for k in keys}
    id_field=by_norm.get("ID ENTE")
    region_code_field=by_norm.get("CODICE REGIONE")
    region_label_field=by_norm.get("DIZIONE REGIONE")
    if not id_field or (not region_code_field and not region_label_field):
        raise RuntimeError(
            f"RGS: Anagrafe Ente senza ID/Regione; headers={keys}"
        )
    mapping={}
    for row in rows:
        entity_id=clean_code(row.get(id_field))
        if not entity_id: continue
        mapping[entity_id]={
            "code":str(row.get(region_code_field) or "").strip() if region_code_field else "",
            "label":str(row.get(region_label_field) or "").strip() if region_label_field else "",
        }
    if len(mapping)<5000:
        raise RuntimeError(f"RGS: Anagrafe Ente copertura inattesa {len(mapping)}")
    return mapping,{
        "source":ANAGRAFE_ENTE_URL,
        "rows":len(rows),
        "mappedEntities":len(mapping),
        "idField":id_field,
        "regionCodeField":region_code_field,
        "regionLabelField":region_label_field,
    }

def geography_selector(rows):
    target=src.norm("COMUNE DI CAMAIORE")
    sample=next((r for r in rows if src.norm(r.get("Descrizione Ente",""))==target),None)
    if not sample: raise RuntimeError("RGS: Camaiore assente")
    region_keys=[k for k in sample if "REGION" in src.norm(k) and str(sample.get(k) or "").strip()]
    if region_keys:
        preferred=sorted(region_keys,key=lambda k:(0 if "CODICE" in src.norm(k) else 1,len(k)))[0]
        return {"mode":"same-value","field":preferred,"value":str(sample.get(preferred) or "").strip()}
    province_keys=[k for k in sample if ("PROVINC" in src.norm(k) or src.norm(k) in {"PROV","SIGLA PROVINCIA"}) and str(sample.get(k) or "").strip()]
    if province_keys:
        preferred=sorted(province_keys,key=lambda k:(0 if "SIGLA" in src.norm(k) else 1,len(k)))[0]
        return {"mode":"tuscany-provinces","field":preferred,"value":str(sample.get(preferred) or "").strip()}
    if "Codice Ente BDAP" in sample:
        return {"mode":"bdap-anagrafe","field":"Codice Ente BDAP","source":ANAGRAFE_ENTE_URL}
    raise RuntimeError(f"RGS: nessun campo regione/provincia né Codice Ente BDAP; headers={list(sample)}")

def scope_codes(turnover_rows,selector,wanted_tuscany,region_by_bdap=None):
    result=set(); missing=set()
    for r in turnover_rows:
        if src.norm(r.get("Descrizione Tipo Istituzione",""))!="COMUNI": continue
        if selector["mode"]=="bdap-anagrafe":
            bdap=clean_code(r.get(selector["field"]))
            geo=(region_by_bdap or {}).get(bdap)
            if not bdap or geo is None:
                missing.add(bdap or "<empty>")
                continue
            if wanted_tuscany:
                region_code=src.norm(geo.get("code",""))
                region_label=src.norm(geo.get("label",""))
                if region_code not in {"9","09"} and region_label!="TOSCANA": continue
        elif wanted_tuscany:
            field=selector["field"]; value=src.norm(r.get(field,""))
            if selector["mode"]=="same-value":
                if value!=src.norm(selector["value"]): continue
            elif selector["mode"]=="tuscany-provinces":
                if value not in TUSCANY_PROVINCES: continue
            else:
                raise RuntimeError(f"RGS: selector inatteso {selector}")
        code=str(r.get("Codice Istituzione") or "").strip()
        if code: result.add(code)
    return result,missing

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
    selector=geography_selector(ds["turnover"])
    region_by_bdap=None; anagrafe_meta=None
    if selector["mode"]=="bdap-anagrafe":
        region_by_bdap,anagrafe_meta=anagrafe_region_map()
    tg,ag,hg,cg=groups(ds["turnover"]),groups(ds["age"]),groups(ds["hires"]),groups(ds["cessations"])
    tus_codes,tus_missing=scope_codes(ds["turnover"],selector,True,region_by_bdap)
    ita_codes,ita_missing=scope_codes(ds["turnover"],selector,False,region_by_bdap)
    if ita_missing:
        raise RuntimeError(
            f"RGS: join Codice Ente BDAP→Anagrafe incompleto: {len(ita_missing)} mancanti; sample={sorted(ita_missing)[:20]}"
        )
    if not 250<=len(tus_codes)<=300: raise RuntimeError(f"RGS: Comuni Toscana inattesi {len(tus_codes)} selector={selector}")
    if not 7000<=len(ita_codes)<=9000: raise RuntimeError(f"RGS: Comuni Italia inattesi {len(ita_codes)}")
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
      "qualityGate":{"status":gate,"publicSourceSnapshotReconciliation":"2 metrics × 7/7 towns PASS" if gate=="PASS" else "FAIL","geographySelector":selector,"anagrafeEnte":anagrafe_meta,"tuscanyInstitutionCount":len(tus_codes),"italyInstitutionCount":len(ita_codes),"errors":errors},
      "blocked":{
        "municipalEmployeesPer1000":"denominatore regionale/nazionale 2024 da certificare sullo stesso riferimento temporale del contratto pubblico",
        "municipalStaffTraining":"l'API formazione è verificata 7/7 ma serve una strategia aggregata Toscana/Italia distinta"
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(payload["benchmarks"]),"raw":payload["raw"],"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
