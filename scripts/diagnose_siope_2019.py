#!/usr/bin/env python3
"""Read-only probe for the official SIOPE 2019 OData resource."""
from __future__ import annotations

import json
import time
from urllib.parse import quote

import build_siope_history as builder

BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3"
PACKAGE_ID = "7deb457c-3207-481f-bed0-ffd45be4ff59"


def request_probe(
    session,
    label: str,
    url: str,
    accept: str,
    attempts: int = 3,
    timeout: int = 25,
) -> None:
    outcomes = []
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            response = session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={"Accept": accept},
            )
            elapsed = round(time.monotonic() - started, 3)
            content = response.content
            outcomes.append({
                "attempt": attempt,
                "status": response.status_code,
                "elapsed_seconds": elapsed,
                "final_url": response.url,
                "content_type": response.headers.get("content-type"),
                "content_disposition": response.headers.get("content-disposition"),
                "retry_after": response.headers.get("retry-after"),
                "bytes": len(content),
                "magic_hex": content[:32].hex(),
                "preview": content[:1600].decode("utf-8", errors="replace"),
            })
            if response.status_code < 500:
                break
        except Exception as exc:
            outcomes.append({
                "attempt": attempt,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "error": f"{type(exc).__name__}: {exc}",
            })
        if attempt < attempts:
            time.sleep(attempt * 2)

    print("=" * 100)
    print(label)
    print(json.dumps({
        "requested_url": url,
        "accept": accept,
        "outcomes": outcomes,
    }, ensure_ascii=False, indent=2))


def main() -> None:
    session = builder.requests.Session()
    session.headers.update({"User-Agent": "OsservatorioVersilia/1.0"})

    package_url = f"{BASE}/action/package_show?id={quote(PACKAGE_ID)}"
    package_response = session.get(package_url, timeout=30)
    package_response.raise_for_status()
    package = package_response.json()["result"]
    odata_resources = [
        resource for resource in package.get("resources", [])
        if str(resource.get("resource_type") or "").casefold() == "odata"
        or "odataproxy" in str(resource.get("url") or "").casefold()
    ]
    if len(odata_resources) != 1:
        raise RuntimeError(f"Risorsa OData non univoca: {odata_resources}")

    resource = odata_resources[0]
    rows_url = str(resource["url"]).replace("http://", "https://", 1)
    service_url = rows_url.rsplit("/DataRows", 1)[0]
    host_metadata_url = "https://bdap-opendata.rgs.mef.gov.it/ODataProxy/$metadata"

    print("=== RISORSA ODATA UFFICIALE SIOPE 2019 ENTRATA ===")
    print(json.dumps({
        key: resource.get(key)
        for key in (
            "id", "name", "format", "resource_type", "url", "package_id"
        )
    }, ensure_ascii=False, indent=2))

    variants = [
        ("rows-json-top", f"{rows_url}?$top=3&$format=json", "application/json"),
        ("rows-json-format-first", f"{rows_url}?$format=json&$top=3", "application/json"),
        ("rows-json-urlencoded", f"{rows_url}?%24top=3&%24format=json", "application/json"),
        ("rows-json-minimal", f"{rows_url}?$top=1", "application/json;odata=verbose,application/json"),
        ("rows-atom", f"{rows_url}?$top=1", "application/atom+xml,application/xml;q=0.9,*/*;q=0.1"),
        ("rows-xml-format", f"{rows_url}?$top=1&$format=xml", "application/xml,text/xml;q=0.9,*/*;q=0.1"),
        ("rows-count", f"{rows_url}/$count", "text/plain,*/*;q=0.1"),
        ("service-document-json", service_url, "application/json"),
        ("service-metadata-json", f"{service_url}/$metadata", "application/xml,application/json;q=0.8"),
        ("host-metadata", host_metadata_url, "application/xml,application/json;q=0.8"),
    ]

    for label, url, accept in variants:
        request_probe(session, label, url, accept)


if __name__ == "__main__":
    main()
