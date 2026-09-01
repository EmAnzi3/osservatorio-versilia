#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "assets" / "app-parts" / "03.txt"
SITE = ROOT / "data" / "site-data.json"
MATERIALIZER = ROOT / "scripts" / "materialize_demanio_marittimo_v127.py"
BROWSER_TEST = ROOT / "scripts" / "test_costa_mare_v123_browser.py"
KEYS = ("maritimeConcessions", "maritimeConcessionFeesDue")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Token non trovato in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_app() -> None:
    helper_marker = "\n  function updateFiscalRecoveryTownPosition(metric,row,choice,position) {"
    helper = r'''
  function updateMaritimeTownPosition(metric,row,choice,position) {
    if (!position || !['maritimeConcessions','maritimeConcessionFeesDue'].includes(metric?.meta?.key) || row?.notApplicable) return;
    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const local=Number(selected?.value);
    const total=Number(agg?.value);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : null;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(overline) overline.textContent=metric.meta.comparisonOverline || 'Peso sulla Versilia costiera';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>quota non disponibile</small>`
      : `${html(number1.format(share))}%<small>del totale dei quattro Comuni costieri</small>`;
    if(noteEl) noteEl.textContent=metric.meta.comparisonNote || 'Quota del valore comunale sul totale dei quattro Comuni costieri.';
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }
'''
    text = APP.read_text(encoding="utf-8")
    if "function updateMaritimeTownPosition" not in text:
        if helper_marker not in text:
            raise RuntimeError("Punto inserimento helper demanio non trovato")
        text = text.replace(helper_marker, helper + helper_marker, 1)

    initial_old = "      updateAgricultureProfileTownPosition(metric,row,initialChoice,initialPosition);\n"
    initial_new = initial_old + "      updateMaritimeTownPosition(metric,row,initialChoice,initialPosition);\n"
    if "updateMaritimeTownPosition(metric,row,initialChoice,initialPosition);" not in text:
        if initial_old not in text:
            raise RuntimeError("Hook iniziale benchmark comunale non trovato")
        text = text.replace(initial_old, initial_new, 1)

    dynamic_old = "        updateAgricultureProfileTownPosition(metric,row,choice,position);\n"
    dynamic_new = dynamic_old + "        updateMaritimeTownPosition(metric,row,choice,position);\n"
    if "updateMaritimeTownPosition(metric,row,choice,position);" not in text:
        if dynamic_old not in text:
            raise RuntimeError("Hook dinamico benchmark comunale non trovato")
        text = text.replace(dynamic_old, dynamic_new, 1)

    APP.write_text(text, encoding="utf-8")


def patch_site_data() -> None:
    data = json.loads(SITE.read_text(encoding="utf-8"))
    note = "Quota del valore comunale sul totale dei quattro Comuni costieri; i tre Comuni non costieri sono n.a. e non entrano nell’aggregato."
    for key in KEYS:
        meta = data["metrics"][key]["meta"]
        meta["comparisonDifference"] = "shareOfAggregate"
        meta["comparisonOverline"] = "Peso sulla Versilia costiera"
        meta["comparisonNote"] = note
    SITE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_materializer() -> None:
    old = "'comparisonDifference':'absolute','comparisonLabel':'Versilia costiera','comparisonOverline':'Rispetto alla Versilia costiera','comparisonNote':'Il riferimento è la somma dei quattro Comuni costieri; i tre Comuni non costieri sono n.a. e non entrano nell’aggregato.'"
    new = "'comparisonDifference':'shareOfAggregate','comparisonLabel':'Versilia costiera','comparisonOverline':'Peso sulla Versilia costiera','comparisonNote':'Quota del valore comunale sul totale dei quattro Comuni costieri; i tre Comuni non costieri sono n.a. e non entrano nell’aggregato.'"
    replace_once(MATERIALIZER, old, new)


def patch_browser_test() -> None:
    anchor = '''    for key in DEMANIO_METRICS:\n        page.goto(\n            urljoin(base, f"comuni/massarosa/?tema=ambiente&indicatore={key}"),\n'''
    block = '''    share_expectations = {\n        "maritimeConcessions": ("44,9%", "30,3%", "799"),\n        "maritimeConcessionFeesDue": ("40,9%", "31,2%", "6.524.121,74"),\n    }\n    for key, (total_share, tourist_share, aggregate_marker) in share_expectations.items():\n        page.goto(\n            urljoin(base, f"comuni/viareggio/?tema=ambiente&indicatore={key}"),\n            wait_until="networkidle",\n        )\n        page.wait_for_timeout(300)\n        position = page.locator("#town-topic .composite-versilia-position")\n        assert position.count() == 1, f"{key}: pannello quota Versilia assente"\n        text = " ".join(position.inner_text().split())\n        assert "Peso sulla Versilia costiera" in text, text\n        assert total_share in text, text\n        assert aggregate_marker in text, text\n        assert "sotto la Versilia" not in text and "−" not in position.locator("[data-composite-delta]").inner_text(), text\n        selector = page.locator("#town-topic select[data-composite-choice]")\n        assert selector.count() == 1\n        selector.select_option("part-1")\n        page.wait_for_timeout(220)\n        text = " ".join(position.inner_text().split())\n        assert tourist_share in text, text\n        assert "del totale dei quattro Comuni costieri" in text, text\n\n'''
    text = BROWSER_TEST.read_text(encoding="utf-8")
    if "share_expectations = {" not in text:
        if anchor not in text:
            raise RuntimeError("Punto inserimento test quota demanio non trovato")
        text = text.replace(anchor, block + anchor, 1)
    BROWSER_TEST.write_text(text, encoding="utf-8")


def main() -> None:
    patch_app()
    patch_site_data()
    patch_materializer()
    patch_browser_test()
    print("Demanio v1.27: benchmark comunale convertito in peso percentuale sul totale costiero.")


if __name__ == "__main__":
    main()
