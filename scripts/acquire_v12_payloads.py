#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("v12-payloads")
OUT.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersiliaDataAudit/1.2; +https://github.com/EmAnzi3/osservatorio-versilia)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
})
MAX_BYTES = 250_000_000


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", v.lower()).strip("-")


def get(url: str, name: str, *, method: str = "get", data: dict | None = None, headers: dict | None = None) -> dict:
    print(f"{method.upper()} {name}: {url}", flush=True)
    rec = {"name": name, "url": url, "method": method, "data": data}
    try:
        req = S.post if method == "post" else S.get
        with req(url, data=data, headers=headers or {}, timeout=(30, 180), stream=True, allow_redirects=True, verify=False) as r:
            chunks, n = [], 0
            for chunk in r.iter_content(512 * 1024):
                if not chunk:
                    continue
                n += len(chunk)
                if n > MAX_BYTES:
                    raise RuntimeError(f"payload exceeds {MAX_BYTES} bytes")
                chunks.append(chunk)
            content = b"".join(chunks)
            rec.update(status=r.status_code, final_url=r.url, content_type=r.headers.get("content-type"), size=len(content))
        ct = (rec.get("content_type") or "").lower()
        suffix = ".bin"
        if content.startswith(b"PK"): suffix = ".zip"
        elif "csv" in ct or content[:1000].count(b";") > 4 or content[:1000].count(b",") > 8: suffix = ".csv"
        elif "json" in ct: suffix = ".json"
        elif "html" in ct or b"<html" in content[:300].lower(): suffix = ".html"
        elif "xml" in ct or content.lstrip().startswith(b"<"): suffix = ".xml"
        path = OUT / f"{slug(name)}{suffix}"
        path.write_bytes(content)
        rec["path"] = str(path)
        if suffix == ".html":
            text = content.decode("utf-8", errors="replace")
            soup = BeautifulSoup(text, "html.parser")
            rec["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            rec["links"] = [{"text": a.get_text(" ", strip=True), "href": urljoin(r.url, a.get("href", ""))} for a in soup.find_all("a", href=True)]
            rec["forms"] = []
            for form in soup.find_all("form"):
                rec["forms"].append({
                    "id": form.get("id"),
                    "action": urljoin(r.url, form.get("action", "")),
                    "method": form.get("method", "get").lower(),
                    "controls": [
                        {"tag": el.name, "name": el.get("name"), "value": el.get("value"),
                         "options": [{"value": o.get("value"), "text": o.get_text(" ", strip=True)} for o in el.find_all("option")] if el.name == "select" else None}
                        for el in form.find_all(["input", "select", "button"])
                    ],
                })
        print(f" -> {rec.get('status')} {rec.get('content_type')} {rec.get('size')} bytes", flush=True)
    except Exception as exc:
        rec["error"] = repr(exc)
        print(f" !! {exc!r}", flush=True)
    return rec


records: list[dict] = []

# OpenCivitas: data and official metadata.
for name, url in {
    "opencivitas-social-nursery-data": "https://docs.opencivitas.it/2022_Ind_FC80SOCNID_1_csv.zip",
    "opencivitas-social-nursery-variable-metadata": "https://docs.opencivitas.it/2022_Metadati_Ind_FC80SOCNID_1_xlsx.zip",
    "opencivitas-entity-metadata": "https://docs.opencivitas.it/Metadati_Enti_2022_xlsx.zip",
}.items():
    records.append(get(url, name))

# School buildings: official 2024/25 CSVs and record metadata.
school_files = {
    "school-anagraph-202425": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/EDIANAGRAFESTA202120242520250806.csv",
    "school-environment-202425": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/EDIAMBIENTESTA202120242520250806.csv",
    "school-structural-202425": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/EDIUNITASTRUTSTA20242520250806.csv",
}
for name, url in school_files.items():
    records.append(get(url, name))

# The metadata endpoints are extracted from the official catalog pages.
for name, url in {
    "school-anagraph-metadata": "https://dati.istruzione.it/opendata/opendata/sparql/endpoint/query/ExportServlet?query=SELECT%20DISTINCT%20%3FAttributo%20%3FEtichetta%20%3FDescrizione%20%3FTipoDato%20WHERE%20%7B%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23describe%3E%20%3Fdset.%20%3Fdset%20%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2Fidentifier%3E%20%3Fidentifier.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Posizione%3E%20%3FPosizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Attributo%3E%20%3FAttributo.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Etichetta%3E%20%3FEtichetta.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Descrizione%3E%20%3FDescrizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23TipoDato%3E%20%3FTipoDato.%20FILTER%20regex%20%28%3Fidentifier%2C%22DS0101EDIANAGRAFESTA2021%22%29%7D%20order%20by%20%3FPosizione&dataset=/metadata&dataType=csv&datasetId=DS0101EDIANAGRAFESTA2021",
    "school-environment-metadata": "https://dati.istruzione.it/opendata/opendata/sparql/endpoint/query/ExportServlet?query=SELECT%20DISTINCT%20%3FAttributo%20%3FEtichetta%20%3FDescrizione%20%3FTipoDato%20WHERE%20%7B%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23describe%3E%20%3Fdset.%20%3Fdset%20%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2Fidentifier%3E%20%3Fidentifier.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Posizione%3E%20%3FPosizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Attributo%3E%20%3FAttributo.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Etichetta%3E%20%3FEtichetta.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Descrizione%3E%20%3FDescrizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23TipoDato%3E%20%3FTipoDato.%20FILTER%20regex%20%28%3Fidentifier%2C%22DS0111EDIAMBIENTESTA2021%22%29%7D%20order%20by%20%3FPosizione&dataset=/metadata&dataType=csv&datasetId=DS0111EDIAMBIENTESTA2021",
    "school-structural-metadata": "https://dati.istruzione.it/opendata/opendata/sparql/endpoint/query/ExportServlet?query=SELECT%20DISTINCT%20%3FAttributo%20%3FEtichetta%20%3FDescrizione%20%3FTipoDato%20WHERE%20%7B%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23describe%3E%20%3Fdset.%20%3Fdset%20%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2Fidentifier%3E%20%3Fidentifier.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Posizione%3E%20%3FPosizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Attributo%3E%20%3FAttributo.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Etichetta%3E%20%3FEtichetta.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23Descrizione%3E%20%3FDescrizione.%20%3Fsubject%20%3Chttp%3A%2F%2Fwww.miur.it%2Fns%2Fmiur%23TipoDato%3E%20%3FTipoDato.%20FILTER%20regex%20%28%3Fidentifier%2C%22DS0166EDIUNITASTRUTSTA%22%29%7D%20order%20by%20%3FPosizione&dataset=/metadata&dataType=csv&datasetId=DS0166EDIUNITASTRUTSTA",
}.items():
    records.append(get(url, name))

# Istat monthly demographic balance: discover and download the official 2024 ZIP.
demo = get("https://demo.istat.it/app/?a=2024&i=D7B&l=it", "istat-demographic-demo-2024")
records.append(demo)
for i, link in enumerate(demo.get("links", []), start=1):
    href = link.get("href") or ""
    text = (link.get("text") or "").lower()
    if href.lower().endswith(".zip") and ("2024" in href or "2024" in text):
        records.append(get(href, f"istat-demographic-2024-zip-{i}"))

# Ministry of the Interior: discover open-data files and download 2024 European election archives.
eligendo = get("https://elezionistorico.interno.gov.it/eligendo/opendata.php", "eligendo-open-data")
records.append(eligendo)
for i, link in enumerate(eligendo.get("links", []), start=1):
    href = link.get("href") or ""
    hay = ((link.get("text") or "") + " " + href).lower()
    if any(ext in href.lower() for ext in [".zip", ".csv"]) and "2024" in hay and any(k in hay for k in ["euro", "europe"]):
        records.append(get(href, f"eligendo-european-2024-{i}"))

# OMI: reproduce the official consultation steps for Lucca province.
omi_start = get("https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm?lingua=IT", "omi-start")
records.append(omi_start)
omi_lucca = get("https://www1.agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm", "omi-lucca-step", method="post", data={"level": "1", "lingua": "IT", "pr": "LU"})
records.append(omi_lucca)

(OUT / "summary.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "links.txt").open("w", encoding="utf-8") as fh:
    for rec in records:
        fh.write(f"\n## {rec['name']}\nSTATUS {rec.get('status')}\nURL {rec.get('url')}\nFINAL {rec.get('final_url')}\nPATH {rec.get('path')}\n")
        for link in rec.get("links", []):
            href = link.get("href") or ""
            if any(token in href.lower() for token in ["csv", "zip", "download", "scarica", "opendata"]):
                fh.write(f"- {link.get('text')!r}: {href}\n")
        for form in rec.get("forms", []):
            fh.write("FORM " + json.dumps(form, ensure_ascii=False) + "\n")

print(json.dumps({"records": len(records), "output": str(OUT)}, indent=2))
