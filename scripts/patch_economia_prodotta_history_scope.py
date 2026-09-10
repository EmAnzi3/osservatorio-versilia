#!/usr/bin/env python3
"""Rende ux-history coerente con il perimetro Frame SBS di Economia prodotta.

Il renderer principale inserisce il selettore nel pannello della visualizzazione.
ux-history ricostruisce poi quel pannello per offrire Valore attuale / Storico:
questa patch conserva il nodo del selettore (e i suoi listener) e proietta la
stessa variante Totale / Industria / Servizi anche sulla copia dati usata dal
modulo storico.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "ux-history.js"
MARKER = "OV ECONOMIA PRODOTTA HISTORY SCOPE v1.34.0"

HELPER = r'''
  // OV ECONOMIA PRODOTTA HISTORY SCOPE v1.34.0
  function economicScopeMetric(metric) {
    if (!metric?.meta?.economicScopeSelector || !metric.rows?.some(row => row.economicScopes)) return metric;
    const requested = new URL(location.href).searchParams.get('perimetro') || 'total';
    const scope = ['total','industry','services'].includes(requested) ? requested : 'total';
    const clone = {
      ...metric,
      meta: { ...metric.meta, activeEconomicScope: scope },
      rows: metric.rows.map(row => {
        const variant = row.economicScopes?.[scope] || row.economicScopes?.total;
        if (!variant) return { ...row };
        return {
          ...row,
          value: variant.value,
          formatted: variant.formatted || row.formatted,
          series: variant.series || null,
          benchmarkValue: variant.value,
        };
      }),
      aggregate: metric.aggregate ? { ...metric.aggregate } : metric.aggregate,
    };
    const aggregateVariant = metric.aggregate?.economicScopes?.[scope] || metric.aggregate?.economicScopes?.total;
    if (aggregateVariant && clone.aggregate) {
      clone.aggregate = {
        ...clone.aggregate,
        value: aggregateVariant.value,
        formatted: aggregateVariant.formatted,
        series: aggregateVariant.series || null,
        label: `Versilia · ${aggregateVariant.label || scope}`,
      };
    }
    return clone;
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
        print("Patch ux-history Frame SBS già presente.")
        return

    source = replace_once(
        source,
        "  function selectedMetric(data) {",
        HELPER + "\n  function selectedMetric(data) {",
        "helper perimetro storico",
    )
    source = replace_once(
        source,
        "    return key && data.metrics[key] ? { key, metric: { ...data.metrics[key], key } } : null;",
        "    return key && data.metrics[key] ? { key, metric: economicScopeMetric({ ...data.metrics[key], key }) } : null;",
        "proiezione perimetro nel modulo storico",
    )
    source = replace_once(
        source,
        "    const panel = document.querySelector('.history-panel');\n    if (!panel) return;",
        "    const panel = document.querySelector('.history-panel');\n    if (!panel) return;\n    const economicScopeControl = panel.querySelector(':scope > .economic-scope-control');",
        "conservazione controllo comunale",
    )

    lines = source.splitlines()
    rebuilt: list[str] = []
    panel_rewrites = 0
    for line in lines:
        rebuilt.append(line)
        if "panel.innerHTML =" in line:
            panel_rewrites += 1
            indent = line[: len(line) - len(line.lstrip())]
            rebuilt.append(
                indent
                + "if (economicScopeControl) panel.querySelector(':scope > .panel-title')?.insertAdjacentElement('afterend', economicScopeControl);"
            )
    if panel_rewrites != 2:
        raise RuntimeError(f"ux-history: attese 2 ricostruzioni del pannello comunale, trovate {panel_rewrites}")

    TARGET.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
    print("ux-history allineato al perimetro Frame SBS e selettore preservato nel pannello comunale.")


if __name__ == "__main__":
    main()
