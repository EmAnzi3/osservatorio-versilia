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


def req(cond, msg):
    if not cond:
        raise AssertionError(msg)


def no_overflow(page, label):
    values = page.evaluate("() => ({w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})")
    req(max(values["doc"], values["body"]) <= values["w"] + 2, f"Overflow {label}: {values}")


def check_pyramid(page, base, theme, key):
    page.goto(f"{base}confronta/{theme}/?indicatore={key}", wait_until="networkidle")
    page.wait_for_selector("#compare-demographic-pyramid .demographic-rate-pyramid")

    host = page.locator("#compare-demographic-pyramid")
    req(host.locator(".demographic-rate-pyramid").count() == 1, f"{key}: piramide Versilia assente")
    req(host.locator(".demographic-rate-pyramid-chart").count() == 1, f"{key}: SVG Versilia assente")
    req(host.locator(".age-pyramid-point").count() == 8, f"{key}: attese 4 fasce × 2 sessi")
    text = host.inner_text()
    req("Totale Versilia" in text and "Piramide per età e genere" in text, f"{key}: intestazione Versilia assente")
    req("non mediando le percentuali" in text, f"{key}: metodo aggregazione non dichiarato")

    geometry = page.evaluate(
        """async (key) => {
          const response = await fetch('/data/site-data.json');
          const data = await response.json();
          const metric = data.metrics[key];
          const ageMap = new Map((metric.meta.ageOptions || []).map(age => [age.key, age]));
          const bands = (metric.meta.pyramidAgeKeys || []).map(key => ageMap.get(key)).filter(Boolean).reverse();
          const parts = new Map((metric.aggregate?.parts || []).map(part => [part.key, part]));
          const expected = [];
          bands.forEach(age => {
            expected.push((Number(parts.get(`${age.key}|men`)?.value) || 0) * 3);
            expected.push((Number(parts.get(`${age.key}|women`)?.value) || 0) * 3);
          });
          const actual = [...document.querySelectorAll('#compare-demographic-pyramid .age-pyramid-point rect')]
            .map(rect => Number(rect.getAttribute('width')));
          return {expected, actual};
        }""",
        key,
    )
    req(len(geometry["expected"]) == 8 and len(geometry["actual"]) == 8, f"{key}: geometria incompleta {geometry}")
    for idx, (expected, actual) in enumerate(zip(geometry["expected"], geometry["actual"])):
        req(abs(expected - actual) <= 0.25, f"{key}: barra {idx} non usa aggregate.parts ({actual} vs {expected})")

    first = host.locator(".age-pyramid-point").first
    aria = first.get_attribute("aria-label") or ""
    req("%" in aria and " su " in aria, f"{key}: aria/tooltip incompleto: {aria}")
    first.focus()
    page.wait_for_function("() => !document.querySelector('#compare-demographic-pyramid .age-pyramid-point .chart-tooltip')?.hasAttribute('hidden')")
    tooltip = host.locator(".age-pyramid-point .chart-tooltip").first.text_content() or ""
    req("%" in tooltip and "/" in tooltip, f"{key}: tooltip aggregato incompleto")

    no_overflow(page, f"versilia-pyramid/{key}")


def run(base):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for viewport in ({"width": 1440, "height": 1000}, {"width": 390, "height": 844}):
            context = browser.new_context(viewport=viewport)
            page = context.new_page()
            for theme, key in KEYS:
                check_pyramid(page, base, theme, key)

            page.goto(f"{base}confronta/lavoro/?indicatore=employmentGenderGap", wait_until="networkidle")
            req(page.locator("#compare-demographic-pyramid .demographic-rate-pyramid").count() == 0, "Piramide Versilia visibile su indicatore non età×genere")
            no_overflow(page, "versilia-pyramid/non-demographic")
            context.close()
        browser.close()
    print("Piramidi totale Versilia: 5 indicatori OK, aggregate.parts verificati, tooltip e mobile senza overflow.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    run(args.base.rstrip("/") + "/")
