#!/usr/bin/env python3
"""Browser contract e screenshot review per Economia prodotta v1.34.0."""
from __future__ import annotations

import argparse
import contextlib
import json
import math
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
    page.wait_for_timeout(500)


def chart_values(page):
    return page.locator(".comparison-bars .bar-row strong").all_text_contents()[:7]


def chart_state(page):
    return page.locator(".comparison-bars .bar-row").evaluate_all(
        """rows => rows.slice(0, 7).map(row => ({
          town: row.querySelector('.bar-town')?.textContent.trim(),
          value: row.querySelector('strong')?.textContent.trim(),
          width: Number.parseFloat(row.querySelector('.comparison-stem, .bar-fill')?.style.width || '0'),
          reference: Number.parseFloat(row.querySelector('.comparison-reference')?.style.left || '0')
        }))"""
    )


def expected_scope_rows(metric, scope):
    rows = sorted(
        metric["rows"],
        key=lambda row: row["economicScopes"][scope]["value"],
        reverse=True,
    )
    return [
        {
            "town": row["town"],
            "value": row["economicScopes"][scope]["formatted"],
            "raw": row["economicScopes"][scope]["value"],
        }
        for row in rows
    ]


def nice_outer_bound(value):
    if not math.isfinite(value) or value == 0:
        return 1
    magnitude = 10 ** math.floor(math.log10(abs(value)))
    normalized = abs(value) / magnitude
    stop = next(candidate for candidate in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10) if normalized <= candidate)
    return stop * magnitude


def assert_chart_recomputed(actual, expected, aggregate_value):
    assert [(row["town"], row["value"]) for row in actual] == [
        (row["town"], row["value"]) for row in expected
    ], "Valori o ordinamento non ricalcolati dal renderer canonico"
    maximum = nice_outer_bound(max(max(row["raw"] for row in expected), aggregate_value) * 1.06)
    expected_reference = aggregate_value / maximum * 100
    for row, expected_row in zip(actual, expected, strict=True):
        expected_width = expected_row["raw"] / maximum * 100
        assert abs(row["width"] - expected_width) < 0.15, (
            f"Scala del grafico non ricalcolata sul perimetro: {row} / {expected_width}"
        )
        assert abs(row["reference"] - expected_reference) < 0.15, "Riferimento Versilia non ricalcolato sulla scala"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/economia-prodotta-browser")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    shots = Path(args.screenshots_dir).resolve()
    shots.mkdir(parents=True, exist_ok=True)
    site_data = json.loads((directory / "data" / "site-data.json").read_text(encoding="utf-8"))
    turnover_metric = site_data["metrics"]["businessTurnover"]
    productivity_metric = site_data["metrics"]["labourProductivity"]
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
        assert page.locator("#compare-bars > .economic-scope-control").count() == 0
        assert page.locator("#compare-bars .topic-bars > .economic-scope-control").count() == 1, "Selettore non locale al pannello grafico"
        scope_select = page.locator('#compare-bars select[data-economic-scope]')
        assert scope_select.input_value() == "total"
        assert page.locator('button[data-economic-scope]').count() == 0, "I tre pulsanti Frame SBS sono ancora presenti"
        total_state = chart_state(page)
        assert_chart_recomputed(total_state, expected_scope_rows(turnover_metric, "total"), turnover_metric["aggregate"]["economicScopes"]["total"]["value"])
        page.screenshot(path=str(shots / "economia-prodotta-confronto-totale-desktop.png"), full_page=True)

        total_values = chart_values(page)
        scope_select.select_option("industry")
        page.wait_for_timeout(400)
        assert "perimetro=industry" in page.url
        industry_values = chart_values(page)
        industry_state = chart_state(page)
        assert_chart_recomputed(industry_state, expected_scope_rows(turnover_metric, "industry"), turnover_metric["aggregate"]["economicScopes"]["industry"]["value"])
        assert total_values != industry_values, "Il selettore Industria non modifica i valori"
        assert turnover_metric["aggregate"]["economicScopes"]["industry"]["formatted"] in page.locator("#compare-definition").inner_text(), "Aggregato Versilia Industria non ricalcolato"
        assert not page.locator("#compare-benchmark").inner_text().strip(), "Benchmark totale visibile nel confronto Industria"
        page.screenshot(path=str(shots / "economia-prodotta-confronto-industria-desktop.png"), full_page=True)

        page.locator('#compare-bars select[data-economic-scope]').select_option("services")
        page.wait_for_timeout(400)
        services_values = chart_values(page)
        services_state = chart_state(page)
        assert_chart_recomputed(services_state, expected_scope_rows(turnover_metric, "services"), turnover_metric["aggregate"]["economicScopes"]["services"]["value"])
        assert "perimetro=services" in page.url
        assert services_values != industry_values and services_values != total_values
        assert turnover_metric["aggregate"]["economicScopes"]["services"]["formatted"] in page.locator("#compare-definition").inner_text(), "Aggregato Versilia Servizi non ricalcolato"
        assert not page.locator("#compare-benchmark").inner_text().strip(), "Benchmark totale visibile nel confronto Servizi"
        report["checks"].append({
            "compareScopePlacement": "pass",
            "canonicalScaleAndOrder": "pass",
            "versiliaAggregate": "pass",
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
        assert page.locator("#town-topic .history-panel select[data-economic-scope]").input_value() == "total"
        page.locator('#town-topic .history-panel [data-view-mode="history"]').click()
        page.wait_for_timeout(250)
        total_history = page.locator('#town-topic .history-panel [data-view-pane="history"] svg').inner_html()
        page.locator('#town-topic .history-panel [data-view-mode="current"]').click()
        town_total = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert page.locator("main.town-profile .town-benchmark").count() == 1
        page.locator('#town-topic .history-panel select[data-economic-scope]').select_option("industry")
        page.wait_for_timeout(500)
        town_industry = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert town_total != town_industry, "Il perimetro Industria non aggiorna il valore comunale"
        assert "perimetro=industry" in page.url
        assert page.locator("main.town-profile .town-benchmark").count() == 0, "Benchmark Toscana/Italia visibile in Industria"
        assert page.locator("#town-topic .history-panel .economic-scope-control").count() == 1, "ux-history ha rimosso il selettore Frame"
        industry_expected = expected_scope_rows(productivity_metric, "industry")
        current_order = page.locator('#town-topic .history-panel [data-view-pane="current"] .ux-bar-town').all_text_contents()
        assert current_order == [row["town"] for row in industry_expected], "Ordine comunale Industria non ricalcolato"
        versilia_position_text = page.locator("#town-topic .versilia-position").inner_text().replace("\xa0", " ")
        assert productivity_metric["aggregate"]["economicScopes"]["industry"]["formatted"] in versilia_position_text, "Media Versilia Industria non ricalcolata"
        page.locator('#town-topic .history-panel [data-view-mode="history"]').click()
        page.wait_for_timeout(250)
        assert page.locator('#town-topic .history-panel [data-view-pane="history"] .ux-history-card').count() == 1, "Storico comunale Frame non renderizzato"
        industry_history = page.locator('#town-topic .history-panel [data-view-pane="history"] svg').inner_html()
        assert total_history != industry_history, "Lo storico non è stato ricalcolato sul perimetro Industria"
        assert page.locator('#town-topic .history-panel select[data-economic-scope]').input_value() == "industry", "Perimetro Industria perso nello storico"
        page.locator('#town-topic .history-panel [data-view-mode="current"]').click()
        page.wait_for_timeout(200)
        page.screenshot(path=str(shots / "economia-prodotta-massarosa-industria-desktop.png"), full_page=True)
        page.locator('#town-topic .history-panel select[data-economic-scope]').select_option("services")
        page.wait_for_timeout(500)
        town_services = page.locator("#town-topic .town-metric-primary > strong").inner_text()
        assert town_services not in (town_total, town_industry)
        report["checks"].append({
            "townScopePlacement": "pass",
            "townTotal": town_total,
            "townIndustry": town_industry,
            "townServices": town_services,
            "townBenchmarkScopeCoherence": "pass",
            "townHistoryScopeCoherence": "pass",
            "townRankAndVersiliaScopeCoherence": "pass",
        })

        indicator_url = f"{base}/indicatori/fatturato-delle-unita-locali/?perimetro=industry"
        page.goto(indicator_url, wait_until="networkidle")
        wait_app(page)
        assert page.locator(".indicator-current > .economic-scope-control").count() == 1, "Selettore assente dalla scheda indicatore"
        assert page.locator('.indicator-current select[data-economic-scope]').input_value() == "industry"
        assert page.locator('button[data-economic-scope]').count() == 0
        assert not page.locator(".indicator-benchmark").inner_text().strip(), "Benchmark totale visibile nella scheda indicatore Industria"
        indicator_industry = page.locator(".indicator-current-layout").inner_text()
        page.locator('.indicator-current select[data-economic-scope]').select_option("services")
        page.wait_for_timeout(400)
        assert page.locator('.indicator-current select[data-economic-scope]').input_value() == "services"
        assert page.locator(".indicator-current-layout").inner_text() != indicator_industry, "Scheda indicatore non ricalcolata su Servizi"
        report["checks"].append({"indicatorScopePlacement": "pass"})

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("console", lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        mobile.goto(url, wait_until="networkidle")
        wait_app(mobile)
        mobile.get_by_role("heading", name="Fatturato delle unità locali").wait_for(timeout=10_000)
        assert mobile.locator("#compare-bars .economic-scope-control").count() == 1
        assert mobile.locator("#compare-bars select[data-economic-scope]").count() == 1
        assert mobile.locator("#compare-bars select[data-economic-scope]").bounding_box()["width"] <= 390
        assert mobile.locator(".comparison-bars .bar-row").count() >= 7
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
    print("PASS browser Economia prodotta: selettore locale, storico coerente, isolamento non-Frame, desktop/mobile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
