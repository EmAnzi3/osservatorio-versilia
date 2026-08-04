#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests

OUT = Path("v12-extra")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersiliaDataAudit/1.2; +https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})


def download(url: str, name: str, *, method: str = "get", data: dict | None = None) -> dict:
    print(f"{method.upper()} {name}: {url}", flush=True)
    rec = {"name": name, "url": url, "method": method, "data": data}
    try:
        fn = S.post if method == "post" else S.get
        r = fn(url, data=data, timeout=(30, 240), allow_redirects=True, verify=False)
        rec.update(status=r.status_code, final_url=r.url, content_type=r.headers.get("content-type"), size=len(r.content))
        suffix = ".bin"
        ct = (r.headers.get("content-type") or "").lower()
        if r.content.startswith(b"PK"): suffix = ".zip"
        elif "html" in ct or b"<html" in r.content[:500].lower(): suffix = ".html"
        elif "csv" in ct: suffix = ".csv"
        path = OUT / f"{name}{suffix}"
        path.write_bytes(r.content)
        rec["path"] = str(path)
        print(f" -> {r.status_code} {ct} {len(r.content)} bytes", flush=True)
    except Exception as exc:
        rec["error"] = repr(exc)
        print(f" !! {exc!r}", flush=True)
    return rec


records = []
records.append(download("https://demo.istat.it/data/d7b/D7B2024.csv.zip", "istat-demographic-balance-2024"))
records.append(download("https://elezionistorico.interno.gov.it/daithome/documenti/opendata/europee/europee-20240609.zip", "eligendo-european-2024"))

omi_codes = {
    "camaiore": "B455",
    "forte-dei-marmi": "D730",
    "massarosa": "F035",
    "pietrasanta": "G628",
    "seravezza": "I622",
    "stazzema": "I942",
    "viareggio": "L833",
}
for slug, code in omi_codes.items():
    records.append(download(
        "https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm",
        f"omi-2025s2-{slug}",
        method="post",
        data={"level": "2", "lingua": "IT", "pr": "LU", "anno_semestre": "20252", "co": code},
    ))

(OUT / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(records, ensure_ascii=False, indent=2))
