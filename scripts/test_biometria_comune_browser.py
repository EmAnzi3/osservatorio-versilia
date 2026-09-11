#!/usr/bin/env python3
"""Browser contract e screenshot review per Biometria v1.35.0."""
from __future__ import annotations

import argparse
import contextlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


@contextlib.contextmanager
def serve(directory: Path):
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(directory), **kwargs)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


def wait_app(page):
    page.wait_for_selector("#app main", timeout=20_000)
    page.wait_for_timeout(450)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/biometria-comune-browser")
    args = parser.parse_args()
    directory = Path(args.directory).resolve()
    shots = Path(args.screenshots_dir).resolve()
    shots.mkdir(parents=True, exist_ok=True)

    site = json.loads((directory / "data" / "site-data.json").read_text(encoding="utf-8"))
    assert site["release_version"] == "1.35.0"
    assert site["themes"]["ambiente"]["sections"][0]["key"] == "profilo-territoriale"
    for key in ("municipalSurface", "populationDensity", "altitudeProfile"):
        assert key in site["metrics"]

    report = {"checks": [], "consoleErrors": [], "pageErrors": []}
    with serve(directory) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on("console", lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        town_url = f"{base}/comuni/massarosa/?tema=ambiente&indicatore=altitudeProfile"
        page.goto(town_url, wait_until="networkidle")
        wait_app(page)
        assert page.locator("main.town-profile").count() == 1
        assert page.locator("#site-header-mount").inner_text().strip()
        assert page.locator("#site-footer-mount").inner_text().strip()
        page.get_by_role("heading", name="Massarosa", exact=True).wait_for(timeout=10_000)
        assert page.get_by_text("Profilo fisico del territorio", exact=True).count() >= 1
        assert page.locator("#town-topic .composite-stack .composite-segment").count() == 8
        primary = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert "11,4%" in primary, primary
        detail = page.locator("#town-topic .composite-town-detail").first.inner_text()
        for label in ("0–299 m", "300–599 m", "600–899 m", "900–1.199 m"):
            assert label in detail
        page.screenshot(path=str(shots / "massarosa-profilo-altimetrico-desktop.png"), full_page=True)

        # Le metriche v1.35 usano le route canoniche della scheda comunale. Qui le
        # verifichiamo tramite deep link, senza dipendere dal markup interno dei card
        # switcher (che appartiene al renderer condiviso e non alla feature Biometria).
        surface_url = f"{base}/comuni/massarosa/?tema=ambiente&indicatore=municipalSurface"
        page.goto(surface_url, wait_until="networkidle")
        wait_app(page)
        assert "68,59 km²" in page.locator("#town-topic .town-metric-primary > strong").inner_text()
        density_url = f"{base}/comuni/massarosa/?tema=ambiente&indicatore=populationDensity"
        page.goto(density_url, wait_until="networkidle")
        wait_app(page)
        assert "ab./km²" in page.locator("#town-topic .town-metric-primary > strong").inner_text()
        report["checks"].append({"townCanonicalShell": "pass", "townAltitudeBands": 8, "townUnits": "pass"})

        compare_url = f"{base}/confronta/ambiente/?indicatore=altitudeProfile"
        page.goto(compare_url, wait_until="networkidle")
        wait_app(page)
        assert page.locator("main.inner-page").count() == 1
        assert page.locator(".topic-hero").count() == 1
        assert page.get_by_text("Profilo fisico del territorio", exact=True).count() >= 1
        assert page.locator(".composite-distribution-row").count() == 7
        assert page.locator(".composite-distribution-row .composite-stack").count() == 7
        page.screenshot(path=str(shots / "confronto-profilo-altimetrico-desktop.png"), full_page=True)
        report["checks"].append({"compareCanonicalRenderer": "pass", "townCount": 7})

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.on("console", lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        mobile.goto(town_url, wait_until="networkidle")
        wait_app(mobile)
        assert mobile.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1")
        assert mobile.locator("#site-header-mount").inner_text().strip()
        assert mobile.locator("#site-footer-mount").inner_text().strip()
        mobile.screenshot(path=str(shots / "massarosa-profilo-altimetrico-mobile.png"), full_page=True)
        report["checks"].append({"mobileNoOverflow": "pass"})
        mobile.close()
        browser.close()

    if report["consoleErrors"] or report["pageErrors"]:
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))
    (shots / "browser-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS browser Biometria: shell main, renderer canonici, desktop/mobile, nessun overflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
