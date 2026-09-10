from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP03=ROOT/'assets/app-parts/03.txt'
APP05=ROOT/'assets/app-parts/05.txt'
if ("metric.meta.compositeType === 'hydroRisk'" in APP03.read_text(encoding='utf-8')
    and "case 'decile'" in (ROOT/'assets/app-parts/00.txt').read_text(encoding='utf-8')
    and "hydro-risk-indicator-comparison" in APP05.read_text(encoding='utf-8')):
    print('Runtime fragilità v1.33.0 già materializzato.')
    raise SystemExit(0)

def replace_once(text, old, new, label):
    c=text.count(old)
    if c!=1: raise RuntimeError(f'{label}: atteso 1, trovato {c}')
    return text.replace(old,new,1)

def patch_function(text, name, callback):
    marker=f'  function {name}('
    start=text.find(marker)
    if start<0: raise RuntimeError(f'funzione {name} non trovata')
    end=text.find('\n  function ', start+len(marker))
    if end<0: end=len(text)
    before=text[:start]; block=text[start:end]; after=text[end:]
    patched=callback(block)
    return before+patched+after

# app 00
p=ROOT/'assets/app-parts/00.txt'; s=p.read_text()
s=replace_once(s,"      case 'minutes': return `${number1.format(v)} min`;","      case 'minutes': return `${number1.format(v)} min`;\n      case 'decile': return `${number0.format(v)}/10`;\n      case 'ventile': return `${number0.format(v)}/20`;",'formatValue ordinal')
p.write_text(s)

p=ROOT/'assets/app-parts/03.txt'; s=p.read_text()

def f_defaults(b):
    return replace_once(b,"    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };","    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n    if (metric.meta.compositeType === 'hydroRisk') return { choice:metric.meta.defaultScenario || metric.rows?.[0]?.parts?.[0]?.key || '', scale:'residentsPct' };",'defaults hydro')
s=patch_function(s,'compositeCompareDefaults',f_defaults)

def f_sel(b):
    old="    if (metric.meta.compositeType === 'stock') {"
    new="    if (metric.meta.compositeType === 'hydroRisk') {\n      const part = (row.parts || []).find(item => item.key === choice) || row.parts?.[0] || {};\n      const territory = scale === 'areaPct';\n      return { value: territory ? part.areaPct : part.residentsPct, unit:'percent', part };\n    }\n"+old
    return replace_once(b,old,new,'selection hydro')
s=patch_function(s,'compositeCompareSelection',f_sel)

def f_agg(b):
    old="    if (metric.meta.compositeType === 'stock') {"
    new="    if (metric.meta.compositeType === 'hydroRisk') {\n      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};\n      const territory = scale === 'areaPct';\n      return { value: territory ? part.areaPct : part.residentsPct, unit:'percent', label:`Versilia · ${territory ? 'territorio' : 'residenti'} · ${part.label || choice}`, note:metric.aggregate?.note };\n    }\n"+old
    return replace_once(b,old,new,'aggregate hydro')
s=patch_function(s,'compositeCompareAggregate',f_agg)

def f_controls(b):
    old="    if (metric.meta.compositeType === 'stock') {"
    new="    if (metric.meta.compositeType === 'hydroRisk') {\n      const parts = metric.rows?.[0]?.parts || [];\n      return `<div class=\"compare-view-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Scenario')}</span><select data-composite-component>${parts.map(part=>`<option value=\"${html(part.key)}\" ${part.key === choice ? 'selected' : ''}>${html(part.label)}</option>`).join('')}</select></label><div><span class=\"compare-view-label\">Lettura</span><div class=\"scale-switch compact\" role=\"group\" aria-label=\"Lettura del rischio idrogeologico\"><button type=\"button\" data-composite-scale=\"residentsPct\" class=\"${scale === 'residentsPct' ? 'active' : ''}\">Residenti</button><button type=\"button\" data-composite-scale=\"areaPct\" class=\"${scale === 'areaPct' ? 'active' : ''}\">Territorio</button></div></div></div>`;\n    }\n"+old
    return replace_once(b,old,new,'controls hydro')
s=patch_function(s,'compositeCompareControls',f_controls)

def f_town_markup(b):
    old="    if (metric.meta.compositeType === 'stock') {"
    new="    if (metric.meta.compositeType === 'hydroRisk') {\n      const history = row.hazardHistory?.length ? `<details class=\"detail-disclosure\"><summary><span>Storico P3+P4</span><small>superficie comunale · %</small></summary><div class=\"indicator-table-scroll\"><table class=\"indicator-values-table\"><thead><tr><th>Anno</th><th>Territorio P3+P4</th></tr></thead><tbody>${row.hazardHistory.map(item=>`<tr><th>${html(item.year)}</th><td>${html(formatValue(item.value,'percent'))}</td></tr>`).join('')}</tbody></table></div></details>` : '';\n      return `<div class=\"indicator-table-scroll\"><table class=\"indicator-values-table\"><thead><tr><th>${html(metric.meta.selectorLabel || 'Scenario')}</th><th>Superficie km²</th><th>Territorio %</th><th>Residenti</th><th>Residenti %</th></tr></thead><tbody>${parts.map(part=>`<tr><th>${html(part.label)}</th><td>${html(number2.format(part.areaKm2))}</td><td>${html(formatValue(part.areaPct,'percent'))}</td><td>${html(number0.format(part.residents))}</td><td>${html(formatValue(part.residentsPct,'percent'))}</td></tr>`).join('')}</tbody></table></div>${metric.meta.scenarioNote ? `<p class=\"aggregate-note\"><strong>Come leggere gli scenari.</strong> ${html(metric.meta.scenarioNote)}</p>` : ''}<p class=\"aggregate-note\">Popolazione di riferimento: Istat ${html(row.populationReference)}. Superficie comunale: ${html(number2.format(row.municipalAreaKm2))} km².</p>${history}`;\n    }\n"+old
    return replace_once(b,old,new,'town hydro')
s=patch_function(s,'compositeTownMarkup',f_town_markup)

def f_options(b):
    old="    if (metric.meta.compositeType === 'stock') return ["
    new="    if (metric.meta.compositeType === 'hydroRisk') {\n      const preferred = metric.meta.defaultScenario;\n      return [...(row.parts || [])].sort((a,b)=>(a.key===preferred?-1:b.key===preferred?1:0)).map(part=>({ key:part.key, label:part.label, value:part.residentsPct, unit:'percent', formatted:formatValue(part.residentsPct,'percent'), part }));\n    }\n"+old
    return replace_once(b,old,new,'options hydro')
s=patch_function(s,'compositeSelectionOptions',f_options)

def f_selagg(b):
    old="    if (metric.meta.compositeType === 'stock') {"
    new="    if (metric.meta.compositeType === 'hydroRisk') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; return {label:`Versilia · residenti · ${part.label || choice}`,value:part.residentsPct,unit:'percent',formatted:formatValue(part.residentsPct,'percent')}; }\n"+old
    return replace_once(b,old,new,'selection aggregate hydro')
s=patch_function(s,'compositeSelectionAggregate',f_selagg)

def f_rank(b):
    old="      if (metric.meta.compositeType === 'stock') return { code:r.code, value:Number(choice === 'count' ? r.count : r.value) };"
    new="      if (metric.meta.compositeType === 'hydroRisk') { const part=(r.parts || []).find(item=>item.key===choice)||{}; return {code:r.code,value:Number(part.residentsPct)}; }\n"+old
    return replace_once(b,old,new,'rank hydro')
s=patch_function(s,'compositeSelectionRank',f_rank)

def f_render_compare(b):
    b=replace_once(b,"['stock','mobility','omi','securityMeasures','agricultureProfile','financialProfile','ratioProfile','demographicBreakdown','sexBreakdown'].includes(compositeType)","['stock','mobility','omi','securityMeasures','agricultureProfile','financialProfile','ratioProfile','demographicBreakdown','sexBreakdown','hydroRisk'].includes(compositeType)",'selectable compare hydro')
    b=replace_once(b,"      const financialHistory = compositeType === 'financialProfile' ? financialProfileAggregateHistoryMarkup(metric,view.choice) : '';\n      bars.innerHTML = `<div class=\"topic-bars selectable-topic-bars${compositeType === 'financialProfile' ? ' financial-topic-bars' : ''}\"><div class=\"compare-chart-toolbar\"><div class=\"compare-chart-legend-host\" aria-live=\"polite\"></div>${chartControls}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(view.choice)}\" data-composite-scale=\"${html(view.scale)}\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${financialHistory}${note}${stockDetail}</div>`;","      const financialHistory = compositeType === 'financialProfile' ? financialProfileAggregateHistoryMarkup(metric,view.choice) : '';\n      const scenarioNote = compositeType === 'hydroRisk' && metric.meta.scenarioNote ? `<p class=\"composite-compare-note\"><strong>Come leggere gli scenari:</strong> ${html(metric.meta.scenarioNote)}</p>` : '';\n      bars.innerHTML = `<div class=\"topic-bars selectable-topic-bars${compositeType === 'financialProfile' ? ' financial-topic-bars' : ''}\"><div class=\"compare-chart-toolbar\"><div class=\"compare-chart-legend-host\" aria-live=\"polite\"></div>${chartControls}</div>${scenarioNote}<div class=\"comparison-bars\" data-composite-choice=\"${html(view.choice)}\" data-composite-scale=\"${html(view.scale)}\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${financialHistory}${note}${stockDetail}</div>`;",'compare scenario note below toolbar')
    return b
s=patch_function(s,'renderCompareMetric',f_render_compare)

def f_csv(b):
    b=replace_once(b,"    const isSexBreakdown = metric.meta.compositeType === 'sexBreakdown';\n    const lines = isSexBreakdown ?","    const isSexBreakdown = metric.meta.compositeType === 'sexBreakdown';\n    const isHydroRisk = metric.meta.compositeType === 'hydroRisk';\n    const lines = isHydroRisk ? [['Comune','Codice Istat','Indicatore','Anno pericolosità','Classe / scenario','Superficie km²','Territorio %','Residenti esposti','Residenti esposti %','Popolazione di riferimento','Fonte']] : isSexBreakdown ?",'csv header hydro')
    b=replace_once(b,"    if (isSexBreakdown) {","    if (isHydroRisk) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town,row.code,label,metric.meta.year,part.label,part.areaKm2,part.areaPct,part.residents,part.residentsPct,row.populationReference,metric.sourceUrl])));\n    else if (isSexBreakdown) {",'csv rows hydro')
    return b
s=patch_function(s,'downloadMetricCSV',f_csv)

def f_render_town_metric(b):
    b=replace_once(b,"    const remediation = metric.meta.compositeType === 'remediationProceedings';","    const remediation = metric.meta.compositeType === 'remediationProceedings';\n    const hydroRisk = metric.meta.compositeType === 'hydroRisk';\n    const ordinalScale = metric.meta.ordinalScale || null;",'town flags')
    b=replace_once(b,"    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown;","    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || hydroRisk;",'town selectable')
    b=replace_once(b,"(omi || stock || securityMeasures) ? options[0] : null)","((omi || stock || securityMeasures || hydroRisk) ? options[0] : null)",'town summary')
    b=replace_once(b,"(securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)","securityMeasures ? compositeSelectionAggregate(metric,'part-0') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null)",'town aggregate summary')
    b=replace_once(b,"financialProfile ? `Indicatore ${initialFinancialReading.code}` : composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo'","financialProfile ? `Indicatore ${initialFinancialReading.code}` : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo'",'town overline')
    b=replace_once(b,"financialProfile ? initialFinancialReading.label : composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label)","financialProfile ? initialFinancialReading.label : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label)",'town title')
    b=replace_once(b,"    const positionMarkup = selectable\n      ? `<aside class=\"versilia-position composite-versilia-position\"","    const positionMarkup = ordinalScale\n      ? `<aside class=\"versilia-position ordinal-versilia-position\"><span class=\"overline\">Scala Istat</span><strong>${html(formatValue(row.value,metric.meta.unit))}<small>${html(ordinalScale.minLabel)} → ${html(ordinalScale.maxLabel)}</small></strong><p>Classe ordinale a scala fissa ${html(formatValue(ordinalScale.min,metric.meta.unit))}–${html(formatValue(ordinalScale.max,metric.meta.unit))}; non è una graduatoria di merito.</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value,metric.meta.unit))}</b></div></aside>`\n      : selectable\n      ? `<aside class=\"versilia-position composite-versilia-position\"",'ordinal position')
    b=replace_once(b,"['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)","['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)",'hydro no external benchmark')
    return b
s=patch_function(s,'renderTownMetric',f_render_town_metric)
p.write_text(s)

# app05 · canonical indicator pages
p=ROOT/'assets/app-parts/05.txt'; s=p.read_text()

def f_indicator_table(b):
    old="    if (metric.meta.compositeType === 'financialProfile') return `<div class=\"indicator-composite-table financial-indicator-comparison\"><div class=\"compare-chart-toolbar\"><div><span class=\"overline\">Confronto dei Comuni</span></div>${compositeCompareControls(metric,financialChoice,'value')}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(financialChoice)}\">${compositeCompareBarRows(data,metricKey,financialChoice,'value')}</div></div>`;\n    if (metric.meta.compositeType) return `<div class=\"indicator-composite-table\">${compositeCompareMarkup(data, metricKey)}</div>`;"
    new="    if (metric.meta.compositeType === 'financialProfile') return `<div class=\"indicator-composite-table financial-indicator-comparison\"><div class=\"compare-chart-toolbar\"><div><span class=\"overline\">Confronto dei Comuni</span></div>${compositeCompareControls(metric,financialChoice,'value')}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(financialChoice)}\">${compositeCompareBarRows(data,metricKey,financialChoice,'value')}</div></div>`;\n    if (metric.meta.compositeType === 'hydroRisk') {\n      const view = arguments[3] || compositeCompareDefaults(metric);\n      return `<div class=\"indicator-composite-table hydro-risk-indicator-comparison\"><div class=\"compare-chart-toolbar\"><div><span class=\"overline\">Confronto dei Comuni</span></div>${compositeCompareControls(metric,view.choice,view.scale)}</div>${metric.meta.scenarioNote ? `<p class=\"composite-compare-note\"><strong>Come leggere gli scenari:</strong> ${html(metric.meta.scenarioNote)}</p>` : ''}<div class=\"comparison-bars\" data-composite-choice=\"${html(view.choice)}\" data-composite-scale=\"${html(view.scale)}\">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div></div>`;\n    }\n    if (metric.meta.compositeType) return `<div class=\"indicator-composite-table\">${compositeCompareMarkup(data, metricKey)}</div>`;"
    return replace_once(b,old,new,'indicator comparison hydro')
s=patch_function(s,'indicatorComparisonTable',f_indicator_table)

def f_render_indicator(b):
    b=replace_once(b,"    const financialProfile = metric.meta.compositeType === 'financialProfile';\n    const initialFinancialChoice = 'part-0';\n    const initialFinancialReading = financialProfile ? financialProfileReading(metric,initialFinancialChoice) : null;","    const financialProfile = metric.meta.compositeType === 'financialProfile';\n    const hydroRisk = metric.meta.compositeType === 'hydroRisk';\n    const initialFinancialChoice = 'part-0';\n    const initialFinancialReading = financialProfile ? financialProfileReading(metric,initialFinancialChoice) : null;\n    const initialHydroView = hydroRisk ? compositeCompareDefaults(metric) : null;\n    const initialHydroAggregate = hydroRisk ? compositeCompareAggregate(metric,initialHydroView.choice,initialHydroView.scale) : null;",'indicator flags hydro')
    b=replace_once(b,"${indicatorComparisonTable(data, pageMetric, initialFinancialChoice)}</div><aside data-financial-indicator-aggregate>${financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : `<span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p>`}</aside>","${indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)}</div><aside data-financial-indicator-aggregate>${financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : hydroRisk ? `<span>${html(initialHydroAggregate.label)}</span><strong>${html(formatValue(initialHydroAggregate.value,initialHydroAggregate.unit))}</strong><p>${html(initialHydroAggregate.note || metric.aggregate.note || '')}</p>` : `<span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p>`}</aside>",'indicator aggregate hydro')
    b=replace_once(b,"<section class=\"indicator-benchmark page-width\">${financialProfile ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>","<section class=\"indicator-benchmark page-width\">${(financialProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>",'indicator benchmark hydro')
    tail="      currentSection?.addEventListener('change',event=>{\n        const select=event.target.closest('select[data-composite-component]');\n        if(select&&currentSection.contains(select)) applyFinancialChoice(select.value);\n      });\n    }"
    addition=tail+"\n    if (hydroRisk) {\n      const currentSection=document.querySelector('.indicator-current');\n      let hydroView={...initialHydroView};\n      const renderHydro=()=>{\n        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');\n        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');\n        const aggregate=compositeCompareAggregate(metric,hydroView.choice,hydroView.scale);\n        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,initialFinancialChoice,hydroView);\n        if(aggregateHost) aggregateHost.innerHTML=`<span>${html(aggregate.label)}</span><strong>${html(formatValue(aggregate.value,aggregate.unit))}</strong><p>${html(aggregate.note || metric.aggregate.note || '')}</p>`;\n      };\n      currentSection?.addEventListener('change',event=>{\n        const select=event.target.closest('select[data-composite-component]');\n        if(select&&currentSection.contains(select)){ hydroView={...hydroView,choice:select.value}; renderHydro(); }\n      });\n      currentSection?.addEventListener('click',event=>{\n        const button=event.target.closest('button[data-composite-scale]');\n        if(button&&currentSection.contains(button)){ hydroView={...hydroView,scale:button.dataset.compositeScale}; renderHydro(); }\n      });\n    }"
    b=replace_once(b,tail,addition,'indicator hydro interactions')
    return b
s=patch_function(s,'renderIndicator',f_render_indicator)
p.write_text(s)

# app06
p=ROOT/'assets/app-parts/06.txt'; s=p.read_text()
s=replace_once(s,"        const isFlood = metricKey === 'floodExposure';\n        const isLandslide = metricKey === 'landslideExposure';","        const legacyRiskDetail = data.metrics?.[metricKey]?.meta?.compositeType !== 'hydroRisk';\n        const isFlood = legacyRiskDetail && metricKey === 'floodExposure';\n        const isLandslide = legacyRiskDetail && metricKey === 'landslideExposure';",'legacy risk detail')
p.write_text(s)

# visual grammar
p=ROOT/'assets/visual-grammar.js'; s=p.read_text()
s=replace_once(s,"    if (kind === 'percent') return `${formatted}%`;","    if (kind === 'percent') return `${formatted}%`;\n    if (kind === 'decile') return `${number0.format(n)}/10`;\n    if (kind === 'ventile') return `${number0.format(n)}/20`;",'visual units')
old="    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile','ratioProfile','financialProfile','sexBreakdown'].includes(type)) return null;"
if s.count(old)!=2: raise RuntimeError(f'visual guards attesi2 trovato{s.count(old)}')
s=s.replace(old,old.replace("'sexBreakdown'","'sexBreakdown','hydroRisk'"),2)

def insert_after_guard(text, func, insertion):
    marker=f'  function {func}('
    start=text.find(marker); end=text.find('\n  function ',start+len(marker)); block=text[start:end]
    guard_end=block.find('\n',block.find("    if (!choice ||"))+1
    block=block[:guard_end]+insertion+block[guard_end:]
    return text[:start]+block+text[end:]
s=insert_after_guard(s,'compositeSelectionFor',"    if (type === 'hydroRisk') { const part=(row?.parts || []).find(item=>item.key===choice)||row?.parts?.[0]||{}; return {value:scale==='areaPct'?part.areaPct:part.residentsPct,unit:'percent'}; }\n")
s=insert_after_guard(s,'compositeAggregateFor',"    if (type === 'hydroRisk') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const territory=scale==='areaPct'; return {value:territory?part.areaPct:part.residentsPct,label:`Versilia · ${territory?'territorio':'residenti'} · ${part.label||choice}`,unit:'percent'}; }\n")
s=replace_once(s,"    const scale = scaleFor(mapped.map(item => item.value), aggregate?.value, unit);","    const ordinalScale = metric.meta?.ordinalScale;\n    const scale = ordinalScale ? { min:Number(ordinalScale.min), max:Number(ordinalScale.max), kind:'ordinal' } : scaleFor(mapped.map(item => item.value), aggregate?.value, unit);",'visual fixed scale')
s=replace_once(s,"        : scale.kind === 'focused'\n          ? 'scala adattata ai prezzi'\n          : 'scala con origine a zero';","        : scale.kind === 'focused'\n          ? 'scala adattata ai prezzi'\n          : scale.kind === 'ordinal'\n            ? `scala Istat fissa ${formatAxis(scale.min, unit)}–${formatAxis(scale.max, unit)}`\n            : 'scala con origine a zero';",'visual scale label')
s=replace_once(s,"    if (['distribution','agricultureProfile','ratioProfile','financialProfile'].includes(metric.meta?.compositeType)) return;","    if (['distribution','agricultureProfile','ratioProfile','financialProfile','hydroRisk'].includes(metric.meta?.compositeType) || metric.meta?.ordinalScale) return;",'visual town skip')
p.write_text(s)

# ux history skip hydro
p=ROOT/'assets/ux-history.js'; s=p.read_text(); old="['drinkingWaterQuality','remediationProceedings','financialProfile'].includes(selected.metric?.meta?.compositeType)"
if s.count(old)!=2: raise RuntimeError(f'ux skip atteso2 trovato{s.count(old)}')
s=s.replace(old,"['drinkingWaterQuality','remediationProceedings','financialProfile','hydroRisk'].includes(selected.metric?.meta?.compositeType)",2); p.write_text(s)
# core history fixed ordinal
p=ROOT/'assets/ux-history-core.js'; s=p.read_text()
s=replace_once(s,"      case 'minutes': return `${formatNumber(number, 1)} min`;","      case 'minutes': return `${formatNumber(number, 1)} min`;\n      case 'decile': return `${formatNumber(number, 0)}/10`;\n      case 'ventile': return `${formatNumber(number, 0)}/20`;",'history units')
s=replace_once(s,"      const rawMin = Math.min(...allValues), rawMax = Math.max(...allValues);\n      const padding = (rawMax - rawMin || Math.max(Math.abs(rawMax) * .1, 1)) * .08;\n      let min = rawMin - padding, max = rawMax + padding;\n      if (rawMin >= 0 && min < 0) min = 0;\n      if (rawMax <= 0 && max > 0) max = 0;","      const rawMin = Math.min(...allValues), rawMax = Math.max(...allValues);\n      const ordinalScale = metric.meta?.ordinalScale;\n      const padding = (rawMax - rawMin || Math.max(Math.abs(rawMax) * .1, 1)) * .08;\n      let min = ordinalScale ? Number(ordinalScale.min) : rawMin - padding, max = ordinalScale ? Number(ordinalScale.max) : rawMax + padding;\n      if (!ordinalScale && rawMin >= 0 && min < 0) min = 0;\n      if (!ordinalScale && rawMax <= 0 && max > 0) max = 0;",'history fixed scale')
s=replace_once(s,"    if (focusedFuel) {\n      const rawMin = Math.min(...values), rawMax = Math.max(...values);","    const ordinalScale = metric.meta?.ordinalScale;\n    if (ordinalScale) {\n      min = Number(ordinalScale.min);\n      max = Number(ordinalScale.max);\n    } else if (focusedFuel) {\n      const rawMin = Math.min(...values), rawMax = Math.max(...values);",'history current fixed scale')
p.write_text(s)
print('Runtime fragilità v1.33.0 materializzato nei renderer condivisi.')
