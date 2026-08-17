#!/usr/bin/env python3
from __future__ import annotations

import json
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8123"


def fetch_json(path: str) -> dict:
    with urlopen(BASE + path, timeout=10) as response:
        return json.load(response)


def assert_no_horizontal_overflow(page) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, f"Overflow orizzontale: {overflow}px"


def main() -> None:
    payload = fetch_json("/data/data-status.json")
    assert payload["summary"]["metricCount"] == 127
    assert len(payload["metrics"]) == 127
    assert "current" in payload["statuses"]
    assert "verification_required" in payload["statuses"]
    for item in payload["metrics"].values():
        assert item["publishedPeriod"]
        assert item["frequencyLabel"]
        if item["nextExpectedRelease"]:
            assert item["nextExpectedRelease"]["basis"] in {"official_calendar", "documented_schedule"}
        if item["climateCompleteYearsOnly"]:
            observed = str(item.get("observedLatestPeriod") or "").lower()
            assert "ytd" not in observed and "parziale" not in observed

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for viewport in ({"width": 1440, "height": 900}, {"width": 390, "height": 844}):
            page = browser.new_page(viewport=viewport)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE + "/stato-dati/", wait_until="networkidle")
            page.locator("#status-list .data-status-row").first.wait_for()
            assert page.locator("#status-list .data-status-row").count() == 127
            assert "127" in page.locator("#status-count").inner_text()
            page.locator("#status-state").select_option("source_unavailable")
            page.wait_for_timeout(100)
            assert page.locator("#status-list .data-status-row").count() >= 1
            assert_no_horizontal_overflow(page)
            assert not errors, errors
            page.close()

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(BASE + "/indicatori/popolazione-residente/", wait_until="networkidle")
        panel = page.locator(".data-update-card")
        panel.wait_for()
        assert panel.locator("text=Periodo pubblicato").count() == 1
        assert panel.locator("text=Frequenza della fonte").count() == 1
        assert page.locator(".indicator-method dt", has_text="Cadenza indicativa della fonte").count() == 1
        assert_no_horizontal_overflow(page)
        browser.close()

    print("Data status page browser tests passed: desktop, mobile e pagina indicatore.")


if __name__ == "__main__":
    main()
