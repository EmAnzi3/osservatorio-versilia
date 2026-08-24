#!/usr/bin/env python3
"""Probe official Welfare / first-infancy sources for the seven Versilia municipalities.

This is intentionally diagnostic: it downloads the official Istat 2022 municipal
workbook and Regione Toscana 2024/25 first-infancy CSV, then records structure,
headers and matching municipal rows so the canonical materializer can be built
without guessing column semantics.
"""
from __future__ import annotations

import csv
import io
import json
import re
import ssl
import unicodedata
import urllib.request
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "welfare-probe"
OUT.mkdir(parents=True, exist_ok=True)

ISTAT_URL = "https://www.istat.it/wp-content/uploads/2025/09/Tavole_2022_spesa_comuni-1.xlsx"
TOSCANA_URL = "https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv"
TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
KEYWORDS = [
    "comune", "spesa", "abitante", "pro capite", "pro-capite", "totale",
    "famiglie", "minori", "disabil", "anzian", "povert", "immigr",
    "dipenden", "multiutenza", "utente", "utenza", "ricett", "posti",
    "bambini", "popolazione", "servizi educativi",
]


def norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def fetch(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=180, context=ctx) as response:
        target.write_bytes(response.read())


def compact_row(values: list[object]) -> list[object]:
    last = -1
    for i, value in enumerate(values):
        if value not in (None, ""):
            last = i
    return values[: last + 1] if last >= 0 else []


def probe_istat(path: Path) -> dict:
    wb = load_workbook(path, read_only=True, data_only=True)
    result = {"url": ISTAT_URL, "sheets": [], "townCoverage": {town: [] for town in TOWNS}}
    towns_norm = {norm(t): t for t in TOWNS}
    for ws in wb.worksheets:
        sheet = {"title": ws.title, "maxRow": ws.max_row, "maxColumn": ws.max_column, "keywordRows": [], "townRows": []}
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            values = compact_row(list(row))
            if not values:
                continue
            joined = " | ".join(norm(v) for v in values if v not in (None, ""))
            if len(sheet["keywordRows"]) < 30 and any(k in joined for k in KEYWORDS):
                sheet["keywordRows"].append({"row": r_idx, "values": values[:40]})
            matched = []
            for cell in values:
                n = norm(cell)
                for town_n, town in towns_norm.items():
                    if town_n and (n == town_n or town_n in n):
                        matched.append(town)
            if matched:
                item = {"row": r_idx, "towns": sorted(set(matched)), "values": values[:60]}
                sheet["townRows"].append(item)
                for town in set(matched):
                    result["townCoverage"][town].append({"sheet": ws.title, "row": r_idx})
        result["sheets"].append(sheet)
    return result


def decode_csv(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    raise RuntimeError("Impossibile decodificare CSV Toscana")


def probe_toscana(path: Path) -> dict:
    text, encoding = decode_csv(path.read_bytes())
    sample = text[:12000]
    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
    rows = list(csv.reader(io.StringIO(text), dialect))
    header = rows[0] if rows else []
    matches = []
    coverage = {town: 0 for town in TOWNS}
    town_norm = {norm(t): t for t in TOWNS}
    for idx, row in enumerate(rows[1:], start=2):
        joined = " | ".join(norm(v) for v in row)
        found = [town for town_n, town in town_norm.items() if town_n in joined]
        if found:
            matches.append({"row": idx, "towns": sorted(set(found)), "values": row})
            for town in set(found):
                coverage[town] += 1
    return {
        "url": TOSCANA_URL,
        "encoding": encoding,
        "delimiter": dialect.delimiter,
        "header": header,
        "rowCount": max(0, len(rows) - 1),
        "townRows": matches,
        "townCoverage": coverage,
    }


def main() -> None:
    istat_path = OUT / "istat-2022-comuni.xlsx"
    toscana_path = OUT / "toscana-prima-infanzia-2024-25.csv"
    fetch(ISTAT_URL, istat_path)
    fetch(TOSCANA_URL, toscana_path)

    result = {"istat": probe_istat(istat_path), "toscana": probe_toscana(toscana_path)}
    (OUT / "probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    lines = ["# Welfare / prima infanzia · probe fonti", "", "## Istat 2022 · Tavole spesa Comuni"]
    for sheet in result["istat"]["sheets"]:
        lines += [f"### {sheet['title']}", f"- dimensione: {sheet['maxRow']} × {sheet['maxColumn']}", f"- righe Versilia trovate: {len(sheet['townRows'])}"]
        for item in sheet["townRows"][:20]:
            lines.append(f"- riga {item['row']} · {', '.join(item['towns'])}: `{item['values']}`")
    lines += ["", "### Copertura Istat"]
    for town, hits in result["istat"]["townCoverage"].items():
        lines.append(f"- {town}: {len(hits)} occorrenze")

    t = result["toscana"]
    lines += ["", "## Regione Toscana · Prima infanzia 2024/25", f"- intestazioni: `{t['header']}`", f"- righe: {t['rowCount']}", "### Righe Versilia"]
    for item in t["townRows"]:
        lines.append(f"- riga {item['row']} · {', '.join(item['towns'])}: `{item['values']}`")
    lines += ["", "### Copertura Toscana"]
    for town, count in t["townCoverage"].items():
        lines.append(f"- {town}: {count} righe")

    (OUT / "probe.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    missing_istat = [town for town, hits in result["istat"]["townCoverage"].items() if not hits]
    missing_toscana = [town for town, count in result["toscana"]["townCoverage"].items() if count == 0]
    print(f"Istat sheets: {len(result['istat']['sheets'])}; missing towns: {missing_istat}")
    print(f"Toscana rows: {t['rowCount']}; missing towns: {missing_toscana}")
    if missing_istat or missing_toscana:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
