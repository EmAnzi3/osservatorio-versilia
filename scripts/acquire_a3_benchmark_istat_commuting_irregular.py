#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
FLOW="DF_BULK_PEND_LAV_2021_1"
BASE="https://esploradati.istat.it/SDMXWS/rest/data"
SOURCE_URL="https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/"
TUSCANY_PREFIXES={"045","046","047","048","049","050","051","052","053","100"}

def norm(v:Any)->str:
    return re.sub(r"[^a-z0-9]+","_",str(v or "").strip().lower()).strip("_")

def six(v:Any)->str:
    s=re.sub(r"\D","",str(v or "").strip())
    return s if len(s)==6 else ""

def num(v:Any)->float:
    s=str(v or "").strip().replace(",",".")
    x=float(s)
    if not math.isfinite(x): raise ValueError(v)
    return x

def decode_blob(blob:bytes)->str:
    if blob.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            members=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
            if not members: raise RuntimeError("Pendolarismo: ZIP senza CSV/TXT")
            member=max(members,key=lambda n:z.getinfo(n).file_size)
            blob=z.read(member)
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:return blob.decode(enc)
        except UnicodeDecodeError: pass
    return blob.decode("latin-1",errors="replace")

def fetch_matrix(session:requests.Session)->tuple[str,str]:
    attempts=[
      (f"{BASE}/IT1,{FLOW},1.0/all/all",{"format":"csvfile"}),
      (f"{BASE}/IT1,{FLOW},1.0/all",{"format":"csvfile"}),
      (f"{BASE}/{FLOW}/all/IT1",{"format":"csvfile"}),
      (f"{BASE}/{FLOW}/all",{"format":"csvfile"}),
      (f"{BASE}/IT1,{FLOW},1.0/",{"format":"csvfile"}),
      (f"{BASE}/{FLOW}/",{"format":"csvfile"}),
      (f"{BASE}/{FLOW}//IT1",{"format":"csvfile"}),
    ]
    errors=[]
    for url,params in attempts:
        try:
            r=session.get(url,params=params,timeout=300)
            r.raise_for_status()
            text=decode_blob(r.content)
            if len(text)>1000 and ("OBS_VALUE" in text or "obs_value" in text.lower()):
                return text,r.url
            errors.append(f"{r.url}: schema non riconosciuto bytes={len(r.content)}")
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(" | ".join(errors))

def pick_headers(headers:list[str])->tuple[str,str,str]:
    def score(header:str,tokens:tuple[str,...])->int:
        h=norm(header); return sum(1 for token in tokens if token in h)
    origins=sorted(((score(h,("orig","origine","residenza","partenza")),h) for h in headers),reverse=True)
    dests=sorted(((score(h,("dest","destin","lavoro","arrivo")),h) for h in headers),reverse=True)
    origin=origins[0][1] if origins and origins[0][0]>0 else None
    dest=dests[0][1] if dests and dests[0][0]>0 else None
    value=next((h for h in headers if norm(h) in {"obs_value","value","valore","numero"}),None)
    if not origin or not dest or origin==dest or not value:
        raise RuntimeError(f"Pendolarismo: header non risolti origin={origin} dest={dest} value={value}; headers={headers}")
    return origin,dest,value

def public_rows(site:dict,metric_id:str)->dict[str,dict]:
    metric=(site.get("metrics") or {}).get(metric_id) or {}
    rows={str(r.get("code") or ""):r for r in metric.get("rows") or [] if six(r.get("code"))}
    if len(rows)!=7: raise RuntimeError(f"{metric_id}: pubblico {len(rows)}/7")
    return rows

def aggregate_stats(flows:list[tuple[str,str,float]],scope:str)->dict[str,float]:
    internal=outbound=inbound=0.0
    def inside(code:str)->bool:
        return True if scope=="italy" else code[:3] in TUSCANY_PREFIXES
    origins=set()
    for o,d,v in flows:
        if inside(o):
            origins.add(o)
            if o==d: internal+=v
            else: outbound+=v
        if inside(d) and o!=d:
            inbound+=v
    resident=internal+outbound
    return {"internal":internal,"outbound":outbound,"inbound":inbound,"balance":inbound-outbound,"residentCommuters":resident,"municipalityOrigins":len(origins)}

def town_stats(flows:list[tuple[str,str,float]],codes:set[str])->dict[str,dict[str,float]]:
    out={c:{"internal":0.0,"outbound":0.0,"inbound":0.0} for c in codes}
    for o,d,v in flows:
        if o in out:
            if o==d: out[o]["internal"]+=v
            else: out[o]["outbound"]+=v
        if d in out and o!=d: out[d]["inbound"]+=v
    for d in out.values():
        d["balance"]=d["inbound"]-d["outbound"]
        d["residentCommuters"]=d["internal"]+d["outbound"]
    return out

def resolve_formula(metric_id:str,rows:dict[str,dict],stats:dict[str,dict])->tuple[str,callable]|None:
    if metric_id=="selfContainment":
        candidates={"internal/resident*100":lambda s:s["internal"]/s["residentCommuters"]*100.0}
    elif metric_id=="outsideMunicipality":
        candidates={"outbound/resident*100":lambda s:s["outbound"]/s["residentCommuters"]*100.0}
    elif metric_id=="inboundCommutersRate":
        candidates={
          "inbound/resident*100":lambda s:s["inbound"]/s["residentCommuters"]*100.0,
          "inbound/resident*1000":lambda s:s["inbound"]/s["residentCommuters"]*1000.0,
        }
    elif metric_id=="outboundCommutersRate":
        candidates={
          "outbound/resident*100":lambda s:s["outbound"]/s["residentCommuters"]*100.0,
          "outbound/resident*1000":lambda s:s["outbound"]/s["residentCommuters"]*1000.0,
        }
    elif metric_id=="commuterBalanceRate":
        candidates={
          "balance/resident*100":lambda s:s["balance"]/s["residentCommuters"]*100.0,
          "balance/resident*1000":lambda s:s["balance"]/s["residentCommuters"]*1000.0,
        }
    else:
        return None
    matches=[]
    for label,fn in candidates.items():
        ok=True
        for code,row in rows.items():
            try: expected=fn(stats[code]); observed=float(row["value"])
            except Exception: ok=False; break
            if not math.isclose(observed,expected,rel_tol=0.0,abs_tol=.11):
                ok=False; break
        if ok: matches.append((label,fn))
    return matches[0] if len(matches)==1 else None

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    session=requests.Session(); session.headers["User-Agent"]="OsservatorioVersilia-A3-commuting-benchmark/1.0"
    text,resolved=fetch_matrix(session)
    sample=text[:8192]
    try: delim=csv.Sniffer().sniff(sample,delimiters=",;|\t").delimiter
    except csv.Error: delim=","
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    headers=list(reader.fieldnames or [])
    origin_h,dest_h,value_h=pick_headers(headers)
    flows=[]; seen=set(); duplicates=[]; skipped=0
    for row in reader:
        o=six(row.get(origin_h)); d=six(row.get(dest_h))
        if not o or not d:
            skipped+=1; continue
        try:v=num(row.get(value_h))
        except Exception:
            skipped+=1; continue
        key=(o,d)
        if key in seen:
            duplicates.append(key)
            if len(duplicates)>=20: break
        seen.add(key); flows.append((o,d,v))
    if duplicates:
        raise RuntimeError(f"Pendolarismo: coppie O/D duplicate, dimensioni ulteriori non governate sample={duplicates}")
    if len(flows)<400000:
        raise RuntimeError(f"Pendolarismo: matrice troppo corta {len(flows)} righe")
    site=json.loads(SITE.read_text(encoding="utf-8"))
    metric_ids=[
      "commuterBalance","commuterBalanceRate","inboundCommuters","inboundCommutersRate",
      "outboundCommuters","outboundCommutersRate","outsideMunicipality","selfContainment",
    ]
    codes=set()
    public={}
    for mid in metric_ids:
        public[mid]=public_rows(site,mid); codes.update(public[mid])
    towns=town_stats(flows,codes)
    scopes={"tuscany":aggregate_stats(flows,"tuscany"),"italy":aggregate_stats(flows,"italy")}
    errors=[]; blocked={}; benchmarks={}

    direct={
      "inboundCommuters":"inbound","outboundCommuters":"outbound","commuterBalance":"balance",
    }
    for mid,key in direct.items():
        ok=True
        for code,row in public[mid].items():
            if not math.isclose(float(row["value"]),towns[code][key],rel_tol=0.0,abs_tol=.1):
                ok=False; break
        if ok:
            unit=str(((site["metrics"][mid].get("meta") or {}).get("unit")) or "number")
            benchmarks[mid]={"year":"2021","unit":unit,"formula":key,"tuscany":scopes["tuscany"][key],"italy":scopes["italy"][key]}
        else:
            blocked[mid]="conteggio pubblico 7/7 non riconciliato con matrice 2021"

    for mid in ("commuterBalanceRate","inboundCommutersRate","outboundCommutersRate","outsideMunicipality","selfContainment"):
        resolved_formula=resolve_formula(mid,public[mid],towns)
        if resolved_formula is None:
            blocked[mid]="formula pubblica non riconciliata in modo univoco sul denominatore residentCommuters"
            continue
        label,fn=resolved_formula
        unit=str(((site["metrics"][mid].get("meta") or {}).get("unit")) or "percent")
        benchmarks[mid]={"year":"2021","unit":unit,"formula":label,"tuscany":fn(scopes["tuscany"]),"italy":fn(scopes["italy"])}

    status="ACQUIRED_CANDIDATE" if benchmarks else "CANDIDATE_REJECTED"
    payload={
      "schemaVersion":1,"publisher":"Istat — Matrice di pendolarismo per lavoro 2021",
      "profileId":"istat-commuting-irregular","status":status,"sourceUrl":SOURCE_URL,
      "resolvedDataUrl":resolved,"headers":{"origin":origin_h,"destination":dest_h,"value":value_h,"all":headers},
      "matrixRows":len(flows),"skippedRows":skipped,"benchmarks":benchmarks,"scopes":scopes,
      "qualityGate":{"status":"PASS" if benchmarks else "FAIL","candidateCount":len(benchmarks),"public7of7":sorted(benchmarks),"errors":errors},
      "blocked":blocked,
    }
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"candidateMetrics":sorted(benchmarks),"matrixRows":len(flows),"blocked":blocked},ensure_ascii=False))
if __name__=="__main__": main()
