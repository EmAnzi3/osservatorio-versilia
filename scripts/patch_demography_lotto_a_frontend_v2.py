#!/usr/bin/env python3
"""Espone nel frontend canonico gli approfondimenti Demografia Lotto A v2.

Il patch viene eseguito DOPO `patch_income_lotto_a_frontend.py`, così preserva
anche il dettaglio Redditi introdotto dalla #80. Questa revisione applica il
contratto di coerenza della #79:
- 85+ NON ha un box autonomo: è una normale componente di `ageDistribution`;
- la piramide usa lo stesso sistema `.chart-point/.chart-tooltip` dei grafici storici;
- il dettaglio RCS usa le superfici canoniche e deve sempre andare a capo;
- nessun blocco aggiuntivo duplica le componenti di `populationChange`.
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
    helpers = r'''  function agePyramidTooltipMarkup({boxX,boxY,guideX,guideY,label,value}) {
    const boxWidth = 208, boxHeight = 40;
    const targetY = boxY < guideY ? boxY + boxHeight : boxY;
    return `<g class="chart-tooltip" hidden><line class="chart-guide" x1="${guideX}" y1="${guideY}" x2="${guideX}" y2="${targetY}"></line><rect x="${boxX}" y="${boxY}" width="${boxWidth}" height="${boxHeight}" rx="8"></rect><text class="chart-tooltip-year" x="${boxX+12}" y="${boxY+15}">${html(label)}</text><text class="chart-tooltip-value" x="${boxX+12}" y="${boxY+31}">${html(number0.format(value))} residenti</text></g>`;
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
      const tooltipY = y < 112 ? y + 22 : y - 46;
      const menBoxX = Math.max(8, center-gap-menWidth-218);
      const womenBoxX = Math.min(644, center+gap+womenWidth+10);
      const menLabel = `${item.label} · Uomini`;
      const womenLabel = `${item.label} · Donne`;
      return `<g class="age-pyramid-row"><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(menLabel)}: ${html(number0.format(men))} residenti"><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="17" rx="3" class="age-pyramid-men"></rect>${agePyramidTooltipMarkup({boxX:menBoxX,boxY:tooltipY,guideX:center-gap-menWidth,guideY:y+8.5,label:menLabel,value:men})}</g><g class="chart-point age-pyramid-point" tabindex="0" role="button" aria-label="${html(womenLabel)}: ${html(number0.format(women))} residenti"><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="17" rx="3" class="age-pyramid-women"></rect>${agePyramidTooltipMarkup({boxX:womenBoxX,boxY:tooltipY,guideX:center+gap+womenWidth,guideY:y+8.5,label:womenLabel,value:women})}</g><text x="${center}" y="${y+13}" text-anchor="middle">${html(item.label)}</text></g>`;
    }).join('');
    return `<details class="detail-disclosure age-pyramid-detail"><summary><span>${html(metric.meta.pyramidLabel || 'Piramide per età e sesso')}</span><small>${html(String(pyramid.year))} · asse X in residenti</small></summary><div class="age-pyramid-body"><div class="trend-chart age-pyramid-trend"><svg class="age-pyramid-chart" viewBox="0 0 860 ${height}" role="img" aria-label="Piramide per età e sesso di ${html(row.town)}"><text x="215" y="32" text-anchor="middle" class="age-pyramid-title">Uomini</text><text x="645" y="32" text-anchor="middle" class="age-pyramid-title">Donne</text><text x="430" y="54" text-anchor="middle" class="age-pyramid-unit">Scala: residenti per classe d’età</text>${axis}<line x1="${center-gap}" y1="${top-22}" x2="${center-gap}" y2="${height-bottom+10}" class="age-pyramid-center"/><line x1="${center+gap}" y1="${top-22}" x2="${center+gap}" y2="${height-bottom+10}" class="age-pyramid-center"/>${rows}<text x="430" y="${height-4}" text-anchor="middle" class="age-pyramid-unit">residenti</text></svg></div><p class="aggregate-note age-pyramid-note">Classi quinquennali costruite dal dettaglio POSAS per singola età e sesso.</p></div></details>`;
  }

  function foreignOriginsListMarkup(title, items, note) {
    return `<section class="income-band-town-detail foreign-origin-section"><h4>${html(title)}</h4><div class="composite-town-detail">${(items||[]).map(item=>`<div><span>${html(item.label)}</span><b>${html(number0.format(item.count))}</b><small>${item.share === null || item.share === undefined ? '' : `${html(number1.format(item.share))}%`} ${html(note)}</small></div>`).join('')}</div></section>`;
  }

  function foreignOriginsMarkup(metric, source, scope = 'town') {
    const detail = source?.foreignOrigins || source;
    if (metric.meta.key !== 'foreignResidents' || !detail) return '';
    const title = scope === 'compare' ? 'Versilia · cittadinanze e paesi esteri di nascita' : 'Principali cittadinanze e paesi di nascita';
    const caption = scope === 'compare' ? `${html(String(detail.year))} · somma dei 7 comuni` : `${html(String(detail.year))} · Istat RCS`;
    return `<details class="detail-disclosure foreign-origins-detail ${scope === 'compare' ? 'compare-foreign-origins' : ''}"><summary><span>${html(title)}</span><small>${caption}</small></summary><div class="foreign-origin-body">${foreignOriginsListMarkup('Cittadinanze straniere più numerose',detail.citizenshipTop,'dei residenti stranieri')}${foreignOriginsListMarkup('Paesi esteri di nascita più frequenti',detail.birthCountryTop,'dei residenti nati all’estero')}</div><p class="aggregate-note foreign-origins-note">Cittadinanza e paese di nascita sono due distribuzioni separate: Istat RCS non pubblica il loro incrocio. Nel confronto Versilia i valori sono somme comunali riordinate sul totale.</p></details>`;
  }

  function foreignOriginsCompareMarkup(metric) {
    return foreignOriginsMarkup(metric, metric.aggregate?.foreignOrigins, 'compare');
  }

'''
    if 'function agePyramidTooltipMarkup(' in text:
        return text
    if anchor not in text:
        raise RuntimeError('Anchor helper OMI non trovato')
    return text.replace(anchor, helpers + anchor, 1)


def patch_app() -> None:
    text = APP.read_text(encoding='utf-8')
    text = patch_helpers(text)

    old_stock_town = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>`;'''
    new_stock_town = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>${foreignOriginsMarkup(metric,row,'town')}`;'''
    text = replace_once(text, old_stock_town, new_stock_town, 'RCS nella scheda comunale')

    old_detail_const = '''    const detailDisclosure = detailParts.length ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div class="composite-town-detail">${detailParts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></details>` : '';'''
    new_detail_const = old_detail_const + '''
    const agePyramidDisclosure = agePyramidMarkup(metric,row);'''
    text = replace_once(text, old_detail_const, new_detail_const, 'piramide nella scheda comunale')

    old_town_distribution_return = '''    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div></div>${detailDisclosure}`;'''
    new_town_distribution_return = '''    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div>${agePyramidDisclosure}</div>${detailDisclosure}`;'''
    text = replace_once(text, old_town_distribution_return, new_town_distribution_return, 'piramide nella distribuzione comunale')

    stock_compare_block = '''      bars.innerHTML = `<div class="topic-bars selectable-topic-bars"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${chartControls}</div><div class="comparison-bars" data-composite-choice="${html(view.choice)}" data-composite-scale="${html(view.scale)}">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${note}</div>`;'''
    stock_compare_with_rcs = '''      const stockDetail = compositeType === 'stock' ? foreignOriginsCompareMarkup(metric) : '';
      bars.innerHTML = `<div class="topic-bars selectable-topic-bars"><div class="compare-chart-toolbar"><div class="compare-chart-legend-host" aria-live="polite"></div>${chartControls}</div><div class="comparison-bars" data-composite-choice="${html(view.choice)}" data-composite-scale="${html(view.scale)}">${compositeCompareBarRows(data,metricKey,view.choice,view.scale)}</div>${note}${stockDetail}</div>`;'''
    text = replace_once(text, stock_compare_block, stock_compare_with_rcs, 'RCS aggregato nella superficie stock')

    APP.write_text(text, encoding='utf-8')


def patch_cache_version() -> None:
    text = BUILD.read_text(encoding='utf-8')
    text = replace_any(text, [
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v117"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v118"'),
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v116"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v118"'),
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v115"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v118"'),
        ('APP_BUNDLE_ASSET_VERSION = "20260820-v114"', 'APP_BUNDLE_ASSET_VERSION = "20260820-v118"'),
    ], 'cache bundle v118')
    BUILD.write_text(text, encoding='utf-8')

    text = BRAND_TEST.read_text(encoding='utf-8')
    text = replace_any(text, [
        ('assets/app-bundle.js?v=20260820-v117', 'assets/app-bundle.js?v=20260820-v118'),
        ('assets/app-bundle.js?v=20260820-v116', 'assets/app-bundle.js?v=20260820-v118'),
        ('assets/app-bundle.js?v=20260820-v115', 'assets/app-bundle.js?v=20260820-v118'),
        ('assets/app-bundle.js?v=20260820-v114', 'assets/app-bundle.js?v=20260820-v118'),
    ], 'test cache bundle v118')
    BRAND_TEST.write_text(text, encoding='utf-8')


def patch_css() -> None:
    marker = '/* PR81 Demografia Lotto A v2 coherence fixes */'
    text = ORIGINAL_CSS.read_text(encoding='utf-8')
    if marker in text:
        return
    css = r'''

/* PR81 Demografia Lotto A v2 coherence fixes */
.detail-disclosure{margin-top:16px;border:1px solid var(--line);border-radius:18px;background:#fffaf1cc;overflow:hidden;line-height:1.45}.detail-disclosure>summary{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:17px 19px;cursor:pointer}.detail-disclosure>summary span{font-weight:780;min-width:0;white-space:normal}.detail-disclosure>summary small{color:var(--muted);font-size:12px;line-height:1.35;text-align:right;white-space:normal}.detail-disclosure>.age-pyramid-body,.detail-disclosure>.foreign-origin-body{padding:0 19px 19px}.age-pyramid-body{overflow-x:auto}.age-pyramid-trend{min-width:720px;overflow:visible}.age-pyramid-chart{width:100%;height:auto;display:block;margin:0 auto;overflow:visible}.age-pyramid-title{font-size:14px;font-weight:800;fill:currentColor}.age-pyramid-unit{font-size:12px;fill:var(--muted)}.age-pyramid-axis line{stroke:currentColor;opacity:.12}.age-pyramid-axis text,.age-pyramid-row>text{font-size:11px;fill:var(--muted)}.age-pyramid-center{stroke:currentColor;opacity:.18}.age-pyramid-men{fill:var(--theme-color);opacity:.9}.age-pyramid-women{fill:var(--theme-color);opacity:.48}.age-pyramid-point{cursor:pointer;outline:none}.age-pyramid-point:focus .age-pyramid-men,.age-pyramid-point.active .age-pyramid-men,.age-pyramid-point:focus .age-pyramid-women,.age-pyramid-point.active .age-pyramid-women{opacity:1}.age-pyramid-note{margin:10px 0 0;white-space:normal}.foreign-origin-body{display:grid;gap:15px;min-width:0}.foreign-origin-section,.foreign-origin-section .composite-town-detail,.foreign-origin-section .composite-town-detail>div{min-width:0}.foreign-origin-section{margin:0}.foreign-origin-section .composite-town-detail{gap:10px}.foreign-origin-section .composite-town-detail>div{padding:14px 15px;line-height:1.42}.foreign-origin-section span,.foreign-origin-section small,.foreign-origins-detail summary span,.foreign-origins-note{white-space:normal;overflow-wrap:anywhere;word-break:normal}.foreign-origins-detail>.foreign-origins-note{box-sizing:border-box;width:auto;max-width:none;margin:0 19px 19px;padding:0;line-height:1.5;min-width:0}.foreign-origins-detail *{box-sizing:border-box}@media (max-width:760px){.detail-disclosure>summary{align-items:flex-start;flex-direction:column}.detail-disclosure>summary small{text-align:left}.age-pyramid-trend{min-width:640px}.foreign-origins-detail>.foreign-origins-note{margin:0 15px 15px}.detail-disclosure>.foreign-origin-body{padding:0 15px 15px}}
'''
    ORIGINAL_CSS.write_text(text + css, encoding='utf-8')


def main() -> None:
    patch_app()
    patch_css()
    patch_cache_version()
    print('Frontend Demografia v2 coerente: 85+ in distribuzione, piramide con tooltip nativo, RCS senza clipping; bundle v118.')


if __name__ == '__main__':
    main()
