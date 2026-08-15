#!/usr/bin/env python3
"""Apply review corrections requested after visual QA of the cost/fiscality draft."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/site-data.json'
REGISTRY = ROOT / 'data/source-registry.json'
NIC = ROOT / 'data/source-snapshots/nic-italia-2016-2024.json'
APP02 = ROOT / 'assets/app-parts/02.txt'
APP03 = ROOT / 'assets/app-parts/03.txt'
APP05 = ROOT / 'assets/app-parts/05.txt'
VISUAL = ROOT / 'assets/visual-grammar.js'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def format_eur0(value):
    return f"{float(value):,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.') + '\u00a0€'


def fix_income(data):
    metric = data['metrics']['income']
    for current in metric['rows']:
        series = current.get('longSeries') or current.get('series')
        if not series or not series.get('years') or not series.get('values'):
            raise RuntimeError(f"Serie reddito mancante per {current.get('town')}")
        latest = float(series['values'][-1])
        current['value'] = latest
        current['formatted'] = format_eur0(latest)
        current['series'] = series
        current['longSeries'] = series
        current['benchmarkValue'] = latest

    long_aggregate = metric.get('longAggregate') or {}
    aggregate_values = long_aggregate.get('values') or []
    if not aggregate_values:
        raise RuntimeError('Aggregato reddito lungo mancante')

    metric['meta'].update({
        'label': 'Reddito imponibile medio per dichiarante',
        'shortLabel': 'Reddito imponibile medio',
        'description': 'Reddito imponibile dichiarato diviso per la relativa frequenza dei dichiaranti. La stessa definizione è usata nel valore corrente e nello storico.',
        'unit': 'currency',
        'year': '2024',
        'source': 'Dipartimento delle Finanze — MEF',
        'longHistoryLabel': 'Reddito imponibile medio · serie storica',
        'longHistoryYears': '2011–2024',
        'longHistoryNote': 'Valore corrente e storico usano la stessa definizione MEF: «Reddito imponibile — Ammontare / Frequenza».',
    })
    metric['aggregate'].update({
        'value': float(aggregate_values[-1]),
        'label': 'Media ponderata Versilia',
        'note': 'Ammontare complessivo / frequenza complessiva dei sette comuni.',
    })
    long_aggregate['label'] = 'Imponibile medio Versilia'
    long_aggregate['note'] = 'Ammontare complessivo / frequenza complessiva dei sette comuni.'
    metric['longAggregate'] = long_aggregate


def fix_imu(data):
    metric = data['metrics']['municipalImuStandard']
    rate_groups = {}
    for current in metric['rows']:
        parts = current.get('parts') or []
        if len(parts) < 2:
            raise RuntimeError(f"Componenti IMU mancanti per {current.get('town')}")
        tax = float(parts[0]['value'])
        rate = float(parts[1]['value'])
        rate_groups.setdefault(rate, []).append(current['town'])
        current['value'] = tax
        current['benchmarkValue'] = tax
        current['ratePercent'] = rate
        current['series'] = {'years': [metric['meta']['year']], 'values': [tax]}
        current.pop('parts', None)
        current.pop('componentSeries', None)

    aggregate_parts = metric.get('aggregate', {}).get('parts') or []
    if aggregate_parts:
        metric['aggregate']['value'] = float(aggregate_parts[0]['value'])
    metric['aggregate'].pop('parts', None)

    rate_note = '; '.join(
        f"{rate:.2f}%".replace('.', ',') + f": {', '.join(towns)}"
        for rate, towns in sorted(rate_groups.items())
    )
    metric['meta'].pop('compositeType', None)
    metric['meta'].pop('selectorLabel', None)
    metric['meta']['description'] = (
        'Imposta annua teorica su una seconda abitazione A/2 con base imponibile IMU identica di 100.000 €, '
        f'usando l’aliquota 2025 «Altri fabbricati». Aliquote applicate: {rate_note}.'
    )
    metric['method']['caveat'] = (
        'La base imponibile è standardizzata per isolare l’effetto dell’aliquota comunale. '
        f'{rate_note}.'
    )


def fix_inflation(data, registry):
    nic = load(NIC)
    current = data.get('incomeInflationContext') or {}
    context = dict(nic['incomeInflationContext'])
    context['incomeSourceUrl'] = current.get('incomeSourceUrl') or data['metrics']['income'].get('sourceUrl')
    context['priceSourceUrl'] = nic['sourceUrl']
    context['priceSource'] = nic['source']
    data['incomeInflationContext'] = context

    profiles = registry.setdefault('sourceProfiles', {})
    profiles['istat-nic-national-annual'] = {
        'publisher': 'ISTAT',
        'frequency': 'annual',
        'frequencyLabel': 'Annuale',
        'expectedRelease': 'Con i dati definitivi di dicembre',
        'acquisitionMethod': 'Variazioni medie annue NIC nazionale, indice generale; ricostruzione indicizzata con base 2016=100.',
        'licenseName': 'Fonte ufficiale ISTAT',
        'licenseUrl': nic['sourceUrl'],
    }
    registry.setdefault('sourceProfileByUrl', {})[nic['sourceUrl']] = 'istat-nic-national-annual'


def patch_catalog_link():
    text = APP02.read_text(encoding='utf-8')
    if 'metric-context-jump' in text:
        return
    old = '''      <div class="metric-group-buttons">${section.metrics.map(key => { const meta = data.metrics[key].meta; const label = labelCounts[meta.shortLabel] > 1 ? meta.label : meta.shortLabel; return `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(label)}</button>`; }).join('')}</div>'''
    new = '''      <div class="metric-group-buttons">${section.metrics.map(key => { const meta = data.metrics[key].meta; const label = labelCounts[meta.shortLabel] > 1 ? meta.label : meta.shortLabel; return `<button type="button" role="tab" data-metric="${key}" class="${key === metricKey ? 'active' : ''}" aria-selected="${key === metricKey}" tabindex="${key === metricKey ? '0' : '-1'}">${html(label)}</button>`; }).join('')}${themeKey === 'economia' && section.key === 'redditi' ? `<a class="button-link metric-context-jump" href="#redditi-prezzi">Redditi vs inflazione <span>↓</span></a>` : ''}</div>'''
    if old not in text:
        raise RuntimeError('Catalogo indicatori: anchor non trovato')
    APP02.write_text(text.replace(old, new, 1), encoding='utf-8')


def reposition_inflation_context():
    text = APP03.read_text(encoding='utf-8')
    line = "      ${themeKey === 'economia' ? incomeInflationMarkup(data) : ''}\n"
    text = text.replace(line, '')
    anchor = '      <section class="topic-dashboard page-width" data-theme="${themeKey}"><aside class="topic-controls">${metricControls(data, themeKey, metricKey, true)}<div id="compare-definition"></div></aside><div id="compare-bars"></div></section>\n'
    if anchor not in text:
        raise RuntimeError('Dashboard economia: anchor non trovato')
    APP03.write_text(text.replace(anchor, anchor + line, 1), encoding='utf-8')


def patch_inflation_copy():
    text = APP05.read_text(encoding='utf-8')
    replacements = {
        '<h2>Quanto della crescita dei redditi resta dopo l’inflazione?</h2>': '<h2>Redditi vs inflazione</h2>',
        'Confronto tra imponibile medio dichiarato nei sette comuni e NIC della Toscana, entrambi riportati a': 'Confronto tra reddito imponibile medio dei sette comuni e NIC nazionale ISTAT, entrambi riportati a',
        '<span>Prezzi NIC Toscana</span>': '<span>Prezzi NIC Italia</span>',
        'Fonte prezzi · Toscana/Istat ↗': 'Fonte prezzi · ISTAT ↗',
        'Il NIC è regionale <strong>Toscana</strong>: non è il dato della Provincia di Lucca né quello del Comune di Lucca. “A prezzi costanti” è un’elaborazione sull’imponibile medio, non sul reddito disponibile delle famiglie.': 'Il NIC nazionale misura l’andamento medio dei prezzi in Italia. Il reddito è invece calcolato sui sette Comuni della Versilia: il grafico è un confronto di contesto, non un’identità territoriale.',
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
    if 'NIC nazionale ISTAT' not in text:
        raise RuntimeError('Copy redditi vs inflazione non aggiornato')
    APP05.write_text(text, encoding='utf-8')


def patch_axis_units():
    text = VISUAL.read_text(encoding='utf-8')
    old_alias = "    if (token === 'currency' || token === 'eur' || token === '€' || token === '€/ab.') return 'currency';"
    new_alias = "    if (token === 'currency' || token === 'currency2' || token === 'eur' || token === '€') return 'currency';\n    if (token === 'eurliter' || token === '€/l') return 'eurliter';\n    if (token === 'eurperresident' || token === '€/ab' || token === '€/ab.') return 'eurperresident';"
    if "token === 'currency2'" not in text:
        if old_alias not in text:
            raise RuntimeError('Alias unità visual grammar non trovato')
        text = text.replace(old_alias, new_alias, 1)

    old_format = "    if (kind === 'rentm2') return `${formatted} €/m²/mese`;\n    return kind === 'count' ? formatted : (unit ? `${formatted} ${unit}` : formatted);"
    new_format = "    if (kind === 'rentm2') return `${formatted} €/m²/mese`;\n    if (kind === 'eurliter') return `${formatted} €/l`;\n    if (kind === 'eurperresident') return `${formatted} €/ab`;\n    return kind === 'count' ? formatted : (unit ? `${formatted} ${unit}` : formatted);"
    if "kind === 'eurliter'" not in text:
        if old_format not in text:
            raise RuntimeError('Formato assi visual grammar non trovato')
        text = text.replace(old_format, new_format, 1)
    VISUAL.write_text(text, encoding='utf-8')


def main():
    data = load(DATA)
    registry = load(REGISTRY)
    fix_income(data)
    fix_imu(data)
    fix_inflation(data, registry)
    data['costsFiscalDraft']['note'] = (
        'Revisione visuale applicata: unità assi leggibili, IMU senza selettore aliquota, '
        'reddito corrente e storico omogenei, confronto redditi-inflazione su NIC nazionale ISTAT.'
    )
    save(DATA, data)
    save(REGISTRY, registry)
    patch_catalog_link()
    reposition_inflation_context()
    patch_inflation_copy()
    patch_axis_units()
    print('Review corrections applied: units, IMU, income consistency, NIC Italia, context visibility')


if __name__ == '__main__':
    main()
