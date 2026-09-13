#!/usr/bin/env python3
"""Browser QA desktop/mobile per i sei indicatori Bilanci v1.39.0."""
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
    for key, label, short_label, first_year in METRICS:
        metric = data["metrics"][key]
        assert metric["meta"]["label"] == label
        assert metric["meta"]["shortLabel"] == short_label
        assert metric["meta"]["year"] == "2025"
        assert len(metric["rows"]) == 7
        assert metric["rows"][0]["series"]["years"][0] == first_year
        assert metric["rows"][0]["series"]["years"][-1] == 2025

    errors: list[str] = []
    report = {"checks": [], "consoleErrors": [], "pageErrors": []}
    with serve(directory) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 1050})
        desktop.on(
            "console",
            lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None,
        )
        desktop.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        desktop.goto(f"{base}/", wait_until="networkidle")
        wait_app(desktop)
        hero_facts = desktop.locator(".hero-facts").inner_text()
        assert "Aggiornato 13 settembre 2026" in hero_facts
        assert "2026-09-13" not in hero_facts
        report["checks"].append({"homepageUpdatedLabel": "pass"})

        for key, label, _short_label, first_year in METRICS:
            check_compare(desktop, base, key, label, first_year)
            report["checks"].append({key: "compare-pass"})
        for key, _label, short_label, _first_year in (METRICS[0], METRICS[1], METRICS[-1]):
            check_town(desktop, base, key, short_label)
            report["checks"].append({key: "town-pass"})

        for key, filename in (
            ("fcdePerResident", "bilanci-fcde-desktop.png"),
            ("yearEndCashFundPerResident", "bilanci-cassa-desktop.png"),
            ("economicDevelopmentMissionExpenditurePerResident", "bilanci-m14-desktop.png"),
        ):
            desktop.goto(f"{base}/confronta/bilanci/?indicatore={key}", wait_until="networkidle")
            wait_app(desktop)
            desktop.screenshot(path=str(screenshots / filename), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.on(
            "console",
            lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None,
        )
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        for key, label, _short_label, first_year in METRICS:
            check_compare(mobile, base, key, label, first_year)
        mobile.screenshot(path=str(screenshots / "bilanci-missioni-mobile.png"), full_page=True)
        report["checks"].append({"mobile": "six-metrics-pass"})
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
