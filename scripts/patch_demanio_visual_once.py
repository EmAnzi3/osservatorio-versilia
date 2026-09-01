#!/usr/bin/env python3
from pathlib import Path

p = Path('assets/visual-grammar.js')
t = p.read_text(encoding='utf-8')

old_key = """    const key = metricKey || metric?.meta?.key || '';
    if (key === 'population') {"""
new_key = """    const key = metricKey || metric?.meta?.key || '';
    if (['maritimeConcessions','maritimeConcessionFeesDue'].includes(key) && metric?.meta?.comparisonDifference === 'shareOfAggregate') {
      const total = finite(metric?.aggregate?.value);
      if (total === null || total <= 0) {
        return { headline: 'n.d.', direction: 'quota non disponibile', compact: 'quota non disponibile', overline: metric?.meta?.comparisonOverline, note: metric?.meta?.comparisonNote };
      }
      const share = local / total * 100;
      const formattedShare = number1.format(share);
      return {
        headline: `${formattedShare}%`,
        direction: 'del totale dei quattro Comuni costieri',
        compact: `${formattedShare}% del totale costiero`,
        overline: metric?.meta?.comparisonOverline || 'Peso sulla Versilia costiera',
        note: metric?.meta?.comparisonNote || 'Quota del valore comunale sul totale dei quattro Comuni costieri.',
      };
    }
    if (key === 'population') {"""
if new_key not in t:
    if old_key not in t:
        raise SystemExit('Punto deltaFor non trovato')
    t = t.replace(old_key, new_key, 1)

old_town = """    const row = townRow(metric, townName);
    if (!metric || !row) return;
    if (['distribution','agricultureProfile'].includes(metric.meta?.compositeType)) return;"""
new_town = """    const row = townRow(metric, townName);
    if (!metric || !row) return;
    if (['maritimeConcessions','maritimeConcessionFeesDue'].includes(metricKey)) return;
    if (['distribution','agricultureProfile'].includes(metric.meta?.compositeType)) return;"""
if new_town not in t:
    if old_town not in t:
        raise SystemExit('Punto enhanceTownPosition non trovato')
    t = t.replace(old_town, new_town, 1)

p.write_text(t, encoding='utf-8')
print('Visual grammar: i due indicatori demaniali mantengono la quota percentuale sul totale costiero.')
