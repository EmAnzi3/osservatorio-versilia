#!/usr/bin/env python3
"""Patch puntuale della review Morosità ERP v1.25.0.

Corregge il riferimento territoriale, l'unità visibile, la gerarchia cromatica
ed il respiro del dettaglio contabile. Mantiene il materializzatore idempotente.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Pattern non trovato in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def patch_materializer() -> None:
    path = ROOT / "scripts/materialize_erp_arrears_v125.py"
    text = path.read_text(encoding="utf-8")

    hash_replacements = {
        "7f018ba02adbff4ac10923a35d575547449508641123372f64172f5c9f8ce60d": "0362d001246832bc66040c533a14b503ed9e6e3416d11a870638b56ccc3199bd",
        "651d55b4a126f48cfb8fd1169b219feaf8d9f989c706796442300565a7eea624": "52d476f097066a3807099202ca508e961c6c61c5efe452a9861df538c980f757",
        "7baea08a7a7f987125c6ad2fad25f16d9bfc23b98d9534cc893b3e6a701054b8": "831ba0712eb026ec955e45763831fe12ab6a941bc6f7940c585b888371ff872a",
        "d30e26daf98116440780c6120cecb2b57ae5e1dea98303bcc73cf295e835ce1e": "de36675ef97245b818bee99caec598f334166884e61c300c2be28c5d13902983",
        "80c1b1eee9d8b81a725580e928b0f00f008837979bb8c3387ab11191aa9658ba": "ca00f1a212d6fa29bdfa688ebc949ee5d9fb3c708342d36f07832add8b495422",
    }
    for old, new in hash_replacements.items():
        text = text.replace(old, new)

    old_unit = '            "unit": "percent2",\n'
    new_unit = (
        '            "unit": "%",\n'
        '            "comparisonReference": "aggregate",\n'
        '            "comparisonLabel": "valore Versilia",\n'
        '            "comparisonOverline": "Rispetto alla Versilia",\n'
        '            "comparisonNote": "Il riferimento è il rapporto calcolato sulla somma della morosità e degli importi emessi dei sette Comuni, non la media semplice delle percentuali comunali.",\n'
    )
    if new_unit not in text:
        if old_unit not in text:
            raise RuntimeError("Unità ERP attesa non trovata nel materializzatore")
        text = text.replace(old_unit, new_unit, 1)

    anomaly_marker = '''            {\n                "year": 2023,\n                "type": "published_percentage_inconsistency",\n'''
    anomaly_2022 = '''            {\n                "year": 2022,\n                "type": "published_header_date_mismatch",\n                "note": "Intestazione tabella riportata come 31/12/2021 nel bilancio 2022; valori riferiti all’esercizio 2022.",\n            },\n'''
    if "published_header_date_mismatch" not in text:
        if anomaly_marker not in text:
            raise RuntimeError("Marker anomalia 2023 non trovato")
        text = text.replace(anomaly_marker, anomaly_2022 + anomaly_marker, 1)

    old_percent = '''    percent_marker = "      case 'percent': return `${number1.format(v)}%`;"\n    percent2_line = "      case 'percent2': return `${number2.format(v)}%`;"\n    if percent2_line not in text:\n        if percent_marker not in text:\n            raise RuntimeError("Marker format percent non trovato")\n        text = text.replace(percent_marker, percent_marker + "\\n" + percent2_line, 1)\n'''
    new_percent = '''    percent_marker = "      case 'percent': return `${number1.format(v)}%`;"\n    percent_precise_line = "      case '%': return `${number2.format(v)}%`;"\n    if percent_precise_line not in text:\n        if percent_marker not in text:\n            raise RuntimeError("Marker format percent non trovato")\n        text = text.replace(percent_marker, percent_marker + "\\n" + percent_precise_line, 1)\n'''
    if new_percent not in text:
        if old_percent not in text:
            raise RuntimeError("Blocco formatter percent2 non trovato")
        text = text.replace(old_percent, new_percent, 1)

    app_marker = '    app = APP03.read_text(encoding="utf-8")\n'
    class_patch = '''    view_marker = "    container.dataset.theme = themeKey;"\n    view_line = "    container.classList.toggle('erp-arrears-view', metricKey === 'erpArrears');"\n    if view_line not in app:\n        if view_marker not in app:\n            raise RuntimeError("Marker vista comunale ERP non trovato")\n        app = app.replace(view_marker, view_marker + "\\n" + view_line, 1)\n'''
    if "view_line = \"    container.classList.toggle('erp-arrears-view'" not in text:
        if app_marker not in text:
            raise RuntimeError("Marker APP03 non trovato")
        text = text.replace(app_marker, app_marker + class_patch, 1)

    path.write_text(text, encoding="utf-8")


def patch_data_test() -> None:
    path = ROOT / "scripts/test_erp_arrears_v125.py"
    text = path.read_text(encoding="utf-8")
    hashes = {
        "7f018ba02adbff4ac10923a35d575547449508641123372f64172f5c9f8ce60d": "0362d001246832bc66040c533a14b503ed9e6e3416d11a870638b56ccc3199bd",
        "651d55b4a126f48cfb8fd1169b219feaf8d9f989c706796442300565a7eea624": "52d476f097066a3807099202ca508e961c6c61c5efe452a9861df538c980f757",
        "7baea08a7a7f987125c6ad2fad25f16d9bfc23b98d9534cc893b3e6a701054b8": "831ba0712eb026ec955e45763831fe12ab6a941bc6f7940c585b888371ff872a",
        "d30e26daf98116440780c6120cecb2b57ae5e1dea98303bcc73cf295e835ce1e": "de36675ef97245b818bee99caec598f334166884e61c300c2be28c5d13902983",
        "80c1b1eee9d8b81a725580e928b0f00f008837979bb8c3387ab11191aa9658ba": "ca00f1a212d6fa29bdfa688ebc949ee5d9fb3c708342d36f07832add8b495422",
    }
    for old, new in hashes.items():
        text = text.replace(old, new)
    text = text.replace('assert metric["meta"]["unit"] == "percent2"', 'assert metric["meta"]["unit"] == "%"')
    text = text.replace('assert "case \'percent2\'" in app00', 'assert "case \'%\'" in app00')

    meta_anchor = '    assert metric["meta"]["polarity"] == "neutral"\n'
    meta_checks = (
        '    assert metric["meta"]["comparisonReference"] == "aggregate"\n'
        '    assert metric["meta"]["comparisonLabel"] == "valore Versilia"\n'
        '    assert "non la media semplice" in metric["meta"]["comparisonNote"]\n'
    )
    if 'metric["meta"]["comparisonReference"]' not in text:
        if meta_anchor not in text:
            raise RuntimeError("Anchor meta test ERP non trovato")
        text = text.replace(meta_anchor, meta_anchor + meta_checks, 1)

    aggregate_anchor = '    assert close(metric["aggregate"]["value"], 8.56)\n'
    mean_checks = (
        '    simple_mean = sum(row["value"] for row in metric["rows"]) / len(metric["rows"])\n'
        '    assert close(simple_mean, 6.31)\n'
        '    assert not close(simple_mean, metric["aggregate"]["value"]), "Il benchmark ERP non deve usare la media semplice comunale"\n'
    )
    if "simple_mean = sum" not in text:
        if aggregate_anchor not in text:
            raise RuntimeError("Anchor aggregato test ERP non trovato")
        text = text.replace(aggregate_anchor, aggregate_anchor + mean_checks, 1)

    anomaly_assert = '    assert any(item["type"] == "published_percentage_inconsistency" and item["year"] == 2023 for item in snapshot["anomalies"])\n'
    extra = '    assert any(item["type"] == "published_header_date_mismatch" and item["year"] == 2022 for item in snapshot["anomalies"])\n'
    if extra not in text:
        if anomaly_assert not in text:
            raise RuntimeError("Anchor anomalie test ERP non trovato")
        text = text.replace(anomaly_assert, extra + anomaly_assert, 1)

    app03_anchor = '    assert "${erpArrearsDetailMarkup(metric,row)}" in app03\n'
    app03_check = '    assert "erp-arrears-view" in app03\n'
    if app03_check not in text:
        if app03_anchor not in text:
            raise RuntimeError("Anchor APP03 test ERP non trovato")
        text = text.replace(app03_anchor, app03_anchor + app03_check, 1)

    path.write_text(text, encoding="utf-8")


def patch_runtime() -> None:
    app00 = ROOT / "assets/app-parts/00.txt"
    text = app00.read_text(encoding="utf-8")
    precise = "      case '%': return `${number2.format(v)}%`;"
    percent = "      case 'percent': return `${number1.format(v)}%`;"
    if precise not in text:
        if percent not in text:
            raise RuntimeError("Formatter percentuale APP00 non trovato")
        text = text.replace(percent, percent + "\n" + precise, 1)
    app00.write_text(text, encoding="utf-8")

    app03 = ROOT / "assets/app-parts/03.txt"
    text = app03.read_text(encoding="utf-8")
    marker = "    container.dataset.theme = themeKey;"
    view = "    container.classList.toggle('erp-arrears-view', metricKey === 'erpArrears');"
    if view not in text:
        if marker not in text:
            raise RuntimeError("Marker town-topic APP03 non trovato")
        text = text.replace(marker, marker + "\n" + view, 1)
    app03.write_text(text, encoding="utf-8")


def patch_css() -> None:
    path = ROOT / "assets/fidelity.css"
    text = path.read_text(encoding="utf-8")
    marker = "/* v1.25 ERP review — contrasto, respiro e gerarchia */"
    if marker in text:
        return
    block = r'''

/* v1.25 ERP review — contrasto, respiro e gerarchia */
.town-topic.erp-arrears-view .town-metric-primary {
  background: #ffffff;
}
.town-topic.erp-arrears-view .history-panel {
  background: #f5f8f7;
  border-color: #d6e1df;
}
.town-topic.erp-arrears-view .versilia-position {
  background: #eef3f6;
  border-color: #d3dfe6;
}
.erp-arrears-detail {
  background: #ffffff;
  border-color: #cbd9d6;
  box-shadow: 0 8px 24px rgba(24, 54, 62, .05);
}
.erp-arrears-detail > summary {
  min-height: 64px;
  padding: 18px 22px;
  background: #f1f6f5;
}
.erp-arrears-detail .composite-town-detail {
  margin-top: 0;
  padding: 18px 20px 20px;
  gap: 14px;
  background: #ffffff;
  border-top: 1px solid #dce6e3;
}
.erp-arrears-detail .composite-town-detail > div {
  border: 1px solid #d5e1de;
  border-radius: 12px;
  padding: 16px 18px;
  background: #f5f9f8;
}
.erp-arrears-detail .composite-town-detail > div:nth-child(2) {
  background: #eef4f8;
  border-color: #d7e1e8;
}
.erp-arrears-detail .composite-town-detail small {
  margin-left: 0;
}
.erp-arrears-detail > .aggregate-note {
  margin: 0;
  padding: 16px 20px 18px;
  background: #ffffff;
  border-top: 1px solid #e1e8e6;
}
@media (max-width: 700px) {
  .erp-arrears-detail > summary {
    padding: 16px 17px;
  }
  .erp-arrears-detail .composite-town-detail {
    padding: 14px 14px 16px;
    gap: 10px;
  }
  .erp-arrears-detail .composite-town-detail > div {
    padding: 14px 15px;
  }
  .erp-arrears-detail > .aggregate-note {
    padding: 14px 15px 16px;
  }
}
'''
    path.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def patch_browser_test() -> None:
    path = ROOT / "scripts/test_erp_arrears_v125_browser.py"
    content = r'''#!/usr/bin/env python3
"""Browser gate desktop/mobile e light/dark per Morosità ERP v1.25.0."""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def body_text(page) -> str:
    return page.locator("body").inner_text()


def check_page(page, url: str, required: list[str]) -> None:
    response = page.goto(url, wait_until="networkidle")
    assert response is None or response.ok, (url, response.status if response else None)
    text = body_text(page)
    for token in required:
        assert token in text, (url, token)
    assert page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), f"Overflow orizzontale: {url}"


def css_number(locator, property_name: str) -> float:
    return float(locator.evaluate(f"el => parseFloat(getComputedStyle(el).{property_name})"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    parser.add_argument("--screenshots-dir", default="reports/erp-arrears-v125-browser")
    args = parser.parse_args()
    output = Path(args.screenshots_dir)
    output.mkdir(parents=True, exist_ok=True)

    compare = urljoin(args.base, "confronta/abitare/?indicatore=erpArrears")
    town = urljoin(args.base, "comuni/massarosa/?tema=abitare&indicatore=erpArrears")
    indicator = urljoin(args.base, "indicatori/morosita-erp/")

    configurations = [
        ("desktop", {"width": 1440, "height": 1000}),
        ("mobile", {"width": 390, "height": 844}),
    ]
    schemes = ["light", "dark"]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for label, viewport in configurations:
            for scheme in schemes:
                context = browser.new_context(viewport=viewport, color_scheme=scheme)
                page = context.new_page()

                check_page(page, compare, ["Morosità ERP", "8,56%", "Viareggio", "10,83%", "Massarosa", "3,48%"])
                page.locator(".comparison-legend").wait_for(state="visible")
                legend = page.locator(".comparison-legend").inner_text()
                assert "Versilia · 7 Comuni" in legend, legend
                assert "Media semplice" not in legend, legend
                assert "percent2" not in body_text(page), "L'unità tecnica percent2 non deve essere visibile"

                camaiore = page.locator(".comparison-bars > .bar-row").filter(has_text="Camaiore").first
                reference = camaiore.locator(".comparison-reference")
                dot = camaiore.locator(".comparison-dot")
                assert reference.count() == 1 and dot.count() == 1
                reference_left = float(reference.evaluate("el => parseFloat(el.style.left)"))
                dot_left = float(dot.evaluate("el => parseFloat(el.style.left)"))
                assert reference_left > dot_left, (reference_left, dot_left, "8,56% deve stare a destra di Camaiore 7,37%")
                page.screenshot(path=output / f"compare-{label}-{scheme}.png", full_page=True)

                check_page(page, town, ["Morosità ERP", "3,48%", "Dettaglio contabile 2024"])
                primary_value = page.locator(".town-metric-primary [data-composite-primary-value]").inner_text().strip()
                assert primary_value == "3,48%", primary_value
                y_labels = page.locator(".trend-chart .chart-y-label").all_inner_texts()
                assert any("%" in item for item in y_labels), y_labels
                assert "percent2" not in body_text(page)

                detail = page.locator("details.erp-arrears-detail")
                assert detail.count() == 1, "Accordion dettaglio contabile ERP assente o duplicato"
                detail.evaluate("el => el.open = true")
                expanded = body_text(page)
                for token in (
                    "Importi emessi cumulati",
                    "Morosità cumulata",
                    "2.078.965,36",
                    "72.398,09",
                ):
                    assert token in expanded, (town, token)

                summary = detail.locator(":scope > summary")
                first_card = detail.locator(".composite-town-detail > div").first
                assert css_number(summary, "paddingLeft") >= 16
                assert css_number(first_card, "paddingLeft") >= 14
                detail_background = detail.evaluate("el => getComputedStyle(el).backgroundColor")
                card_background = first_card.evaluate("el => getComputedStyle(el).backgroundColor")
                assert detail_background != card_background, (detail_background, card_background)
                assert page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), f"Overflow orizzontale dopo apertura dettaglio: {town}"
                page.screenshot(path=output / f"massarosa-{label}-{scheme}.png", full_page=True)

                check_page(page, indicator, ["Morosità ERP", "8,56%", "2020", "2024", "Fonte originale"])
                context.close()
        browser.close()

    print("Morosità ERP v1.25.0 browser: benchmark Versilia 8,56%, unità %, contrasto e padding verificati desktop/mobile light/dark.")


if __name__ == "__main__":
    main()
'''
    path.write_text(content, encoding="utf-8")


def main() -> None:
    patch_materializer()
    patch_data_test()
    patch_runtime()
    patch_css()
    patch_browser_test()
    print("Patch review ERP v1.25 applicata.")


if __name__ == "__main__":
    main()
