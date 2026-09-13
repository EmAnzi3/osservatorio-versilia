#!/usr/bin/env python3
"""Browser QA desktop/mobile per Bilanci v1.39.0 e benchmark pro capite globale."""
from __future__ import annotations

import argparse
import contextlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


METRICS = (
    ("fcdePerResident", "Fondo crediti di dubbia esigibilità per residente", "FCDE", 2019),
    ("yearEndCashFundPerResident", "Fondo di cassa al 31 dicembre per residente", "Fondo cassa finale", 2019),
    (
        "generalAdministrationMissionExpenditurePerResident",
        "Spesa impegnata per servizi istituzionali e generali per residente",
        "Servizi generali",
        2019,
    ),
    (
        "territorialPlanningMissionExpenditurePerResident",
        "Spesa impegnata per assetto del territorio ed edilizia abitativa per residente",
        "Assetto territorio",
        2019,
    ),
    ("civilProtectionMissionExpenditurePerResident", "Spesa impegnata per soccorso civile per residente", "Soccorso civile", 2021),
    (
        "economicDevelopmentMissionExpenditurePerResident",
        "Spesa impegnata per sviluppo economico e competitività per residente",
        "Sviluppo economico",
        2019,
    ),
)

PER_CAPITA_UI_SENTINELS = (
    ("educationMissionExpenditurePerResident", "bilanci"),
    ("wastePerResident", "ambiente"),
    ("civilProtectionMissionExpenditurePerResident", "bilanci"),
)


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


def wait_app(page: Page) -> None:
    page.wait_for_selector("#app main", timeout=20_000)
    page.wait_for_timeout(500)


def no_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate(
        "document.documentElement.scrollWidth-document.documentElement.clientWidth"
    )
    assert overflow <= 2, f"{label}: overflow orizzontale {overflow}px"


def check_compare(page: Page, base: str, key: str, label: str, first_year: int) -> None:
    page.goto(f"{base}/confronta/bilanci/?indicatore={key}", wait_until="networkidle")
    wait_app(page)
    main_text = page.locator("main").inner_text()
    assert label in main_text, f"{key}: etichetta non renderizzata"
    assert "Ragioneria generale dello Stato" in main_text, f"{key}: fonte OpenBDAP non visibile"
    assert "2025" in main_text, f"{key}: anno corrente 2025 non visibile"
    assert "NaN" not in main_text and "undefined" not in main_text, f"{key}: valore tecnico esposto"
    bars = page.locator("#compare-bars .bar-row")
    assert bars.count() == 7, f"{key}: attese 7 barre comunali, trovate {bars.count()}"

    history_button = page.locator('#compare-bars [data-view-mode="history"]')
    if history_button.count():
        history_button.click()
        page.wait_for_timeout(400)
        history = page.locator('#compare-bars [data-view-pane="history"]')
        if history.count():
            history_text = history.inner_text()
            assert str(first_year) in history_text, f"{key}: storico non parte dal {first_year}"
            assert "2025" in history_text, f"{key}: storico non arriva al 2025"
    no_overflow(page, f"confronto {key}")


def check_town(page: Page, base: str, key: str, short_label: str) -> None:
    page.goto(
        f"{base}/comuni/massarosa/?tema=bilanci&indicatore={key}",
        wait_until="networkidle",
    )
    wait_app(page)
    page.get_by_role("heading", name="Massarosa", exact=True).wait_for(timeout=10_000)
    town = page.locator("#town-topic")
    assert town.count() == 1
    active = town.locator(f'.metric-catalog [data-metric="{key}"]')
    assert active.count() == 1, f"{key}: controllo indicatore assente nella scheda Massarosa"
    assert active.get_attribute("aria-selected") == "true", f"{key}: indicatore non attivo nella scheda Massarosa"
    assert short_label in active.inner_text(), f"{key}: short label inattesa nella scheda Massarosa"
    text = town.inner_text()
    assert "2025" in text, f"{key}: anno 2025 assente nella scheda Massarosa"
    assert "Fonte originale" in text, f"{key}: fonte originale assente nella scheda Massarosa"
    assert "NaN" not in text and "undefined" not in text, f"{key}: valore tecnico nella scheda Massarosa"
    no_overflow(page, f"Massarosa {key}")


def check_per_capita_compare_reference(page: Page, base: str, key: str, theme: str) -> None:
    page.goto(f"{base}/confronta/{theme}/?indicatore={key}", wait_until="networkidle")
    wait_app(page)
    page.wait_for_function(
        "document.querySelector('.comparison-legend')?.textContent?.includes('Valore pro capite Versilia')",
        timeout=10_000,
    )
    legend = page.locator(".comparison-legend").first.inner_text()
    assert "Valore pro capite Versilia" in legend, (key, legend)
    assert "Media semplice" not in legend, (key, legend)
    definition = page.locator("#compare-definition").inner_text()
    assert "Valore pro capite Versilia" in definition, (key, definition)
    first_row = page.locator("#compare-bars .bar-row").first
    aria = first_row.get_attribute("aria-label") or ""
    assert "Valore pro capite Versilia:" in aria, (key, aria)


def check_civil_protection_pietrasanta_reference(page: Page, base: str, data: dict) -> None:
    key = "civilProtectionMissionExpenditurePerResident"
    metric = data["metrics"][key]
    row = next(item for item in metric["rows"] if item["town"] == "Pietrasanta")
    expected = ((float(row["value"]) / float(metric["aggregate"]["value"])) - 1) * 100
    expected_text = f"{expected:+.1f}%".replace(".", ",").replace("-", "−")

    page.goto(
        f"{base}/comuni/pietrasanta/?tema=bilanci&indicatore={key}",
        wait_until="networkidle",
    )
    wait_app(page)
    page.get_by_role("heading", name="Pietrasanta", exact=True).wait_for(timeout=10_000)
    panel = page.locator(".versilia-position")
    page.wait_for_function(
        "document.querySelector('.versilia-position .overline')?.textContent?.includes('valore pro capite Versilia')",
        timeout=10_000,
    )
    text = panel.inner_text()
    assert "rispetto al valore pro capite versilia" in text.lower(), text
    assert "Valore pro capite Versilia" in text, text
    assert expected_text in text, (expected_text, text)
    assert "sotto la media Versilia" not in text, text
    assert "non la media semplice" in text.lower(), text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/bilanci-v139-browser")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    screenshots = Path(args.screenshots_dir).resolve()
    screenshots.mkdir(parents=True, exist_ok=True)
    data = json.loads((directory / "data/site-data.json").read_text(encoding="utf-8"))
    assert data["version"] == "v1.39.0", data["version"]
    assert data["release_version"] == "1.39.0", data["release_version"]
    assert data["updated"] == "13 settembre 2026", data["updated"]
    assert len(data["metrics"]) == 213, len(data["metrics"])

    homepage = (directory / "index.html").read_text(encoding="utf-8")
    assert "Aggiornato 13 settembre 2026" in homepage
    assert "Aggiornato 2026-09-13" not in homepage

    for key, label, short_label, first_year in METRICS:
        metric = data["metrics"][key]
        assert metric["meta"]["label"] == label
        assert metric["meta"]["shortLabel"] == short_label
        assert metric["meta"]["year"] == "2025"
        assert len(metric["rows"]) == 7
        assert metric["rows"][0]["series"]["years"][0] == first_year
        assert metric["rows"][0]["series"]["years"][-1] == 2025

    errors: list[str] = []
    report = {"checks": [{"homepageUpdatedLabel": "pass"}], "consoleErrors": [], "pageErrors": []}
    with serve(directory) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 1050})
        desktop.on(
            "console",
            lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None,
        )
        desktop.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        for key, label, _short_label, first_year in METRICS:
            check_compare(desktop, base, key, label, first_year)
            report["checks"].append({key: "compare-pass"})
        for key, _label, short_label, _first_year in (METRICS[0], METRICS[1], METRICS[-1]):
            check_town(desktop, base, key, short_label)
            report["checks"].append({key: "town-pass"})

        for key, theme in PER_CAPITA_UI_SENTINELS:
            check_per_capita_compare_reference(desktop, base, key, theme)
            report["checks"].append({key: "per-capita-reference-pass"})
        check_civil_protection_pietrasanta_reference(desktop, base, data)
        report["checks"].append({"civilProtectionPietrasanta": "weighted-reference-pass"})

        for key, filename in (
            ("fcdePerResident", "bilanci-fcde-desktop.png"),
            ("yearEndCashFundPerResident", "bilanci-cassa-desktop.png"),
            ("economicDevelopmentMissionExpenditurePerResident", "bilanci-m14-desktop.png"),
            ("civilProtectionMissionExpenditurePerResident", "bilanci-m11-reference-desktop.png"),
        ):
            desktop.goto(f"{base}/confronta/bilanci/?indicatore={key}", wait_until="networkidle")
            wait_app(desktop)
            desktop.screenshot(path=str(screenshots / filename), full_page=True)

        desktop.goto(
            f"{base}/comuni/pietrasanta/?tema=bilanci&indicatore=civilProtectionMissionExpenditurePerResident",
            wait_until="networkidle",
        )
        wait_app(desktop)
        desktop.screenshot(path=str(screenshots / "bilanci-m11-pietrasanta-reference-desktop.png"), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.on(
            "console",
            lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None,
        )
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        for key, label, _short_label, first_year in METRICS:
            check_compare(mobile, base, key, label, first_year)
        check_per_capita_compare_reference(mobile, base, "civilProtectionMissionExpenditurePerResident", "bilanci")
        mobile.screenshot(path=str(screenshots / "bilanci-missioni-mobile.png"), full_page=True)
        report["checks"].append({"mobile": "six-metrics-and-reference-pass"})
        browser.close()

    errors.extend(report["pageErrors"])
    errors.extend(report["consoleErrors"])
    assert not errors, " | ".join(errors)
    output = screenshots.parent / "bilanci-v139-browser-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Bilanci v1.39 browser QA OK:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
