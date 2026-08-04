#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("acquisition-diagnostics")
OUT.mkdir(exist_ok=True)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "OsservatorioVersiliaDataAudit/1.0 (+https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})


def safe_name(label: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", label).strip("-").lower()


def fetch(label: str, url: str, *, headers: dict | None = None, allow_redirects: bool = True) -> dict:
    print(f"FETCH {label}: {url}", flush=True)
    rec = {"label": label, "url": url}
    try:
        r = SESSION.get(url, headers=headers or {}, timeout=240, allow_redirects=allow_redirects, verify=False)
        rec.update({
            "status": r.status_code,
            "final_url": r.url,
            "content_type": r.headers.get("content-type"),
            "content_length": len(r.content),
            "headers": dict(r.headers),
        })
        suffix = ".bin"
        ct = (r.headers.get("content-type") or "").lower()
        if "html" in ct: suffix = ".html"
        elif "json" in ct: suffix = ".json"
        elif "csv" in ct or r.content[:100].count(b";") > 2 or r.content[:100].count(b",") > 2: suffix = ".csv"
        elif "xml" in ct or r.content.lstrip().startswith(b"<"): suffix = ".xml"
        elif r.content.startswith(b"PK"): suffix = ".zip"
        path = OUT / f"{safe_name(label)}{suffix}"
        path.write_bytes(r.content)
        rec["saved_as"] = str(path)
        if suffix == ".html":
            soup = BeautifulSoup(r.text, "html.parser")
            rec["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            rec["links"] = [
                {"text": a.get_text(" ", strip=True), "href": urljoin(r.url, a.get("href", ""))}
                for a in soup.find_all("a", href=True)
            ]
            rec["forms"] = []
            for form in soup.find_all("form"):
                rec["forms"].append({
                    "action": urljoin(r.url, form.get("action", "")),
                    "method": form.get("method", "get"),
                    "inputs": [
                        {"name": el.get("name"), "value": el.get("value"), "type": el.name, "options": [o.get("value") for o in el.find_all("option")] if el.name == "select" else None}
                        for el in form.find_all(["input", "select", "button"])
                    ],
                })
        print(f"  -> {r.status_code} {rec['content_type']} {len(r.content)} bytes", flush=True)
    except Exception as exc:
        rec["error"] = repr(exc)
        print(f"  !! {exc!r}", flush=True)
    return rec


records = []

# ISTAT: municipal demographic balance and foreign population balance.
istat_urls = {
    "istat-demographic-flow": "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/22_315_DF_DCIS_POPORESBIL1_24/1.0?references=all&format=jsonstructure",
    "istat-demographic-data-new": "https://esploradati.istat.it/SDMXWS/rest/data/IT1,22_315_DF_DCIS_POPORESBIL1_24,1.0/all?startPeriod=2024&endPeriod=2024&format=csvfile",
    "istat-demographic-data-legacy": "https://sdmx.istat.it/SDMXWS/rest/data/22_315_DF_DCIS_POPORESBIL1_24/all?startPeriod=2024&endPeriod=2024",
    "istat-foreign-flow": "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/29_316_DF_DCIS_POPSTRBIL1_23/1.0?references=all&format=jsonstructure",
    "istat-foreign-data-new": "https://esploradati.istat.it/SDMXWS/rest/data/IT1,29_316_DF_DCIS_POPSTRBIL1_23,1.0/all?startPeriod=2024&endPeriod=2024&format=csvfile",
    "istat-foreign-data-legacy": "https://sdmx.istat.it/SDMXWS/rest/data/29_316_DF_DCIS_POPSTRBIL1_23/all?startPeriod=2024&endPeriod=2024",
}
for label, url in istat_urls.items():
    headers = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0,text/csv,application/json,application/xml;q=0.8"}
    records.append(fetch(label, url, headers=headers))

# AGCOM municipal broadband report.
records.append(fetch(
    "agcom-municipal-coverage",
    "https://geo.agcom.it/arcgis/sharing/rest/content/items/25830559c5784c1eb5eb1cf748889f4c/data",
))

# OpenCivitas welfare and nursery data page.
records.append(fetch(
    "opencivitas-social-nursery-page",
    "https://www.opencivitas.it/it/dataset/2022-comuni-sociale-e-asili-nido-indicatori-e-determinanti",
))
records.append(fetch("opencivitas-open-data", "https://www.opencivitas.it/it/open-data"))

# Ministry of Education: school-building data pages; HTML contains direct CSV links.
school_pages = {
    "school-anagraph-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0101EDIANAGRAFESTA2021",
    "school-environment-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0111EDIAMBIENTESTA2021",
    "school-structural-page": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0166EDIUNITASTRUTSTA",
}
for label, url in school_pages.items():
    records.append(fetch(label, url))

# Elections open-data pages.
election_pages = {
    "eligendo-home": "https://elezioni.interno.gov.it/opendata/",
    "eligendo-archive": "https://elezionistorico.interno.gov.it/index.php?tpel=E&dtel=09/06/2024&tpa=I&tpe=A&lev0=0&levsut0=0&es0=S&ms=S",
    "interior-elections-2024": "https://www.interno.gov.it/it/elezioni-2024",
}
for label, url in election_pages.items():
    records.append(fetch(label, url))

# OMI official consultation pages.
omi_pages = {
    "omi-search": "https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm?lingua=IT",
    "omi-map": "https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm",
}
for label, url in omi_pages.items():
    records.append(fetch(label, url))

(OUT / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

# Human-readable link index.
with (OUT / "links.txt").open("w", encoding="utf-8") as fh:
    for rec in records:
        fh.write(f"\n## {rec['label']}\nURL: {rec['url']}\nSTATUS: {rec.get('status')}\nFINAL: {rec.get('final_url')}\n")
        for link in rec.get("links", []):
            if any(token in (link.get("href") or "").lower() for token in ["csv", "zip", "download", "opendata", "scarica", "json", "rdf"]):
                fh.write(f"- {link.get('text')!r}: {link.get('href')}\n")
        for form in rec.get("forms", []):
            fh.write(f"FORM {form}\n")

print(json.dumps({"records": len(records), "output": str(OUT)}, indent=2))
