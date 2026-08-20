#!/usr/bin/env python3
"""Validazione post-materializzazione del primo blocco Demografia Lotto A."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data/site-data.json').read_text(encoding='utf-8'))
REGISTRY = json.loads((ROOT / 'data/source-registry.json').read_text(encoding='utf-8'))
MONITOR = json.loads((ROOT / 'data/source-monitor-state.json').read_text(encoding='utf-8'))
AUDIT = json.loads((ROOT / 'data/data-audit-lotto-a.json').read_text(encoding='utf-8'))
SNAPSHOT = json.loads((ROOT / 'data/source-snapshots/istat-demography-lotto-a-2026-08.json').read_text(encoding='utf-8'))

EXPECTED_TOWNS = [
    'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta',
    'Seravezza', 'Stazzema', 'Viareggio'
]
NEW_KEYS = ['dependencyIndices', 'naturalDemographicDynamics']


def row_by_town(metric: dict) -> dict[str, dict]:
    return {row['town']: row for row in metric['rows']}


def assert_series(metric: dict, years: list[int]) -> None:
    rows = row_by_town(metric)
    assert set(rows) == set(EXPECTED_TOWNS), (metric['meta']['key'], sorted(rows))
    for town in EXPECTED_TOWNS:
        row = rows[town]
        assert row['series']['years'] == years, (metric['meta']['key'], town, row['series']['years'])
        assert len(row['series']['values']) == len(years)
        assert all(value is not None for value in row['series']['values'])
        assert row.get('componentSeries'), (metric['meta']['key'], town)


def main() -> None:
    assert SITE['version'] == 'v1.14.0'
    assert len(SITE['metrics']) == 129
    external = [
        key for key, metric in SITE['metrics'].items()
        if metric.get('dataStorage', {}).get('type') == 'external-climate'
    ]
    assert len(external) == 4, external
    assert REGISTRY['expectedMetricCount'] == 129
    assert REGISTRY['expectedInlineMetricCount'] == 125
    assert REGISTRY['expectedExternalMetricCount'] == 4

    for key in NEW_KEYS:
        assert key in SITE['metrics'], key
        metric = SITE['metrics'][key]
        assert metric['meta']['theme'] == 'demografia'
        # Il tipo interno è già gestito dal renderer multi-misura canonico.
        assert metric['meta']['compositeType'] == 'securityMeasures'
        assert metric['sourceUrl'] == 'https://demo.istat.it/'
        assert len(metric['rows']) == 7
        assert metric['method']['coverage'] == '7/7'

    natural = SITE['metrics']['naturalDemographicDynamics']
    assert natural['meta']['year'] == '2025'
    assert natural['meta']['unit'] == 'per1000'
    assert_series(natural, list(range(2019, 2026)))
    natural_labels = [part['label'] for part in natural['rows'][0]['parts']]
    assert natural_labels == ['Saldo naturale', 'Natalità', 'Mortalità']
    assert 'provvisorio' in natural['method']['caveat'].lower()

    dependency = SITE['metrics']['dependencyIndices']
    assert dependency['meta']['year'] == '2026'
    assert dependency['meta']['unit'] == 'index'
    assert_series(dependency, list(range(2019, 2027)))
    dep_labels = [part['label'] for part in dependency['rows'][0]['parts']]
    assert dep_labels == ['Indice di dipendenza strutturale', 'Indice di dipendenza degli anziani']

    # 80+ non deve diventare una nuova card: esiste già nel composito ageDistribution.
    assert 'share80Plus' not in SITE['metrics']
    age = SITE['metrics']['ageDistribution']
    age_labels = [part.get('selectorLabel') or part['label'] for part in age['rows'][0]['parts']]
    assert '80+' in age_labels

    demography = SITE['themes']['demografia']
    assert demography['metrics'].index('dependencyIndices') == demography['metrics'].index('oldAgeIndex') + 1
    dynamic_section = next(section for section in demography['sections'] if section['key'] == 'dinamica')
    assert dynamic_section['metrics'] == ['naturalDemographicDynamics', 'populationChange']

    demo_source = MONITOR['sources']['https://demo.istat.it/']
    for key in NEW_KEYS:
        assert key in demo_source['metrics']

    assert AUDIT['status'] == 'implementation_demography_draft'
    assert AUDIT['catalogMetricCountCurrentDraft'] == 129
    decisions = {candidate['key']: candidate.get('implementationStatus') for candidate in AUDIT['candidates']}
    assert decisions['share80Plus'] == 'covered_by_existing_ageDistribution'
    assert decisions['populationAgeSexDetail'] == 'snapshot_materialized_2026'

    # Snapshot: copertura completa, flag 2025 provvisorio e dettagli età×sesso 2026.
    assert set(SNAPSHOT['p02']['towns']) == set(EXPECTED_TOWNS)
    assert set(SNAPSHOT['posas']['towns']) == set(EXPECTED_TOWNS)
    assert set(SNAPSHOT['posas']['ageSex2026']) == set(EXPECTED_TOWNS)
    for town in EXPECTED_TOWNS:
        p2 = SNAPSHOT['p02']['towns'][town]
        assert [row['year'] for row in p2] == list(range(2019, 2026))
        assert p2[-1]['informationFlag'].lower() == 'p', (town, p2[-1]['informationFlag'])
        assert p2[-1]['naturalBalance'] == p2[-1]['births'] - p2[-1]['deaths']
        posas = SNAPSHOT['posas']['towns'][town]
        assert [row['year'] for row in posas] == list(range(2019, 2027))
        latest = posas[-1]
        assert latest['population'] == latest['age0to14'] + latest['age15to64'] + latest['age65plus']
        assert latest['age80plus'] <= latest['age65plus']
        assert len(SNAPSHOT['posas']['ageSex2026'][town]) >= 100

    # Controllo formula su un caso noto, senza hardcodare il valore pubblicato.
    massarosa = SNAPSHOT['p02']['towns']['Massarosa'][-1]
    expected_rate = massarosa['naturalBalance'] / massarosa['meanPopulation'] * 1000
    actual = row_by_town(natural)['Massarosa']['value']
    assert abs(actual - expected_rate) < 1e-8

    print(
        'Demografia Lotto A materializzata OK: 129 metriche, 7/7, '
        'P02 2019–2025 + POSAS 2019–2026, nessun duplicato 80+, UI canonica.'
    )


if __name__ == '__main__':
    main()
