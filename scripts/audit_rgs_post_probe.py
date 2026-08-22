#!/usr/bin/env python3
from __future__ import annotations

import http.cookiejar
import re
import urllib.parse
import urllib.request

URL = 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34887/csv/5458/77e11303-b0f6-460a-b6b3-85e350300fac@rgs'
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
headers = {'User-Agent': 'Mozilla/5.0'}
with opener.open(urllib.request.Request(URL, headers=headers), timeout=30) as r:
    page = r.read().decode('utf-8', errors='replace')

m = re.search(r'name="form_build_id" value="([^"]+)"', page)
if not m:
    raise SystemExit('form_build_id non trovato')
form_build_id = m.group(1)
print('form_build_id', form_build_id)
form_match = re.search(r'(<form[^>]+id="metadata-download-form".*?</form>)', page, re.I | re.S)
if form_match:
    print('FORM_BLOCK_BEGIN')
    print(form_match.group(1)[:12000])
    print('FORM_BLOCK_END')

payload = urllib.parse.urlencode({
    'export_type': 'csv',
    'mail': '',
    'op': 'Scarica',
    'form_build_id': form_build_id,
    'form_id': 'metadata_download_form',
}).encode('utf-8')
req = urllib.request.Request(URL, data=payload, headers={**headers, 'Content-Type': 'application/x-www-form-urlencoded', 'Referer': URL})
with opener.open(req, timeout=60) as r:
    body = r.read()
    print('POST status', r.status)
    print('POST final-url', r.geturl())
    print('POST content-type', r.headers.get('Content-Type'))
    print('POST disposition', r.headers.get('Content-Disposition'))
    print('POST bytes', len(body))
    print('POST head', repr(body[:500]))
