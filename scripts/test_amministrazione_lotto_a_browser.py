#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def no_overflow(page, label: str) -> None:
    report = page.evaluate(r"""() => {
      const viewport = window.innerWidth;
      const doc = document.documentElement.scrollWidth;
      const body = document.body.scrollWidth;
      const offenders = [...document.querySelectorAll('*')]
        .map((el) => {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return {
            tag: el.tagName.toLowerCase(),
            id: el.id || '',
            cls: typeof el.className === 'string' ? el.className : '',
            text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 90),
            left: Math.round(rect.left * 10) / 10,
            right: Math.round(rect.right * 10) / 10,
            width: Math.round(rect.width * 10) / 10,
            display: style.display,
            overflowX: style.overflowX,
          };
        })
        .filter((item) => item.display !== 'none' && (item.right > viewport + 2 || item.left < -2))
        .slice(0, 12);
      return {viewport, doc, body, offenders};
    }""")
    actual = max(int(report["doc"]), int(report["body"]))
    require(
        actual <= int(report["viewport"]) + 2,
        f"Overflow {label}: viewport={report['viewport']} doc={report['doc']} body={report['body']} offenders={report['offenders']}",
    )


def check_compare(page, base: str, key: str, expected_label: str) -> None:
    page.goto(f"{base}confronta/bilanci/?indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), f"{key}: indicatore non selezionabile nel confronto")
    page.wait_for_selector("#compare-bars")
    require(expected_label in page.locator("body").inner_text(), f"{key}: etichetta confronto assente")
    require(page.locator("#compare-bars .bar-row").count() == 7, f"{key}: confronto non 7/7")
    no_overflow(page, f"confronto/{key}")


def check_age_compare(page, base: str) -> None:
    key = "municipalStaffAgeStructure"
    page.goto(f"{base}confronta/bilanci/?indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), "Età personale: indicatore non selezionabile nel confronto")
    page.wait_for_selector("select[data-composite-component]")
    selector = page.locator("select[data-composite-component]")
    require(selector.locator("option").count() == 3, "Età personale: selettore confronto non ha 3 fasce")
    require(page.locator("#compare-bars .bar-row").count() == 7, "Età personale: confronto non 7/7")
    first_axis = page.locator("#compare-bars .comparison-axis").inner_text()
    selector.select_option("part-2")
    page.wait_for_function(
        "() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === 'part-2'"
    )
    changed_axis = page.locator("#compare-bars .comparison-axis").inner_text()
    require(first_axis != changed_axis, "Età personale: il cambio fascia non aggiorna il grafico")
    no_overflow(page, "confronto/eta-personale")


def check_training_compare(page, base: str) -> None:
    key = "municipalStaffTraining"
    page.goto(f"{base}confronta/bilanci/?indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), "Formazione: indicatore non selezionabile nel confronto")
    page.wait_for_selector("select[data-composite-component]")
    selector = page.locator("select[data-composite-component]")
    require(selector.locator("option").count() == 4, "Formazione: selettore confronto non ha 4 letture")
    require(page.locator("#compare-bars .bar-row").count() == 7, "Formazione: confronto non 7/7")
    selector.select_option("part-1")
    page.wait_for_function(
        "() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === 'part-1'"
    )
    require("Giornate complessive" in page.locator("body").inner_text(), "Formazione: lettura giornate complessive assente")
    require(page.locator("#compare-bars .bar-row").count() == 7, "Formazione: confronto giornate non 7/7")
    no_overflow(page, "confronto/formazione")


def check_town(page, base: str, key: str, expected_short_label: str) -> None:
    page.goto(f"{base}comuni/massarosa/?tema=bilanci&indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), f"{key}: indicatore non selezionabile nella scheda Massarosa")
    classes = (metric.get_attribute("class") or "").split()
    require("active" in classes, f"{key}: indicatore non attivo nella scheda Massarosa")
    require(expected_short_label in metric.inner_text(), f"{key}: etichetta breve non visibile nella scheda Massarosa")
    require(page.locator(".town-metric-primary").is_visible(), f"{key}: pannello principale comunale non visibile")
    no_overflow(page, f"massarosa/{key}")


def check_age_town(page, base: str) -> None:
    key = "municipalStaffAgeStructure"
    page.goto(f"{base}comuni/massarosa/?tema=bilanci&indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), "Età personale: indicatore non selezionabile a Massarosa")
    require("active" in (metric.get_attribute("class") or "").split(), "Età personale: indicatore non attivo a Massarosa")
    detail_text = page.locator(".composite-fixed-detail").inner_text()
    require("39 dipendenti su 87" in detail_text, "Età personale: conteggio assoluto 55+ di Massarosa non visibile")
    require("38 dipendenti su 87" in detail_text, "Età personale: conteggio assoluto 40–54 di Massarosa non visibile")
    require("10 dipendenti su 87" in detail_text, "Età personale: conteggio assoluto <40 di Massarosa non visibile")
    page.wait_for_selector("select[data-composite-choice]")
    selector = page.locator("select[data-composite-choice]")
    require(selector.locator("option").count() == 3, "Età personale: selettore comunale non ha 3 fasce")
    selector.select_option("part-2")
    page.wait_for_function(
        "() => document.querySelector('[data-view-pane=\"current\"]')?.dataset.compositeChoice === 'part-2'"
    )
    require(page.locator('[data-view-pane="current"] .ux-bar-row').count() == 7, "Età personale: ranking comunale non 7/7")
    no_overflow(page, "massarosa/eta-personale")


def check_training_town(page, base: str) -> None:
    key = "municipalStaffTraining"
    page.goto(f"{base}comuni/massarosa/?tema=bilanci&indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), "Formazione: indicatore non selezionabile a Massarosa")
    require("active" in (metric.get_attribute("class") or "").split(), "Formazione: indicatore non attivo a Massarosa")
    detail_text = page.locator(".composite-fixed-detail").inner_text()
    require("Media totale RGS" in detail_text, "Formazione: media totale RGS non visibile")
    require("Giornate complessive" in detail_text and "267" in detail_text, "Formazione: 267 giornate Massarosa non visibili")
    require("Media uomini RGS" in detail_text and "Media donne RGS" in detail_text, "Formazione: medie per genere non visibili")
    selector = page.locator("select[data-composite-choice]")
    require(selector.locator("option").count() == 4, "Formazione: selettore comunale non ha 4 letture")
    selector.select_option("part-1")
    page.wait_for_function(
        "() => document.querySelector('[data-view-pane=\"current\"]')?.dataset.compositeChoice === 'part-1'"
    )
    require(page.locator('[data-view-pane="current"] .ux-bar-row').count() == 7, "Formazione: ranking comunale non 7/7")
    no_overflow(page, "massarosa/formazione")


def check_online_town(page, base: str) -> None:
    key = "municipalOnlineServicesAdvanced"
    page.goto(f"{base}comuni/massarosa/?tema=bilanci&indicatore={key}", wait_until="networkidle")
    metric = page.locator(f'[data-metric="{key}"]')
    require(metric.count() == 1 and metric.is_visible(), "Servizi online: indicatore non selezionabile a Massarosa")
    require("active" in (metric.get_attribute("class") or "").split(), "Servizi online: indicatore non attivo a Massarosa")
    require("Servizi online · livello massimo" in metric.inner_text(), "Servizi online: etichetta breve non visibile")
    body = page.locator("body").inner_text()
    require("33,3%" in body, "Servizi online: valore 2022 di Massarosa non visibile")
    require("2022" in body, "Servizi online: annualità 2022 non visibile")
    no_overflow(page, "massarosa/servizi-online")


def run(base: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for viewport in ({"width": 1440, "height": 1000}, {"width": 390, "height": 844}):
            context = browser.new_context(viewport=viewport)
            page = context.new_page()
            check_compare(page, base, "municipalEmployeesPer1000", "Dipendenti comunali per 1.000 residenti")
            check_compare(page, base, "municipalStaffTurnover", "Turnover netto del personale comunale")
            check_age_compare(page, base)
            check_training_compare(page, base)
            check_compare(page, base, "municipalOnlineServicesAdvanced", "Servizi comunali online al massimo livello di disponibilità")
            check_town(page, base, "municipalEmployeesPer1000", "Dipendenti / 1.000 residenti")
            check_town(page, base, "municipalStaffTurnover", "Turnover del personale")
            check_age_town(page, base)
            check_training_town(page, base)
            check_online_town(page, base)
            context.close()
        browser.close()
    print("Amministrazione browser: 5 indicatori OK su desktop e mobile, servizi online 2022 visibili e nessun overflow.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    run(args.base.rstrip("/") + "/")
