#!/usr/bin/env python3
"""Apply the Salute demographic UI overlay after the stable v1.40 core runtime.

The patch composes with all previous release overlays by using small stable
structural anchors. It never replaces the whole Versilia comparison card.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PART_03 = ROOT / "assets" / "app-parts" / "03.txt"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Salute demographic runtime patch non univoca ({label}): {count}")
    return source.replace(old, new, 1)


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

  function updateHealthDemographicPosition(position,metric,choice) {
    if(!position||metric?.meta?.theme!=='salute'||!metric?.meta?.demographicSource) return;
    position.dataset.compositeSelection=choice;
    const overline=position.querySelector('.overline');
    const note=position.querySelector('p');
    if(overline) overline.textContent='Rispetto al valore ARS Versilia';
    if(note) note.textContent='Confronto con l’aggregato ufficiale Zona Versilia della stessa fascia d’età e dello stesso sesso; non è una media dei Comuni.';
    const tuscany=compositeTuscanySelection(metric,choice);
    let host=position.querySelector('.health-tuscany-reference');
    if(tuscany&&!host) {
      host=document.createElement('div');
      host.className='health-tuscany-reference';
      host.innerHTML='<span data-composite-tuscany-label></span><b data-composite-tuscany-value></b>';
      position.appendChild(host);
    }
    const label=host?.querySelector('[data-composite-tuscany-label]');
    const value=host?.querySelector('[data-composite-tuscany-value]');
    if(tuscany&&label) label.textContent=tuscany.label;
    if(tuscany&&value) value.textContent=tuscany.formatted;
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
        "    const initialCompositeChoice=sexBreakdown?defaultSexChoice:(demographicBreakdown?defaultDemographicChoice:(options[0]?.key||'summary'));\n    const summaryDelta = selectable ? (row.notApplicable ? { headline:'n.a.', direction:'Comune non costiero' } : compositeDeltaText(summary.value,aggregateSummary.value,summary.unit)) : null;",
        "initial demographic selection",
    )

    source = replace_once(
        source,
        "      updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);",
        "      updateExtractiveTownPosition(metric,row,initialChoice,initialPosition);\n      updateHealthDemographicPosition(initialPosition,metric,initialCompositeChoice);",
        "initial health benchmark",
    )

    source = replace_once(
        source,
        "        updateExtractiveTownPosition(metric,row,choice,position);",
        "        updateExtractiveTownPosition(metric,row,choice,position);\n        updateHealthDemographicPosition(position,metric,choice);",
        "dynamic health benchmark",
    )

    APP_PART_03.write_text(source, encoding="utf-8")
    print("Salute demographic runtime: sesso, fasce d'eta', Versilia ARS e Toscana allineati")


if __name__ == "__main__":
    main()
