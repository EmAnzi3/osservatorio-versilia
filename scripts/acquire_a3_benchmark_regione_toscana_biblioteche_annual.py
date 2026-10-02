#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,io,json,math,re,unicodedata
from pathlib import Path
from typing import Any
import requests

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
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
    public={}
    codes=set()
    for mid in FIELDS:
        metric=(site.get("metrics") or {}).get(mid) or {}
        rr={str(x.get("code") or ""):x for x in metric.get("rows") or [] if str(x.get("code") or "")}
        if len(rr)!=7: raise RuntimeError(f"{mid}: pubblico {len(rr)}/7")
        public[mid]=rr; codes.update(rr)
    year_rows={}
    for row in rows:
        code=str(row.get(by_norm["codistat"]) or "").strip()
        if code not in codes: continue
        try: year=int(float(str(row.get(by_norm["anno"]) or "").strip()))
        except Exception: continue
        year_rows.setdefault(year,{})[code]=row
    eligible=[y for y,m in year_rows.items() if set(m)==codes]
    if not eligible: raise RuntimeError("Biblioteche: nessuna annualità 7/7")
    year=max(eligible); selected=year_rows[year]
    benchmarks={}; errors=[]
    tolerances={"libraryActiveBorrowersPer100":.011,"libraryLoansPerResident":.011,"libraryWeeklyOpeningHours":.011}
    for mid,(ck,tk) in resolved.items():
        tus=[]
        for code,row in selected.items():
            src=number(row.get(ck)); observed=number(public[mid][code].get("value"))
            if src is None or observed is None or not math.isclose(src,observed,rel_tol=0.0,abs_tol=tolerances[mid]):
                errors.append(f"{mid}/{code}: {src} != {observed}")
            tv=number(row.get(tk))
            if tv is not None: tus.append(tv)
        distinct=[]
        for v in tus:
            if not any(math.isclose(v,x,rel_tol=0.0,abs_tol=1e-9) for x in distinct): distinct.append(v)
        if len(distinct)!=1:
            errors.append(f"{mid}: Toscana non univoca {distinct}")
            continue
        meta=((site["metrics"][mid].get("meta") or {}))
        benchmarks[mid]={"year":str(year),"unit":str(meta.get("unit") or "decimal"),"tuscany":distinct[0],"italy":None,
          "formula":ck}
    gate="PASS" if not errors and len(benchmarks)==3 else "FAIL"
    payload={"schemaVersion":1,"publisher":"Regione Toscana","profileId":"regione-toscana-biblioteche-annual",
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED","sourceUrl":LANDING,
      "dataUrl":URL,"referenceYear":year,"benchmarks":benchmarks,
      "qualityGate":{"status":gate,"publicReconciliation":"3 metrics × 7/7 PASS" if gate=="PASS" else "FAIL","errors":errors}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(benchmarks),"year":year,"errors":errors[:20]},ensure_ascii=False))
if __name__=="__main__": main()
