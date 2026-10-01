#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math, urllib.request
from pathlib import Path

import audit_waste_cost_ispra as src

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
REGIONAL_URL="https://www.catasto-rifiuti.isprambiente.it/index.php?aa=2024&advice=si&pg=costiregione"

def official_regional_costs():
    request=urllib.request.Request(REGIONAL_URL,headers=src.UA)
    with urllib.request.urlopen(request,timeout=45) as response:
        text=response.read().decode("utf-8",errors="replace")
    table=src.Tables(); table.feed(text)
    out={}
    for row in table.rows:
        if len(row)<12: continue
        name=src.norm(row[0])
        if name not in {"toscana","italia"}: continue
        value=src.number(row[-1])
        if value is None or not 50<=value<=1000: continue
        out[name]={"ctot":float(value),"rawRow":row}
    if set(out)!={"toscana","italia"}:
        raise RuntimeError(f"ISPRA: righe ufficiali Toscana/Italia CTOTab non univoche: {out}")
    return out

def all_tuscany_rows():
    found={}
    aggregates=[]
    pages=[]
    for page in range(1,20):
        text=src.fetch(page); table=src.Tables(); table.feed(text); pages.append(src.URL.format(page=page))
        valid_on_page=0
        for row in table.rows:
            if len(row)<5: continue
            municipalities=src.number(row[2])
            population=src.number(row[3])
            ctot=src.number(row[-1])
            name=src.norm(row[0])
            if municipalities is not None and population is not None and population>0 and ctot is not None and 230<=int(round(municipalities))<=280:
                aggregates.append({"municipalityCount":int(round(municipalities)),"population":population,"ctot":ctot,"rawRow":row,"page":page})
                continue
            if municipalities is None or int(round(municipalities))!=1 or population is None or population<=0 or ctot is None:
                continue
            if not name: continue
            if name in found:
                old=found[name]
                if not math.isclose(old["population"],population,abs_tol=.5) or not math.isclose(old["ctot"],ctot,abs_tol=.01):
                    raise RuntimeError(f"ISPRA duplicato incoerente {row[0]}")
            found[name]={"label":row[0],"population":population,"ctot":ctot}
            valid_on_page+=1
        if page>=10 and valid_on_page==0:
            break
    return found,aggregates,pages

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    site=json.loads(SITE.read_text(encoding="utf-8"))
    rows,aggregates,pages=all_tuscany_rows()
    if not 230<=len(rows)<=280: raise RuntimeError(f"ISPRA: copertura comunale Toscana inattesa {len(rows)}")
    official=official_regional_costs()
    regional={"ctot":official["toscana"]["ctot"],"rawRow":official["toscana"]["rawRow"],"source":REGIONAL_URL}
    national={"ctot":official["italia"]["ctot"],"rawRow":official["italia"]["rawRow"],"source":REGIONAL_URL}
    errors=[]
    public={str(r["town"]):float(r["value"]) for r in site["metrics"]["wasteServiceCost"]["rows"]}
    if len(public)!=7: errors.append(f"wasteServiceCost pubblico {len(public)}/7")
    for town,observed in public.items():
        got=rows.get(src.norm(town))
        if not got: errors.append(f"{town}: ISPRA assente"); continue
        if not math.isclose(observed,float(got["ctot"]),rel_tol=0.0,abs_tol=.011):
            errors.append(f"{town}: {observed} != {got['ctot']}")
    pop=sum(v["population"] for v in rows.values())
    weighted=sum(v["population"]*v["ctot"] for v in rows.values())/pop
    regional_value=float(regional["ctot"])
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":1,"publisher":"ISPRA — Catasto Nazionale Rifiuti","profileId":"ispra-environment-annual","referenceYear":2024,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"template":src.URL,"pagesScanned":pages},
      "benchmarks":{"wasteServiceCost":{"year":"2024","unit":"currency","formula":"CTOTab regionale/nazionale ufficiale ISPRA","tuscany":regional_value,"italy":float(national["ctot"])}},
      "raw":{"tuscanyMunicipalitiesWithCost":len(rows),"municipalWeightedCheck":weighted,"regionalOfficial":regional,"nationalOfficial":national},
      "qualityGate":{"status":gate,"publicReconciliation":"1 metric × 7/7 towns PASS" if gate=="PASS" else "FAIL","errors":errors},
      "blocked":{
        "recycling":"richiede la tabella RD/produzione comunale omogenea, non il dataset costi",
        "residualWaste":"richiede la tabella produzione comunale omogenea, non il dataset costi",
        "wastePerResident":"richiede la tabella produzione comunale omogenea, non il dataset costi",
        "italy":"Riga Italia CTOTab acquisita dalla stessa tabella ufficiale ISPRA 2024"
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":["wasteServiceCost"],"tuscany":regional_value,"townsWithCost":len(rows),"officialItaly":float(national["ctot"]),"weightedMunicipalCheck":weighted,"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
