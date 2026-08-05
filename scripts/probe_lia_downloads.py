#!/usr/bin/env python3
"""Probe leggero degli endpoint ufficiali usati dall'espansione LIA."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("lia-probe")
OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/151 Safari/537.36"


def info(response: requests.Response, first: bytes = b"") -> dict:
    return {
        "status": response.status_code,
        "url": response.url,
        "content_type": response.headers.get("content-type"),
        "content_length": response.headers.get("content-length"),
        "content_disposition": response.headers.get("content-disposition"),
        "first_hex": first[:64].hex(),
        "first_text": first[:300].decode("utf-8", errors="replace"),
    }


def probe_mim(label: str, url: str) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    page = session.get(url, timeout=90)
    records = [{"variant": "page", **info(page, page.content[:4096])}]
    variants = [
        ("referer", url, {"Referer": page.url, "Accept": "text/csv,*/*;q=0.8"}),
        ("download", url + "?download=true", {"Referer": page.url, "Accept": "text/csv,*/*;q=0.8"}),
        ("raw", url + "?raw=1", {"Referer": page.url, "Accept": "text/csv,*/*;q=0.8"}),
    ]
    for name, target, headers in variants:
        try:
            with session.get(target, headers=headers, stream=True, timeout=90, allow_redirects=True) as response:
                first = next(response.iter_content(4096), b"")
                records.append({"variant": name, **info(response, first)})
        except Exception as exc:
            records.append({"variant": name, "error": repr(exc)})
    (OUT / f"{label}.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(label, json.dumps(records, ensure_ascii=False), flush=True)


def inspect_html(label: str, url: str) -> None:
    try:
        response = requests.get(url, headers={"User-Agent": UA}, timeout=90)
        result = info(response, response.content[:4096])
        response.raise_for_status()
        (OUT / f"{label}.html").write_bytes(response.content)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for tag in soup.find_all(["a", "iframe", "script", "object", "embed"]):
            attr = "href" if tag.name == "a" else "src"
            value = tag.get(attr) or tag.get("data")
            if value:
                links.append({"tag": tag.name, "text": tag.get_text(" ", strip=True)[:200], "url": urljoin(response.url, value)})
        result["links"] = links
    except Exception as exc:
        result = {"url": url, "error": repr(exc)}
    (OUT / f"{label}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(label, json.dumps(result, ensure_ascii=False)[:10000], flush=True)


def tourism() -> None:
    url = "https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0"
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": UA})
        page = session.get(url, timeout=90)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(" ", strip=True)
            target = urljoin(page.url, anchor["href"])
            if "locazioni" in text.lower() or "consistenza" in text.lower():
                record = {"text": text, "url": target}
                try:
                    with session.get(target, stream=True, timeout=120) as response:
                        first = next(response.iter_content(4096), b"")
                        record.update(info(response, first))
                except Exception as exc:
                    record["error"] = repr(exc)
                links.append(record)
        result = {"page": info(page, page.content[:4096]), "links": links}
    except Exception as exc:
        result = {"error": repr(exc)}
    (OUT / "tourism.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("tourism", json.dumps(result, ensure_ascii=False), flush=True)


def main() -> None:
    mim = {
        "anagrafe_statali": "https://dati.istruzione.it/opendata/opendata/catalog/SCUANAGRAFESTAT/SCUANAGRAFESTAT20242520250831.csv",
        "studenti_classi_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUCORSOINDCLASTA/ALUCORSOINDCLASTA20242520250831.csv",
        "tempo_statali": "https://dati.istruzione.it/opendata/opendata/catalog/ALUTEMPOSCUOLASTA/ALUTEMPOSCUOLASTA20242520250831.csv",
    }
    for label, url in mim.items():
        probe_mim(label, url)
    inspect_html("sil_avviamenti_comuni", "https://rtbi.regione.toscana.it/SIL/Avviamenti_04_Comuni_index.html")
    inspect_html("sil_disoccupazione_residenza", "https://rtbi.regione.toscana.it/SIL/Disoccupazione_02_Residenza_index.html")
    tourism()


if __name__ == "__main__":
    main()
