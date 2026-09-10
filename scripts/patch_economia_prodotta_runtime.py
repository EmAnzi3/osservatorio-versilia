#!/usr/bin/env python3
"""Inietta il selettore locale Totale / Industria / Servizi per Economia prodotta.

Il perimetro Frame SBS è una dimensione della singola metrica, non un indicatore:
- viene applicato soltanto alla metrica Frame attualmente renderizzata;
- il controllo vive nel pannello della visualizzazione;
- sparisce e il parametro URL viene rimosso quando si passa a metriche non Frame;
- i renderer canonici restano gli unici responsabili di grafici, schede e tabelle.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPARE_TARGET = ROOT / "assets" / "app-parts" / "03.txt"
INDICATOR_TARGET = ROOT / "assets" / "app-parts" / "05.txt"
RUNTIME_TARGET = ROOT / "assets" / "app-parts" / "06.txt"
VISUAL_TARGET = ROOT / "assets" / "visual-grammar.js"
MARKER = "/* OV ECONOMIA PRODOTTA SCOPE v1.34.0 */"
VISUAL_MARKER = "/* OV ECONOMIA PRODOTTA VISUAL SCOPE v1.34.0 */"

INSERT = r'''
  /* OV ECONOMIA PRODOTTA SCOPE v1.34.0 */
  const ECONOMIC_SCOPE_PARAM = 'perimetro';
  const ECONOMIC_SCOPE_KEYS = ['total', 'industry', 'services'];

  function economicScopeFromLocation() {
    const raw = new URLSearchParams(location.search).get(ECONOMIC_SCOPE_PARAM) || 'total';
    return ECONOMIC_SCOPE_KEYS.includes(raw) ? raw : 'total';
  }

  function isEconomicScopeMetric(metric) {
    return Boolean(metric?.meta?.economicScopeSelector && metric?.rows?.some(row => row.economicScopes));
  }

  function scopedEconomicMetric(metric, requestedScope = economicScopeFromLocation()) {
    if (!isEconomicScopeMetric(metric)) return { metric, scope: 'total' };
    const scope = ECONOMIC_SCOPE_KEYS.includes(requestedScope) ? requestedScope : 'total';
    const rows = metric.rows.map(row => {
      const variant = row.economicScopes?.[scope] || row.economicScopes?.total;
      if (!variant) return { ...row };
      return {
        ...row,
        value: variant.value,
        formatted: variant.formatted || formatValue(variant.value, metric.meta.unit),
        series: variant.series || null,
        benchmarkValue: variant.value,
      };
    });
    const aggregateVariant = metric.aggregate?.economicScopes?.[scope] || metric.aggregate?.economicScopes?.total;
    const aggregate = metric.aggregate ? {
      ...metric.aggregate,
      ...(aggregateVariant ? {
        value: aggregateVariant.value,
        formatted: aggregateVariant.formatted,
        series: aggregateVariant.series || null,
        label: `Versilia · ${aggregateVariant.label || scope}`,
      } : {}),
    } : metric.aggregate;
    return {
      scope,
      metric: {
        ...metric,
        meta: { ...metric.meta, activeEconomicScope: scope },
        rows,
        aggregate,
      },
    };
  }

  function clearEconomicScopeParam() {
    const url = new URL(location.href);
    if (!url.searchParams.has(ECONOMIC_SCOPE_PARAM)) return;
    url.searchParams.delete(ECONOMIC_SCOPE_PARAM);
    history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
  }

  function economicScopeData(data, metricKey, requestedScope = economicScopeFromLocation()) {
    const original = data.metrics?.[metricKey];
    if (!isEconomicScopeMetric(original)) {
      clearEconomicScopeParam();
      return { data, metric: original, scope: 'total' };
    }
    const scoped = scopedEconomicMetric(original, requestedScope);
    return {
      scope: scoped.scope,
      metric: scoped.metric,
      data: { ...data, metrics: { ...data.metrics, [metricKey]: scoped.metric } },
    };
  }

  function setEconomicScopeParam(scope) {
    const next = ECONOMIC_SCOPE_KEYS.includes(scope) ? scope : 'total';
    const url = new URL(location.href);
    if (next === 'total') url.searchParams.delete(ECONOMIC_SCOPE_PARAM);
    else url.searchParams.set(ECONOMIC_SCOPE_PARAM, next);
    history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
    return next;
  }

  function economicScopeControlMarkup(scope) {
    return `<div class="compare-chart-toolbar economic-scope-control">
      <div><span class="overline">Perimetro Frame SBS</span><small>Stesso indicatore, dettaglio per macrosettore</small></div>
      <label class="compare-choice-select economic-scope-select"><span>Perimetro</span>
        <select data-economic-scope aria-label="Perimetro Frame SBS">
        ${[
          ['total', 'Totale'],
          ['industry', 'Industria'],
          ['services', 'Servizi']
        ].map(([key, label]) => `<option value="${key}" ${key === scope ? 'selected' : ''}>${label}</option>`).join('')}
        </select>
      </label>
    </div>`;
  }

  function syncEconomicScopeLinks(data, metricKey, scope) {
    const metric = data.metrics?.[metricKey];
    const active = isEconomicScopeMetric(metric) && scope !== 'total';
    document.querySelectorAll('#app a[href]').forEach(link => {
      const raw = link.getAttribute('href');
      if (!raw || raw.startsWith('#') || raw.startsWith('mailto:')) return;
      try {
        const url = new URL(link.href, location.href);
        if (url.origin !== location.origin) return;
        const targetKey = url.searchParams.get('indicatore');
        const targetMetric = targetKey ? data.metrics?.[targetKey] : null;
        const isIndicatorDetail = link.matches('.data-actions a[href*="/indicatori/"], .indicator-hero-actions a[href*="/confronta/"]');
        const shouldCarry = active && (
          (targetMetric && isEconomicScopeMetric(targetMetric)) ||
          (isIndicatorDetail && isEconomicScopeMetric(metric))
        );
        if (shouldCarry) url.searchParams.set(ECONOMIC_SCOPE_PARAM, scope);
        else url.searchParams.delete(ECONOMIC_SCOPE_PARAM);
        link.href = `${url.pathname}${url.search}${url.hash}`;
      } catch (_) {
        // Collegamento non interpretabile: non viene modificato.
      }
    });
  }
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: attesa 1 occorrenza, trovate {count}")
    return source.replace(old, new, 1)


def patch_runtime_helpers() -> None:
    source = RUNTIME_TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        return
    source = replace_once(
        source,
        "  function installSearch(data) {",
        INSERT + "\n  function installSearch(data) {",
        "helper scope",
    )
    RUNTIME_TARGET.write_text(source, encoding="utf-8")


def patch_visual_grammar() -> None:
    source = VISUAL_TARGET.read_text(encoding="utf-8")
    if VISUAL_MARKER in source:
        return
    helper = r'''
  /* OV ECONOMIA PRODOTTA VISUAL SCOPE v1.34.0 */
  function metricForEconomicScope(metric) {
    if (!metric?.meta?.economicScopeSelector || !metric.rows?.some(row => row.economicScopes)) return metric;
    const requested = new URLSearchParams(location.search).get('perimetro') || 'total';
    const scope = ['total','industry','services'].includes(requested) ? requested : 'total';
    const aggregateVariant = metric.aggregate?.economicScopes?.[scope] || metric.aggregate?.economicScopes?.total;
    return {
      ...metric,
      meta: { ...metric.meta, activeEconomicScope: scope },
      rows: metric.rows.map(row => {
        const variant = row.economicScopes?.[scope] || row.economicScopes?.total;
        return variant ? { ...row, value: variant.value, formatted: variant.formatted || row.formatted, series: variant.series || null, benchmarkValue: variant.value } : { ...row };
      }),
      aggregate: metric.aggregate ? {
        ...metric.aggregate,
        ...(aggregateVariant ? { value: aggregateVariant.value, formatted: aggregateVariant.formatted, series: aggregateVariant.series || null, label: `Versilia · ${aggregateVariant.label || scope}` } : {}),
      } : metric.aggregate,
    };
  }
'''
    source = replace_once(source, "  function enhanceComparison(container) {", helper + "\n  function enhanceComparison(container) {", "helper scope grammatica visiva")
    source = replace_once(
        source,
        "    const metric = data.metrics?.[metricKey];\n    if (!metric) return;\n\n    const normalized = normalizedFor(container);",
        "    const metric = metricForEconomicScope(data.metrics?.[metricKey]);\n    if (!metric) return;\n\n    const normalized = normalizedFor(container);",
        "scope grammatica visiva",
    )
    VISUAL_TARGET.write_text(source, encoding="utf-8")


def patch_compare_and_town() -> None:
    source = COMPARE_TARGET.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {\n    const metric = data.metrics[metricKey];",
        "  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {\n    const economicContext = economicScopeData(data, metricKey);\n    data = economicContext.data;\n    const metric = economicContext.metric;\n    const economicScope = economicContext.scope;",
        "scope locale nel confronto",
    )
    source = replace_once(
        source,
        "    const chartScaleControls = controls;\n",
        "    const chartScaleControls = controls;\n    const economicScopeControls = isEconomicScopeMetric(metric) ? economicScopeControlMarkup(economicScope) : '';\n",
        "markup scope nel confronto",
    )
    source = replace_once(
        source,
        "      bars.innerHTML = compositeType ? `<div class=\"topic-bars composite-topic-bars\">${compositeCompareMarkup(data,metricKey,view)}</div>` : `<div class=\"topic-bars\">${chartScaleControls ? `<div class=\"compare-chart-toolbar scale-toolbar\">${chartScaleControls}</div>` : ''}<div class=\"comparison-bars\">${barRows(data,metricKey,{normalized})}</div></div>`;",
        "      bars.innerHTML = compositeType ? `<div class=\"topic-bars composite-topic-bars\">${compositeCompareMarkup(data,metricKey,view)}</div>` : `<div class=\"topic-bars\">${economicScopeControls}${chartScaleControls ? `<div class=\"compare-chart-toolbar scale-toolbar\">${chartScaleControls}</div>` : ''}<div class=\"comparison-bars\">${barRows(data,metricKey,{normalized})}</div></div>`;",
        "selettore dentro il pannello grafico",
    )
    scope_delegate_anchor = """    } else {
      bars.onclick = null;
      bars.onchange = null;
    }

    if (demographicPyramid) {"""
    scope_delegate_new = """    } else {
      bars.onclick = null;
      bars.onchange = null;
    }

    if (isEconomicScopeMetric(metric)) {
      const baseChange = bars.onchange;
      bars.onchange = event => {
        const scopeSelect = event.target.closest('select[data-economic-scope]');
        if (scopeSelect && bars.contains(scopeSelect)) {
          setEconomicScopeParam(scopeSelect.value);
          renderCompareMetric(data,themeKey,metricKey,normalized,view);
          return;
        }
        if (typeof baseChange === 'function') baseChange.call(bars,event);
      };
    }

    if (demographicPyramid) {"""
    source = replace_once(source, scope_delegate_anchor, scope_delegate_new, "delega scope confronto")
    source = replace_once(
        source,
        "    benchmark.innerHTML = (metricKey.startsWith('slowMobility') || (metric.meta.compositeType && compositeType !== 'sexBreakdown')) ? '' : benchmarkMarkup(benchmarkMetric,aggregate,unit,null);",
        "    benchmark.innerHTML = (isEconomicScopeMetric(metric) && economicScope !== 'total') || metricKey.startsWith('slowMobility') || (metric.meta.compositeType && compositeType !== 'sexBreakdown') ? '' : benchmarkMarkup(benchmarkMetric,aggregate,unit,null);\n    syncEconomicScopeLinks(data, metricKey, economicScope);",
        "benchmark e link confronto",
    )

    source = replace_once(
        source,
        "      history.replaceState(history.state, '', `?indicatore=${encodeURIComponent(key)}`);",
        "      const nextParams = new URLSearchParams(location.search);\n      nextParams.set('indicatore', key);\n      history.replaceState(history.state, '', `?${nextParams.toString()}`);",
        "persistenza query nel confronto",
    )

    source = replace_once(
        source,
        "  function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect) {\n    const theme = data.themes[themeKey];\n    const metric = data.metrics[metricKey];\n    const row = metric.rows.find(r => r.code === town.code);",
        "  function renderTownMetric(data, town, themeKey, metricKey, onMetricSelect) {\n    const theme = data.themes[themeKey];\n    const economicContext = economicScopeData(data, metricKey);\n    data = economicContext.data;\n    const metric = economicContext.metric;\n    const economicScope = economicContext.scope;\n    const row = metric.rows.find(r => r.code === town.code);",
        "scope locale nella scheda comunale",
    )
    source = replace_once(
        source,
        """      <section class="history-panel ${composite ? 'composite-history-panel' : ''}"><div class="panel-title"><div><span class="overline" data-financial-panel-overline>${html(panelOverline)}</span><h3 data-financial-panel-title>${html(panelTitle)}</h3></div><a class="source-pill" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${html(metric.meta.source)} ↗</a></div>
        ${extractiveProductionHistory ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : (composite ? `<div class="composite-fixed-detail">${compositeTownMarkup(metric, row)}</div>` : (historical ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : `<div class="comparison-bars">${barRows(data, metricKey, { selectedTown: normalize(town.name).replaceAll(' ', '-') })}</div>`))}</section>""",
        """      <section class="history-panel ${composite ? 'composite-history-panel' : ''}"><div class="panel-title"><div><span class="overline" data-financial-panel-overline>${html(panelOverline)}</span><h3 data-financial-panel-title>${html(panelTitle)}</h3></div><a class="source-pill" href="${html(metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${html(metric.meta.source)} ↗</a></div>
        ${isEconomicScopeMetric(metric) ? economicScopeControlMarkup(economicScope) : ''}
        ${extractiveProductionHistory ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : (composite ? `<div class="composite-fixed-detail">${compositeTownMarkup(metric, row)}</div>` : (historical ? seriesChart(row.series, metric.meta.unit, `${metric.meta.label} a ${town.name}`) : `<div class="comparison-bars">${barRows(data, metricKey, { selectedTown: normalize(town.name).replaceAll(' ', '-') })}</div>`))}</section>""",
        "selettore dentro lo storico comunale",
    )
    town_benchmark_variants = (
        (
            """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}""",
            """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType) || (isEconomicScopeMetric(metric) && economicScope !== 'total')) ? '' : townBenchmarkMarkup(metric, row, town)}""",
        ),
        (
            """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}""",
            """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType) || (isEconomicScopeMetric(metric) && economicScope !== 'total')) ? '' : townBenchmarkMarkup(metric, row, town)}""",
        ),
    )
    matched = [(old, new) for old, new in town_benchmark_variants if old in source]
    if len(matched) != 1:
        raise RuntimeError(f"benchmark comunale omogeneo: attesa 1 variante, trovate {len(matched)}")
    source = source.replace(matched[0][0], matched[0][1], 1)
    source = replace_once(
        source,
        "    const tablist = container.querySelector('[role=\"tablist\"]');\n    installTablist(tablist, onMetricSelect);",
        """    const tablist = container.querySelector('[role="tablist"]');
    installTablist(tablist, onMetricSelect);
    container.querySelectorAll('select[data-economic-scope]').forEach(select => select.addEventListener('change', () => {
      setEconomicScopeParam(select.value);
      renderTownMetric(data,town,themeKey,metricKey,onMetricSelect);
    }));
    syncEconomicScopeLinks(data, metricKey, economicScope);""",
        "eventi scope comunale",
    )

    COMPARE_TARGET.write_text(source, encoding="utf-8")


def patch_indicator() -> None:
    source = INDICATOR_TARGET.read_text(encoding="utf-8")
    source = replace_once(
        source,
        "  function renderIndicator(data, registry, monitorState) {\n    const metric = data.metrics[pageMetric];\n    if (!metric) return renderNotFound();",
        "  function renderIndicator(data, registry, monitorState) {\n    if (!data.metrics[pageMetric]) return renderNotFound();\n    const economicContext = economicScopeData(data, pageMetric);\n    data = economicContext.data;\n    const metric = economicContext.metric;\n    const economicScope = economicContext.scope;",
        "scope nella scheda indicatore",
    )
    source = replace_once(
        source,
        """      <section class="indicator-current page-width" aria-labelledby="indicator-current-title"><div class="section-heading"><div><span class="overline">Valori comunali</span><h2 id="indicator-current-title" data-financial-indicator-title>${html(financialProfile ? `${initialFinancialReading.code} · ${initialFinancialReading.label}` : 'Il dato nei sette comuni')}</h2></div><p data-financial-indicator-description>${html(financialProfile ? `${initialFinancialReading.description} I Comuni sono ordinati per valore per facilitare il confronto: nessuna graduatoria e nessun giudizio di merito.` : 'Ordine alfabetico: nessuna graduatoria e nessun giudizio di merito.')}</p></div>
        <div class="indicator-current-layout">""",
        """      <section class="indicator-current page-width" aria-labelledby="indicator-current-title"><div class="section-heading"><div><span class="overline">Valori comunali</span><h2 id="indicator-current-title" data-financial-indicator-title>${html(financialProfile ? `${initialFinancialReading.code} · ${initialFinancialReading.label}` : 'Il dato nei sette comuni')}</h2></div><p data-financial-indicator-description>${html(financialProfile ? `${initialFinancialReading.description} I Comuni sono ordinati per valore per facilitare il confronto: nessuna graduatoria e nessun giudizio di merito.` : 'Ordine alfabetico: nessuna graduatoria e nessun giudizio di merito.')}</p></div>
        ${isEconomicScopeMetric(metric) ? economicScopeControlMarkup(economicScope) : ''}
        <div class="indicator-current-layout">""",
        "selettore nella scheda indicatore",
    )
    indicator_benchmark_variants = (
        (
            """      <section class="indicator-benchmark page-width">${financialProfile ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>""",
            """      <section class="indicator-benchmark page-width">${(financialProfile || (isEconomicScopeMetric(metric) && economicScope !== 'total')) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>""",
        ),
        (
            """      <section class="indicator-benchmark page-width">${(financialProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>""",
            """      <section class="indicator-benchmark page-width">${(financialProfile || hydroRisk || (isEconomicScopeMetric(metric) && economicScope !== 'total')) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>""",
        ),
    )
    matched = [(old, new) for old, new in indicator_benchmark_variants if old in source]
    if len(matched) != 1:
        raise RuntimeError(f"benchmark scheda indicatore: attesa 1 variante, trovate {len(matched)}")
    source = source.replace(matched[0][0], matched[0][1], 1)
    source = replace_once(
        source,
        "    document.querySelector('[data-share]')?.addEventListener('click', event => shareCurrentPage(event.currentTarget));",
        """    document.querySelectorAll('.indicator-current select[data-economic-scope]').forEach(select => select.addEventListener('change', () => {
      setEconomicScopeParam(select.value);
      renderIndicator(data, registry, monitorState);
    }));
    syncEconomicScopeLinks(data, pageMetric, economicScope);
    document.querySelector('[data-share]')?.addEventListener('click', event => shareCurrentPage(event.currentTarget));""",
        "eventi scope scheda indicatore",
    )
    INDICATOR_TARGET.write_text(source, encoding="utf-8")


def main() -> None:
    patch_runtime_helpers()
    patch_visual_grammar()
    patch_compare_and_town()
    patch_indicator()
    print("Selettore Frame SBS reso locale alla visualizzazione canonica (confronto, comune, indicatore).")


if __name__ == "__main__":
    main()
