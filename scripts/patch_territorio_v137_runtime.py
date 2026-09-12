#!/usr/bin/env python3
"""Estende i renderer canonici ai profili territoriali v1.37.

La patch viene applicata nel workspace temporaneo della build canonica, dopo le
patch runtime delle release precedenti. Tutte le sostituzioni sono fail-closed.
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

    # Unita' specifiche. Ettari e km riusano rispettivamente 'hectares' e 'km'.
    app00 = replace_once(
        app00,
        "      case 'hectares': return `${number2.format(v)} ha`;\n",
        "      case 'hectares': return `${number2.format(v)} ha`;\n"
        "      case 'sqm_per_resident': return `${number1.format(v)} m²/residente`;\n",
        "formatter m2/residente",
    )
    app00 = replace_once(
        app00,
        "      case 'km': return `${number2.format(v)} km`;\n",
        "      case 'km': return `${number2.format(v)} km`;\n"
        "      case 'km_per_km2': return `${number2.format(v)} km/km²`;\n",
        "formatter densita lineare",
    )

    helper = """
  const territoryProfileTypes = new Set(['soilStockProfile','soilChangeProfile','protectedAreasProfile','hydroNetworkProfile','roadNetworkProfile']);
  function isTerritoryProfileType(value) {
    const type = typeof value === 'string' ? value : value?.meta?.compositeType;
    return territoryProfileTypes.has(type);
  }

"""
    app03 = replace_once(
        app03,
        "  function compositeCompareDefaults(metric) {\n",
        helper + "  function compositeCompareDefaults(metric) {\n",
        "helper profili territorio",
    )
    app03 = replace_once(
        app03,
        "    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n",
        "    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n"
        "    if (isTerritoryProfileType(metric)) return { choice:metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key || '', scale:'value' };\n",
        "default profilo territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n",
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n"
        "    if (isTerritoryProfileType(metric)) {\n"
        "      const part=(row.parts || []).find(item=>item.key===choice) || row.parts?.[0] || {};\n"
        "      return { value:part.value, unit:part.unit || metric.meta.unit, part };\n"
        "    }\n",
        "selezione profilo territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n",
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n"
        "    if (isTerritoryProfileType(metric)) {\n"
        "      const part=(metric.aggregate?.parts || []).find(item=>item.key===choice) || metric.aggregate?.parts?.[0] || {};\n"
        "      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.label || metric.meta.label}`, note:metric.aggregate?.note };\n"
        "    }\n",
        "aggregato profilo territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeCompareControls(metric, choice, scale = 'value') {\n",
        "  function compositeCompareControls(metric, choice, scale = 'value') {\n"
        "    if (isTerritoryProfileType(metric)) {\n"
        "      const labels=metric.rows?.[0]?.parts || [];\n"
        "      return `<div class=\"compare-view-controls territory-profile-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${labels.map(part=>`<option value=\"${html(part.key)}\" ${part.key===choice?'selected':''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`;\n"
        "    }\n",
        "controlli profilo territorio",
    )
    app03 = replace_once(
        app03,
        "    const parts = row.parts || [];\n    if (metric.meta.compositeType === 'financialProfile') {\n",
        "    const parts = row.parts || [];\n"
        "    if (isTerritoryProfileType(metric)) {\n"
        "      const histories=parts.filter(part=>row.seriesByView?.[part.key]?.years?.length).map((part,index)=>`<details class=\"detail-disclosure territory-profile-history\" ${part.key===(metric.meta.defaultView||parts[0]?.key)?'open':''}><summary><span>${html(part.label)}</span><small>Serie ufficiale</small></summary><div>${seriesChart(row.seriesByView[part.key],part.unit || metric.meta.unit,`${metric.meta.label} · ${part.label} · ${row.town}`)}</div></details>`).join('');\n"
        "      return `<div class=\"composite-town-mobility territory-profile-town\">${parts.map((part,index)=>`<article class=\"${part.key===(metric.meta.defaultView||parts[0]?.key)?'balance':''}\"><span>${html(part.label)}</span><strong>${html(formatMetricRowValue(row,part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>${histories}`;\n"
        "    }\n"
        "    if (metric.meta.compositeType === 'financialProfile') {\n",
        "dettaglio comunale profilo territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeSelectionOptions(metric, row) {\n",
        "  function compositeSelectionOptions(metric, row) {\n"
        "    if (isTerritoryProfileType(metric)) return (row.parts || []).map(part=>({ key:part.key, label:part.selectorLabel || part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatMetricRowValue(row,part.value,part.unit || metric.meta.unit), part }));\n",
        "opzioni profilo territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeSelectionAggregate(metric, choice) {\n",
        "  function compositeSelectionAggregate(metric, choice) {\n"
        "    if (isTerritoryProfileType(metric)) { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.label || metric.meta.label}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }\n",
        "aggregato selettore territorio",
    )
    app03 = replace_once(
        app03,
        "  function compositeSelectionRank(metric, row, choice) {\n    const values = metric.rows.map(r => {\n",
        "  function compositeSelectionRank(metric, row, choice) {\n    const values = metric.rows.map(r => {\n"
        "      if (isTerritoryProfileType(metric)) { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:part?.value===null||part?.value===undefined?NaN:Number(part.value)}; }\n",
        "rank profilo territorio",
    )
    app03 = replace_once(
        app03,
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','financialProfile','ratioProfile','demographicBreakdown','sexBreakdown','hydroRisk'].includes(compositeType);\n",
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures','agricultureProfile','financialProfile','ratioProfile','demographicBreakdown','sexBreakdown','hydroRisk'].includes(compositeType) || isTerritoryProfileType(compositeType);\n",
        "confronto selezionabile territorio",
    )
    app03 = replace_once(
        app03,
        "      const note = compositeType === 'omi' ? `<p class=\"composite-compare-note\"><strong>Dettaglio OMI:</strong> il dettaglio delle singole sotto-aree è disponibile nelle schede dei comuni. Clicca una riga per aprire il territorio.</p>` : (compositeType === 'mobility' ? `<p class=\"composite-compare-note\">Scegli la voce e l’unità direttamente dal grafico. “Ogni 1.000” rende più omogeneo il confronto tra comuni di dimensioni diverse.</p>` : '');\n",
        "      const note = isTerritoryProfileType(compositeType) ? `<p class=\"composite-compare-note\">Scegli la lettura dal selettore. Ogni vista conserva la propria unità e il proprio metodo di aggregazione Versilia.</p>` : (compositeType === 'omi' ? `<p class=\"composite-compare-note\"><strong>Dettaglio OMI:</strong> il dettaglio delle singole sotto-aree è disponibile nelle schede dei comuni. Clicca una riga per aprire il territorio.</p>` : (compositeType === 'mobility' ? `<p class=\"composite-compare-note\">Scegli la voce e l’unità direttamente dal grafico. “Ogni 1.000” rende più omogeneo il confronto tra comuni di dimensioni diverse.</p>` : ''));\n",
        "nota confronto territorio",
    )

    app03 = replace_once(
        app03,
        "    const securityMeasures = ['securityMeasures','agricultureProfile','financialProfile'].includes(metric.meta.compositeType);\n",
        "    const securityMeasures = ['securityMeasures','agricultureProfile','financialProfile'].includes(metric.meta.compositeType);\n"
        "    const territoryProfile = isTerritoryProfileType(metric);\n",
        "flag profilo territorio comunale",
    )
    app03 = replace_once(
        app03,
        "    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || hydroRisk;\n",
        "    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown || sexBreakdown || hydroRisk || territoryProfile;\n",
        "profilo territorio selezionabile comunale",
    )
    app03 = replace_once(
        app03,
        "    const defaultSexChoice = sexBreakdown ? (metric.meta.defaultSex || 'totale') : null;\n",
        "    const defaultSexChoice = sexBreakdown ? (metric.meta.defaultSex || 'totale') : null;\n"
        "    const defaultTerritoryChoice = territoryProfile ? (metric.meta.defaultView || options[0]?.key) : null;\n",
        "default territorio comunale",
    )
    app03 = replace_once(
        app03,
        "    const summary = distribution ? compositeSummary(metric,row) : (sexBreakdown ? (options.find(option=>option.key===defaultSexChoice) || options[0]) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures || hydroRisk) ? options[0] : null)));\n",
        "    const summary = territoryProfile ? (options.find(option=>option.key===defaultTerritoryChoice) || options[0]) : (distribution ? compositeSummary(metric,row) : (sexBreakdown ? (options.find(option=>option.key===defaultSexChoice) || options[0]) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures || hydroRisk) ? options[0] : null))));\n",
        "summary territorio comunale",
    )
    app03 = replace_once(
        app03,
        "    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (sexBreakdown ? compositeSelectionAggregate(metric,defaultSexChoice) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null))))));\n",
        "    const aggregateSummary = territoryProfile ? compositeSelectionAggregate(metric,defaultTerritoryChoice) : (distribution ? compositeAggregateSummary(metric) : (sexBreakdown ? compositeSelectionAggregate(metric,defaultSexChoice) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null)))))));\n",
        "aggregato territorio comunale",
    )
    app03 = replace_once(
        app03,
        "    const panelOverline = drinkingQuality ? 'Dati analitici GAIA' : remediation ? 'Dettaglio dei procedimenti' : extractiveProductionHistory ? 'Andamento storico' : financialProfile ? `Indicatore ${initialFinancialReading.code}` : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : sexBreakdown ? 'Totale, Maschi e Femmine' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa') : (historical ? 'Andamento storico' : 'Confronto territoriale');\n",
        "    const panelOverline = drinkingQuality ? 'Dati analitici GAIA' : remediation ? 'Dettaglio dei procedimenti' : extractiveProductionHistory ? 'Andamento storico' : financialProfile ? `Indicatore ${initialFinancialReading.code}` : territoryProfile ? 'Letture territoriali' : hydroRisk ? 'Matrice ufficiale ISPRA' : composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : sexBreakdown ? 'Totale, Maschi e Femmine' : securityMeasures ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa') : (historical ? 'Andamento storico' : 'Confronto territoriale');\n",
        "overline territorio comunale",
    )
    app03 = replace_once(
        app03,
        "    const panelTitle = drinkingQuality ? 'Valori per località e parametro' : remediation ? 'Iter attivi e chiusi' : extractiveProductionHistory ? 'Evoluzione della produzione estrattiva' : financialProfile ? initialFinancialReading.label : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : sexBreakdown ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`) : (historical ? 'Evoluzione nel tempo' : 'Confronto tra i comuni');\n",
        "    const panelTitle = drinkingQuality ? 'Valori per località e parametro' : remediation ? 'Iter attivi e chiusi' : extractiveProductionHistory ? 'Evoluzione della produzione estrattiva' : financialProfile ? initialFinancialReading.label : territoryProfile ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : hydroRisk ? `Territorio e residenti · ${html(metric.meta.year)}` : composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : sexBreakdown ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : securityMeasures ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`) : (historical ? 'Evoluzione nel tempo' : 'Confronto tra i comuni');\n",
        "titolo pannello territorio comunale",
    )
    app03 = replace_once(
        app03,
        "${options.map((option,index)=>`<option value=\"${html(option.key)}\" ${index===0?'selected':''}>${html(option.label)}</option>`).join('')}"
        ,
        "${options.map((option,index)=>`<option value=\"${html(option.key)}\" ${option.key===(territoryProfile?defaultTerritoryChoice:options[0]?.key)?'selected':''}>${html(option.label)}</option>`).join('')}"
        ,
        "selezione iniziale territorio comunale",
    )
    app03 = replace_once(
        app03,
        "      ${financialProfile ? `<div data-financial-profile-method>${financialProfileMethodDisclosure(metric,'part-0')}</div>` : methodDisclosure(metric)}\n",
        "      ${financialProfile ? `<div data-financial-profile-method>${financialProfileMethodDisclosure(metric,'part-0')}</div>` : methodDisclosure(metric)}\n",
        "metodo invariato",
    ) if False else app03
    app03 = replace_once(
        app03,
        "      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}\n",
        "      ${(metricKey.startsWith('slowMobility') || territoryProfile || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}\n",
        "benchmark comunale territorio",
    )
    app03 = replace_once(
        app03,
        "      const initialChoice=options[0]?.key || 'summary';\n",
        "      const initialChoice=territoryProfile ? defaultTerritoryChoice : (options[0]?.key || 'summary');\n",
        "choice iniziale territorio",
    )

    # Scheda indicatore: confronto e serie storica seguono la lettura selezionata.
    app05 = replace_once(
        app05,
        "  function indicatorComparisonTable(data, metricKey, financialChoice='part-0') {\n    const metric = data.metrics[metricKey];\n    const rows = [...metric.rows].sort((a, b) => a.town.localeCompare(b.town, 'it'));\n",
        "  function indicatorComparisonTable(data, metricKey, financialChoice='part-0') {\n    const metric = data.metrics[metricKey];\n    const rows = [...metric.rows].sort((a, b) => a.town.localeCompare(b.town, 'it'));\n"
        "    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return `<div class=\"indicator-composite-table territory-indicator-comparison\"><div class=\"compare-chart-toolbar\">${compositeCompareControls(metric,choice,'value')}</div><div class=\"comparison-bars\" data-composite-choice=\"${html(choice)}\">${compositeCompareBarRows(data,metricKey,choice,'value')}</div></div>`; }\n",
        "confronto scheda territorio",
    )
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
    app05 = replace_once(
        app05,
        "  function financialProfileHistoryTable(metric,choice='part-0') {\n",
        history_helpers + "  function financialProfileHistoryTable(metric,choice='part-0') {\n",
        "helper storico scheda territorio",
    )
    app05 = replace_once(
        app05,
        "    if (metric.meta.compositeType === 'financialProfile') return financialProfileHistoryTable(metric,financialChoice);\n",
        "    if (metric.meta.compositeType === 'financialProfile') return financialProfileHistoryTable(metric,financialChoice);\n"
        "    if (isTerritoryProfileType(metric)) { const choice=financialChoice==='part-0'?(metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key):financialChoice; return territoryProfileHistoryTable(metric,choice); }\n",
        "storico scheda territorio",
    )
    app05 = replace_once(
        app05,
        "    const financialProfile = metric.meta.compositeType === 'financialProfile';\n",
        "    const financialProfile = metric.meta.compositeType === 'financialProfile';\n"
        "    const territoryProfile = isTerritoryProfileType(metric);\n"
        "    const initialTerritoryChoice = territoryProfile ? (metric.meta.defaultView || metric.rows?.[0]?.parts?.[0]?.key) : null;\n",
        "flag scheda territorio",
    )
    app05 = replace_once(
        app05,
        "${indicatorComparisonTable(data, pageMetric, initialFinancialChoice, initialHydroView)}</div><aside data-financial-indicator-aggregate>${financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : hydroRisk ? `<span>${html(initialHydroAggregate.label)}</span><strong>${html(formatValue(initialHydroAggregate.value,initialHydroAggregate.unit))}</strong><p>${html(initialHydroAggregate.note || metric.aggregate.note || '')}</p>` : `<span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p>`}</aside>"
        ,
        "${indicatorComparisonTable(data, pageMetric, territoryProfile ? initialTerritoryChoice : initialFinancialChoice, initialHydroView)}</div><aside data-financial-indicator-aggregate>${financialProfile ? financialProfileIndicatorAsideMarkup(metric,initialFinancialChoice) : territoryProfile ? territoryProfileIndicatorAsideMarkup(metric,initialTerritoryChoice) : hydroRisk ? `<span>${html(initialHydroAggregate.label)}</span><strong>${html(formatValue(initialHydroAggregate.value,initialHydroAggregate.unit))}</strong><p>${html(initialHydroAggregate.note || metric.aggregate.note || '')}</p>` : `<span>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).label : metric.aggregate.label)}</span><strong>${html(metric.meta.compositeType === 'distribution' ? compositeAggregateSummary(metric).formatted : formatValue(metric.aggregate.value, metric.meta.unit))}</strong><p>${html(metric.meta.compositeType === 'distribution' ? (metric.aggregate.summaryNote || metric.aggregate.note) : metric.aggregate.note)}</p>`}</aside>"
        ,
        "aggregato scheda territorio",
    )
    app05 = replace_once(
        app05,
        "<section class=\"indicator-benchmark page-width\">${(financialProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>\n",
        "<section class=\"indicator-benchmark page-width\">${(financialProfile || territoryProfile || hydroRisk) ? '' : benchmarkMarkup(metric, metric.aggregate, metric.meta.unit, null)}</section>\n",
        "benchmark scheda territorio",
    )
    app05 = replace_once(
        app05,
        "${indicatorHistoryTable(metric,initialFinancialChoice)}</div></section>\n",
        "${indicatorHistoryTable(metric,territoryProfile ? initialTerritoryChoice : initialFinancialChoice)}</div></section>\n",
        "storico iniziale scheda territorio",
    )
    event_marker = """    if (financialProfile) {
"""
    territory_events = """    if (territoryProfile) {
      const currentSection=document.querySelector('.indicator-current');
      const applyTerritoryChoice=choice=>{
        const comparisonHost=document.querySelector('[data-financial-indicator-comparison]');
        const aggregateHost=document.querySelector('[data-financial-indicator-aggregate]');
        const historyHost=document.querySelector('[data-financial-indicator-history]');
        if(comparisonHost) comparisonHost.innerHTML=indicatorComparisonTable(data,pageMetric,choice);
        if(aggregateHost) aggregateHost.innerHTML=territoryProfileIndicatorAsideMarkup(metric,choice);
        if(historyHost) historyHost.innerHTML=territoryProfileHistoryTable(metric,choice);
      };
      currentSection?.addEventListener('change',event=>{
        const select=event.target.closest('select[data-composite-component]');
        if(select&&currentSection.contains(select)) applyTerritoryChoice(select.value);
      });
    }
"""
    app05 = replace_once(app05, event_marker, territory_events + event_marker, "eventi scheda territorio")

    APP00.write_text(app00, encoding="utf-8")
    APP03.write_text(app03, encoding="utf-8")
    APP05.write_text(app05, encoding="utf-8")
    print("Renderer territorio v1.37 applicato ai renderer canonici.")


if __name__ == "__main__":
    main()
