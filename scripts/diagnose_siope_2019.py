#!/usr/bin/env python3
"""Read-only probe for official HTTPS access to SIOPE 2019 Entrata."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote, urljoin

import build_siope_history as builder

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3"


def slim_resource(resource: dict) -> dict:
    return {
        key: resource.get(key)
        for key in (
            "id", "name", "format", "mimetype", "resource_type", "url",
            "download_url", "size", "package_id", "description",
        )
        if resource.get(key) not in (None, "")
    }


def probe(session, label: str, url: str, timeout: int = 18) -> None:
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        content = response.content
        print("=" * 90)
        print(label)
        print(json.dumps({
            "requested_url": url,
            "final_url": response.url,
            "status": response.status_code,
            "content_type": response.headers.get("content-type"),
            "content_disposition": response.headers.get("content-disposition"),
            "bytes": len(content),
            "magic_hex": content[:32].hex(),
            "preview": content[:1200].decode("utf-8", errors="replace"),
        }, ensure_ascii=False, indent=2))
    except Exception as exc:
        print("=" * 90)
        print(label)
        print(f"ERROR: {type(exc).__name__}: {exc}")


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = discovery["datasets"]["entrata-2019-toscana"]
    package_id = str(package["id"])

    session = builder.requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0",
        "Accept": "application/json,text/csv,application/octet-stream,*/*;q=0.8",
    })

    package_show_url = f"{BASE}/action/package_show?id={quote(package_id)}"
    package_response = session.get(package_show_url, timeout=25)
    package_response.raise_for_status()
    package_payload = package_response.json()
    package_result = package_payload.get("result", package_payload)
    resources = package_result.get("resources", []) if isinstance(package_result, dict) else []

    print("=== PACKAGE_SHOW SIOPE 2019 ENTRATA ===")
    print(f"Package ID: {package_id}")
    print(f"Titolo: {package_result.get('title') if isinstance(package_result, dict) else None}")
    print(json.dumps([slim_resource(item) for item in resources], ensure_ascii=False, indent=2))

    package_metadata_url = f"{BASE}/datastore/dump/{package_id}"
    metadata_response = session.get(package_metadata_url, timeout=25)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    metadata_resources = metadata.get("resources", [])
    print("\n=== RISORSE DAL DUMP METADATI ===")
    print(json.dumps([slim_resource(item) for item in metadata_resources], ensure_ascii=False, indent=2))

    all_resources = resources + metadata_resources
    numeric_ids = list(dict.fromkeys(
        str(item.get("id") or "").strip()
        for item in all_resources
        if str(item.get("id") or "").strip()
    ))
    explicit_urls = list(dict.fromkeys(
        str(item.get(key) or "").strip()
        for item in all_resources
        for key in ("url", "download_url")
        if str(item.get(key) or "").strip()
    ))

    probes: list[tuple[str, str]] = [
        ("package-show", package_show_url),
        ("dump-package-metadata", package_metadata_url),
        ("csv-https", f"{BASE}/datastore/dump/{package_id}.csv"),
        ("csv-https-format", f"{BASE}/datastore/dump/{package_id}.csv?format=csv"),
        ("csv-https-download", f"{BASE}/datastore/dump/{package_id}.csv?download=1"),
        ("datastore-search-package", f"{BASE}/action/datastore_search?resource_id={quote(package_id)}&limit=3"),
        (
            "datastore-search-sql-package",
            f"{BASE}/action/datastore_search_sql?sql={quote(f'SELECT * FROM \"{package_id}\" LIMIT 3')}",
        ),
    ]

    for resource_id in numeric_ids:
        probes.extend([
            (f"resource-show-{resource_id}", f"{BASE}/action/resource_show?id={quote(resource_id)}"),
            (f"datastore-search-{resource_id}", f"{BASE}/action/datastore_search?resource_id={quote(resource_id)}&limit=3"),
            (f"dump-{resource_id}", f"{BASE}/datastore/dump/{quote(resource_id)}"),
            (f"dump-{resource_id}-csv", f"{BASE}/datastore/dump/{quote(resource_id)}.csv"),
        ])

    for index, raw_url in enumerate(explicit_urls, start=1):
        https_url = raw_url.replace("http://", "https://", 1)
        probes.append((f"resource-url-{index}", https_url))
        resource_name = Path(https_url.split("?", 1)[0]).name
        resource_id = next(
            (
                str(item.get("id")) for item in all_resources
                if str(item.get("url") or "").strip() == raw_url
            ),
            "",
        )
        if resource_id and resource_name:
            standard = (
                "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/dataset/"
                f"{package_id}/resource/{resource_id}/download/{quote(resource_name)}"
            )
            probes.append((f"standard-download-{resource_id}", standard))

    for item in all_resources:
        resource_type = str(item.get("resource_type") or "").casefold()
        url = str(item.get("url") or "").strip().replace("http://", "https://", 1)
        if url and (resource_type == "odata" or "odata" in url.casefold()):
            separator = "&" if "?" in url else "?"
            probes.append(("odata-top-3", f"{url}{separator}$top=3"))

    seen: set[str] = set()
    print("\n=== PROVE ENDPOINT UFFICIALI ===")
    for label, url in probes:
        normalized_url = urljoin(package_show_url, url)
        if normalized_url in seen:
            continue
        seen.add(normalized_url)
        probe(session, label, normalized_url)


if __name__ == "__main__":
    main()
