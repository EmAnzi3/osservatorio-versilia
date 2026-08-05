#!/usr/bin/env python3
"""Scarica le tavole ufficiali compatte utili all'espansione LIA."""
from __future__ import annotations

import json
from pathlib import Path

import requests

OUT = Path("lia-compact-sources")
OUT.mkdir(exist_ok=True)
UA = "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)"

SOURCES = {
    "istat_istruzione.xlsx": "https://www.istat.it/storage/misura-comune/4-Istruzione.xlsx",
    "istat_lavoro.xlsx": "https://www.istat.it/storage/misura-comune/5-Lavoro.xlsx",
    "istat_genere_istruzione.xlsx": "https://www.istat.it/storage/misura-comune/9a-Tematiche-di-genere-istruzione.xlsx",
    "istat_genere_lavoro.xlsx": "https://www.istat.it/storage/misura-comune/9b-Tematiche-di-genere-lavoro.xlsx",
    "locazioni_turistiche_2025.ods": "https://www.regione.toscana.it/documents/d/guest/6-locazioni-agg-maggio-2026-",
    "offerta_ricettiva_2025.ods": "https://www.regione.toscana.it/documents/d/guest/1-consistenza-media-per-comune-e-tipologia-ricettiva-2025",
}


def main() -> None:
    report = {}
    for filename, url in SOURCES.items():
        response = requests.get(url, timeout=240, allow_redirects=True, headers={"User-Agent": UA})
        response.raise_for_status()
        target = OUT / filename
        target.write_bytes(response.content)
        report[filename] = {
            "url": response.url,
            "bytes": target.stat().st_size,
            "content_type": response.headers.get("content-type"),
            "content_disposition": response.headers.get("content-disposition"),
        }
        print(filename, report[filename], flush=True)
    (OUT / "sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
