#!/usr/bin/env python3
"""Preserve real-income values through the shared historical-series adapter.

The income-vs-inflation history displays nominal income as the chart series,
but its tooltip also needs the separate ratio-based real-income series. The
shared comparableSeries() adapter used to retain only the displayed values,
so the tooltip renderer could not see realSeries and rendered `n.d.`.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'assets' / 'ux-history-core.js'

OLD = r"""  function comparableSeries(metric) {
    if (!metric?.rows?.length) return null;
    const rows = metric.rows.map((row, index) => {
      const years = row.series?.years || [];
      const values = row.series?.values || [];
      const map = new Map();
      years.forEach((year, yearIndex) => {
        const value = Number(values[yearIndex]);
        if (Number.isFinite(value)) map.set(String(year), value);
      });
      return {
        town: row.town,
        slug: row.slug || slug(row.town),
        color: colors[index % colors.length],
        map
      };
    });
    if (rows.some(row => row.map.size < 2)) return null;
    let years = [...rows[0].map.keys()].filter(year => rows.every(row => row.map.has(year)));
    years = years.sort((a, b) => Number(a) - Number(b));
    if (years.length < 2) return null;
    return {
      years,
      rows: rows.map(row => ({ ...row, values: years.map(year => row.map.get(year)) }))
    };
  }
"""

NEW = r"""  function comparableSeries(metric) {
    if (!metric?.rows?.length) return null;
    const rows = metric.rows.map((row, index) => {
      const years = row.series?.years || [];
      const values = row.series?.values || [];
      const map = new Map();
      years.forEach((year, yearIndex) => {
        const value = Number(values[yearIndex]);
        if (Number.isFinite(value)) map.set(String(year), value);
      });
      const realMap = new Map();
      (row.realSeries?.years || []).forEach((year, yearIndex) => {
        const value = Number(row.realSeries?.values?.[yearIndex]);
        if (Number.isFinite(value)) realMap.set(String(year), value);
      });
      return {
        town: row.town,
        slug: row.slug || slug(row.town),
        color: colors[index % colors.length],
        map,
        realMap
      };
    });
    if (rows.some(row => row.map.size < 2)) return null;
    let years = [...rows[0].map.keys()].filter(year => rows.every(row => row.map.has(year)));
    years = years.sort((a, b) => Number(a) - Number(b));
    if (years.length < 2) return null;
    return {
      years,
      rows: rows.map(row => ({
        ...row,
        values: years.map(year => row.map.get(year)),
        realSeries: row.realMap.size
          ? { years, values: years.map(year => row.realMap.get(year) ?? null) }
          : null
      }))
    };
  }
"""


def main() -> None:
    text = CORE.read_text(encoding='utf-8')
    if NEW in text:
        print('Historical adapter already preserves real-income tooltip data')
        return
    if OLD not in text:
        raise RuntimeError('comparableSeries anchor missing')
    text = text.replace(OLD, NEW, 1)
    CORE.write_text(text, encoding='utf-8')
    print('Historical adapter now preserves ratio-based real-income tooltip data')


if __name__ == '__main__':
    main()
