#!/usr/bin/env python3
"""Allinea regressioni Redditi/Demografia e la compatibilità del selettore 85+.

- Redditi: la sezione v1.15 include fonti, peso pensioni e contribuenti/maggiorenni.
- Demografia v2: `ageDistribution` usa il POSAS 2026 invece dello snapshot
  statico pre-Lotto A 2025; la validazione puntuale della fonte 2026 resta nel
  test dedicato `test_demography_lotto_a_v5.py`.
- Demografia v2: rende robusta l'interazione del selettore `85+` nella scheda
  comunale e allinea la vista corrente gestita da `ux-history.js`.

Il patch è idempotente e modifica soltanto aspettative/compatibilità mirate.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'
APP = ROOT / 'assets' / 'app-parts' / '03.txt'
UX_HISTORY = ROOT / 'assets' / 'ux-history.js'

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

AGE85_INTERACTION_MARKER = 'data-age85-choice-fallback'
AGE85_UX_MARKER = "choice === 'age85Plus'"


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


def patch_age85_app_interaction() -> None:
    text = APP.read_text(encoding='utf-8')
    if AGE85_INTERACTION_MARKER in text:
        return

    anchor = '''    installChartInteractions(container);
    scrollActiveControl(tablist);'''
    replacement = r'''    if (metric.meta.key === 'ageDistribution' && selectable) {
      container.dataset.age85ChoiceFallback = '1';
      container.addEventListener('change', event => {
        const choiceSelect = event.target.closest('select[data-composite-choice]');
        if (!choiceSelect || !container.contains(choiceSelect) || choiceSelect.value !== 'age85Plus') return;
        const selected = options.find(option => option.key === 'age85Plus');
        if (!selected) return;
        const agg = compositeSelectionAggregate(metric,'age85Plus');
        const delta = compositeDeltaText(selected.value,agg.value,selected.unit);
        const labelEl = container.querySelector('[data-composite-primary-label]');
        const valueEl = container.querySelector('[data-composite-primary-value]');
        const position = container.querySelector('.composite-versilia-position');
        if (labelEl) labelEl.textContent = selected.label;
        if (valueEl) valueEl.textContent = selected.formatted;
        if (position) {
          position.dataset.compositeSelection = 'age85Plus';
          const deltaEl = position.querySelector('[data-composite-delta]');
          if (deltaEl) deltaEl.innerHTML = `${html(delta.headline)}<small>${html(delta.direction)}</small>`;
          const aggLabel = position.querySelector('[data-composite-aggregate-label]');
          const aggValue = position.querySelector('[data-composite-aggregate-value]');
          if (aggLabel) aggLabel.textContent = agg.label;
          if (aggValue) aggValue.textContent = agg.formatted;
        }
        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice:'age85Plus',town:town.slug}}));
      });
    }
    /* data-age85-choice-fallback */
    installChartInteractions(container);
    scrollActiveControl(tablist);'''
    if anchor not in text:
        raise RuntimeError('Age85 interaction anchor not found in app-parts/03.txt')
    APP.write_text(text.replace(anchor, replacement, 1), encoding='utf-8')


def patch_age85_history_adapter() -> None:
    text = UX_HISTORY.read_text(encoding='utf-8')
    if AGE85_UX_MARKER in text:
        return

    anchor = '''    if (choice === 'summary') {
      const unit = metric.meta.summaryUnit || metric.meta.unit;'''
    replacement = r'''    if (metric.meta.key === 'ageDistribution' && choice === 'age85Plus') {
      clone.meta.unit = 'percent';
      clone.meta.label = '85 anni e oltre';
      clone.rows = metric.rows.map(row => {
        const detail = row.age85PlusDetail || row.seniorAgeDetail?.age85Plus;
        const value = Number(detail?.value);
        return { ...row, value, formatted: Number.isFinite(value) ? `${percent1.format(value)}%` : 'n.d.' };
      });
      return clone;
    }
    if (choice === 'summary') {
      const unit = metric.meta.summaryUnit || metric.meta.unit;'''
    if anchor not in text:
        raise RuntimeError('Age85 history adapter anchor not found in ux-history.js')
    UX_HISTORY.write_text(text.replace(anchor, replacement, 1), encoding='utf-8')


def main() -> None:
    patch_regression_expectations()
    patch_age85_app_interaction()
    patch_age85_history_adapter()
    print('Composite regression aligned: Redditi completi + ageDistribution POSAS 2026; selettore 85+ reso robusto.')


if __name__ == '__main__':
    main()
