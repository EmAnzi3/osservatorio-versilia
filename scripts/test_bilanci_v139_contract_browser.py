#!/usr/bin/env python3
"""Forward-compatible browser contract for the Bilanci v1.39 tranche.

The v1.39 gate owns the Bilanci indicators introduced in that tranche, not the
version/count of every later public release. This test deliberately validates
those Bilanci contracts on the current materialized preview so future tranches
do not have to masquerade as v1.39.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import test_bilanci_v139_browser as legacy


def release_tuple(value: str) -> tuple[int, int, int]:
    parts = str(value).strip().lstrip("v").split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise AssertionError(f"release_version non valida: {value!r}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/bilanci-v139-browser")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    screenshots = Path(args.screenshots_dir).resolve()
    screenshots.mkdir(parents=True, exist_ok=True)
    data = json.loads((directory / "data/site-data.json").read_text(encoding="utf-8"))

    release = release_tuple(data["release_version"])
    assert release >= (1, 39, 0), release
    assert len(data["metrics"]) >= 213, len(data["metrics"])

    homepage = (directory / "index.html").read_text(encoding="utf-8")
    assert f"Aggiornato {data['updated']}" in homepage, data["updated"]

    for key, label, short_label, first_year in legacy.METRICS:
        metric = data["metrics"][key]
        assert metric["meta"]["label"] == label
        assert metric["meta"]["shortLabel"] == short_label
        assert metric["meta"]["year"] == "2025"
        assert len(metric["rows"]) == 7
        assert metric["rows"][0]["series"]["years"][0] == first_year
        assert metric["rows"][0]["series"]["years"][-1] == 2025

    report = {
        "release": data["release_version"],
        "metricCount": len(data["metrics"]),
        "checks": [{"homepageUpdatedLabel": "pass"}],
        "consoleErrors": [],
        "pageErrors": [],
    }
    with legacy.serve(directory) as base, legacy.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 1050})
        desktop.on(
            "console",
            lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None,
        )
        desktop.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        for key, label, _short_label, first_year in legacy.METRICS:
            legacy.check_compare(desktop, base, key, label, first_year)
            report["checks"].append({key: "compare-pass"})
        for key, _label, short_label, _first_year in (
            legacy.METRICS[0], legacy.METRICS[1], legacy.METRICS[-1]
        ):
            legacy.check_town(desktop, base, key, short_label)
            report["checks"].append({key: "town-pass"})

        for key, theme in legacy.PER_CAPITA_UI_SENTINELS:
            legacy.check_per_capita_compare_reference(desktop, base, key, theme)
            report["checks"].append({key: "per-capita-reference-pass"})
        legacy.check_civil_protection_pietrasanta_reference(desktop, base, data)
        report["checks"].append({"civilProtectionPietrasanta": "weighted-reference-pass"})

        for key, filename in (
            ("fcdePerResident", "bilanci-fcde-desktop.png"),
            ("yearEndCashFundPerResident", "bilanci-cassa-desktop.png"),
            ("economicDevelopmentMissionExpenditurePerResident", "bilanci-m14-desktop.png"),
            ("civilProtectionMissionExpenditurePerResident", "bilanci-m11-reference-desktop.png"),
        ):
            desktop.goto(f"{base}/confronta/bilanci/?indicatore={key}", wait_until="networkidle")
            legacy.wait_app(desktop)
            desktop.screenshot(path=str(screenshots / filename), full_page=True)

        desktop.goto(
            f"{base}/comuni/pietrasanta/?tema=bilanci&indicatore=civilProtectionMissionExpenditurePerResident",
            wait_until="networkidle",
        )
        legacy.wait_app(desktop)
        desktop.screenshot(
            path=str(screenshots / "bilanci-m11-pietrasanta-reference-desktop.png"),
            full_page=True,
        )

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.on(
            "console",
            lambda msg: report["consoleErrors"].append(f"mobile: {msg.text}") if msg.type == "error" else None,
        )
        mobile.on("pageerror", lambda exc: report["pageErrors"].append(f"mobile: {exc}"))
        for key, label, _short_label, first_year in legacy.METRICS:
            legacy.check_compare(mobile, base, key, label, first_year)
        legacy.check_per_capita_compare_reference(
            mobile, base, "civilProtectionMissionExpenditurePerResident", "bilanci"
        )
        mobile.screenshot(path=str(screenshots / "bilanci-missioni-mobile.png"), full_page=True)
        report["checks"].append({"mobile": "six-metrics-and-reference-pass"})
        browser.close()

    errors = [*report["pageErrors"], *report["consoleErrors"]]
    assert not errors, " | ".join(errors)
    output = screenshots.parent / "bilanci-v139-browser-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Bilanci v1.39 contract browser QA OK on current release:",
        data["release_version"],
        f"({len(data['metrics'])} metriche)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
