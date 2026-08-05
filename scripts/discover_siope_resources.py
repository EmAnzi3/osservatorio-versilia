#!/usr/bin/env python3
"""Inspect the official BDAP CKAN catalogue before building SIOPE histories."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
API = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action"
DATASETS = {
    "entrate-2025-toscana": "spd_rnd_ent_sio_reg09_01_2025",
    "spese-2025-toscana": "spd_rnd_spe_sio_reg09_01_2025",
    "entrate-2018-toscana": "spd_rnd_ent_sio_reg09_01_2018",
    "spese-2018-toscana": "spd_rnd_spe_sio_reg09_01_2018",
}


def request_json(session: requests.Session, endpoint: str, params: dict[str, str]) -> dict:
    response = session.get(f"{API}/{endpoint}", params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN {endpoint} non riuscita: {payload}")
    return payload["result"]


def find_package(session: requests.Session, identifier: str) -> dict:
    try:
        result = request_json(session, "package_show", {"id": identifier})
        if result:
            return result
    except (requests.RequestException, RuntimeError, ValueError):
        pass

    result = request_json(session, "package_search", {"q": identifier, "rows": "20"})
    packages = result.get("results", []) if isinstance(result, dict) else []
    exact = [
        item for item in packages
        if identifier.lower() in {
            str(item.get("name", "")).lower(),
            str(item.get("id", "")).lower(),
            str(item.get("identifier", "")).lower(),
        }
        or identifier.lower() in str(item.get("url", "")).lower()
    ]
    if exact:
        return exact[0]
    if len(packages) == 1:
        return packages[0]
    raise RuntimeError(f"Dataset CKAN non individuato in modo univoco: {identifier}")


def slim(package: dict) -> dict:
    resources = []
    for resource in package.get("resources", []):
        resources.append(
            {
                key: resource.get(key)
                for key in (
                    "id",
                    "name",
                    "description",
                    "format",
                    "mimetype",
                    "url",
                    "download_url",
                    "resource_type",
                    "created",
                    "last_modified",
                )
                if resource.get(key) not in (None, "")
            }
        )
    return {
        "id": package.get("id"),
        "name": package.get("name"),
        "title": package.get("title"),
        "url": package.get("url"),
        "metadata_created": package.get("metadata_created"),
        "metadata_modified": package.get("metadata_modified"),
        "resources": resources,
    }


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
            "Accept": "application/json",
        }
    )
    discovered = {
        label: slim(find_package(session, identifier))
        for label, identifier in DATASETS.items()
    }
    if any(not item["resources"] for item in discovered.values()):
        raise RuntimeError("Almeno un dataset SIOPE non espone risorse scaricabili")
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue": "BDAP Open Data — API CKAN v3",
        "api": API,
        "datasets": discovered,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Risorse SIOPE censite in {OUT}")


if __name__ == "__main__":
    main()
