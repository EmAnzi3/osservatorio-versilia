#!/usr/bin/env python3
"""Interroga gli endpoint pubblici OpenBDAP usati nelle analisi comunali.

Salva le risposte grezze e prova a individuare i sette Comuni della Versilia.
Non modifica il dataset del sito.
"""
from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

OUT = Path("audit-openbdap-api")
OUT.mkdir(exist_ok=True)
BASE = "https://openbdap.rgs.mef.gov.it/api/api/fet"
UA = "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)"
TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
VOICES = [
    "SpeseCorrentiProcapite",
    "Speseincontocapitaleprocapite",
    "EntrateCorrentidinaturatributaria,contributivaeperequativaProcapite",
    "Trasferimenticorrentiprocapite",
    "EntrateExtra-tributarieprocapite",
]


def norm(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").upper().strip()


def fetch(url: str, attempts: int = 12) -> requests.Response:
    last: Exception | None = None
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=(30, 180), allow_redirects=True)
            response.raise_for_status()
            return response
        except Exception as exc:
            last = exc
            wait = min(60, attempt * 5)
            print(f"tentativo {attempt}/{attempts} fallito per {url}: {exc!r}; attesa {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"endpoint non raggiungibile dopo {attempts} tentativi: {url}; ultimo errore {last!r}")


def walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def find_towns(payload: Any) -> dict[str, list[dict[str, Any]]]:
    found = {town: [] for town in TOWNS}
    for path, item in walk(payload):
        serialized = norm(json.dumps(item, ensure_ascii=False, default=str))
        for town in TOWNS:
            if norm(town) in serialized:
                found[town].append({"path": path, "item": item})
    return found


def main() -> None:
    report: dict[str, Any] = {"base": BASE, "queries": {}}
    for year in (2024, 2025):
        for voice in VOICES:
            url = f"{BASE}/data_FET_sh4?anno={year}&voce={quote(voice, safe=',')}"
            key = f"{year}_{voice}"
            try:
                response = fetch(url)
                raw = response.text
                (OUT / f"{key}.json").write_text(raw, encoding="utf-8")
                try:
                    payload = response.json()
                    matches = find_towns(payload)
                    report["queries"][key] = {
                        "url": response.url,
                        "status": response.status_code,
                        "bytes": len(response.content),
                        "content_type": response.headers.get("content-type"),
                        "payload_type": type(payload).__name__,
                        "town_matches": {town: len(items) for town, items in matches.items()},
                        "town_items": matches,
                    }
                except Exception as exc:
                    report["queries"][key] = {
                        "url": response.url,
                        "status": response.status_code,
                        "bytes": len(response.content),
                        "content_type": response.headers.get("content-type"),
                        "parse_error": repr(exc),
                        "head": raw[:1000],
                    }
            except Exception as exc:
                report["queries"][key] = {"url": url, "error": repr(exc)}
            print(key, report["queries"][key].get("status", "ERROR"), flush=True)

    # Endpoint di confronto: serve anche a documentare campi e serie esposte.
    pairs = [
        ("MASSAROSA, (LU, Fascia 10001-20000)", "VIAREGGIO, (LU, Fascia 50001-100000)"),
        ("CAMAIORE, (LU, Fascia 20001-60000)", "PIETRASANTA, (LU, Fascia 20001-60000)"),
        ("SERAVEZZA, (LU, Fascia 10001-20000)", "STAZZEMA, (LU, Fascia <=5000)"),
    ]
    for index, (city1, city2) in enumerate(pairs, 1):
        url = f"{BASE}/data_FET_a2?city1={quote(city1)}&city2={quote(city2)}"
        key = f"comparison_{index}"
        try:
            response = fetch(url)
            (OUT / f"{key}.json").write_text(response.text, encoding="utf-8")
            payload = response.json()
            report["queries"][key] = {
                "url": response.url,
                "status": response.status_code,
                "bytes": len(response.content),
                "payload": payload,
            }
        except Exception as exc:
            report["queries"][key] = {"url": url, "error": repr(exc)}
        print(key, report["queries"][key].get("status", "ERROR"), flush=True)

    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
