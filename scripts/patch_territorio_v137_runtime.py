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

    if SENTINEL in app03:
        required = ("sqm_per_resident", "km_per_km2", "territoryProfileHistoryTable")
        if not all(token in app00 + app03 + app05 for token in required):
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

    app03 = patch_function(app03, "compositeCompareDefaults", lambda b: insert_after_line(b, "function compositeCompareDefaults(metric)", "    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:'value' };\n", "default territorio"))
    app03 = patch_function(app03, "compositeCompareSelection", lambda b: insert_after_line(b, "function compositeCompareSelection(metric, row, choice", "    if (isTerritoryProfileType(metric)) { const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,part}; }\n", "selezione territorio"))
    app03 = patch_function(app03, "compositeCompareAggregate", lambda b: insert_after_line(b, "function compositeCompareAggregate(metric, choice", "    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note}; }\n", "aggregato territorio"))
    app03 = patch_function(app03, "compositeCompareControls", lambda b: insert_after_line(b, "function compositeCompareControls(metric, choice", "    if (isTerritoryProfileType(metric)) { const parts=metric.rows?.[0]?.parts || []; return `<div class=\"compare-view-controls territory-profile-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${parts.map(part=>`<option value=\"${html(part.key)}\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`; }\n", "controlli territorio"))

    def town_markup(b: str) -> str:
        addition = (
            "    if (isTerritoryProfileType(metric)) {\n"
            "      const histories=parts.filter(part=>row.seriesByView?.[part.key]?.years?.length).map(part=>`<details class=\"detail-disclosure territory-profile-history\" ${part.key===(metric.meta.defaultView||parts[0]?.key)?'open':''}><summary><span>${html(part.label)}</span><small>Serie ufficiale</small></summary><div>${seriesChart(row.seriesByView[part.key],part.unit || metric.meta.unit,`${metric.meta.label} · ${part.label} · ${row.town}`)}</div></details>`).join('');\n"
            "      return `<div class=\"composite-town-mobility territory-profile-town\">${parts.map(part=>`<article class=\"${part.key===(metric.meta.defaultView||parts[0]?.key)?'balance':''}\"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>${histories}`;\n"
            "    }\n"
        )
        return insert_after_line(b, "const parts = row.parts || [];", addition, "dettaglio comunale territorio")
    app03 = patch_function(app03, "compositeTownMarkup", town_markup)

    app03 = patch_function(app03, "compositeSelectionOptions", lambda b: insert_after_line(b, "function compositeSelectionOptions(metric, row)", "    if (isTerritoryProfileType(metric)) return (row.parts || []).map(part=>({key:part.key,label:part.selectorLabel || part.label,value:part.value,unit:part.unit || metric.meta.unit,formatted:formatMetricRowValue(row,part.value,part.unit || metric.meta.unit),part}));\n", "opzioni territorio"))
    app03 = patch_function(app03, "compositeSelectionAggregate", lambda b: insert_after_line(b, "function compositeSelectionAggregate(metric, choice)", "    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }\n", "aggregato selettore territorio"))
    app03 = patch_function(app03, "compositeSelectionRank", lambda b: insert_after_line(b, "const values = metric.rows.map(r => {", "      if (isTerritoryProfileType(metric)) { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:part?.value===null||part?.value===undefined?NaN:Number(part.value)}; }\n", "rank territorio"))

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
        return b
    app03 = patch_function(app03, "renderTownMetric", town_render)

    def indicator_comparison(b: str) -> str:
        addition = "    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return `<div class=\"indicator-composite-table territory-indicator-comparison\"><div class=\"compare-chart-toolbar\">${compositeCompareControls(metric,choice,'value')}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(choice)}\">${compositeCompareBarRows(data,metricKey,choice,'value')}</div></div>`; }\n"
        return insert_after_line(b, "const rows = [...metric.rows]", addition, "confronto scheda territorio")
    app05 = patch_function(app05, "indicatorComparisonTable", indicator_comparison)

    history_helpers = """
  function territoryProfileHistoryTable(metric,choice) {
    const part0=metric.rows?.[0]?.parts?.find(part=>part.key===choice) || metric.rows?.[0]?.parts?.[0] || {};
    const unit=part0.unit || metric.meta.unit;
    const rows=[...metric.rows].sort((a,b)=>a.town.localeCompare(b.town,'it'));
    const sources=rows.map(row=>({label:row.town,series:row.seriesByView?.[choice]})).filter(source=>source.series?.years?.length);
    if (!sources.length) return '<div class="indicator-history-empty"><strong>Serie storica non disponibile per questa lettura</strong></div>';
    const years=[...new Set(sources.flatMap(source=>source.series.years))].sort((a,b)=>Number(a)-Number(b));
    return `<div class="indicator-table-scroll"><table class="indicator-history-table territory-history-table"><thead><tr><th scope="col">Comune</th>${years.map(year=>`<th scope="col">${html(year)}</th>`).join('')}</tr></thead><tbody>${sources.map(source=>{const values=new Map(source.series.years.map((year,index)=>[String(year),source.series.values[index]]));return `<tr><th scope="row">${html(source.label)}</th>${years.map(year=>`<td>${values.has(String(year))?html(formatValue(values.get(String(year)),unit)):'—'}</td>`).join('')}</tr>`;}).join('')}</tbody></table></div>`;
  }

  function territoryProfileIndicatorAsideMarkup(metric,choice) {
    const selected=compositeCompareAggregate(metric,choice,'value');
    return `<span>${html(selected.label)}</span><strong>${html(formatValue(selected.value,selected.unit))}</strong><p>${html(selected.note || metric.aggregate?.note || '')}</p>`;
  }

"""
    app05 = replace_once(app05, "  function financialProfileHistoryTable(metric,choice='part-0') {\n", history_helpers + "  function financialProfileHistoryTable(metric,choice='part-0') {\n", "helper storico scheda territorio")

    app05 = patch_function(app05, "indicatorHistoryTable", lambda b: insert_after_line(b, "financialProfileHistoryTable(metric,financialChoice)", "    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return territoryProfileHistoryTable(metric,choice); }\n", "storico scheda territorio"))

    def indicator_render(b: str) -> str:
        b = insert_after_line(b, "const hydroRisk = metric.meta.compositeType === 'hydroRisk';", "    const territoryProfile = isTerritoryProfileType(metric);\n", "flag scheda territorio")
        b = insert_after_line(b, "const initialHydroAggregate =", "    const initialTerritoryChoice = territoryProfile ? (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key) : null;\n", "default scheda territorio")
        b = edit_line_once(b, "const historyCount =", lambda line: line.replace("const historyCount = metric.rows.filter(row => row.series?.years?.length).length;", "const historyCount = territoryProfile ? metric.rows.filter(row => Object.values(row.seriesByView || {}).some(series=>series?.years?.length)).length : metric.rows.filter(row => row.series?.years?.length).length;", 1), "history count territorio")
        def layout_edit(line: str) -> str:
            line = line.replace("indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)", "indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)", 1)
            return line.replace(": hydroRisk ? `<span>${html(initialHydroAggregate.label)}", ": territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : hydroRisk ? `<span>${html(initialHydroAggregate.label)}", 1)
        b = edit_line_once(b, "indicator-current-layout", layout_edit, "layout scheda territorio")
        b = edit_line_once(b, "indicator-benchmark page-width", lambda line: line.replace("(financialProfile || hydroRisk ||", "(financialProfile || territoryProfile || hydroRisk ||", 1), "benchmark scheda territorio")
        b = edit_line_once(b, "indicator-history page-width", lambda line: line.replace("indicatorHistoryTable(metric,initialFinancialChoice)", "indicatorHistoryTable(metric,territoryProfile ? initialTerritoryChoice : initialFinancialChoice)", 1), "storico iniziale territorio")
        events = """    if (territoryProfile) {
      const currentSection=document.querySelector('.indicator-current');
      const applyTerritoryChoice=choice=>{
        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');
        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');
        const historyHost=document.querySelector('[data-financial-indicator-history]');
        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,choice,initialHydroView);
        if(aggregateHost) aggregateHost.innerHTML=territoryProfileIndicatorAsideMarkup(metric,choice);
        if(historyHost) historyHost.innerHTML=territoryProfileHistoryTable(metric,choice);
      };
      currentSection?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-composite-component]');
        if(select&&currentSection.contains(select)) applyTerritoryChoice(select.value);
      });
    }
"""
        return insert_after_line(b, "document.querySelector('[data-print]')", events, "eventi scheda territorio")
    app05 = patch_function(app05, "renderIndicator", indicator_render)

    APP00.write_text(app00, encoding="utf-8")
    APP03.write_text(app03, encoding="utf-8")
    APP05.write_text(app05, encoding="utf-8")
    print("Renderer territorio v1.37 applicato ai renderer canonici post-v1.36.")


if __name__ == "__main__":
    main()
