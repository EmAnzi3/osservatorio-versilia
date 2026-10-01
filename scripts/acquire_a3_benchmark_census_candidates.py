#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import requests
URLS=[
 "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip",
 "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip"
]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-census-regional/1.0"
    probes=[]
    for url in URLS:
        try:
            r=s.get(url,timeout=180); probes.append({"url":url,"status":r.status_code,"bytes":len(r.content),"contentType":r.headers.get("content-type"),"ok":r.ok})
        except Exception as e: probes.append({"url":url,"ok":False,"error":f"{type(e).__name__}: {e}"})
    status="REGIONAL_SOURCE_AVAILABLE" if any(x.get("ok") for x in probes) else "REGIONAL_SOURCE_UNAVAILABLE"
    payload={"schemaVersion":1,"publisher":"Istat","profileId":"istat-census-annual","status":status,"probes":probes,"note":"Nessuna derivazione da Comuni_2023: il perimetro subcomunale non è usato come benchmark Toscana/Italia."}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"output":str(p)},ensure_ascii=False))
if __name__=="__main__": main()
