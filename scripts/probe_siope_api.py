#!/usr/bin/env python3
"""Probe official CKAN/OData access variants for one SIOPE dataset."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"


def main() -> None:
    payload = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    package = payload["datasets"]["entrata-2018-toscana"]
    package_id = str(package["id"])
    csv_resource = next(
        item for item in package["resources"]
        if str(item.get("mimetype", "")).lower() == "text/csv"
    )
    numeric_resource_id = str(csv_resource["id"])
    odata = next(
        item for item in package["resources"]
        if str(item.get("resource_type", "")).lower() == "odata"
    )["url"]
    base = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3"
    urls = [
        ("catalogue-csv", str(csv_resource["url"]).replace("http://", "https://", 1)),
        ("dump-no-extension", f"{base}/datastore/dump/{package_id}"),
        ("dump-format-query", f"{base}/datastore/dump/{package_id}?format=csv"),
        ("search-package-uuid", f"{base}/action/datastore_search?resource_id={package_id}&limit=3"),
        ("search-numeric-resource", f"{base}/action/datastore_search?resource_id={numeric_resource_id}&limit=3"),
        ("search-sql-package", f"{base}/action/datastore_search_sql?sql={quote(f'SELECT * FROM \"{package_id}\" LIMIT 3')}"),
        ("odata-top", f"{odata}?$top=3"),
    ]
    session = requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0", "Accept": "*/*"})
    for label, url in urls:
        try:
            response = session.get(url, timeout=60)
            preview = response.content[:1200].decode("utf-8", errors="replace")
            print("=" * 80)
            print(label)
            print(f"URL: {url}")
            print(f"STATUS: {response.status_code}")
            print(f"CONTENT-TYPE: {response.headers.get('content-type')}")
            print(f"LENGTH: {len(response.content)}")
            print("BODY:")
            print(preview)
        except requests.RequestException as exc:
            print("=" * 80)
            print(label)
            print(f"ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
