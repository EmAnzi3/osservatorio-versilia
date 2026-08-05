#!/usr/bin/env python3
"""Audit puntuale delle fonti comunali più promettenti.

Produce estratti e schemi, senza modificare il dataset del sito.
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = Path("audit-toscana-specific-sources")
OUT.mkdir(exist_ok=True)
UA = "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)"
TOWNS = {
    "046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa",
    "046024": "Pietrasanta", "046028": "Seravezza", "046030": "Stazzema",
    "046033": "Viareggio",
}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def get(url: str, timeout: int = 300, **kwargs) -> requests.Response:
    headers = dict(kwargs.pop("headers", {}))
    headers.setdefault("User-Agent", UA)
    response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers, **kwargs)
    response.raise_for_status()
    return response


def read_csv(raw: bytes) -> pd.DataFrame:
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        for sep in (";", ",", "\t", "|"):
            try:
                frame = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep, dtype=str, low_memory=False)
                if frame.shape[1] > 1:
                    return frame
            except Exception as exc:
                last = exc
    raise RuntimeError(f"CSV non leggibile: {last}")


def select_towns(frame: pd.DataFrame) -> tuple[pd.DataFrame, str | None, str | None]:
    code_col = None
    name_col = None
    for col in frame.columns:
        n = norm(col)
        if code_col is None and (("COD" in n and "COM" in n) or "CODICE ISTAT" in n):
            code_col = col
        if name_col is None and (n == "COMUNE" or "DENOMINAZIONE COMUNE" in n or "NOME COMUNE" in n):
            name_col = col
    mask = pd.Series(False, index=frame.index)
    codes = None
    if code_col:
        codes = frame[code_col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
        mask |= codes.isin(TOWNS)
    if name_col:
        mask |= frame[name_col].map(norm).isin({norm(x) for x in TOWNS.values()})
    selected = frame.loc[mask].copy()
    if codes is not None:
        selected.insert(0, "_codice_istat", codes.loc[mask])
        selected.insert(1, "_comune_osservatorio", selected["_codice_istat"].map(TOWNS))
    elif name_col:
        mapping = {norm(v): v for v in TOWNS.values()}
        selected.insert(0, "_comune_osservatorio", selected[name_col].map(lambda x: mapping.get(norm(x))))
    return selected, code_col, name_col


def package_show(name: str) -> dict:
    response = get("https://dati.toscana.it/api/3/action/package_show", params={"id": name})
    return response.json()["result"]


def audit_asia() -> dict:
    package = package_show("imprese-e-addetti-asia-anno-2023")
    resource = next(r for r in package["resources"] if "occup" in (str(r.get("name", "")) + str(r.get("url", ""))).lower())
    response = get(resource["url"])
    frame = read_csv(response.content)
    selected, code_col, name_col = select_towns(frame)
    selected.to_csv(OUT / "asia_occupazione_2023_versilia.csv", index=False)
    dimensions = {}
    for col in frame.columns:
        values = frame[col].dropna().astype(str).str.strip()
        unique = sorted(values.unique().tolist())
        if len(unique) <= 100:
            dimensions[col] = unique
    return {
        "dataset": package.get("title"), "resource": response.url, "bytes": len(response.content),
        "shape": list(frame.shape), "columns": list(frame.columns), "code_column": code_col,
        "name_column": name_col, "town_rows": int(selected.shape[0]), "dimensions": dimensions,
        "town_coverage": sorted(selected.get("_comune_osservatorio", pd.Series(dtype=str)).dropna().unique().tolist()),
    }


def audit_sau_bio() -> dict:
    package = package_show("saubio2024")
    resource = package["resources"][0]
    response = get(resource["url"])
    frame = read_csv(response.content)
    selected, code_col, name_col = select_towns(frame)
    selected.to_csv(OUT / "sau_bio_2024_versilia.csv", index=False)
    return {
        "dataset": package.get("title"), "resource": response.url, "bytes": len(response.content),
        "shape": list(frame.shape), "columns": list(frame.columns), "code_column": code_col,
        "name_column": name_col, "town_rows": int(selected.shape[0]),
        "rows": selected.to_dict(orient="records"),
    }


def audit_infortuni() -> dict:
    page_url = "https://www.regione.toscana.it/-/infortuni-sul-lavoro-in-toscana-dati-2020-2024"
    page = get(page_url)
    soup = BeautifulSoup(page.text, "html.parser")
    candidates = []
    for anchor in soup.find_all("a", href=True):
        text = " ".join(anchor.get_text(" ", strip=True).split())
        if "Tavola 2e" in text or ("infortuni" in text.lower() and "lucca" in text.lower()):
            candidates.append({"text": text, "url": urljoin(page.url, anchor["href"])})
    result = {"page": page.url, "candidates": candidates, "files": []}
    for index, candidate in enumerate(candidates):
        response = get(candidate["url"])
        record = {"url": response.url, "bytes": len(response.content), "content_type": response.headers.get("content-type")}
        try:
            sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, dtype=str)
            record["sheets"] = {name: {"shape": list(frame.shape), "columns": list(frame.columns)} for name, frame in sheets.items()}
            all_rows = []
            for name, frame in sheets.items():
                selected, _, _ = select_towns(frame)
                if not selected.empty:
                    selected.insert(0, "_foglio", name)
                    all_rows.append(selected)
            if all_rows:
                combined = pd.concat(all_rows, ignore_index=True)
                combined.to_csv(OUT / f"infortuni_lucca_2020_2024_versilia_{index}.csv", index=False)
                record["town_rows"] = int(combined.shape[0])
                record["towns"] = sorted(combined["_comune_osservatorio"].dropna().unique().tolist())
        except Exception as exc:
            record["parse_error"] = repr(exc)
            (OUT / f"infortuni_lucca_{index}.bin").write_bytes(response.content)
        result["files"].append(record)
    return result


def parse_document_links(text: str, base_url: str) -> list[str]:
    links = []
    try:
        payload = json.loads(text)
        stack = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, str) and (".zip" in item.lower() or "datasets_fet" in item.lower()):
                links.append(urljoin(base_url, item))
    except Exception:
        soup = BeautifulSoup(text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = urljoin(base_url, anchor["href"])
            if ".zip" in href.lower() or "datasets_fet" in href.lower():
                links.append(href)
        links.extend(urljoin(base_url, x) for x in re.findall(r"(?:href=|url[=:]\s*[\"']?)([^\"'<>\s]+\.zip)", text, re.I))
    return sorted(set(links))


def inspect_zip(raw: bytes, label: str) -> dict:
    result = {"bytes": len(raw), "files": []}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            record = {"name": info.filename, "bytes": info.file_size, "compressed": info.compress_size}
            low = info.filename.lower()
            try:
                if low.endswith((".csv", ".txt")) and info.file_size <= 800_000_000:
                    data = archive.read(info.filename)
                    frame = read_csv(data)
                    selected, code_col, name_col = select_towns(frame)
                    record.update({"shape": list(frame.shape), "columns": list(frame.columns), "code_column": code_col, "name_column": name_col, "town_rows": int(selected.shape[0])})
                    if not selected.empty:
                        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(info.filename).name)
                        selected.to_csv(OUT / f"{label}_{safe}_versilia.csv", index=False)
                        record["towns"] = sorted(selected["_comune_osservatorio"].dropna().unique().tolist())
                elif low.endswith((".xlsx", ".xls")) and info.file_size <= 300_000_000:
                    data = archive.read(info.filename)
                    sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=str)
                    record["sheets"] = {n: {"shape": list(f.shape), "columns": list(f.columns)} for n, f in sheets.items()}
            except Exception as exc:
                record["parse_error"] = repr(exc)
            result["files"].append(record)
    return result


def audit_openbdap() -> dict:
    endpoint = "https://openbdap.rgs.mef.gov.it/fet/GetDocuments"
    result = {"endpoint": endpoint, "queries": {}}
    for year in (2024, 2025):
        response = get(endpoint, params={"type": "Rendiconto", "year": year, "country": "Toscana"})
        text = response.text
        (OUT / f"openbdap_getdocuments_rendiconto_{year}_toscana.txt").write_text(text, encoding="utf-8")
        links = parse_document_links(text, response.url)
        query = {"url": response.url, "status": response.status_code, "content_type": response.headers.get("content-type"), "links": links, "downloads": []}
        for index, link in enumerate(links):
            if "schema" not in link.lower() and "bilancio" not in link.lower():
                continue
            download = get(link, timeout=900)
            record = {"url": download.url, "content_type": download.headers.get("content-type")}
            try:
                record.update(inspect_zip(download.content, f"openbdap_{year}_{index}"))
            except Exception as exc:
                record["error"] = repr(exc)
            query["downloads"].append(record)
        result["queries"][str(year)] = query
    return result


def main() -> None:
    report = {}
    for key, function in (("asia2023", audit_asia), ("sauBio2024", audit_sau_bio), ("infortuni", audit_infortuni), ("openbdap", audit_openbdap)):
        try:
            report[key] = function()
            print(key, "OK", flush=True)
        except Exception as exc:
            report[key] = {"error": repr(exc)}
            print(key, "ERROR", repr(exc), flush=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str)[:50000], flush=True)


if __name__ == "__main__":
    main()
