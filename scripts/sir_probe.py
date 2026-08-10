#!/usr/bin/env python3
"""Probe the public SIR Toscana archive page to discover reproducible data endpoints.

This is intentionally diagnostic: it records forms, script assets, links and likely
API/download endpoint strings from the official SIR site without assuming an
undocumented URL contract.
"""
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
    "/index.php?IDS=191&IDSS=751",  # pluviometria public page
    "/termometria-pub",
]
UA = "OsservatorioVersilia-SIRValidation/1.0"


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.links = []
        self.scripts = []
        self.inputs = []
        self._form = None

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
            item = {"name": a.get("name"), "type": "select", "value": None, "id": a.get("id")}
            self.inputs.append(item)
            if self._form is not None:
                self._form["inputs"].append(item)
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "form":
            self._form = None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
        return raw.decode(enc, errors="replace")


def likely_strings(text: str):
    patterns = [
        r"[\"']([^\"']*(?:ajax|download|scaric|csv|json|archiv|sensor|stazion|dati)[^\"']*)[\"']",
        r"(?:url|action)\s*[:=]\s*[\"']([^\"']+)[\"']",
        r"(?:fetch|ajax|post|get)\s*\(\s*[\"']([^\"']+)[\"']",
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.I):
            s = m.group(1).strip()
            if 1 < len(s) < 300:
                found.add(s)
    return sorted(found)


def main() -> int:
    out = {"base": BASE, "pages": [], "scripts": {}}
    script_urls = set()
    for path in PAGES:
        url = urllib.parse.urljoin(BASE, path)
        html = fetch(url)
        p = Parser()
        p.feed(html)
        page = {
            "url": url,
            "length": len(html),
            "forms": p.forms,
            "inputs": p.inputs,
            "links_likely": sorted({x for x in p.links if re.search(r"ajax|download|scaric|csv|json|archiv|sensor|stazion|dati", x, re.I)}),
            "scripts": p.scripts,
            "likely_strings": likely_strings(html),
        }
        out["pages"].append(page)
        for src in p.scripts:
            script_urls.add(urllib.parse.urljoin(url, src))

    for url in sorted(script_urls):
        if not url.startswith(BASE):
            continue
        try:
            text = fetch(url)
        except Exception as exc:
            out["scripts"][url] = {"error": repr(exc)}
            continue
        hits = likely_strings(text)
        if hits:
            out["scripts"][url] = {"length": len(text), "likely_strings": hits}

    dest = Path("reports/runtime/sir-probe.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:30000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
