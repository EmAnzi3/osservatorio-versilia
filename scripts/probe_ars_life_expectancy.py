#!/usr/bin/env python3
"""Temporary CI probe for the official ARS life-expectancy export.

This file is diagnostic only and will be removed before the PR is ready.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile

import requests

EXPORT_URL = "https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=1290"
TARGET_CODES = {"046005", "046013", "046018", "046024", "046028", "046030", "046033"}
TARGET_NAMES = {
    "CAMAIORE",
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


def decode(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Unable to decode ARS CSV")


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
    outer = response.content
    print("=== EXPORT METADATA ===")
    print(json.dumps({
        "url": response.url,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "content_disposition": response.headers.get("content-disposition"),
        "bytes": len(outer),
        "sha256": hashlib.sha256(outer).hexdigest(),
    }, ensure_ascii=False))

    with zipfile.ZipFile(io.BytesIO(outer)) as archive:
        names = archive.namelist()
        print("=== ZIP MEMBERS ===")
        print(json.dumps(names, ensure_ascii=False))
        csv_name = next((name for name in names if name.lower().endswith(".csv")), None)
        if not csv_name:
            raise RuntimeError("ARS export does not contain a CSV")
        raw = archive.read(csv_name)

    text, encoding = decode(raw)
    print("=== CSV METADATA ===")
    print(json.dumps({
        "member": csv_name,
        "encoding": encoding,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }, ensure_ascii=False))
    print("=== FIRST RAW LINES ===")
    for line in text.splitlines()[:8]:
        print(line[:2000])

    sample = text[:30000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"
    print(f"delimiter={delimiter!r}")

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    print("=== HEADERS ===")
    print(json.dumps(reader.fieldnames, ensure_ascii=False))
    rows = list(reader)
    print(f"row_count={len(rows)}")

    print("=== DISTINCT VALUES BY COLUMN ===")
    for field in reader.fieldnames or []:
        values = sorted({str(row.get(field, "")).strip() for row in rows})
        if len(values) <= 40:
            print(json.dumps({"field": field, "values": values}, ensure_ascii=False))

    matched = []
    for row in rows:
        normalized_values = {norm(v) for v in row.values()}
        joined = "|".join(normalized_values)
        if any(code in normalized_values or code in joined for code in TARGET_CODES) or any(
            name and (name in normalized_values or name in joined) for name in TARGET_NAMES
        ):
            matched.append(row)

    print("=== TARGET ROWS ===")
    for row in matched:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    print(f"target_row_count={len(matched)}")


if __name__ == "__main__":
    main()
