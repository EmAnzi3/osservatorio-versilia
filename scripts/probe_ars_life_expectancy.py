#!/usr/bin/env python3
"""Temporary CI probe for the official ARS life-expectancy CSV export.

This file is diagnostic only and will be removed before the PR is ready.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json

import requests

EXPORT_URL = "https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=1290"
TARGET_CODES = {"046005", "046013", "046018", "046024", "046028", "046030", "046033"}
TARGET_NAMES = {
    "CAM AIORE".replace(" ", ""),
    "FORTEDEIMARMI",
    "MASSAROSA",
    "PIETRASANTA",
    "SERAVEZZA",
    "STAZZEMA",
    "VIAREGGIO",
    "VERSILIA",
    "REGIONETOSCANA",
    "TOSCANA",
}


def norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def main() -> None:
    response = requests.get(
        EXPORT_URL,
        timeout=90,
        headers={
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.5",
            "User-Agent": "OsservatorioVersilia-source-audit/1.0",
        },
    )
    response.raise_for_status()
    raw = response.content
    print("=== EXPORT METADATA ===")
    print(json.dumps({
        "url": response.url,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "content_disposition": response.headers.get("content-disposition"),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }, ensure_ascii=False))

    text = None
    used_encoding = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            used_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("Unable to decode ARS export")

    print(f"encoding={used_encoding}")
    print("=== FIRST RAW LINES ===")
    for line in text.splitlines()[:12]:
        print(line[:2000])

    sample = text[:20000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"
    print(f"delimiter={delimiter!r}")

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    print("=== HEADERS ===")
    print(json.dumps(reader.fieldnames, ensure_ascii=False))

    rows = list(reader)
    print(f"row_count={len(rows)}")
    print("=== TARGET ROWS ===")
    matched = []
    for row in rows:
        normalized_values = {norm(v) for v in row.values()}
        joined = "|".join(normalized_values)
        if any(code in normalized_values or code in joined for code in TARGET_CODES) or any(
            name and (name in normalized_values or name in joined) for name in TARGET_NAMES
        ):
            matched.append(row)
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    print(f"target_row_count={len(matched)}")


if __name__ == "__main__":
    main()
