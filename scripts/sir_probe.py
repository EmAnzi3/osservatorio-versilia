#!/usr/bin/env python3
"""Minimal probe of SIR Toscana historical table HTML used by the validator."""
from __future__ import annotations
import json, re, urllib.parse, urllib.request
from pathlib import Path

BASE="https://www.sir.toscana.it"
UA="OsservatorioVersilia-SIRValidation/1.0"

def fetch(path:str, timeout=30)->dict:
    url=urllib.parse.urljoin(BASE,path)
    print(f"[sir-probe] GET {url}", flush=True)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(); enc=r.headers.get_content_charset() or "utf-8"; text=raw.decode(enc,errors="replace")
        compact=re.sub(r"\s+"," ",text).strip()
        print(f"[sir-probe] OK {len(text)} chars", flush=True)
        return {"url":url,"ok":True,"length":len(text),"content":compact[:30000]}
    except Exception as exc:
        print(f"[sir-probe] FAIL {exc!r}", flush=True)
        return {"url":url,"ok":False,"error":repr(exc)}

def main()->int:
    samples=[]
    # One coastal/valley station and one Apuan mountain station are enough to
    # establish the common HTML schema before the full validation download.
    tests=[
        ("Camaiore","TOS02004059","pluvio",2024),
        ("Camaiore","TOS02004059","termo",2024),
        ("Cardoso","TOS02000077","pluvio",2024),
    ]
    for name,sid,sensor,year in tests:
        samples.append({"station":name,"id":sid,"sensor":sensor,"year":year,
                        "panel":fetch(f"/archivio/stazione.php?IDST={sensor}&IDS={sid}"),
                        "data":fetch(f"/archivio/dati.php?A={year}&IDS={sid}&IDST={sensor}")})
    out={"samples":samples}
    dest=Path("reports/runtime/sir-probe.json"); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2)[:100000])
    return 0
if __name__=="__main__": raise SystemExit(main())
