#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

URL = 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34887/csv/5458/77e11303-b0f6-460a-b6b3-85e350300fac@rgs'
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as response:
    raw = response.read().decode('utf-8', errors='replace')
    print('bytes', len(raw))
    links = re.findall(r'''(?:href|src|action)\s*=\s*["']([^"']+)["']''', raw, re.I)
    print('LINKS')
    for link in links:
        absolute = urllib.parse.urljoin(URL, html.unescape(link))
        print(absolute)
    print('MATCHING_LINES')
    for line in raw.splitlines():
        if any(token in line.lower() for token in ('csv', 'export', 'download', 'odata', 'xml', 'json')):
            print(line.strip()[:2000])
