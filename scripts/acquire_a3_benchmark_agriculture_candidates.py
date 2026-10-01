#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,re
from pathlib import Path
from typing import Any,Callable
import requests

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/"data/source-snapshots/istat-agricoltura-territorio-2020.json"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
TOWNS="046005+046013+046018+046024+046028+046030+046033"
TUSCANY_PREFIXES={"045","046","047","048","049","050","051","052","053","100"}

def fetch(session:requests.Session,flow:str,key:str)->tuple[list[dict[str,str]],str]:
    errors=[]
    for url in (f"{BASE}/{flow}/{key}/IT1",f"{BASE}/IT1,{flow},1.0/{key}/all"):
        try:
            r=session.get(url,params={"startPeriod":"2020","endPeriod":"2020","format":"csvfile"},timeout=300)
            r.raise_for_status()
            text=r.content.decode("utf-8-sig",errors="strict")
            rows=list(csv.DictReader(io.StringIO(text)))
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

def municipality_index(rows:list[dict[str,str]],extra:tuple[str,...]=())->dict[tuple[str,...],float]:
    out={}
    for r in rows:
        code=six(r.get("REF_AREA"))
        if not code: continue
        key=(code,str(r.get("DATA_TYPE") or "").strip(),*(str(r.get(x) or "").strip() for x in extra))
        value=num(r.get("OBS_VALUE"))
        if key in out and not math.isclose(out[key],value,abs_tol=1e-9): raise RuntimeError(f"duplicato {key}")
        out[key]=value
    return out

def scope_codes(indexes:list[dict[tuple[str,...],float]],pred:Callable[[str],bool])->set[str]:
    sets=[]
    for idx in indexes:
        sets.append({k[0] for k in idx if pred(k[0])})
    return set.intersection(*sets)

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    session=requests.Session(); session.headers["User-Agent"]="OsservatorioVersilia-A3-agriculture/4.0"
    local=json.loads(LOCAL.read_text(encoding="utf-8"))["towns"]

    town_surface,u1=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_ALL",f"A.{TOWNS}.HO+ARU+FUAA")
    town_irr,u2=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS",f"A.{TOWNS}.IA")
    town_loc,u3=fetch(session,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2",f"A.{TOWNS}.ARU.ALL.TOT")
    all_surface,u4=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_ALL","A..HO+ARU+FUAA")
    all_irr,u5=fetch(session,"DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS","A..IA")
    all_loc,u6=fetch(session,"DF_DCAT_CENSAGRIC2020_UA_CROPS_2","A..ARU.ALL.TOT")

    ts=municipality_index(town_surface); ti=municipality_index(town_irr); tl=municipality_index(town_loc,("TYPE_OF_CROP","ALTIMETRIC_ZONE"))
    errors=[]
    for code,d in local.items():
        checks={"farms":ts.get((code,"HO")),"sauCenterHa":ts.get((code,"ARU")),"farmsWithSau":ts.get((code,"FUAA")),"irrigatedAreaHa":ti.get((code,"IA")),"sauLocalizedHa":tl.get((code,"ARU","ALL","TOT"))}
        for field,value in checks.items():
            if value is None or not math.isclose(float(value),float(d[field]),rel_tol=0.0,abs_tol=.02):
                errors.append(f"{code}/{field}: {value} != {d[field]}")

    s=municipality_index(all_surface); irr=municipality_index(all_irr); loc=municipality_index(all_loc,("TYPE_OF_CROP","ALTIMETRIC_ZONE"))
    required=lambda c: all((c,k) in s for k in ("HO","ARU","FUAA")) and (c,"IA") in irr and (c,"ARU","ALL","TOT") in loc
    italy={c for c,_ in s if required(c)}
    tuscany={c for c in italy if c[:3] in TUSCANY_PREFIXES}
    if not 7500<=len(italy)<=8000: errors.append(f"perimetro Italia inatteso: {len(italy)}")
    if not 260<=len(tuscany)<=280: errors.append(f"perimetro Toscana inatteso: {len(tuscany)}")

    def aggregate(codes:set[str])->dict[str,float]:
        return {
          "farms":sum(s[(c,"HO")] for c in codes),
          "sauCenterHa":sum(s[(c,"ARU")] for c in codes),
          "farmsWithSau":sum(s[(c,"FUAA")] for c in codes),
          "sauLocalizedHa":sum(loc[(c,"ARU","ALL","TOT")] for c in codes),
          "irrigatedAreaHa":sum(irr[(c,"IA")] for c in codes),
        }
    raw={"tuscany":aggregate(tuscany),"italy":aggregate(italy)}
    benchmarks={
      "agriculturalFarms":{"year":"2020","unit":"number","tuscany":raw["tuscany"]["farms"],"italy":raw["italy"]["farms"]},
      "agriculturalUsedArea":{"year":"2020","unit":"hectares","tuscany":raw["tuscany"]["sauLocalizedHa"],"italy":raw["italy"]["sauLocalizedHa"]},
      "averageAgriculturalFarmSize":{"year":"2020","unit":"hectaresPerFarm","tuscany":raw["tuscany"]["sauCenterHa"]/raw["tuscany"]["farmsWithSau"],"italy":raw["italy"]["sauCenterHa"]/raw["italy"]["farmsWithSau"]},
      "irrigatedAgriculturalArea":{"year":"2020","unit":"hectares","tuscany":raw["tuscany"]["irrigatedAreaHa"],"italy":raw["italy"]["irrigatedAreaHa"]},
    }
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":3,"publisher":"Istat — 7° Censimento generale dell’agricoltura 2020","profileId":"istat-agriculture-census-2020","referenceYear":2020,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"townSurface":u1,"townIrrigation":u2,"townLocalizedSau":u3,"allMunicipalSurface":u4,"allMunicipalIrrigation":u5,"allMunicipalLocalizedSau":u6},
      "benchmarks":benchmarks,"raw":raw,
      "scope":{"italyMunicipalities":len(italy),"tuscanyMunicipalities":len(tuscany),"tuscanyProvincePrefixes":sorted(TUSCANY_PREFIXES)},
      "qualityGate":{"status":gate,"publicSnapshotReconciliation":"4 metrics × 7/7 towns PASS" if not errors else "FAIL","errors":errors},
      "blocked":{"cropProfile":"composite: componente benchmark da certificare separatamente","agriculturalRenewalAndLeadership":"fasce età aggregate non consentono <=40","agriculturalDiversificationAndModernization":"serve totale distinto delle aziende con attività connesse"}
    }
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"scope":payload["scope"],"benchmarks":benchmarks,"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
