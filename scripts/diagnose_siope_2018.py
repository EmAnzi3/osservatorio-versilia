#!/usr/bin/env python3
"""Read-only diagnostic for municipality recognition in the official SIOPE 2018 dump."""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import build_siope_history as builder

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def choose_resource(package: dict) -> dict:
    candidates = [
        item for item in package.get("resources", [])
        if str(item.get("mimetype", "")).casefold() == "text/csv"
        or str(item.get("format", "")).casefold() == "csv"
    ]
    if not candidates:
        raise RuntimeError("Nessuna risorsa CSV nel pacchetto SIOPE 2018 Entrata")
    return candidates[0]


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = discovery["datasets"]["entrata-2018-toscana"]
    resource = choose_resource(package)

    session = builder.requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0"})
    content, url = builder.download_csv(session, resource)
    text, encoding = builder.decode_csv(content)

    sample = text[:200_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"

    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    headers = list(reader.fieldnames or [])
    normalized_headers = {header: norm(header) for header in headers}
    interesting_headers = [
        header for header, normalized in normalized_headers.items()
        if any(token in normalized for token in (
            "ente", "denomin", "comune", "territ", "prov", "codice", "cod ",
            "istat", "fisc", "mese", "period", "data", "import", "categoria",
        ))
    ]

    row_count = 0
    matches: dict[str, list[dict[str, str]]] = defaultdict(list)
    value_counts: dict[str, Counter[str]] = {header: Counter() for header in interesting_headers}
    samples: list[dict[str, str]] = []
    lucca_rows: list[dict[str, str]] = []

    for row in reader:
        row_count += 1
        if len(samples) < 5:
            samples.append(row)
        joined = " | ".join(norm(value) for value in row.values())
        for town in TOWNS:
            if norm(town) in joined and len(matches[town]) < 8:
                matches[town].append(row)
        if "lucca" in joined and len(lucca_rows) < 20:
            lucca_rows.append(row)
        for header in interesting_headers:
            value = str(row.get(header, "")).strip()
            if value:
                value_counts[header][value] += 1

    print("=== SIOPE 2018 ENTRATA: DIAGNOSTICA LETTURA ===")
    print(f"URL effettivo: {url}")
    print(f"Byte: {len(content)}")
    print(f"Decodifica: {encoding}")
    print(f"Separatore: {delimiter!r}")
    print(f"Righe dati: {row_count}")
    print(f"Intestazioni ({len(headers)}): {headers}")
    print(f"Colonne candidate: {interesting_headers}")

    for town in TOWNS:
        print(f"\n=== MATCH TESTUALE {town}: {len(matches[town])} campioni ===")
        for row in matches[town]:
            print({header: row.get(header) for header in interesting_headers if row.get(header)})

    print(f"\n=== RIGHE CONTENENTI LUCCA: {len(lucca_rows)} campioni ===")
    for row in lucca_rows:
        print({header: row.get(header) for header in interesting_headers if row.get(header)})

    print("\n=== VALORI PIÙ FREQUENTI NELLE COLONNE CANDIDATE ===")
    for header in interesting_headers:
        print(f"-- {header} --")
        for value, count in value_counts[header].most_common(40):
            print(f"{count}\t{value}")

    print("\n=== PRIME RIGHE, COLONNE CANDIDATE ===")
    for row in samples:
        print({header: row.get(header) for header in interesting_headers if row.get(header)})

    if not matches["Camaiore"]:
        raise RuntimeError(
            "Diagnostica conclusa: nessuna cella contiene letteralmente 'Camaiore'; "
            "serve identificare l’ente tramite le colonne e i codici stampati sopra."
        )


if __name__ == "__main__":
    main()
