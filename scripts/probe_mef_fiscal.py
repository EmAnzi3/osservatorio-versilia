#!/usr/bin/env python3
"""Sonda dei documenti MEF di fiscalità locale (IRPEF, IMU, TARI) per un anno.

Gira sui runner GitHub (`update_source_data.py mef-fiscal-probe --year AAAA`),
perché il Portale del federalismo fiscale non è raggiungibile altrove. Non tocca
il catalogo: salva in `data/source-probes/mef-fiscal-AAAA.json` le pagine
consultate, i documenti elencati e il testo estratto dai PDF, così che aliquote
e tariffe si trascrivano dal documento ufficiale con la sua provenienza.
"""
from __future__ import annotations

import html as htmllib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/"
IMU_RESULT = BASE + "nuova_imu/risultato.htm?DOWNLOAD=Procedi&anno={year}&cc={code}&cm=O&lista=1&pagina=&pr=&r=2"
TARI_RESULT = BASE + "nuova_at/risultato.htm?DOWNLOAD=Procedi&annosel={year}&cc={code}&lista=1&pagina=sceltaregione.htm&r=2&tipo_trib=tutti"
IRPEF_PAGES = [BASE + "nuova_addcomirpef/", BASE + "nuova_addcomirpef/download/tabella.htm"]
IRPEF_GUESSES = [
    BASE + "nuova_addcomirpef/risultato.htm?DOWNLOAD=Procedi&anno={year}&cc={code}&lista=1&pagina=&pr=&r=2",
    BASE + "nuova_addcomirpef/risultato.htm?cc={code}&anno={year}",
]
TOWNS = {
    "Camaiore": "B455", "Forte dei Marmi": "D730", "Massarosa": "F035", "Pietrasanta": "G628",
    "Seravezza": "I622", "Stazzema": "I942", "Viareggio": "L833",
}
UA = {"User-Agent": "OsservatorioVersilia-data-audit/1.0"}
MAX_DOCS = 12
TEXT_CAP = 60000


def fetch(url: str, tries: int = 3) -> bytes:
    error: Exception | None = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - la sonda registra ogni errore
            error = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{type(error).__name__}: {error}")


def strip(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def links(page: str, url: str) -> list[dict[str, str]]:
    out, seen = [], set()
    rows = [(m.start(), m.end()) for m in re.finditer(r"<tr\b.*?</tr>", page, flags=re.I | re.S)]
    for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", page, flags=re.I | re.S):
        href = urllib.parse.urljoin(url, htmllib.unescape(m.group(1)))
        if href in seen or href.startswith(("javascript:", "mailto:")):
            continue
        seen.add(href)
        row = next((page[a:b] for a, b in rows if a <= m.start() < b), "")
        out.append({"url": href, "text": strip(m.group(2))[:300], "row": strip(row)[:600]})
    return out


def pdf_text(data: bytes) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text(extraction_mode="layout") or "")
        except TypeError:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks), len(reader.pages)


def is_doc(link: dict[str, str]) -> bool:
    """Atti comunali depositati (DIMUNIC: delibere e allegati); esclusi regolamenti e pagine di servizio."""
    u = link["url"]
    return "download_lib" in u and "DIMUNIC" in u.upper()


def context(text: str, pattern: str, before: int = 300, after: int = 2500) -> list[str]:
    clean = re.sub(r"[ \t\xa0]+", " ", text)
    return [clean[max(0, m.start() - before):m.start() + after] for m in re.finditer(pattern, clean, flags=re.I)][:3]


def documents(page_url: str, keep: re.Pattern[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"page": page_url, "links": [], "documents": []}
    try:
        page = fetch(page_url).decode("utf-8", errors="replace")
    except RuntimeError as exc:
        result["pageError"] = str(exc)
        return result
    result["pageText"] = strip(page)[:4000]
    result["links"] = links(page, page_url)
    for link in [l for l in result["links"] if is_doc(l)][:MAX_DOCS]:
        doc: dict[str, Any] = dict(link)
        try:
            data = fetch(link["url"])
            doc["bytes"] = len(data)
            text, pages = pdf_text(data)
            doc["pages"] = pages
            doc["head"] = re.sub(r"\s+", " ", text[:1500])
            if keep.search(text):
                doc["pdfText"] = text[:TEXT_CAP]
                doc["pdfTextTruncated"] = len(text) > TEXT_CAP
        except Exception as exc:  # noqa: BLE001
            doc["error"] = f"{type(exc).__name__}: {exc}"
        result["documents"].append(doc)
    return result


def imu(year: int) -> dict[str, Any]:
    out = {}
    for town, code in TOWNS.items():
        r = documents(IMU_RESULT.format(year=year, code=code), re.compile(r"Altri\s+fabbricati", re.I))
        for doc in r["documents"]:
            if "pdfText" in doc:
                doc["altriFabbricati"] = context(doc["pdfText"], r"Altri\s+fabbricati")
        out[town] = r
        print(f"IMU {town}: {len(r['documents'])} documenti, errore pagina: {r.get('pageError', '-')}")
    return out


def tari(year: int) -> dict[str, Any]:
    out = {}
    keep = re.compile(r"domestic|component|occupant", re.I)
    for town, code in TOWNS.items():
        r = documents(TARI_RESULT.format(year=year, code=code), keep)
        out[town] = r
        print(f"TARI {town}: {len(r['documents'])} documenti, con tariffe domestiche: "
              f"{sum('pdfText' in d for d in r['documents'])}")
    return out


def irpef(year: int) -> dict[str, Any]:
    out: dict[str, Any] = {"pages": [], "files": [], "guesses": {}}
    names = [n.upper() for n in TOWNS] + list(TOWNS.values())
    candidates: list[dict[str, str]] = []
    for url in IRPEF_PAGES:
        try:
            page = fetch(url).decode("utf-8", errors="replace")
            ls = links(page, url)
            forms = re.findall(r"<form\b.*?</form>", page, flags=re.I | re.S)
            out["pages"].append({"url": url, "text": strip(page)[:4000], "links": ls, "forms": [f[:3000] for f in forms]})
            candidates += [l for l in ls if re.search(r"\.(zip|csv|xls|xlsx)\b", l["url"], re.I) or str(year) in l["url"] + l["text"]]
        except RuntimeError as exc:
            out["pages"].append({"url": url, "error": str(exc)})
    for link in candidates[:10]:
        item: dict[str, Any] = dict(link)
        try:
            data = fetch(link["url"])
            item["bytes"] = len(data)
            blobs: list[tuple[str, bytes]] = []
            if data[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    blobs = [(n, z.read(n)) for n in z.namelist()]
            else:
                blobs = [(link["url"], data)]
            item["entries"] = []
            for name, blob in blobs:
                text = blob.decode("utf-8", errors="replace") if b"\x00" not in blob[:2000] else blob.decode("latin-1", errors="replace")
                lines = text.splitlines()
                hits = [ln for ln in lines if any(n in ln.upper() for n in names)]
                item["entries"].append({"name": name, "header": lines[:3], "lines": len(lines), "hits": hits[:60]})
        except Exception as exc:  # noqa: BLE001
            item["error"] = f"{type(exc).__name__}: {exc}"
        out["files"].append(item)
    for town, code in TOWNS.items():
        out["guesses"][town] = []
        for pattern in IRPEF_GUESSES:
            url = pattern.format(year=year, code=code)
            try:
                page = fetch(url, tries=1).decode("utf-8", errors="replace")
                text = strip(page)
                i = text.upper().find(town.upper())
                out["guesses"][town].append({"url": url, "found": i >= 0, "text": text[max(0, i - 200):i + 3000] if i >= 0 else text[:800],
                                             "links": [l for l in links(page, url) if is_doc(l) or "dettaglio" in l["url"].lower()][:20]})
            except RuntimeError as exc:
                out["guesses"][town].append({"url": url, "error": str(exc)})
    print(f"IRPEF: {len(out['files'])} file candidati, pagine {len(out['pages'])}")
    return out


def run(year: int, output: Path | None = None) -> Path:
    path = output or ROOT / "data" / "source-probes" / f"mef-fiscal-{year}.json"
    probe = {"schemaVersion": 1, "year": year, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "note": "Sonda: documenti ufficiali MEF consultati; non è un dato pubblicato.",
             "imu": imu(year), "tari": tari(year), "irpef": irpef(year)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(probe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Sonda MEF {year} scritta in {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return path
