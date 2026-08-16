#!/usr/bin/env python3
"""Second visual/data QA pass for the cost/fiscality draft.

- keeps taxable income and total income clearly distinct;
- turns income vs inflation into a normal municipal indicator;
- removes the ad-hoc aggregate context jump;
- updates source-registry counts after the derived indicator is added.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/site-data.json'
REGISTRY = ROOT / 'data/source-registry.json'
APP02 = ROOT / 'assets/app-parts/02.txt'
APP03 = ROOT / 'assets/app-parts/03.txt'

KEY = 'incomeVsInflation'
EXTERNAL_METRICS = 4


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def add_after(items: list[str], key: str, anchor: str):
    if key in items:
        return
    if anchor in items:
        items.insert(items.index(anchor) + 1, key)
    else:
        items.append(key)


def clarify_income_definitions(data: dict):
    income = data['metrics']['income']
    distribution = data['metrics']['incomeDistribution']

    income['meta']['description'] = (
        'Reddito imponibile dichiarato diviso per la relativa frequenza dei dichiaranti. '
        'È una variabile MEF diversa dal «Reddito complessivo medio dichiarato» mostrato nella distribuzione per fasce: '
        'i due valori non devono coincidere. Qui si usa l’imponibile perché consente una serie comunale omogenea 2011–2024.'
    )
    income['meta']['longHistoryNote'] = (
        'Valore corrente e storico usano la stessa definizione MEF: «Reddito imponibile — Ammontare / Frequenza». '
        'Il «Reddito complessivo medio dichiarato» della distribuzione per fasce è una misura diversa e non viene mescolata a questa serie.'
    )

    distribution['meta']['summaryLabel'] = 'Reddito complessivo medio dichiarato'
    distribution['meta']['description'] = (
        'Distribuzione dei dichiaranti in quattro fasce esclusive ricavate dalle classi ufficiali MEF. '
        'Il dato riepilogativo «Reddito complessivo medio dichiarato» è distinto dal reddito imponibile medio: '
        'sono due variabili MEF diverse e quindi possono avere valori differenti.'
    )
    aggregate = distribution.setdefault('aggregate', {})
    aggregate['summaryLabel'] = 'Reddito complessivo medio Versilia'
    aggregate['summaryNote'] = (
        'Media ponderata del reddito complessivo dichiarato. È distinta dalla serie del reddito imponibile medio.'
    )


def income_vs_inflation_metric(data: dict) -> dict:
    income = data['metrics']['income']
    context = data.get('incomeInflationContext') or {}
    years = [int(year) for year in context.get('years', [])]
    prices = [float(value) for value in context.get('priceIndex', [])]
    if not years or len(years) != len(prices) or years[0] != 2016:
        raise RuntimeError('Contesto NIC Italia 2016–2024 mancante o incoerente')

    rows = []
    for current in income['rows']:
        series = current.get('longSeries') or current.get('series') or {}
        series_map = {int(year): float(value) for year, value in zip(series.get('years', []), series.get('values', [])) if value is not None}
        missing = [year for year in years if year not in series_map]
        if missing:
            raise RuntimeError(f"Reddito imponibile incompleto per {current['town']}: {missing}")
        base = series_map[years[0]]
        if base <= 0:
            raise RuntimeError(f"Base reddito non valida per {current['town']}")
        real_changes = []
        for year, price_index in zip(years, prices):
            nominal_index = series_map[year] / base * 100.0
            real_index = nominal_index / price_index * 100.0
            real_changes.append(round(real_index - 100.0, 4))
        value = real_changes[-1]
        rows.append({
            'town': current['town'],
            'code': current['code'],
            'slug': current['slug'],
            'value': value,
            'formatted': '',
            'series': {'years': years, 'values': real_changes},
            'normalized': None,
            'benchmarkValue': value,
        })

    aggregate_value = float(context.get('realGrowthPercent', 0.0))
    return {
        'meta': {
            'key': KEY,
            'theme': 'economia',
            'label': 'Redditi vs inflazione',
            'shortLabel': 'Redditi vs inflazione',
            'description': (
                'Variazione cumulata del reddito imponibile medio per dichiarante rispetto al 2016, '
                'depurata dall’andamento del NIC nazionale ISTAT. 0% indica lo stesso livello reale del 2016; '
                'un valore positivo indica crescita oltre l’inflazione. Il reddito è comunale, il riferimento dei prezzi è nazionale.'
            ),
            'unit': 'percent',
            'year': '2024',
            'source': 'MEF + ISTAT',
            'polarity': 'neutral',
            'searchTerms': ['redditi inflazione', 'potere acquisto', 'reddito reale', 'nic', 'prezzi'],
        },
        'sourceUrl': context.get('incomeSourceUrl') or income.get('sourceUrl'),
        'secondarySourceUrl': context.get('priceSourceUrl'),
        'rows': rows,
        'aggregate': {
            'value': aggregate_value,
            'label': 'Versilia · variazione reale 2016–2024',
            'note': 'Ammontare/frequenza dei sette Comuni, depurato con il NIC nazionale ISTAT; confronto di contesto tra perimetri diversi.',
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su MEF e ISTAT',
            'formula': '[(imponibile medio anno / imponibile medio 2016) / (NIC Italia anno / NIC Italia 2016) − 1] × 100.',
            'caveat': (
                'Il reddito riguarda ciascun Comune; l’inflazione è il NIC nazionale. '
                'L’indicatore misura l’evoluzione reale del reddito imponibile medio dichiarato, non il reddito disponibile familiare.'
            ),
            'coverage': '7/7 · 2016–2024',
            'sources': [context.get('incomeSourceUrl'), context.get('priceSourceUrl')],
        },
    }


def integrate_metric(data: dict):
    data['metrics'][KEY] = income_vs_inflation_metric(data)
    economy = data['themes']['economia']
    add_after(economy['metrics'], KEY, 'incomeDistribution')
    income_section = next(section for section in economy['sections'] if section.get('key') == 'redditi')
    add_after(income_section['metrics'], KEY, 'incomeDistribution')
    income_section['description'] = (
        'Reddito imponibile, distribuzione dei redditi dichiarati e confronto comunale con l’inflazione.'
    )

    draft = data.setdefault('costsFiscalDraft', {})
    published = draft.setdefault('publishedInDraft', [])
    if KEY not in published:
        published.append(KEY)
    draft['contextViews'] = [item for item in draft.get('contextViews', []) if item != 'incomeInflationContext']
    draft['note'] = (
        'Seconda revisione QA: reddito imponibile e reddito complessivo distinti esplicitamente; '
        'redditi vs inflazione trasformato in indicatore comunale; carburanti con precisione e scala dedicate.'
    )


def update_registry(data: dict, registry: dict):
    total = len(data['metrics'])
    registry['expectedMetricCount'] = total
    registry['expectedInlineMetricCount'] = total - EXTERNAL_METRICS
    registry['expectedExternalMetricCount'] = EXTERNAL_METRICS
    profiles = registry.setdefault('sourceProfiles', {})
    profiles['mef-istat-real-income-annual'] = {
        'publisher': 'Dipartimento delle Finanze — MEF / ISTAT',
        'frequency': 'annual',
        'frequencyLabel': 'Annuale',
        'expectedRelease': 'Dopo la disponibilità delle dichiarazioni fiscali e della media annua NIC',
        'acquisitionMethod': 'Reddito imponibile medio comunale MEF deflazionato con NIC nazionale ISTAT, base 2016.',
        'licenseName': 'Condizioni indicate dalle fonti ufficiali',
        'licenseUrl': data['metrics'][KEY].get('secondarySourceUrl') or data['metrics'][KEY].get('sourceUrl'),
    }
    registry.setdefault('metricOverrides', {})[KEY] = {'profile': 'mef-istat-real-income-annual'}


def remove_legacy_context_ui():
    app02 = APP02.read_text(encoding='utf-8')
    legacy = "${themeKey === 'economia' && section.key === 'redditi' ? `<a class=\"button-link metric-context-jump\" href=\"#redditi-prezzi\">Redditi vs inflazione <span>↓</span></a>` : ''}"
    app02 = app02.replace(legacy, '')
    APP02.write_text(app02, encoding='utf-8')

    app03 = APP03.read_text(encoding='utf-8')
    line = "      ${themeKey === 'economia' ? incomeInflationMarkup(data) : ''}\n"
    app03 = app03.replace(line, '')
    APP03.write_text(app03, encoding='utf-8')


def main():
    data = load(DATA)
    registry = load(REGISTRY)
    clarify_income_definitions(data)
    integrate_metric(data)
    update_registry(data, registry)
    save(DATA, data)
    save(REGISTRY, registry)
    remove_legacy_context_ui()
    print(f'Second QA pass applied: {len(data["metrics"])} metrics; income distinction explicit; municipal income-vs-inflation enabled')


if __name__ == '__main__':
    main()
