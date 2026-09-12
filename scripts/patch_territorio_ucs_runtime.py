#!/usr/bin/env python3
"""Estende i renderer canonici con le capacità territoriali/UCS della v1.36.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMATTER = ROOT / "assets/app-parts/00.txt"
RENDERER = ROOT / "assets/app-parts/03.txt"
CSS = ROOT / "assets/static.css"
UX_HISTORY = ROOT / "assets/ux-history.js"
VISUAL_GRAMMAR = ROOT / "assets/visual-grammar.js"
HELPERS = ROOT / "scripts/territorio_ucs_runtime_helpers.js"
CSS_PAYLOAD = ROOT / "scripts/territorio_ucs_runtime.css"

UNITS_MARKER = "/* OV TERRITORIO UCS UNITS v1.36.0 */"
JS_MARKER = "/* OV TERRITORIO UCS RUNTIME v1.36.0 */"
CSS_MARKER = "/* OV TERRITORIO UCS UI v1.36.0 */"
UX_HISTORY_MARKER = "/* OV TERRITORIO UCS UX-HISTORY BYPASS v1.36.0 */"
VISUAL_GRAMMAR_MARKER = "/* OV TERRITORIO UCS VISUAL-GRAMMAR BYPASS v1.36.0 */"


def replace_once(source: str, needle: str, replacement: str, label: str) -> str:
    count = source.count(needle)
    if count != 1:
        raise RuntimeError(f"v1.36 runtime: {label} non patchabile in modo univoco ({count} occorrenze).")
    return source.replace(needle, replacement, 1)


def patch_units() -> None:
    source = FORMATTER.read_text(encoding="utf-8")
    if UNITS_MARKER in source:
        return
    needle = """      case 'metres': return `${number0.format(v)} m`;
      case 'km': return `${number2.format(v)} km`;"""
    replacement = """      case 'metres': return `${number0.format(v)} m`;
      /* OV TERRITORIO UCS UNITS v1.36.0 */
      case 'hectares': return `${number2.format(v)} ha`;
      case 'km': return `${number2.format(v)} km`;"""
    FORMATTER.write_text(replace_once(source, needle, replacement, "unità ettari"), encoding="utf-8")


def patch_renderer() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    if JS_MARKER in source:
        return
    helpers = HELPERS.read_text(encoding="utf-8")
    if JS_MARKER not in helpers:
        raise RuntimeError("v1.36 runtime: marker helper JS assente.")

    source = replace_once(
        source,
        "  function compositeCompareMarkup(data, metricKey, view={}) {",
        helpers + "  function compositeCompareMarkup(data, metricKey, view={}) {",
        "helper territoriali/UCS",
    )
    source = replace_once(
        source,
        """    const metric = data.metrics[metricKey];
    const rows = metricRows(data, metricKey);
    if (metric.meta.compositeType === 'drinkingWaterQuality')""",
        """    const metric = data.metrics[metricKey];
    const rows = metricRows(data, metricKey);
    if (metric.meta.compositeType === 'landCoverProfile') return landCoverCompareMarkup(data,metricKey,view);
    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationCompareMarkup(data,metricKey);
    if (metric.meta.compositeType === 'drinkingWaterQuality')""",
        "routing compare custom",
    )
    source = replace_once(
        source,
        """  function compositeTownMarkup(metric, row) {
    if (metric.meta.compositeType === 'drinkingWaterQuality')""",
        """  function compositeTownMarkup(metric, row) {
    if (metric.meta.compositeType === 'landCoverProfile') return landCoverTownMarkup(metric,row);
    if (metric.meta.compositeType === 'territorialClassification') return territorialClassificationTownMarkup(metric,row);
    if (metric.meta.compositeType === 'drinkingWaterQuality')""",
        "routing town custom",
    )
    source = replace_once(
        source,
        "    const specialComposite = ['drinkingWaterQuality','remediationProceedings'].includes(compositeType);",
        "    const specialComposite = ['drinkingWaterQuality','remediationProceedings','landCoverProfile','territorialClassification'].includes(compositeType);",
        "special composite compare",
    )
    source = replace_once(
        source,
        """      bars.onchange = event => {
        const qualitySelect=event.target.closest('select[data-water-quality-parameter-compare]');""",
        """      bars.onchange = event => {
        const landCategory=event.target.closest('select[data-land-cover-compare-category]');
        const landYear=event.target.closest('select[data-land-cover-compare-year]');
        const landUnit=event.target.closest('select[data-land-cover-compare-unit]');
        if((landCategory||landYear||landUnit)&&bars.contains(event.target)) {
          const shell=event.target.closest('[data-land-cover-compare-shell]');
          renderCompareMetric(data,themeKey,metricKey,normalized,{
            ...view,
            landCoverCategory:landCategory?.value||shell?.querySelector('[data-land-cover-compare-category]')?.value||view.landCoverCategory||'artificialized',
            landCoverYear:Number(landYear?.value||shell?.querySelector('[data-land-cover-compare-year]')?.value||view.landCoverYear||2019),
            landCoverUnit:landUnit?.value||shell?.querySelector('[data-land-cover-compare-unit]')?.value||view.landCoverUnit||'percent'
          });
          return;
        }
        const qualitySelect=event.target.closest('select[data-water-quality-parameter-compare]');""",
        "eventi compare UCS",
    )
    source = replace_once(
        source,
        "    const remediation = metric.meta.compositeType === 'remediationProceedings';",
        """    const remediation = metric.meta.compositeType === 'remediationProceedings';
    const territorialClassification = metric.meta.compositeType === 'territorialClassification';
    const landCoverProfile = metric.meta.compositeType === 'landCoverProfile';
    const coastlineShareMetric = metric.meta.key === 'statisticalCoastlineLength';""",
        "flag town custom",
    )
    source = replace_once(
        source,
        """    const panelOverline = drinkingQuality ? 'Dati analitici GAIA' : remediation ? 'Dettaglio dei procedimenti' : extractiveProductionHistory ? 'Andamento storico'""",
        """    const panelOverline = territorialClassification ? 'Classificazioni ufficiali' : landCoverProfile ? 'Serie territoriale UCS' : drinkingQuality ? 'Dati analitici GAIA' : remediation ? 'Dettaglio dei procedimenti' : extractiveProductionHistory ? 'Andamento storico'""",
        "overline town custom",
    )
    source = replace_once(
        source,
        """    const panelTitle = drinkingQuality ? 'Valori per località e parametro' : remediation ? 'Iter attivi e chiusi' : extractiveProductionHistory ? 'Evoluzione della produzione estrattiva'""",
        """    const panelTitle = territorialClassification ? 'Litoraneità, zona costiera e DEGURBA' : landCoverProfile ? 'Evoluzione 2007–2019' : drinkingQuality ? 'Valori per località e parametro' : remediation ? 'Iter attivi e chiusi' : extractiveProductionHistory ? 'Evoluzione della produzione estrattiva'""",
        "titolo town custom",
    )
    source = replace_once(
        source,
        """    const primaryLabel = drinkingQuality ? 'Consultazione analitica' : remediation ? 'Procedimenti SISBON' : selectable ? summary.label : (composite ? (metric.meta.primaryLabel || 'Valore di riferimento') : '');
    const primaryValue = drinkingQuality ? `${number0.format(metric.parameterDefinitions?.length||0)} parametri GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : selectable ? summary.formatted : formatMetricRowValue(row,row.value,metric.meta.unit);""",
        """    const primaryLabel = territorialClassification ? 'Grado di urbanizzazione' : drinkingQuality ? 'Consultazione analitica' : remediation ? 'Procedimenti SISBON' : selectable ? summary.label : (composite ? (metric.meta.primaryLabel || 'Valore di riferimento') : '');
    const primaryValue = territorialClassification ? `DEGURBA ${html(String(row.classification?.degurba||'n.d.'))}` : drinkingQuality ? `${number0.format(metric.parameterDefinitions?.length||0)} parametri GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : selectable ? summary.formatted : formatMetricRowValue(row,row.value,metric.meta.unit);""",
        "primary town custom",
    )
    source = replace_once(
        source,
        """      : (drinkingQuality
        ? ''""",
        """      : territorialClassification
        ? `<aside class="versilia-position classification-overview"><span class="overline">Versilia · conteggi</span><strong>${html(String(metric.aggregate?.classificationCounts?.coastalZone??'n.d.'))}/7</strong><small class="classification-overview-label">Comuni in zona costiera</small><p>DEGURBA è una classificazione territoriale, non un punteggio: non viene calcolata alcuna media.</p><div class="classification-overview-counts"><span>DEGURBA</span><b>${html(String(metric.aggregate?.classificationCounts?.degurba2??0))} Comuni in classe 2</b><b>${html(String(metric.aggregate?.classificationCounts?.degurba3??0))} Comune in classe 3</b></div></aside>`
      : landCoverProfile
        ? `<aside class="versilia-position land-cover-overview"><span class="overline">Serie UCS</span><strong>${html(String(metric.landCoverYears?.length||0))}<small>annualità omogenee</small></strong><p>Il confronto cambia con copertura, anno e unità selezionati nel grafico; non viene fissata una graduatoria unica.</p><div><span>Periodo</span><b>2007–2019</b></div></aside>`
      : coastlineShareMetric
        ? `<aside class="versilia-position coastline-share-overview"><span class="overline">Quota della linea litoranea Versilia</span><strong>${row.notApplicable ? 'n.a.' : `${html(number1.format(Number(row.value)/Number(metric.aggregate?.value)*100))}%`}</strong><small>${row.notApplicable ? 'Comune non litoraneo' : 'della linea litoranea statistica dei quattro Comuni costieri'}</small><p>È la quota del Comune sul totale Versilia, non uno scostamento dalla media.</p><div><span>Totale Versilia</span><b>${html(formatMetricRowValue(metric.aggregate,metric.aggregate?.value,metric.meta.unit))}</b></div></aside>`
      : (drinkingQuality
        ? ''""",
        "posizione town custom",
    )
    source = replace_once(
        source,
        "['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType) || (isEconomicScopeMetric(metric) && economicScope !== 'total')",
        "metric.meta.key === 'statisticalCoastlineLength' || ['drinkingWaterQuality','remediationProceedings','hydroRisk','territorialClassification','landCoverProfile'].includes(metric.meta.compositeType) || (isEconomicScopeMetric(metric) && economicScope !== 'total')",
        "benchmark town custom",
    )
    source = replace_once(
        source,
        """    if (drinkingQuality) {
      const root=container.querySelector('.water-quality-town');""",
        """    if (landCoverProfile) {
      const root=container.querySelector('[data-land-cover-town-shell]');
      const categorySelect=root?.querySelector('[data-land-cover-town-category]');
      const unitSelect=root?.querySelector('[data-land-cover-town-unit]');
      const chartHost=root?.querySelector('[data-land-cover-town-chart]');
      const applyLandCover=()=>{
        if(chartHost) {
          chartHost.innerHTML=landCoverChartMarkup(metric,row,categorySelect?.value||'artificialized',unitSelect?.value||'percent',row.town);
          installChartInteractions(chartHost);
        }
      };
      categorySelect?.addEventListener('change',applyLandCover);
      unitSelect?.addEventListener('change',applyLandCover);
    }
    if (drinkingQuality) {
      const root=container.querySelector('.water-quality-town');""",
        "eventi town UCS",
    )
    source = replace_once(
        source,
        """    const drinkingQuality=metric.meta.compositeType==='drinkingWaterQuality',remediation=metric.meta.compositeType==='remediationProceedings';
    const cardValue = drinkingQuality ? `${number0.format(row.localities?.length||0)} località GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : metric.meta.compositeType === 'distribution' ? compositeSummary(metric,row).formatted : formatMetricRowValue(row,row.value,metric.meta.unit);
    const cardMeta=drinkingQuality ? `${metric.meta.year} · dettaglio analitico` : remediation ? `${metric.meta.year} · conteggi SISBON` : `${metric.meta.year} · ${row.notApplicable ? 'n.a.' : `${rank}° valore`}`;""",
        """    const drinkingQuality=metric.meta.compositeType==='drinkingWaterQuality',remediation=metric.meta.compositeType==='remediationProceedings',territorialClassification=metric.meta.compositeType==='territorialClassification',landCoverProfile=metric.meta.compositeType==='landCoverProfile';
    const cardValue = territorialClassification ? `DEGURBA ${html(String(row.classification?.degurba||'n.d.'))}` : landCoverProfile ? `${html(number1.format(row.value))}% artificializzato` : drinkingQuality ? `${number0.format(row.localities?.length||0)} località GAIA` : remediation ? `${number0.format(remediationPartValue(row,'active'))} attivi · ${number0.format(remediationPartValue(row,'closed'))} chiusi` : metric.meta.compositeType === 'distribution' ? compositeSummary(metric,row).formatted : formatMetricRowValue(row,row.value,metric.meta.unit);
    const cardMeta=territorialClassification ? `${metric.meta.year} · ${row.classification?.coastalZone?'zona costiera':'non costiera'}` : landCoverProfile ? `2019 · serie 2007–2019` : drinkingQuality ? `${metric.meta.year} · dettaglio analitico` : remediation ? `${metric.meta.year} · conteggi SISBON` : `${metric.meta.year} · ${row.notApplicable ? 'n.a.' : `${rank}° valore`}`;""",
        "indicator card custom",
    )
    RENDERER.write_text(source, encoding="utf-8")


def patch_auxiliary_runtime() -> None:
    history = UX_HISTORY.read_text(encoding="utf-8")
    if UX_HISTORY_MARKER not in history:
        needle = "if (['drinkingWaterQuality','remediationProceedings','financialProfile','hydroRisk'].includes(selected.metric?.meta?.compositeType)) return;"
        if history.count(needle) != 2:
            raise RuntimeError(f"v1.36 runtime: bypass ux-history non patchabile ({history.count(needle)} occorrenze).")
        replacement = UX_HISTORY_MARKER + "\n    if (['drinkingWaterQuality','remediationProceedings','financialProfile','hydroRisk','territorialClassification','landCoverProfile'].includes(selected.metric?.meta?.compositeType)) return;"
        history = history.replace(needle, replacement)
        UX_HISTORY.write_text(history, encoding="utf-8")

    grammar = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    if VISUAL_GRAMMAR_MARKER not in grammar:
        grammar = replace_once(
            grammar,
            """  function enhanceComparison(container) {
    if (!data || !container?.isConnected) return;""",
            """  function enhanceComparison(container) {
    if (!data || !container?.isConnected) return;
    /* OV TERRITORIO UCS VISUAL-GRAMMAR BYPASS v1.36.0 */
    if (container.closest('[data-land-cover-compare-shell]')) return;""",
            "visual grammar compare UCS",
        )
        grammar = replace_once(
            grammar,
            "if (['distribution','agricultureProfile','ratioProfile','financialProfile','hydroRisk'].includes(metric.meta?.compositeType) || metric.meta?.ordinalScale) return;",
            "if (['distribution','agricultureProfile','ratioProfile','financialProfile','hydroRisk','territorialClassification','landCoverProfile'].includes(metric.meta?.compositeType) || metric.meta?.ordinalScale) return;",
            "visual grammar town UCS",
        )
        VISUAL_GRAMMAR.write_text(grammar, encoding="utf-8")


def patch_css() -> None:
    source = CSS.read_text(encoding="utf-8")
    if CSS_MARKER in source:
        return
    payload = CSS_PAYLOAD.read_text(encoding="utf-8")
    if CSS_MARKER not in payload:
        raise RuntimeError("v1.36 runtime: marker CSS assente.")
    CSS.write_text(source.rstrip() + "\n\n" + payload.strip() + "\n", encoding="utf-8")


def main() -> None:
    patch_units()
    patch_renderer()
    patch_auxiliary_runtime()
    patch_css()
    print("v1.36: renderer territoriali/UCS, storico a linee e selettori interni al box grafico abilitati.")


if __name__ == "__main__":
    main()
