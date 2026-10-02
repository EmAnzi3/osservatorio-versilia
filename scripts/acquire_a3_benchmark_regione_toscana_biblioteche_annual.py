#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,io,json,math,re,unicodedata
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
GOVERNED=ROOT/"data/source-snapshots/regione-toscana-cultura-biblioteche-2024.json"
URL="https://dati.toscana.it/dataset/bf1166d3-b12a-4d07-a04f-49d9ca391a25/resource/6e2fd7ad-9699-4d1d-b90d-c96a69a18179/download/dataset_indicatori.csv"
LANDING="https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria"
FIELDS={
 "libraryActiveBorrowersPer100":("Indice di impatto Comunale","Indice di impatto Toscana"),
 "libraryLoansPerResident":("Indice di prestito Comunale","Indice di prestito Toscana"),
 "libraryWeeklyOpeningHours":("Ore medie di apertura settimanale Comunale","Ore medie di apertura settimanale Toscana"),
}
def norm(v:Any)->str:
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")
def code6(v:Any)->str:
    raw=str(v or "").strip()
    if not raw: return ""
    if re.fullmatch(r"\d+(?:\.0+)?",raw):
        digits=str(int(float(raw)))
    else:
        digits=re.sub(r"\D","",raw)
    return digits.zfill(6) if 1<=len(digits)<=6 else ""

def number(v:Any)->float|None:
    s=str(v or "").strip()
    if not s or s.casefold() in {"(null)","null","nan"}: return None
    s=s.replace(",",".")
    try:x=float(s)
    except ValueError:return None
    return x if math.isfinite(x) else None
def decode(blob:bytes)->str:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:return blob.decode(enc)
        except UnicodeDecodeError: pass
    return blob.decode("latin-1",errors="replace")
def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    r=requests.get(URL,timeout=180,headers={"User-Agent":"OsservatorioVersilia-A3-library-benchmark/1.0"}); r.raise_for_status()
    text=decode(r.content)
    try: delim=csv.Sniffer().sniff(text[:8192],delimiters=";,\t|").delimiter
    except csv.Error: delim=";"
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    rows=list(reader); headers=list(reader.fieldnames or [])
    by_norm={norm(h):h for h in headers}
    required={"anno","codistat","comune"}
    if not required.issubset(by_norm): raise RuntimeError(f"Biblioteche: schema base inatteso {headers[:30]}")
    resolved={}
    for mid,(communal,tuscany) in FIELDS.items():
        ck=by_norm.get(norm(communal)); tk=by_norm.get(norm(tuscany))
        if not ck or not tk: raise RuntimeError(f"{mid}: colonne mancanti {communal!r}/{tuscany!r}")
        resolved[mid]=(ck,tk)
    site=json.loads(SITE.read_text(encoding="utf-8"))
    governed=json.loads(GOVERNED.read_text(encoding="utf-8"))
    codes=set(governed["scope"]["townCodes"])
    if len(codes)!=7 or governed["scope"]["referenceYear"]!=2024:
        raise RuntimeError("Biblioteche: snapshot governato inatteso")
    current={row["code"]:row for row in governed["current2024"]}
    if set(current)!=codes:
        raise RuntimeError("Biblioteche: snapshot governato non 7/7")
    if current["046030"]["indicatorRowPresent"]:
        raise RuntimeError("Biblioteche: Stazzema deve restare assente, non zero")
    year=2024
    selected={}
    for row in rows:
        code=code6(row.get(by_norm["codistat"]))
        if code not in codes: continue
        try: row_year=int(float(str(row.get(by_norm["anno"]) or "").strip()))
        except Exception: continue
        if row_year!=year: continue
        selected[code]=row
    if set(selected)!=(codes-{"046030"}):
        raise RuntimeError(f"Biblioteche: copertura 2024 inattesa present={sorted(selected)}")
    benchmarks={}; errors=[]
    tolerances={"libraryActiveBorrowersPer100":.011,"libraryLoansPerResident":.011,"libraryWeeklyOpeningHours":.011}
    snapshot_field={
      "libraryActiveBorrowersPer100":"Indice di impatto Comunale",
      "libraryLoansPerResident":"Indice di prestito Comunale",
      "libraryWeeklyOpeningHours":"Ore medie di apertura settimanale Comunale",
    }
    for mid,(ck,tk) in resolved.items():
        tus=[]
        available=0
        for code,row in selected.items():
            src=number(row.get(ck))
            governed_row=(current[code].get("selectedIndicatorRow") or {})
            observed=number(governed_row.get(snapshot_field[mid]))
            if src is None and observed is None:
                continue
            if src is None or observed is None or not math.isclose(src,observed,rel_tol=0.0,abs_tol=tolerances[mid]):
                errors.append(f"{mid}/{code}: {src} != {observed}")
                continue
            available+=1
            tv=number(row.get(tk))
            if tv is not None: tus.append(tv)
        if available!=5:
            errors.append(f"{mid}: copertura numerica {available}/7 != 5/7 governata")
        distinct=[]
        for v in tus:
            if not any(math.isclose(v,x,rel_tol=0.0,abs_tol=1e-9) for x in distinct): distinct.append(v)
        if len(distinct)!=1:
            errors.append(f"{mid}: Toscana non univoca {distinct}")
            continue
        meta=((site["metrics"][mid].get("meta") or {}))
        benchmarks[mid]={"year":"2024","unit":str(meta.get("unit") or "decimal"),"tuscany":distinct[0],"italy":None,
          "formula":ck}
    gate="PASS" if not errors and len(benchmarks)==3 else "FAIL"
    payload={"schemaVersion":2,"publisher":"Regione Toscana","profileId":"regione-toscana-biblioteche-annual",
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED","sourceUrl":LANDING,
      "dataUrl":URL,"referenceYear":year,"benchmarks":benchmarks,
      "qualityGate":{"status":gate,"publicReconciliation":"3 metrics × 5/7 numeric + Massarosa/Stazzema n.d. governed PASS" if gate=="PASS" else "FAIL","missingPolicy":"Massarosa n.d.; Stazzema absent; no zero imputation","errors":errors}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(benchmarks),"year":year,"errors":errors[:20]},ensure_ascii=False))
if __name__=="__main__": main()
