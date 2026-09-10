#!/usr/bin/env python3
"""Inietta il selettore Totale / Industria / Servizi nel runtime canonico OV.

La patch è intenzionalmente minima: non crea un renderer parallelo. Se una metrica
espone `economicScopes`, prima del render viene selezionata la variante richiesta e
i renderer standard continuano a leggere `value`, `series` e `aggregate`.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "app-parts" / "06.txt"
COMPARE_TARGET = ROOT / "assets" / "app-parts" / "03.txt"
MARKER = "/* OV ECONOMIA PRODOTTA SCOPE v1.34.0 */"

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

  function applyEconomicScope(data, requestedScope = economicScopeFromLocation()) {
    const scope = ECONOMIC_SCOPE_KEYS.includes(requestedScope) ? requestedScope : 'total';
    Object.values(data.metrics || {}).forEach(metric => {
      if (!isEconomicScopeMetric(metric)) return;
      metric.rows.forEach(row => {
        const variant = row.economicScopes?.[scope] || row.economicScopes?.total;
        if (!variant) return;
        row.value = variant.value;
        row.formatted = variant.formatted || formatValue(variant.value, metric.meta.unit);
        row.series = variant.series || null;
        row.benchmarkValue = variant.value;
      });
      const aggregateVariant = metric.aggregate?.economicScopes?.[scope] || metric.aggregate?.economicScopes?.total;
      if (aggregateVariant) {
        metric.aggregate.value = aggregateVariant.value;
        metric.aggregate.label = `Versilia · ${aggregateVariant.label || scope}`;
      }
      metric.meta.activeEconomicScope = scope;
    });
    return scope;
  }

  function activeEconomicMetricKey(data) {
    const params = new URLSearchParams(location.search);
    const explicit = params.get('indicatore');
    if (explicit && data.metrics?.[explicit]) return explicit;
    if (pageMetric && data.metrics?.[pageMetric]) return pageMetric;
    if ((pageType === 'compare' || pageType === 'town') && pageTheme && data.themes?.[pageTheme]) {
      return data.themes[pageTheme].metrics?.[0] || '';
    }
    return '';
  }

  function preserveEconomicScopeLinks(scope) {
    if (scope === 'total') return;
    document.querySelectorAll(
      '#app a.bar-row, #app [data-town-link], #app .data-actions a, #app a[href*="/indicatori/"], #app a[href*="confronta/economia"]'
    ).forEach(link => {
      try {
        const url = new URL(link.href, location.href);
        if (url.origin !== location.origin) return;
        url.searchParams.set(ECONOMIC_SCOPE_PARAM, scope);
        link.href = url.href;
      } catch (_) {
        // Collegamento non URL: nessuna modifica.
      }
    });
  }

  function renderEconomicScopePage(data, sourceRegistry, monitorState) {
    if (pageType === 'compare') renderCompare(data);
    else if (pageType === 'town') renderTown(data);
    else if (pageType === 'indicator') renderIndicator(data, sourceRegistry, monitorState);
  }

  function installEconomicScopeControl(data, sourceRegistry, monitorState) {
    document.querySelectorAll('.economic-scope-control').forEach(node => node.remove());

    const metricKey = activeEconomicMetricKey(data);
    const metric = data.metrics?.[metricKey];
    if (!isEconomicScopeMetric(metric)) return;

    const scope = metric.meta.activeEconomicScope || economicScopeFromLocation();
    const wrapper = document.createElement('div');
    wrapper.className = 'metric-switch metric-catalog compact-list economic-scope-control';
    wrapper.setAttribute('aria-label', 'Perimetro Frame SBS Territoriale');
    wrapper.innerHTML = `<section class="metric-group" data-section="frame-sbs-perimetro">
      <div class="metric-group-heading"><strong>Perimetro Frame SBS</strong><span>Stesso indicatore: totale di industria e servizi oppure dettaglio per macrosettore.</span></div>
      <div class="metric-group-buttons" role="tablist" aria-label="Perimetro Frame SBS">
        ${[
          ['total', 'Totale'],
          ['industry', 'Industria'],
          ['services', 'Servizi']
        ].map(([key, label]) => `<button type="button" role="tab" data-economic-scope="${key}" class="${key === scope ? 'active' : ''}" aria-selected="${key === scope}" tabindex="${key === scope ? '0' : '-1'}">${label}</button>`).join('')}
      </div>
    </section>`;

    const catalog = document.querySelector('#app .metric-catalog');
    if (catalog) {
      catalog.insertAdjacentElement('afterend', wrapper);
    } else {
      const heading = document.querySelector('#app h1');
      const host = heading?.closest('section');
      if (host) host.insertAdjacentElement('afterend', wrapper);
      else document.getElementById('app')?.prepend(wrapper);
    }

    wrapper.querySelectorAll('[data-economic-scope]').forEach(button => {
      button.addEventListener('click', () => {
        const next = button.dataset.economicScope;
        const url = new URL(location.href);
        if (next === 'total') url.searchParams.delete(ECONOMIC_SCOPE_PARAM);
        else url.searchParams.set(ECONOMIC_SCOPE_PARAM, next);
        history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
        applyEconomicScope(data, next);
        renderEconomicScopePage(data, sourceRegistry, monitorState);
        queueMicrotask(() => installEconomicScopeControl(data, sourceRegistry, monitorState));
      });
    });

    const benchmark = document.getElementById('compare-benchmark');
    if (benchmark && pageType === 'compare') benchmark.hidden = scope !== 'total';

    preserveEconomicScopeLinks(scope);
  }

  function observeEconomicScopeControl(data, sourceRegistry, monitorState) {
    if (!app) return;
    const metric = data.metrics?.[activeEconomicMetricKey(data)];
    if (!isEconomicScopeMetric(metric)) return;
    if (app.dataset.economicScopeObserver === '1') return;
    app.dataset.economicScopeObserver = '1';
    let pending = false;
    const sync = () => {
      if (pending) return;
      pending = true;
      queueMicrotask(() => {
        pending = false;
        installEconomicScopeControl(data, sourceRegistry, monitorState);
      });
    };
    new MutationObserver(sync).observe(app, { childList: true, subtree: false });
    sync();
  }
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: attesa 1 occorrenza, trovate {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        print("Patch Economia prodotta runtime già presente.")
        return

    source = replace_once(
        source,
        "  function installSearch(data) {",
        INSERT + "\n  function installSearch(data) {",
        "inserimento funzioni scope",
    )
    source = replace_once(
        source,
        "      mountShell(data);\n",
        "      applyEconomicScope(data);\n      mountShell(data);\n",
        "hydration scope prima del render",
    )

    anchor = "      if (['compare', 'town'].includes(pageType)) installEnvironmentClimateCoherence(data);"
    source = replace_once(
        source,
        anchor,
        anchor + "\n      observeEconomicScopeControl(data, sourceRegistry, monitorState);",
        "installazione observer scope dopo dispatch canonico",
    )

    TARGET.write_text(source, encoding="utf-8")

    compare_source = COMPARE_TARGET.read_text(encoding="utf-8")
    compare_old = "      history.replaceState(history.state, '', `?indicatore=${encodeURIComponent(key)}`);"
    compare_new = "      const nextParams = new URLSearchParams(location.search);\n      nextParams.set('indicatore', key);\n      history.replaceState(history.state, '', `?${nextParams.toString()}`);"
    if compare_new not in compare_source:
        compare_source = replace_once(
            compare_source, compare_old, compare_new, "persistenza query perimetro nel confronto"
        )
        COMPARE_TARGET.write_text(compare_source, encoding="utf-8")

    print("Selettore Frame SBS Totale / Industria / Servizi iniettato nel runtime canonico.")


if __name__ == "__main__":
    main()
