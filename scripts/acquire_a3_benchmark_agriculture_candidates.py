#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/istat-agricoltura-territorio-2020.json"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
TOWNS="046005+046013+046018+046024+046028+046030+046033"
TUSCANY_PREFIXES={"045","046","047","048","049","050","051","052","053","100"}
OFFICIAL={
 "tuscany":{"farms":52337.0,"sauCenterHa":651434.43},
 "italy":{"farms":1133006.0,"sauCenterHa":12431807.72},
}
OFFICIAL_TABLE="Regione Toscana/Istat, TOSCANA_AGRICOLTURA_CENSIMENTO2020.xlsx, Tav.1"

def fetch(session:requests.Session,flow:str,key:str)->tuple[list[dict[str,str]],str]:
    errors=[]
    for url in (f"{BASE}/{flow}/{key}/IT1",f"{BASE}/IT1,{flow},1.0/{key}/all"):
        try:
            r=session.get(url,params={"startPeriod":"2020","endPeriod":"2020","format":"csvfile"},timeout=300)
            r.raise_for_status()
            rows=list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig",errors="strict"))))
            if rows and "REF_AREA" in rows[0] and "OBS_VALUE" in rows[0]:
                return rows,r.url
            errors.append(f"{r.url}: schema inatteso")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(" | ".join(errors))

def num(v:Any)->float:
    s=str(v or "").strip().replace(",",".")
    if not s: raise RuntimeError("valore SDMX vuoto")
    x=float(s)
    if not math.isfinite(x): raise RuntimeError("valore SDMX non finito")
    return x

def six(v:Any)->str:
    s=str(v or "").strip()
    return s if re.fullmatch(r"\d{6}",s) else ""

def put(out:dict[tuple[str,...],float],key:tuple[str,...],value:float)->None:
    if key in out and not math.isclose(out[key],value,rel_tol=0.0,abs_tol=1e-9):
        raise RuntimeError(f"duplicato incoerente {key}: {out[key]} != {value}")
    out[key]=value

def surface_index(rows):
    out={}
    for r in rows:
        c=six(r.get("REF_AREA")); dt=str(r.get("DATA_TYPE") or "").strip()
        if c and dt in {"HO","ARU","FUAA"}: put(out,(c,dt),num(r.get("OBS_VALUE")))
    return out

def irrigation_index(rows):
    out={}
    for r in rows:
        c=six(r.get("REF_AREA")); dt=str(r.get("DATA_TYPE") or "").strip()
        if c and dt=="IA": put(out,(c,dt),num(r.get("OBS_VALUE")))
    return out

def localized_index(rows):
    out={}
    for r in rows:
        c=six(r.get("REF_AREA")); dt=str(r.get("DATA_TYPE") or "").strip()
        crop=str(r.get("TYPE_OF_CROP") or "").strip(); alt=str(r.get("ALTIMETRIC_ZONE") or "").strip()
        if c and dt=="ARU" and crop=="ALL" and alt=="TOT": put(out,(c,dt,crop,alt),num(r.get("OBS_VALUE")))
    return out

def codes_for(index:dict[tuple[str,...],float],dtype:str)->set[str]:
    return {k[0] for k in index if len(k)>=2 and k[1]==dtype}

def scope_sum(index,keys,scope):
    def pred(c): return True if scope=="italy" else c[:3] in TUSCANY_PREFIXES
    return sum(v for k,v in index.items() if k in keys and pred(k[0]))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-agriculture/5.0"
    local=json.loads(LOCAL.read_text(encoding="utf-8"))["towns"]

    town_s,u1=fetch(s,"DF_DCAT_CENSAGRIC2020_SURF_ALL",f"A.{TOWNS}.HO+ARU+FUAA")
    town_i,u2=fetch(s,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",f"A.{TOWNS}.IA")
    town_l,u3=fetch(s,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2",f"A.{TOWNS}.ARU.ALL.TOT")
    all_s,u4=fetch(s,"DF_DCAT_CENSAGRIC2020_SURF_ALL","A..HO+ARU+FUAA")
    all_i,u5=fetch(s,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS","A..IA")
    all_l,u6=fetch(s,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2","A..ARU.ALL.TOT")

    ts,ti,tl=surface_index(town_s),irrigation_index(town_i),localized_index(town_l)
    errors=[]
    for code,d in local.items():
        checks={
          "farms":ts.get((code,"HO")),
          "sauCenterHa":ts.get((code,"ARU")),
          "farmsWithSau":ts.get((code,"FUAA")),
          "irrigatedAreaHa":ti.get((code,"IA")),
          "sauLocalizedHa":tl.get((code,"ARU","ALL","TOT")),
        }
        for field,value in checks.items():
            if value is None or not math.isclose(float(value),float(d[field]),rel_tol=0.0,abs_tol=.02):
                errors.append(f"{code}/{field}: {value} != {d[field]}")

    si,ii,li=surface_index(all_s),irrigation_index(all_i),localized_index(all_l)
    raw={}
    for scope in ("tuscany","italy"):
        pred=lambda c: True if scope=="italy" else c[:3] in TUSCANY_PREFIXES
        farm_codes={c for c in codes_for(si,"HO") if pred(c)}
        sau_codes={c for c in codes_for(si,"ARU") if pred(c)}
        fsau_codes={c for c in codes_for(si,"FUAA") if pred(c)}
        irr_codes={c for c in codes_for(ii,"IA") if pred(c)}
        loc_codes={k[0] for k in li if pred(k[0])}
        raw[scope]={
          "farms":sum(si[(c,"HO")] for c in farm_codes),
          "sauCenterHa":sum(si[(c,"ARU")] for c in sau_codes),
          "farmsWithSau":sum(si[(c,"FUAA")] for c in fsau_codes),
          "sauLocalizedHa":sum(li[(c,"ARU","ALL","TOT")] for c in loc_codes),
          "irrigatedAreaHa":sum(ii[(c,"IA")] for c in irr_codes),
          "coverage":{"farms":len(farm_codes),"sauCenter":len(sau_codes),"farmsWithSau":len(fsau_codes),"localizedSau":len(loc_codes),"irrigation":len(irr_codes)},
        }
        for field in ("farms","sauCenterHa"):
            if not math.isclose(raw[scope][field],OFFICIAL[scope][field],rel_tol=0.0,abs_tol=.05):
                errors.append(f"{scope}/{field}: {raw[scope][field]} != official {OFFICIAL[scope][field]}")
    # A livello Italia la SAU per localizzazione deve chiudere con la SAU nazionale per centro aziendale.
    if not math.isclose(raw["italy"]["sauLocalizedHa"],OFFICIAL["italy"]["sauCenterHa"],rel_tol=0.0,abs_tol=.1):
        errors.append(f"italy/sauLocalizedHa: {raw['italy']['sauLocalizedHa']} != official SAU {OFFICIAL['italy']['sauCenterHa']}")

    # Gate per-metrica: un mismatch sulla SAU localizzata non deve bloccare
    # metriche indipendenti già riconciliate e controllate su totali ufficiali.
    core_errors=[e for e in errors if "sauLocalizedHa" not in e]
    localized_errors=[e for e in errors if "sauLocalizedHa" in e]
    benchmarks={
      "agriculturalFarms":{"year":"2020","unit":"number","formula":"somma aziende agricole comunali","tuscany":raw["tuscany"]["farms"],"italy":raw["italy"]["farms"]},
      "averageAgriculturalFarmSize":{"year":"2020","unit":"hectaresPerFarm","formula":"Σ SAU per centro aziendale / Σ aziende con SAU","tuscany":raw["tuscany"]["sauCenterHa"]/raw["tuscany"]["farmsWithSau"],"italy":raw["italy"]["sauCenterHa"]/raw["italy"]["farmsWithSau"]},
    }
    safe_gate="PASS" if not core_errors else "FAIL"
    payload={
      "schemaVersion":5,"publisher":"Istat — 7° Censimento generale dell’agricoltura 2020","profileId":"istat-agriculture-census-2020","referenceYear":2020,
      "status":"ACQUIRED_CANDIDATE" if safe_gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"townSurface":u1,"townIrrigation":u2,"townLocalizedSau":u3,"allMunicipalSurface":u4,"allMunicipalIrrigation":u5,"allMunicipalLocalizedSau":u6,"officialControl":OFFICIAL_TABLE},
      "benchmarks":benchmarks,"raw":raw,
      "qualityGate":{
        "status":safe_gate,
        "publicSnapshotReconciliation":"2 metrics × 7/7 towns PASS" if safe_gate=="PASS" else "FAIL",
        "officialTotalsControl":"HO + center SAU Tuscany/Italy PASS" if safe_gate=="PASS" else "FAIL",
        "errors":core_errors,
      },
      "blocked":{
        "agriculturalUsedArea":{
          "reason":"SAU localizzata Italia non chiude il totale nazionale per centro aziendale; non forzata",
          "candidate":{"tuscany":raw["tuscany"]["sauLocalizedHa"],"italy":raw["italy"]["sauLocalizedHa"]},
          "errors":localized_errors,
          "coverage":{"tuscany":raw["tuscany"]["coverage"]["localizedSau"],"italy":raw["italy"]["coverage"]["localizedSau"]},
        },
        "irrigatedAgriculturalArea":{"reason":"manca un controllo aggregato ufficiale indipendente","candidate":{"tuscany":raw["tuscany"]["irrigatedAreaHa"],"italy":raw["italy"]["irrigatedAreaHa"]}},
        "cropProfile":"composite: componente benchmark da certificare separatamente",
        "agriculturalRenewalAndLeadership":"fasce età aggregate non consentono <=40",
        "agriculturalDiversificationAndModernization":"serve totale distinto delle aziende con attività connesse",
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"benchmarks":benchmarks,"raw":raw,"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
