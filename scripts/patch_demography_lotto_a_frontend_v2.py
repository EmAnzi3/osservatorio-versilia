#!/usr/bin/env python3
"""Espone nel frontend canonico gli approfondimenti Demografia Lotto A v2.

Il patch viene eseguito DOPO `patch_income_lotto_a_frontend.py`, così preserva
anche il dettaglio Redditi a 8 fasce introdotto dalla #80. Questa revisione:
- elimina il box separato 80+/85+ e lascia 80+ nella distribuzione principale;
- espone 85+ come dettaglio dell'indicatore `ageDistribution`;
- rende la piramide per età e sesso un grafico specchiato con asse e scala;
- aggiunge l'aggregato Versilia del dettaglio RCS in `foreignResidents`;
- rende esplicite le componenti della variazione demografica anche nel confronto.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'assets' / 'app-parts' / '03.txt'
BUILD = ROOT / 'scripts' / 'build_static_brand.py'
BRAND_TEST = ROOT / 'scripts' / 'test_brand_identity.py'
ORIGINAL_CSS = ROOT / 'assets' / 'original.css'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Anchor frontend non trovato: {label}')
    return text.replace(old, new, 1)


def replace_any(text: str, replacements: list[tuple[str, str]], label: str) -> str:
    for old, new in replacements:
        if new in text:
            return text
        if old in text:
            return text.replace(old, new, 1)
    raise RuntimeError(f'Anchor frontend non trovato: {label}')


def patch_helpers(text: str) -> str:
    anchor = '''  function omiZoneTableMarkup(row, compact = false) {'''
    helpers = r'''  function age85DetailData(item) {
    const detail = item?.age85PlusDetail || item?.seniorAgeDetail?.age85Plus;
    if (!detail) return null;
    return {
      year: item?.age85PlusDetail?.year || item?.seniorAgeDetail?.year,
      count: detail.count,
      value: detail.value,
      population: item?.age85PlusDetail?.population || item?.seniorAgeDetail?.population
    };
  }

  function age85InlineMarkup(metric, item) {
    const detail = age85DetailData(item);
    if (metric.meta.key !== 'ageDistribution' || !detail) return '';
    const scope = item?.town ? item.town : 'Versilia';
    return `<div class="composite-age-extra age85-inline-detail" aria-label="${html(scope)} · 85 anni e oltre"><div><span>Dettaglio 85+</span><strong>85 anni e oltre</strong></div><div><b>${html(number1.format(detail.value))}%</b><small>${html(number0.format(detail.count))} residenti · ${html(String(detail.year))}</small></div></div>`;
  }

  function agePyramidMarkup(metric, row) {
    const pyramid = row?.ageSexPyramid;
    if (metric.meta.key !== 'ageDistribution' || !pyramid?.displayBands?.length) return '';
    const bands = [...pyramid.displayBands].reverse();
    const max = Math.max(...bands.flatMap(item => [Number(item.men)||0, Number(item.women)||0]), 1);
    const niceMax = Math.ceil(max / 250) * 250 || max;
    const center = 430, gap = 42, maxWidth = 300, rowHeight = 25, top = 74, bottom = 54;
    const height = top + bands.length * rowHeight + bottom;
    const axisTicks = [niceMax, Math.round(niceMax/2), 0, Math.round(niceMax/2), niceMax];
    const tickXs = [center-gap-maxWidth, center-gap-maxWidth/2, center, center+gap+maxWidth/2, center+gap+maxWidth];
    const axis = tickXs.map((x,index)=>`<g class="age-pyramid-axis"><line x1="${x}" y1="${top-16}" x2="${x}" y2="${height-bottom+10}"/><text x="${x}" y="${height-22}" text-anchor="middle">${html(number0.format(axisTicks[index]))}</text></g>`).join('');
    const rows = bands.map((item,index)=>{
      const y = top + index * rowHeight;
      const men = Number(item.men)||0;
      const women = Number(item.women)||0;
      const menWidth = men / niceMax * maxWidth;
      const womenWidth = women / niceMax * maxWidth;
      return `<g class="age-pyramid-row"><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="17" rx="3" class="age-pyramid-men"><title>${html(item.label)} anni · uomini: ${html(number0.format(men))} residenti</title></rect><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="17" rx="3" class="age-pyramid-women"><title>${html(item.label)} anni · donne: ${html(number0.format(women))} residenti</title></rect><text x="${center}" y="${y+13}" text-anchor="middle">${html(item.label)}</text></g>`;
    }).join('');
    return `<details class="detail-disclosure age-pyramid-detail"><summary><span>${html(metric.meta.pyramidLabel || 'Piramide per età e sesso')}</span><small>${html(String(pyramid.year))} · asse X in residenti</small></summary><div class="age-pyramid-body"><svg class="age-pyramid-chart" viewBox="0 0 860 ${height}" role="img" aria-label="Piramide per età e sesso di ${html(row.town)}"><text x="215" y="32" text-anchor="middle" class="age-pyramid-title">Uomini</text><text x="645" y="32" text-anchor="middle" class="age-pyramid-title">Donne</text><text x="430" y="54" text-anchor="middle" class="age-pyramid-unit">Scala: residenti per classe d’età</text>${axis}<line x1="${center-gap}" y1="${top-22}" x2="${center-gap}" y2="${height-bottom+10}" class="age-pyramid-center"/><line x1="${center+gap}" y1="${top-22}" x2="${center+gap}" y2="${height-bottom+10}" class="age-pyramid-center"/>${rows}<text x="430" y="${height-4}" text-anchor="middle" class="age-pyramid-unit">residenti</text></svg><p class="aggregate-note">Classi quinquennali costruite dal dettaglio POSAS per singola età e sesso; tooltip disponibili su ogni barra.</p></div></details>`;
  }

  function populationChangeComponentsTownMarkup(metric, row) {
    const detail = row?.changeComponents;
    if (metric.meta.key !== 'populationChange' || !detail?.parts?.length) return '';
    return `<section class="history-panel demographic-change-components"><div class="panel-title"><div><span class="overline">Da cosa deriva la variazione</span><h3>Componenti della variazione · ${html(String(detail.year))}</h3></div></div><div class="composite-town-mobility">${detail.parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || 'per1000'))}</strong><small>${part.count === null || part.count === undefined ? 'conteggio n.d.' : `${html(number0.format(part.count))} persone`}</small></article>`).join('')}</div><p class="aggregate-note">${html(detail.note || '')}</p></section>`;
  }

  function populationChangeComponentsCompareMarkup(metric) {
    if (metric.meta.key !== 'populationChange' || !metric.rows?.some(row => row.changeComponents?.parts?.length)) return '';
    const rows = [...metric.rows].sort((a,b)=>a.town.localeCompare(b.town,'it'));
    const year = rows.find(row => row.changeComponents)?.changeComponents?.year;
    const labels = rows.find(row => row.changeComponents?.parts?.length)?.changeComponents?.parts?.map(part => part.label) || [];
    return `<section class="history-panel demographic-change-components compare-change-components"><div class="panel-title"><div><span class="overline">Da cosa deriva la variazione</span><h3>Componenti della variazione · ${html(String(year))}</h3></div></div><div class="demographic-components-grid" role="table" aria-label="Componenti della variazione demografica"><div class="demographic-components-head" role="row"><strong>Comune</strong>${labels.map(label=>`<strong>${html(label)}</strong>`).join('')}</div>${rows.map(row=>`<div role="row"><span>${html(row.town)}</span>${(row.changeComponents?.parts || []).map(part=>`<span><b>${html(formatValue(part.value,part.unit || 'per1000'))}</b><small>${part.count === null || part.count === undefined ? 'conteggio n.d.' : `${html(number0.format(part.count))} persone`}</small></span>`).join('')}</div>`).join('')}</div><p class="aggregate-note">${html(rows[0]?.changeComponents?.note || '')}</p></section>`;
  }

  function foreignOriginsListMarkup(title, items, note) {
    return `<section class="income-band-town-detail"><h4>${html(title)}</h4><div class="composite-town-detail">${(items||[]).map(item=>`<div><span>${html(item.label)}</span><b>${html(number0.format(item.count))}</b><small>${item.share === null || item.share === undefined ? '' : `${html(number1.format(item.share))}%`} ${html(note)}</small></div>`).join('')}</div></section>`;
  }

  function foreignOriginsMarkup(metric, source, scope = 'town') {
    const detail = source?.foreignOrigins || source;
    if (metric.meta.key !== 'foreignResidents' || !detail) return '';
    const title = scope === 'compare' ? 'Versilia · cittadinanze e paesi esteri di nascita' : 'Principali cittadinanze e paesi di nascita';
    const caption = scope === 'compare' ? `${html(String(detail.year))} · somma dei 7 comuni` : `${html(String(detail.year))} · Istat RCS`;
    return `<details class="detail-disclosure foreign-origins-detail ${scope === 'compare' ? 'compare-foreign-origins' : ''}"><summary><span>${html(title)}</span><small>${caption}</small></summary><div class="foreign-origin-body">${foreignOriginsListMarkup('Cittadinanze straniere più numerose',detail.citizenshipTop,'dei residenti stranieri')}${foreignOriginsListMarkup('Paesi esteri di nascita più frequenti',detail.birthCountryTop,'dei residenti nati all’estero')}</div><p class="aggregate-note">Cittadinanza e paese di nascita sono due distribuzioni separate: Istat RCS non pubblica il loro incrocio. Nel confronto Versilia i valori sono somme comunali riordinate sul totale.</p></details>`;
  }

  function foreignOriginsCompareMarkup(metric) {
    return foreignOriginsMarkup(metric, metric.aggregate?.foreignOrigins, 'compare');
  }

'''
    if 'function age85DetailData(item)' in text:
        return text
    if anchor not in text:
        raise RuntimeError('Anchor helper OMI non trovato')
    return text.replace(anchor, helpers + anchor, 1)


def patch_app() -> None:
    text = APP.read_text(encoding='utf-8')
    text = patch_helpers(text)

    old_stack_compare = '''        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;'''
    new_stack_compare = '''        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
        ${age85InlineMarkup(metric,row)}
      </div>`;'''
    text = replace_once(text, old_stack_compare, new_stack_compare, '85+ nel confronto distribuzione')

    old_stock_compare = '''      return `<div class="composite-stock-list">${rows.map(row=>{const query=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a class="composite-stock-row" href="${route(`comuni/${row.slug}/?${query}`)}"><strong>${html(row.town)}</strong><span><b>${html(formatValue(row.value,'percent'))}</b><small>quota residenti</small></span><span><b>${html(formatValue(row.count,'number'))}</b><small>residenti stranieri</small></span></a>`;}).join('')}</div>`;'''
    new_stock_compare = '''      return `<div class="composite-stock-list">${rows.map(row=>{const query=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a class="composite-stock-row" href="${route(`comuni/${row.slug}/?${query}`)}"><strong>${html(row.town)}</strong><span><b>${html(formatValue(row.value,'percent'))}</b><small>quota residenti</small></span><span><b>${html(formatValue(row.count,'number'))}</b><small>residenti stranieri</small></span></a>`;}).join('')}</div>${foreignOriginsCompareMarkup(metric)}`;'''
    text = replace_once(text, old_stock_compare, new_stock_compare, 'RCS aggregato nel confronto')

    old_stock_town = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>`;'''
    new_stock_town = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>${foreignOriginsMarkup(metric,row,'town')}`;'''
    text = replace_once(text, old_stock_town, new_stock_town, 'RCS nella scheda comunale')

    old_detail_const = '''    const detailDisclosure = detailParts.length ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div class="composite-town-detail">${detailParts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></details>` : '';'''
    new_detail_const = old_detail_const + '''
    const age85Extra = age85InlineMarkup(metric,row);
    const agePyramidDisclosure = agePyramidMarkup(metric,row);'''
    text = replace_once(text, old_detail_const, new_detail_const, '85+ const scheda comunale')

    old_town_distribution_return = '''    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div></div>${detailDisclosure}`;'''
    new_town_distribution_return = '''    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div>${age85Extra}${agePyramidDisclosure}</div>${detailDisclosure}`;'''
    text = replace_once(text, old_town_distribution_return, new_town_distribution_return, '85+ e piramide nella distribuzione comunale')

    old_options = '''    const summary = compositeSummary(metric,row);
    return [{ key:'summary', label:summary.label, value:summary.value, unit:summary.unit, formatted:summary.formatted }, ...(row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:'percent', formatted:`${number1.format(part.value)}%`, index }))];'''
    new_options = '''    const summary = compositeSummary(metric,row);
    const partOptions = (row.parts || []).map((part,index)=>({ key:`part-${index}`, label:part.selectorLabel || part.label, value:part.value, unit:'percent', formatted:`${number1.format(part.value)}%`, index }));
    const age85 = age85DetailData(row);
    return [{ key:'summary', label:summary.label, value:summary.value, unit:summary.unit, formatted:summary.formatted }, ...partOptions, ...(metric.meta.key === 'ageDistribution' && age85 ? [{ key:'age85Plus', label:'85 anni e oltre', value:age85.value, unit:'percent', formatted:`${number1.format(age85.value)}%` }] : [])];'''
    text = replace_once(text, old_options, new_options, '85+ nel selettore distribuzione')

    old_agg = '''    if (choice === 'summary') return compositeAggregateSummary(metric);
    const index = Number(String(choice).replace('part-',''));'''
    new_agg = '''    if (metric.meta.key === 'ageDistribution' && choice === 'age85Plus') {
      const detail = age85DetailData(metric.aggregate);
      return { label:'Versilia · 85 anni e oltre', value:detail?.value, unit:'percent', formatted:detail?.value === undefined ? 'n.d.' : `${number1.format(detail.value)}%` };
    }
    if (choice === 'summary') return compositeAggregateSummary(metric);
    const index = Number(String(choice).replace('part-',''));'''
    text = replace_once(text, old_agg, new_agg, '85+ aggregato distribuzione')

    old_rank = '''      if (choice === 'summary') return { code:r.code, value:Number(r.summaryValue) };
      const index = Number(String(choice).replace('part-',''));'''
    new_rank = '''      if (metric.meta.key === 'ageDistribution' && choice === 'age85Plus') return { code:r.code, value:Number(age85DetailData(r)?.value) };
      if (choice === 'summary') return { code:r.code, value:Number(r.summaryValue) };
      const index = Number(String(choice).replace('part-',''));'''
    text = replace_once(text, old_rank, new_rank, '85+ ranking distribuzione')

    old_compare_render = '''      bars.innerHTML = compositeType ? `<div class="topic-bars composite-topic-bars">${compositeCompareMarkup(data,metricKey)}</div>` : `<div class="topic-bars"><div class="comparison-bars">${barRows(data,metricKey,{normalized})}</div></div>`;'''
    new_compare_render = '''      const changeComponents = populationChangeComponentsCompareMarkup(metric);
      bars.innerHTML = compositeType ? `<div class="topic-bars composite-topic-bars">${compositeCompareMarkup(data,metricKey)}${changeComponents}</div>` : `<div class="topic-bars"><div class="comparison-bars">${barRows(data,metricKey,{normalized})}</div>${changeComponents}</div>`;'''
    text = replace_once(text, old_compare_render, new_compare_render, 'componenti variazione nel confronto')

    old_town_render = '''      ${deepDiveMarkup(data, town, themeKey)}'''
    new_town_render = '''      ${populationChangeComponentsTownMarkup(metric,row)}
      ${deepDiveMarkup(data, town, themeKey)}'''
    text = replace_once(text, old_town_render, new_town_render, 'componenti variazione nella scheda comunale')

    APP.write_text(text, encoding='utf-8')


def patch_cache_version() -> None:
    text = BUILD.read_text(encoding='utf-8')
    text = replace_any(text, [
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v116"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v117"'),
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v115"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v117"'),
    ], 'cache bundle v117')
    BUILD.write_text(text, encoding='utf-8')

    text = BRAND_TEST.read_text(encoding='utf-8')
    text = replace_any(text, [
        ('assets/app-bundle.js?v=20260820-v116', 'assets/app-bundle.js?v=20260820-v117'),
        ('assets/app-bundle.js?v=20260820-v115', 'assets/app-bundle.js?v=20260820-v117'),
    ], 'test cache bundle v117')
    BRAND_TEST.write_text(text, encoding='utf-8')


def patch_css() -> None:
    marker = '/* PR81 Demografia Lotto A v2 review fixes */'
    text = ORIGINAL_CSS.read_text(encoding='utf-8')
    if marker in text:
        return
    css = r'''

/* PR81 Demografia Lotto A v2 review fixes */
.composite-age-extra{margin-top:14px;padding:15px 17px;border:1px solid var(--line);border-radius:16px;background:#fffaf1cc;display:flex;justify-content:space-between;align-items:center;gap:16px;line-height:1.45}.composite-age-extra span{color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.11em;text-transform:uppercase}.composite-age-extra strong{display:block;font-size:15px}.composite-age-extra b{font-size:20px}.composite-age-extra small{display:block;color:var(--muted);font-size:12px;margin-top:3px}.detail-disclosure{margin-top:16px;border:1px solid var(--line);border-radius:18px;background:#fffaf1cc;overflow:hidden;line-height:1.45}.detail-disclosure>summary{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:17px 19px;cursor:pointer}.detail-disclosure>summary span{font-weight:780}.detail-disclosure>summary small{color:var(--muted);font-size:12px;line-height:1.35;text-align:right}.detail-disclosure>div,.detail-disclosure>.foreign-origin-body,.detail-disclosure>.age-pyramid-body{padding:0 19px 19px}.age-pyramid-body{overflow-x:auto}.age-pyramid-chart{width:100%;min-width:720px;height:auto;display:block;margin:0 auto}.age-pyramid-title{font-size:14px;font-weight:800;fill:currentColor}.age-pyramid-unit{font-size:12px;fill:var(--muted)}.age-pyramid-axis line{stroke:currentColor;opacity:.12}.age-pyramid-axis text,.age-pyramid-row text{font-size:11px;fill:var(--muted)}.age-pyramid-center{stroke:currentColor;opacity:.18}.age-pyramid-men{fill:var(--theme-color);opacity:.9}.age-pyramid-women{fill:var(--theme-color);opacity:.48}.demographic-change-components{padding:21px;line-height:1.5}.demographic-change-components .panel-title{margin-bottom:14px}.demographic-change-components .composite-town-mobility article{min-width:0;padding:16px;line-height:1.42}.demographic-components-grid{display:grid;gap:9px;margin-top:12px}.demographic-components-grid [role=row]{display:grid;grid-template-columns:minmax(120px,1.05fr) repeat(3,minmax(130px,1fr));gap:9px;align-items:stretch}.demographic-components-grid span,.demographic-components-grid strong{padding:13px 14px;border:1px solid var(--line);border-radius:13px;background:#fff;line-height:1.38}.demographic-components-grid strong{font-size:12px}.demographic-components-grid b{display:block}.demographic-components-grid small{display:block;color:var(--muted);font-size:11px;margin-top:4px}.foreign-origin-body{display:grid;gap:15px}.foreign-origin-body .income-band-town-detail{margin:0}.foreign-origin-body .composite-town-detail{gap:10px}.foreign-origin-body .composite-town-detail>div{padding:14px 15px;line-height:1.42}@media (max-width:760px){.composite-age-extra{align-items:flex-start;flex-direction:column}.detail-disclosure>summary{align-items:flex-start;flex-direction:column}.detail-disclosure>summary small{text-align:left}.age-pyramid-chart{min-width:640px}.demographic-change-components{padding:17px}.demographic-components-grid [role=row]{grid-template-columns:1fr}.demographic-components-head{display:none}.demographic-components-grid [role=row] span:first-child{font-weight:800;background:var(--theme-soft)}}
'''
    ORIGINAL_CSS.write_text(text + css, encoding='utf-8')


def main() -> None:
    patch_app()
    patch_css()
    patch_cache_version()
    print('Frontend Demografia v2 revisionato: 85+ come dettaglio, piramide con asse, RCS Versilia, componenti variazione e padding; bundle v117.')


if __name__ == '__main__':
    main()
