#!/usr/bin/env python3
"""Apply the optional Salute demographic UI overlay after the stable v1.40 core runtime.

This patch intentionally targets structural anchors instead of the full literal
markup emitted by previous release overlays. It therefore composes with the
v1.33-v1.40 runtime chain without depending on the exact wording of the base
Versilia comparison panel.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PART_03 = ROOT / "assets" / "app-parts" / "03.txt"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Salute demographic runtime patch non univoca ({label}): {count}")
    return source.replace(old, new, 1)


def regex_once(source: str, pattern: re.Pattern[str], replacement: str, label: str) -> str:
    updated, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError(f"Salute demographic runtime patch non univoca ({label}): {count}")
    return updated


def main() -> None:
    source = APP_PART_03.read_text(encoding="utf-8")
    sentinel = "function healthDemographicTableMarkup(metric,row)"
    if sentinel in source:
        print("Salute demographic runtime gia' applicato.")
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

    position_pattern = re.compile(
        r'    const positionMarkup = selectable\n'
        r'      \? `<aside class="versilia-position composite-versilia-position"[^`]*?</aside>`\n'
    )
    new_position = """    const positionMarkup = selectable
      ? `<aside class=\"versilia-position composite-versilia-position\" data-composite-selection=\"${html(initialCompositeChoice)}\"><span class=\"overline\">${themeKey==='salute'&&metric.meta.demographicSource?'Rispetto al valore ARS Versilia':'Rispetto alla Versilia'}</span><strong data-composite-delta>${html(summaryDelta.headline)}<small>${html(summaryDelta.direction)}</small></strong><p>${themeKey==='salute'&&metric.meta.demographicSource?'Confronto con l’aggregato ufficiale Zona Versilia della stessa fascia d’età e dello stesso sesso; non è una media dei Comuni.':'Il confronto descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.'}</p><div><span data-composite-aggregate-label>${html(aggregateSummary.label)}</span><b data-composite-aggregate-value>${html(aggregateSummary.formatted)}</b></div>${initialTuscany?`<div class=\"health-tuscany-reference\"><span data-composite-tuscany-label>${html(initialTuscany.label)}</span><b data-composite-tuscany-value>${html(initialTuscany.formatted)}</b></div>`:''}</aside>`
"""
    source = regex_once(source, position_pattern, new_position, "health town benchmark panel")

    apply_pattern = re.compile(
        r"(      const applyChoice=\(choice\)=>\{.*?"
        r"          if\(aggLabel\) aggLabel\.textContent=agg\.label;\n"
        r"          if\(aggValue\) aggValue\.textContent=agg\.formatted;\n)"
        r"(        \}\n        updateFiscalRecoveryTownPosition)",
        flags=re.DOTALL,
    )
    apply_extra = """          const tuscany=themeKey==='salute'?compositeTuscanySelection(metric,choice):null;
          const tuscanyLabel=position.querySelector('[data-composite-tuscany-label]');
          const tuscanyValue=position.querySelector('[data-composite-tuscany-value]');
          if(tuscany&&tuscanyLabel) tuscanyLabel.textContent=tuscany.label;
          if(tuscany&&tuscanyValue) tuscanyValue.textContent=tuscany.formatted;
"""
    source, count = apply_pattern.subn(lambda match: match.group(1) + apply_extra + match.group(2), source, count=1)
    if count != 1:
        raise RuntimeError(f"Salute demographic runtime patch non univoca (dynamic Tuscany benchmark): {count}")

    APP_PART_03.write_text(source, encoding="utf-8")
    print("Salute demographic runtime: sesso, fasce d'eta', Versilia ARS e Toscana allineati")


if __name__ == "__main__":
    main()
