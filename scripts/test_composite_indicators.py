#!/usr/bin/env python3
"""Verifica dati, UI e responsive dei tre indicatori compositi."""
from __future__ import annotations

import contextlib
import json
import math
import os
import re
import socket
import threading
import unicodedata
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "composite-indicators-v1.9.0.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"
COMPOSITE_KEYS = {"ageDistribution", "internalResidentialMobility", "incomeDistribution"}
REMOVED_KEYS = {"share014", "share65", "incomeUnder15k"}
CLIMATE_KEYS = {
    "climateTemperatureTrend50y", "climatePrecipitationTrend50y",
    "climateTminTrend", "climateTmaxTrend",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
    previous = Path.cwd()
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
        os.chdir(previous)


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(character for character in value if unicodedata.category(character) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-11), (
        f"{label}: {actual} != {expected}"
    )


def static_checks() -> dict:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    built = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert data == built, "Il build statico non usa il dataset canonico aggiornato"

    app_runtime = (ROOT / "assets" / "app-parts" / "06.txt").read_text(encoding="utf-8")
    assert len(data["metrics"]) == 115
    assert CLIMATE_KEYS <= set(data["metrics"])
    external_metrics = {
        key for key, metric in data["metrics"].items()
        if metric.get("dataStorage", {}).get("type") == "external-climate"
    }
    assert external_metrics == CLIMATE_KEYS
    assert all(not data["metrics"][key]["rows"] for key in CLIMATE_KEYS)
    assert len(data["metrics"]) - len(external_metrics) == 111
    assert all(key in app_runtime for key in CLIMATE_KEYS)
    assert COMPOSITE_KEYS <= set(data["metrics"])
    assert not (REMOVED_KEYS & set(data["metrics"]))
    assert not any(
        REMOVED_KEYS & set(theme["metrics"])
        for theme in data["themes"].values()
    )
    assert data["themes"]["demografia"]["metrics"] == [
        "population", "ageDistribution", "oldAgeIndex",
        "internalResidentialMobility", "populationChange",
    ]
    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution",
    ]

    assert set(snapshot["raw"]) == {town["name"] for town in data["towns"]}
    registry_map = registry["sourceProfileByUrl"]
    for key in COMPOSITE_KEYS:
        metric = data["metrics"][key]
        assert len(metric["rows"]) == 7
        assert metric["method"]["coverage"] == "7/7"
        assert registry_map[metric["sourceUrl"]]
        indicator = DIST / "indicatori" / slugify(metric["meta"]["label"]) / "index.html"
        assert indicator.is_file(), f"Routing indicatore mancante: {key}"

    population_rows = {row["town"]: row for row in data["metrics"]["population"]["rows"]}
    age = data["metrics"]["ageDistribution"]
    assert age["meta"]["label"] == "Distribuzione per fasce d’età"
    for row in age["rows"]:
        parts = row["parts"]
        assert len(parts) == 7
        close(sum(part["value"] for part in parts), 100.0, f"Età/{row['town']} somma")
        assert all(part["count"] > 0 for part in parts)
        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")

    income = data["metrics"]["incomeDistribution"]
    official_groups = snapshot["sources"]["incomeDistribution"]["officialClassAggregation"]
    assert [len(official_groups[label]) for label in official_groups] == [3, 1, 1, 3]
    for row in income["rows"]:
        parts = row["parts"]
        assert len(parts) == 4
        close(sum(part["value"] for part in parts), 100.0, f"Reddito/{row['town']} somma")
        assert all(part["count"] > 0 for part in parts)
        assert [part["count"] for part in parts] == snapshot["raw"][row["town"]]["incomeBands"]

    mobility = data["metrics"]["internalResidentialMobility"]
    assert mobility["meta"]["theme"] == "demografia"
    assert "pendolari" in mobility["method"]["caveat"].lower()
    for row in mobility["rows"]:
        assert row["series"]["years"] == [2019, 2020, 2021, 2022, 2023, 2024]
        assert len(row["series"]["values"]) == 6
        assert len(row["parts"]) == 3
        close(row["parts"][0]["value"] - row["parts"][1]["value"], row["parts"][2]["value"], f"Saldo/{row['town']}")
        assert row["parts"][0]["count"] - row["parts"][1]["count"] == row["parts"][2]["count"]
        assert row["series"]["values"] == row["componentSeries"]["Saldo migratorio interno"]["values"]

    return data


def normalized_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def expected_value(value: float, unit: str) -> str:
    if unit == "percent":
        return f"{value:.1f}%".replace(".", ",")
    if unit == "years":
        return f"{value:.1f} anni".replace(".", ",")
    if unit == "currency":
        return f"{round(value):,} €".replace(",", ".")
    raise AssertionError(f"Unità non prevista: {unit}")


def selector_choices(metric: dict, row: dict) -> list[tuple[str, str, float, str]]:
    choices = [("summary", metric["meta"]["summaryLabel"], row["summaryValue"], metric["meta"]["summaryUnit"])]
    choices.extend(
        (f"part-{index}", part.get("selectorLabel", part["label"]), part["value"], "percent")
        for index, part in enumerate(row["parts"])
    )
    return choices


def verify_selector_page(page: Page, base: str, data: dict, town: str, metric_key: str) -> None:
    metric = data["metrics"][metric_key]
    row = next(item for item in metric["rows"] if item["town"] == town)
    page.goto(
        base + f"comuni/{row['slug']}/?tema={metric['meta']['theme']}&indicatore={metric_key}",
        wait_until="networkidle",
    )
    page.wait_for_selector("[data-composite-choice]")
    page.wait_for_selector(".history-panel .ux-view-shell")
    choices = selector_choices(metric, row)
    assert page.locator("[data-composite-choice] option").all_text_contents() == [choice[1] for choice in choices]
    for choice, label, value, unit in choices:
        page.locator("[data-composite-choice]").select_option(choice)
        page.wait_for_function(
            "choice => document.querySelector('[data-view-pane=\"current\"]')?.dataset.compositeChoice === choice",
            choice,
        )
        primary_label = normalized_text(page.locator("[data-composite-primary-label]").inner_text())
        primary_value = normalized_text(page.locator("[data-composite-primary-value]").inner_text())
        aggregate_label = normalized_text(page.locator("[data-composite-aggregate-label]").inner_text())
        aggregate_value = normalized_text(page.locator("[data-composite-aggregate-value]").inner_text())
        assert primary_label == label
        assert primary_value == expected_value(value, unit)
        assert aggregate_label.startswith("Età media" if choice == "summary" and metric_key == "ageDistribution" else "Reddito medio" if choice == "summary" else "Versilia ·")
        aggregate = metric["aggregate"]["summaryValue"] if choice == "summary" else metric["aggregate"]["parts"][int(choice.removeprefix("part-"))]["value"]
        assert aggregate_value == expected_value(aggregate, unit)

        expected_order = sorted(
            metric["rows"],
            key=lambda item: item["summaryValue"] if choice == "summary" else item["parts"][int(choice.removeprefix("part-"))]["value"],
            reverse=True,
        )
        graph_order = page.locator('[data-view-pane="current"] .ux-bar-town').all_text_contents()
        assert graph_order == [item["town"] for item in expected_order], f"Ranking non sincronizzato: {town}/{metric_key}/{choice}"
        assert page.locator('[data-view-pane="current"] .ux-bar-row').count() == 7

    widths = page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
    assert widths["scroll"] <= widths["client"], f"Overflow pagina: {town}/{metric_key}/{widths}"


def tooltip_checks(page: Page, base: str, theme: str, metric_key: str, expected_rows: int, parts: int) -> None:
    page.goto(base + f"confronta/{theme}/?indicatore={metric_key}", wait_until="networkidle")
    page.wait_for_selector(".composite-distribution-list")
    assert page.locator(".composite-distribution-row").count() == expected_rows
    assert page.locator(".composite-legend").count() == 1
    segments = page.locator(".composite-segment")
    assert segments.count() == expected_rows * parts
    for index in range(segments.count()):
        segment = segments.nth(index)
        assert "%" in segment.locator(":scope > b").inner_text()
        aria = segment.get_attribute("aria-label") or ""
        tooltip = segment.locator(".bar-hover-label")
        assert tooltip.inner_text().replace(" · ", ": ") in aria
        segment.focus()
        assert float(tooltip.evaluate("element => getComputedStyle(element).opacity")) == 1.0


def browser_checks(data: dict) -> None:
    executable = os.environ.get("CHROMIUM_PATH")
    launch = {"headless": True}
    if executable:
        launch["executable_path"] = executable
    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch)
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = desktop.new_page()

        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 7)
        assert page.locator(".composite-row-head > span").count() == 7
        assert all("Età media" in text for text in page.locator(".composite-row-head > span").all_text_contents())
        tooltip_checks(page, base, "economia", "incomeDistribution", 7, 4)
        assert all("Reddito medio" in text for text in page.locator(".composite-row-head > span").all_text_contents())

        page.goto(base + "confronta/demografia/?indicatore=internalResidentialMobility", wait_until="networkidle")
        page.wait_for_selector(".composite-mobility-table")
        assert page.locator(".composite-mobility-row").count() == 7
        assert page.locator(".composite-mobility-row > span").count() == 21
        headings = page.locator(".composite-mobility-head span").all_text_contents()
        assert headings == ["Comune", "Iscritti da altri Comuni", "Cancellati verso altri Comuni", "Saldo migratorio interno"]

        search_terms = {
            "fasce età": "ageDistribution",
            "trasferimenti di residenza": "internalResidentialMobility",
            "fasce reddito": "incomeDistribution",
        }
        for term, metric_key in search_terms.items():
            page.goto(base, wait_until="networkidle")
            page.locator(".global-search-trigger").click()
            page.locator(".search-field input").fill(term)
            assert page.locator(f'[data-search-result][href*="/indicatori/{slugify(data["metrics"][metric_key]["meta"]["label"])}/"]').count() == 1

        towns = [town["name"] for town in data["towns"]]
        for town in towns:
            verify_selector_page(page, base, data, town, "ageDistribution")
            verify_selector_page(page, base, data, town, "incomeDistribution")
        desktop.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        tooltip_checks(mobile_page, base, "demografia", "ageDistribution", 7, 7)
        tooltip_checks(mobile_page, base, "economia", "incomeDistribution", 7, 4)
        for town in towns:
            verify_selector_page(mobile_page, base, data, town, "ageDistribution")
            verify_selector_page(mobile_page, base, data, town, "incomeDistribution")
        mobile.close()
        browser.close()


def main() -> None:
    data = static_checks()
    browser_checks(data)
    print("Indicatori compositi verificati: 7 Comuni, tutti i selettori, desktop e mobile.")


if __name__ == "__main__":
    main()
