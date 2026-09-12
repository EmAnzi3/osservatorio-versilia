#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/patch_territorio_v137_runtime.py')
s = p.read_text(encoding='utf-8')


def once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: attesa 1 occorrenza, trovate {n}')
    s = s.replace(old, new, 1)

once(
    'APP05 = ROOT / "assets" / "app-parts" / "05.txt"\nSENTINEL = "territoryProfileTypes"',
    'APP05 = ROOT / "assets" / "app-parts" / "05.txt"\nVISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"\nSENTINEL = "territoryProfileTypes"',
    'visual grammar path',
)
once(
    '    app05 = APP05.read_text(encoding="utf-8")\n\n    if SENTINEL in app03:',
    '    app05 = APP05.read_text(encoding="utf-8")\n    visual = VISUAL_GRAMMAR.read_text(encoding="utf-8")\n\n    if SENTINEL in app03:',
    'visual grammar read',
)
once(
    '        required = ("sqm_per_resident", "km_per_km2", "territoryProfileHistoryTable")\n        if not all(token in app00 + app03 + app05 for token in required):',
    '        required = ("sqm_per_resident", "km_per_km2", "territoryProfileHistoryChart", "data-metric-key", "sqm-per-resident")\n        if not all(token in app00 + app03 + app05 + visual for token in required):',
    'idempotency contract',
)

once(
    '<div class=\\"comparison-bars\\" data-composite-choice=\\"${html(view.choice)}\\" data-composite-scale=\\"${html(view.scale)}\\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>',
    '<div class=\\"comparison-bars\\" data-metric-key=\\"${html(metricKey)}\\" data-composite-choice=\\"${html(view.choice)}\\" data-composite-scale=\\"${html(view.scale)}\\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>',
    'indicator metric key',
)

start = s.find('  function territoryProfileHistoryTable(metric,choice) {')
end = s.find('\n\n  function territoryProfileIndicatorAsideMarkup', start)
if start < 0 or end < 0:
    raise RuntimeError('history helper boundaries not found')
new_history = r'''  function territoryProfileHistoryChart(metric,choice,territory='__versilia') {
    const part0=metric.rows?.[0]?.parts?.find(part=>part.key===choice) || metric.rows?.[0]?.parts?.[0] || {};
    const unit=part0.unit || metric.meta.unit;
    const options=[{key:'__versilia',label:'Versilia',source:metric.aggregate},...(metric.rows||[]).map(row=>({key:String(row.code||row.slug||row.town),label:row.town,source:row}))];
    const selected=options.find(item=>item.key===String(territory)) || options[0];
    const series=selected.source?.seriesByView?.[choice];
    if (!series?.years?.length) return '<div class="indicator-history-empty"><strong>Serie storica non disponibile per questa lettura</strong></div>';
    const label=part0.label || metric.meta.label;
    return `<div class="territory-history-chart-shell"><div class="land-cover-controls territory-history-controls"><label><span>Territorio</span><select data-territory-history-town>${options.map(item=>`<option value="${html(item.key)}" ${item.key===selected.key?'selected':''}>${html(item.label)}</option>`).join('')}</select></label></div>${seriesChart(series,unit,`${metric.meta.label} · ${label} · ${selected.label}`)}</div>`;
  }'''
s = s[:start] + new_history + s[end:]
s = s.replace('territoryProfileHistoryTable(metric,choice)', 'territoryProfileHistoryChart(metric,choice)', 1)
s = s.replace('historyHost.innerHTML=territoryProfileHistoryTable(metric,territoryView.choice);', 'historyHost.innerHTML=territoryProfileHistoryChart(metric,territoryView.choice);', 1)

anchor = """      currentSection?.addEventListener('click',event=>{\n        const button=event.target.closest('button[data-composite-scale]');\n        if(button&&currentSection.contains(button)){ territoryView={...territoryView,scale:button.dataset.compositeScale}; renderTerritory(); }\n      });\n"""
if s.count(anchor) != 1:
    raise RuntimeError('history event anchor not unique')
s = s.replace(anchor, anchor + """      const territoryHistoryHost=document.querySelector('[data-financial-indicator-history]');\n      territoryHistoryHost?.addEventListener('change',event=>{\n        const select=event.target.closest('select[data-territory-history-town]');\n        if(select&&territoryHistoryHost.contains(select)) territoryHistoryHost.innerHTML=territoryProfileHistoryChart(metric,territoryView.choice,select.value);\n      });\n""", 1)

write_anchor = '    APP00.write_text(app00, encoding="utf-8")\n'
if s.count(write_anchor) != 1:
    raise RuntimeError('write anchor not unique')
visual_patch = r'''    # Estende la visual grammar canonica ai nuovi profili territoriali: in questo
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
    visual = patch_function(visual, "enhanceTownPosition", lambda b: insert_after_line(b, "const metric = data.metrics?.[metricKey];", "    if (['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile'].includes(metric?.meta?.compositeType)) return;\n", "town position territorio"))

'''
s = s.replace(write_anchor, visual_patch + write_anchor, 1)
once(
    '    APP05.write_text(app05, encoding="utf-8")\n    print("Renderer territorio v1.37 applicato ai renderer canonici post-v1.36.")',
    '    APP05.write_text(app05, encoding="utf-8")\n    VISUAL_GRAMMAR.write_text(visual, encoding="utf-8")\n    print("Renderer territorio v1.37 applicato ai renderer canonici post-v1.36.")',
    'visual grammar write',
)

p.write_text(s, encoding='utf-8')
print('Patch visuale v1.37 aggiornata: lollipop canonici + storico a linee.')
