#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,re
from collections import defaultdict
from pathlib import Path
import requests

BASE="https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/"
TAX_YEAR=2024
DECLARATION_YEAR=2025
URL_CANDIDATES={
    "calc":[BASE+"REG_calcolo_irpef_2025.csv?d=1615465800",BASE+"REG_calcolo_irpef_2025.csv"],
    "type":[BASE+"REG_tipo_reddito_2025.csv?d=1615465800",BASE+"REG_tipo_reddito_2025.csv"],
}

def norm(x):
    import unicodedata
    s=unicodedata.normalize("NFKD",str(x or "")); s="".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+"," ",s.lower()).strip()

def val(x):
    if isinstance(x,(int,float)) and not isinstance(x,bool):
        return float(x)
    s=str(x or "").strip().replace(".","").replace(",",".")
    try:return float(s)
    except:return 0.0

def read(session,candidates):
    errors=[]
    for url in candidates:
        try:
            r=session.get(url,timeout=180); r.raise_for_status()
            text=r.content.decode("utf-8-sig",errors="replace")
            if "<!doctype html" in text[:500].lower() or "<html" in text[:500].lower():
                raise RuntimeError("risposta HTML, non CSV")
            try:d=csv.Sniffer().sniff(text[:8000],delimiters=";,\t").delimiter
            except csv.Error:d=";"
            rows=list(csv.DictReader(io.StringIO(text),delimiter=d))
            if not rows:
                raise RuntimeError("CSV senza righe")
            return rows,r.url,d
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError("Nessun CSV MEF 2025 valido: "+" | ".join(errors))

def header(row,*tokens):
    hits=[]
    for h in row:
        n=norm(h)
        if all(t in n for t in tokens): hits.append(h)
    if not hits:
        raise RuntimeError("Header non trovato: "+"/".join(tokens))
    return hits[0]

def totals(rows):
    sample=rows[0]
    region_h=header(sample,"regione")
    class_candidates=[
        h for h in sample
        if "classi" in norm(h) and "reddito complessivo" in norm(h)
    ]
    if len(class_candidates)!=1:
        raise RuntimeError(f"Classificazione reddito non univoca: {class_candidates}")
    class_h=class_candidates[0]

    grouped=defaultdict(list)
    for r in rows:
        reg=str(r.get(region_h) or "").strip()
        if reg:
            grouped[reg].append(r)

    out={}
    diagnostics={}
    for reg,items in grouped.items():
        labels=[norm(r.get(class_h)) for r in items]
        if not labels or any(not label for label in labels) or len(set(labels))!=len(labels):
            raise RuntimeError(f"{reg}: classi reddito mancanti o duplicate")
        # Le righe REG_* sono classi di reddito disgiunte, non totali cumulativi.
        if not any(label=="zero" for label in labels):
            raise RuntimeError(f"{reg}: classe zero assente")
        if not any("minore" in label for label in labels):
            raise RuntimeError(f"{reg}: classe inferiore assente")
        if not any(("oltre" in label or "maggiore" in label) for label in labels):
            raise RuntimeError(f"{reg}: classe superiore aperta assente")

        synthetic={h:"" for h in sample}
        synthetic[region_h]=reg
        synthetic[class_h]="TOTALE RICOSTRUITO DA CLASSI DISGIUNTE"
        for h in sample:
            if h in {region_h,class_h}:
                continue
            synthetic[h]=sum(val(r.get(h)) for r in items)
        out[reg]=synthetic
        diagnostics[reg]={
            "method":"sum_disjoint_income_classes",
            "rowCount":len(items),
            "classHeader":class_h,
            "classLabels":labels,
        }

    if "Toscana" not in out:
        raise RuntimeError(f"Toscana assente; regioni trovate={sorted(out)[:30]}")
    return out,diagnostics


def sumfield(rows,h): return sum(val(r.get(h)) for r in rows.values())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-MEF-benchmark/2.0"
    calc_rows,calc_url,calc_delim=read(s,URL_CANDIDATES["calc"])
    type_rows,type_url,type_delim=read(s,URL_CANDIDATES["type"])
    calc,calc_diag=totals(calc_rows); typ,type_diag=totals(type_rows)
    cr=next(iter(calc.values())); tr=next(iter(typ.values()))

    contrib=header(cr,"numero contribuenti")
    taxable_f=header(cr,"reddito imponibile","frequenza")
    taxable_a=header(cr,"reddito imponibile","ammontare")
    total_f=header(cr,"reddito complessivo","frequenza")
    total_a=header(cr,"reddito complessivo","ammontare")
    pension_f=header(tr,"reddito da pensione","frequenza")
    pension_a=header(tr,"reddito da pensione","ammontare")
    source_specs=[
      ("buildings","reddito da fabbricati"),("employment","reddito da lavoro dipendente"),
      ("pension","reddito da pensione"),("selfEmployment","reddito da lavoro autonomo"),
      ("entrepreneurOrdinary","imprenditore in contabilita ordinaria"),
      ("entrepreneurSimplified","imprenditore in contabilita semplificata"),("participation","reddito da partecipazione")
    ]

    def calc_scope(crows,trows):
        taxable_amount=sumfield(crows,taxable_a); taxable_freq=sumfield(crows,taxable_f)
        total_amount=sumfield(crows,total_a); total_freq=sumfield(crows,total_f)
        pension_amount=sumfield(trows,pension_a); pension_freq=sumfield(trows,pension_f)
        sources=[]
        for key,label in source_specs:
            try:
                ah=header(tr,*norm(label).split(),"ammontare")
                fh=header(tr,*norm(label).split(),"frequenza")
            except RuntimeError:
                continue
            amount=sumfield(trows,ah); frequency=sumfield(trows,fh)
            sources.append({"key":key,"amountEuro":amount,"frequency":frequency,"average":amount/frequency if frequency else None})
        return {
            "taxpayers":sumfield(crows,contrib),
            "taxableIncomeFrequency":taxable_freq,
            "taxableIncomeAmountEuro":taxable_amount,
            "averageTaxableIncome":taxable_amount/taxable_freq if taxable_freq else None,
            "totalIncomeFrequency":total_freq,
            "totalIncomeAmountEuro":total_amount,
            "averageTotalIncome":total_amount/total_freq if total_freq else None,
            "pensionIncomeFrequency":pension_freq,
            "pensionIncomeAmountEuro":pension_amount,
            "pensionIncomeShare":pension_amount/total_amount*100 if total_amount else None,
            "incomeSources":sources,
        }

    tusc_c={"Toscana":calc["Toscana"]}; tusc_t={"Toscana":typ["Toscana"]}
    candidates={"tuscany":calc_scope(tusc_c,tusc_t),"italy":calc_scope(calc,typ)}
    sanity={
        "tuscanyTaxpayers":2_000_000 <= candidates["tuscany"]["taxpayers"] <= 4_000_000,
        "italyTaxpayers":35_000_000 <= candidates["italy"]["taxpayers"] <= 50_000_000,
        "tuscanyAverageTotalIncome":10_000 <= (candidates["tuscany"]["averageTotalIncome"] or 0) <= 60_000,
        "italyAverageTotalIncome":10_000 <= (candidates["italy"]["averageTotalIncome"] or 0) <= 60_000,
    }
    status="ACQUIRED_CANDIDATE" if all(sanity.values()) else "CANDIDATE_REJECTED_SANITY"
    payload={
        "schemaVersion":2,
        "publisher":"MEF — Dipartimento Finanze",
        "profileId":"mef-irpef-annual",
        "declarationYear":DECLARATION_YEAR,
        "taxYear":TAX_YEAR,
        "sources":{"calc":calc_url,"type":type_url},
        "parsing":{"calcDelimiter":calc_delim,"typeDelimiter":type_delim,"calc":calc_diag,"type":type_diag},
        "candidates":candidates,
        "metricMapping":{
            "income":"averageTotalIncome",
            "pensionIncomeShare":"pensionIncomeAmountEuro / totalIncomeAmountEuro × 100",
            "incomeSourceProfile":"incomeSources.average",
            "taxpayersAdultPopulationRate":"numerator only: taxpayers; denominator must come from POSAS 18+",
            "incomeDistribution":"not materialized by this worker yet; requires class-frequency mapping matching the four public groups",
        },
        "sanityGate":sanity,
        "status":status,
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"metrics":["income","pensionIncomeShare","incomeSourceProfile","taxpayersAdultPopulationRate:numerator"],"output":str(p)},ensure_ascii=False))

if __name__=="__main__":
    main()
