#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,zipfile,io
from pathlib import Path
from typing import Any
import requests
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
URLS={
 "structures":"https://www.regione.toscana.it/documents/d/guest/1-consistenza-media-per-comune-e-tipologia-ricettiva-2025",
 "movement":"https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-",
 "monthly":"https://www.regione.toscana.it/documents/d/guest/5-movimento-comune_mese-2025-agg-maggio-2026-",
}
METRICS=["foreignTourismShare","tourismArrivals","tourismAverageStay","tourismBedsPer1000","tourismIntensity","tourismPresences","tourismSeasonality","tourismStructuresPer1000"]
TOWNS={"massarosa","viareggio","camaiore","pietrasanta","seravezza","forte dei marmi","stazzema","toscana"}
NS={
 "office":"urn:oasis:names:tc:opendocument:xmlns:office:1.0",
 "table":"urn:oasis:names:tc:opendocument:xmlns:table:1.0",
 "text":"urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

def cell_value(cell:ET.Element)->Any:
    typ=cell.attrib.get(f"{{{NS['office']}}}value-type")
    if typ in {"float","currency","percentage"}:
        raw=cell.attrib.get(f"{{{NS['office']}}}value")
        if raw is not None:
            try:return float(raw)
            except ValueError:pass
    if typ=="date":
        return cell.attrib.get(f"{{{NS['office']}}}date-value")
    texts=[]
    for p in cell.findall(".//text:p",NS):
        texts.append("".join(p.itertext()))
    return " ".join(x for x in texts if x).strip()

def parse_ods(blob:bytes)->dict[str,Any]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("content.xml"))
    sheets=[]
    for table in root.findall(".//table:table",NS):
        name=table.attrib.get(f"{{{NS['table']}}}name","")
        rows=[]; matched=[]
        physical=0
        for tr in table.findall("table:table-row",NS):
            repeat=int(tr.attrib.get(f"{{{NS['table']}}}number-rows-repeated","1"))
            vals=[]
            for cell in list(tr):
                if cell.tag not in {f"{{{NS['table']}}}table-cell",f"{{{NS['table']}}}covered-table-cell"}: continue
                rep=int(cell.attrib.get(f"{{{NS['table']}}}number-columns-repeated","1"))
                value=cell_value(cell)
                vals.extend([value]*min(rep,50))
                if len(vals)>=100: break
            while vals and vals[-1] in ("",None): vals.pop()
            if not vals:
                physical+=repeat; continue
            physical+=1
            text=" | ".join(str(x) for x in vals if x not in ("",None)).casefold()
            if len(rows)<35: rows.append({"row":physical,"values":vals})
            if any(t in text for t in TOWNS) and len(matched)<180:
                matched.append({"row":physical,"values":vals})
            physical+=max(0,repeat-1)
        sheets.append({"name":name,"preview":rows,"matched":matched})
    return {"sheets":sheets}

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    site=json.loads(SITE.read_text(encoding="utf-8"))
    contracts={}
    for mid in METRICS:
        m=(site.get("metrics") or {}).get(mid)
        if not isinstance(m,dict):
            contracts[mid]={"missing":True}; continue
        contracts[mid]={
          "meta":m.get("meta"),
          "sourceUrl":m.get("sourceUrl"),
          "method":m.get("method"),
          "aggregate":m.get("aggregate"),
          "rows":[{"town":r.get("town"),"code":r.get("code"),"value":r.get("value"),"parts":r.get("parts"),"population":r.get("population"),"beds":r.get("beds"),"structures":r.get("structures")} for r in (m.get("rows") or [])]
        }
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-tourism/1.0"
    sources={}
    for key,url in URLS.items():
        r=s.get(url,timeout=180); r.raise_for_status()
        sources[key]={"url":r.url,"bytes":len(r.content),"ods":parse_ods(r.content)}
    payload={
      "schemaVersion":1,"profileId":"regione-toscana-tourism-annual","referenceYear":2025,
      "status":"SOURCE_DIAGNOSTIC_READY","contracts":contracts,"sources":sources,
      "goal":"Derivare nello stesso universo ufficiale Regione Toscana i benchmark regionali 2025 e riconciliare 8 metriche × 7 Comuni; Italia resterà n.d. finché non viene agganciata una fonte Istat nazionale identica."
    }
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"metrics":len(contracts),"sources":{k:v["bytes"] for k,v in sources.items()}},ensure_ascii=False))
if __name__=="__main__": main()
