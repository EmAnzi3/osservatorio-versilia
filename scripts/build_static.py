#!/usr/bin/env python3
"""Build a fully pre-rendered static version of Osservatorio Versilia.

The current application remains the source of truth for markup during this
migration phase. It is executed only at build time to write complete HTML into
``dist``. The browser bundle is still shipped for interaction, but no page is
blank when JavaScript is unavailable.
"""

from __future__ import annotations

import contextlib
import datetime as dt
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


def slugify(value: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


SITE_DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
INDICATOR_SLUGS = {
    metric_key: slugify(metric["meta"]["label"])
    for metric_key, metric in SITE_DATA["metrics"].items()
    if metric.get("dataStorage", {}).get("type") != "external-climate"
}
INDICATOR_ROUTES = [f"indicatori/{slug}/" for slug in INDICATOR_SLUGS.values()]
METRIC_KEY_BY_ROUTE = {
    f"indicatori/{slug}/": metric_key
    for metric_key, slug in INDICATOR_SLUGS.items()
}

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
    "sicurezza",
]
ROUTES = [
    "",
    *[f"comuni/{slug}/" for slug in TOWN_SLUGS],
    *[f"confronta/{slug}/" for slug in THEME_SLUGS],
    *INDICATOR_ROUTES,
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


def create_indicator_shells() -> None:
    """Crea i gusci delle pagine indicatore, poi completati dal prerender."""
    for metric_key, slug in INDICATOR_SLUGS.items():
        metric = SITE_DATA["metrics"][metric_key]
        meta = metric["meta"]
        title = f"{meta['label']} in Versilia · Osservatorio Versilia"
        description = (
            f"{meta['label']} nei sette comuni della Versilia: valori {meta['year']}, "
            "serie storiche disponibili, metodo e fonte ufficiale."
        )
        target = DIST / "indicatori" / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "<!doctype html>\n"
            '<html lang="it">\n<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"  <title>{html.escape(title)}</title>\n"
            f'  <meta name="description" content="{html.escape(description, quote=True)}">\n'
            f'  <meta property="og:title" content="{html.escape(title, quote=True)}">\n'
            f'  <meta property="og:description" content="{html.escape(description, quote=True)}">\n'
            '  <meta property="og:type" content="website">\n'
            '  <meta property="og:locale" content="it_IT">\n'
            '  <link rel="icon" href="../../favicon.svg" sizes="any">\n'
            '  <link rel="icon" href="../../favicon.svg" type="image/svg+xml">\n'
            '  <link rel="manifest" href="../../site.webmanifest">\n'
            '  <link rel="stylesheet" href="../../assets/original.css">\n'
            '  <link rel="stylesheet" href="../../assets/static.css">\n'
            '  <link rel="stylesheet" href="../../assets/fidelity.css">\n'
            '</head>\n'
            f'<body class="antialiased" data-page="indicator" data-theme="{html.escape(meta["theme"], quote=True)}" data-town="" data-metric="{html.escape(metric_key, quote=True)}">\n'
            '  <div id="site-header-mount"></div>\n'
            '  <div id="app"><div class="app-loading" role="status">Caricamento dei dati…</div></div>\n'
            '  <div id="site-footer-mount"></div>\n'
            '  <noscript><div class="app-error">Il sito richiede JavaScript per mostrare confronti, ricerca e schede comunali.</div></noscript>\n'
            '  <script src="../../assets/fidelity.js" defer></script>\n'
            '  <script src="../../assets/app.js" defer></script>\n'
            '</body>\n</html>\n',
            encoding="utf-8",
        )


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
        text = re.sub(r"(?:\.\./)*assets/ateco-detail\.css(?:\?v=[^\"]+)?", f"{assets}assets/ateco-detail.css", text)
        text = re.sub(r"(?:\.\./)*assets/(?:app|app-bundle)\.js(?:\?v=[^\"]+)?", f"{assets}assets/app-bundle.js", text)
        text = re.sub(r"(?:\.\./)*assets/fidelity\.js(?:\?v=[^\"]+)?", f"{assets}assets/fidelity.js", text)
        text = re.sub(r"(?:\.\./)*assets/ateco-detail\.js(?:\?v=[^\"]+)?", f"{assets}assets/ateco-detail.js", text)

        if "assets/fidelity.css" not in text:
            text = text.replace("</head>", f'  <link rel="stylesheet" href="{assets}assets/fidelity.css">\n</head>')
        if "assets/ateco-detail.css" not in text:
            text = text.replace("</head>", f'  <link rel="stylesheet" href="{assets}assets/ateco-detail.css">\n</head>')
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
        if "assets/ateco-detail.js" not in text:
            text = text.replace(
                "</body>",
                f'  <script src="{assets}assets/ateco-detail.js" defer></script>\n</body>',
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


def page_json_ld(route: str, data: dict, title: str, description: str) -> dict:
    common = {
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
            "@context": "https://schema.org",
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
        entity = {
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
        parent_name = "Comuni"
        parent_url = canonical_url("") + "#comuni"
    elif route.startswith("confronta/"):
        theme_key = route.split("/")[1]
        theme = data["themes"][theme_key]
        entity = {
            **common,
            "@type": "Dataset",
            "spatialCoverage": {"@type": "Place", "name": "Versilia, Toscana, Italia"},
            "variableMeasured": [data["metrics"][key]["meta"]["label"] for key in theme["metrics"]],
        }
        parent_name = "Temi"
        parent_url = canonical_url("") + "#temi"
    elif route.startswith("indicatori/"):
        metric_key = METRIC_KEY_BY_ROUTE[route]
        metric = data["metrics"][metric_key]
        meta = metric["meta"]
        years = sorted({
            str(year)
            for row in metric["rows"]
            for year in ((row.get("series") or {}).get("years") or [])
        })
        temporal_coverage = f"{years[0]}/{years[-1]}" if years else str(meta["year"])
        entity = {
            **common,
            "@type": "Dataset",
            "identifier": metric_key,
            "dateModified": italian_date_iso(data.get("updated", "")),
            "spatialCoverage": {"@type": "Place", "name": "Versilia, Toscana, Italia"},
            "temporalCoverage": temporal_coverage,
            "variableMeasured": {
                "@type": "PropertyValue",
                "name": meta["label"],
                "unitText": meta["unit"],
            },
            "isBasedOn": metric["sourceUrl"],
            "measurementTechnique": metric.get("method", {}).get("formula", ""),
        }
        parent_name = data["themes"][meta["theme"]]["label"]
        parent_url = canonical_url(f"confronta/{meta['theme']}/")
    else:
        entity = {**common, "@type": "WebPage"}
        parent_name = "Informazioni"
        parent_url = canonical_url("")

    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Osservatorio Versilia",
                "item": canonical_url(""),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": parent_name,
                "item": parent_url,
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": canonical_url(route),
            },
        ],
    }
    return {"@context": "https://schema.org", "@graph": [entity, breadcrumb]}


def italian_date_iso(value: str) -> str:
    months = {
        "gennaio": 1,
        "febbraio": 2,
        "marzo": 3,
        "aprile": 4,
        "maggio": 5,
        "giugno": 6,
        "luglio": 7,
        "agosto": 8,
        "settembre": 9,
        "ottobre": 10,
        "novembre": 11,
        "dicembre": 12,
    }
    match = re.fullmatch(r"\s*(\d{1,2})\s+([a-zà]+)\s+(\d{4})\s*", value.lower())
    if not match or match.group(2) not in months:
        return dt.date.today().isoformat()
    return dt.date(int(match.group(3)), months[match.group(2)], int(match.group(1))).isoformat()


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
            page.wait_for_timeout(350)
            page.evaluate("document.body.dataset.prerendered = 'true'")
            document = page.evaluate("'<!doctype html>\\n' + document.documentElement.outerHTML")
            route_file(route).write_text(inject_metadata(document, route, data), encoding="utf-8")
        browser.close()


def write_sitemap() -> None:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    last_modified = italian_date_iso(data.get("updated", ""))
    urls = [canonical_url(route) for route in ROUTES if route != "404.html"]
    content = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/sitemap/0.9">']
    content.extend(
        f"  <url><loc>{html.escape(url)}</loc><lastmod>{last_modified}</lastmod></url>"
        for url in urls
    )
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
    create_indicator_shells()
    bundle_application()
    prepare_shells()
    prerender()
    write_sitemap()
    write_manifest()
    print(f"Build statico completato: {DIST}")


if __name__ == "__main__":
    main()
