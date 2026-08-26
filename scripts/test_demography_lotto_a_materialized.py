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
HISTORY_CORE = (ROOT / 'assets/ux-history-core.js').read_text(encoding='utf-8')

EXPECTED_TOWNS = [
    'Camaiore', 'Forte dei Marmi', 'Massarosa', 'Pietrasanta',
    'Seravezza', 'Stazzema', 'Viareggio'
]
NEW_KEYS = ['dependencyIndices', 'naturalDemographicDynamics']


def row_by_town(metric: dict) -> dict[str, dict]:
    return {row['town']: row for row in metric['rows']}


def series_map(metric: dict, town: str) -> dict[int, float]:
    row = row_by_town(metric)[town]
    return dict(zip(row['series']['years'], row['series']['values'], strict=True))


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
    # Il lotto Demografia resta invariato: questo gate segue però il contratto
    # globale corrente della release, che ora comprende anche Welfare.
    assert SITE['version'] == 'v1.19.0'
    assert len(SITE['metrics']) == 149
    external = [
        key for key, metric in SITE['metrics'].items()
        if metric.get('dataStorage', {}).get('type') == 'external-climate'
    ]
    assert len(external) == 4, external
    assert REGISTRY['expectedMetricCount'] == 149
    assert REGISTRY['expectedInlineMetricCount'] == 145
    assert REGISTRY['expectedExternalMetricCount'] == 4

    for key in NEW_KEYS:
        assert key in SITE['metrics'], key
        metric = SITE['metrics'][key]
        assert metric['meta']['theme'] == 'demografia'
        assert metric['meta']['compositeType'] == 'securityMeasures'
        assert metric['sourceUrl'] == 'https://demo.istat.it/'
        assert len(metric['rows']) == 7
        assert metric['method']['coverage'] == '7/7'

    natural = SITE['metrics']['naturalDemographicDynamics']
    assert natural['meta']['year'] == '2025'
    assert natural['meta']['unit'] == 'per1000'
    assert_series(natural, list(range(2019, 2026)))
    assert [part['label'] for part in natural['rows'][0]['parts']] == [
        'Saldo naturale', 'Natalità', 'Mortalità'
    ]
    assert 'provvisorio' in natural['method']['caveat'].lower()

    dependency = SITE['metrics']['dependencyIndices']
    assert dependency['meta']['year'] == '2026'
    assert dependency['meta']['unit'] == 'per100'
    assert 'ogni 100 persone' in dependency['meta']['description']
    assert '15 e 64 anni' in dependency['meta']['description']
    assert 'non è una percentuale della popolazione totale' in dependency['method']['caveat'].lower()
    assert_series(dependency, list(range(2019, 2027)))
    assert [part['label'] for part in dependency['rows'][0]['parts']] == [
        'Indice di dipendenza strutturale', 'Indice di dipendenza degli anziani'
    ]
    for row in dependency['rows']:
        assert row['formatted'].endswith(' ogni 100')
        assert all(part['unit'] == 'per100' for part in row['parts'])
    assert all(part['unit'] == 'per100' for part in dependency['aggregate']['parts'])

    # Il renderer storico canonico deve riservare più spazio alle unità testuali lunghe:
    # la correzione vale quindi sia nel confronto sia nelle pagine dei Comuni.
    assert "['per100','per1000','per10k','per100k'].includes(metric.meta.unit) ? 132 : 78" in HISTORY_CORE

    # 80+ non deve diventare una nuova card: il composito espone 80–84 e 85+.
    assert 'share80Plus' not in SITE['metrics']
    age = SITE['metrics']['ageDistribution']
    age_labels = [part.get('selectorLabel') or part['label'] for part in age['rows'][0]['parts']]
    assert '80–84' in age_labels and '85+' in age_labels

    demography = SITE['themes']['demografia']
    assert demography['metrics'].index('dependencyIndices') == demography['metrics'].index('oldAgeIndex') + 1
    dynamic_section = next(section for section in demography['sections'] if section['key'] == 'dinamica')
    assert dynamic_section['metrics'] == ['naturalDemographicDynamics', 'populationChange']

    demo_source = MONITOR['sources']['https://demo.istat.it/']
    for key in NEW_KEYS:
        assert key in demo_source['metrics']

    assert AUDIT['catalogMetricCountAtAuditStart'] == 127
    decisions = {candidate['key']: candidate.get('implementationStatus') for candidate in AUDIT['candidates']}
    assert decisions['share80Plus'] == 'public_distribution_split_80_84_85_plus_2026'
    assert decisions['populationAgeSexDetail'] == 'public_pyramid_2026_towns_and_versilia'
    dependency_audit = next(candidate for candidate in AUDIT['candidates'] if candidate['key'] == 'dependencyIndices')
    assert dependency_audit['unit'] == 'per100'
    assert '15–64' in dependency_audit['unitExplanation']

    # Snapshot: copertura completa, P02 provvisorio 2025 e POSAS senza riga totale 999.
    assert set(SNAPSHOT['p02']['towns']) == set(EXPECTED_TOWNS)
    assert set(SNAPSHOT['posas']['towns']) == set(EXPECTED_TOWNS)
    assert set(SNAPSHOT['posas']['ageSex2026']) == set(EXPECTED_TOWNS)
    population = SITE['metrics']['population']
    old_age = SITE['metrics']['oldAgeIndex']

    for town in EXPECTED_TOWNS:
        p2 = SNAPSHOT['p02']['towns'][town]
        assert [row['year'] for row in p2] == list(range(2019, 2026))
        assert p2[-1]['informationFlag'].lower() == 'p', (town, p2[-1]['informationFlag'])
        assert p2[-1]['naturalBalance'] == p2[-1]['births'] - p2[-1]['deaths']

        posas = SNAPSHOT['posas']['towns'][town]
        assert [row['year'] for row in posas] == list(range(2019, 2027))
        canonical_population = series_map(population, town)
        canonical_old_age = series_map(old_age, town)
        for row in posas:
            year = row['year']
            assert row['population'] == row['age0to14'] + row['age15to64'] + row['age65plus']
            assert row['age80plus'] <= row['age65plus']
            # Il nuovo parsing per età deve riprodurre esattamente la popolazione già canonica.
            assert row['population'] == canonical_population[year], (
                town, year, row['population'], canonical_population[year]
            )
            # E deve ricostruire l'indice di vecchiaia già pubblicato entro l'arrotondamento a 1 decimale.
            reconstructed_old_age = row['age65plus'] / row['age0to14'] * 100
            assert abs(reconstructed_old_age - canonical_old_age[year]) <= 0.11, (
                town, year, reconstructed_old_age, canonical_old_age[year]
            )

        detail = SNAPSHOT['posas']['ageSex2026'][town]
        assert len(detail) >= 100
        assert all(0 <= item['age'] <= 120 for item in detail)
        assert 999 not in {item['age'] for item in detail}
        assert sum(item['total'] for item in detail) == posas[-1]['population']

    # Controllo formula su un caso noto, senza hardcodare il valore pubblicato.
    massarosa = SNAPSHOT['p02']['towns']['Massarosa'][-1]
    expected_rate = massarosa['naturalBalance'] / massarosa['meanPopulation'] * 1000
    actual = row_by_town(natural)['Massarosa']['value']
    assert abs(actual - expected_rate) < 1e-8

    print(
        'Demografia Lotto A materializzata OK: catalogo v1.19 con 149 metriche, 7/7, '
        'P02 2019–2025 + POSAS 2019–2026, dipendenza leggibile ogni 100 persone 15–64, '
        'assi storici con margine per unità lunghe, nessun duplicato 80+, UI canonica.'
    )


if __name__ == '__main__':
    main()
