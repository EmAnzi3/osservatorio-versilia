#!/usr/bin/env python3
"""Allinea le regressioni esistenti alle tranche Redditi e Demografia Lotto A.

- Redditi: la sezione v1.15 include fonti, peso pensioni e contribuenti/maggiorenni.
- Demografia v2: `ageDistribution` usa il POSAS 2026 invece dello snapshot
  statico pre-Lotto A 2025; la validazione puntuale della fonte 2026 resta nel
  test dedicato `test_demography_lotto_a_v5.py`.
- Demografia v2: 85+ resta un dettaglio leggibile dentro la distribuzione per età,
  senza aggiungere un controllo autonomo al selettore della card.
- Demografia v2: il dettaglio RCS aggregato Versilia viene aggiunto alla vera
  superficie di confronto usata dai compositi `stock`, senza creare nuove card.

Il patch è idempotente e modifica soltanto aspettative/compatibilità mirate.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'
APP = ROOT / 'assets' / 'app-parts' / '03.txt'

OLD_BASE = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeVsInflation",
    ]'''

OLD_V1 = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "pensionIncomeShare", "incomeVsInflation",
    ]'''

NEW_INCOME = '''    assert data["themes"]["economia"]["sections"][0]["metrics"] == [
        "income", "incomeDistribution", "incomeSourceProfile", "pensionIncomeShare",
        "taxpayersAdultPopulationRate", "incomeVsInflation",
    ]'''

OLD_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")'''

NEW_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2026)
        assert age["meta"]["year"] == "2026"
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        assert row["summaryValue"] > 0
        assert row.get("seniorAgeDetail", {}).get("age85Plus", {}).get("count", 0) > 0
        assert row.get("ageSexPyramid", {}).get("displayBands")'''

AGE85_SELECTOR_BLOCK = '''    const summary = compositeSummary(metric,row);
    const partOptions = (row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:'percent', formatted:`${number1.format(part.value)}%`, index }));
    const age85 = age85DetailData(row);
    return [{ key:'summary', label:summary.label, value:summary.value, unit:summary.unit, formatted:summary.formatted }, ...partOptions, ...(metric.meta.key === 'ageDistribution' && age85 ? [{ key:'age85Plus', label:'85 anni e oltre', value:age85.value, unit:'percent', formatted:`${number1.format(age85.value)}%` }] : [])];'''

AGE85_SELECTOR_CLEAN = '''    const summary = compositeSummary(metric,row);
    return [{ key:'summary', label:summary.label, value:summary.value, unit:summary.unit, formatted:summary.formatted }, ...(row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:'percent', formatted:`${number1.format(part.value)}%`, index }))];'''

STOCK_COMPARE_BLOCK = '''      bars.innerHTML = `<div class="topic-bars selectable-topic-bars"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${chartControls}</div><div class="comparison-bars" data-composite-choice="${html(view.choice)}" data-composite-scale="${html(view.scale)}">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${note}</div>`;'''

STOCK_COMPARE_WITH_RCS = '''      const stockDetail = compositeType === 'stock' ? foreignOriginsCompareMarkup(metric) : '';
      bars.innerHTML = `<div class="topic-bars selectable-topic-bars"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${chartControls}</div><div class="comparison-bars" data-composite-choice="${html(view.choice)}" data-composite-scale="${html(view.scale)}">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${note}${stockDetail}</div>`;'''


def patch_regression_expectations() -> None:
    text = TARGET.read_text(encoding='utf-8')

    if NEW_INCOME not in text:
        if OLD_V1 in text:
            text = text.replace(OLD_V1, NEW_INCOME, 1)
        elif OLD_BASE in text:
            text = text.replace(OLD_BASE, NEW_INCOME, 1)
        else:
            raise RuntimeError('Composite economy/redditi expectation anchor not found')

    if NEW_AGE not in text:
        if OLD_AGE not in text:
            raise RuntimeError('Age distribution 2025 regression anchor not found')
        text = text.replace(OLD_AGE, NEW_AGE, 1)

    TARGET.write_text(text, encoding='utf-8')


def patch_age85_selector_cleanup() -> None:
    text = APP.read_text(encoding='utf-8')
    if AGE85_SELECTOR_BLOCK in text:
        text = text.replace(AGE85_SELECTOR_BLOCK, AGE85_SELECTOR_CLEAN, 1)
    elif AGE85_SELECTOR_CLEAN not in text:
        raise RuntimeError('Age85 selector cleanup anchor not found in app-parts/03.txt')
    APP.write_text(text, encoding='utf-8')


def patch_foreign_origins_compare_surface() -> None:
    text = APP.read_text(encoding='utf-8')
    if STOCK_COMPARE_WITH_RCS in text:
        return
    if STOCK_COMPARE_BLOCK not in text:
        raise RuntimeError('Selectable stock compare anchor not found in app-parts/03.txt')
    APP.write_text(text.replace(STOCK_COMPARE_BLOCK, STOCK_COMPARE_WITH_RCS, 1), encoding='utf-8')


def main() -> None:
    patch_regression_expectations()
    patch_age85_selector_cleanup()
    patch_foreign_origins_compare_surface()
    print('Composite regression aligned: Redditi + ageDistribution POSAS 2026; 85+ inline; RCS Versilia nella superficie confronto stock.')


if __name__ == '__main__':
    main()
