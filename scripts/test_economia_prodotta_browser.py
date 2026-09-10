#!/usr/bin/env python3
"""Browser contract e screenshot review per Economia prodotta v1.34.0."""
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
    page.wait_for_timeout(300)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/economia-prodotta-browser")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    shots = Path(args.screenshots_dir).resolve()
    shots.mkdir(parents=True, exist_ok=True)
    report = {"checks": [], "consoleErrors": [], "pageErrors": []}

    with serve(directory) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
        page.on("console", lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        url = f"{base}/confronta/economia/?indicatore=businessTurnover"
        page.goto(url, wait_until="networkidle")
        wait_app(page)
        page.get_by_role("heading", name="Fatturato delle unità locali").wait_for(timeout=10_000)
        assert page.get_by_text("Economia prodotta", exact=True).count() >= 1
        assert page.locator(".comparison-bars .bar-row").count() >= 7
        assert page.locator(".economic-scope-control").count() == 1
        assert page.locator('[data-economic-scope="total"].active').count() == 1

        total_values = page.locator(".comparison-bars .bar-row strong").all_text_contents()[:7]
        page.locator('[data-economic-scope="industry"]').click()
        page.wait_for_timeout(350)
        assert "perimetro=industry" in page.url
        assert page.locator('[data-economic-scope="industry"].active').count() == 1
        industry_values = page.locator(".comparison-bars .bar-row strong").all_text_contents()[:7]
        assert total_values != industry_values, "Il selettore Industria non modifica i valori"
        report["checks"].append({"compareDesktop": "pass", "totalValues": total_values, "industryValues": industry_values})
        page.screenshot(path=str(shots / "economia-prodotta-confronto-desktop.png"), full_page=True)

        page.locator('[data-economic-scope="services"]').click()
        page.wait_for_timeout(350)
        assert "perimetro=services" in page.url
        assert page.locator('[data-economic-scope="services"].active').count() == 1
        services_values = page.locator(".comparison-bars .bar-row strong").all_text_contents()[:7]
        assert services_values != industry_values
        report["checks"].append({"servicesScope": "pass", "servicesValues": services_values})

        town_url = f"{base}/comuni/massarosa/?tema=economia&indicatore=labourProductivity"
        page.goto(town_url, wait_until="networkidle")
        wait_app(page)
        page.get_by_role("heading", name="Massarosa", exact=True).wait_for(timeout=10_000)
        assert page.get_by_text("Economia prodotta", exact=True).count() >= 1
        assert page.locator(".economic-scope-control").count() == 1
        page.locator('[data-economic-scope="industry"]').click()
        page.wait_for_timeout(350)
        assert "perimetro=industry" in page.url
        page.screenshot(path=str(shots / "economia-prodotta-massarosa-desktop.png"), full_page=True)
        report["checks"].append({"townDesktop": "pass"})

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("console", lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        mobile.goto(url, wait_until="networkidle")
        wait_app(mobile)
        mobile.get_by_role("heading", name="Fatturato delle unità locali").wait_for(timeout=10_000)
        assert mobile.locator(".economic-scope-control").count() == 1
        assert mobile.locator(".comparison-bars .bar-row").count() >= 7
        mobile.screenshot(path=str(shots / "economia-prodotta-confronto-mobile.png"), full_page=True)
        report["checks"].append({"compareMobile": "pass"})
        mobile.close()
        browser.close()

    # Gli errori JS sono bloccanti; errori rete non-console non vengono inclusi.
    if report["pageErrors"] or report["consoleErrors"]:
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))

    (shots / "browser-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS browser Economia prodotta: desktop, mobile, comune e 3 perimetri.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
