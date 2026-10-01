#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,re,zipfile
from collections import defaultdict
from pathlib import Path
import requests

POSAS="https://demo.istat.it/data/posas/POSAS_2026_it_Comuni.zip"
P2="https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip"
TOSC_PROV={"045","046","047","048","049","050","051","052","053","100"}
def n(x):
    try:return float(str(x or "0").replace(",","."))
    except:return 0.0
def norm(x):
    import unicodedata
    s=unicodedata.normalize("NFKD",str(x or "")); s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+"," ",s.lower()).strip()
def ziprows(session,url):
    r=session.get(url,timeout=240); r.raise_for_status()
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=[x for x in z.namelist() if x.lower().endswith((".csv",".txt"))]
    if len(names)!=1: raise RuntimeError(f"Archivio inatteso {url}: {names}")
    text=z.read(names[0]).decode("utf-8-sig",errors="replace")
    lines=text.splitlines()
    # POSAS/P2 hanno spesso una riga titolo prima dell'header.
    start=next((i for i,l in enumerate(lines[:10]) if "Codice comune" in l or "Codice Comune" in l),0)
    body="\n".join(lines[start:])
    try:d=csv.Sniffer().sniff(body[:8000],delimiters=";,\t").delimiter
    except:d=";"
    return list(csv.DictReader(io.StringIO(body),delimiter=d)),names[0]
def aggregate_posas(rows,pred):
    ages=defaultdict(float)
    for r in rows:
        code=re.sub(r"\D","",str(r.get("Codice comune") or ""))[-6:].zfill(6)
        if not pred(code): continue
        age=str(r.get("Età") or "").strip()
        total=n(r.get("Totale"))
        ages[age]+=total
    def age_num(k):
        try:return int(k)
        except:return None
    total=sum(ages.values()); a014=sum(v for k,v in ages.items() if age_num(k) is not None and age_num(k)<=14)
    a1564=sum(v for k,v in ages.items() if age_num(k) is not None and 15<=age_num(k)<=64)
    a65=sum(v for k,v in ages.items() if age_num(k) is not None and age_num(k)>=65)
    return {"population":total,"age0_14":a014,"age15_64":a1564,"age65plus":a65,"structuralDependencyIndex":(a014+a65)/a1564*100 if a1564 else None,"oldAgeDependencyIndex":a65/a1564*100 if a1564 else None,"ageDistribution":{"0-14":a014/total*100 if total else None,"15-64":a1564/total*100 if total else None,"65+":a65/total*100 if total else None}}
def aggregate_p2(rows,pred):
    if not rows:return {}
    numeric=defaultdict(float); headers=list(rows[0])
    for r in rows:
        code=""
        for h in headers:
            if norm(h) in {"codice comune","codice comune formato numerico"}:
                code=re.sub(r"\D","",str(r.get(h) or ""))[-6:].zfill(6); break
        if not code or not pred(code): continue
        for h,v in r.items():
            if h and any(tok in norm(h) for tok in ("popolazione","nati vivi","morti","saldo naturale","iscritti","cancellati","saldo migratorio")):
                numeric[h]+=n(v)
    return dict(numeric)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-demography-benchmark/1.0"
    pos,pos_member=ziprows(s,POSAS); p2,p2_member=ziprows(s,P2)
    pred_t=lambda code: code[:3] in TOSC_PROV
    pred_i=lambda code: True
    payload={"schemaVersion":1,"publisher":"Istat","profileId":"istat-demography-annual","reference":{"posas":2026,"p2":2025},"sources":{"posas":POSAS,"p2":P2},"archiveMembers":{"posas":pos_member,"p2":p2_member},"candidates":{"tuscany":{"posas":aggregate_posas(pos,pred_t),"p2":aggregate_p2(p2,pred_t)},"italy":{"posas":aggregate_posas(pos,pred_i),"p2":aggregate_p2(p2,pred_i)}},"status":"ACQUIRED_CANDIDATE"}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"metrics":["population","ageDistribution","dependencyIndices","P2 demographic flows"],"output":str(p)},ensure_ascii=False))
if __name__=="__main__": main()
