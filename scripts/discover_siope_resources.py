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
BUILDER = ROOT / "scripts" / "build_siope_history.py"
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

    # Some CKAN deployments do not honour quoted searches. Retry with the stable
    # year, region and SIOPE terms, then require an exact title match locally.
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


def patch_builder_download() -> None:
    """Use CKAN's canonical dump variants when the catalogue's .csv URL is stale."""
    if not BUILDER.exists():
        print("Costruttore SIOPE non presente: nessuna patch runtime necessaria.")
        return
    text = BUILDER.read_text(encoding="utf-8")
    old = '''def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
    official_url = str(resource["url"]).replace("http://", "https://", 1)
    response = session.get(official_url, timeout=TIMEOUT)
    response.raise_for_status()
    content = response.content
    if len(content) < 1_000 or b";" not in content[:20_000]:
        raise RuntimeError(f"Risposta CSV non valida: {official_url}, {len(content)} byte")
    return content, official_url
'''
    new = '''def download_csv(session: requests.Session, resource: dict) -> tuple[bytes, str]:
    official_url = str(resource["url"]).replace("http://", "https://", 1)
    candidates = [official_url]
    if official_url.lower().endswith(".csv"):
        canonical = official_url[:-4]
        candidates.extend([canonical, canonical + "?format=csv"])
    errors = []
    for candidate in candidates:
        try:
            response = session.get(candidate, timeout=TIMEOUT, headers={"Accept": "text/csv,*/*;q=0.8"})
            response.raise_for_status()
            content = response.content
            sample = content[:20_000]
            if len(content) >= 1_000 and b"\\n" in sample and any(mark in sample for mark in (b";", b",", b"\\t", b"|")):
                return content, candidate
            preview = content[:300].decode("utf-8", errors="replace")
            errors.append(f"{candidate}: risposta non CSV, {len(content)} byte, {preview!r}")
        except requests.RequestException as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    raise RuntimeError("Risorsa SIOPE non scaricabile tramite i dump CKAN ufficiali:\\n" + "\\n".join(errors))
'''
    if new in text:
        print("Fallback canonico CKAN già presente nel costruttore SIOPE.")
        return
    if old not in text:
        raise RuntimeError("Funzione download_csv del costruttore SIOPE non riconosciuta")
    BUILDER.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Fallback canonico CKAN applicato al costruttore SIOPE.")


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
    patch_builder_download()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Risorse SIOPE censite in {OUT}")


if __name__ == "__main__":
    main()
