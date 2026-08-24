#!/usr/bin/env python3
from urllib.request import Request, urlopen

url = "https://dati.istruzione.it/opendata/opendata/catalog/EDIANAGRAFESTA202120242520250806.csv"
for headers in (
    {"User-Agent": "Mozilla/5.0 OsservatorioVersilia/1.0", "Accept": "text/csv,*/*"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36", "Accept": "text/csv,*/*", "Referer": "https://dati.istruzione.it/opendata/opendata/catalog/EDIANAGRAFESTA2021"},
):
    req = Request(url, headers=headers)
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(1000)
        print("REQUEST", headers)
        print("STATUS", resp.status)
        print("FINAL_URL", resp.geturl())
        print("CONTENT_TYPE", resp.headers.get("Content-Type"))
        print("CONTENT_DISPOSITION", resp.headers.get("Content-Disposition"))
        print("SET_COOKIE", resp.headers.get("Set-Cookie"))
        print("HEAD", repr(raw[:500]))
