#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("acquisition-diagnostics")
OUT.mkdir(exist_ok=True)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "OsservatorioVersiliaDataAudit/1.1 (+https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})
MAX_BYTES = 120_000_000


def safe_name(label: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", label).strip("-").lower()


def fetch(label: str, url: str, *, headers: dict | None = None) -> dict:
    print(f"FETCH {label}: {url}", flush=True)
    rec = {"label": label, "url": url}
    try:
        with SESSION.get(url, headers=headers or {}, timeout=(30, 100), allow_redirects=True, verify=False, stream=True) as r:
            chunks, size = [], 0
            for chunk in r.iter_content(1024 * 512):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_BYTES:
                    raise RuntimeError(f"response exceeds {MAX_BYTES} bytes")
                chunks.append(chunk)
            content = b"".join(chunks)
            rec.update({
                "status": r.status_code,
                "final_url": r.url,
                "content_type": r.headers.get("content-type"),
                "content_length": len(content),
                "headers": dict(r.headers),
            })
        ct = (rec.get("content_type") or "").lower()
        suffix = ".bin"
        if "html" in ct: suffix = ".html"
        elif "json" in ct: suffix = ".json"
        elif "csv" in ct or content[:500].count(b";") > 3 or content[:500].count(b",") > 5: suffix = ".csv"
        elif "xml" in ct or content.lstrip().startswith(b"<"): suffix = ".xml"
        elif content.startswith(b"PK"): suffix = ".zip"
        path = OUT / f"{safe_name(label)}{suffix}"
        path.write_bytes(content)
        rec["saved_as"] = str(path)
        if suffix == ".html":
            text = content.decode("utf-8", errors="replace")
            soup = BeautifulSoup(text, "html.parser")
            rec["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            rec["links"] = [
                {"text": a.get_text(" ", strip=True), "href": urljoin(rec["final_url"], a.get("href", ""))}
                for a in soup.find_all("a", href=True)
            ]
            rec["forms"] = []
            for form in soup.find_all("form"):
                rec["forms"].append({
                    "action": urljoin(rec["final_url"], form.get("action", "")),
                    "method": form.get("method", "get"),
                    "inputs": [
                        {"name": el.get("name"), "value": el.get("value"), "tag": el.name,
                         "options": [{"value": o.get("value"), "text": o.get_text(" ", strip=True)} for o in el.find_all("option")] if el.name == "select" else None}
                        for el in form.find_all(["input", "select", "button"])
                    ],
                })
        print(f"  -> {rec.get('status')} {rec.get('content_type')} {len(content)} bytes", flush=True)
    except Exception as exc:
        rec["error"] = repr(exc)
        print(f"  !! {exc!r}", flush=True)
    return rec


records: list[dict] = []
csv_accept = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0,text/csv,application/json,application/xml;q=0.8"}

# ISTAT regional flows: Toscana only, still detailed by municipality.
for label, url in {
    "istat-demographic-tuscany": "https://esploradati.istat.it/SDMXWS/rest/data/IT1,22_315_DF_DCIS_POPORESBIL1_12,1.0/all?startPeriod=2024&endPeriod=2024&format=csvfile",
    "istat-foreign-balance-tuscany": "https://esploradati.istat.it/SDMXWS/rest/data/IT1,29_316_DF_DCIS_POPSTRBIL1_11,1.0/all?startPeriod=2024&endPeriod=2024&format=csvfile",
    "istat-foreign-residents-tuscany": "https://esploradati.istat.it/SDMXWS/rest/data/IT1,29_7_DF_DCIS_POPSTRRES1_11,1.0/all?startPeriod=2025&endPeriod=2025&format=csvfile",
}.items():
    records.append(fetch(label, url, headers=csv_accept))

# AGCOM municipal broadband report.
records.append(fetch("agcom-municipal-coverage", "https://geo.agcom.it/arcgis/sharing/rest/content/items/25830559c5784c1eb5eb1cf748889f4c/data"))

# OpenCivitas welfare and nursery data page.
records.append(fetch("opencivitas-social-nursery-page", "https://www.opencivitas.it/it/dataset/2022-comuni-sociale-e-asili-nido-indicatori-e-determinanti"))
records.append(fetch("opencivitas-open-data", "https://www.opencivitas.it/it/open-data"))

# Ministry of Education school-building pages.
for label, url in {
    "school-anagraph-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0101EDIANAGRAFESTA2021",
    "school-environment-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0111EDIAMBIENTESTA2021",
    "school-structural-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0166EDIUNITASTRUTSTA",
}.items():
    records.append(fetch(label, url))

# Elections and OMI discovery pages.
for label, url in {
    "eligendo-home": "https://elezioni.interno.gov.it/opendata/",
    "eligendo-archive": "https://elezionistorico.interno.gov.it/index.php?tpel=E&dtel=09/06/2024&tpa=I&tpe=A&lev0=0&levsut0=0&es0=S&ms=S",
    "interior-elections-2024": "https://www.interno.gov.it/it/elezioni-2024",
    "omi-search": "https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm?lingua=IT",
    "omi-map": "https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm",
}.items():
    records.append(fetch(label, url))

(OUT / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "links.txt").open("w", encoding="utf-8") as fh:
    for rec in records:
        fh.write(f"\n## {rec['label']}\nURL: {rec['url']}\nSTATUS: {rec.get('status')}\nFINAL: {rec.get('final_url')}\n")
        for link in rec.get("links", []):
            if any(token in ((link.get("href") or "") + " " + (link.get("text") or "")).lower() for token in ["csv", "zip", "download", "opendata", "scarica", "json", "rdf"]):
                fh.write(f"- {link.get('text')!r}: {link.get('href')}\n")
        for form in rec.get("forms", []):
            fh.write(f"FORM {json.dumps(form, ensure_ascii=False)}\n")
print(json.dumps({"records": len(records), "output": str(OUT)}, indent=2))
