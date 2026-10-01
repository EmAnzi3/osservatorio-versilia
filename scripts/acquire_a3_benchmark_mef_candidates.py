#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,re
from collections import defaultdict
from pathlib import Path
import requests

BASE="https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/"
URLS={"calc":BASE+"REG_calcolo_irpef_2024.csv?d=1615465800","type":BASE+"REG_tipo_reddito_2024.csv?d=1615465800"}
def norm(x):
    import unicodedata
    s=unicodedata.normalize("NFKD",str(x or "")); s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+"," ",s.lower()).strip()
def val(x):
    s=str(x or "").strip().replace(".","").replace(",",".")
    try:return float(s)
    except:return 0.0
def read(session,url):
    r=session.get(url,timeout=180); r.raise_for_status()
    text=r.content.decode("utf-8-sig",errors="replace")
    try:d=csv.Sniffer().sniff(text[:8000],delimiters=";,\t").delimiter
    except: d=";"
    return list(csv.DictReader(io.StringIO(text),delimiter=d))
def header(row,*tokens):
    for h in row:
        n=norm(h)
        if all(t in n for t in tokens): return h
    raise RuntimeError("Header non trovato: "+"/".join(tokens))
def totals(rows):
    sample=rows[0]; class_h=list(sample)[0]; region_h=header(sample,"regione")
    grouped=defaultdict(list)
    for r in rows: grouped[str(r.get(region_h) or "").strip()].append(r)
    out={}
    for reg,items in grouped.items():
        hits=[r for r in items if norm(r.get(class_h)) in {"totale","totale complessivo"}]
        if hits: out[reg]=hits[0]
    if "Toscana" not in out: raise RuntimeError("Riga TOTALE Toscana assente")
    return out
def sumfield(rows,h): return sum(val(r.get(h)) for r in rows.values())
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-MEF-benchmark/1.0"
    calc=totals(read(s,URLS["calc"])); typ=totals(read(s,URLS["type"]))
    cr=next(iter(calc.values())); tr=next(iter(typ.values()))
    income_f=header(cr,"reddito complessivo","frequenza"); income_a=header(cr,"reddito complessivo","ammontare")
    contrib=header(cr,"numero contribuenti")
    pension_f=header(tr,"reddito da pensione","frequenza"); pension_a=header(tr,"reddito da pensione","ammontare")
    source_specs=[
      ("buildings","reddito da fabbricati"),("employment","reddito da lavoro dipendente"),
      ("pension","reddito da pensione"),("selfEmployment","reddito da lavoro autonomo"),
      ("entrepreneurOrdinary","imprenditore in contabilita ordinaria"),
      ("entrepreneurSimplified","imprenditore in contabilita semplificata"),("participation","reddito da partecipazione")
    ]
    def calc_scope(crows,trows):
        ia=sumfield(crows,income_a); inf=sumfield(crows,income_f)
        pa=sumfield(trows,pension_a); pf=sumfield(trows,pension_f)
        sources=[]
        for key,label in source_specs:
            try: ah=header(tr,*norm(label).split(),"ammontare"); fh=header(tr,*norm(label).split(),"frequenza")
            except: continue
            sources.append({"key":key,"amountEuro":sumfield(trows,ah),"frequency":sumfield(trows,fh)})
        return {"taxpayers":sumfield(crows,contrib),"totalIncomeFrequency":inf,"totalIncomeAmountEuro":ia,"averageIncome":ia/inf if inf else None,"pensionIncomeFrequency":pf,"pensionIncomeAmountEuro":pa,"pensionIncomeShare":pa/ia*100 if ia else None,"incomeSources":sources}
    tusc_c={"Toscana":calc["Toscana"]}; tusc_t={"Toscana":typ["Toscana"]}
    payload={"schemaVersion":1,"publisher":"MEF — Dipartimento Finanze","profileId":"mef-irpef-annual","taxYear":2024,"sources":URLS,"candidates":{"tuscany":calc_scope(tusc_c,tusc_t),"italy":calc_scope(calc,typ)},"status":"ACQUIRED_CANDIDATE"}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"metrics":["income","pensionIncomeShare","incomeSourceProfile","taxpayersAdultPopulationRate:numerator"],"output":str(p)},ensure_ascii=False))
if __name__=="__main__": main()
