#!/usr/bin/env python3
"""Read-only diagnostic for municipality recognition in SIOPE 2019 Entrata."""
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
DUMP_BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/"
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


def choose_csv_resource(metadata: dict) -> dict:
    candidates = [
        item for item in metadata.get("resources", [])
        if str(item.get("mimetype", "")).casefold() == "text/csv"
    ]
    if not candidates:
        candidates = [
            item for item in metadata.get("resources", [])
            if str(item.get("format", "")).casefold() == "csv"
            and not str(item.get("url", "")).casefold().endswith(".pdf")
        ]
    if len(candidates) != 1:
        raise RuntimeError(f"Risorsa CSV SIOPE 2019 non univoca: {candidates}")
    return candidates[0]


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = discovery["datasets"]["entrata-2019-toscana"]
    package_id = str(package["id"])

    session = builder.requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0"})
    metadata_response = session.get(f"{DUMP_BASE}{package_id}", timeout=45)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    resource = choose_csv_resource(metadata)

    content, url = builder.download_csv(session, resource)
    text, encoding = builder.decode_csv(content)
    sample = text[:500_000]
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
            "comparto", "siope",
        ))
    ]

    row_count = 0
    matches: dict[str, list[dict[str, str]]] = defaultdict(list)
    broad_matches: dict[str, int] = defaultdict(int)
    lucca_rows: list[dict[str, str]] = []
    code_046_rows: list[dict[str, str]] = []
    samples: list[dict[str, str]] = []
    value_counts: dict[str, Counter[str]] = {header: Counter() for header in interesting_headers}

    for row in reader:
        row_count += 1
        if len(samples) < 8:
            samples.append(row)
        joined = " | ".join(norm(value) for value in row.values())
        for town in TOWNS:
            town_norm = norm(town)
            if town_norm in joined:
                broad_matches[town] += 1
                if len(matches[town]) < 12:
                    matches[town].append(row)
        if "lucca" in joined and len(lucca_rows) < 20:
            lucca_rows.append(row)
        if re.search(r"(?:^|\D)046(?:\D|$)", joined) and len(code_046_rows) < 20:
            code_046_rows.append(row)
        for header in interesting_headers:
            value = str(row.get(header, "")).strip()
            if value:
                value_counts[header][value] += 1

    print("=== SIOPE 2019 ENTRATA: DIAGNOSTICA ENTI ===")
    print(f"URL CSV effettivo: {url}")
    print(f"Risorsa CKAN: {json.dumps(resource, ensure_ascii=False, sort_keys=True)}")
    print(f"Byte: {len(content)}")
    print(f"Decodifica: {encoding}")
    print(f"Separatore: {delimiter!r}")
    print(f"Righe dati: {row_count}")
    print(f"Intestazioni ({len(headers)}): {headers}")
    print(f"Colonne candidate: {interesting_headers}")

    for town in TOWNS:
        print(f"\n=== MATCH {town}: {broad_matches[town]} righe; campioni {len(matches[town])} ===")
        for row in matches[town]:
            print({header: row.get(header) for header in interesting_headers if row.get(header)})

    print(f"\n=== RIGHE CONTENENTI LUCCA: {len(lucca_rows)} campioni ===")
    for row in lucca_rows:
        print({header: row.get(header) for header in interesting_headers if row.get(header)})

    print(f"\n=== RIGHE CONTENENTI CODICE 046: {len(code_046_rows)} campioni ===")
    for row in code_046_rows:
        print({header: row.get(header) for header in interesting_headers if row.get(header)})

    print("\n=== VALORI PIÙ FREQUENTI NELLE COLONNE CANDIDATE ===")
    for header in interesting_headers:
        print(f"-- {header} --")
        for value, count in value_counts[header].most_common(50):
            print(f"{count}\t{value}")

    print("\n=== PRIME RIGHE, COLONNE CANDIDATE ===")
    for row in samples:
        print({header: row.get(header) for header in interesting_headers if row.get(header)})

    if broad_matches["Camaiore"] == 0:
        raise RuntimeError(
            "Nessuna cella contiene letteralmente Camaiore: usare le colonne e i codici stampati."
        )


if __name__ == "__main__":
    main()
