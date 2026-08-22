#!/usr/bin/env python3
from __future__ import annotations

import io
import zipfile
import urllib.request

URL = 'https://bdap-opendata.rgs.mef.gov.it/metadata_download_page/34887/csv/5458/77e11303-b0f6-460a-b6b3-85e350300fac@rgs'
req = urllib.request.Request(URL, headers={'User-Agent': 'OsservatorioVersilia/1.0'})
with urllib.request.urlopen(req, timeout=30) as response:
    body = response.read()
    print('status', response.status)
    print('final-url', response.geturl())
    print('content-type', response.headers.get('Content-Type'))
    print('content-disposition', response.headers.get('Content-Disposition'))
    print('content-encoding', response.headers.get('Content-Encoding'))
    print('bytes', len(body))
    print('head-hex', body[:64].hex())
    print('head-repr', repr(body[:240]))
    if zipfile.is_zipfile(io.BytesIO(body)):
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            print('zip-members', zf.namelist())
            for name in zf.namelist()[:3]:
                sample = zf.read(name)[:500]
                print('member', name, 'head', repr(sample))
