#!/usr/bin/env python3
"""Patch the canonical visual grammar for lifeExpectancy sex selection.

The compare renderer changes the displayed value through sexBreakdown. The
canonical visual-grammar layer must consume the same selected part for the
lollipop position and the official ARS Versilia reference, rather than falling
back to the base (Totale) row value and a computed municipal mean.
"""
from pathlib import Path

PATH = Path("assets/visual-grammar.js")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")

    old_selection = """  function compositeSelectionFor(container, metric, row) {
    const choice = container?.dataset?.compositeChoice || '';
    const scale = container?.dataset?.compositeScale || 'value';
    const type = metric?.meta?.compositeType;
    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile'].includes(type)) return null;
    // demographicBreakdown visual selection: usa la cella selezionata, non il valore base 25–64 Totale.
"""
    new_selection = """  function compositeSelectionFor(container, metric, row) {
    const choice = container?.dataset?.compositeChoice || '';
    const scale = container?.dataset?.compositeScale || 'value';
    const type = metric?.meta?.compositeType;
    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile','sexBreakdown'].includes(type)) return null;
    if (type === 'sexBreakdown') {
      const part = (row?.parts || []).find(item => item.key === choice) || row?.parts?.[0] || {};
      return { value: part.value, unit: part.unit || metric?.meta?.unit || 'years' };
    }
    // demographicBreakdown visual selection: usa la cella selezionata, non il valore base 25–64 Totale.
"""

    old_aggregate = """  function compositeAggregateFor(container, metric) {
    const choice = container?.dataset?.compositeChoice || '';
    const scale = container?.dataset?.compositeScale || 'value';
    const type = metric?.meta?.compositeType;
    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile'].includes(type)) return null;
    if (type === 'demographicBreakdown') {
"""
    new_aggregate = """  function compositeAggregateFor(container, metric) {
    const choice = container?.dataset?.compositeChoice || '';
    const scale = container?.dataset?.compositeScale || 'value';
    const type = metric?.meta?.compositeType;
    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile','sexBreakdown'].includes(type)) return null;
    if (type === 'sexBreakdown') {
      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};
      return { value: part.value, label:`Versilia (ARS) · ${part.label || ''}`, unit: part.unit || metric?.meta?.unit || 'years' };
    }
    if (type === 'demographicBreakdown') {
"""

    already = "['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile','sexBreakdown']"
    if text.count(already) == 2 and "Versilia (ARS)" in text:
        print("visual grammar lifeExpectancy v1.22 already patched")
        return

    text = replace_once(text, old_selection, new_selection, "selection contract")
    text = replace_once(text, old_aggregate, new_aggregate, "aggregate contract")
    PATH.write_text(text, encoding="utf-8")
    print("visual grammar lifeExpectancy v1.22 patched")


if __name__ == "__main__":
    main()
