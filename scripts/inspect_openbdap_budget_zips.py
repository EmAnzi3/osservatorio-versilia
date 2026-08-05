#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "openbdap-budget-zip-inspection.json"
BASE = "https://openbdap.rgs.mef.gov.it"
TIMEOUT = 180
TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
DOCUMENTS = {
    "2025-schemi": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2025-indicatori": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Piano degli indicatori_TOSCANA.zip",
    "2024-schemi": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2024-indicatori": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Piano degli indicatori_TOSCANA.zip",
}
TEXT_SUFFIXES = {".csv", ".txt", ".tsv"}


def decode_text(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace"), "latin-1-replace"


def sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample[:20000], delimiters=";,\t|").delimiter
    except csv.Error:
        counts = {delimiter: sample[:20000].count(delimiter) for delimiter in (";", ",", "\t", "|")}
        return max(counts, key=counts.get)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def inspect_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    suffix = Path(info.filename).suffix.lower()
    result = {
        "name": info.filename,
        "size": info.file_size,
        "compressed_size": info.compress_size,
        "crc": info.CRC,
    }
    if suffix not in TEXT_SUFFIXES or info.file_size > 250_000_000:
        return result

    raw = archive.read(info)
    text, encoding = decode_text(raw)
    delimiter = sniff_delimiter(text)
    result.update(
        {
            "encoding": encoding,
            "delimiter": "\\t" if delimiter == "\t" else delimiter,
            "line_count": text.count("\n") + (1 if text else 0),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    )

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for _, row in zip(range(6), reader):
        rows.append(row[:80])
    result["sample_rows"] = rows
    result["header"] = rows[0] if rows else []

    matches: dict[str, dict[str, object]] = {}
    lines = text.splitlines()
    for town in TOWNS:
        needle = town.casefold()
        matched_lines = [line for line in lines if needle in line.casefold()]
        matches[town] = {
            "line_count": len(matched_lines),
            "sample_lines": matched_lines[:4],
        }
    result["town_matches"] = matches
    return result


def inspect_document(session: requests.Session, label: str, path: str) -> dict:
    url = BASE + quote(path, safe="/:_-.")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    raw = response.content
    result = {
        "label": label,
        "url": response.url,
        "status_code": response.status_code,
        "content_type": response.headers.get("Content-Type"),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "members": [],
    }
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            result["members"].append(inspect_member(archive, info))
    return result


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
            "Accept": "application/zip,*/*;q=0.8",
        }
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "towns": TOWNS,
        "documents": {},
        "errors": [],
    }
    for label, path in DOCUMENTS.items():
        try:
            payload["documents"][label] = inspect_document(session, label, path)
        except Exception as exc:  # noqa: BLE001
            payload["errors"].append({"document": label, "error": repr(exc)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ispezione archivi scritta in {OUT}")
    if payload["errors"]:
        print(json.dumps(payload["errors"], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
