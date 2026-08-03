#!/usr/bin/env python3
"""Build a fully pre-rendered static version of Osservatorio Versilia.

The current application remains the source of truth for markup during this
migration phase. It is executed only at build time to write complete HTML into
``dist``. The browser bundle is still shipped for interaction, but no page is
blank when JavaScript is unavailable.
"""

from __future__ import annotations

import contextlib
import html
import json
import os
import re
import shutil
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BASE_URL = "https://emanzi3.github.io/osservatorio-versilia/"

TOWN_SLUGS = [
    "camaiore",
    "forte-dei-marmi",
    "massarosa",
    "pietrasanta",
    "seravezza",
    "stazzema",
    "viareggio",
]
THEME_SLUGS = [
    "abitare",
    "ambiente",
    "comunita",
    "demografia",
    "economia",
    "istruzione",
    "lavoro",
    "mobilita",
    "salute",
]
ROUTES = [
    "",
    *[f"comuni/{slug}/" for slug in TOWN_SLUGS],
    *[f"confronta/{slug}/" for slug in THEME_SLUGS],
    "progetto/",
    "segnala/",
    "404.html",
]

COPY_ENTRIES = [
    ".nojekyll",
    "404.html",
    "assets",
    "comuni",
    "confronta",
    "crests",
    "data",
    "favicon.svg",
    "images",
    "index.html",
    "progetto",
    "robots.txt",
    "segnala",
    "site.webmanifest",
]


def copy_source_tree() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for name in COPY_ENTRIES:
        source = ROOT / name
        target = DIST / name
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def bundle_application() -> None:
    parts = sorted((ROOT / "assets" / "app-parts").glob("[0-9][0-9].txt"))
    if len(parts) != 7:
        raise RuntimeError(f"Attesi 7 moduli applicativi, trovati {len(parts)}")
    bundle = "".join(path.read_text(encoding="utf-8") for path in parts)
    (DIST / "assets" / "app-bundle.js").write_text(bundle, encoding="utf-8")


def relative_asset_prefix(path: Path) -> str:
    return os.path.relpath(DIST, path.parent).replace(os.sep, "/")


def prepare_shells() -> None:
    for path in DIST.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        prefix = relative_asset_prefix(path)
        assets = "" if prefix == "." else f"{prefix}/"

        # Remove migration-only runtime patches. The built site uses local files.
        text = re.sub(
            r"\s*<script>\s*\(\(\) => \{\s*const correctHero.*?</script>",
            "",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(r"\s*<script[^>]*data-ov-fidelity[^>]*>.*?</script>", "", text, flags=re.DOTALL)

        # Normalize stylesheets and scripts for the static build.
        text = re.sub(r"(?:\.\./)*assets/original\.css(?:\?v=[^\"]+)?", f"{assets}assets/original.css", text)
        text = re.sub(r"(?:\.\./)*assets/static\.css(?:\?v=[^\"]+)?", f"{assets}assets/static.css", text)
        text = re.sub(r"(?:\.\./)*assets/fidelity\.css(?:\?v=[^\"]+)?", f"{assets}assets/fidelity.css", text)
        text = re.sub(r"(?:\.\./)*assets/(?:app|app-bundle)\.js(?:\?v=[^\"]+)?", f"{assets}assets/app-bundle.js", text)
        text = re.sub(r"(?:\.\./)*assets/fidelity\.js(?:\?v=[^\"]+)?", f"{assets}assets/fidelity.js", text)

        if "assets/fidelity.css" not in text:
            text = text.replace("</head>", f'  <link rel="stylesheet" href="{assets}assets/fidelity.css">\n</head>')
        if "assets/fidelity.js" not in text:
            text = text.replace(
                "</body>",
                f'  <script src="{assets}assets/fidelity.js" defer></script>\n</body>',
            )
        if "assets/app-bundle.js" not in text:
            text = text.replace(
                "</body>",
                f'  <script src="{assets}assets/app-bundle.js" defer></script>\n</body>',
            )

        path.write_text(text, encoding="utf-8")


def route_file(route: str) -> Path:
    if route == "":
        return DIST / "index.html"
    if route.endswith("/"):
        return DIST / route / "index.html"
    return DIST / route


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def local_server(directory: Path) -> Iterable[str]:
    old_cwd = Path.cwd()
    os.chdir(directory)
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            server.shutdown()
            thread.join(timeout=5)
    finally:
        os.chdir(old_cwd)


def canonical_url(route: str) -> str:
    return BASE_URL + route


def slugify(value: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def page_json_ld(route: str, data: dict, title: str, description: str) -> dict:
    common = {
        "@context": "https://schema.org",
        "url": canonical_url(route),
        "name": title,
        "description": description,
        "inLanguage": "it-IT",
        "isAccessibleForFree": True,
        "creator": {"@type": "Person", "name": "Emanuele Anzilotti"},
        "publisher": {"@type": "Person", "name": "Emanuele Anzilotti"},
    }
    if route == "":
        return {
            **common,
            "@type": "DataCatalog",
            "spatialCoverage": {"@type": "Place", "name": "Versilia, Toscana, Italia"},
            "dataset": [
                {
                    "@type": "Dataset",
                    "name": f"Indicatori del Comune di {town['name']}",
                    "url": canonical_url(f"comuni/{slugify(town['name'])}/"),
                }
                for town in data["towns"]
            ],
        }
    if route.startswith("comuni/"):
        slug = route.split("/")[1]
        town = next(item for item in data["towns"] if slugify(item["name"]) == slug)
        return {
            **common,
            "@type": "Dataset",
            "spatialCoverage": {"@type": "AdministrativeArea", "name": town["name"]},
            "temporalCoverage": "2019/2026",
            "variableMeasured": [
                data["metrics"][key]["meta"]["label"]
                for theme in data["themes"].values()
                for key in theme["metrics"]
                if key in data["metrics"]
            ],
        }
    if route.startswith("confronta/"):
        theme_key = route.split("/")[1]
        theme = data["themes"][theme_key]
        return {
            **common,
            "@type": "Dataset",
            "spatialCoverage": {"@type": "Place", "name": "Versilia, Toscana, Italia"},
            "variableMeasured": [data["metrics"][key]["meta"]["label"] for key in theme["metrics"]],
        }
    return {**common, "@type": "WebPage"}


def inject_metadata(document: str, route: str, data: dict) -> str:
    title_match = re.search(r"<title>(.*?)</title>", document, re.DOTALL | re.IGNORECASE)
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', document, re.IGNORECASE)
    title = html.unescape(title_match.group(1).strip()) if title_match else "Osservatorio Versilia"
    description = html.unescape(desc_match.group(1).strip()) if desc_match else "Dati pubblici dei comuni della Versilia."
    canonical = canonical_url(route)
    json_ld = json.dumps(page_json_ld(route, data, title, description), ensure_ascii=False, separators=(",", ":"))

    document = re.sub(r"\s*<link\s+rel=\"canonical\"[^>]*>", "", document, flags=re.IGNORECASE)
    document = re.sub(r"\s*<script\s+type=\"application/ld\+json\"[^>]*>.*?</script>", "", document, flags=re.DOTALL | re.IGNORECASE)
    metadata = (
        f'\n  <link rel="canonical" href="{html.escape(canonical, quote=True)}">'
        f'\n  <script type="application/ld+json">{json_ld}</script>\n'
    )
    document = document.replace("</head>", metadata + "</head>")
    document = document.replace("<body ", '<body data-prerendered="true" ', 1)
    return document


def prerender() -> None:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    with local_server(DIST) as server_url, sync_playwright() as playwright:
        chromium_path = os.environ.get("CHROMIUM_PATH")
        launch_args = {"headless": True}
        if chromium_path:
            launch_args["executable_path"] = chromium_path
        browser = playwright.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        for route in ROUTES:
            page.goto(server_url + route, wait_until="networkidle")
            page.wait_for_selector("#app main", timeout=30_000)
            page.wait_for_timeout(150)
            page.evaluate("document.body.dataset.prerendered = 'true'")
            document = page.evaluate("'<!doctype html>\\n' + document.documentElement.outerHTML")
            route_file(route).write_text(inject_metadata(document, route, data), encoding="utf-8")
        browser.close()


def write_sitemap() -> None:
    urls = [canonical_url(route) for route in ROUTES if route != "404.html"]
    content = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    content.extend(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    content.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(content) + "\n", encoding="utf-8")

    robots_path = DIST / "robots.txt"
    robots = robots_path.read_text(encoding="utf-8") if robots_path.exists() else "User-agent: *\nAllow: /\n"
    robots = re.sub(r"(?im)^Sitemap:.*$", "", robots).rstrip()
    robots += f"\nSitemap: {BASE_URL}sitemap.xml\n"
    robots_path.write_text(robots, encoding="utf-8")


def write_manifest() -> None:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    manifest = {
        "dataVersion": data["version"],
        "updated": data["updated"],
        "pages": len(ROUTES),
        "preRendered": True,
        "deployment": "disabled-on-refactor-branch",
    }
    (DIST / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    copy_source_tree()
    bundle_application()
    prepare_shells()
    prerender()
    write_sitemap()
    write_manifest()
    print(f"Build statico completato: {DIST}")


if __name__ == "__main__":
    main()
