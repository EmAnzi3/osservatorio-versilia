#!/usr/bin/env python3
"""Browser QA for Salute v1.40 municipal pages and demographic enrichment."""
from __future__ import annotations

import argparse
import contextlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


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


def wait_town(page: Page, metric_key: str) -> None:
    page.wait_for_selector("#town-topic .town-metric-layout", timeout=20_000)
    page.wait_for_function(
        """key => {
          const active = document.querySelector('#town-topic [data-metric].active, #town-topic [data-metric][aria-selected="true"]');
          return active?.dataset?.metric === key && document.querySelector('#town-topic .versilia-position');
        }""",
        arg=metric_key,
        timeout=20_000,
    )
    page.wait_for_timeout(350)


def expected_relative(metric: dict, town: str) -> str:
    row = next(item for item in metric["rows"] if item["town"] == town)
    value = ((float(row["value"]) / float(metric["aggregate"]["value"])) - 1) * 100
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}{abs(value):.1f}%".replace(".", ",")


def expected_share(metric: dict, town: str) -> str:
    row = next(item for item in metric["rows"] if item["town"] == town)
    value = float(row["value"]) / float(metric["aggregate"]["value"]) * 100
    return f"{value:.1f}%".replace(".", ",")


def italian_decimal(value: float, decimals: int = 2) -> str:
    text = f"{float(value):,.{decimals}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def part_by_key(container: dict, choice: str) -> dict:
    return next(part for part in container.get("parts", []) if part.get("key") == choice)


def assert_no_footer_overlap(page: Page) -> None:
    overlap = page.evaluate(
        """() => {
          const position = document.querySelector('#town-topic .versilia-position');
          const label = position?.querySelector(':scope > div span');
          const value = position?.querySelector(':scope > div b');
          if (!label || !value) return true;
          const a = label.getBoundingClientRect();
          const b = value.getBoundingClientRect();
          return !(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top);
        }"""
    )
    assert overlap is False, "Etichetta e valore Versilia si sovrappongono"


def open_metric(page: Page, base: str, metric_key: str) -> None:
    page.goto(
        f"{base}/comuni/viareggio/?tema=salute&indicatore={metric_key}",
        wait_until="networkidle",
    )
    wait_town(page, metric_key)


def town_sex_select(page: Page):
    selector = page.locator("#town-topic .town-metric-primary select[data-composite-choice]")
    count = selector.count()
    assert count == 1, (
        f"Selettore sesso comunale atteso 1, trovato {count}; "
        f"controlli={page.locator('#town-topic .composite-read-selector').all_inner_texts()}"
    )
    return selector


def town_age_select(page: Page):
    selector = page.locator("#town-topic .town-metric-primary select[data-demographic-town-age]")
    count = selector.count()
    assert count == 1, f"Selettore fascia d'età comunale atteso 1, trovato {count}"
    return selector


def town_gender_select(page: Page):
    selector = page.locator("#town-topic .town-metric-primary select[data-demographic-town-gender]")
    count = selector.count()
    assert count == 1, f"Selettore sesso comunale atteso 1, trovato {count}"
    return selector


def assert_tuscany_visible(page: Page) -> str:
    panel = page.locator("#town-topic .versilia-position")
    text = panel.inner_text()
    assert "Toscana" in text, text
    assert panel.locator("[data-composite-tuscany-value]").count() == 1, text
    return text


def assert_demographic_benchmark(panel, metric: dict, choice: str, label: str) -> None:
    """Validate the selected ARS slice against data, not against a stale static label."""
    panel_text = panel.inner_text()
    overline = panel.locator(".overline").inner_text().casefold()
    assert "rispetto al valore ars versilia" in overline, panel_text

    aggregate_label = panel.locator("[data-composite-aggregate-label]").inner_text()
    tuscany_label = panel.locator("[data-composite-tuscany-label]").inner_text()
    assert aggregate_label.casefold() == f"Versilia · {label}".casefold(), aggregate_label
    assert tuscany_label.casefold() == f"Toscana · {label}".casefold(), tuscany_label

    aggregate_part = part_by_key(metric["aggregate"], choice)
    tuscany_part = part_by_key(metric["tuscany"], choice)
    aggregate_value = panel.locator("[data-composite-aggregate-value]").inner_text()
    tuscany_value = panel.locator("[data-composite-tuscany-value]").inner_text()
    assert italian_decimal(aggregate_part["value"]) in aggregate_value, (aggregate_part, aggregate_value)
    assert italian_decimal(tuscany_part["value"]) in tuscany_value, (tuscany_part, tuscany_value)
    assert "0,00 ogni 1.000" not in panel_text, panel_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/salute-v140-town-browser")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    screenshots = Path(args.screenshots_dir).resolve()
    screenshots.mkdir(parents=True, exist_ok=True)
    data = json.loads((directory / "data/site-data.json").read_text(encoding="utf-8"))

    errors: list[str] = []
    report = {"checks": [], "consoleErrors": [], "pageErrors": []}
    with serve(directory) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on(
            "console",
            lambda msg: report["consoleErrors"].append(msg.text) if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: report["pageErrors"].append(str(exc)))

        # ARS mortality: official 202M benchmark + sex detail + same-source Tuscany.
        key = "mortalityCirculatory"
        open_metric(page, base, key)
        panel = page.locator("#town-topic .versilia-position")
        text = panel.inner_text()
        normalized = text.casefold()
        assert "rispetto al valore ars versilia" in normalized, text
        assert expected_relative(data["metrics"][key], "Viareggio") in text, text
        assert "media versilia" not in normalized, text
        assert "aggregato ufficiale zona versilia" in normalized, text
        assert page.get_by_text("Dettaglio per sesso", exact=True).count() == 1
        sex_select = town_sex_select(page)
        assert {option.get_attribute("value") for option in sex_select.locator("option").all()} == {"totale", "maschi", "femmine"}
        assert_tuscany_visible(page)
        sex_select.select_option("femmine")
        page.wait_for_timeout(150)
        assert "Toscana · Femmine" in panel.inner_text()
        assert_no_footer_overlap(page)
        assert page.get_by_text("Dettagli sanitari aggiuntivi", exact=True).count() == 0
        page.screenshot(path=str(screenshots / "viareggio-mortalita-circolatoria-sesso.png"), full_page=True)
        report["checks"].append({key: "official-202M-sex-Tuscany-pass"})

        # MaCro: age x sex selectors and Tuscany update with the chosen demographic slice.
        key = "hypertensionPrevalence"
        open_metric(page, base, key)
        assert page.get_by_text("Dettaglio per fascia d’età e sesso", exact=True).count() == 1
        age_select = town_age_select(page)
        gender_select = town_gender_select(page)
        assert [option.get_attribute("value") for option in age_select.locator("option").all()] == ["totale", "16-44", "45-64", "65-84", "85+"]
        assert {option.get_attribute("value") for option in gender_select.locator("option").all()} == {"totale", "maschi", "femmine"}
        table_text = page.locator("#town-topic .health-demographic-table").inner_text()
        table_folded = table_text.casefold()
        for label in ("16–44 anni", "45–64 anni", "65–84 anni", "85+ anni", "Totale", "Maschi", "Femmine"):
            assert label.casefold() in table_folded, (label, table_text)
        # Structural standardized zeroes from the ARS export must never be rendered
        # as actual age-specific rates: the materializer uses misura_grezza here.
        assert "0,00 ogni 1.000" not in table_text, table_text
        assert_tuscany_visible(page)
        age_select.select_option("65-84")
        gender_select.select_option("femmine")
        page.wait_for_timeout(200)
        panel = page.locator("#town-topic .versilia-position")
        assert_demographic_benchmark(
            panel,
            data["metrics"][key],
            "65-84|femmine",
            "65–84 anni · Femmine",
        )
        assert_no_footer_overlap(page)
        page.screenshot(path=str(screenshots / "viareggio-ipertensione-65-84-femmine.png"), full_page=True)
        report["checks"].append({key: "age-sex-Tuscany-selection-pass"})

        # Legacy ARS metric: enrichment must also apply to indicators already in the catalogue.
        key = "diabetes"
        open_metric(page, base, key)
        assert page.get_by_text("Dettaglio per fascia d’età e sesso", exact=True).count() == 1
        town_age_select(page)
        town_gender_select(page)
        assert "0,00 ogni 1.000" not in page.locator("#town-topic .health-demographic-table").inner_text()
        assert_tuscany_visible(page)
        page.screenshot(path=str(screenshots / "viareggio-diabete-demografia.png"), full_page=True)
        report["checks"].append({key: "legacy-age-sex-Tuscany-pass"})

        # Life expectancy already had sex history: enrichment must preserve it and add Tuscany.
        key = "lifeExpectancy"
        open_metric(page, base, key)
        assert page.get_by_text("Dettaglio per sesso", exact=True).count() == 1
        assert page.get_by_text("Storico · Totale", exact=True).count() == 1
        sex_select = town_sex_select(page)
        sex_select.select_option("femmine")
        page.wait_for_timeout(150)
        assert "Toscana · Femmine" in page.locator("#town-topic .versilia-position").inner_text()
        page.screenshot(path=str(screenshots / "viareggio-speranza-vita-sesso.png"), full_page=True)
        report["checks"].append({key: "existing-sex-history-Tuscany-pass"})

        # Deliberately unreconciled legacy metrics must not receive invented demographic selectors.
        key = "chronicTotal"
        open_metric(page, base, key)
        assert page.locator("#town-topic .health-demographic-detail, #town-topic .health-sex-detail").count() == 0
        assert page.locator("#town-topic [data-demographic-town-age], #town-topic [data-demographic-town-gender]").count() == 0
        report["checks"].append({key: "unreconciled-no-forcing-pass"})

        # Presidi ospedalieri: quota del Comune sul totale Versilia, non +133,3% vs media.
        key = "hospitals"
        open_metric(page, base, key)
        text = page.locator("#town-topic .versilia-position").inner_text()
        normalized = text.casefold()
        assert "quota sul totale versilia" in normalized, text
        assert expected_share(data["metrics"][key], "Viareggio") in text, text
        assert "del totale versilia" in normalized, text
        assert "+133,3%" not in text, text
        assert_no_footer_overlap(page)
        page.screenshot(path=str(screenshots / "viareggio-presidi-ospedalieri.png"), full_page=True)
        report["checks"].append({key: "share-of-total-pass"})

        # RSA accreditate: stessa semantica delle strutture fisiche.
        key = "accreditedRsaCount"
        open_metric(page, base, key)
        text = page.locator("#town-topic .versilia-position").inner_text()
        normalized = text.casefold()
        assert "quota sul totale versilia" in normalized, text
        assert expected_share(data["metrics"][key], "Viareggio") in text, text
        assert "del totale versilia" in normalized, text
        assert_no_footer_overlap(page)
        page.screenshot(path=str(screenshots / "viareggio-rsa-accreditate.png"), full_page=True)
        report["checks"].append({key: "share-of-total-pass"})

        browser.close()

    errors.extend(report["pageErrors"])
    errors.extend(report["consoleErrors"])
    assert not errors, " | ".join(errors)
    output = screenshots.parent / "salute-v140-town-browser-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Salute v1.40 enriched town browser QA OK:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
