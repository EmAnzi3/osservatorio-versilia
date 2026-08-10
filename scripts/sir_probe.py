#!/usr/bin/env python3
"""Probe public SIR Toscana pages and document archive/data request contracts."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.sir.toscana.it"
PAGES = [
    "/consistenza-rete",
    "/index.php?IDS=191&IDSS=751",
    "/termometria-pub",
]
UA = "OsservatorioVersilia-SIRValidation/1.0"
MARKERS = [
    "function searchGauge", "function getData", "function getUrl",
    "ajax_stations", "archivio/stazione.php", "archivio/stazione_full.php",
    "archivio/dati.php", "&csv=1", "open_layers/ajax_stations.php",
]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.links = []
        self.scripts = []
        self.inputs = []
        self.options = []
        self._form = None
        self._select = None
        self._option = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._form = {"action": a.get("action"), "method": a.get("method"), "inputs": []}
            self.forms.append(self._form)
        elif tag == "input":
            item = {k: a.get(k) for k in ("name", "type", "value", "id")}
            self.inputs.append(item)
            if self._form is not None:
                self._form["inputs"].append(item)
        elif tag == "select":
            self._select = a.get("name") or a.get("id")
            item = {"name": a.get("name"), "type": "select", "value": None, "id": a.get("id")}
            self.inputs.append(item)
            if self._form is not None:
                self._form["inputs"].append(item)
        elif tag == "option":
            self._option = {"select": self._select, "value": a.get("value"), "text": ""}
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])

    def handle_data(self, data):
        if self._option is not None:
            self._option["text"] += data

    def handle_endtag(self, tag):
        if tag == "form":
            self._form = None
        elif tag == "select":
            self._select = None
        elif tag == "option" and self._option is not None:
            self._option["text"] = self._option["text"].strip()
            self.options.append(self._option)
            self._option = None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
        return raw.decode(enc, errors="replace")


def contexts(text: str, markers=MARKERS, radius=1000) -> dict[str, list[str]]:
    out = {}
    low = text.lower()
    for marker in markers:
        needle = marker.lower()
        pos = 0
        chunks = []
        while True:
            i = low.find(needle, pos)
            if i < 0:
                break
            chunks.append(text[max(0, i-radius):min(len(text), i+len(marker)+radius)])
            pos = i + len(marker)
            if len(chunks) >= 4:
                break
        if chunks:
            out[marker] = chunks
    return out


def try_url(path: str) -> dict:
    url = urllib.parse.urljoin(BASE, path)
    try:
        text = fetch(url)
        return {"url": url, "ok": True, "length": len(text), "head": text[:1200]}
    except Exception as exc:
        return {"url": url, "ok": False, "error": repr(exc)}


def main() -> int:
    out = {"base": BASE, "pages": [], "endpoint_tests": []}
    for path in PAGES:
        url = urllib.parse.urljoin(BASE, path)
        html = fetch(url)
        p = Parser(); p.feed(html)
        page = {
            "url": url,
            "length": len(html),
            "forms": p.forms,
            "inputs": p.inputs,
            "options_interesting": [o for o in p.options if any(x in (o.get("text") or "").casefold() for x in ("camaiore", "viareggio", "cardoso", "cervaiole", "forte", "seravezza", "pietrasanta"))],
            "contexts": contexts(html),
        }
        out["pages"].append(page)

    # Harmless GET probes against a known public station code. These help determine
    # whether archive endpoints use the public TOS code or an internal numeric id.
    for path in [
        "/archivio/stazione.php?IDST=TOS02004059",
        "/archivio/stazione_full.php?IDS=TOS02004059",
        "/archivio/dati.php?A=TOS02004059",
        "/monitoraggio/actions.php?action=list&type_gauge=pluvio",
        "/monitoraggio/actions.php?action=station&id=TOS02004059&type_gauge=pluvio",
    ]:
        out["endpoint_tests"].append(try_url(path))

    dest = Path("reports/runtime/sir-probe.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:70000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
