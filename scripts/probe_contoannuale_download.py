#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

URL = 'https://contoannuale.rgs.mef.gov.it/it/web/sicosito/download'
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (compatible; OsservatorioVersilia/1.0)'})
with urllib.request.urlopen(req, timeout=60) as response:
    page = response.read().decode('utf-8', errors='replace')
    print('status', response.status, 'bytes', len(page), 'final', response.geturl())

print('FORMS_BEGIN')
for match in re.finditer(r'<form\b.*?</form>', page, re.I | re.S):
    block = match.group(0)
    if any(token in block.lower() for token in ('download', 'anno', 'tipologia')):
        compact = re.sub(r'\s+', ' ', block)
        print(compact[:20000])
print('FORMS_END')

print('RESOURCE_URLS_BEGIN')
seen = set()
for candidate in re.findall(r'''(?:href|src|action)\s*=\s*["']([^"']+)["']''', page, re.I):
    url = urllib.parse.urljoin(URL, html.unescape(candidate))
    if any(token in url.lower() for token in ('download', 'resource', 'sico')) and url not in seen:
        seen.add(url)
        print(url)
for candidate in re.findall(r'''https?:\\?/\\?/[^"'<>\s]+''', page, re.I):
    url = html.unescape(candidate).replace('\\/', '/')
    if any(token in url.lower() for token in ('download', 'resource')) and url not in seen:
        seen.add(url)
        print(url)
print('RESOURCE_URLS_END')

print('RELEVANT_LINES_BEGIN')
for line in page.splitlines():
    low = line.lower()
    if any(token in low for token in ('download', 'tipologia', 'anno', 'resourceurl', 'resource_url', 'serve_resource', '.zip', '.csv')):
        cleaned = line.strip()
        if cleaned:
            print(cleaned[:6000])
print('RELEVANT_LINES_END')
