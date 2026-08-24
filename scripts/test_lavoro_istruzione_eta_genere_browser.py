#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright

KEYS = [
    ("lavoro", "employmentRate"),
    ("lavoro", "unemploymentRate"),
    ("lavoro", "activityRate"),
    ("istruzione", "diplomaPlus"),
    ("istruzione", "tertiary"),
]
LABOUR_LABELS = ["15–24 anni", "25–49 anni", "50–64 anni", "65 anni e oltre", "25–64 anni", "15 anni e oltre"]
EDUCATION_LABELS = ["9–24 anni", "25–49 anni", "50–64 anni", "65 anni e oltre", "25–64 anni", "9 anni e oltre"]


def req(cond, msg):
    if not cond:
        raise AssertionError(msg)


def no_overflow(page, label):
    values = page.evaluate("() => ({w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})")
    req(max(values["doc"], values["body"]) <= values["w"] + 2, f"Overflow {label}: {values}")


def assert_monotonic_lollipop(page, key):
    rows = page.evaluate(
        """() => [...document.querySelectorAll('#compare-bars .bar-row')].map(row => {
          const raw = row.querySelector(':scope > strong')?.textContent || '';
          const value = Number(raw.replace(/[^0-9,.-]/g,'').replace(',','.'));
          const left = Number.parseFloat(row.querySelector('.comparison-dot')?.style.left || 'NaN');
          return {value,left,town:row.querySelector('.bar-town')?.textContent?.trim() || ''};
        })"""
    )
    req(len(rows) == 7, f"{key}: lollipop non 7/7")
    req(all(row["left"] == row["left"] for row in rows), f"{key}: posizione dot non numerica {rows}")
    req(all(rows[i]["value"] >= rows[i + 1]["value"] - 1e-9 for i in range(6)), f"{key}: valori non ordinati {rows}")
    req(all(rows[i]["left"] >= rows[i + 1]["left"] - 0.05 for i in range(6)), f"{key}: geometria non monotona rispetto ai valori {rows}")
    if rows[0]["value"] > rows[-1]["value"] + 0.05:
        req(rows[0]["left"] > rows[-1]["left"] + 0.05, f"{key}: valore maggiore non produce lollipop maggiore {rows}")


def compare(page, base, theme, key):
    page.goto(f"{base}confronta/{theme}/?indicatore={key}", wait_until="networkidle")
    page.wait_for_selector("select[data-demographic-age]")
    age = page.locator("select[data-demographic-age]")
    gender = page.locator("select[data-demographic-gender]")
    req(age.count() == 1 and gender.count() == 1, f"{key}: filtri doppi assenti")
    req(age.locator("option").count() == 6, f"{key}: attese 6 fasce")
    req(age.locator("optgroup").count() == 2, f"{key}: fasce e aggregati non raggruppati")
    labels = age.locator("option").all_text_contents()
    expected = LABOUR_LABELS if theme == "lavoro" else EDUCATION_LABELS
    req(labels == expected, f"{key}: ordine fasce incoerente {labels}")
    req(age.input_value() == "25-64", f"{key}: default deve restare 25-64")
    req(gender.locator("option").count() == 3, f"{key}: attesi 3 generi")
    req(page.locator("#compare-bars .bar-row").count() == 7, f"{key}: confronto non 7/7")

    before = page.locator("#compare-bars").inner_text()
    gender.select_option("women")
    page.wait_for_function("() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice?.endsWith('|women')")
    after = page.locator("#compare-bars").inner_text()
    req(before != after, f"{key}: filtro genere non cambia il confronto")

    age.select_option("25-49")
    page.wait_for_function("() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === '25-49|women'")
    page.wait_for_function("() => document.querySelector('#compare-bars .comparison-bars')?.dataset.visualGrammarSignature?.includes('25-49|women')")
    req(page.locator("#compare-bars .bar-row").count() == 7, f"{key}: filtro età×genere perde Comuni")
    req(page.locator("#compare-bars .comparison-dot").count() == 7, f"{key}: visual grammar non applicata")
    assert_monotonic_lollipop(page, key)
    no_overflow(page, f"compare/{key}")


def town(page, base, theme, key):
    page.goto(f"{base}comuni/massarosa/?tema={theme}&indicatore={key}", wait_until="networkidle")
    age = page.locator("select[data-demographic-town-age]")
    gender = page.locator("select[data-demographic-town-gender]")
    req(age.count() == 1 and gender.count() == 1, f"{key}: filtri scheda comunale assenti")
    req(age.locator("optgroup").count() == 2, f"{key}: fasce comunali non raggruppate")
    req(page.locator(".demographic-matrix").count() == 0, f"{key}: vecchia matrice caotica ancora presente")
    req(page.locator(".demographic-rate-pyramid").count() == 1, f"{key}: piramide età/sesso assente")
    req(page.locator(".demographic-rate-pyramid-chart").count() == 1, f"{key}: SVG piramide assente")
    req(page.locator(".demographic-rate-pyramid .age-pyramid-point").count() == 8, f"{key}: piramide deve avere 4 fasce × 2 sessi")
    req(page.locator(".demographic-rate-detail").count() == 1, f"{key}: dettaglio analitico assente")
    req(page.locator(".demographic-rate-table tbody tr").count() == 6, f"{key}: dettaglio fasce incompleto")

    first_point = page.locator(".demographic-rate-pyramid .age-pyramid-point").first
    aria = first_point.get_attribute("aria-label") or ""
    req("%" in aria and " su " in aria, f"{key}: tooltip/aria non espone tasso e base di calcolo: {aria}")
    first_point.focus()
    page.wait_for_function("() => !document.querySelector('.demographic-rate-pyramid .age-pyramid-point .chart-tooltip')?.hasAttribute('hidden')")
    tooltip_text = page.locator(".demographic-rate-pyramid .age-pyramid-point .chart-tooltip").first.text_content() or ""
    req("%" in tooltip_text and "/" in tooltip_text, f"{key}: tooltip non contiene percentuale e numeratore/denominatore")

    panel = page.locator(".history-panel").bounding_box()
    pyramid = page.locator(".demographic-rate-pyramid").bounding_box()
    req(panel is not None and pyramid is not None, f"{key}: bounding box non disponibile")
    req(pyramid["x"] >= panel["x"] + 6, f"{key}: piramide troppo vicina al bordo sinistro")
    req(pyramid["x"] + pyramid["width"] <= panel["x"] + panel["width"] - 6, f"{key}: piramide troppo vicina al bordo destro")

    initial = page.locator("[data-composite-primary-value]").inner_text()
    gender.select_option("women")
    page.wait_for_timeout(120)
    changed = page.locator("[data-composite-primary-value]").inner_text()
    req(initial != changed, f"{key}: selezione donne non aggiorna valore")
    age.select_option("50-64")
    page.wait_for_timeout(120)
    req("50–64" in page.locator(".composite-versilia-position").inner_text(), f"{key}: benchmark Versilia non segue età")
    req(page.locator(".town-benchmark").count() == 0, f"{key}: benchmark esterno fisso non deve apparire con filtro dinamico")
    if key == "employmentRate":
        gender.select_option("women")
        age.select_option("25-64")
        page.wait_for_timeout(120)
        req("64,9" in page.locator("[data-composite-primary-value]").inner_text(), "Massarosa occupazione donne 25–64 inattesa")
    no_overflow(page, f"town/{key}")


def run(base):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for viewport in ({"width": 1440, "height": 1000}, {"width": 1024, "height": 768}, {"width": 390, "height": 844}):
            ctx = browser.new_context(viewport=viewport)
            page = ctx.new_page()
            for theme, key in KEYS:
                compare(page, base, theme, key)
                town(page, base, theme, key)
            page.goto(f"{base}confronta/lavoro/?indicatore=employmentRate", wait_until="networkidle")
            body = page.locator("body").inner_text()
            req(
                "Occupazione femminile" in body and "Occupazione maschile" in body,
                "Serie storiche 15–64 per genere assenti dalla navigazione",
            )
            ctx.close()
        browser.close()
    print("Lavoro/Istruzione età×genere browser: ordine fasce, lollipop coerenti, piramidi+tooltip e spaziature OK desktop/laptop/mobile.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8123/")
    a = p.parse_args()
    run(a.base.rstrip("/") + "/")
