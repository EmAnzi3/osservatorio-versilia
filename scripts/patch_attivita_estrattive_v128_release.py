#!/usr/bin/env python3
"""Completa integrazione UI e regression gate del lotto Attività estrattive v1.28.0."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP03 = ROOT / "assets/app-parts/03.txt"
CATALOG_TEST = ROOT / "scripts/test_catalog_release_v116.py"
PAGES = ROOT / ".github/workflows/pages.yml"


def patch_extractive_position() -> None:
    text = APP03.read_text(encoding="utf-8")
    if "function updateExtractiveTownPosition" not in text:
        marker = "  function updateFiscalRecoveryTownPosition(metric,row,choice,position) {\n"
        function = r'''  function updateExtractiveTownPosition(metric,row,choice,position) {
    if (!position || !['extractiveSites','extractivePlanning'].includes(metric?.meta?.key)) return;
    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const localRaw=selected?.value;
    const totalRaw=agg?.value;
    const local=localRaw === null || localRaw === undefined ? NaN : Number(localRaw);
    const total=totalRaw === null || totalRaw === undefined ? NaN : Number(totalRaw);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : null;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(overline) overline.textContent=metric.meta.comparisonOverline || 'Peso sulla Versilia';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>${total === 0 ? 'totale Versilia pari a zero' : 'quota non disponibile'}</small>`
      : `${html(number2.format(share))}%<small>del totale della lettura selezionata</small>`;
    if(noteEl) noteEl.textContent=metric.meta.comparisonNote || 'Quota del valore comunale sul totale dei sette Comuni per la lettura selezionata.';
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }

'''
        if marker not in text:
            raise RuntimeError("Marker updateFiscalRecoveryTownPosition non trovato")
        text = text.replace(marker, function + marker, 1)

    initial = "      updateMaritimeTownPosition(metric,row,initialChoice,initialPosition);\n"
    if "updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);" not in text:
        if initial not in text:
            raise RuntimeError("Marker inizializzazione composite non trovato")
        text = text.replace(initial, initial + "      updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);\n", 1)

    choice = "        updateMaritimeTownPosition(metric,row,choice,position);\n"
    if "updateExtractiveTownPosition(metric,row,choice,position);" not in text:
        if choice not in text:
            raise RuntimeError("Marker cambio selector composite non trovato")
        text = text.replace(choice, choice + "        updateExtractiveTownPosition(metric,row,choice,position);\n", 1)

    APP03.write_text(text, encoding="utf-8")


def patch_catalog_regression() -> None:
    text = CATALOG_TEST.read_text(encoding="utf-8")
    text = text.replace(
        '"""Contratto pubblico e metodologico della release v1.27.0."""',
        '"""Contratto pubblico e metodologico della release v1.28.0."""',
    )
    old = "assert '**v1.27.0** — 1 settembre 2026' in readme and '177 indicatori' in readme and '173 con valori incorporati' in readme"
    new = "assert '**v1.28.0** — 2 settembre 2026' in readme and '180 indicatori' in readme and '176 con valori incorporati' in readme"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("Assert README release non trovato nel regression test catalogo")
    CATALOG_TEST.write_text(text, encoding="utf-8")


def patch_pages_workflow() -> None:
    text = PAGES.read_text(encoding="utf-8")

    data_marker = "          python scripts/test_costa_mare_v123.py\n"
    data_line = "          python scripts/test_attivita_estrattive_v128.py\n"
    if data_line not in text:
        if data_marker not in text:
            raise RuntimeError("Marker test Costa non trovato in pages.yml")
        text = text.replace(data_marker, data_marker + data_line, 1)

    json_marker = "          python -m json.tool data/source-snapshots/costa-mare-v123.json > /dev/null\n"
    json_line = "          python -m json.tool data/source-snapshots/attivita-estrattive-v128.json > /dev/null\n"
    if json_line not in text:
        if json_marker not in text:
            raise RuntimeError("Marker snapshot Costa non trovato in pages.yml")
        text = text.replace(json_marker, json_marker + json_line, 1)

    browser_marker = "      - name: Validate Ambiente acqua e bonifiche\n"
    browser_block = """      - name: Validate Attività estrattive\n        run: python scripts/test_attivita_estrattive_v128_browser.py --base http://127.0.0.1:8123/\n\n"""
    if "Validate Attività estrattive" not in text:
        if browser_marker not in text:
            raise RuntimeError("Marker browser Ambiente non trovato in pages.yml")
        text = text.replace(browser_marker, browser_block + browser_marker, 1)

    compile_marker = "            scripts/materialize_costa_mare_v123.py \\\n"
    compile_lines = "            scripts/materialize_attivita_estrattive_v128.py \\\n            scripts/patch_attivita_estrattive_v128_release.py \\\n            scripts/test_attivita_estrattive_v128.py \\\n            scripts/test_attivita_estrattive_v128_browser.py \\\n"
    if "scripts/materialize_attivita_estrattive_v128.py" not in text:
        if compile_marker not in text:
            raise RuntimeError("Marker py_compile Costa non trovato in pages.yml")
        text = text.replace(compile_marker, compile_marker + compile_lines, 1)

    PAGES.write_text(text, encoding="utf-8")


def main() -> None:
    patch_extractive_position()
    patch_catalog_regression()
    patch_pages_workflow()
    print("Patch release Attività estrattive v1.28 applicata: confronto comunale, test catalogo e CI aggiornati.")


if __name__ == "__main__":
    main()
