#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re,unicodedata
from pathlib import Path
from typing import Any
import requests
import build_siope_history as histlib

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/"data/source-snapshots/siope-history-v1.6.0.json"
FISCAL=ROOT/"data/source-snapshots/fiscal-lotto-b-2025.json"
DEMO=ROOT/"data/source-snapshots/a3-istat-demography-benchmark-2026.json"
SPESA="https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/74533d22-b1c2-4d89-b1b9-b98e6c9713ff.csv"
ENTRATA="https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/4dbef43d-72fa-4fe2-a716-45986be658f2.csv"
TOWNS={"Camaiore":"046005","Forte dei Marmi":"046013","Massarosa":"046018","Pietrasanta":"046024","Seravezza":"046028","Stazzema":"046030","Viareggio":"046033"}

def norm(v:Any)->str:
    t=unicodedata.normalize("NFKD",str(v or ""))
    t="".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+"," ",t.casefold()).strip()

def get_blob(session:requests.Session,url:str)->bytes:
    r=session.get(url,timeout=300); r.raise_for_status()
    if len(r.content)<1000: raise RuntimeError(f"dump troppo corto {url}: {len(r.content)}")
    return r.content

def parse(blob:bytes,movement:str)->tuple[dict[str,dict[str,float]],dict[str,Any]]:
    text,encoding=histlib.decode_csv(blob); delim=histlib.choose_delimiter(text[:10000])
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    headers=histlib.header_lookup(reader.fieldnames or [])
    f={
      "province":histlib.require_header(headers,"Codice Istat Provincia"),
      "commune":histlib.require_header(headers,"Codice Istat Comune"),
      "entity_type":histlib.require_header(headers,"Codice Tipologia Ente BDAP"),
      "month":histlib.require_header(headers,"Anno/Mese Calendario","AnnoMese Calendario"),
      "movement":histlib.require_header(headers,"Tipologia del Movimento","Flag Tipologia Classificazione"),
      "title":histlib.require_header(headers,"Codice Titolo CG"),
      "detail":histlib.require_header(headers,"Codice Gestionale Enti Locali"),
      "description":histlib.require_header(headers,"Descrizione CG"),
      "population":histlib.require_header(headers,"Popolazione ISTAT"),
      "amount":histlib.require_header(headers,"Importo cumulato"),
    }
    flag="E" if movement=="entrata" else "S"
    out={}
    seen=set(); selected=0
    for row in reader:
        prov=histlib.digits(row.get(f["province"]))[-3:].zfill(3)
        if prov not in {"045","046","047","048","049","050","051","052","053","100"}: continue
        if str(row.get(f["entity_type"],"")).strip().upper()!="CO": continue
        md=histlib.digits(row.get(f["month"]))
        if not md.endswith("202512"): continue
        if flag not in str(row.get(f["movement"],"")).strip().upper(): continue
        cd=histlib.digits(row.get(f["commune"]))
        if not cd: continue
        code=(prov+cd[-3:].zfill(3)) if len(cd)<=3 else cd[-6:].zfill(6)
        detail=str(row.get(f["detail"],"")).strip()
        key=(code,detail)
        if key in seen: raise RuntimeError(f"duplicato {movement}: {key}")
        seen.add(key)
        amount=histlib.parse_number(row.get(f["amount"]))
        pop=int(round(histlib.parse_number(row.get(f["population"]))))
        if pop<=0 or not math.isfinite(amount): raise RuntimeError(f"{code}: valore non valido")
        state=out.setdefault(code,{"population":pop,"total":0.0,"current":0.0,"capital":0.0,"recovery":0.0,"rows":0})
        if state["population"]!=pop: raise RuntimeError(f"{code}: popolazione non univoca")
        state["total"]+=amount; state["rows"]+=1
        title=histlib.title_number(row.get(f["title"]),flag)
        if movement=="spesa" and title==1: state["current"]+=amount
        if movement=="spesa" and title==2: state["capital"]+=amount
        if movement=="entrata":
            desc=norm(row.get(f["description"]))
            if "riscoss" in desc and "a seguito di attivita di verifica e controllo" in desc:
                state["recovery"]+=amount
        selected+=1
    if len(out)<260: raise RuntimeError(f"Toscana comuni SIOPE troppo pochi: {len(out)}")
    return out,{"encoding":encoding,"delimiter":delim,"selectedRows":selected,"municipalities":len(out)}

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    session=requests.Session(); session.headers["User-Agent"]="OsservatorioVersilia-A3-SIOPE-benchmark/2.0"
    spesa_blob=get_blob(session,SPESA); entrata_blob=get_blob(session,ENTRATA)
    spesa,sa=parse(spesa_blob,"spesa"); entrata,ea=parse(entrata_blob,"entrata")
    history=json.loads(HISTORY.read_text(encoding="utf-8"))
    fiscal=json.loads(FISCAL.read_text(encoding="utf-8"))
    demo=json.loads(DEMO.read_text(encoding="utf-8"))
    errors=[]
    for town,code in TOWNS.items():
        if code not in spesa or code not in entrata:
            errors.append(f"{town}: assente dal dump"); continue
        hraw=history["raw"][town]["2025"]
        resident=float(hraw["population_resident"])
        checks={
          "siopePayments":spesa[code]["total"]/resident,
          "currentPayments":spesa[code]["current"]/spesa[code]["population"],
          "capitalPayments":spesa[code]["capital"]/spesa[code]["population"],
        }
        for metric,calc in checks.items():
            existing=float(history["validation_2025"][metric][town]["existing_2025"])
            if not math.isclose(calc,existing,rel_tol=0.0,abs_tol=.02):
                errors.append(f"{metric}/{town}: {calc} != {existing}")
        fs=fiscal["towns"][town]
        if not math.isclose(entrata[code]["recovery"],float(fs["verificationControlReceiptsEuro"]),rel_tol=0.0,abs_tol=.02):
            errors.append(f"fiscalRecoveryActivity/{town}: {entrata[code]['recovery']} != {fs['verificationControlReceiptsEuro']}")
    resident_tuscany=float(demo["benchmarks"]["population"]["tuscany"])
    pop_spesa=sum(v["population"] for v in spesa.values())
    pop_entrata=sum(v["population"] for v in entrata.values())
    benchmarks={
      "siopePayments":{"year":"2025","unit":"currency","tuscany":sum(v["total"] for v in spesa.values())/resident_tuscany,"italy":None},
      "currentPayments":{"year":"2025","unit":"currency","tuscany":sum(v["current"] for v in spesa.values())/pop_spesa,"italy":None},
      "capitalPayments":{"year":"2025","unit":"currency","tuscany":sum(v["capital"] for v in spesa.values())/pop_spesa,"italy":None},
      "fiscalRecoveryActivity":{"year":"2025","unit":"currency","tuscany":sum(v["recovery"] for v in entrata.values())/pop_entrata,"italy":None},
    }
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":1,"publisher":"Ragioneria Generale dello Stato — OpenBDAP/SIOPE",
      "profileId":"siope-monthly","referenceYear":2025,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"spesaToscana":SPESA,"entrataToscana":ENTRATA,"spesaBytes":len(spesa_blob),"entrataBytes":len(entrata_blob)},
      "benchmarks":benchmarks,
      "rawTuscany":{"residentPopulation2026":resident_tuscany,"siopePopulationSpesa":pop_spesa,"siopePopulationEntrata":pop_entrata,"municipalitiesSpesa":len(spesa),"municipalitiesEntrata":len(entrata)},
      "qualityGate":{"status":gate,"publicReconciliation":"4 metrics × 7/7 towns PASS" if not errors else "FAIL","errors":errors,"spesaAudit":sa,"entrataAudit":ea},
      "italyPolicy":"Italia non materializzata in questo blocco: OpenBDAP pubblica il flusso 2025 per regione; l'aggregato nazionale richiede fan-out sui dataset regionali separati."
    }
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"benchmarks":benchmarks,"gate":payload["qualityGate"]},ensure_ascii=False))

if __name__=="__main__": main()
