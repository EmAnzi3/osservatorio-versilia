#!/usr/bin/env python3
"""Runner robusto del refiner v1.36 sui renderer generati dalla pipeline canonica."""
from __future__ import annotations

import refine_territorio_ucs_release as base


def insert_after_in_block(source: str, start_marker: str, end_marker: str, needle: str, insertion: str, label: str) -> str:
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise RuntimeError(f"v1.36 refine v2: blocco {label} non trovato.")
    block = source[start:end]
    if block.count(needle) != 1:
        raise RuntimeError(f"v1.36 refine v2: {label} non patchabile ({block.count(needle)} occorrenze).")
    block = block.replace(needle, needle + "\n" + insertion.rstrip(), 1)
    return source[:start] + block + source[end:]


def robust_patch_visual_grammar() -> None:
    source = base.VISUAL_GRAMMAR.read_text(encoding="utf-8")
    if base.GRAMMAR_MARKER in source:
        return

    bypass = "    /* OV TERRITORIO UCS VISUAL-GRAMMAR BYPASS v1.36.0 */\n    if (container.closest('[data-land-cover-compare-shell]')) return;"
    if source.count(bypass) != 1:
        raise RuntimeError(f"v1.36 refine v2: bypass UCS atteso una volta, trovato {source.count(bypass)}.")
    source = source.replace(bypass, f"    {base.GRAMMAR_MARKER}", 1)

    selection_insert = """    if (type === 'landCoverProfile') {
      const mode=container?.dataset?.landCoverMode||'profile';
      if (mode === 'transformation') return { value:row?.transformation?.changedPct, unit:'percent' };
      const category=container?.dataset?.landCoverCategory||'artificialized';
      const year=Number(container?.dataset?.landCoverYear)||2019;
      const unit=container?.dataset?.landCoverUnit||'percent';
      const index=(metric?.landCoverYears||[]).indexOf(year);
      const series=row?.coverSeries?.[category]||{};
      const values=unit==='hectares'?(series.ha||[]):(series.pct||[]);
      return { value:index>=0?values[index]:null, unit };
    }
    if (type === 'forestCoverIndex') {
      const unit=container?.dataset?.forestCoverUnit||'percent';
      return { value:unit==='hectares'?row?.forestAreaHa:row?.forestCoverPct, unit };
    }"""
    source = insert_after_in_block(
        source,
        "  function compositeSelectionFor(container, metric, row) {",
        "  function compositeAggregateFor(container, metric) {",
        "    const type = metric?.meta?.compositeType;",
        selection_insert,
        "selezione composita canonica",
    )

    aggregate_insert = """    if (type === 'landCoverProfile') {
      const mode=container?.dataset?.landCoverMode||'profile';
      if (mode === 'transformation') return { value:metric?.aggregate?.transformation?.changedPct, label:'Versilia · trasformazione 2007→2019', unit:'percent' };
      const category=container?.dataset?.landCoverCategory||'artificialized';
      const year=Number(container?.dataset?.landCoverYear)||2019;
      const unit=container?.dataset?.landCoverUnit||'percent';
      const index=(metric?.landCoverYears||[]).indexOf(year);
      const series=metric?.aggregate?.coverSeries?.[category]||{};
      if (unit === 'hectares') return { value:null, label:'Versilia · totale mostrato separatamente', unit };
      return { value:index>=0?(series.pct||[])[index]:null, label:'Versilia · quota ponderata', unit };
    }
    if (type === 'forestCoverIndex') {
      const unit=container?.dataset?.forestCoverUnit||'percent';
      if (unit === 'hectares') return { value:null, label:'Versilia · totale mostrato separatamente', unit };
      return { value:metric?.aggregate?.forestCoverPct, label:'Versilia · Indice di Boscosità', unit };
    }"""
    source = insert_after_in_block(
        source,
        "  function compositeAggregateFor(container, metric) {",
        "  function enhanceComparison(container) {",
        "    const type = metric?.meta?.compositeType;",
        aggregate_insert,
        "aggregato composito canonico",
    )

    source = base.replace_in_block(
        source,
        "  function enhanceComparison(container) {",
        "  function enhance() {",
        "    const aggregate = compositeAggregate || aggregateFor(metric, normalized);",
        "    const aggregate = metricKey === 'statisticalCoastlineLength' ? {value:null,label:'Totale Versilia mostrato separatamente'} : (compositeAggregate || aggregateFor(metric, normalized));",
        "riferimento confronto litoranea",
    )

    coast_delta_anchor = "    const key = metricKey || metric?.meta?.key || '';"
    coast_delta_insert = """    if (key === 'statisticalCoastlineLength') {
      const total=finite(metric?.aggregate?.value);
      if (total === null || total <= 0) return { headline:'n.d.', direction:'quota non disponibile', compact:'quota non disponibile' };
      const share=local/total*100;
      const formattedShare=number1.format(share);
      return {
        headline:`${formattedShare}%`,
        direction:'della linea litoranea statistica della Versilia',
        compact:`${formattedShare}% della linea litoranea statistica della Versilia`,
        overline:'Quota sulla linea litoranea statistica',
        note:`Totale Versilia ${number2.format(total)} km`,
      };
    }"""
    source = insert_after_in_block(
        source,
        "  function deltaFor(metric, row, metricKey = '') {",
        "  function compositeSelectionFor(container, metric, row) {",
        coast_delta_anchor,
        coast_delta_insert,
        "quota litoranea nelle card",
    )

    source = base.replace_in_block(
        source,
        "  function enhanceTownPosition() {",
        "  function enhanceIndicatorCards() {",
        "    const metricKey = metricKeyFor(panel);",
        "    const metricKey = metricKeyFor(panel);\n    if (metricKey === 'statisticalCoastlineLength') return;",
        "sidebar litoranea preservata",
    )

    base.VISUAL_GRAMMAR.write_text(source, encoding="utf-8")


def main() -> None:
    base.patch_renderer()
    robust_patch_visual_grammar()
    base.patch_css()
    base.validate_final_state()
    print("v1.36 refine v2: lollipop canonici UCS/foreste, costa a quota Versilia, DEGURBA robusto, 202 metriche.")


if __name__ == "__main__":
    main()
