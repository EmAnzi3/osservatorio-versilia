#!/usr/bin/env python3
"""Integra la dimensione sesso di lifeExpectancy nei renderer canonici.

Non crea grafici o tooltip paralleli: riusa i controlli compositi esistenti e
proietta la scelta Totale/Maschi/Femmine sui renderer comparison/history.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PART = ROOT / "assets" / "app-parts" / "03.txt"
HISTORY = ROOT / "assets" / "ux-history.js"
CORE = ROOT / "assets" / "ux-history-core.js"
APP_JS = ROOT / "assets" / "app.js"
SW = ROOT / "service-worker.js"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Pattern non trovato ({label})")
    return text.replace(old, new, 1)


def patch_app_part() -> None:
    text = APP_PART.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "  function compositeCompareDefaults(metric) {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeCompareDefaults(metric) {\n    if (metric.meta.compositeType === 'sexBreakdown') return { choice:metric.meta.defaultSex || 'totale', scale:'value' };\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "default sesso",
    )
    text = replace_once(
        text,
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'sexBreakdown') {\n      const part = (row.parts || []).find(item => item.key === choice) || row.parts?.[0] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, part };\n    }\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "selezione sesso compare",
    )
    text = replace_once(
        text,
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'sexBreakdown') {\n      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };\n    }\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "aggregato sesso compare",
    )
    text = replace_once(
        text,
        "  function compositeCompareControls(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeCompareControls(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'sexBreakdown') {\n      const options = metric.meta.sexOptions || (metric.rows?.[0]?.parts || []).map(part => ({key:part.key,label:part.label}));\n      return `<div class=\"compare-view-controls demographic-view-controls\"><label class=\"compare-choice-select\"><span>Sesso</span><select data-composite-component>${options.map(option=>`<option value=\"${html(option.key)}\" ${option.key === choice ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>`;\n    }\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "controllo sesso compare",
    )
    text = replace_once(
        text,
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','demographicBreakdown'].includes(compositeType);",
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','demographicBreakdown','sexBreakdown'].includes(compositeType);",
        "abilitazione sesso compare",
    )
    text = replace_once(
        text,
        "    benchmark.innerHTML = (metricKey.startsWith('slowMobility') || metric.meta.compositeType) ? '' : benchmarkMarkup(metric,aggregate,unit,null);",
        "    const benchmarkMetric = compositeType === 'sexBreakdown' && metric.meta.benchmarksBySex?.[view.choice]\n      ? { ...metric, meta:{ ...metric.meta, benchmark:metric.meta.benchmarksBySex[view.choice] } }\n      : metric;\n    benchmark.innerHTML = (metricKey.startsWith('slowMobility') || (metric.meta.compositeType && compositeType !== 'sexBreakdown')) ? '' : benchmarkMarkup(benchmarkMetric,aggregate,unit,null);",
        "benchmark sesso compare",
    )

    text = replace_once(
        text,
        "  function compositeTownMarkup(metric, row) {\n    const parts = row.parts || [];",
        "  function compositeTownMarkup(metric, row) {\n    const parts = row.parts || [];\n    if (metric.meta.compositeType === 'sexBreakdown') return '';",
        "dettaglio town sesso",
    )
    text = replace_once(
        text,
        "  function compositeSelectionOptions(metric, row) {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeSelectionOptions(metric, row) {\n    if (metric.meta.compositeType === 'sexBreakdown') return (row.parts || []).map(part=>({ key:part.key, label:part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatValue(part.value,part.unit || metric.meta.unit), part }));\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "opzioni town sesso",
    )
    text = replace_once(
        text,
        "  function compositeSelectionAggregate(metric, choice) {\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "  function compositeSelectionAggregate(metric, choice) {\n    if (metric.meta.compositeType === 'sexBreakdown') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }\n    if (metric.meta.compositeType === 'demographicBreakdown')",
        "aggregato town sesso",
    )
    text = replace_once(
        text,
        "    const values = metric.rows.map(r => {\n      if (metric.meta.compositeType === 'demographicBreakdown')",
        "    const values = metric.rows.map(r => {\n      if (metric.meta.compositeType === 'sexBreakdown') { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:Number(part?.value)}; }\n      if (metric.meta.compositeType === 'demographicBreakdown')",
        "rank town sesso",
    )

    text = replace_once(
        text,
        "    const demographicBreakdown = metric.meta.compositeType === 'demographicBreakdown';\n    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown;",
        "    const demographicBreakdown = metric.meta.compositeType === 'demographicBreakdown';\n    const sexBreakdown = metric.meta.compositeType === 'sexBreakdown';\n    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown;",
        "town selezionabile sesso",
    )
    text = replace_once(
        text,
        "    const defaultDemographicChoice = demographicBreakdown ? `${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}` : null;\n    const summary = distribution ? compositeSummary(metric,row) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures) ? options[0] : null));\n    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null))));",
        "    const defaultDemographicChoice = demographicBreakdown ? `${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}` : null;\n    const defaultSexChoice = sexBreakdown ? (metric.meta.defaultSex || 'totale') : null;\n    const summary = distribution ? compositeSummary(metric,row) : (sexBreakdown ? (options.find(option=>option.key===defaultSexChoice) || options[0]) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures) ? options[0] : null)));\n    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (sexBreakdown ? compositeSelectionAggregate(metric,defaultSexChoice) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)))));",
        "default town sesso",
    )
    text = replace_once(
        text,
        "    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')",
        "    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : sexBreakdown ? 'Totale, Maschi e Femmine' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')",
        "titolo town sesso",
    )
    text = replace_once(
        text,
        "    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}`",
        "    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : sexBreakdown ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}`",
        "titolo pannello town sesso",
    )
    text = replace_once(
        text,
        "      ${(metricKey.startsWith('slowMobility') || demographicBreakdown) ? '' : townBenchmarkMarkup(metric, row, town)}",
        "      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown) ? '' : townBenchmarkMarkup(metric, row, town)}",
        "benchmark town sesso",
    )

    text = replace_once(
        text,
        "    const isDemographic = metric.meta.compositeType === 'demographicBreakdown';\n    const lines = isOmi ? [['Comune','Codice Istat','Indicatore','Anno','Zona OMI','Area','Vendita €/m²','Affitto €/m²/mese','Fonte']] : isDemographic ?",
        "    const isDemographic = metric.meta.compositeType === 'demographicBreakdown';\n    const isSexBreakdown = metric.meta.compositeType === 'sexBreakdown';\n    const lines = isSexBreakdown ? [['Territorio','Codice Istat','Indicatore','Anno','Sesso','Valore','Unità','Fonte']] : isOmi ? [['Comune','Codice Istat','Indicatore','Anno','Zona OMI','Area','Vendita €/m²','Affitto €/m²/mese','Fonte']] : isDemographic ?",
        "header csv sesso",
    )
    text = replace_once(
        text,
        "    if (isOmi) rows.forEach(row => (row.zones || []).forEach(zone => lines.push([row.town,row.code,label,metric.meta.year,zone.code,zone.label,zone.sale,zone.rent,metric.sourceUrl])));\n    else if (isDemographic)",
        "    if (isSexBreakdown) {\n      const sources = [...metric.rows.map(row=>({territory:row.town,code:row.code,parts:row.parts||[]})), {territory:'Versilia',code:'202M',parts:metric.aggregate?.parts||[]}];\n      sources.forEach(source => source.parts.forEach(part => (part.series?.years || []).forEach((year,index) => lines.push([source.territory,source.code,label,year,part.label,part.series.values[index],part.unit || metric.meta.unit,metric.sourceUrl]))));\n    }\n    else if (isOmi) rows.forEach(row => (row.zones || []).forEach(zone => lines.push([row.town,row.code,label,metric.meta.year,zone.code,zone.label,zone.sale,zone.rent,metric.sourceUrl])));\n    else if (isDemographic)",
        "righe csv sesso",
    )

    APP_PART.write_text(text, encoding="utf-8")


def patch_history() -> None:
    text = HISTORY.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  function compositeChoiceMetric(metric, choice) {\n    if (!['distribution','omi','stock','securityMeasures'].includes(metric?.meta?.compositeType)) return metric;",
        "  function compositeChoiceMetric(metric, choice) {\n    if (!['distribution','omi','stock','securityMeasures','sexBreakdown'].includes(metric?.meta?.compositeType)) return metric;",
        "history abilita sesso",
    )
    text = replace_once(
        text,
        "    const clone = { ...metric, meta: { ...metric.meta }, rows: metric.rows.map(row => ({ ...row })) };\n    if (metric.meta.compositeType === 'securityMeasures')",
        "    const clone = { ...metric, meta: { ...metric.meta }, rows: metric.rows.map(row => ({ ...row })), aggregate:metric.aggregate ? { ...metric.aggregate } : metric.aggregate };\n    if (metric.meta.compositeType === 'sexBreakdown') {\n      const selected = choice || metric.meta.defaultSex || 'totale';\n      const option = (metric.meta.sexOptions || []).find(item=>item.key===selected);\n      clone.meta.label = option ? `${metric.meta.label} · ${option.label}` : metric.meta.label;\n      clone.meta.benchmark = metric.meta.benchmarksBySex?.[selected] || metric.meta.benchmark;\n      clone.rows = metric.rows.map(row => {\n        const part=(row.parts || []).find(item=>item.key===selected) || row.parts?.[0] || {};\n        return { ...row, value:part.value, formatted:part.formatted || row.formatted, series:part.series || row.series };\n      });\n      const aggregatePart=(metric.aggregate?.parts || []).find(item=>item.key===selected) || metric.aggregate?.parts?.[0] || {};\n      clone.aggregate = { ...metric.aggregate, value:aggregatePart.value, formatted:aggregatePart.formatted, series:aggregatePart.series, label:`Versilia · ${aggregatePart.label || option?.label || ''}` };\n      return clone;\n    }\n    if (metric.meta.compositeType === 'securityMeasures')",
        "history proiezione sesso",
    )
    text = replace_once(
        text,
        "  function refreshTownCompositeCurrent(metric, shell, selectedTown, choice) {\n    if (!shell || !['distribution','omi','stock','securityMeasures'].includes(metric?.meta?.compositeType)) return;",
        "  function refreshTownCompositeCurrent(metric, shell, selectedTown, choice) {\n    if (!shell || !['distribution','omi','stock','securityMeasures','sexBreakdown'].includes(metric?.meta?.compositeType)) return;",
        "town current sesso",
    )
    text = replace_once(
        text,
        "  function currentCompositeChoice() {\n    return document.querySelector('select[data-composite-choice]')?.value || document.querySelector('select[data-composite-component]')?.value || 'summary';\n  }",
        "  function currentCompositeChoice() {\n    return document.querySelector('select[data-composite-choice]')?.value || document.querySelector('select[data-composite-component]')?.value || 'summary';\n  }\n\n  function withOfficialVersiliaSeries(metric, series) {\n    if (!series || metric?.meta?.compositeType !== 'sexBreakdown' || !metric.aggregate?.series?.years?.length) return series;\n    const map = new Map(metric.aggregate.series.years.map((year,index)=>[String(year),Number(metric.aggregate.series.values?.[index])]));\n    if (!series.years.every(year=>Number.isFinite(map.get(String(year))))) return series;\n    return { ...series, rows:[...series.rows,{ town:'Versilia', slug:'versilia', color:'var(--ink)', map:new Map(), realMap:new Map(), values:series.years.map(year=>map.get(String(year))), realSeries:null }] };\n  }",
        "serie Versilia ufficiale",
    )
    text = replace_once(
        text,
        "    const normalized = Boolean(document.querySelector('[data-scale=\"normalized\"].active'));\n    const historyView = historyMetric(selected.metric);\n    const series = normalized ? null : toolkit.comparableSeries(historyView);",
        "    const normalized = Boolean(document.querySelector('[data-scale=\"normalized\"].active'));\n    const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null;\n    const historyView = historyMetric(selectedChoice ? compositeChoiceMetric(selected.metric, selectedChoice) : selected.metric);\n    const series = normalized ? null : withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));",
        "compare history sesso",
    )
    text = replace_once(
        text,
        "    const fixedDetail = panel.querySelector('.composite-fixed-detail')?.outerHTML || '';\n    const historyView = historyMetric(selected.metric);\n    const series = toolkit.comparableSeries(historyView);\n    const historyAvailable = Boolean(series);\n    const viewMetric = compositeChoiceMetric(selected.metric, currentCompositeChoice());",
        "    const fixedDetail = panel.querySelector('.composite-fixed-detail')?.outerHTML || '';\n    const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null;\n    const historyView = historyMetric(selectedChoice ? compositeChoiceMetric(selected.metric, selectedChoice) : selected.metric);\n    const series = withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));\n    const historyAvailable = Boolean(series);\n    const viewMetric = compositeChoiceMetric(selected.metric, currentCompositeChoice());",
        "town history sesso",
    )
    text = replace_once(
        text,
        "      refreshTownCompositeCurrent(metric, shell, document.body.dataset.town || '', event.detail?.choice || 'summary');",
        "      const choice = event.detail?.choice || 'summary';\n      refreshTownCompositeCurrent(metric, shell, document.body.dataset.town || '', choice);\n      if (metric.meta?.compositeType === 'sexBreakdown') {\n        const selectedTown = document.body.dataset.town || '';\n        const historyView = historyMetric(compositeChoiceMetric(metric, choice));\n        const series = withOfficialVersiliaSeries(historyView, toolkit.comparableSeries(historyView));\n        const pane = shell.querySelector('[data-view-pane=\"history\"]');\n        if (pane) {\n          pane.innerHTML = renderHistoryMarkup(historyView, series, selectedTown);\n          toolkit.wireHistorySelection(shell, selectedTown, false);\n        }\n      }",
        "refresh town history sesso",
    )
    text = replace_once(
        text,
        "    if (metric?.meta?.key !== 'incomeVsInflation' || !metric.inflationSeries?.years?.length) return markup;",
        "    if (metric?.meta?.compositeType === 'sexBreakdown') {\n      return markup.replace('Una linea per comune; sono mostrati solo gli anni disponibili per tutti e sette.', 'Sette Comuni più l’aggregato ufficiale Versilia; sono mostrati solo gli anni omogenei della fonte ARS.');\n    }\n    if (metric?.meta?.key !== 'incomeVsInflation' || !metric.inflationSeries?.years?.length) return markup;",
        "copy storico sesso",
    )
    text = replace_once(
        text,
        "  const HOTFIX_VERSION = '20260827-v121-history-ui6';",
        "  const HOTFIX_VERSION = '20260828-v122-lifeexp-ui1';",
        "cache history",
    )
    HISTORY.write_text(text, encoding="utf-8")


def patch_core_copy() -> None:
    text = CORE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "'Una linea per comune; sono mostrati solo gli anni disponibili per tutti e sette.'",
        "'Una linea per territorio; sono mostrati solo gli anni disponibili in modo omogeneo.'",
        "copy storico generico",
    ) if "'Una linea per comune; sono mostrati solo gli anni disponibili per tutti e sette.'" in text else text
    CORE.write_text(text, encoding="utf-8")


def patch_versions() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    text = replace_once(text, "const VERSION='20260827-v121-history-ui2';", "const VERSION='20260828-v122-lifeexp-ui1';", "cache app")
    APP_JS.write_text(text, encoding="utf-8")

    text = SW.read_text(encoding="utf-8")
    text = replace_once(text, "const VERSION = 'ov-pwa-20260827-v121-tooltip-ui6';", "const VERSION = 'ov-pwa-20260828-v122-lifeexp-ui1';", "cache service worker")
    SW.write_text(text, encoding="utf-8")


def main() -> None:
    patch_app_part()
    patch_history()
    patch_core_copy()
    patch_versions()
    print("Frontend lifeExpectancy v1.22.0: selettore sesso collegato ai renderer canonici e allo storico ARS.")


if __name__ == "__main__":
    main()
