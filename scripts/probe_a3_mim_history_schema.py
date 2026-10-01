#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; OsservatorioVersilia-A3-MIM-history/1.0)"
SPECS = {
    "registry_state": ("Scuole", "SCUANAGRAFESTAT"),
    "registry_private": ("Scuole", "SCUANAGRAFEPAR"),
    "classes_state": ("Studenti", "ALUCORSOINDCLASTA"),
    "classes_private": ("Studenti", "ALUCORSOINDCLAPAR"),
    "time_state": ("Studenti", "ALUTEMPOSCUOLASTA"),
    "time_private": ("Studenti", "ALUTEMPOSCUOLAPAR"),
}


def discover(session: requests.Session, area: str, prefix: str, year: str) -> str:
    home = f"https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area={area}"
    page = session.get(home, timeout=120)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    urls = []
    for anchor in soup.find_all("a", href=True):
        target = urljoin(page.url, anchor["href"])
        name = Path(target.split("?", 1)[0]).name
        if name.startswith(prefix) and year in name and name.lower().endswith(".csv"):
            urls.append(target)
    if not urls:
        raise RuntimeError(f"file non trovato: {prefix} {year}")
    return sorted(set(urls))[-1]


def inspect_csv(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=300, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8"})
    response.raise_for_status()
    raw = response.content
    text = raw.decode("utf-8-sig", errors="replace")
    first = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if first.count(";") >= first.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for idx, row in enumerate(reader):
        rows.append(row)
        if idx >= 5:
            break
    return {
        "url": response.url,
        "bytes": len(raw),
        "delimiter": delimiter,
        "header": rows[0] if rows else [],
        "samples": rows[1:],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = UA
    files = {}
    failures = []
    for role, (area, prefix) in SPECS.items():
        try:
            url = discover(session, area, prefix, args.year)
            files[role] = inspect_csv(session, url)
        except Exception as exc:
            failures.append({"role": role, "error": f"{type(exc).__name__}: {exc}"})

    report = {
        "schemaVersion": 1,
        "schoolYear": args.year,
        "files": files,
        "failures": failures,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "year": args.year,
        "files": len(files),
        "failures": len(failures),
        "roles": sorted(files),
    }, ensure_ascii=False))
    if len(files) < 4:
        raise SystemExit(f"MIM {args.year}: solo {len(files)}/6 file individuati")


if __name__ == "__main__":
    main()
