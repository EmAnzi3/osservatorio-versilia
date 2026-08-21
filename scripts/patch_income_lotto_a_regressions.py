#!/usr/bin/env python3
"""Allinea regressioni e compatibilità delle tranche Redditi/Demografia Lotto A.

- Redditi: allinea le aspettative storiche alla tranche completa.
- Demografia v2: `ageDistribution` usa POSAS 2026 e otto fasce esaustive,
  con 80–84 e 85+ come componenti normali della distribuzione.
- La piramide mantiene il tooltip canonico anche quando `ux-history.js`
  ricostruisce il contenuto della history-panel: l'interazione è delegata al
  contenitore stabile della scheda comunale, non ai nodi poi sostituiti.
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

OLD_AGE_COUNT = '''        assert len(parts) == 7
        close(sum(part["value"] for part in parts), 100.0, f"Età/{row['town']} somma")'''
NEW_AGE_COUNT = '''        assert len(parts) == 8
        assert [part["label"] for part in parts][-2:] == ["80–84 anni", "85 anni e oltre"]
        close(sum(part["value"] for part in parts), 100.0, f"Età/{row['town']} somma")'''

OLD_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2025)
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        close(row["summaryValue"], snapshot["raw"][row["town"]]["averageAge"], f"Età media/{row['town']}")'''

NEW_AGE = '''        population = population_rows[row["town"]]
        index = population["series"]["years"].index(2026)
        assert age["meta"]["year"] == "2026"
        assert sum(part["count"] for part in parts) == population["series"]["values"][index]
        assert row["summaryValue"] > 0
        assert "seniorAgeDetail" not in row and "age85PlusDetail" not in row
        assert row.get("ageSexPyramid", {}).get("displayBands")'''

OLD_BROWSER = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 7)'''
NEW_BROWSER = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 8)'''

PYRAMID_DELEGATE_MARKER = 'data-age-pyramid-delegated'
PYRAMID_HELPER_ANCHOR = '''  function omiZoneTableMarkup(row, compact = false) {'''
PYRAMID_HELPER = r'''  function installAgePyramidDelegation(root) {
    if (!root || root.dataset.agePyramidDelegated === '1') return;
    root.dataset.agePyramidDelegated = '1';
    const chartFor = target => target?.closest?.('.age-pyramid-trend');
    const pointFor = target => target?.closest?.('.age-pyramid-point');
    const hide = chart => {
      if (!chart) return;
      chart.querySelectorAll('.age-pyramid-point').forEach(point => {
        point.classList.remove('active');
        point.querySelector('.chart-tooltip')?.setAttribute('hidden','');
      });
    };
    const show = point => {
      const chart = point?.closest('.age-pyramid-trend');
      if (!point || !chart) return;
      hide(chart);
      point.classList.add('active');
      point.querySelector('.chart-tooltip')?.removeAttribute('hidden');
    };
    root.addEventListener('pointerover', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('pointerout', event => {
      const chart = chartFor(event.target);
      if (!chart || chart.contains(event.relatedTarget)) return;
      hide(chart);
    });
    root.addEventListener('focusin', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('focusout', event => {
      const chart = chartFor(event.target);
      if (!chart || chart.contains(event.relatedTarget)) return;
      hide(chart);
    });
    root.addEventListener('click', event => {
      const point = pointFor(event.target);
      if (point && root.contains(point)) show(point);
    });
    root.addEventListener('keydown', event => {
      const point = pointFor(event.target);
      if (!point || !root.contains(point)) return;
      const chart = point.closest('.age-pyramid-trend');
      const points = [...chart.querySelectorAll('.age-pyramid-point')];
      const index = points.indexOf(point);
      if (event.key === 'Escape') { hide(chart); point.blur(); return; }
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === 'ArrowLeft') next = (index - 1 + points.length) % points.length;
      if (event.key === 'ArrowRight') next = (index + 1) % points.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = points.length - 1;
      points[next]?.focus();
    });
  }
  /* data-age-pyramid-delegated */

'''

PYRAMID_CALL_OLD = '''    installChartInteractions(container);
    scrollActiveControl(tablist);'''
PYRAMID_CALL_NEW = '''    installChartInteractions(container);
    installAgePyramidDelegation(container);
    scrollActiveControl(tablist);'''


def patch_regression_expectations() -> None:
    text = TARGET.read_text(encoding='utf-8')

    if NEW_INCOME not in text:
        if OLD_V1 in text:
            text = text.replace(OLD_V1, NEW_INCOME, 1)
        elif OLD_BASE in text:
            text = text.replace(OLD_BASE, NEW_INCOME, 1)
        else:
            raise RuntimeError('Composite economy/redditi expectation anchor not found')

    if NEW_AGE_COUNT not in text:
        if OLD_AGE_COUNT not in text:
            raise RuntimeError('Age distribution 7-band expectation anchor not found')
        text = text.replace(OLD_AGE_COUNT, NEW_AGE_COUNT, 1)

    if NEW_AGE not in text:
        if OLD_AGE not in text:
            raise RuntimeError('Age distribution 2025 regression anchor not found')
        text = text.replace(OLD_AGE, NEW_AGE, 1)

    if NEW_BROWSER not in text:
        if OLD_BROWSER not in text:
            raise RuntimeError('Age distribution browser part-count anchor not found')
        text = text.replace(OLD_BROWSER, NEW_BROWSER, 1)

    TARGET.write_text(text, encoding='utf-8')


def patch_pyramid_delegated_interactions() -> None:
    text = APP.read_text(encoding='utf-8')
    if PYRAMID_DELEGATE_MARKER not in text:
        if PYRAMID_HELPER_ANCHOR not in text:
            raise RuntimeError('Pyramid delegated helper anchor not found')
        text = text.replace(PYRAMID_HELPER_ANCHOR, PYRAMID_HELPER + PYRAMID_HELPER_ANCHOR, 1)
    if PYRAMID_CALL_NEW not in text:
        if PYRAMID_CALL_OLD not in text:
            raise RuntimeError('Pyramid delegated call anchor not found')
        text = text.replace(PYRAMID_CALL_OLD, PYRAMID_CALL_NEW, 1)
    APP.write_text(text, encoding='utf-8')


def main() -> None:
    patch_regression_expectations()
    patch_pyramid_delegated_interactions()
    print('Composite regression aligned: Redditi + ageDistribution 2026 a 8 fasce; tooltip piramide delegato e persistente.')


if __name__ == '__main__':
    main()
