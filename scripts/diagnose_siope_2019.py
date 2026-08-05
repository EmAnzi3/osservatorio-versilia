#!/usr/bin/env python3
"""Read-only diagnostic for the official SIOPE 2019 Entrata dump format."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import build_siope_history as builder

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"


def choose_resource(package: dict) -> dict:
    candidates = [
        item for item in package.get("resources", [])
        if str(item.get("mimetype", "")).casefold() == "text/csv"
        or str(item.get("format", "")).casefold() == "csv"
    ]
    if not candidates:
        raise RuntimeError("Nessuna risorsa CSV nel pacchetto SIOPE 2019 Entrata")
    return candidates[0]


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = discovery["datasets"]["entrata-2019-toscana"]
    resource = choose_resource(package)

    session = builder.requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0"})
    content, url = builder.download_csv(session, resource)
    text, encoding = builder.decode_csv(content)
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]

    print("=== SIOPE 2019 ENTRATA: FORMATO DEL DUMP ===")
    print(f"URL effettivo: {url}")
    print(f"Byte: {len(content)}")
    print(f"Magic iniziale: {content[:32].hex()}")
    print(f"Decodifica: {encoding}")
    print(f"Caratteri: {len(text)}")
    print(f"Righe totali: {len(lines)}")
    print(f"Righe non vuote: {len(non_empty)}")
    print(f"NUL nel testo: {text.count(chr(0))}")

    print("\n=== PRIME 20 RIGHE GREZZE ===")
    for index, line in enumerate(lines[:20], start=1):
        print(f"{index}: {line[:1000]!r}")

    print("\n=== CONTEGGIO SEPARATORI NELLE PRIME RIGHE NON VUOTE ===")
    sample_lines = non_empty[:20]
    for delimiter in (";", ",", "\t", "|", ":"):
        counts = [line.count(delimiter) for line in sample_lines[:10]]
        widths = [len(next(csv.reader([line], delimiter=delimiter))) for line in sample_lines[:10]]
        print(f"{delimiter!r}: occorrenze={counts}; colonne={widths}")

    sample = "\n".join(sample_lines[:200])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|:")
        print(f"\nSniffer: separatore {dialect.delimiter!r}")
    except csv.Error as exc:
        print(f"\nSniffer fallito: {exc}")

    print("\n=== INTESTAZIONI CANDIDATE PER OGNI SEPARATORE ===")
    first = sample_lines[0] if sample_lines else ""
    for delimiter in (";", ",", "\t", "|", ":"):
        row = next(csv.reader([first], delimiter=delimiter))
        print(f"{delimiter!r}: {row[:80]}")

    if not non_empty:
        raise RuntimeError("Il dump SIOPE 2019 non contiene righe non vuote")


if __name__ == "__main__":
    main()
