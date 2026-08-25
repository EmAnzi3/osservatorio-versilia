#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173/"
METRIC = "scheduledTplTripsPer1000"
OUT = Path("artifacts/mobilita-v6-site-review")
OUT.mkdir(parents=True, exist_ok=True)


def settle(page, selector: str) -> None:
    page.wait_for_selector(selector, timeout=30000)
    page.wait_for_timeout(900)
    page.evaluate("document.fonts && document.fonts.ready")


def capture_compare(browser, mobile: bool = False) -> dict:
    viewport = {"width": 390, "height": 844} if mobile else {"width": 1440, "height": 1050}
    context = browser.new_context(viewport=viewport, device_scale_factor=1)
    page = context.new_page()
    page.goto(f"{BASE}confronta/mobilita/?indicatore={METRIC}", wait_until="networkidle")
    settle(page, ".topic-dashboard")
    body = page.locator("body").inner_text()
    checks = {
        "theme": "Mobilità e infrastrutture" in body,
        "section": "Trasporto pubblico" in body,
        "metric": "Offerta TPL programmata" in body,
        "source": "Regione Toscana" in body,
        "coverage": "7/7" in body,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Confronto non coerente: {checks}")
    name = "02-confronto-mobile.png" if mobile else "01-confronto-desktop.png"
    page.screenshot(path=str(OUT / name), full_page=True)
    result = {
        "url": page.url,
        "title": page.title(),
        "checks": checks,
        "definition": page.locator("#compare-definition").inner_text() if page.locator("#compare-definition").count() else "",
    }
    context.close()
    return result


def capture_town(browser, slug: str, expected_name: str, mobile: bool, prefix: str, expected_rail: int, capture_top: bool = False) -> dict:
    viewport = {"width": 390, "height": 900} if mobile else {"width": 1440, "height": 1000}
    context = browser.new_context(viewport=viewport, device_scale_factor=1)
    page = context.new_page()
    page.goto(f"{BASE}comuni/{slug}/?tema=mobilita&indicatore={METRIC}", wait_until="networkidle")
    settle(page, ".tpl-offer-detail")

    if capture_top:
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT / f"{prefix}-pagina.png"), full_page=False)

    page.locator(".tpl-offer-detail summary").click()
    page.wait_for_timeout(250)
    detail_locator = page.locator(".tpl-offer-detail")
    detail = detail_locator.inner_text()
    body = page.locator("body").inner_text()
    checks = {
        "town": expected_name in body,
        "metric": "Offerta TPL programmata" in body,
        "detail": "Corse programmate" in detail and "Accesso e finestra oraria" in detail,
        "rail": f"Ferrovia\n{expected_rail}" in detail or f"Ferrovia {expected_rail}" in detail,
        "rawGtfsClockHidden": "29:" not in detail and "30:" not in detail,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Scheda {expected_name} non coerente: {checks}\n{detail}")

    # Screenshot del componente reale, senza artefatti di stitching causati dall'header sticky.
    deep = page.locator(".topic-deep-dive")
    deep.scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    deep.screenshot(path=str(OUT / f"{prefix}-dettaglio.png"))

    result = {"url": page.url, "title": page.title(), "checks": checks, "detail": detail}
    context.close()
    return result


def main() -> None:
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        report["compareDesktop"] = capture_compare(browser, mobile=False)
        report["compareMobile"] = capture_compare(browser, mobile=True)
        report["forteDesktop"] = capture_town(browser, "forte-dei-marmi", "Forte dei Marmi", False, "03-forte-dei-marmi", 0, capture_top=True)
        report["massarosaMobile"] = capture_town(browser, "massarosa", "Massarosa", True, "05-massarosa-mobile", 20, capture_top=False)
        browser.close()
    (OUT / "browser-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v["checks"] for k, v in report.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
