#!/usr/bin/env python3
"""Fail closed when a Pages artifact or live site is missing core experiences."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

TOWNS = ("camaiore", "forte-dei-marmi", "massarosa", "pietrasanta", "seravezza", "stazzema", "viareggio")
STATIC_ROUTES = ("/stato-dati/", "/pnrr/", "/percorsi/")
PNRR_MARKERS = {
    "/pnrr/": ("data-page=\"pnrr\"", "Le 22 opere fisiche"),
    "/confronta/comunita/": ("pnrr-town-detail.js", "Investimenti e comunità"),
    "/comuni/massarosa/": ("pnrr-town-detail.js",),
}
REQUIRED_ASSETS = ("assets/pnrr-town-detail.js", "assets/pnrr-town-detail.css")


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_dist(root: Path) -> list[str]:
    failures: list[str] = []
    for route in STATIC_ROUTES:
        page = root / route.strip("/") / "index.html"
        require(page.is_file() and page.stat().st_size > 100, f"route non generata: {route}", failures)
    for route, markers in PNRR_MARKERS.items():
        page = root / route.strip("/") / "index.html"
        if not page.is_file():
            failures.append(f"route PNRR non generata: {route}")
            continue
        content = page.read_text(encoding="utf-8")
        for marker in markers:
            require(marker in content, f"marcatore assente in {route}: {marker}", failures)
    for slug in TOWNS:
        page = root / "comuni" / slug / "index.html"
        require(page.is_file(), f"scheda comunale non generata: /comuni/{slug}/", failures)
        if page.is_file():
            content = page.read_text(encoding="utf-8")
            require("pnrr-town-detail.js" in content, f"dettaglio PNRR assente in /comuni/{slug}/", failures)
    for asset in REQUIRED_ASSETS:
        require((root / asset).is_file(), f"asset richiesto non generato: {asset}", failures)
    if (root / "pnrr" / "index.html").is_file():
        content = (root / "pnrr" / "index.html").read_text(encoding="utf-8")
        require("pnrr-deep-dive.css" in content, "stile PNRR assente", failures)
    return failures


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "OsservatorioVersilia-PagesHealth/1.0"})
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def validate_live(base_url: str) -> list[str]:
    failures: list[str] = []
    base = base_url.rstrip("/")
    routes = set(STATIC_ROUTES) | set(PNRR_MARKERS) | {f"/comuni/{slug}/" for slug in TOWNS}
    for route in sorted(routes):
        try:
            content = fetch(base + route)
            markers = PNRR_MARKERS.get(route, ())
            for marker in markers:
                require(marker in content, f"marcatore live assente in {route}: {marker}", failures)
            if route in {f"/comuni/{slug}/" for slug in TOWNS}:
                require("pnrr-town-detail.js" in content, f"dettaglio PNRR live assente in {route}", failures)
        except (URLError, TimeoutError, RuntimeError, UnicodeDecodeError) as exc:
            failures.append(f"{route}: {exc}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dist", type=Path)
    group.add_argument("--base-url")
    args = parser.parse_args()
    failures = validate_dist(args.dist) if args.dist else validate_live(args.base_url)
    if failures:
        print("PUBLIC SITE VALIDATION FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Public site integrity PASS: Stato dati, PNRR, Percorsi e dettagli PNRR comunali/tematici presenti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
