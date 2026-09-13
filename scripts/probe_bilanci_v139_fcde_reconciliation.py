#!/usr/bin/env python3
"""Inspect 2025 OpenBDAP FCDE reconciliation members without mutating data."""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import zipfile
from urllib.parse import quote

import requests

BASE = "https://openbdap.rgs.mef.gov.it"
PATH = "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip"
TOWNS = {"005": "Camaiore", "013": "Forte dei Marmi", "018": "Massarosa", "024": "Pietrasanta", "028": "Seravezza", "030": "Stazzema", "033": "Viareggio"}


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def main() -> None:
    url = BASE + quote(PATH, safe="/:_-.")
    response = requests.get(url, timeout=240, headers={"User-Agent": "OsservatorioVersilia/1.39-fcde-probe"})
    response.raise_for_status()
    report = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        candidates = [
            item for item in archive.infolist()
            if item.filename.lower().endswith(".csv") and (
                "allegato a1" in norm(item.filename) or "fcde" in norm(item.filename)
            )
        ]
        for info in candidates:
            reader = csv.DictReader(io.StringIO(decode(archive.read(info))), delimiter=";")
            rows = list(reader)
            matches = []
            for row in rows:
                if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
                    continue
                if (row.get("Codice Provincia") or "").strip().zfill(3) != "046":
                    continue
                code = (row.get("Codice Comune") or "").strip().zfill(3)
                if code not in TOWNS:
                    continue
                haystack = " | ".join(norm(value) for value in row.values())
                if any(token in haystack for token in ("dubbia esigibilita", "fcde", "fondo crediti")):
                    matches.append({
                        "town": TOWNS[code],
                        "nonempty": {key: value for key, value in row.items() if key and str(value or "").strip()},
                    })
            report.append({
                "member": info.filename,
                "headers": list(reader.fieldnames or []),
                "matching_rows_count": len(matches),
                "matching_rows_sample": matches[:21],
            })
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
