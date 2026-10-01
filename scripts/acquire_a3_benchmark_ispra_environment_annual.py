#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math
from pathlib import Path

import audit_waste_cost_ispra as src

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"

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
            if municipalities is not None and population is not None and population>0 and ctot is not None and name=="toscana" and int(round(municipalities))>1:
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
    unique_aggregates=[]
    for item in aggregates:
        if not any(math.isclose(item["ctot"],x["ctot"],abs_tol=.001) and item["municipalityCount"]==x["municipalityCount"] for x in unique_aggregates):
            unique_aggregates.append(item)
    if len(unique_aggregates)!=1:
        raise RuntimeError(f"ISPRA: riga aggregata Toscana non univoca: {unique_aggregates}")
    regional=unique_aggregates[0]
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
      "benchmarks":{"wasteServiceCost":{"year":"2024","unit":"currency","formula":"CTOTab regionale ufficiale ISPRA","tuscany":regional_value,"italy":None}},
      "raw":{"tuscanyMunicipalitiesWithCost":len(rows),"municipalWeightedCheck":weighted,"regionalOfficial":regional},
      "qualityGate":{"status":gate,"publicReconciliation":"1 metric × 7/7 towns PASS" if gate=="PASS" else "FAIL","errors":errors},
      "blocked":{
        "recycling":"richiede la tabella RD/produzione comunale omogenea, non il dataset costi",
        "residualWaste":"richiede la tabella produzione comunale omogenea, non il dataset costi",
        "wastePerResident":"richiede la tabella produzione comunale omogenea, non il dataset costi",
        "italy":"worker corrente acquisisce il perimetro regionale Toscana; aggregato nazionale non forzato"
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":["wasteServiceCost"],"tuscany":regional_value,"townsWithCost":len(rows),"regionalMunicipalityCount":regional["municipalityCount"],"weightedMunicipalCheck":weighted,"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
