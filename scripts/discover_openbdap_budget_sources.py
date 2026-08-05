#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "openbdap-budget-discovery.json"
BASE = "https://bdap-opendata.rgs.mef.gov.it"
CKAN = BASE + "/SpodCkanApi/api/3/action"
FET_URL = "https://openbdap.rgs.mef.gov.it/it/FET/Analizza"
TIMEOUT = 60

QUERIES = [
    "Finanza degli Enti Territoriali",
    "Rendiconto Schemi di Bilancio",
    "Rendiconto Piano degli Indicatori",
    "bilanci armonizzati enti territoriali",
    "debito residuo enti territoriali",
]

KEYWORDS = (
    "finanza degli enti territoriali",
    "rendiconto - schemi di bilancio",
    "rendiconto schemi di bilancio",
    "rendiconto - piano degli indicatori",
    "bilanci armonizzati",
    "debito residuo enti territoriali",
)


def get_json(session: requests.Session, url: str, **params):
    response = session.get(url, params=params or None, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def compact_resource(resource: dict) -> dict:
    return {
        "id": resource.get("id"),
        "name": resource.get("name"),
        "description": resource.get("description"),
        "format": resource.get("format"),
        "mimetype": resource.get("mimetype"),
        "url": resource.get("url"),
        "url_type": resource.get("url_type"),
        "created": resource.get("created"),
        "last_modified": resource.get("last_modified"),
    }


def compact_package(package: dict) -> dict:
    return {
        "id": package.get("id"),
        "name": package.get("name"),
        "title": package.get("title"),
        "notes": package.get("notes"),
        "metadata_created": package.get("metadata_created"),
        "metadata_modified": package.get("metadata_modified"),
        "groups": [
            {"id": g.get("id"), "name": g.get("name"), "title": g.get("title")}
            for g in package.get("groups", [])
        ],
        "tags": [tag.get("name") for tag in package.get("tags", [])],
        "resources": [compact_resource(r) for r in package.get("resources", [])],
    }


def relevant(package: dict) -> bool:
    haystack = " ".join(
        str(package.get(field, "")) for field in ("title", "name", "notes")
    ).lower()
    haystack += " " + " ".join(tag.get("name", "") for tag in package.get("tags", [])).lower()
    haystack += " " + " ".join(group.get("title", "") for group in package.get("groups", [])).lower()
    return any(keyword in haystack for keyword in KEYWORDS)


def discover_ckan(session: requests.Session) -> dict:
    result: dict[str, object] = {"queries": {}, "groups": [], "packages": []}
    packages: dict[str, dict] = {}

    group_payload = get_json(session, CKAN + "/group_list", all_fields="true")
    groups = group_payload.get("result", []) if group_payload.get("success") else []
    matching_groups = []
    for group in groups:
        text = f"{group.get('name', '')} {group.get('title', '')} {group.get('description', '')}".lower()
        if "territorial" in text or "bilanci degli enti" in text or "finanza" in text:
            matching_groups.append(
                {
                    "id": group.get("id"),
                    "name": group.get("name"),
                    "title": group.get("title"),
                    "description": group.get("description"),
                    "package_count": group.get("package_count"),
                }
            )
    result["groups"] = matching_groups

    for query in QUERIES:
        payload = get_json(session, CKAN + "/package_search", q=query, rows=100)
        packages_found = payload.get("result", {}).get("results", []) if payload.get("success") else []
        result["queries"][query] = {
            "count": payload.get("result", {}).get("count"),
            "package_ids": [p.get("id") for p in packages_found],
        }
        for package in packages_found:
            if relevant(package):
                packages[package.get("id") or package.get("name")] = package

    for group in matching_groups:
        name = group.get("name")
        if not name:
            continue
        payload = get_json(session, CKAN + "/package_search", fq=f"groups:{name}", rows=1000)
        for package in payload.get("result", {}).get("results", []) if payload.get("success") else []:
            if relevant(package):
                packages[package.get("id") or package.get("name")] = package

    result["packages"] = [compact_package(p) for p in packages.values()]
    return result


def discover_page(session: requests.Session) -> dict:
    response = session.get(FET_URL, timeout=TIMEOUT)
    response.raise_for_status()
    html = response.text
    urls = set()
    for match in re.findall(r"(?:href|src|action)=[\"']([^\"']+)[\"']", html, flags=re.I):
        urls.add(urljoin(FET_URL, match))

    scripts = sorted(url for url in urls if url.lower().split("?")[0].endswith(".js"))
    interesting_urls = sorted(
        url
        for url in urls
        if any(token in url.lower() for token in ("fet", "rend", "bilanc", "download", "zip", "csv"))
    )

    snippets = []
    endpoint_pattern = re.compile(
        r".{0,180}(?:rendiconto|schemi.{0,20}bilancio|download|\.zip|\.csv|ajax|api/).{0,260}",
        flags=re.I,
    )
    for script_url in scripts[:30]:
        try:
            script_response = session.get(script_url, timeout=TIMEOUT)
            script_response.raise_for_status()
        except requests.RequestException as exc:
            snippets.append({"script": script_url, "error": str(exc)})
            continue
        text = script_response.text
        matches = []
        for match in endpoint_pattern.finditer(text):
            snippet = " ".join(match.group(0).split())
            if snippet not in matches:
                matches.append(snippet)
            if len(matches) >= 30:
                break
        if matches:
            snippets.append({"script": script_url, "matches": matches})

    return {
        "url": FET_URL,
        "status_code": response.status_code,
        "html_length": len(html),
        "scripts": scripts,
        "interesting_urls": interesting_urls,
        "script_snippets": snippets,
    }


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        }
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Individuare fonti ufficiali e risorse elaborabili per i bilanci comunali della Versilia.",
        "ckan_api": CKAN,
        "fet_page": FET_URL,
    }
    errors = []
    try:
        payload["ckan"] = discover_ckan(session)
    except Exception as exc:  # noqa: BLE001
        errors.append({"stage": "ckan", "error": repr(exc)})
    try:
        payload["fet_discovery"] = discover_page(session)
    except Exception as exc:  # noqa: BLE001
        errors.append({"stage": "fet_page", "error": repr(exc)})
    payload["errors"] = errors

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audit scritto in {OUT}")
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
