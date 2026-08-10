#!/usr/bin/env python3
"""Probe public SIR Toscana pages and sample historical archive tables."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.sir.toscana.it"
PAGES = ["/consistenza-rete"]
UA = "OsservatorioVersilia-SIRValidation/1.0"
MARKERS = ["function getData", "archivio/stazione.php", "archivio/dati.php"]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.forms=[]; self.inputs=[]; self.options=[]; self._form=None; self._select=None; self._option=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="form": self._form={"action":a.get("action"),"method":a.get("method"),"inputs":[]}; self.forms.append(self._form)
        elif tag=="input":
            item={k:a.get(k) for k in ("name","type","value","id")}; self.inputs.append(item)
            if self._form is not None: self._form["inputs"].append(item)
        elif tag=="select": self._select=a.get("name") or a.get("id")
        elif tag=="option": self._option={"select":self._select,"value":a.get("value"),"text":""}
    def handle_data(self,data):
        if self._option is not None: self._option["text"]+=data
    def handle_endtag(self,tag):
        if tag=="form": self._form=None
        elif tag=="select": self._select=None
        elif tag=="option" and self._option is not None:
            self._option["text"]=self._option["text"].strip(); self.options.append(self._option); self._option=None


def fetch(url:str)->str:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read(); enc=r.headers.get_content_charset() or "utf-8"; return raw.decode(enc,errors="replace")


def compact(text:str,limit=12000)->str:
    text=re.sub(r"\s+"," ",text).strip()
    return text[:limit]


def sample(path:str)->dict:
    url=urllib.parse.urljoin(BASE,path)
    try:
        text=fetch(url)
        return {"url":url,"ok":True,"length":len(text),"content":compact(text)}
    except Exception as exc:
        return {"url":url,"ok":False,"error":repr(exc)}


def main()->int:
    html=fetch(urllib.parse.urljoin(BASE,"/consistenza-rete"))
    p=Parser(); p.feed(html)
    out={
        "archive_notice": compact(html[html.find("È possibile visualizzare"):html.find("All'utilizzatore")+500],3000),
        "samples": []
    }
    targets=[
        ("Camaiore","TOS02004059"),
        ("Cardoso","TOS02000077"),
        ("Cervaiole","TOS02000081"),
    ]
    for name,station in targets:
        out["samples"].append({"station":name,"id":station,"full":sample(f"/archivio/stazione_full.php?IDS={station}")})
        for sensor in ("pluvio","termo"):
            out["samples"].append({"station":name,"id":station,"sensor":sensor,"station_panel":sample(f"/archivio/stazione.php?IDST={sensor}&IDS={station}")})
            out["samples"].append({"station":name,"id":station,"sensor":sensor,"year":2024,"data":sample(f"/archivio/dati.php?A=2024&IDS={station}&IDST={sensor}")})
            out["samples"].append({"station":name,"id":station,"sensor":sensor,"year":2015,"data":sample(f"/archivio/dati.php?A=2015&IDS={station}&IDST={sensor}")})
    dest=Path("reports/runtime/sir-probe.json"); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2)[:100000])
    return 0

if __name__=="__main__": raise SystemExit(main())
