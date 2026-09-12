#!/usr/bin/env python3
"""Rifinisce v1.36: grammatica lollipop canonica, conteggi robusti, costa e foreste."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "assets/app-parts/03.txt"
VISUAL_GRAMMAR = ROOT / "assets/visual-grammar.js"
CSS = ROOT / "assets/static.css"
SITE_DATA = ROOT / "data/site-data.json"

REVIEW_MARKER = "/* OV TERRITORIO UCS REVIEW v1.36.0 */"
GRAMMAR_MARKER = "/* OV TERRITORIO UCS CANONICAL COMPARISONS v1.36.0 */"
CSS_MARKER = "/* OV TERRITORIO UCS REVIEW CSS v1.36.0 */"


def replace_once(source: str, needle: str, replacement: str, label: str) -> str:
    count = source.count(needle)
    if count != 1:
        raise RuntimeError(f"v1.36 refine: {label} non patchabile in modo univoco ({count} occorrenze).")
    return source.replace(needle, replacement, 1)


def replace_between(source: str, start_marker: str, end_marker: str, replacement: str, label: str) -> str:
    start = source.find(start_marker)
    if start < 0:
        raise RuntimeError(f"v1.36 refine: inizio {label} non trovato.")
    end = source.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"v1.36 refine: fine {label} non trovata.")
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


def replace_in_block(source: str, start_marker: str, end_marker: str, needle: str, replacement: str, label: str) -> str:
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise RuntimeError(f"v1.36 refine: blocco {label} non trovato.")
    block = source[start:end]
    if block.count(needle) != 1:
        raise RuntimeError(f"v1.36 refine: {label} non patchabile ({block.count(needle)} occorrenze).")
    return source[:start] + block.replace(needle, replacement, 1) + source[end:]


DEGURBA_COMPARE = r'''  function territorialClassificationCompareMarkup(data,metricKey) {
    const metric=data.metrics[metricKey],counts=metric.aggregate?.classificationCounts||{};
    const rows=metric.rows||[];
    return `<div class="territorial-classification-shell">
      <div class="territorial-count-box" aria-label="Versilia: conteggi delle classificazioni territoriali">
        <div class="territorial-count-primary"><strong>${html(String(counts.coastalZone??'n.d.'))}/7</strong><span>Comuni in zona costiera</span></div>
        <div><span>Litoranei</span><strong>${html(String(counts.littoral??'n.d.'))}/7</strong></div>
        <div><span>DEGURBA</span><strong>${html(String(counts.degurba2??0))} comuni classe 2 · ${html(String(counts.degurba3??0))} comune classe 3</strong></div>
      </div>
      <div class="territorial-classification-list" role="table" aria-label="Classificazioni territoriali dei sette Comuni">
        <div class="territorial-classification-head" role="row"><span>Comune</span><span>Litoraneo</span><span>Zona costiera</span><span>DEGURBA</span></div>
        ${rows.map(row=>{const c=row.classification||{},q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a role="row" href="${route(`comuni/${row.slug}/?${q}`)}"><strong>${html(row.town)}</strong><span>${c.littoral?'Sì':'No'}</span><span>${c.coastalZone?'Sì':'No'}</span><span><b>${html(String(c.degurba||'n.d.'))}</b><small>${html(c.degurbaLabel||'')}</small></span></a>`;}).join('')}
      </div>
      ${degurbaExplainerMarkup()}
    </div>`;
  }'''

CANONICAL_COMPARE_HELPERS = r'''  /* OV TERRITORIO UCS REVIEW v1.36.0 */
  function territoryDynamicRows(metric,metricKey,items,unit,formatter) {
    const max=Math.max(...items.map(item=>Math.max(0,Number(item.value)||0)),0.0001);
    return [...items].sort((a,b)=>(Number(b.value)||0)-(Number(a.value)||0)).map((item,index)=>{
      const row=item.row,q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});
      const formatted=formatter(item.value,unit);
      const numeric=Math.max(0,Number(item.value)||0);
      const width=numeric===0?0:numeric/max*100;
      return `<a class="bar-row" href="${route(`comuni/${row.slug}/?${q}`)}" aria-label="${html(row.town)}: ${html(formatted)}"><span class="bar-rank">${index+1}</span><span class="bar-town">${html(row.town)}</span><span class="bar-track"><span class="bar-fill" style="width:${width}%"></span><span class="bar-hover-label">${html(row.town)} · ${html(formatted)}</span></span><strong>${html(formatted)}</strong></a>`;
    }).join('');
  }

  function landCoverCompareRows(data,metricKey,category,year,unit) {
    const metric=data.metrics[metricKey],years=metric.landCoverYears||[],index=Math.max(0,years.indexOf(Number(year)));
    const items=metric.rows.map(row=>({row,value:landCoverSeriesValues(row,category,unit)[index]}));
    return territoryDynamicRows(metric,metricKey,items,unit,landCoverFormat);
  }

  function landCoverTransformationCompareMarkup(metric) {
    const items=(metric.rows||[]).map(row=>({row,value:row.transformation?.changedPct}));
    const rowsMarkup=territoryDynamicRows(metric,metric.meta.key,items,'percent',landCoverFormat);
    return `<div class="land-cover-transform-compare"><div class="land-cover-subheading"><span class="overline">Trasformazione 2007→2019</span><h4>Superficie che cambia macroclasse UCS</h4></div><div class="comparison-bars territory-canonical-comparison" data-land-cover-mode="transformation">${rowsMarkup}</div><p class="aggregate-note">Versilia: <b>${html(landCoverFormat(metric.aggregate?.transformation?.changedPct,'percent'))}</b> (${html(landCoverFormat(metric.aggregate?.transformation?.changedHa,'hectares'))}). Il valore Versilia è Σ ha cambiati / Σ ha UCS, non la media delle percentuali comunali.</p></div>`;
  }

  function landCoverCompareMarkup(data,metricKey,view={}) {
    const metric=data.metrics[metricKey];
    const category=view.landCoverCategory||'artificialized';
    const year=Number(view.landCoverYear)||2019;
    const unit=view.landCoverUnit||'percent';
    const def=landCoverCategory(metric,category),years=metric.landCoverYears||[];
    const index=Math.max(0,years.indexOf(year));
    const aggregateValues=landCoverSeriesValues(metric.aggregate,category,unit);
    const aggregateValue=aggregateValues[index];
    const rowsMarkup=landCoverCompareRows(data,metricKey,category,year,unit);
    return `<div class="land-cover-shell land-cover-compare-shell" data-land-cover-compare-shell>
      <div class="land-cover-controls" aria-label="Selettori del grafico">
        <label><span>Copertura</span><select data-land-cover-compare-category>${landCoverOptionsMarkup(metric,category)}</select></label>
        <label><span>Anno</span><select data-land-cover-compare-year>${years.map(item=>`<option value="${item}" ${item===year?'selected':''}>${item}</option>`).join('')}</select></label>
        <label><span>Unità</span><select data-land-cover-compare-unit><option value="percent" ${unit==='percent'?'selected':''}>%</option><option value="hectares" ${unit==='hectares'?'selected':''}>ha</option></select></label>
      </div>
      <div class="land-cover-aggregate-reading"><span>Versilia · ${html(def.shortLabel||def.label||'')}</span><strong>${html(landCoverFormat(aggregateValue,unit))}</strong><small>${html(String(year))} · aggregato da superfici</small></div>
      <div class="comparison-bars territory-canonical-comparison" data-land-cover-mode="profile" data-land-cover-category="${html(category)}" data-land-cover-year="${html(String(year))}" data-land-cover-unit="${html(unit)}">${rowsMarkup}</div>
      <p class="composite-compare-note">La quota Versilia è calcolata come Σ ettari della categoria / Σ ettari UCS dei sette Comuni. Non viene usata la media aritmetica delle percentuali comunali.</p>
      ${landCoverTransformationCompareMarkup(metric)}
    </div>`;
  }

  function forestCoverFormat(value,unit) {
    const numeric=Number(value);
    if(!Number.isFinite(numeric)) return 'n.d.';
    return unit==='hectares'?formatValue(numeric,'hectares'):formatValue(numeric,'percent');
  }

  function forestCoverTownMarkup(metric,row) {
    return `<div class="forest-cover-shell">
      <div class="forest-cover-town-readings">
        <article><span>Indice di Boscosità</span><strong>${html(forestCoverFormat(row.forestCoverPct,'percent'))}</strong><small>superficie forestale / superficie comunale</small></article>
        <article><span>Superficie forestale</span><strong>${html(forestCoverFormat(row.forestAreaHa,'hectares'))}</strong><small>Carta Forestale d'Italia / SINFor</small></article>
        <article><span>Superficie comunale</span><strong>${html(forestCoverFormat(row.municipalityAreaHa,'hectares'))}</strong><small>denominatore dell'indice</small></article>
      </div>
      <p class="aggregate-note">Carta Forestale d'Italia: riferimento nominale 2020, aggiornata al 2024. Il rapporto Foreste in Comune è pubblicato a giugno 2026 e usa una definizione nazionale di bosco ai sensi del TUFF.</p>
      <p class="aggregate-note"><b>Serie distinta:</b> questo dato CFI/SINFor non viene concatenato a “Boschi” della serie UCS regionale 2007–2019, perché le due fonti non sono trattate come metodologicamente equivalenti.</p>
    </div>`;
  }

  function forestCoverCompareMarkup(data,metricKey,view={}) {
    const metric=data.metrics[metricKey],unit=view.forestCoverUnit||'percent';
    const items=(metric.rows||[]).map(row=>({row,value:unit==='hectares'?row.forestAreaHa:row.forestCoverPct}));
    const rowsMarkup=territoryDynamicRows(metric,metricKey,items,unit,forestCoverFormat);
    const aggregateValue=unit==='hectares'?metric.aggregate?.forestAreaHa:metric.aggregate?.forestCoverPct;
    return `<div class="forest-cover-shell forest-cover-compare-shell" data-forest-cover-compare-shell>
      <div class="land-cover-controls forest-cover-controls" aria-label="Selettore del grafico forestale">
        <label><span>Lettura</span><select data-forest-cover-compare-unit><option value="percent" ${unit==='percent'?'selected':''}>Indice di Boscosità (%)</option><option value="hectares" ${unit==='hectares'?'selected':''}>Superficie forestale (ha)</option></select></label>
      </div>
      <div class="land-cover-aggregate-reading"><span>Versilia · ${unit==='hectares'?'superficie forestale':'Indice di Boscosità'}</span><strong>${html(forestCoverFormat(aggregateValue,unit))}</strong><small>${unit==='hectares'?'Σ ha forestali dei 7 Comuni':'Σ ha forestali / Σ ha comunali'}</small></div>
      <div class="comparison-bars territory-canonical-comparison" data-forest-cover-unit="${html(unit)}">${rowsMarkup}</div>
      <p class="composite-compare-note">L'Indice di Boscosità Versilia è ponderato sulle superfici: Σ ha forestali / Σ ha comunali. Non è la media aritmetica dei sette indici comunali.</p>
    </div>`;
  }'''

REVIEW_CSS = r'''/* OV TERRITORIO UCS REVIEW CSS v1.36.0 */
.territorial-count-box{display:grid;gap:0;border:1px solid var(--line,#d8ded8);border-radius:14px;background:#fff;overflow:hidden;margin-bottom:16px}
.territorial-count-box>div{display:grid;grid-template-columns:minmax(150px,.8fr) minmax(0,1.8fr);gap:14px;align-items:center;padding:13px 15px;border-top:1px solid var(--line,#e1e5df)}
.territorial-count-box>div:first-child{border-top:0}
.territorial-count-box span{color:var(--muted,#59655e);font-size:.82rem;font-weight:700;line-height:1.35}
.territorial-count-box strong{font-size:1rem;line-height:1.35;text-align:right;overflow-wrap:anywhere}
.territorial-count-box .territorial-count-primary strong{font-size:1.65rem;text-align:left}
.territorial-count-box .territorial-count-primary span{font-size:.9rem}
.territory-canonical-comparison{margin-top:4px}
.forest-cover-shell{display:grid;gap:16px}
.forest-cover-town-readings{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.forest-cover-town-readings article{border:1px solid var(--line,#d8ded8);border-radius:14px;background:#fff;padding:14px;min-width:0}
.forest-cover-town-readings span,.forest-cover-town-readings small{display:block;color:var(--muted,#59655e);line-height:1.4}
.forest-cover-town-readings span{font-size:.78rem;font-weight:700}
.forest-cover-town-readings strong{display:block;margin-top:5px;font-size:1.35rem;line-height:1.15;overflow-wrap:anywhere}
.forest-cover-town-readings small{margin-top:5px;font-size:.78rem}
.forest-cover-controls label{max-width:520px}
/* Correzione locale: le etichette Y lunghe in ha/% restano interamente nel pannello UCS. */
.land-cover-chart-content .trend-chart{box-sizing:border-box;padding-left:46px!important;padding-right:14px!important;overflow:visible!important}
.land-cover-chart-content .trend-chart svg{overflow:visible!important}
.land-cover-chart-content .chart-shell{box-sizing:border-box;padding-left:0;overflow-x:auto;overflow-y:visible}
@media(max-width:760px){
  .territorial-count-box>div{grid-template-columns:1fr;gap:4px;padding:12px 13px}
  .territorial-count-box strong,.territorial-count-box .territorial-count-primary strong{text-align:left}
  .forest-cover-town-readings{grid-template-columns:1fr}
  .land-cover-chart-content .trend-chart{padding-left:40px!important;padding-right:8px!important;min-width:560px}
}
'''


def patch_renderer() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    if REVIEW_MARKER in source:
        return
    source = replace_between(source,"  function territorialClassificationCompareMarkup(data,metricKey)","  function landCoverDefinitions(metric)",DEGURBA_COMPARE,"confronto DEGURBA")
    source = replace_between(source,"  function landCoverCompareRows(data,metricKey,category,year,unit)","  function compositeCompareMarkup(data, metricKey, view={})",CANONICAL_COMPARE_HELPERS,"confronti UCS/foreste")
    source = replace_once(source,"    if (metric.meta.compositeType === 'landCoverProfile') return landCoverCompareMarkup(data,metricKey,view);\n    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationCompareMarkup(data,metricKey);\n    if (metric.meta.compositeType === 'drinkingWaterQuality')","    if (metric.meta.compositeType === 'landCoverProfile') return landCoverCompareMarkup(data,metricKey,view);\n    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationCompareMarkup(data,metricKey);\n    if (metric.meta.compositeType === 'forestCoverIndex') return forestCoverCompareMarkup(data,metricKey,view);\n    if (metric.meta.compositeType === 'drinkingWaterQuality')","routing compare foreste")
    source = replace_once(source,"    if (metric.meta.compositeType === 'landCoverProfile') return landCoverTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'drinkingWaterQuality')","    if (metric.meta.compositeType === 'landCoverProfile') return landCoverTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'forestCoverIndex') return forestCoverTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'drinkingWaterQuality')","routing town foreste")
    source = replace_once(source,"const specialComposite = ['drinkingWaterQuality','remediationProceedings','landCoverProfile','territorialClassification'].includes(compositeType);","const specialComposite = ['drinkingWaterQuality','remediationProceedings','landCoverProfile','territorialClassification','forestCoverIndex'].includes(compositeType);","special composite foreste")
    source = replace_once(source,"        const qualitySelect=event.target.closest('select[data-water-quality-parameter-compare]');","        const forestUnit=event.target.closest('select[data-forest-cover-compare-unit]');\n        if(forestUnit&&bars.contains(event.target)) {\n          renderCompareMetric(data,themeKey,metricKey,normalized,{...view,forestCoverUnit:forestUnit.value||'percent'});\n          return;\n        }\n        const qualitySelect=event.target.closest('select[data-water-quality-parameter-compare]');","eventi confronto foreste")
    old_classification="? `<aside class=\"versilia-position classification-overview\"><span class=\"overline\">Versilia · conteggi</span><strong>${html(String(metric.aggregate?.classificationCounts?.coastalZone??'n.d.'))}/7</strong><small class=\"classification-overview-label\">Comuni in zona costiera</small><p>DEGURBA è una classificazione territoriale, non un punteggio: non viene calcolata alcuna media.</p><div class=\"classification-overview-counts\"><span>DEGURBA</span><b>${html(String(metric.aggregate?.classificationCounts?.degurba2??0))} Comuni in classe 2</b><b>${html(String(metric.aggregate?.classificationCounts?.degurba3??0))} Comune in classe 3</b></div></aside>`"
    new_classification="? `<aside class=\"versilia-position classification-overview\"><span class=\"overline\">Versilia · conteggi</span><strong>${html(String(metric.aggregate?.classificationCounts?.coastalZone??'n.d.'))}/7</strong><small class=\"classification-overview-label\">Comuni in zona costiera</small><div class=\"classification-overview-counts\"><span>Litoranei</span><b>${html(String(metric.aggregate?.classificationCounts?.littoral??0))}/7</b><span>DEGURBA</span><b>${html(String(metric.aggregate?.classificationCounts?.degurba2??0))} comuni classe 2 · ${html(String(metric.aggregate?.classificationCounts?.degurba3??0))} comune classe 3</b></div></aside>`"
    source=replace_once(source,old_classification,new_classification,"box conteggi scheda comunale")
    old_coast="? `<aside class=\"versilia-position coastline-share-overview\"><span class=\"overline\">Quota della linea litoranea Versilia</span><strong>${row.notApplicable ? 'n.a.' : `${html(number1.format(Number(row.value)/Number(metric.aggregate?.value)*100))}%`}</strong><small>${row.notApplicable ? 'Comune non litoraneo' : 'della linea litoranea statistica dei quattro Comuni costieri'}</small><p>È la quota del Comune sul totale Versilia, non uno scostamento dalla media.</p><div><span>Totale Versilia</span><b>${html(formatMetricRowValue(metric.aggregate,metric.aggregate?.value,metric.meta.unit))}</b></div></aside>`"
    new_coast="? `<aside class=\"versilia-position coastline-share-overview\"><span class=\"overline\">Linea litoranea statistica</span><strong>${row.notApplicable ? 'n.a.' : `${html(number1.format(Number(row.value)/Number(metric.aggregate?.value)*100))}%`}</strong><small>${row.notApplicable ? 'Comune non litoraneo' : 'della linea litoranea statistica della Versilia'}</small><div><span>Totale Versilia</span><b>${html(formatMetricRowValue(metric.aggregate,metric.aggregate?.value,metric.meta.unit))}</b></div></aside>`"
    source=replace_once(source,old_coast,new_coast,"quota litoranea senza media")
    RENDERER.write_text(source,encoding="utf-8")


def patch_visual_grammar() -> None:
    source=VISUAL_GRAMMAR.read_text(encoding="utf-8")
    if GRAMMAR_MARKER in source:return
    source=source.replace("    /* OV TERRITORIO UCS VISUAL-GRAMMAR BYPASS v1.36.0 */\n    if (container.closest('[data-land-cover-compare-shell]')) return;",f"    {GRAMMAR_MARKER}",1)
    selection_insert="""    if (type === 'landCoverProfile') {\n      const mode=container?.dataset?.landCoverMode||'profile';\n      if (mode === 'transformation') return { value:row?.transformation?.changedPct, unit:'percent' };\n      const category=container?.dataset?.landCoverCategory||'artificialized';\n      const year=Number(container?.dataset?.landCoverYear)||2019;\n      const unit=container?.dataset?.landCoverUnit||'percent';\n      const index=(metric?.landCoverYears||[]).indexOf(year);\n      const series=row?.coverSeries?.[category]||{};\n      const values=unit==='hectares'?(series.ha||[]):(series.pct||[]);\n      return { value:index>=0?values[index]:null, unit };\n    }\n    if (type === 'forestCoverIndex') {\n      const unit=container?.dataset?.forestCoverUnit||'percent';\n      return { value:unit==='hectares'?row?.forestAreaHa:row?.forestCoverPct, unit };\n    }\n"""
    needle="    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown','agricultureProfile','financialProfile','sexBreakdown'].includes(type)) return null;"
    source=replace_in_block(source,"  function compositeSelectionFor(container, metric, row) {","  function compositeAggregateFor(container, metric) {",needle,selection_insert+needle,"selezione composita canonica")
    aggregate_insert="""    if (type === 'landCoverProfile') {\n      const mode=container?.dataset?.landCoverMode||'profile';\n      if (mode === 'transformation') return { value:metric?.aggregate?.transformation?.changedPct, label:'Versilia · trasformazione 2007→2019' };\n      const category=container?.dataset?.landCoverCategory||'artificialized';\n      const year=Number(container?.dataset?.landCoverYear)||2019;\n      const unit=container?.dataset?.landCoverUnit||'percent';\n      const index=(metric?.landCoverYears||[]).indexOf(year);\n      const series=metric?.aggregate?.coverSeries?.[category]||{};\n      if (unit === 'hectares') return { value:null, label:'Versilia · totale mostrato separatamente' };\n      return { value:index>=0?(series.pct||[])[index]:null, label:'Versilia · quota ponderata' };\n    }\n    if (type === 'forestCoverIndex') {\n      const unit=container?.dataset?.forestCoverUnit||'percent';\n      if (unit === 'hectares') return { value:null, label:'Versilia · totale mostrato separatamente' };\n      return { value:metric?.aggregate?.forestCoverPct, label:'Versilia · Indice di Boscosità' };\n    }\n"""
    source=replace_in_block(source,"  function compositeAggregateFor(container, metric) {","  function enhanceComparison(container) {",needle,aggregate_insert+needle,"aggregato composito canonico")
    source=replace_in_block(source,"  function enhanceComparison(container) {","  function enhance() {","    const aggregate = compositeAggregate || aggregateFor(metric, normalized);","    const aggregate = metricKey === 'statisticalCoastlineLength' ? {value:null,label:'Totale Versilia mostrato separatamente'} : (compositeAggregate || aggregateFor(metric, normalized));","riferimento confronto litoranea")
    VISUAL_GRAMMAR.write_text(source,encoding="utf-8")


def patch_css() -> None:
    source=CSS.read_text(encoding="utf-8")
    if CSS_MARKER in source:return
    CSS.write_text(source.rstrip()+"\n\n"+REVIEW_CSS.strip()+"\n",encoding="utf-8")


def validate_final_state() -> None:
    site=json.loads(SITE_DATA.read_text(encoding="utf-8"))
    if len(site.get("metrics",{}))!=202:raise RuntimeError(f"v1.36 refine: catalogo finale {len(site.get('metrics',{}))}, attese 202 metriche.")
    forest=site["metrics"].get("forestCoverIndex")
    if not forest or len(forest.get("rows",[]))!=7:raise RuntimeError("v1.36 refine: forestCoverIndex assente o incompleto.")
    coast=site["metrics"].get("statisticalCoastlineLength")
    expected={"Camaiore":12.1,"Forte dei Marmi":19.4,"Pietrasanta":17.7,"Viareggio":50.8};total=float(coast["aggregate"]["value"])
    for row in coast["rows"]:
        if row["town"] in expected:
            share=float(row["value"])/total*100.0
            if round(share,1)!=expected[row["town"]]:raise RuntimeError(f"v1.36 refine: quota costa inattesa per {row['town']}: {share:.3f}%.")
        elif not row.get("notApplicable"):raise RuntimeError(f"v1.36 refine: {row['town']} deve essere n.a. per la linea litoranea.")
    renderer=RENDERER.read_text(encoding="utf-8");grammar=VISUAL_GRAMMAR.read_text(encoding="utf-8");css=CSS.read_text(encoding="utf-8")
    for item in (REVIEW_MARKER,'data-land-cover-mode="profile"','data-land-cover-mode="transformation"','data-forest-cover-unit'):
        if item not in renderer:raise RuntimeError(f"v1.36 refine: runtime incompleto, manca {item}.")
    if "if (container.closest('[data-land-cover-compare-shell]')) return;" in grammar:raise RuntimeError("v1.36 refine: bypass visual grammar UCS ancora presente.")
    if GRAMMAR_MARKER not in grammar or CSS_MARKER not in css:raise RuntimeError("v1.36 refine: marker finali canonici mancanti.")


def main() -> None:
    patch_renderer();patch_visual_grammar();patch_css();validate_final_state()
    print("v1.36 refinita: lollipop canonici UCS/foreste, costa a quota Versilia, DEGURBA robusto, 202 metriche.")


if __name__ == "__main__":main()
