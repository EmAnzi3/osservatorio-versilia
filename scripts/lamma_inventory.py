#!/usr/bin/env python3
"""Discover LaMMA open-data climate packages and downloadable resources.

This is deliberately metadata-only: it proves that the 1 km products can be
resolved programmatically before adding raster processing to the POC.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://dati.lamma.toscana.it/api/3/action/package_search"
QUERIES = ["climatologia", "temperatura", "precipitazione"]


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/runtime/meteo-poc/lamma-inventory.json")
    args = parser.parse_args()

    packages: dict[str, dict] = {}
    for query in QUERIES:
        url = API + "?" + urllib.parse.urlencode({"q": query, "rows": 100})
        payload = request_json(url)
        if not payload.get("success"):
            raise RuntimeError(f"LaMMA CKAN search failed for {query}")
        for pkg in payload.get("result", {}).get("results", []):
            title = (pkg.get("title") or "").lower()
            notes = (pkg.get("notes") or "").lower()
            haystack = title + " " + notes
            if not any(word in haystack for word in ("climat", "temperatura", "precipit")):
                continue
            resources = []
            for r in pkg.get("resources", []):
                resources.append({
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "url": r.get("url"),
                    "last_modified": r.get("last_modified"),
                    "size": r.get("size"),
                    "license": pkg.get("license_title"),
                })
            packages[pkg.get("name") or pkg.get("id")] = {
                "id": pkg.get("id"),
                "name": pkg.get("name"),
                "title": pkg.get("title"),
                "notes": pkg.get("notes"),
                "license_title": pkg.get("license_title"),
                "resources": resources,
            }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    selected = sorted(packages.values(), key=lambda p: (p.get("title") or ""))
    out.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[lamma] packages found: {len(selected)}")
    for pkg in selected:
        print(f"[lamma] {pkg.get('name')} | {pkg.get('title')} | {pkg.get('license_title')}")
        for r in pkg.get("resources", [])[:5]:
            print(f"  - {r.get('name')} | {r.get('format')} | {r.get('url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
