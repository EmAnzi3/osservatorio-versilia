#!/usr/bin/env python3
from __future__ import annotations

import re
import urllib.parse
import urllib.request

URL = "https://contoannuale.rgs.mef.gov.it/it/web/sicosito/dipendenti/abitanti-comune-acc"
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersilia/1.0)"})
with urllib.request.urlopen(req, timeout=90) as response:
    page = response.read().decode("utf-8", errors="replace")
    print("status", response.status, "bytes", len(page), "final", response.geturl())

print("RELEVANT_URLS_BEGIN")
seen = set()
for candidate in re.findall(r'''(?:href|src|action)\s*=\s*["']([^"']+)["']''', page, re.I):
    url = urllib.parse.urljoin(URL, candidate.replace("&amp;", "&"))
    low = url.lower()
    if any(token in low for token in ("abitanti", "dipendenti", "resource", "ajax", "chart", "json", "api", "portlet")) and url not in seen:
        seen.add(url)
        print(url)
print("RELEVANT_URLS_END")

print("RELEVANT_LINES_BEGIN")
for line in page.splitlines():
    low = line.lower()
    if any(token in low for token in ("abitanti", "dipendenti", "resourceurl", "ajax", "json", "api", "portlet", "anno", "regione", "comune")):
        cleaned = line.strip()
        if cleaned:
            print(cleaned[:12000])
print("RELEVANT_LINES_END")
