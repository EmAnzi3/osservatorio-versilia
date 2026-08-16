#!/usr/bin/env python3
"""Add a comparable inflation reference to the income-vs-inflation history.

The current indicator remains the validated real-income change. Historical
views instead put nominal taxable-income growth and NIC Italia on the same
2016=0% scale, so the distance between the two can be read year by year.
The patch is materialized only by the economy draft workflow.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/site-data.json'
UX = ROOT / 'assets/ux-history.js'
CSS = ROOT / 'assets/ux-experiment.css'
KEY = 'incomeVsInflation'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Patch anchor missing: {label}')
    return text.replace(old, new, 1)


def patch_data() -> None:
    data = load(DATA)
    metric = data['metrics'][KEY]
    income = data['metrics']['income']
    context = data.get('incomeInflationContext') or {}

    years = [int(year) for year in context.get('years', [])]
    prices = [float(value) for value in context.get('priceIndex', [])]
    if years != list(range(2016, 2025)) or len(prices) != len(years):
        raise RuntimeError('Serie NIC Italia 2016–2024 non disponibile o incoerente')

    inflation_values = [round(value - 100.0, 4) for value in prices]
    reference_label = context.get('priceLabel') or 'NIC Italia'
    metric['inflationSeries'] = {
        'label': f'Inflazione · {reference_label}',
        'years': years,
        'values': inflation_values,
    }
    metric['historyPresentation'] = {
        'type': 'nominal-income-vs-inflation',
        'baseYear': 2016,
        'baseLabel': '2016 = 0%',
        'note': (
            'Nello storico il reddito imponibile nominale di ciascun Comune e il NIC Italia sono riportati '
            'alla stessa base 2016 = 0%. La distanza tra le linee mostra anno per anno se i redditi crescono '
            'più o meno dei prezzi; il valore sintetico dell’indicatore resta la variazione reale già calcolata.'
        ),
    }

    income_rows = {row['slug']: row for row in income['rows']}
    for row in metric['rows']:
        source = income_rows.get(row['slug'])
        if not source:
            raise RuntimeError(f"Serie reddito mancante per {row['town']}")
        source_series = source.get('longSeries') or source.get('series') or {}
        source_map = {
            int(year): float(value)
            for year, value in zip(source_series.get('years', []), source_series.get('values', []))
            if value is not None
        }
        missing = [year for year in years if year not in source_map]
        if missing:
            raise RuntimeError(f"Reddito nominale incompleto per {row['town']}: {missing}")
        base = source_map[years[0]]
        if base <= 0:
            raise RuntimeError(f"Base reddito non valida per {row['town']}")
        nominal_changes = [round(source_map[year] / base * 100.0 - 100.0, 4) for year in years]
        row['nominalSeries'] = {
            'label': 'Reddito imponibile nominale',
            'years': years,
            'values': nominal_changes,
        }

    if len(metric['rows']) != 7 or any(row['nominalSeries']['values'][0] != 0 for row in metric['rows']):
        raise RuntimeError('Serie nominali comunali non coerenti con la base 2016')
    if metric['inflationSeries']['values'][0] != 0:
        raise RuntimeError('Serie inflazione non coerente con la base 2016')

    save(DATA, data)


def patch_history_js() -> None:
    text = UX.read_text(encoding='utf-8')

    old_history_metric = """  function historyMetric(metric) {
    if (metric?.meta?.key !== 'income' || !metric.rows?.some(row => row.longSeries?.years?.length)) return metric;
    return { ...metric, meta:{...metric.meta,label:metric.meta.longHistoryLabel || 'Reddito imponibile medio · serie lunga',unit:'currency'}, rows:metric.rows.map(row=>({...row,series:row.longSeries || row.series})) };
  }
"""
    new_history_metric = """  function historyMetric(metric) {
    if (metric?.meta?.key === 'income' && metric.rows?.some(row => row.longSeries?.years?.length)) {
      return { ...metric, meta:{...metric.meta,label:metric.meta.longHistoryLabel || 'Reddito imponibile medio · serie lunga',unit:'currency'}, rows:metric.rows.map(row=>({...row,series:row.longSeries || row.series})) };
    }
    if (metric?.meta?.key === 'incomeVsInflation' && metric.inflationSeries?.years?.length) {
      const reference = metric.inflationSeries;
      return {
        ...metric,
        meta: { ...metric.meta, label: 'Redditi nominali vs inflazione', unit: 'percent' },
        rows: [
          ...metric.rows.map(row => ({ ...row, series: row.nominalSeries || row.series })),
          {
            town: reference.label || 'Inflazione · NIC Italia',
            slug: 'inflazione-nic-italia',
            value: Number(reference.values?.at(-1)),
            formatted: '',
            series: reference,
            normalized: null,
            benchmarkValue: Number(reference.values?.at(-1)),
          },
        ],
      };
    }
    return metric;
  }

  function historyMarkup(metric, series, selectedTown) {
    const markup = toolkit.historicalChartMarkup(metric, series, selectedTown);
    if (metric?.meta?.key !== 'incomeVsInflation' || !metric.inflationSeries?.years?.length) return markup;
    const referenceLabel = toolkit.escapeHtml(metric.inflationSeries.label || 'Inflazione · NIC Italia');
    return markup
      .replace(
        'Una linea per comune; sono mostrati solo gli anni disponibili per tutti e sette.',
        'Redditi nominali e inflazione sono riportati alla stessa base 2016 = 0%. La distanza mostra se i redditi crescono più o meno dei prezzi.'
      )
      .replace(
        /<g class="ux-series-group [^"]*" data-history-town="inflazione-nic-italia" style="--series-color:[^"]+">/,
        '<g class="ux-inflation-reference" style="--series-color:var(--ink)">'
      )
      .replace(
        /<button type="button" data-history-select="inflazione-nic-italia"[^>]*>[^<]*<\/button>/,
        `<span class="ux-history-reference"><i aria-hidden="true"></i>${referenceLabel}</span>`
      );
  }
"""
    text = replace_once(text, old_history_metric, new_history_metric, 'history metric helper')

    call_pattern = re.compile(
        r'toolkit\.historicalChartMarkup\((?:historyView|selected\.metric), series, selectedTown\)'
    )
    text, replacements = call_pattern.subn(
        'historyMarkup(historyView, series, selectedTown)',
        text,
    )
    if replacements == 0 and text.count('historyMarkup(historyView, series, selectedTown)') < 2:
        raise RuntimeError('Historical markup call anchors missing')
    if text.count('historyMarkup(historyView, series, selectedTown)') < 2:
        raise RuntimeError('Historical markup not wired on both compare and town surfaces')

    compare_old = """      : historyAvailable && selected.metric?.meta?.key === 'income'
        ? selected.metric.meta.longHistoryNote
        : historyAvailable
          ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
          : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    compare_new = """      : historyAvailable && selected.metric?.meta?.key === 'incomeVsInflation'
        ? selected.metric.historyPresentation?.note
        : historyAvailable && selected.metric?.meta?.key === 'income'
          ? selected.metric.meta.longHistoryNote
          : historyAvailable
            ? 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
            : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    text = replace_once(text, compare_old, compare_new, 'compare income/inflation note')

    town_old = """    const note = historyAvailable && selected.metric?.meta?.key === 'income'
      ? selected.metric.meta.longHistoryNote
      : historyAvailable
        ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
        : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    town_new = """    const note = historyAvailable && selected.metric?.meta?.key === 'incomeVsInflation'
      ? selected.metric.historyPresentation?.note
      : historyAvailable && selected.metric?.meta?.key === 'income'
        ? selected.metric.meta.longHistoryNote
        : historyAvailable
          ? 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
          : 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.';"""
    text = replace_once(text, town_old, town_new, 'town income/inflation note')

    UX.write_text(text, encoding='utf-8')


def patch_css() -> None:
    text = CSS.read_text(encoding='utf-8')
    marker = '/* Income vs inflation historical reference */'
    if marker in text:
        return
    text += r'''

/* Income vs inflation historical reference */
.ux-inflation-reference .ux-series-line {
  fill: none;
  stroke: var(--ink);
  stroke-width: 3;
  stroke-dasharray: 9 7;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .88;
}

.ux-inflation-reference .ux-series-point {
  fill: var(--paper);
  stroke: var(--ink);
  stroke-width: 2.2;
  opacity: .92;
}

.ux-inflation-reference .chart-guide {
  stroke: var(--ink);
}

.ux-inflation-reference .chart-point.active .chart-dot,
.ux-inflation-reference .chart-point:focus .chart-dot {
  fill: var(--ink);
  stroke: var(--surface);
  stroke-width: 3;
  r: 5.5px;
}

.ux-history-reference {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px dashed color-mix(in srgb, var(--ink) 30%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--ink) 4%, transparent);
  color: var(--ink);
  padding: 6px 9px;
  font-size: 10px;
  font-weight: 750;
}

.ux-history-reference i {
  width: 19px;
  border-top: 2px dashed var(--ink);
}
'''
    CSS.write_text(text, encoding='utf-8')


def main() -> None:
    patch_data()
    patch_history_js()
    patch_css()
    print('Income/inflation history patched: nominal municipal growth + NIC Italia, base 2016 = 0%')


if __name__ == '__main__':
    main()
