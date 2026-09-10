#!/usr/bin/env python3
"""Allinea la UX storica canonica al perimetro Frame SBS selezionato."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "ux-history.js"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: attesa 1 occorrenza, trovate {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")

    source = replace_once(
        source,
        """  function selectedMetric(data) {
    const urlKey = new URL(location.href).searchParams.get('indicatore');
    const activeKey = document.querySelector('[data-metric].active')?.dataset.metric || '';
    const key = urlKey && data.metrics[urlKey] ? urlKey : activeKey;
    return key && data.metrics[key] ? { key, metric: { ...data.metrics[key], key } } : null;
  }
""",
        """  function selectedMetric(data) {
    const url = new URL(location.href);
    const urlKey = url.searchParams.get('indicatore');
    const activeKey = document.querySelector('[data-metric].active')?.dataset.metric || '';
    const key = urlKey && data.metrics[urlKey] ? urlKey : activeKey;
    if (!key || !data.metrics[key]) return null;
    const original = data.metrics[key];
    let metric = { ...original, key };
    if (original.meta?.economicScopeSelector && original.rows?.some(row => row.economicScopes)) {
      const requested = url.searchParams.get('perimetro') || 'total';
      const scope = ['total','industry','services'].includes(requested) ? requested : 'total';
      metric = {
        ...metric,
        meta: { ...original.meta, activeEconomicScope: scope },
        rows: original.rows.map(row => {
          const variant = row.economicScopes?.[scope] || row.economicScopes?.total;
          return variant ? { ...row, value: variant.value, formatted: variant.formatted || row.formatted, series: variant.series || null, benchmarkValue: variant.value } : { ...row };
        }),
        aggregate: original.aggregate ? { ...original.aggregate } : original.aggregate,
      };
      const aggregateVariant = original.aggregate?.economicScopes?.[scope] || original.aggregate?.economicScopes?.total;
      if (aggregateVariant && metric.aggregate) {
        metric.aggregate.value = aggregateVariant.value;
        metric.aggregate.formatted = aggregateVariant.formatted;
        metric.aggregate.label = `Versilia · ${aggregateVariant.label || scope}`;
        metric.aggregate.series = aggregateVariant.series || null;
      }
    }
    return { key, metric };
  }
""",
        "scope Frame nella UX storica",
    )

    source = replace_once(
        source,
        "    const existingShell = panel.querySelector('.ux-view-shell');\n",
        "    const existingShell = panel.querySelector('.ux-view-shell');\n    const economicScopeControl = panel.querySelector(':scope > .economic-scope-control');\n",
        "preserva controllo Frame",
    )

    source = replace_once(
        source,
        """    panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>Valore attuale e andamento</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}${fixedDetail}`;
    wireShell(panel.querySelector('.ux-view-shell'), 'ov-town-view', selectedTown, false);
""",
        """    panel.innerHTML = `<div class="panel-title"><div><span class="overline">Confronto dell’indicatore</span><h3>Valore attuale e andamento</h3></div><a class="source-pill" href="${toolkit.escapeHtml(selected.metric.sourceUrl)}" target="_blank" rel="noreferrer">Fonte ${toolkit.escapeHtml(selected.metric.meta.source)} ↗</a></div>${toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)}${fixedDetail}`;
    if (economicScopeControl) panel.querySelector(':scope > .panel-title')?.insertAdjacentElement('afterend', economicScopeControl);
    wireShell(panel.querySelector('.ux-view-shell'), 'ov-town-view', selectedTown, false);
""",
        "reinserimento controllo Frame",
    )

    TARGET.write_text(source, encoding="utf-8")
    print("UX storica allineata al perimetro Frame SBS selezionato.")


if __name__ == "__main__":
    main()
