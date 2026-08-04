#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("v12-school-omi")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersiliaDataAudit/1.2; +https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})


def save_response(r: requests.Response, name: str) -> dict:
    ct = (r.headers.get("content-type") or "").lower()
    suffix = ".bin"
    if r.content.startswith(b"PK"): suffix = ".zip"
    elif "html" in ct or b"<html" in r.content[:500].lower(): suffix = ".html"
    elif "csv" in ct or r.content[:1000].count(b",") > 5: suffix = ".csv"
    path = OUT / f"{name}{suffix}"
    path.write_bytes(r.content)
    print(name, r.status_code, ct, len(r.content), flush=True)
    return {"name": name, "url": r.url, "status": r.status_code, "content_type": ct, "size": len(r.content), "path": str(path)}


records = []
for name, url in {
    "school-accessibility-202425": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/EDISUPBARARCSTA202120242520250806.csv",
    "school-safety-202425": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/EDICONSICUREZZASTA202120242520250806.csv",
}.items():
    r = S.get(url, timeout=(30, 240), verify=False)
    records.append(save_response(r, name))

omi_codes = {
    "camaiore": "B455",
    "forte-dei-marmi": "D730",
    "massarosa": "F035",
    "pietrasanta": "G628",
    "seravezza": "I622",
    "stazzema": "I942",
    "viareggio": "L833",
}
endpoint = "https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm"
for town, code in omi_codes.items():
    step = S.post(endpoint, data={"level": "2", "lingua": "IT", "pr": "LU", "anno_semestre": "20252", "co": code}, timeout=(30, 120), verify=False)
    records.append(save_response(step, f"omi-zones-{town}"))
    soup = BeautifulSoup(step.content, "html.parser")
    select = soup.find("select", attrs={"name": "linkzonastrada"})
    if not select:
        continue
    zones = [(o.get("value"), o.get_text(" ", strip=True)) for o in select.find_all("option") if o.get("value")]
    for index, (zone, label) in enumerate(zones, start=1):
        r = S.post(endpoint, data={
            "level": "4", "lingua": "IT", "pr": "LU", "co": code,
            "anno_semestre": "20252", "linkzonastrada": zone,
        }, timeout=(30, 120), verify=False)
        rec = save_response(r, f"omi-quote-{town}-{index:02d}-{zone}")
        rec["town"] = town
        rec["zone"] = zone
        rec["zone_label"] = label
        records.append(rec)

(OUT / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
