#!/usr/bin/env python3
"""Read-only diagnostic for the official SIOPE 2019 Entrata resource."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

import build_siope_history as builder

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
DUMP_BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/"


def describe_response(session, url: str) -> None:
    try:
        response = session.get(url, timeout=45, allow_redirects=True)
        content = response.content
        print(
            json.dumps(
                {
                    "requested_url": url,
                    "final_url": response.url,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type"),
                    "content_disposition": response.headers.get("content-disposition"),
                    "bytes": len(content),
                    "magic_hex": content[:24].hex(),
                    "preview": content[:220].decode("utf-8", errors="replace"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except Exception as exc:
        print(json.dumps({"requested_url": url, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = discovery["datasets"]["entrata-2019-toscana"]
    package_id = str(package["id"])
    package_url = f"{DUMP_BASE}{package_id}"

    session = builder.requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0",
        "Accept": "application/json,text/csv,application/octet-stream,*/*;q=0.8",
    })

    response = session.get(package_url, timeout=45)
    response.raise_for_status()
    metadata = response.json()
    resources = metadata.get("resources", [])

    print("=== SIOPE 2019 ENTRATA: PACCHETTO CKAN ===")
    print(f"Package ID: {package_id}")
    print(f"Package URL effettivo: {response.url}")
    print(f"Risorse dichiarate: {len(resources)}")
    print(json.dumps(resources, ensure_ascii=False, indent=2, sort_keys=True))

    candidate_urls: list[str] = []
    for resource in resources:
        resource_id = str(resource.get("id") or "").strip()
        for key in ("url", "download_url"):
            value = str(resource.get(key) or "").strip()
            if value:
                candidate_urls.append(urljoin(response.url, value))
        if resource_id:
            candidate_urls.extend([
                f"{DUMP_BASE}{resource_id}",
                f"{DUMP_BASE}{resource_id}.csv",
                f"{DUMP_BASE}{resource_id}?format=csv",
            ])

    unique_candidates = list(dict.fromkeys(candidate_urls))
    print("\n=== PROVA ENDPOINT DELLE RISORSE ===")
    for candidate in unique_candidates:
        describe_response(session, candidate)

    if not resources:
        raise RuntimeError("Il pacchetto CKAN non dichiara risorse")


if __name__ == "__main__":
    main()
