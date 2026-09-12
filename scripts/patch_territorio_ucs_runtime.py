#!/usr/bin/env python3
"""Estende i renderer canonici con le capacità territoriali/UCS della v1.36.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMATTER = ROOT / "assets/app-parts/00.txt"
RENDERER = ROOT / "assets/app-parts/03.txt"
CSS = ROOT / "assets/static.css"
HELPERS = ROOT / "scripts/territorio_ucs_runtime_helpers.js"
CSS_PAYLOAD = ROOT / "scripts/territorio_ucs_runtime.css"

UNITS_MARKER = "/* OV TERRITORIO UCS UNITS v1.36.0 */"
JS_MARKER = "/* OV TERRITORIO UCS RUNTIME v1.36.0 */"
CSS_MARKER = "/* OV TERRITORIO UCS UI v1.36.0 */"


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
    const landCoverProfile = metric.meta.compositeType === 'landCoverProfile';""",
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
        ? `<aside class="versilia-position classification-overview"><span class="overline">Versilia · conteggi</span><strong>${html(String(metric.aggregate?.classificationCounts?.coastalZone??'n.d.'))}/7<small>Comuni in zona costiera</small></strong><p>Le classi territoriali sono categoriali: non viene calcolata alcuna media DEGURBA.</p><div><span>DEGURBA</span><b>${html(String(metric.aggregate?.classificationCounts?.degurba2??0))} classe 2 · ${html(String(metric.aggregate?.classificationCounts?.degurba3??0))} classe 3</b></div></aside>`
      : (drinkingQuality
        ? ''""",
        "posizione town classificazione",
    )
    source = replace_once(
        source,
        """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}""",
        """      ${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings','hydroRisk','territorialClassification','landCoverProfile'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}""",
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
        if(chartHost) chartHost.innerHTML=landCoverChartMarkup(metric,row,categorySelect?.value||'artificialized',unitSelect?.value||'percent',row.town);
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
    patch_css()
    print("v1.36: renderer territoriali/UCS e selettori interni al box grafico abilitati.")


if __name__ == "__main__":
    main()
