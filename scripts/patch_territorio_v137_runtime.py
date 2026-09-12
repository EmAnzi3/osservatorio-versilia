#!/usr/bin/env python3
"""Estende i renderer canonici ai profili territoriali v1.37.

La patch viene applicata nel workspace effimero della build canonica dopo tutte
le patch runtime/materializzazioni delle release precedenti. Gli agganci sono
limitati alle singole funzioni JavaScript per evitare dipendenze da intere righe
che cambiano tra release.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP00 = ROOT / "assets" / "app-parts" / "00.txt"
APP03 = ROOT / "assets" / "app-parts" / "03.txt"
APP05 = ROOT / "assets" / "app-parts" / "05.txt"
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
UX_HISTORY_CORE = ROOT / "assets" / "ux-history-core.js"
UX_HISTORY = ROOT / "assets" / "ux-history.js"
SENTINEL = "territoryProfileTypes"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"v1.37 runtime: {label}: attesa 1 occorrenza, trovate {count}")
    return text.replace(old, new, 1)


def replace_exact_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"v1.37 runtime: {label}: attese {expected} occorrenze, trovate {count}")
    return text.replace(old, new)


def function_block(text: str, name: str) -> tuple[int, int, str]:
    marker = f"  function {name}("
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"v1.37 runtime: funzione {name} non trovata")
    end = text.find("\n  function ", start + len(marker))
    if end < 0:
        end = len(text)
    return start, end, text[start:end]


def patch_function(text: str, name: str, transform) -> str:
    start, end, block = function_block(text, name)
    patched = transform(block)
    if patched == block:
        raise RuntimeError(f"v1.37 runtime: funzione {name} non modificata")
    return text[:start] + patched + text[end:]


def edit_line_once(text: str, needle: str, editor, label: str) -> str:
    lines = text.splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if needle in line]
    if len(hits) != 1:
        raise RuntimeError(f"v1.37 runtime: {label}: attesa 1 riga, trovate {len(hits)}")
    i = hits[0]
    new = editor(lines[i])
    if new == lines[i]:
        raise RuntimeError(f"v1.37 runtime: {label}: riga invariata")
    lines[i] = new
    return "".join(lines)


def insert_after_line(text: str, needle: str, addition: str, label: str) -> str:
    return edit_line_once(text, needle, lambda line: line + addition, label)


def main() -> None:
    app00 = APP00.read_text(encoding="utf-8")
    app03 = APP03.read_text(encoding="utf-8")
    app05 = APP05.read_text(encoding="utf-8")
    visual = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    ux_core = UX_HISTORY_CORE.read_text(encoding="utf-8")
    ux_history = UX_HISTORY.read_text(encoding="utf-8")

    if SENTINEL in app03:
        required = ("sqm_per_resident", "km_per_km2", "territoryProfileHistoryChart", "data-metric-key", "sqm-per-resident", "updateTerritoryProfileTownPosition", "TERRITORY_PROFILE_HISTORY_TYPES", "wireHistoryTooltips")
        if not all(token in app00 + app03 + app05 + visual + ux_core + ux_history for token in required):
            raise RuntimeError("v1.37 runtime: patch parzialmente applicata")
        print("Renderer territorio v1.37 gia' applicato.")
        return

    app00 = replace_exact_count(
        app00,
        "      case 'hectares': return `${number2.format(v)} ha`;\n",
        "      case 'hectares': return `${number2.format(v)} ha`;\n"
        "      case 'sqm_per_resident': return `${number1.format(v)} m²/residente`;\n",
        2,
        "formatter m2/residente",
    )
    app00 = replace_exact_count(
        app00,
        "      case 'km': return `${number2.format(v)} km`;\n",
        "      case 'km': return `${number2.format(v)} km`;\n"
        "      case 'km_per_km2': return `${number2.format(v)} km/km²`;\n",
        1,
        "formatter densita lineare",
    )

    helper = """
  const territoryProfileTypes = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']);
  function isTerritoryProfileType(value) {
    const type = typeof value === 'string' ? value : value?.meta?.compositeType;
    return territoryProfileTypes.has(type);
  }

"""
    app03 = replace_once(app03, "  function compositeCompareDefaults(metric) {\n", helper + "  function compositeCompareDefaults(metric) {\n", "helper profili territorio")

    app03 = patch_function(app03, "compositeCompareDefaults", lambda b: insert_after_line(b, "function compositeCompareDefaults(metric)", "    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:metric.meta.compositeType === 'protectedAreasProfile' ? 'percent' : 'value' };\n", "default territorio"))
    app03 = patch_function(app03, "compositeCompareSelection", lambda b: insert_after_line(b, "function compositeCompareSelection(metric, row, choice", "    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),part}; }\n", "selezione territorio"))
    app03 = patch_function(app03, "compositeCompareAggregate", lambda b: insert_after_line(b, "function compositeCompareAggregate(metric, choice", "    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; const hectares=metric.meta.compositeType === 'protectedAreasProfile' && scale === 'hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric.meta.unit),label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\n", "aggregato territorio"))
    app03 = patch_function(app03, "compositeCompareControls", lambda b: insert_after_line(b, "function compositeCompareControls(metric, choice", "    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; const unitControls=metric.meta.compositeType === 'protectedAreasProfile' ? `<div><span class=\"compare-view-label\">Unità</span><div class=\"scale-switch compact\" role=\"group\" aria-label=\"Unità aree protette\"><button type=\"button\" data-composite-scale=\"percent\" class=\"${scale==='percent'?'active':''}\">%</button><button type=\"button\" data-composite-scale=\"hectares\" class=\"${scale==='hectares'?'active':''}\">ha</button></div></div>` : ''; return `<div class=\"compare-view-controls territory-profile-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\"${html(part.key)}\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label>${unitControls}</div>`; }\n", "controlli territorio"))

    def town_markup(b: str) -> str:
        addition = (
            "    if (isTerritoryProfileType(metric)) {\n"
            "      const histories=parts.filter(part=>row.seriesByView?.[part.key]?.years?.length).map(part=>`<details class=\"detail-disclosure territory-profile-history\" ${part.key===(metric.meta.defaultView||parts[0]?.key)?'open':''}><summary><span>${html(part.label)}</span><small>Serie ufficiale</small></summary><div>${seriesChart(row.seriesByView[part.key],part.unit || metric.meta.unit,`${metric.meta.label} · ${part.label} · ${row.town}`)}</div></details>`).join('');\n"
            "      return `<div class=\"composite-town-mobility territory-profile-town\">${parts.map(part=>`<article class=\"${part.key===(metric.meta.defaultView||parts[0]?.key)?'balance':''}\"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.compositeType==='protectedAreasProfile'&&part.ha!==undefined?formatValue(part.ha,'hectares'):metric.meta.year)}</small></article>`).join('')}</div>${histories}`;\n"
            "    }\n"
        )
        return insert_after_line(b, "const parts = row.parts || [];", addition, "dettaglio comunale territorio")
    app03 = patch_function(app03, "compositeTownMarkup", town_markup)

    app03 = patch_function(app03, "compositeSelectionOptions", lambda b: insert_after_line(b, "function compositeSelectionOptions(metric, row)", "    if (isTerritoryProfileType(metric)) return (row.parts || []).map(part=>({key:part.key,label:part.selectorLabel || part.label,value:part.value,unit:part.unit || metric.meta.unit,formatted:formatMetricRowValue(row,part.value,part.unit || metric.meta.unit),part}));\n", "opzioni territorio"))
    app03 = patch_function(app03, "compositeSelectionAggregate", lambda b: insert_after_line(b, "function compositeSelectionAggregate(metric, choice)", "    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }\n", "aggregato selettore territorio"))
    app03 = patch_function(app03, "compositeSelectionRank", lambda b: insert_after_line(b, "const values = metric.rows.map(r => {", "      if (isTerritoryProfileType(metric)) { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:part?.value===null||part?.value===undefined?NaN:Number(part.value)}; }\n", "rank territorio"))

    position_helper = """
  function updateTerritoryProfileTownPosition(metric,row,choice,position) {
    if (!position || !isTerritoryProfileType(metric)) return;
    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const local=Number(selected?.value);
    const total=Number(agg?.value);
    const unit=selected?.unit || metric.meta.unit;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    const additive=['hectares','km'].includes(unit);
    if (additive) {
      const share=Number.isFinite(local) && Number.isFinite(total) && total !== 0 ? local/total*100 : null;
      if(overline) overline.textContent='Quota sul totale Versilia';
      if(deltaEl) deltaEl.innerHTML=share === null
        ? `n.d.<small>${total === 0 ? 'totale Versilia pari a zero' : 'quota non disponibile'}</small>`
        : `${html(number1.format(share))}%<small>del totale Versilia</small>`;
      if(noteEl) noteEl.textContent='Quota del valore comunale sul totale dei sette Comuni per la lettura selezionata.';
    } else {
      const diff=Number.isFinite(local) && Number.isFinite(total) ? local-total : null;
      if(overline) overline.textContent='Scostamento dal valore Versilia';
      if(deltaEl) deltaEl.innerHTML=diff === null
        ? 'n.d.<small>confronto non disponibile</small>'
        : `${html(formatValue(diff,unit))}<small>rispetto al valore Versilia</small>`;
      if(noteEl) noteEl.textContent='Per quote, densità e valori pro capite è mostrata la differenza rispetto al valore aggregato Versilia; non è un giudizio di qualità.';
    }
    if(aggLabel) aggLabel.textContent=agg.label;
    if(aggValue) aggValue.textContent=agg.formatted;
  }

"""
    app03 = replace_once(app03, "  function updateAgricultureProfileTownPosition(metric,row,choice,position) {\n", position_helper + "  function updateAgricultureProfileTownPosition(metric,row,choice,position) {\n", "confronto comunale territorio")

    def compare_render(b: str) -> str:
        b = edit_line_once(b, "const selectableComposite =", lambda line: line.replace(".includes(compositeType);", ".includes(compositeType) || isTerritoryProfileType(compositeType);", 1), "selectable compare territorio")
        def note_edit(line: str) -> str:
            prefix = "      const note = "
            expr = line[len(prefix):].rstrip("\n")
            if not expr.endswith(";"):
                raise RuntimeError("v1.37 runtime: nota compare senza terminatore")
            return prefix + "isTerritoryProfileType(compositeType) ? `<p class=\"composite-compare-note\">Scegli la lettura dal selettore. Ogni vista conserva la propria unità e il proprio metodo di aggregazione Versilia.</p>` : (" + expr[:-1] + ");\n"
        return edit_line_once(b, "const note = compositeType === 'omi'", note_edit, "nota compare territorio")
    app03 = patch_function(app03, "renderCompareMetric", compare_render)

    def town_render(b: str) -> str:
        b = insert_after_line(b, "const hydroRisk = metric.meta.compositeType === 'hydroRisk';", "    const territoryProfile = isTerritoryProfileType(metric);\n", "flag territorio comunale")
        b = edit_line_once(b, "const selectable = distribution ||", lambda line: line.replace(" || hydroRisk;", " || hydroRisk || territoryProfile;", 1), "selezionabile territorio comunale")
        b = insert_after_line(b, "const defaultSexChoice =", "    const defaultTerritoryChoice = territoryProfile ? (metric.meta.defaultView || options[0]?.key) : null;\n", "default territorio comunale")

        def wrap_summary(line: str) -> str:
            indent, expr = line.split("const summary = ",1)
            expr = expr.rstrip("\n")
            if not expr.endswith(";"):
                raise RuntimeError("v1.37 runtime: summary comunale senza terminatore")
            return indent + "const summary = territoryProfile ? (options.find(option=>option.key===defaultTerritoryChoice) || options[0]) : (" + expr[:-1] + ");\n"
        b = edit_line_once(b, "const summary = distribution ?", wrap_summary, "summary territorio comunale")

        def wrap_aggregate(line: str) -> str:
            indent, expr = line.split("const aggregateSummary = ",1)
            expr = expr.rstrip("\n")
            if not expr.endswith(";"):
                raise RuntimeError("v1.37 runtime: aggregateSummary senza terminatore")
            return indent + "const aggregateSummary = territoryProfile ? compositeSelectionAggregate(metric,defaultTerritoryChoice) : (" + expr[:-1] + ");\n"
        b = edit_line_once(b, "const aggregateSummary = distribution ?", wrap_aggregate, "aggregato territorio comunale")

        b = edit_line_once(b, "const panelOverline =", lambda line: line.replace(": hydroRisk ? 'Matrice ufficiale ISPRA' : composite ?", ": territoryProfile ? 'Letture territoriali' : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ?", 1), "overline territorio comunale")
        b = edit_line_once(b, "const panelTitle =", lambda line: line.replace(": hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ?", ": territoryProfile ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ?", 1), "titolo territorio comunale")
        b = edit_line_once(b, "const selector = demographicBreakdown ?", lambda line: line.replace("${index===0?'selected':''}", "${option.key===(territoryProfile?defaultTerritoryChoice:options[0]?.key)?'selected':''}", 1), "selettore territorio comunale")
        b = edit_line_once(b, "townBenchmarkMarkup(metric, row, town)", lambda line: line.replace("metricKey.startsWith('slowMobility') || demographicBreakdown", "metricKey.startsWith('slowMobility') || territoryProfile || demographicBreakdown", 1), "benchmark territorio comunale")
        b = edit_line_once(b, "const initialChoice=options[0]?.key || 'summary';", lambda line: line.replace("const initialChoice=options[0]?.key || 'summary';", "const initialChoice=territoryProfile ? defaultTerritoryChoice : (options[0]?.key || 'summary');", 1), "choice territorio comunale")
        b = insert_after_line(b, "updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);", "      updateTerritoryProfileTownPosition(metric,row,initialChoice,initialPosition);\n", "confronto iniziale territorio comunale")
        b = insert_after_line(b, "updateExtractiveTownPosition(metric,row,choice,position);", "        updateTerritoryProfileTownPosition(metric,row,choice,position);\n", "confronto dinamico territorio comunale")
        return b
    app03 = patch_function(app03, "renderTownMetric", town_render)

    def indicator_comparison(b: str) -> str:
        addition = "    if (isTerritoryProfileType(metric)) { const view=arguments[4] || {choice:financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice,scale:metric.meta.compositeType==='protectedAreasProfile'?'percent':'value'}; return `<div class=\"indicator-composite-table territory-indicator-comparison\"><div class=\"compare-chart-toolbar\">${compositeCompareControls(metric,view.choice,view.scale)}</div><div class=\"comparison-bars\" data-metric-key=\"${html(metricKey)}\" data-composite-choice=\"${html(view.choice)}\" data-composite-scale=\"${html(view.scale)}\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`; }\n"
        return insert_after_line(b, "const rows = [...metric.rows]", addition, "confronto scheda territorio")
    app05 = patch_function(app05, "indicatorComparisonTable", indicator_comparison)

    history_helpers = """
  function territoryProfileHistoryChart(metric,choice,territory='__versilia') {
    const part0=metric.rows?.[0]?.parts?.find(part=>part.key===choice) || metric.rows?.[0]?.parts?.[0] || {};
    const unit=part0.unit || metric.meta.unit;
    const options=[{key:'__versilia',label:'Versilia',source:metric.aggregate},...(metric.rows||[]).map(row=>({key:String(row.code||row.slug||row.town),label:row.town,source:row}))];
    const selected=options.find(item=>item.key===String(territory)) || options[0];
    const series=selected.source?.seriesByView?.[choice];
    if (!series?.years?.length) return '<div class="indicator-history-empty"><strong>Serie storica non disponibile per questa lettura</strong></div>';
    const label=part0.label || metric.meta.label;
    return `<div class="territory-history-chart-shell"><div class="land-cover-controls territory-history-controls"><label><span>Territorio</span><select data-territory-history-town>${options.map(item=>`<option value="${html(item.key)}" ${item.key===selected.key?'selected':''}>${html(item.label)}</option>`).join('')}</select></label></div>${seriesChart(series,unit,`${metric.meta.label} · ${label} · ${selected.label}`)}</div>`;
  }

  function territoryProfileIndicatorAsideMarkup(metric,choice,scale='value') {
    const selected=compositeCompareAggregate(metric,choice,scale);
    return `<span>${html(selected.label)}</span><strong>${html(formatValue(selected.value,selected.unit))}</strong><p>${html(selected.note || metric.aggregate?.note || '')}</p>`;
  }

"""
    app05 = replace_once(app05, "  function financialProfileHistoryTable(metric,choice='part-0') {\n", history_helpers + "  function financialProfileHistoryTable(metric,choice='part-0') {\n", "helper storico scheda territorio")

    app05 = patch_function(app05, "indicatorHistoryTable", lambda b: insert_after_line(b, "financialProfileHistoryTable(metric,financialChoice)", "    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return territoryProfileHistoryChart(metric,choice); }\n", "storico scheda territorio"))

    def indicator_render(b: str) -> str:
        b = insert_after_line(b, "const hydroRisk = metric.meta.compositeType === 'hydroRisk';", "    const territoryProfile = isTerritoryProfileType(metric);\n", "flag scheda territorio")
        b = insert_after_line(b, "const initialHydroAggregate =", "    const initialTerritoryView = territoryProfile ? compositeCompareDefaults(metric) : null;\n    const initialTerritoryChoice = initialTerritoryView?.choice || null;\n", "default scheda territorio")
        b = edit_line_once(b, "const historyCount =", lambda line: line.replace("const historyCount = metric.rows.filter(row => row.series?.years?.length).length;", "const historyCount = territoryProfile ? metric.rows.filter(row => Object.values(row.seriesByView || {}).some(series=>series?.years?.length)).length : metric.rows.filter(row => row.series?.years?.length).length;", 1), "history count territorio")
        def layout_edit(line: str) -> str:
            line = line.replace("indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)", "indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView, initialTerritoryView)", 1)
            return line.replace(": hydroRisk ? `<span>${html(initialHydroAggregate.label)}", ": territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice,initialTerritoryView?.scale || 'value') : hydroRisk ? `<span>${html(initialHydroAggregate.label)}", 1)
        b = edit_line_once(b, "indicator-current-layout", layout_edit, "layout scheda territorio")
        b = edit_line_once(b, "indicator-benchmark page-width", lambda line: line.replace("(financialProfile || hydroRisk ||", "(financialProfile || territoryProfile || hydroRisk ||", 1), "benchmark scheda territorio")
        b = edit_line_once(b, "indicator-history page-width", lambda line: line.replace("indicatorHistoryTable(metric,initialFinancialChoice)", "indicatorHistoryTable(metric,territoryProfile ? initialTerritoryChoice : initialFinancialChoice)", 1), "storico iniziale territorio")
        events = """    if (territoryProfile) {
      const currentSection=document.querySelector('.indicator-current');
      let territoryView={...initialTerritoryView};
      const renderTerritory=()=>{
        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');
        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');
        const historyHost=document.querySelector('[data-financial-indicator-history]');
        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,territoryView.choice,initialHydroView,territoryView);
        if(aggregateHost) aggregateHost.innerHTML=territoryProfileIndicatorAsideMarkup(metric,territoryView.choice,territoryView.scale);
        if(historyHost) historyHost.innerHTML=territoryProfileHistoryChart(metric,territoryView.choice);
      };
      currentSection?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-composite-component]');
        if(select&&currentSection.contains(select)){ territoryView={...territoryView,choice:select.value}; renderTerritory(); }
      });
      currentSection?.addEventListener('click',event=>{
        const button=event.target.closest('button[data-composite-scale]');
        if(button&&currentSection.contains(button)){ territoryView={...territoryView,scale:button.dataset.compositeScale}; renderTerritory(); }
      });
      const territoryHistoryHost=document.querySelector('[data-financial-indicator-history]');
      territoryHistoryHost?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-territory-history-town]');
        if(select&&territoryHistoryHost.contains(select)) territoryHistoryHost.innerHTML=territoryProfileHistoryChart(metric,territoryView.choice,select.value);
      });
    }
"""
        return insert_after_line(b, "document.querySelector('[data-print]')", events, "eventi scheda territorio")
    app05 = patch_function(app05, "renderIndicator", indicator_render)

    # Estende la visual grammar canonica ai nuovi profili territoriali: in questo
    # modo confronti generali e pagine indicatore usano la stessa grammatica
    # lollipop/dotplot, compresa la scala firmata per i valori netti negativi.
    visual = patch_function(visual, "metricKeyFor", lambda b: insert_after_line(b, "function metricKeyFor(root)", "    const direct = root?.dataset?.metricKey;\n    if (direct) return direct;\n", "metric key diretto territorio"))
    visual = patch_function(visual, "unitKind", lambda b: insert_after_line(b, "const token = String(unit || '').trim().toLowerCase();", "    if (token === 'sqm_per_resident') return 'sqm-per-resident';\n    if (token === 'km_per_km2') return 'km-per-km2';\n", "unita visual grammar territorio"))
    visual = patch_function(visual, "formatAxis", lambda b: insert_after_line(b, "if (kind === 'hectares-per-farm') return `${formatted} ha/azienda`;", "    if (kind === 'sqm-per-resident') return `${formatted} m²/residente`;\n    if (kind === 'km-per-km2') return `${formatted} km/km²`;\n", "formatter visual grammar territorio"))

    def visual_selection(b: str) -> str:
        addition = "    if (['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile'].includes(type)) { const part=(row?.parts || []).find(item=>item.key===choice) || row?.parts?.[0] || {}; const hectares=type==='protectedAreasProfile' && scale==='hectares'; return {value:hectares?part.ha:part.value,unit:hectares?'hectares':(part.unit || metric?.meta?.unit || '')}; }\n"
        return insert_after_line(b, "const type = metric?.meta?.compositeType;", addition, "selezione visual grammar territorio")
    visual = patch_function(visual, "compositeSelectionFor", visual_selection)

    def visual_aggregate(b: str) -> str:
        addition = "    if (['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile'].includes(type)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; const hectares=type==='protectedAreasProfile' && scale==='hectares'; return {value:hectares?part.ha:part.value,label:`Versilia · ${part.label || metric.meta.label}`,unit:hectares?'hectares':(part.unit || metric?.meta?.unit || '')}; }\n"
        return insert_after_line(b, "const type = metric?.meta?.compositeType;", addition, "aggregato visual grammar territorio")
    visual = patch_function(visual, "compositeAggregateFor", visual_aggregate)

    # Collega seriesByView al layer storico generale e riutilizza i tooltip
    # canonici anche dopo i rerender del wrapper storico.
    ux_core = replace_once(
        ux_core,
        "    wireViewShell,\n    escapeHtml\n",
        "    wireViewShell,\n    wireHistoryTooltips,\n    formatValue,\n    escapeHtml\n",
        "export tooltip/storico territorio",
    )

    ux_helper = """
  const TERRITORY_PROFILE_HISTORY_TYPES = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']);
  function isTerritoryProfileHistoryMetric(metric) {
    return TERRITORY_PROFILE_HISTORY_TYPES.has(metric?.meta?.compositeType);
  }

"""
    ux_history = replace_once(ux_history, "  const LIBRARY_HISTORY_KEYS = new Set(['libraryLoansPerResident','libraryActiveBorrowersPer100','libraryWeeklyOpeningHours']);\n", "  const LIBRARY_HISTORY_KEYS = new Set(['libraryLoansPerResident','libraryActiveBorrowersPer100','libraryWeeklyOpeningHours']);\n" + ux_helper, "helper storico collettivo territorio")

    def ux_composite_choice(b: str) -> str:
        b = edit_line_once(b, "includes(metric?.meta?.compositeType)) return metric;", lambda line: line.replace("'sexBreakdown']", "'sexBreakdown','soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']", 1), "abilita choice storico territorio")
        territory_case = """    if (isTerritoryProfileHistoryMetric(metric)) {
    const selected=(choice && choice !== 'summary') ? choice : (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key);
    const template=(metric.aggregate?.parts || metric.rows?.[0]?.parts || []).find(part=>part.key===selected) || metric.aggregate?.parts?.[0] || metric.rows?.[0]?.parts?.[0] || {};
    const unit=template.unit || metric.meta.unit;
    clone.meta.unit=unit;
    clone.meta.label=template.label ? `${metric.meta.label} · ${template.label}` : metric.meta.label;
    clone.rows=metric.rows.map(row=>{
      const part=(row.parts || []).find(item=>item.key===selected) || row.parts?.[0] || {};
      const value=part.value === null || part.value === undefined || part.value === '' ? undefined : Number(part.value);
      return { ...row, value, formatted:Number.isFinite(value)?toolkit.formatValue(value,unit):'n.d.', series:row.seriesByView?.[selected] || null };
    });
    const aggregatePart=(metric.aggregate?.parts || []).find(item=>item.key===selected) || metric.aggregate?.parts?.[0] || {};
    clone.aggregate={ ...metric.aggregate, value:aggregatePart.value, label:`Versilia · ${aggregatePart.label || metric.meta.label}`, series:metric.aggregate?.seriesByView?.[selected] || null };
    return clone;
  }
"""
        return insert_after_line(b, "const clone = { ...metric", territory_case, "choice seriesByView territorio")
    ux_history = patch_function(ux_history, "compositeChoiceMetric", ux_composite_choice)

    ux_history = patch_function(ux_history, "refreshTownCompositeCurrent", lambda b: edit_line_once(b, "includes(metric?.meta?.compositeType)) return;", lambda line: line.replace("'sexBreakdown']", "'sexBreakdown','soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']", 1), "refresh corrente territorio"))

    def ux_enhance_compare(b: str) -> str:
        return edit_line_once(b, "const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown'", lambda line: line.replace("selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null", "(selected.metric?.meta?.compositeType === 'sexBreakdown' || isTerritoryProfileHistoryMetric(selected.metric)) ? currentCompositeChoice() : null", 1), "choice storico compare territorio")
    ux_history = patch_function(ux_history, "enhanceCompare", ux_enhance_compare)

    def ux_enhance_town(b: str) -> str:
        b = edit_line_once(b, "const selectedChoice = selected.metric?.meta?.compositeType === 'sexBreakdown'", lambda line: line.replace("selected.metric?.meta?.compositeType === 'sexBreakdown' ? currentCompositeChoice() : null", "(selected.metric?.meta?.compositeType === 'sexBreakdown' || isTerritoryProfileHistoryMetric(selected.metric)) ? currentCompositeChoice() : null", 1), "choice storico town territorio")
        return insert_after_line(b, "wireShell(panel.querySelector('.ux-view-shell'), 'ov-town-view', selectedTown, false);", "    panel.querySelectorAll('.composite-fixed-detail .trend-chart').forEach(chart=>toolkit.wireHistoryTooltips?.(chart));\\n", "tooltip fixed detail territorio")
    ux_history = patch_function(ux_history, "enhanceTown", ux_enhance_town)

    ux_history = replace_once(ux_history, "      if (metric.meta?.compositeType === 'sexBreakdown') {\n", "      if (metric.meta?.compositeType === 'sexBreakdown' || isTerritoryProfileHistoryMetric(metric)) {\n", "aggiorna storico town al cambio lettura territorio")

    APP00.write_text(app00, encoding="utf-8")
    APP03.write_text(app03, encoding="utf-8")
    APP05.write_text(app05, encoding="utf-8")
    VISUAL_GRAMMAR.write_text(visual, encoding="utf-8")
    UX_HISTORY_CORE.write_text(ux_core, encoding="utf-8")
    UX_HISTORY.write_text(ux_history, encoding="utf-8")
    print("Renderer territorio v1.37 applicato: quote comunali, storico collettivo e tooltip canonici.")


if __name__ == "__main__":
    main()
