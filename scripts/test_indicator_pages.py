#!/usr/bin/env python3
"""Verifica le pagine canoniche dei 106 indicatori e la loro navigazione."""

from __future__ import annotations

import contextlib
import json
import os
import re
import socket
import threading
import unicodedata
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PUBLIC_BASE = "https://osservatorioversilia.it/"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
    old = Path.cwd()
    os.chdir(directory)
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        httpd = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
    finally:
        os.chdir(old)


def extract_json_ld(document: str) -> dict:
    match = re.search(
        r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
        document,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert match, "JSON-LD assente"
    return json.loads(match.group(1))


def static_checks() -> None:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    assert len(data["metrics"]) == 106

    paths: list[Path] = []
    for metric_key, metric in data["metrics"].items():
        slug = slugify(metric["meta"]["label"])
        path = DIST / "indicatori" / slug / "index.html"
        paths.append(path)
        assert path.exists(), f"Pagina indicatore mancante: {metric_key}"
        document = path.read_text(encoding="utf-8")
        canonical = f'{PUBLIC_BASE}indicatori/{slug}/'
        assert f'<link rel="canonical" href="{canonical}">' in document
        assert metric["meta"]["label"] in document
        assert '<main class="inner-page indicator-page"' in document
        assert 'assets/indicator-pages.css' in document
        assert 'Nessuna graduatoria' in document

        structured = extract_json_ld(document)
        graph = structured.get("@graph", [])
        dataset = next((item for item in graph if item.get("@type") == "Dataset"), None)
        breadcrumb = next((item for item in graph if item.get("@type") == "BreadcrumbList"), None)
        assert dataset and dataset.get("identifier") == metric_key
        assert dataset.get("isBasedOn") == metric["sourceUrl"]
        assert breadcrumb and len(breadcrumb.get("itemListElement", [])) == 3

    assert len(paths) == len(set(paths)) == 106, "Slug indicatore duplicato"

    sitemap = ET.parse(DIST / "sitemap.xml")
    namespace = {"s": "http://www.sitemaps.org/sitemap/0.9"}
    urls = sitemap.findall("s:url", namespace)
    locations = [item.findtext("s:loc", namespaces=namespace) for item in urls]
    assert len(locations) == len(set(locations)) == 126, f"URL sitemap inattese: {len(locations)}"
    assert all(item.findtext("s:lastmod", namespaces=namespace) for item in urls)
    assert sum("/indicatori/" in (url or "") for url in locations) == 106


def browser_checks() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1360, "height": 920})

        page.goto(base + "indicatori/popolazione-residente/", wait_until="networkidle")
        page.wait_for_selector(".indicator-page")
        assert page.locator("h1").first.inner_text() == "Popolazione residente"
        assert page.locator(".indicator-values-table tbody tr").count() == 7
        assert page.locator(".indicator-history-table tbody tr").count() == 7
        assert page.locator(".bar-rank").count() == 0
        assert "Politica fonte" not in page.locator("body").inner_text()
        assert page.locator(".indicator-governance-grid").count() == 1

        page.goto(base + "indicatori/persone-con-almeno-una-patologia-cronica/", wait_until="networkidle")
        page.wait_for_selector(".indicator-page")
        assert page.locator(".indicator-history-empty").count() == 1
        assert page.locator(".benchmark-grid").count() == 1

        page.goto(base, wait_until="networkidle")
        page.locator(".global-search-trigger").click()
        page.locator(".search-field input").fill("disoccupazione")
        result = page.locator('[data-search-result][href*="/indicatori/tasso-di-disoccupazione/"]')
        assert result.count() == 1

        page.goto(base + "confronta/demografia/?indicatore=population", wait_until="networkidle")
        assert page.locator('.data-actions a[href*="/indicatori/popolazione-residente/"]').count() == 1
        page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
        assert page.locator('.town-data-actions a[href*="/indicatori/popolazione-residente/"]').count() == 1

        no_js = browser.new_context(java_script_enabled=False)
        no_js_page = no_js.new_page()
        no_js_page.goto(base + "indicatori/popolazione-residente/", wait_until="networkidle")
        assert no_js_page.locator("h1").first.inner_text() == "Popolazione residente"
        assert no_js_page.locator(".indicator-values-table tbody tr").count() == 7
        no_js.close()
        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("Pagine indicatore verificate: 106 URL canoniche, sitemap, governance e navigazione.")


if __name__ == "__main__":
    main()
