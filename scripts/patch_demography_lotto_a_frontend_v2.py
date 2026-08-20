#!/usr/bin/env python3
"""Espone nel frontend canonico gli approfondimenti Demografia Lotto A v2.

Il patch viene eseguito DOPO `patch_income_lotto_a_frontend.py`, così preserva
anche il dettaglio Redditi a 8 fasce introdotto dalla #80.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'assets' / 'app-parts' / '03.txt'
BUILD = ROOT / 'scripts' / 'build_static_brand.py'
BRAND_TEST = ROOT / 'scripts' / 'test_brand_identity.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Anchor frontend non trovato: {label}')
    return text.replace(old, new, 1)


def patch_helpers(text: str) -> str:
    anchor = '''  function omiZoneTableMarkup(row, compact = false) {'''
    helpers = r'''  function ageSeniorTownMarkup(metric, row) {
    const detail = row?.seniorAgeDetail;
    if (metric.meta.key !== 'ageDistribution' || !detail) return '';
    const entries = [
      ['80 anni e oltre', detail.age80Plus],
      ['85 anni e oltre', detail.age85Plus]
    ];
    return `<details class="detail-disclosure age-senior-detail"><summary><span>${html(metric.meta.detailLabel || 'Grandi anziani · 80+ e 85+')}</span><small>${html(String(detail.year))} · Istat POSAS</small></summary><div class="composite-town-detail">${entries.map(([label,item],index)=>`<div><span><i class="composite-swatch part-${index+5}"></i>${html(label)}</span><b>${html(number1.format(item.value))}%</b><small>${html(number0.format(item.count))} residenti</small></div>`).join('')}</div></details>`;
  }

  function ageSeniorCompareMarkup(metric, rows) {
    if (metric.meta.key !== 'ageDistribution' || !rows.some(row => row.seniorAgeDetail)) return '';
    return `<details class="detail-disclosure age-senior-detail"><summary><span>${html(metric.meta.detailLabel || 'Grandi anziani · 80+ e 85+')}</span><small>${html(metric.meta.year)} · confronto tra i 7 comuni</small></summary><div>${rows.map(row=>{const d=row.seniorAgeDetail;return `<section class="income-band-town-detail"><h4>${html(row.town)}</h4><div class="composite-town-detail"><div><span>80 anni e oltre</span><b>${html(number1.format(d.age80Plus.value))}%</b><small>${html(number0.format(d.age80Plus.count))} residenti</small></div><div><span>85 anni e oltre</span><b>${html(number1.format(d.age85Plus.value))}%</b><small>${html(number0.format(d.age85Plus.count))} residenti</small></div></div></section>`;}).join('')}</div></details>`;
  }

  function agePyramidMarkup(metric, row) {
    const pyramid = row?.ageSexPyramid;
    if (metric.meta.key !== 'ageDistribution' || !pyramid?.displayBands?.length) return '';
    const bands = [...pyramid.displayBands].reverse();
    const max = Math.max(...bands.flatMap(item => [Number(item.men)||0, Number(item.women)||0]), 1);
    const center = 410, gap = 34, maxWidth = 300, rowHeight = 25, top = 54;
    const height = top + bands.length * rowHeight + 28;
    const rows = bands.map((item,index)=>{
      const y = top + index * rowHeight;
      const menWidth = (Number(item.men)||0) / max * maxWidth;
      const womenWidth = (Number(item.women)||0) / max * maxWidth;
      return `<g><rect x="${center-gap-menWidth}" y="${y}" width="${menWidth}" height="17" rx="3" style="fill:var(--theme);opacity:.88"><title>${html(item.label)} · uomini: ${html(number0.format(item.men))}</title></rect><rect x="${center+gap}" y="${y}" width="${womenWidth}" height="17" rx="3" style="fill:var(--theme);opacity:.48"><title>${html(item.label)} · donne: ${html(number0.format(item.women))}</title></rect><text x="${center}" y="${y+13}" text-anchor="middle" style="font-size:12px;fill:currentColor">${html(item.label)}</text></g>`;
    }).join('');
    return `<details class="detail-disclosure age-pyramid-detail"><summary><span>${html(metric.meta.pyramidLabel || 'Piramide per età e sesso')}</span><small>${html(String(pyramid.year))} · classi quinquennali da dati per singola età</small></summary><div><svg viewBox="0 0 820 ${height}" role="img" aria-label="Piramide per età e sesso di ${html(row.town)}" style="width:100%;height:auto;display:block;max-width:920px;margin:0 auto"><text x="210" y="28" text-anchor="middle" style="font-size:13px;font-weight:700;fill:currentColor">Uomini</text><text x="610" y="28" text-anchor="middle" style="font-size:13px;font-weight:700;fill:currentColor">Donne</text><line x1="376" y1="40" x2="376" y2="${height-10}" style="stroke:currentColor;opacity:.14"/><line x1="444" y1="40" x2="444" y2="${height-10}" style="stroke:currentColor;opacity:.14"/>${rows}</svg><p class="aggregate-note">La visualizzazione usa classi quinquennali per restare leggibile anche su mobile; i dati sorgente sono disponibili per singola età e sesso.</p></div></details>`;
  }

  function populationChangeComponentsMarkup(metric, row) {
    const detail = row?.changeComponents;
    if (metric.meta.key !== 'populationChange' || !detail?.parts?.length) return '';
    return `<section class="history-panel demographic-change-components"><div class="panel-title"><div><span class="overline">Come si compone il cambiamento</span><h3>${html(metric.meta.detailLabel || 'Componenti della variazione demografica')} · ${html(String(detail.year))}</h3></div></div><div class="composite-town-mobility">${detail.parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || 'per1000'))}</strong><small>${part.count === null || part.count === undefined ? 'conteggio n.d.' : `${html(number0.format(part.count))} persone`}</small></article>`).join('')}</div><p class="aggregate-note">${html(detail.note || '')}</p></section>`;
  }

  function foreignOriginsMarkup(metric, row) {
    const detail = row?.foreignOrigins;
    if (metric.meta.key !== 'foreignResidents' || !detail) return '';
    const list = (title, items, note) => `<section class="income-band-town-detail"><h4>${html(title)}</h4><div class="composite-town-detail">${(items||[]).map(item=>`<div><span>${html(item.label)}</span><b>${html(number0.format(item.count))}</b><small>${item.share === null || item.share === undefined ? '' : `${html(number1.format(item.share))}%`} ${html(note)}</small></div>`).join('')}</div></section>`;
    return `<details class="detail-disclosure foreign-origins-detail"><summary><span>Principali cittadinanze e paesi di nascita</span><small>${html(String(detail.year))} · Istat RCS</small></summary><div>${list('Cittadinanze straniere più numerose',detail.citizenshipTop,'dei residenti stranieri')}${list('Paesi esteri di nascita più frequenti',detail.birthCountryTop,'dei residenti nati all’estero')}</div><p class="aggregate-note">Cittadinanza e paese di nascita sono due distribuzioni separate: Istat non pubblica il loro incrocio nel dataset RCS.</p></details>`;
  }

'''
    if helpers in text:
        return text
    if anchor not in text:
        raise RuntimeError('Anchor helper OMI non trovato')
    return text.replace(anchor, helpers + anchor, 1)


def patch_app() -> None:
    text = APP.read_text(encoding='utf-8')
    text = patch_helpers(text)

    # Confronto ageDistribution: mantiene la distribuzione principale e aggiunge
    # un disclosure 80+/85+ accanto all'eventuale dettaglio Redditi.
    old = '''    return `${compositePartLegend(metric)}<div class="composite-distribution-list">'''
    new = '''    const ageSeniorDetail = ageSeniorCompareMarkup(metric, rows);
    return `${compositePartLegend(metric)}<div class="composite-distribution-list">'''
    text = replace_once(text, old, new, 'age senior compare const')
    text = replace_once(
        text,
        '''</div>${incomeBandDetail}`;''',
        '''</div>${incomeBandDetail}${ageSeniorDetail}`;''',
        'age senior compare append',
    )

    # Scheda comunale ageDistribution: quota 80+/85+ + piramide, senza nuove card.
    old = '''    const detailParts = metric.meta.key === 'incomeDistribution' ? (row.detailParts || []) : [];'''
    new = '''    const detailParts = metric.meta.key === 'incomeDistribution' ? (row.detailParts || []) : [];
    const ageSeniorDisclosure = ageSeniorTownMarkup(metric,row);
    const agePyramidDisclosure = agePyramidMarkup(metric,row);'''
    text = replace_once(text, old, new, 'age town disclosure const')
    text = replace_once(
        text,
        '''</div></div>${detailDisclosure}`;''',
        '''</div></div>${detailDisclosure}${ageSeniorDisclosure}${agePyramidDisclosure}`;''',
        'age town disclosure append',
    )

    # Residenti stranieri: il dettaglio RCS apparirà automaticamente quando la
    # materializzazione lo avrà popolato.
    old = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>`;'''
    new = '''      return `<div class="composite-town-mobility composite-town-stock"><article class="balance"><span>Quota dei residenti</span><strong>${html(formatValue(row.value,'percent'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Residenti di cittadinanza straniera</span><strong>${html(formatValue(row.count,'number'))}</strong><small>persone · ${html(metric.meta.year)}</small></article></div>${foreignOriginsMarkup(metric,row)}`;'''
    text = replace_once(text, old, new, 'foreign origins detail')

    # PopulationChange: rende leggibili insieme naturale, migrazione interna ed estero.
    old = '''      ${deepDiveMarkup(data, town, themeKey)}'''
    new = '''      ${populationChangeComponentsMarkup(metric,row)}
      ${deepDiveMarkup(data, town, themeKey)}'''
    text = replace_once(text, old, new, 'population change components')

    APP.write_text(text, encoding='utf-8')


def patch_cache_version() -> None:
    text = BUILD.read_text(encoding='utf-8')
    text = replace_once(
        text,
        'APP_BUNDLE_ASSET_VERSION = "20260820-v115"',
        'APP_BUNDLE_ASSET_VERSION = "20260820-v116"',
        'cache bundle v116',
    )
    BUILD.write_text(text, encoding='utf-8')

    text = BRAND_TEST.read_text(encoding='utf-8')
    text = replace_once(
        text,
        'assets/app-bundle.js?v=20260820-v115',
        'assets/app-bundle.js?v=20260820-v116',
        'test cache bundle v116',
    )
    BRAND_TEST.write_text(text, encoding='utf-8')


def main() -> None:
    patch_app()
    patch_cache_version()
    print('Frontend Demografia v2 applicato: 80+/85+, piramide, componenti variazione e hook RCS; bundle v116.')


if __name__ == '__main__':
    main()
