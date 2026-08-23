#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "assets" / "app-parts" / "03.txt"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Patch frontend non applicabile: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    if "data-demographic-age" in text:
        print("Patch età/genere già applicata")
        return

    text = replace_once(text,
        "  function compositeCompareDefaults(metric) {\n    if (metric.meta.compositeType === 'stock')",
        "  function compositeCompareDefaults(metric) {\n    if (metric.meta.compositeType === 'demographicBreakdown') return { choice:`${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}`, scale:'value' };\n    if (metric.meta.compositeType === 'stock')",
        "defaults")

    text = replace_once(text,
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'stock')",
        "  function compositeCompareSelection(metric, row, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'demographicBreakdown') {\n      const part = (row.parts || []).find(item => item.key === choice) || row.parts?.[0] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, part };\n    }\n    if (metric.meta.compositeType === 'stock')",
        "selection")

    text = replace_once(text,
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'stock')",
        "  function compositeCompareAggregate(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'demographicBreakdown') {\n      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || metric.aggregate?.parts?.[0] || {};\n      return { value:part.value, unit:part.unit || metric.meta.unit, label:`Versilia · ${part.ageLabel || ''} · ${part.genderLabel || ''}`, note:metric.aggregate?.note };\n    }\n    if (metric.meta.compositeType === 'stock')",
        "aggregate")

    controls_old = "  function compositeCompareControls(metric, choice, scale = 'value') {\n    if (metric.meta.compositeType === 'stock')"
    controls_new = """  function compositeCompareControls(metric, choice, scale = 'value') {
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const [ageKey,genderKey] = String(choice || '').split('|');
      return `<div class="compare-view-controls demographic-view-controls"><label class="compare-choice-select"><span>Fascia d’età</span><select data-demographic-age>${(metric.meta.ageOptions || []).map(option=>`<option value="${html(option.key)}" ${option.key === ageKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label><label class="compare-choice-select"><span>Genere</span><select data-demographic-gender>${(metric.meta.genderOptions || []).map(option=>`<option value="${html(option.key)}" ${option.key === genderKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>`;
    }
    if (metric.meta.compositeType === 'stock')"""
    text = replace_once(text, controls_old, controls_new, "controls")

    text = replace_once(text,
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures'].includes(compositeType);",
        "    const selectableComposite = ['stock','mobility','omi','securityMeasures','demographicBreakdown'].includes(compositeType);",
        "compare selectable")

    onchange_old = """      bars.onchange = event => {
        const componentSelect = event.target.closest('select[data-composite-component]');
        if (componentSelect && bars.contains(componentSelect)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:componentSelect.value});
        }
      };"""
    onchange_new = """      bars.onchange = event => {
        const ageSelect = event.target.closest('select[data-demographic-age]');
        const genderSelect = event.target.closest('select[data-demographic-gender]');
        if ((ageSelect || genderSelect) && bars.contains(event.target)) {
          const [oldAge,oldGender] = String(view.choice || '').split('|');
          const age = ageSelect ? ageSelect.value : oldAge;
          const gender = genderSelect ? genderSelect.value : oldGender;
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:`${age}|${gender}`});
          return;
        }
        const componentSelect = event.target.closest('select[data-composite-component]');
        if (componentSelect && bars.contains(componentSelect)) {
          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,choice:componentSelect.value});
        }
      };"""
    text = replace_once(text, onchange_old, onchange_new, "compare onchange")

    text = replace_once(text,
        "    if (metric.meta.compositeType === 'securityMeasures') {\n      const defaults = compositeCompareDefaults(metric);",
        "    if (metric.meta.compositeType === 'demographicBreakdown') {\n      const defaults = compositeCompareDefaults(metric);\n      return `<div class=\"comparison-bars\">${compositeCompareBarRows(data,metricKey,defaults.choice,defaults.scale)}</div>`;\n    }\n    if (metric.meta.compositeType === 'securityMeasures') {\n      const defaults = compositeCompareDefaults(metric);",
        "compare markup")

    town_marker = "  function compositeTownMarkup(metric, row) {\n    const parts = row.parts || [];\n    if (metric.meta.compositeType === 'stock')"
    town_new = """  function compositeTownMarkup(metric, row) {
    const parts = row.parts || [];
    if (metric.meta.compositeType === 'demographicBreakdown') {
      const ages = metric.meta.ageOptions || [];
      const genders = metric.meta.genderOptions || [];
      const cells = new Map(parts.map(part => [part.key,part]));
      const table = `<div class="demographic-matrix-wrap"><table class="demographic-matrix"><thead><tr><th>Età</th>${genders.map(g=>`<th>${html(g.label)}</th>`).join('')}</tr></thead><tbody>${ages.map(age=>`<tr><th>${html(age.label)}</th>${genders.map(g=>{const part=cells.get(`${age.key}|${g.key}`)||{};return `<td><strong>${html(formatValue(part.value,'percent'))}</strong><small>${html(number0.format(part.numerator || 0))} / ${html(number0.format(part.denominator || 0))}</small></td>`;}).join('')}</tr>`).join('')}</tbody></table><p class="demographic-matrix-note">Il rapporto sotto ogni percentuale mostra numeratore e denominatore usati nel calcolo. 25–64 è ricostruita sui conteggi Istat 25–49 e 50–64 prima del calcolo del tasso.</p></div>`;
      const history = row.series?.values?.length ? `<details class="detail-disclosure demographic-history"><summary><span>Storico della lettura base</span><small>${html(metric.meta.defaultAge === '25-64' ? '25–64 anni · Totale' : 'lettura base')}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · lettura base`)}</div></details>` : '';
      return table + history;
    }
    if (metric.meta.compositeType === 'stock')"""
    text = replace_once(text, town_marker, town_new, "town matrix")

    text = replace_once(text,
        "  function compositeSelectionOptions(metric, row) {\n    if (metric.meta.compositeType === 'stock')",
        "  function compositeSelectionOptions(metric, row) {\n    if (metric.meta.compositeType === 'demographicBreakdown') return (row.parts || []).map(part=>({ key:part.key, label:part.label, value:part.value, unit:part.unit || metric.meta.unit, formatted:formatValue(part.value,part.unit || metric.meta.unit), part }));\n    if (metric.meta.compositeType === 'stock')",
        "selection options")

    text = replace_once(text,
        "  function compositeSelectionAggregate(metric, choice) {\n    if (metric.meta.compositeType === 'stock')",
        "  function compositeSelectionAggregate(metric, choice) {\n    if (metric.meta.compositeType === 'demographicBreakdown') { const part=(metric.aggregate?.parts || []).find(item=>item.key===choice)||metric.aggregate?.parts?.[0]||{}; const unit=part.unit||metric.meta.unit; return {label:`Versilia · ${part.ageLabel || ''} · ${part.genderLabel || ''}`,value:part.value,unit,formatted:formatValue(part.value,unit)}; }\n    if (metric.meta.compositeType === 'stock')",
        "selection aggregate")

    text = replace_once(text,
        "      if (metric.meta.compositeType === 'stock') return { code:r.code, value:Number(choice === 'count' ? r.count : r.value) };",
        "      if (metric.meta.compositeType === 'demographicBreakdown') { const part=(r.parts || []).find(item=>item.key===choice); return {code:r.code,value:Number(part?.value)}; }\n      if (metric.meta.compositeType === 'stock') return { code:r.code, value:Number(choice === 'count' ? r.count : r.value) };",
        "selection rank")

    town_flags_old = """    const securityMeasures = metric.meta.compositeType === 'securityMeasures';
    const selectable = distribution || omi || stock || securityMeasures;
    const options = selectable ? compositeSelectionOptions(metric,row) : [];
    const summary = distribution ? compositeSummary(metric,row) : ((omi || stock || securityMeasures) ? options[0] : null);
    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null)));"""
    town_flags_new = """    const securityMeasures = metric.meta.compositeType === 'securityMeasures';
    const demographicBreakdown = metric.meta.compositeType === 'demographicBreakdown';
    const selectable = distribution || omi || stock || securityMeasures || demographicBreakdown;
    const options = selectable ? compositeSelectionOptions(metric,row) : [];
    const defaultDemographicChoice = demographicBreakdown ? `${metric.meta.defaultAge || '25-64'}|${metric.meta.defaultGender || 'total'}` : null;
    const summary = distribution ? compositeSummary(metric,row) : (demographicBreakdown ? (options.find(option=>option.key===defaultDemographicChoice) || options[0]) : ((omi || stock || securityMeasures) ? options[0] : null));
    const aggregateSummary = distribution ? compositeAggregateSummary(metric) : (demographicBreakdown ? compositeSelectionAggregate(metric,defaultDemographicChoice) : (omi ? compositeSelectionAggregate(metric,'sale') : (stock ? compositeSelectionAggregate(metric,'share') : (securityMeasures ? compositeSelectionAggregate(metric,'part-0') : null))));"""
    text = replace_once(text, town_flags_old, town_flags_new, "town flags")

    selector_old = "    const selector = selectable ? `<label class=\"composite-read-selector\"><span>${html(metric.meta.selectorLabel || 'Dato in evidenza')}</span><select data-composite-choice>${options.map((option,index)=>`<option value=\"${html(option.key)}\" ${index===0?'selected':''}>${html(option.label)}</option>`).join('')}</select></label>` : '';"
    selector_new = "    const selector = demographicBreakdown ? `<div class=\"composite-read-selector demographic-town-selectors\"><label><span>Fascia d’età</span><select data-demographic-town-age>${(metric.meta.ageOptions || []).map(option=>`<option value=\"${html(option.key)}\" ${option.key === (metric.meta.defaultAge || '25-64') ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label><label><span>Genere</span><select data-demographic-town-gender>${(metric.meta.genderOptions || []).map(option=>`<option value=\"${html(option.key)}\" ${option.key === (metric.meta.defaultGender || 'total') ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select></label></div>` : (selectable ? `<label class=\"composite-read-selector\"><span>${html(metric.meta.selectorLabel || 'Dato in evidenza')}</span><select data-composite-choice>${options.map((option,index)=>`<option value=\"${html(option.key)}\" ${index===0?'selected':''}>${html(option.label)}</option>`).join('')}</select></label>` : '');"
    text = replace_once(text, selector_old, selector_new, "town selectors")

    listener_old = """    if (selectable) {
      const select=container.querySelector('[data-composite-choice]');
      select?.addEventListener('change',()=>{
        const choice=select.value;
        const selected=options.find(option=>option.key===choice) || options[0];
        const agg=compositeSelectionAggregate(metric,choice);"""
    listener_new = """    if (selectable) {
      const select=container.querySelector('[data-composite-choice]');
      const demoAge=container.querySelector('[data-demographic-town-age]');
      const demoGender=container.querySelector('[data-demographic-town-gender]');
      const applyChoice=(choice)=>{
        const selected=options.find(option=>option.key===choice) || options[0];
        const agg=compositeSelectionAggregate(metric,choice);"""
    text = replace_once(text, listener_old, listener_new, "town listener start")

    listener_end_old = """        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));
      });
    }
    installChartInteractions(container);"""
    listener_end_new = """        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));
      };
      select?.addEventListener('change',()=>applyChoice(select.value));
      const applyDemographic=()=>applyChoice(`${demoAge?.value || metric.meta.defaultAge || '25-64'}|${demoGender?.value || metric.meta.defaultGender || 'total'}`);
      demoAge?.addEventListener('change',applyDemographic);
      demoGender?.addEventListener('change',applyDemographic);
    }
    installChartInteractions(container);"""
    text = replace_once(text, listener_end_old, listener_end_new, "town listener end")

    # Non mostrare benchmark Toscana/Italia mentre il filtro locale può cambiare fascia/genere.
    text = replace_once(text,
        "      ${metricKey.startsWith('slowMobility') ? '' : townBenchmarkMarkup(metric, row, town)}",
        "      ${(metricKey.startsWith('slowMobility') || demographicBreakdown) ? '' : townBenchmarkMarkup(metric, row, town)}",
        "benchmark")

    # Export esplicito delle celle età × genere.
    export_old = "    const lines = isOmi ? [['Comune','Codice Istat','Indicatore','Anno','Zona OMI','Area','Vendita €/m²','Affitto €/m²/mese','Fonte']] : metric.meta.compositeType ? [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Componente', 'Valore', 'Unità', 'Conteggio', 'Fonte']] : [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Valore', 'Unità', 'Fonte']];"
    export_new = "    const isDemographic = metric.meta.compositeType === 'demographicBreakdown';\n    const lines = isOmi ? [['Comune','Codice Istat','Indicatore','Anno','Zona OMI','Area','Vendita €/m²','Affitto €/m²/mese','Fonte']] : isDemographic ? [['Comune','Codice Istat','Indicatore','Anno','Fascia età','Genere','Valore %','Numeratore','Denominatore','Fonte']] : metric.meta.compositeType ? [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Componente', 'Valore', 'Unità', 'Conteggio', 'Fonte']] : [['Comune', 'Codice Istat', 'Indicatore', 'Anno', 'Valore', 'Unità', 'Fonte']];"
    text = replace_once(text, export_old, export_new, "export header")
    export_rows_old = "    if (isOmi) rows.forEach(row => (row.zones || []).forEach(zone => lines.push([row.town,row.code,label,metric.meta.year,zone.code,zone.label,zone.sale,zone.rent,metric.sourceUrl])));\n    else if (metric.meta.compositeType)"
    export_rows_new = "    if (isOmi) rows.forEach(row => (row.zones || []).forEach(zone => lines.push([row.town,row.code,label,metric.meta.year,zone.code,zone.label,zone.sale,zone.rent,metric.sourceUrl])));\n    else if (isDemographic) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town,row.code,label,metric.meta.year,part.ageLabel,part.genderLabel,part.value,part.numerator,part.denominator,metric.sourceUrl])));\n    else if (metric.meta.compositeType)"
    text = replace_once(text, export_rows_old, export_rows_new, "export rows")

    APP.write_text(text, encoding="utf-8")
    print("Frontend demographicBreakdown applicato: doppi filtri età/genere in confronto e schede comunali.")


if __name__ == "__main__":
    main()
