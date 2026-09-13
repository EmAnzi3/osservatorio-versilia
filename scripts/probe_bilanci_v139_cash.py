#!/usr/bin/env python3
"""Probe the 2025 year-end cash fund from OpenBDAP Allegato A for 7/7 towns."""
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
MEMBER = "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv"
TOWNS = {
    "Camaiore": "005", "Forte dei Marmi": "013", "Massarosa": "018",
    "Pietrasanta": "024", "Seravezza": "028", "Stazzema": "030", "Viareggio": "033",
}


def norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def decode(raw):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def main():
    url = BASE + quote(PATH, safe="/:_-.")
    r = requests.get(url, timeout=240, headers={"User-Agent": "OsservatorioVersilia/1.39-cash-probe"})
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        hits = [x for x in zf.infolist() if x.filename.endswith(MEMBER)]
        if len(hits) != 1:
            raise SystemExit(f"member count={len(hits)}")
        rows = list(csv.DictReader(io.StringIO(decode(zf.read(hits[0]))), delimiter=";"))

    out = {}
    for town, code in TOWNS.items():
        selected = []
        for row in rows:
            if (row.get("Codice Tipologia Soggetto") or "").strip() != "ELCOMU":
                continue
            if (row.get("Codice Provincia") or "").strip().zfill(3) != "046":
                continue
            if (row.get("Codice Comune") or "").strip().zfill(3) != code:
                continue
            desc = norm(row.get("Desc Voce Ris Amm Rend"))
            if "fondo" in desc and "cassa" in desc and "31" in desc and "dicembre" in desc:
                selected.append(row)
        if len(selected) != 1:
            out[town] = {"status": "FAIL", "rows": len(selected), "descriptions": [r.get("Desc Voce Ris Amm Rend") for r in selected]}
            continue
        row = selected[0]
        raw = (row.get("Totale di Gestione") or "").strip()
        try:
            value = float(raw)
        except ValueError:
            out[town] = {"status": "FAIL", "raw": raw, "row": row}
            continue
        out[town] = {
            "status": "PASS",
            "value": value,
            "raw": raw,
            "row_code": row.get("Cod Voce Ris Amm Rend"),
            "description": row.get("Desc Voce Ris Amm Rend"),
        }

    failures = [town for town, item in out.items() if item["status"] != "PASS"]
    print(json.dumps({"coverage": f"{7-len(failures)}/7", "towns": out}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit("cash fund probe failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
