#!/usr/bin/env python3
"""Espone nel frontend canonico i dati Redditi Lotto A v2.

- per `incomeSourceProfile` mostra anche la frequenza dei dichiaranti per fonte;
- per `incomeDistribution` aggiunge un disclosure pubblico con le 8 fasce MEF
  sia nel confronto sia nelle schede comunali;
- il CSV della distribuzione usa le 8 fasce quando disponibili;
- incrementa il cache-busting del bundle applicativo.
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


def patch_app() -> None:
    text = APP.read_text(encoding='utf-8')

    old_compare = '''    return `${compositePartLegend(metric)}<div class="composite-distribution-list">${rows.map(row => {
      const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
      const parts = row.parts || [];
      const summary = compositeSummary(metric, row);
      return `<div class="composite-distribution-row">
        <div class="composite-row-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(summary.label)} <b>${html(summary.formatted)}</b></span></div>
        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;
    }).join('')}</div>`;'''
    new_compare = '''    const incomeBandDetail = metric.meta.key === 'incomeDistribution' && rows.some(row => row.detailParts?.length)
      ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div>${rows.map(row => `<section class="income-band-town-detail"><h4>${html(row.town)}</h4><div class="composite-town-detail">${(row.detailParts || []).map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></section>`).join('')}</div></details>`
      : '';
    return `${compositePartLegend(metric)}<div class="composite-distribution-list">${rows.map(row => {
      const query = new URLSearchParams({ tema: metric.meta.theme, indicatore: metricKey });
      const parts = row.parts || [];
      const summary = compositeSummary(metric, row);
      return `<div class="composite-distribution-row">
        <div class="composite-row-head"><a class="composite-town-link" href="${route(`comuni/${row.slug}/?${query}`)}">${html(row.town)}</a><span>${html(summary.label)} <b>${html(summary.formatted)}</b></span></div>
        ${compositeStackMarkup(parts,{ ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:6 })}
      </div>`;
    }).join('')}</div>${incomeBandDetail}`;'''
    text = replace_once(text, old_compare, new_compare, 'dettaglio fasce nel confronto')

    old_security = '''    if (metric.meta.compositeType === 'securityMeasures') {
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>`;
    }'''
    new_security = '''    if (metric.meta.compositeType === 'securityMeasures') {
      const incomeSources = metric.meta.key === 'incomeSourceProfile';
      return `<div class="composite-town-mobility">${parts.map((part,index)=>`<article class="${index===0?'balance':''}"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${incomeSources ? (part.count === null || part.count === undefined ? 'n.d. · dichiaranti con questa fonte' : `${html(number0.format(part.count))} dichiaranti con questa fonte`) : html(metric.meta.year)}</small></article>`).join('')}</div>`;
    }'''
    text = replace_once(text, old_security, new_security, 'frequenze fonti reddito')

    old_town_return = '''    const countLabel = metric.meta.key === 'incomeDistribution' ? 'dichiaranti' : 'residenti';
    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div></div>`;'''
    new_town_return = '''    const countLabel = metric.meta.key === 'incomeDistribution' ? 'dichiaranti' : 'residenti';
    const detailParts = metric.meta.key === 'incomeDistribution' ? (row.detailParts || []) : [];
    const detailDisclosure = detailParts.length ? `<details class="detail-disclosure income-bands-detail"><summary><span>${html(metric.meta.detailLabel || 'Dettaglio · 8 fasce MEF')}</span><small>${html(metric.meta.year)} · classi originali MEF</small></summary><div class="composite-town-detail">${detailParts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${part.value === null || part.value === undefined ? 'n.d.' : html(number1.format(part.value)) + '%'}</b><small>${part.count === null || part.count === undefined ? 'n.d.' : html(number0.format(part.count)) + ' dichiaranti'}</small></div>`).join('')}</div></details>` : '';
    return `<div class="composite-town-stack-shell">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}
      <div class="composite-town-detail">${parts.map((part,index)=>`<div><span><i class="composite-swatch part-${index}"></i>${html(part.label)}</span><b>${html(number1.format(part.value))}%</b><small>${html(number0.format(part.count))} ${html(countLabel)}</small></div>`).join('')}</div></div>${detailDisclosure}`;'''
    text = replace_once(text, old_town_return, new_town_return, 'dettaglio fasce nella scheda comunale')

    old_csv = '''    else if (metric.meta.compositeType) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, part.unit || metric.meta.unit, part.count, metric.sourceUrl])));'''
    new_csv = '''    else if (metric.meta.compositeType) rows.forEach(row => ((metric.meta.key === 'incomeDistribution' && row.detailParts?.length) ? row.detailParts : (row.parts || [])).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, part.unit || metric.meta.unit, part.count, metric.sourceUrl])));'''
    text = replace_once(text, old_csv, new_csv, 'CSV dettaglio fasce')

    APP.write_text(text, encoding='utf-8')


def patch_cache_version() -> None:
    text = BUILD.read_text(encoding='utf-8')
    text = replace_once(
        text,
        'APP_BUNDLE_ASSET_VERSION = "20260820-v114"',
        'APP_BUNDLE_ASSET_VERSION = "20260820-v115"',
        'cache bundle v115',
    )
    BUILD.write_text(text, encoding='utf-8')

    text = BRAND_TEST.read_text(encoding='utf-8')
    text = replace_once(
        text,
        'assets/app-bundle.js?v=20260820-v114',
        'assets/app-bundle.js?v=20260820-v115',
        'test cache bundle v115',
    )
    BRAND_TEST.write_text(text, encoding='utf-8')


def main() -> None:
    patch_app()
    patch_cache_version()
    print('Frontend Redditi Lotto A v2 applicato: fonti visibili, 8 fasce espandibili, CSV completo, bundle v115.')


if __name__ == '__main__':
    main()
