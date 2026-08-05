#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "openbdap-budget-candidates.json"
BASE = "https://openbdap.rgs.mef.gov.it"
TIMEOUT = 180
TOWNS = {
    "005": "Camaiore",
    "013": "Forte dei Marmi",
    "018": "Massarosa",
    "024": "Pietrasanta",
    "028": "Seravezza",
    "030": "Stazzema",
    "033": "Viareggio",
}
ARCHIVES = {
    "2025-schemi": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2025-indicatori": "/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Piano degli indicatori_TOSCANA.zip",
    "2024-schemi": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Schemi di bilancio_TOSCANA.zip",
    "2024-indicatori": "/Datasets_FET/Rendiconto/2024/2024_Rendiconto - Piano degli indicatori_TOSCANA.zip",
}
TARGET_SUFFIXES = (
    "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv",
    "Rendiconto SDB Entrate Riepilogo Titoli_TOSCANA.csv",
    "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv",
    "Rendiconto SDB Spese Riepilogo Titoli_TOSCANA.csv",
    "Rendiconto PDI Analitici di Entrate 2-b_TOSCANA.csv",
    "Rendiconto PDI Analitici di Spese 2-d_TOSCANA.csv",
    "Rendiconto PDI Sintetici Allegato 2-a_TOSCANA.csv",
)


def decode(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace"), "latin-1-replace"


def download(session: requests.Session, path: str) -> tuple[bytes, str]:
    url = BASE + quote(path, safe="/:_-.")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content, response.url


def extract_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    raw = archive.read(info)
    text, encoding = decode(raw)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in reader:
        province = (row.get("Codice Provincia") or "").strip()
        municipality = (row.get("Codice Comune") or "").strip().zfill(3)
        if province == "046" and municipality in TOWNS:
            clean = {key: value for key, value in row.items() if key and key.strip()}
            grouped[TOWNS[municipality]].append(clean)
    return {
        "member": info.filename,
        "encoding": encoding,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "header": reader.fieldnames,
        "town_rows": grouped,
        "coverage": {town: len(grouped.get(town, [])) for town in TOWNS.values()},
    }


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
        "scope": "Rendiconti OpenBDAP Toscana 2024-2025, provincia di Lucca, sette Comuni dell'Osservatorio.",
        "town_codes": TOWNS,
        "archives": {},
        "errors": [],
    }
    for label, path in ARCHIVES.items():
        try:
            raw, final_url = download(session, path)
            entry = {
                "url": final_url,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "files": {},
            }
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for info in archive.infolist():
                    if info.filename.endswith(TARGET_SUFFIXES):
                        entry["files"][info.filename] = extract_member(archive, info)
            payload["archives"][label] = entry
        except Exception as exc:  # noqa: BLE001
            payload["errors"].append({"archive": label, "error": repr(exc)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Candidati OpenBDAP scritti in {OUT}")
    if payload["errors"]:
        print(json.dumps(payload["errors"], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
