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
    page.wait_for_timeout(350)


def chart_values(page):
    return page.locator("#compare-bars .comparison-bars .bar-row strong").all_text_contents()[:7]


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
        assert page.locator("#compare-bars .comparison-bars .bar-row").count() >= 7
        assert page.locator(".topic-controls .economic-scope-control").count() == 0, "Il perimetro è ancora nel catalogo indicatori"
        assert page.locator("#compare-bars .economic-scope-control").count() == 1, "Selettore Frame SBS assente dal pannello grafico"
        assert page.locator('#compare-bars [data-economic-scope="total"].active').count() == 1

        total_values = chart_values(page)
        page.screenshot(path=str(shots / "economia-prodotta-confronto-totale-desktop.png"), full_page=True)

        page.locator('#compare-bars [data-economic-scope="industry"]').click()
        page.wait_for_timeout(400)
        assert "perimetro=industry" in page.url
        assert page.locator('#compare-bars [data-economic-scope="industry"].active').count() == 1
        industry_values = chart_values(page)
        assert total_values != industry_values, "Il selettore Industria non modifica il solo indicatore attivo"
        assert page.locator("#compare-benchmark .benchmark-section").count() == 0, "Benchmark totale visibile nel confronto Industria"
        page.screenshot(path=str(shots / "economia-prodotta-confronto-industria-desktop.png"), full_page=True)

        page.locator('#compare-bars [data-economic-scope="services"]').click()
        page.wait_for_timeout(400)
        services_values = chart_values(page)
        assert services_values != industry_values
        assert services_values != total_values
        assert page.locator("#compare-benchmark .benchmark-section").count() == 0, "Benchmark totale visibile nel confronto Servizi"
        report["checks"].append({
            "compareScopePlacement": "pass",
            "totalValues": total_values,
            "industryValues": industry_values,
            "servicesValues": services_values,
        })

        clean_non_frame = f"{base}/confronta/economia/?indicatore=localUnits"
        page.goto(clean_non_frame, wait_until="networkidle")
        wait_app(page)
        clean_values = chart_values(page)
        assert page.locator(".economic-scope-control").count() == 0
        page.goto(clean_non_frame + "&perimetro=industry", wait_until="networkidle")
        wait_app(page)
        stray_values = chart_values(page)
        assert clean_values == stray_values, "Il perimetro Frame altera un indicatore non Frame"
        assert "perimetro=" not in page.url, "Parametro perimetro non rimosso su indicatore non Frame"
        assert page.locator(".economic-scope-control").count() == 0
        report["checks"].append({"nonFrameIsolation": "pass", "metric": "localUnits"})

        town_url = f"{base}/comuni/massarosa/?tema=economia&indicatore=labourProductivity"
        page.goto(town_url, wait_until="networkidle")
        wait_app(page)
        page.get_by_role("heading", name="Massarosa", exact=True).wait_for(timeout=10_000)
        assert page.get_by_text("Economia prodotta", exact=True).count() >= 1
        assert page.locator("#town-topic > .economic-scope-control").count() == 0
        assert page.locator("#town-topic .history-panel .economic-scope-control").count() == 1, "Selettore assente dal grafico comunale"
        town_total = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert page.locator("main.town-profile .town-benchmark").count() == 1
        page.locator('#town-topic .history-panel [data-economic-scope="industry"]').click()
        page.wait_for_timeout(400)
        town_industry = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert town_total != town_industry, "Il perimetro Industria non aggiorna il valore comunale"
        assert "perimetro=industry" in page.url
        assert page.locator("main.town-profile .town-benchmark").count() == 0, "Benchmark Toscana/Italia visibile in Industria"
        page.screenshot(path=str(shots / "economia-prodotta-massarosa-industria-desktop.png"), full_page=True)
        page.locator('#town-topic .history-panel [data-economic-scope="services"]').click()
        page.wait_for_timeout(400)
        town_services = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert town_services not in (town_total, town_industry)
        report["checks"].append({
            "townScopePlacement": "pass",
            "townTotal": town_total,
            "townIndustry": town_industry,
            "townServices": town_services,
            "townBenchmarkScopeCoherence": "pass",
        })

        indicator_url = f"{base}/indicatori/fatturato-delle-unita-locali/?perimetro=industry"
        page.goto(indicator_url, wait_until="networkidle")
        wait_app(page)
        assert page.locator(".indicator-current .economic-scope-control").count() == 1
        assert page.locator('.indicator-current [data-economic-scope="industry"].active').count() == 1
        assert page.locator(".indicator-benchmark .benchmark-section").count() == 0
        report["checks"].append({"indicatorScopePlacement": "pass"})

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("console", lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        mobile.goto(url, wait_until="networkidle")
        wait_app(mobile)
        mobile.get_by_role("heading", name="Fatturato delle unità locali").wait_for(timeout=10_000)
        assert mobile.locator(".topic-controls .economic-scope-control").count() == 0
        assert mobile.locator("#compare-bars .economic-scope-control").count() == 1
        assert mobile.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), "Overflow orizzontale mobile"
        mobile.screenshot(path=str(shots / "economia-prodotta-confronto-mobile.png"), full_page=True)
        report["checks"].append({"compareMobile": "pass"})
        mobile.close()
        browser.close()

    if report["pageErrors"] or report["consoleErrors"]:
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))

    (shots / "browser-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS browser Economia prodotta: selettore locale al grafico, isolamento non-Frame, comune, indicatore e mobile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
