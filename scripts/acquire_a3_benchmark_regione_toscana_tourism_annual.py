#!/usr/bin/env python3
from __future__ import annotations

import argparse, io, json, math, zipfile
from pathlib import Path
from typing import Any
import requests
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
DEMO=ROOT/"data/source-snapshots/a3-istat-demography-benchmark-2026.json"
URLS={
 "movement":"https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-",
 "monthly":"https://www.regione.toscana.it/documents/d/guest/5-movimento-comune_mese-2025-agg-maggio-2026-",
}
NS={"office":"urn:oasis:names:tc:opendocument:xmlns:office:1.0","table":"urn:oasis:names:tc:opendocument:xmlns:table:1.0","text":"urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
TARGETS=["foreignTourismShare","tourismArrivals","tourismAverageStay","tourismIntensity","tourismPresences","tourismSeasonality"]

def cell_value(cell:ET.Element)->Any:
    typ=cell.attrib.get(f"{{{NS['office']}}}value-type")
    if typ in {"float","currency","percentage"}:
        raw=cell.attrib.get(f"{{{NS['office']}}}value")
        if raw is not None:
            try:return float(raw)
            except ValueError: pass
    texts=[]
    for p in cell.findall(".//text:p",NS): texts.append("".join(p.itertext()))
    return " ".join(x for x in texts if x).strip()

def ods_rows(blob:bytes)->list[list[Any]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("content.xml"))
    tables=root.findall(".//table:table",NS)
    if len(tables)!=1: raise RuntimeError(f"ODS: atteso un foglio, trovati {len(tables)}")
    rows=[]
    for tr in tables[0].findall("table:table-row",NS):
        repeat=int(tr.attrib.get(f"{{{NS['table']}}}number-rows-repeated","1"))
        vals=[]
        for cell in list(tr):
            if cell.tag not in {f"{{{NS['table']}}}table-cell",f"{{{NS['table']}}}covered-table-cell"}: continue
            rep=int(cell.attrib.get(f"{{{NS['table']}}}number-columns-repeated","1"))
            vals.extend([cell_value(cell)]*min(rep,60))
        while vals and vals[-1] in ("",None): vals.pop()
        if vals:
            rows.extend([vals]*min(repeat,2))
    return rows

def fetch(url:str)->tuple[list[list[Any]],int]:
    r=requests.get(url,timeout=180,headers={"User-Agent":"OsservatorioVersilia-A3-tourism/2.0"}); r.raise_for_status()
    return ods_rows(r.content),len(r.content)

def find_rows(rows:list[list[Any]])->dict[str,list[Any]]:
    out={}
    for row in rows:
        if not row: continue
        name=str(row[1] if len(row)>1 and row[1] else row[0]).strip()
        if name:
            out[name.casefold()]=row
    return out

def number(v:Any,label:str)->float:
    if isinstance(v,bool): raise RuntimeError(f"{label}: boolean")
    try:x=float(v)
    except Exception as exc: raise RuntimeError(f"{label}: numerico atteso {v!r}") from exc
    if not math.isfinite(x): raise RuntimeError(f"{label}: non finito")
    return x

def town_public(site:dict,metric_id:str)->dict[str,float]:
    metric=site["metrics"][metric_id]
    rows={str(r["town"]):float(r["value"]) for r in metric.get("rows",[]) if r.get("town") and isinstance(r.get("value"),(int,float))}
    if len(rows)!=7: raise RuntimeError(f"{metric_id}: pubblico non 7/7")
    return rows

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    site=json.loads(SITE.read_text(encoding="utf-8"))
    demo=json.loads(DEMO.read_text(encoding="utf-8"))
    movement,mb=fetch(URLS["movement"]); monthly,monb=fetch(URLS["monthly"])
    mi=find_rows(movement); mo=find_rows(monthly)
    town_names=[str(t["name"]) for t in site.get("towns",[])]
    pop_by_town={str(r["town"]):float(r["value"]) for r in site["metrics"]["population"]["rows"]}
    errors=[]
    computed={mid:{} for mid in TARGETS}
    for town in town_names:
        mr=mi.get(town.casefold()); xr=mo.get(town.casefold())
        if mr is None or xr is None:
            errors.append(f"{town}: riga movement/monthly mancante"); continue
        arrivals=number(mr[4],f"{town}/arrivals")
        foreign_pres=number(mr[6],f"{town}/foreign-presences")
        presences=number(mr[7],f"{town}/presences")
        month_pres=[number(xr[i],f"{town}/month-{m}") for m,i in enumerate(range(3,26,2),1)]
        monthly_total=number(xr[27],f"{town}/monthly-total")
        if not math.isclose(sum(month_pres),monthly_total,rel_tol=0.0,abs_tol=.1) or not math.isclose(monthly_total,presences,rel_tol=0.0,abs_tol=.1):
            errors.append(f"{town}: mensile non riconciliato")
        computed["tourismArrivals"][town]=arrivals
        computed["tourismPresences"][town]=presences
        computed["tourismAverageStay"][town]=presences/arrivals
        computed["foreignTourismShare"][town]=foreign_pres/presences*100
        computed["tourismSeasonality"][town]=sum(sorted(month_pres,reverse=True)[:3])/presences*100
        computed["tourismIntensity"][town]=presences/pop_by_town[town]

    tolerances={"tourismArrivals":.1,"tourismPresences":.1,"tourismAverageStay":1e-9,"foreignTourismShare":.11,"tourismSeasonality":1e-9,"tourismIntensity":1e-9}
    for mid in TARGETS:
        public=town_public(site,mid)
        for town,expected in computed[mid].items():
            if not math.isclose(public[town],expected,rel_tol=0.0,abs_tol=tolerances[mid]):
                errors.append(f"{mid}/{town}: {public[town]} != {expected}")

    tr=mi.get("toscana")
    xr=mo.get("toscana")
    if tr is None or xr is None: errors.append("Toscana: riga aggregata mancante")
    benchmarks={}
    if tr is not None and xr is not None:
        arrivals=number(tr[4],"Toscana/arrivals"); foreign_pres=number(tr[6],"Toscana/foreign-presences"); pres=number(tr[7],"Toscana/presences")
        month_pres=[number(xr[i],f"Toscana/month-{m}") for m,i in enumerate(range(3,26,2),1)]
        if not math.isclose(sum(month_pres),pres,rel_tol=0.0,abs_tol=.1): errors.append("Toscana: mensile != presenze annuali")
        pop=float(demo["benchmarks"]["population"]["tuscany"])
        benchmarks={
          "tourismArrivals":{"year":"2025","unit":"number","tuscany":arrivals,"italy":None},
          "tourismPresences":{"year":"2025","unit":"number","tuscany":pres,"italy":None},
          "tourismAverageStay":{"year":"2025","unit":"nights","formula":"presenze / arrivi","tuscany":pres/arrivals,"italy":None},
          "foreignTourismShare":{"year":"2025","unit":"percent","formula":"presenze straniere / presenze totali × 100","tuscany":foreign_pres/pres*100,"italy":None},
          "tourismSeasonality":{"year":"2025","unit":"percent","formula":"tre mesi con più presenze / presenze annue × 100","tuscany":sum(sorted(month_pres,reverse=True)[:3])/pres*100,"italy":None},
          "tourismIntensity":{"year":"2025","unit":"decimal","formula":"presenze 2025 / popolazione benchmark 2026","tuscany":pres/pop,"italy":None},
        }

    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":2,"publisher":"Regione Toscana — Ufficio regionale di Statistica / Istat","profileId":"regione-toscana-tourism-annual","referenceYear":2025,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"movement":URLS["movement"],"monthly":URLS["monthly"],"movementBytes":mb,"monthlyBytes":monb},
      "benchmarks":benchmarks,
      "qualityGate":{"status":gate,"publicReconciliation":"6 metrics × 7/7 towns PASS" if gate=="PASS" else "FAIL","regionalRows":"movement + monthly Toscana PASS" if gate=="PASS" else "FAIL","errors":errors},
      "blocked":{
        "tourismBedsPer1000":"il file consistenza 2025 al netto locazioni non riconcilia il contratto pubblico corrente; non forzato",
        "tourismStructuresPer1000":"il file consistenza 2025 al netto locazioni non riconcilia il contratto pubblico corrente; non forzato",
        "italy":"la stessa fonte Regione Toscana non espone un aggregato nazionale omogeneo; benchmark Italia resta n.d."
      }
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(benchmarks),"tuscany":{k:v["tuscany"] for k,v in benchmarks.items()},"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
