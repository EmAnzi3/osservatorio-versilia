#!/usr/bin/env python3
"""Inspect the official BDAP CKAN catalogue before building SIOPE histories."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
API = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action"
DATASETS = {
    f"{movement.lower()}-{year}-toscana": f"{year} - Toscana - SIOPE Movimenti cumulati mensili di {movement}"
    for year in range(2018, 2026)
    for movement in ("Entrata", "Spesa")
}


def normalized(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def request_json(session: requests.Session, endpoint: str, params: dict[str, str]) -> dict:
    response = session.get(f"{API}/{endpoint}", params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN {endpoint} non riuscita: {payload}")
    return payload["result"]


def find_package(session: requests.Session, title: str) -> dict:
    result = request_json(session, "package_search", {"q": f'"{title}"', "rows": "100"})
    packages = result.get("results", []) if isinstance(result, dict) else []
    target = normalized(title)
    exact = [item for item in packages if normalized(item.get("title")) == target]
    if len(exact) == 1:
        return exact[0]

    year = title[:4]
    result = request_json(
        session,
        "package_search",
        {"q": f"{year} Toscana SIOPE cumulati mensili", "rows": "200"},
    )
    packages = result.get("results", []) if isinstance(result, dict) else []
    exact = [item for item in packages if normalized(item.get("title")) == target]
    if len(exact) != 1:
        found = [str(item.get("title")) for item in packages[:20]]
        raise RuntimeError(f"Dataset CKAN non univoco: {title}. Risultati: {found}")
    return exact[0]


def slim(package: dict) -> dict:
    resources = []
    for resource in package.get("resources", []):
        resources.append(
            {
                key: resource.get(key)
                for key in (
                    "id", "name", "description", "format", "mimetype", "url",
                    "download_url", "resource_type", "created", "last_modified",
                )
                if resource.get(key) not in (None, "")
            }
        )
    extras = {
        str(item.get("key")): item.get("value")
        for item in package.get("extras", [])
        if item.get("key")
    }
    return {
        "id": package.get("id"),
        "name": package.get("name"),
        "title": package.get("title"),
        "url": package.get("url"),
        "notes": package.get("notes"),
        "metadata_created": package.get("metadata_created"),
        "metadata_modified": package.get("metadata_modified"),
        "resources": resources,
        "extras": extras,
    }


def main() -> None:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
        "Accept": "application/json",
    })
    discovered = {
        label: slim(find_package(session, title))
        for label, title in DATASETS.items()
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue": "BDAP Open Data — API CKAN v3",
        "api": API,
        "datasets": discovered,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Risorse SIOPE censite in {OUT}")

    # Temporary read-only diagnostics while aligning the historical parser with
    # the current official dump schema. Failure here is reported but does not
    # replace the strict validation performed by build_siope_history.py.
    diagnostic = ROOT / "scripts" / "diagnose_siope_2018.py"
    builder = ROOT / "scripts" / "build_siope_history.py"
    if diagnostic.exists() and builder.exists():
        try:
            import diagnose_siope_2018
            diagnose_siope_2018.main()
        except Exception as exc:  # diagnostic output must remain visible in CI
            print(f"DIAGNOSTICA SIOPE 2018 CONCLUSA CON ESITO: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
