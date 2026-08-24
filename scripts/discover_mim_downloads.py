#!/usr/bin/env python3
"""Diagnostica temporanea: scopre i link CSV esposti dalle pagine catalogo MIM."""
from __future__ import annotations

import html
import re
from urllib.parse import urljoin
from urllib.request import Request, urlopen

CODES = [
    "EDIANAGRAFESTA2021",
    "EDICONSICUREZZASTA2021",
    "EDISUPBARARCSTA2021",
    "EDIAMBFUNZSTA2021",
    "EDIETAORIGINESTA2021",
    "EDICOLLEGAMENTISTA2021",
]


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


for code in CODES:
    url = f"https://dati.istruzione.it/opendata/opendata/catalog/{code}"
    text = fetch(url)
    print(f"\n=== {code} {len(text):,} chars ===")
    candidates = []
    for match in re.finditer(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', text, flags=re.I):
        link = html.unescape(match.group(1))
        low = link.lower()
        if any(token in low for token in ("csv", "download", "202425", code.lower())):
            candidates.append(urljoin(url, link))
    # Alcuni template generano URL in JavaScript invece che in href.
    for match in re.finditer(r'''["']([^"']*(?:\.csv|202425|download)[^"']*)["']''', text, flags=re.I):
        link = html.unescape(match.group(1))
        if link and not link.startswith(("javascript:", "#")):
            candidates.append(urljoin(url, link))
    seen = set()
    for link in candidates:
        if link in seen:
            continue
        seen.add(link)
        print(link)
    if not seen:
        print("NO_DOWNLOAD_LINKS_FOUND")
        # utile per capire il template senza riversare tutta la pagina nei log
        for line in text.splitlines():
            low = line.lower()
            if "202425" in low or "csv" in low or "download" in low:
                print("HTML:", line.strip()[:2000])
