#!/usr/bin/env python3
"""Raffina la UI età×genere: gruppi logici, piramide sesso/età, tooltip e lollipop coerenti."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "assets" / "app-parts" / "03.txt"
VISUAL_JS = ROOT / "assets" / "visual-grammar.js"
VISUAL_CSS = ROOT / "assets" / "visual-grammar.css"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Raffinamento UI non applicabile: {label}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, new: str, label: str, start_at: int = 0) -> str:
    start_pos = text.find(start, start_at)
    if start_pos < 0:
        raise RuntimeError(f"Raffinamento UI non applicabile: inizio {label}")
    end_pos = text.find(end, start_pos)
    if end_pos < 0:
        raise RuntimeError(f"Raffinamento UI non applicabile: fine {label}")
    return text[:start_pos] + new + text[end_pos:]


def patch_app() -> None:
    text = APP.read_text(encoding="utf-8")
    marker = "data-lavoro-istruzione-pyramid"
    if marker in text:
        print("UI età/genere già raffinata")
        return
    if "data-demographic-age" not in text:
        raise RuntimeError("Applicare prima patch_lavoro_istruzione_eta_genere_frontend.py")

    helper_anchor = "  function compositeCompareControls(metric, choice, scale = 'value') {"
    helpers = r'''  function demographicAgeOptionsMarkup(metric, selectedKey) {
    const options = metric.meta.ageOptions || [];
    const groups = [];
    options.forEach(option => {
      const group = option.group || 'Fasce';
      if (!groups.includes(group)) groups.push(group);
    });
    return groups.map(group => `<optgroup label="${html(group)}">${options.filter(option => (option.group || 'Fasce') === group).map(option => `<option value="${html(option.key)}" ${option.key === selectedKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</optgroup>`).join('');
  }

  function demographicRateTooltipMarkup({boxX,boxY,guideX,guideY,label,part}) {
    const boxWidth = 228, boxHeight = 58;
    const targetY = boxY < guideY ? boxY + boxHeight : boxY;
    const value = part?.value;
    const numerator = Number(part?.numerator) || 0;
    const denominator = Number(part?.denominator) || 0;
    return `<g class="chart-tooltip" hidden><line class="chart-guide" x1="${guideX}" y1="${guideY}" x2="${guideX}" y2="${targetY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+15}">${html(label)}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+34}">${html(formatValue(value,'percent'))}</text><text class="chart-tooltip-meta" x="${boxX+12}" y="${boxY+50}">${html(number0.format(numerator))} / ${html(number0.format(denominator))}</text></g>`;
  }

  function demographicRatePyramidMarkup(metric, row) {
    const cells = new Map((row.parts || []).map(part => [part.key, part]));
    const ageMap = new Map((metric.meta.ageOptions || []).map(age => [age.key, age]));
    const keys = metric.meta.pyramidAgeKeys || [];
    const bands = keys.map(key => ageMap.get(key)).filter(Boolean).reverse();
    if (!bands.length) return '';
    const maxValue = 100;
    const center = 430, gap = 48, maxWidth = 300, rowHeight = 42, top = 78, bottom = 58;
    const height = top + bands.length * rowHeight + bottom;
    const tickXs = [center-gap-maxWidth, center-gap-maxWidth/2, center, center+gap+maxWidth/2, center+gap+maxWidth];
    const tickValues = [100, 50, 0, 50, 100];
    const axis = tickXs.map((x,index)=>`<g class="age-pyramid-axis"><line x1="${x}" y1="${top-18}" x2="${x}" y2="${height-bottom+10}"/><text x="${x}" y="${height-22}" text-anchor="middle">${tickValues[index]}%</text></g>`).join('');
    const rows = bands.map((age,index) => {
      const y = top + index * rowHeight;
      const men = cells.get(`${age.key}|men`) || {};
      const women = cells.get(`${age.key}|women`) || {};
      const menValue = Math.max(0, Math.min(100, Number(men.value) || 0));
      const womenValue = Math.max(0, Math.min(100, Number(women.value) || 0));
      const menWidth = menValue / maxValue * maxWidth;
      const womenWidth = womenValue / maxValue * maxWidth;
      const tooltipY = y < 112 ? y + 22 : y - 64;
      const menBoxX = Math.max(8, center-gap-menWidth-238);
      const womenBoxX = Math.min(624, center+gap+womenWidth+10);
      const menLabel = `${age.label} · Uomini`;
      const womenLabel = `${age.label} · Donne`;
      const menAria = `${menLabel}: ${formatValue(men.value,'percent')}; ${number0.format(Number(men.numerator)||0)} su ${number0.format(Number(men.denominator)||0)}`;
      const womenAria = `${womenLabel}: ${formatValue(women.value,'percent')}; ${number0.format(Number(women.numerator)||0)} su ${number0.format(Number(women.denominator)||0)}`;
      return `<g class="age-pyramid-row"><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(menAria)}"><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="22" rx="4" class="age-pyramid-men"></rect>${demographicRateTooltipMarkup({boxX:menBoxX,boxY:tooltipY,guideX:center-gap-menWidth,guideY:y+11,label:menLabel,part:men})}</g><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(womenAria)}"><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="22" rx="4" class="age-pyramid-women"></rect>${demographicRateTooltipMarkup({boxX:womenBoxX,boxY:tooltipY,guideX:center+gap+womenWidth,guideY:y+11,label:womenLabel,part:women})}</g><text x="${center}" y="${y+16}" text-anchor="middle">${html(age.label)}</text></g>`;
    }).join('');
    return `<div class="demographic-rate-pyramid" data-lavoro-istruzione-pyramid="1"><div class="demographic-rate-pyramid-head"><div><span class="overline">Età e sesso</span><h4>Piramide dei tassi</h4></div><small>2024 · scala 0–100%</small></div><div class="trend-chart age-pyramid-trend"><svg class="age-pyramid-chart demographic-rate-pyramid-chart" viewBox="0 0 860 ${height}" role="img" aria-label="${html(metric.meta.label)} per età e sesso a ${html(row.town)}"><text x="215" y="32" text-anchor="middle" class="age-pyramid-title">Uomini</text><text x="645" y="32" text-anchor="middle" class="age-pyramid-title">Donne</text><text x="430" y="54" text-anchor="middle" class="age-pyramid-unit">Percentuale nella fascia e nel sesso</text>${axis}<line x1="${center-gap}" y1="${top-24}" x2="${center-gap}" y2="${height-bottom+10}" class="age-pyramid-center"/><line x1="${center+gap}" y1="${top-24}" x2="${center+gap}" y2="${height-bottom+10}" class="age-pyramid-center"/>${rows}<text x="430" y="${height-4}" text-anchor="middle" class="age-pyramid-unit">percentuale</text></svg></div><p class="aggregate-note demographic-rate-pyramid-note">La piramide usa solo fasce non sovrapposte. Le letture aggregate 25–64 e complessiva restano disponibili nei selettori e nel dettaglio.</p></div>`;
  }

  function demographicRateTableMarkup(metric, row) {
    const ages = metric.meta.ageOptions || [];
    const genders = metric.meta.genderOptions || [];
    const cells = new Map((row.parts || []).map(part => [part.key,part]));
    return `<details class="detail-disclosure demographic-rate-detail"><summary><span>Valori e basi di calcolo</span><small>6 fasce · Totale, Uomini, Donne</small></summary><div class="demographic-rate-table-wrap"><table class="demographic-rate-table"><thead><tr><th>Età</th>${genders.map(g=>`<th>${html(g.label)}</th>`).join('')}</tr></thead><tbody>${ages.map(age=>`<tr class="${age.group === 'Aggregati' ? 'aggregate-age-row' : ''}"><th><span>${html(age.label)}</span><small>${html(age.group || '')}</small></th>${genders.map(g=>{const part=cells.get(`${age.key}|${g.key}`)||{};return `<td><strong>${html(formatValue(part.value,'percent'))}</strong><small>${html(number0.format(Number(part.numerator)||0))} / ${html(number0.format(Number(part.denominator)||0))}</small></td>`;}).join('')}</tr>`).join('')}</tbody></table></div><p class="demographic-rate-table-note">Il rapporto sotto ogni percentuale mostra numeratore e denominatore utilizzati. 25–64 è ricostruita sommando 25–49 e 50–64 sui conteggi prima del calcolo del tasso.</p></details>`;
  }

'''
    text = replace_once(text, helper_anchor, helpers + helper_anchor, "helper età/genere")

    compare_age_old = "<select data-demographic-age>${(metric.meta.ageOptions || []).map(option=>`<option value=\"${html(option.key)}\" ${option.key === ageKey ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select>"
    compare_age_new = "<select data-demographic-age>${demographicAgeOptionsMarkup(metric,ageKey)}</select>"
    text = replace_once(text, compare_age_old, compare_age_new, "gruppi fasce confronto")

    town_age_old = "<select data-demographic-town-age>${(metric.meta.ageOptions || []).map(option=>`<option value=\"${html(option.key)}\" ${option.key === (metric.meta.defaultAge || '25-64') ? 'selected' : ''}>${html(option.label)}</option>`).join('')}</select>"
    town_age_new = "<select data-demographic-town-age>${demographicAgeOptionsMarkup(metric,metric.meta.defaultAge || '25-64')}</select>"
    text = replace_once(text, town_age_old, town_age_new, "gruppi fasce comune")

    function_pos = text.find("  function compositeTownMarkup(metric, row) {")
    demographic_start = "    if (metric.meta.compositeType === 'demographicBreakdown') {"
    stock_start = "    if (metric.meta.compositeType === 'stock')"
    new_demographic = r'''    if (metric.meta.compositeType === 'demographicBreakdown') {
      const pyramid = demographicRatePyramidMarkup(metric,row);
      const detail = demographicRateTableMarkup(metric,row);
      const history = row.series?.values?.length ? `<details class="detail-disclosure demographic-history"><summary><span>Storico della lettura base</span><small>${html(metric.meta.defaultAge === '25-64' ? '25–64 anni · Totale' : 'lettura base')}</small></summary><div>${seriesChart(row.series,metric.meta.unit,`${metric.meta.label} · lettura base`)}</div></details>` : '';
      return pyramid + detail + history;
    }
'''
    text = replace_between(text, demographic_start, stock_start, new_demographic, "piramide comunale", function_pos)
    APP.write_text(text, encoding="utf-8")
    print("APP: gruppi fasce e piramide età/sesso applicati")


def patch_visual_grammar() -> None:
    text = VISUAL_JS.read_text(encoding="utf-8")
    marker = "demographicBreakdown visual selection"
    if marker in text:
        print("Visual grammar età/genere già corretta")
        return

    selection_old = """    if (!choice || !['stock','omi','mobility','securityMeasures'].includes(type)) return null;
    if (type === 'securityMeasures') {"""
    selection_new = """    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown'].includes(type)) return null;
    // demographicBreakdown visual selection: usa la cella selezionata, non il valore base 25–64 Totale.
    if (type === 'demographicBreakdown') {
      const part = (row?.parts || []).find(item => item.key === choice) || {};
      return { value: part.value, unit: part.unit || metric?.meta?.unit || 'percent' };
    }
    if (type === 'securityMeasures') {"""
    text = replace_once(text, selection_old, selection_new, "visual selection")

    aggregate_old = """    if (!choice || !['stock','omi','mobility','securityMeasures'].includes(type)) return null;
    if (type === 'securityMeasures') {"""
    aggregate_new = """    if (!choice || !['stock','omi','mobility','securityMeasures','demographicBreakdown'].includes(type)) return null;
    if (type === 'demographicBreakdown') {
      const part = (metric.aggregate?.parts || []).find(item => item.key === choice) || {};
      return { value: part.value, label:`Versilia · ${part.ageLabel || ''} · ${part.genderLabel || ''}`, unit: part.unit || metric?.meta?.unit || 'percent' };
    }
    if (type === 'securityMeasures') {"""
    text = replace_once(text, aggregate_old, aggregate_new, "visual aggregate")
    VISUAL_JS.write_text(text, encoding="utf-8")
    print("Visual grammar: lollipop collegati alla combinazione età×genere selezionata")


def patch_css() -> None:
    text = VISUAL_CSS.read_text(encoding="utf-8")
    marker = "PR91 demographic rate pyramid"
    if marker in text:
        print("CSS piramide già presente")
        return
    css = r'''

/* PR91 demographic rate pyramid */
.demographic-view-controls {
  align-items: end;
}

.demographic-town-selectors {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
  margin-top: 18px;
}

.demographic-town-selectors label,
.demographic-view-controls .compare-choice-select {
  min-width: 0;
}

.demographic-rate-pyramid {
  margin-top: 4px;
  padding: 20px 22px 16px;
  border: 1px solid color-mix(in srgb, var(--ink) 11%, transparent);
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface) 94%, var(--theme-soft, var(--blue-soft)));
}

.demographic-rate-pyramid-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  padding: 0 2px 14px;
}

.demographic-rate-pyramid-head h4 {
  margin: 3px 0 0;
  font-size: 18px;
}

.demographic-rate-pyramid-head small,
.demographic-rate-pyramid-note,
.demographic-rate-table-note {
  color: var(--muted);
}

.demographic-rate-pyramid .age-pyramid-trend {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 2px 0 4px;
}

.demographic-rate-pyramid-chart {
  display: block;
  min-width: 720px;
  width: 100%;
  height: auto;
}

.demographic-rate-pyramid .chart-tooltip-meta {
  fill: var(--muted);
  font-size: 10px;
  font-family: var(--font-geist-mono), monospace;
}

.demographic-rate-detail {
  margin-top: 16px;
}

.demographic-rate-table-wrap {
  overflow-x: auto;
  padding: 8px 4px 4px;
}

.demographic-rate-table {
  width: 100%;
  min-width: 660px;
  border-collapse: separate;
  border-spacing: 0;
}

.demographic-rate-table th,
.demographic-rate-table td {
  padding: 12px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 9%, transparent);
  text-align: right;
  vertical-align: middle;
}

.demographic-rate-table thead th {
  color: var(--muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .05em;
}

.demographic-rate-table th:first-child {
  text-align: left;
}

.demographic-rate-table tbody th span,
.demographic-rate-table tbody th small,
.demographic-rate-table td strong,
.demographic-rate-table td small {
  display: block;
}

.demographic-rate-table tbody th small,
.demographic-rate-table td small {
  margin-top: 3px;
  color: var(--muted);
  font-size: 9px;
  font-family: var(--font-geist-mono), monospace;
}

.demographic-rate-table td strong {
  font-size: 15px;
}

.demographic-rate-table .aggregate-age-row {
  background: color-mix(in srgb, var(--theme-soft, var(--blue-soft)) 54%, transparent);
}

.demographic-rate-table-note {
  margin: 10px 6px 4px;
  line-height: 1.55;
}

@media (max-width: 700px) {
  .demographic-town-selectors {
    grid-template-columns: 1fr;
  }

  .demographic-rate-pyramid {
    padding: 16px 12px 14px;
  }

  .demographic-rate-pyramid-head {
    align-items: start;
    flex-direction: column;
    gap: 4px;
  }

  .demographic-rate-table th,
  .demographic-rate-table td {
    padding: 10px 12px;
  }
}
'''
    VISUAL_CSS.write_text(text.rstrip() + css + "\n", encoding="utf-8")
    print("CSS: spaziature e piramide età/sesso applicate")


def main() -> None:
    patch_app()
    patch_visual_grammar()
    patch_css()


if __name__ == "__main__":
    main()
