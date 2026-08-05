#!/usr/bin/env python3
"""Scarica i file ufficiali grezzi usati nell'audit LIA, senza elaborarli."""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("lia-source-files")
OUT.mkdir(exist_ok=True)
UA = "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)"


def session() -> requests.Session:
    value = requests.Session()
    value.headers.update({"User-Agent": UA})
    return value


def save_response(response: requests.Response, path: Path) -> None:
    response.raise_for_status()
    path.write_bytes(response.content)
    print(path, len(response.content), response.headers.get("content-type"), flush=True)


def fetch_mim(area: str, prefix: str, year: str = "202425") -> dict:
    home = f"https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area={area}"
    s = session()
    page = s.get(home, timeout=120)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    urls = []
    for anchor in soup.find_all("a", href=True):
        target = urljoin(page.url, anchor["href"])
        name = Path(target.split("?", 1)[0]).name
        if name.startswith(prefix) and year in name and name.lower().endswith(".csv"):
            urls.append(target)
    if not urls:
        raise RuntimeError(f"File MIM assente: {prefix} {year}")
    url = sorted(set(urls))[-1]
    response = s.get(url, timeout=300, headers={"Referer": page.url, "Accept": "text/csv,application/octet-stream,*/*;q=0.8"})
    response.raise_for_status()
    if "html" in response.headers.get("content-type", "").lower() or response.content.lstrip().startswith(b"<!DOCTYPE html"):
        raise RuntimeError(f"MIM ha restituito HTML per {prefix}: {url}")
    target = OUT / Path(url).name
    save_response(response, target)
    return {"url": url, "file": target.name, "bytes": target.stat().st_size}


def fetch_istat() -> dict:
    url = "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip"
    response = requests.get(url, timeout=900, headers={"User-Agent": UA})
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        tuscany_name = next(name for name in archive.namelist() if "R09_Toscana" in name)
        layout_name = next(name for name in archive.namelist() if "TRACCIATO" in name.upper())
        tuscany = OUT / "R09_Toscana_2023_sezioni.xlsx"
        layout = OUT / "TRACCIATO_FILE_REGIONALI.xlsx"
        tuscany.write_bytes(archive.read(tuscany_name))
        layout.write_bytes(archive.read(layout_name))
    print(tuscany, tuscany.stat().st_size, flush=True)
    print(layout, layout.stat().st_size, flush=True)
    return {
        "url": url,
        "files": [tuscany.name, layout.name],
        "bytes": [tuscany.stat().st_size, layout.stat().st_size],
    }


def fetch_tourism() -> dict:
    page_url = "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0"
    s = session()
    page = s.get(page_url, timeout=120)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    result = {"page": page.url, "files": []}
    for anchor in soup.find_all("a", href=True):
        text = anchor.get_text(" ", strip=True).lower()
        if "locazioni" not in text and "consistenza media" not in text:
            continue
        url = urljoin(page.url, anchor["href"])
        response = s.get(url, timeout=180)
        response.raise_for_status()
        label = "locazioni_turistiche_2025.ods" if "locazioni" in text else "offerta_ricettiva_2025.ods"
        target = OUT / label
        save_response(response, target)
        result["files"].append({"label": text, "url": url, "file": label, "bytes": target.stat().st_size})
    return result


def main() -> None:
    report = {"mim": {}, "istat": None, "tourism": None}
    mim_specs = {
        "registry_state": ("Scuole", "SCUANAGRAFESTAT"),
        "registry_private": ("Scuole", "SCUANAGRAFEPAR"),
        "classes_state": ("Studenti", "ALUCORSOINDCLASTA"),
        "classes_private": ("Studenti", "ALUCORSOINDCLAPAR"),
        "time_state": ("Studenti", "ALUTEMPOSCUOLASTA"),
        "time_private": ("Studenti", "ALUTEMPOSCUOLAPAR"),
    }
    for key, (area, prefix) in mim_specs.items():
        report["mim"][key] = fetch_mim(area, prefix)
    report["istat"] = fetch_istat()
    report["tourism"] = fetch_tourism()
    (OUT / "sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
