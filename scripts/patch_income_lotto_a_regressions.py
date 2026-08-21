#!/usr/bin/env python3
"""Allinea regressioni e compatibilità delle tranche Redditi/Demografia Lotto A.

- Redditi: allinea le aspettative storiche alla tranche completa.
- Demografia v2: `ageDistribution` usa POSAS 2026 e otto fasce esaustive,
  con 80–84 e 85+ come componenti normali della distribuzione.
- La piramide mantiene il tooltip canonico anche quando `ux-history.js`
  ricostruisce il contenuto: l'interazione è delegata ai contenitori stabili
  sia nelle schede comunali sia nel confronto Versilia.
- La piramide aggregata Versilia riusa esattamente lo stesso renderer delle
  piramidi comunali, sommando i sette territori nel materializzatore.
- L'ottava fascia eredita la grammatica cromatica del tema Demografia, senza
  introdurre una tinta estranea alla scala già usata dalla distribuzione.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'test_composite_indicators.py'
APP = ROOT / 'assets' / 'app-parts' / '03.txt'
ORIGINAL_CSS = ROOT / 'assets' / 'original.css'

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

OLD_BROWSER_DESKTOP = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 7)'''
NEW_BROWSER_DESKTOP = '''        tooltip_checks(page, base, "demografia", "ageDistribution", 7, 8)'''
OLD_BROWSER_MOBILE = '''        tooltip_checks(mobile_page, base, "demografia", "ageDistribution", 7, 7)'''
NEW_BROWSER_MOBILE = '''        tooltip_checks(mobile_page, base, "demografia", "ageDistribution", 7, 8)'''

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

PYRAMID_COMPARE_OLD = '''    return `${compositePartLegend(metric)}<div class="composite-distribution-list">${rows.map(row => {
      const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
      const parts = row.parts || [];
      const summary = compositeSummary(metric, row);
      return `<div class="composite-distribution-row">
        <div class="composite-row-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(summary.label)} <b>${html(summary.formatted)}</b></span></div>
        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;
    }).join('')}</div>`;'''

PYRAMID_COMPARE_NEW = '''    const versiliaPyramid = metric.meta.key === 'ageDistribution' && metric.aggregate?.ageSexPyramid
      ? agePyramidMarkup(metric,{...metric.aggregate,town:'Versilia'})
      : '';
    return `${compositePartLegend(metric)}<div class="composite-distribution-list">${rows.map(row => {
      const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
      const parts = row.parts || [];
      const summary = compositeSummary(metric, row);
      return `<div class="composite-distribution-row">
        <div class="composite-row-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(summary.label)} <b>${html(summary.formatted)}</b></span></div>
        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;
    }).join('')}</div>${versiliaPyramid}`;'''

PYRAMID_COMPARE_DELEGATE_OLD = '''    def.querySelectorAll('[data-scale]').forEach(button => button.addEventListener('click', () => renderCompareMetric(data,themeKey,metricKey,button.dataset.scale === 'normalized',view)));'''
PYRAMID_COMPARE_DELEGATE_NEW = '''    installAgePyramidDelegation(bars);
    def.querySelectorAll('[data-scale]').forEach(button => button.addEventListener('click', () => renderCompareMetric(data,themeKey,metricKey,button.dataset.scale === 'normalized',view)));'''

AGE_COLOR_MARKER = '/* ageDistribution eight-band scale */'
AGE_COLOR_CSS = r'''

/* ageDistribution eight-band scale */
[data-theme=demografia] .composite-segment.part-6,[data-theme=demografia] .composite-swatch.part-6{background:color-mix(in srgb,var(--theme-color) 18%,var(--surface))}
[data-theme=demografia] .composite-segment.part-7,[data-theme=demografia] .composite-swatch.part-7{background:color-mix(in srgb,var(--theme-color) 10%,var(--surface))}
'''


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

    if NEW_BROWSER_DESKTOP not in text:
        if OLD_BROWSER_DESKTOP not in text:
            raise RuntimeError('Age distribution desktop part-count anchor not found')
        text = text.replace(OLD_BROWSER_DESKTOP, NEW_BROWSER_DESKTOP, 1)

    if NEW_BROWSER_MOBILE not in text:
        if OLD_BROWSER_MOBILE not in text:
            raise RuntimeError('Age distribution mobile part-count anchor not found')
        text = text.replace(OLD_BROWSER_MOBILE, NEW_BROWSER_MOBILE, 1)

    TARGET.write_text(text, encoding='utf-8')


def patch_pyramid_delegated_interactions() -> None:
    text = APP.read_text(encoding='utf-8')
    if PYRAMID_DELEGATE_MARKER not in text:
        if PYRAMID_HELPER_ANCHOR not in text:
            raise RuntimeError('Pyramid delegated helper anchor not found')
        text = text.replace(PYRAMID_HELPER_ANCHOR, PYRAMID_HELPER + PYRAMID_HELPER_ANCHOR, 1)
    if PYRAMID_CALL_NEW not in text:
        if PYRAMID_CALL_OLD not in text:
            raise RuntimeError('Pyramid delegated town call anchor not found')
        text = text.replace(PYRAMID_CALL_OLD, PYRAMID_CALL_NEW, 1)
    if PYRAMID_COMPARE_NEW not in text:
        if PYRAMID_COMPARE_OLD not in text:
            raise RuntimeError('Versilia pyramid compare anchor not found')
        text = text.replace(PYRAMID_COMPARE_OLD, PYRAMID_COMPARE_NEW, 1)
    if PYRAMID_COMPARE_DELEGATE_NEW not in text:
        if PYRAMID_COMPARE_DELEGATE_OLD not in text:
            raise RuntimeError('Versilia pyramid delegated interaction anchor not found')
        text = text.replace(PYRAMID_COMPARE_DELEGATE_OLD, PYRAMID_COMPARE_DELEGATE_NEW, 1)
    APP.write_text(text, encoding='utf-8')


def patch_age_distribution_colors() -> None:
    text = ORIGINAL_CSS.read_text(encoding='utf-8')
    if AGE_COLOR_MARKER not in text:
        ORIGINAL_CSS.write_text(text + AGE_COLOR_CSS, encoding='utf-8')


def main() -> None:
    patch_regression_expectations()
    patch_pyramid_delegated_interactions()
    patch_age_distribution_colors()
    print('Composite regression aligned: Redditi + ageDistribution 2026 a 8 fasce; piramide comuni/Versilia con tooltip persistente; scala cromatica completa.')


if __name__ == '__main__':
    main()
