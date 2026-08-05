#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "openbdap-budget-documents.json"
BASE = "https://openbdap.rgs.mef.gov.it"
TIMEOUT = 90


def get_json(session: requests.Session, path: str, **params):
    url = urljoin(BASE, path)
    response = session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json(), response.url


def probe_url(session: requests.Session, url: str) -> dict:
    absolute = urljoin(BASE, url)
    result = {"url": absolute}
    try:
        response = session.get(
            absolute,
            headers={"Range": "bytes=0-4095"},
            allow_redirects=True,
            timeout=TIMEOUT,
            stream=True,
        )
        chunk = next(response.iter_content(4096), b"")
        result.update(
            {
                "status_code": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "content_range": response.headers.get("Content-Range"),
                "content_disposition": response.headers.get("Content-Disposition"),
                "first_bytes_hex": chunk[:32].hex(),
            }
        )
        response.close()
    except Exception as exc:  # noqa: BLE001
        result["error"] = repr(exc)
    return result


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
            "Accept": "application/json,*/*;q=0.8",
        }
    )

    payload: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "years": {},
        "documents": {},
        "errors": [],
    }

    try:
        years, requested = get_json(session, "/fet/GetDocumentsYears", type="Rendiconto")
        payload["years"] = {"requested_url": requested, "values": years}
    except Exception as exc:  # noqa: BLE001
        payload["errors"].append({"stage": "years", "error": repr(exc)})

    for year in (2025, 2024):
        for country in ("Toscana", "Tutte"):
            key = f"Rendiconto-{year}-{country}"
            try:
                documents, requested = get_json(
                    session,
                    "/fet/GetDocuments",
                    type="Rendiconto",
                    year=year,
                    country=country,
                )
                rows = []
                for document in documents:
                    row = {
                        "name": document.get("Name"),
                        "url": document.get("Url"),
                    }
                    if document.get("Url"):
                        row["probe"] = probe_url(session, document["Url"])
                    rows.append(row)
                payload["documents"][key] = {
                    "requested_url": requested,
                    "count": len(rows),
                    "rows": rows,
                }
            except Exception as exc:  # noqa: BLE001
                payload["errors"].append({"stage": key, "error": repr(exc)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sonda documenti scritta in {OUT}")
    if payload["errors"]:
        print(json.dumps(payload["errors"], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
