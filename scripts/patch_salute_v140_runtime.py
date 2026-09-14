#!/usr/bin/env python3
"""Runtime refinements for Salute v1.40 town pages.

The public build is transactional: this patch updates the materialized catalog and
UI sources only inside the ephemeral build workspace. Canonical tracked sources are
restored by ``public_build_workspace`` after prerendering.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
APP_PART_03 = ROOT / "assets" / "app-parts" / "03.txt"
APP_PART_04 = ROOT / "assets" / "app-parts" / "04.txt"
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
VISUAL_GRAMMAR_CSS = ROOT / "assets" / "visual-grammar.css"


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Salute v1.40 runtime patch non univoca ({label}): {count}")
    return source.replace(old, new, 1)


def patch_health_comparison_contract() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    health = data.get("themes", {}).get("salute", {})
    metric_keys = health.get("metrics", [])
    metrics = data.get("metrics", {})

    for key in metric_keys:
        metric = metrics.get(key)
        if not isinstance(metric, dict):
            continue
        meta = metric.setdefault("meta", {})
        aggregate = metric.get("aggregate") or {}
        aggregate_label = str(aggregate.get("label") or "")

        # Strutture fisiche: il confronto percentuale corretto è la quota del
        # Comune sul totale dei sette Comuni, non lo scostamento dalla media.
        if key in {"hospitals", "accreditedRsaCount"}:
            meta["comparisonReference"] = "aggregate"
            meta["comparisonDifference"] = "shareOfAggregate"
            meta["comparisonLabel"] = "totale Versilia"
            meta["comparisonOverline"] = "Quota sul totale Versilia"
            meta["comparisonShareDirection"] = "del totale Versilia"
            meta["comparisonNote"] = (
                "Quota delle strutture presenti nel Comune sul totale censito nei sette Comuni; "
                "non misura accessibilità, capacità o qualità del servizio."
            )
            continue

        # Nel tema Salute l'aggregate già pubblicato è il riferimento editoriale:
        # ARS 202M, mediana dichiarata o densità territoriale. Non va sostituito
        # da una media semplice calcolata dal runtime.
        if aggregate.get("value") is None:
            continue
        meta["comparisonReference"] = "aggregate"

        if aggregate_label == "Valore ARS Versilia" or meta.get("demographicSource", {}).get("publisher") == "ARS Toscana":
            meta["comparisonLabel"] = "valore ARS Versilia"
            meta["comparisonDirectionLabel"] = "il valore ARS Versilia"
            meta["comparisonOverline"] = "Rispetto al valore ARS Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa l’aggregato ufficiale Zona Versilia pubblicato da ARS, "
                "non la media semplice dei Comuni; descrive uno scostamento numerico e "
                "non esprime un giudizio di qualità."
            )
        elif aggregate_label.startswith("Mediana"):
            meta["comparisonLabel"] = "mediana Versilia"
            meta["comparisonDirectionLabel"] = "la mediana Versilia"
            meta["comparisonOverline"] = "Rispetto alla mediana Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa la mediana dichiarata per i sette Comuni e descrive "
                "soltanto lo scostamento numerico."
            )
        elif aggregate_label == "Densità Versilia":
            meta["comparisonLabel"] = "densità Versilia"
            meta["comparisonDirectionLabel"] = "la densità Versilia"
            meta["comparisonOverline"] = "Rispetto alla densità Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa la densità calcolata sul totale della popolazione dei "
                "sette Comuni, non la media semplice delle densità comunali."
            )
        else:
            meta["comparisonLabel"] = "riferimento Versilia"
            meta["comparisonDirectionLabel"] = "il riferimento Versilia"
            meta["comparisonOverline"] = "Rispetto al riferimento Versilia"
            meta["comparisonNote"] = (
                "Il confronto usa il riferimento territoriale dichiarato dall’indicatore "
                "e non introduce valutazioni di qualità."
            )

    save_json(DATA, data)


def patch_visual_grammar() -> None:
    source = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    source = replace_once(
        source,
        "if (['maritimeConcessions','maritimeConcessionFeesDue','extractiveSites','extractiveProduction','extractivePlanning'].includes(key) && metric?.meta?.comparisonDifference === 'shareOfAggregate') {",
        "if (metric?.meta?.comparisonDifference === 'shareOfAggregate') {",
        "shareOfAggregate generic contract",
    )
    source = replace_once(
        source,
        ": 'del totale dei quattro Comuni costieri';",
        ": (metric?.meta?.comparisonShareDirection || 'del totale Versilia');",
        "share direction fallback",
    )

    per_capita_tail = """    const territorialPerCapitaReference = comparisonLabel === 'valore pro capite Versilia';
    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0
          ? 'in linea'
          : territorialPerCapitaReference
            ? (diff > 0 ? 'sopra il valore pro capite Versilia' : 'sotto il valore pro capite Versilia')
            : (diff > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'),
        compact: territorialPerCapitaReference ? 'confronto con il valore pro capite Versilia' : 'confronto con Versilia',
        overline,
        note,
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return {
      headline: '0,0%',
      direction: 'in linea',
      compact: territorialPerCapitaReference ? 'in linea con il valore pro capite Versilia' : 'in linea con la media Versilia',
      overline,
      note,
    };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: territorialPerCapitaReference
        ? (relative > 0 ? 'sopra il valore pro capite Versilia' : 'sotto il valore pro capite Versilia')
        : (relative > 0 ? 'sopra la media Versilia' : 'sotto la media Versilia'),
      compact: territorialPerCapitaReference
        ? `${sign}${abs}% vs valore pro capite Versilia`
        : `${sign}${abs}% vs media Versilia`,
      overline,
      note,
    };
"""
    generalized_tail = """    const directionReference = metric?.meta?.comparisonDirectionLabel
      || (/^(valore|riferimento|totale)\b/i.test(comparisonLabel) ? `il ${comparisonLabel}` : `la ${comparisonLabel}`);
    if (aggregate === 0) {
      const diff = local - aggregate;
      return {
        headline: formatAxis(diff, metric.meta.unit),
        direction: diff === 0 ? 'in linea' : diff > 0 ? `sopra ${directionReference}` : `sotto ${directionReference}`,
        compact: `confronto con ${comparisonLabel}`,
        overline,
        note,
      };
    }

    const relative = ((local / aggregate) - 1) * 100;
    if (Math.abs(relative) < 0.05) return {
      headline: '0,0%',
      direction: 'in linea',
      compact: `in linea con ${comparisonLabel}`,
      overline,
      note,
    };
    const sign = relative > 0 ? '+' : '−';
    const abs = number1.format(Math.abs(relative));
    return {
      headline: `${sign}${abs}%`,
      direction: relative > 0 ? `sopra ${directionReference}` : `sotto ${directionReference}`,
      compact: `${sign}${abs}% vs ${comparisonLabel}`,
      overline,
      note,
    };
"""
    source = replace_once(
        source,
        per_capita_tail,
        generalized_tail,
        "relative comparison contract after per-capita runtime",
    )
    VISUAL_GRAMMAR.write_text(source, encoding="utf-8")


def patch_health_demographic_ui() -> None:
    source = APP_PART_03.read_text(encoding="utf-8")
    sentinel = "function healthDemographicTableMarkup(metric,row)"
    if sentinel in source:
        return

    helper = r'''  function healthDemographicTableMarkup(metric,row) {
    const ages=metric.meta.ageOptions||[];
    const genders=metric.meta.genderOptions||[];
    const cells=new Map((row.parts||[]).map(part=>[part.key,part]));
    const valueCell=part=>{
      if(!part||part.value===null||part.value===undefined) return '<strong>n.d.</strong>';
      const unit=part.unit||metric.meta.unit;
      const base=part.numerator!==null&&part.numerator!==undefined&&part.denominator!==null&&part.denominator!==undefined
        ? `<small>${html(number0.format(Number(part.numerator)))} / ${html(number0.format(Number(part.denominator)))}</small>`
        : '';
      return `<strong>${html(formatValue(part.value,unit))}</strong>${base}`;
    };
    return `<details class="detail-disclosure health-demographic-detail" open><summary><span>Dettaglio per fascia d’età e sesso</span><small>${html(metric.meta.year)} · ARS Toscana</small></summary><div class="demographic-rate-table-wrap"><table class="demographic-rate-table health-demographic-table"><thead><tr><th>Fascia d’età</th>${genders.map(g=>`<th>${html(g.label)}</th>`).join('')}</tr></thead><tbody>${ages.map(age=>`<tr><th><span>${html(age.label)}</span></th>${genders.map(g=>`<td>${valueCell(cells.get(`${age.key}|${g.key}`))}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="demographic-rate-table-note">Valori pubblicati da ARS Toscana per la stessa definizione e lo stesso periodo. Dove disponibile viene usata la misura standardizzata della fonte; numeratore e denominatore sono riportati come base di calcolo.</p></details>`;
  }

  function healthSexDetailMarkup(metric,row) {
    const parts=row.parts||[];
    if(!parts.length) return '';
    return `<details class="detail-disclosure health-sex-detail" open><summary><span>Dettaglio per sesso</span><small>${html(metric.meta.year)} · ARS Toscana</small></summary><div class="composite-town-detail">${parts.map(part=>`<div><span>${html(part.label)}</span><b>${part.value===null||part.value===undefined?'n.d.':html(formatValue(part.value,part.unit||metric.meta.unit))}</b>${part.numerator===null||part.numerator===undefined||part.denominator===null||part.denominator===undefined?'':`<small>${html(number0.format(Number(part.numerator)))} / ${html(number0.format(Number(part.denominator)))}</small>`}</div>`).join('')}</div></details>`;
  }

  function compositeTuscanySelection(metric,choice) {
    const parts=metric?.tuscany?.parts||[];
    const part=parts.find(item=>item.key===choice)||parts[0];
    if(!part) return null;
    const unit=part.unit||metric.meta.unit;
    return {label:`Toscana · ${part.label||metric.meta.label}`,value:part.value,unit,formatted:part.value===null||part.value===undefined?'n.d.':formatValue(part.value,unit)};
  }

'''
    source = replace_once(
        source,
        "  function compositeTownMarkup(metric, row) {",
        helper + "  function compositeTownMarkup(metric, row) {",
        "health demographic helpers",
    )

    source = replace_once(
        source,
        "    if (metric.meta.compositeType === 'sexBreakdown') return '';\n    if (metric.meta.compositeType === 'demographicBreakdown') {\n      const pyramid = demographicRatePyramidMarkup(metric,row);\n      const detail = demographicRateTableMarkup(metric,row);\n      const history = row.series?.values?.length ? `<details class=\"detail-disclosure demographic-history\"><summary><span>Storico della lettura base</span><small>${html(metric.meta.defaultAge === '25-64' ? '25–64 anni · Totale' : 'lettura base')}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · lettura base`)}</div></details>` : '';\n      return pyramid + detail + history;\n    }",
        "    if (metric.meta.compositeType === 'sexBreakdown') {\n      if (metric.meta.theme !== 'salute') return '';\n      const history=row.series?.values?.length ? `<details class=\"detail-disclosure demographic-history\"><summary><span>Storico · Totale</span><small>${html(metric.meta.year)}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · Totale`)}</div></details>` : '';\n      return healthSexDetailMarkup(metric,row)+history;\n    }\n    if (metric.meta.compositeType === 'demographicBreakdown') {\n      if (metric.meta.theme === 'salute') {\n        const history=row.series?.values?.length ? `<details class=\"detail-disclosure demographic-history\"><summary><span>Storico · Totale</span><small>${html(metric.meta.year)}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · Totale`)}</div></details>` : '';\n        return healthDemographicTableMarkup(metric,row)+history;\n      }\n      const pyramid = demographicRatePyramidMarkup(metric,row);\n      const detail = demographicRateTableMarkup(metric,row);\n      const history = row.series?.values?.length ? `<details class=\"detail-disclosure demographic-history\"><summary><span>Storico della lettura base</span><small>${html(metric.meta.defaultAge === '25-64' ? '25–64 anni · Totale' : 'lettura base')}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · lettura base`)}</div></details>` : '';\n      return pyramid + detail + history;\n    }",
        "health composite town detail",
    )

    source = replace_once(
        source,
        "    const summaryDelta = selectable ? (row.notApplicable ? { headline:'n.a.', direction:'Comune non costiero' } : compositeDeltaText(summary.value,aggregateSummary.value,summary.unit)) : null;",
        "    const initialCompositeChoice=sexBreakdown?defaultSexChoice:(demographicBreakdown?defaultDemographicChoice:(options[0]?.key||'summary'));\n    const initialTuscany=selectable&&themeKey==='salute'?compositeTuscanySelection(metric,initialCompositeChoice):null;\n    const summaryDelta = selectable ? (row.notApplicable ? { headline:'n.a.', direction:'Comune non costiero' } : compositeDeltaText(summary.value,aggregateSummary.value,summary.unit)) : null;",
        "initial Tuscany selection",
    )

    old_position = """    const positionMarkup = selectable
      ? `<aside class=\"versilia-position composite-versilia-position\" data-composite-selection=\"summary\"><span class=\"overline\">Rispetto alla Versilia</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${html(summaryDelta.direction)}</small></strong><p>Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.</p><div><span data-composite-aggregate-label>${html(aggregateSummary.label)}</span><b data-composite-aggregate-value>${html(aggregateSummary.formatted)}</b></div></aside>`
"""
    new_position = """    const positionMarkup = selectable
      ? `<aside class=\"versilia-position composite-versilia-position\" data-composite-selection=\"${html(initialCompositeChoice)}\"><span class=\"overline\">${themeKey==='salute'&&metric.meta.demographicSource?'Rispetto al valore ARS Versilia':'Rispetto alla Versilia'}</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${html(summaryDelta.direction)}</small></strong><p>${themeKey==='salute'&&metric.meta.demographicSource?'Confronto con l’aggregato ufficiale Zona Versilia della stessa fascia d’età e dello stesso sesso; non è una media dei Comuni.':'Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'}</p><div><span data-composite-aggregate-label>${html(aggregateSummary.label)}</span><b data-composite-aggregate-value>${html(aggregateSummary.formatted)}</b></div>${initialTuscany?`<div class=\"health-tuscany-reference\"><span data-composite-tuscany-label>${html(initialTuscany.label)}</span><b data-composite-tuscany-value>${html(initialTuscany.formatted)}</b></div>`:''}</aside>`
"""
    source = replace_once(source, old_position, new_position, "health town benchmark panel")

    old_apply = """          if(aggLabel) aggLabel.textContent=agg.label;
          if(aggValue) aggValue.textContent=agg.formatted;
        }
"""
    new_apply = """          if(aggLabel) aggLabel.textContent=agg.label;
          if(aggValue) aggValue.textContent=agg.formatted;
          const tuscany=themeKey==='salute'?compositeTuscanySelection(metric,choice):null;
          const tuscanyLabel=position.querySelector('[data-composite-tuscany-label]');
          const tuscanyValue=position.querySelector('[data-composite-tuscany-value]');
          if(tuscany&&tuscanyLabel) tuscanyLabel.textContent=tuscany.label;
          if(tuscany&&tuscanyValue) tuscanyValue.textContent=tuscany.formatted;
        }
"""
    source = replace_once(source, old_apply, new_apply, "dynamic Tuscany benchmark")

    APP_PART_03.write_text(source, encoding="utf-8")


def remove_redundant_health_deep_dive() -> None:
    source = APP_PART_04.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n    if \(themeKey === 'salute'\) \{.*?\n    \}\n    if \(themeKey === 'economia'\)",
        flags=re.DOTALL,
    )
    replacement = "\n    if (themeKey === 'salute') return '';\n    if (themeKey === 'economia')"
    source, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError(f"Blocco approfondimento Salute non trovato in modo univoco: {count}")
    APP_PART_04.write_text(source, encoding="utf-8")


def patch_health_position_layout() -> None:
    source = VISUAL_GRAMMAR_CSS.read_text(encoding="utf-8")
    sentinel = "/* Salute v1.40: confronto comunale senza sovrapposizioni */"
    if sentinel in source:
        return
    source += f"""

{sentinel}
.town-topic[data-theme="salute"] .versilia-position > div {{
  grid-template-columns: 1fr;
  align-items: start;
  gap: 5px;
}}

.town-topic[data-theme="salute"] .versilia-position > div span {{
  min-width: 0;
  overflow-wrap: anywhere;
}}

.town-topic[data-theme="salute"] .versilia-position > div b {{
  max-width: 100%;
  text-align: left;
  line-height: 1.12;
}}

.town-topic[data-theme="salute"] .health-tuscany-reference {{
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid currentColor;
}}

.town-topic[data-theme="salute"] .health-demographic-table th,
.town-topic[data-theme="salute"] .health-demographic-table td {{
  vertical-align: top;
}}

.town-topic[data-theme="salute"] .health-demographic-table td small {{
  display: block;
  margin-top: 3px;
  opacity: .68;
}}
"""
    VISUAL_GRAMMAR_CSS.write_text(source, encoding="utf-8")


def main() -> None:
    patch_health_comparison_contract()
    patch_visual_grammar()
    patch_health_demographic_ui()
    remove_redundant_health_deep_dive()
    patch_health_position_layout()
    print("Salute v1.40 runtime: riferimenti Versilia, quote strutture, demografia ARS e scheda comunale allineati")


if __name__ == "__main__":
    main()
