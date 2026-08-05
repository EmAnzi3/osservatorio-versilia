#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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
FET_JS = "https://openbdap.rgs.mef.gov.it/Content/js/fet_analizza.js"
TIMEOUT = 20

QUERIES = [
    "Finanza degli Enti Territoriali",
    "Rendiconto Schemi di Bilancio",
    "Rendiconto Piano degli Indicatori",
    "bilanci armonizzati enti territoriali",
    "debito residuo enti territoriali",
]


def get_json(session: requests.Session, url: str, **params):
    response = session.get(url, params=params or None, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def compact_resource(resource: dict) -> dict:
    return {
        "id": resource.get("id"),
        "name": resource.get("name"),
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
        "groups": [g.get("title") or g.get("name") for g in package.get("groups", [])],
        "tags": [tag.get("name") for tag in package.get("tags", [])],
        "resources": [compact_resource(r) for r in package.get("resources", [])],
    }


def discover_ckan(session: requests.Session) -> dict:
    result: dict[str, object] = {"queries": {}, "packages": []}
    packages: dict[str, dict] = {}
    for query in QUERIES:
        payload = get_json(session, CKAN + "/package_search", q=query, rows=50)
        found = payload.get("result", {}).get("results", []) if payload.get("success") else []
        result["queries"][query] = {
            "count": payload.get("result", {}).get("count"),
            "package_ids": [p.get("id") for p in found],
        }
        for package in found:
            packages[package.get("id") or package.get("name")] = package
    result["packages"] = [compact_package(p) for p in packages.values()]
    return result


def quoted_strings(text: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"(['\"])(.*?)(?<!\\)\1", text, flags=re.S):
        value = match.group(2).strip()
        if not value or len(value) > 500:
            continue
        if any(token in value.lower() for token in (
            "fet", "rendiconto", "bilanc", "download", "schema", "indicator", "regione", "anno", "ajax", "api", "zip", "csv"
        )):
            values.append(value)
    return list(dict.fromkeys(values))[:300]


def context_snippets(text: str) -> list[str]:
    pattern = re.compile(
        r".{0,240}(?:\$\.ajax|\$\.get|\$\.post|url\s*:|fetch\(|rendiconto|schemi?\s+di\s+bilancio|download|\.zip|\.csv).{0,420}",
        flags=re.I | re.S,
    )
    snippets: list[str] = []
    for match in pattern.finditer(text):
        snippet = " ".join(match.group(0).split())
        if snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= 120:
            break
    return snippets


def discover_page(session: requests.Session) -> dict:
    response = session.get(FET_URL, timeout=TIMEOUT)
    response.raise_for_status()
    html = response.text
    urls = sorted(
        {
            urljoin(FET_URL, match)
            for match in re.findall(r"(?:href|src|action)=[\"']([^\"']+)[\"']", html, flags=re.I)
        }
    )
    js_response = session.get(FET_JS, timeout=TIMEOUT)
    js_response.raise_for_status()
    js = js_response.text
    return {
        "url": FET_URL,
        "status_code": response.status_code,
        "html_length": len(html),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "scripts": [u for u in urls if u.lower().split("?")[0].endswith(".js")],
        "interesting_urls": [
            u
            for u in urls
            if any(token in u.lower() for token in ("fet", "rend", "bilanc", "download", "zip", "csv", "api"))
        ],
        "html_quoted_strings": quoted_strings(html),
        "html_snippets": context_snippets(html),
        "fet_js": {
            "url": FET_JS,
            "status_code": js_response.status_code,
            "length": len(js),
            "sha256": hashlib.sha256(js.encode("utf-8")).hexdigest(),
            "quoted_strings": quoted_strings(js),
            "snippets": context_snippets(js),
        },
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
    for key, function in (("ckan", discover_ckan), ("fet_discovery", discover_page)):
        try:
            payload[key] = function(session)
        except Exception as exc:  # noqa: BLE001
            errors.append({"stage": key, "error": repr(exc)})
    payload["errors"] = errors
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audit scritto in {OUT}")
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
