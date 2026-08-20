#!/usr/bin/env python3
"""Completa gli approfondimenti Demografia Lotto A senza creare nuove card.

Prerequisito: `materialize_demography_lotto_a_v4.py` deve avere già creato lo
snapshot POSAS/P02 e i compositi demografici.

Questa fase:
- riallinea `ageDistribution` al POSAS 2026;
- aggiunge quota 80+ e 85+ come dettaglio leggibile;
- prepara una piramide per età e sesso in classi quinquennali, derivata dal
  dettaglio per singola età già acquisito;
- collega a `populationChange` una lettura unificata delle componenti naturale,
  migrazione interna e migrazione con l'estero sul 2024, ultimo anno comune.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'istat-demography-lotto-a-2026-08.json'

AGE_BANDS = [
    ('0–14 anni', '0–14', 0, 14),
    ('15–19 anni', '15–19', 15, 19),
    ('20–34 anni', '20–34', 20, 34),
    ('35–49 anni', '35–49', 35, 49),
    ('50–64 anni', '50–64', 50, 64),
    ('65–79 anni', '65–79', 65, 79),
    ('80 anni e oltre', '80+', 80, 120),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def percent(value: float) -> str:
    return f'{value:.1f}'.replace('.', ',') + '%'


def age_rows(snapshot: dict, town: str) -> list[dict]:
    rows = snapshot['posas']['ageSex2026'][town]
    return sorted(rows, key=lambda item: int(item['age']))


def build_pyramid(rows: list[dict]) -> list[dict]:
    groups = []
    start = 0
    while start <= 95:
        end = start + 4
        members = [row for row in rows if start <= int(row['age']) <= end]
        groups.append({
            'label': f'{start}–{end}',
            'ageStart': start,
            'ageEnd': end,
            'men': sum(int(row['men']) for row in members),
            'women': sum(int(row['women']) for row in members),
        })
        start += 5
    members = [row for row in rows if int(row['age']) >= 100]
    groups.append({
        'label': '100+',
        'ageStart': 100,
        'ageEnd': 120,
        'men': sum(int(row['men']) for row in members),
        'women': sum(int(row['women']) for row in members),
    })
    return groups


def update_age_distribution(site: dict, snapshot: dict) -> None:
    metric = site['metrics']['ageDistribution']
    total_counts = [0] * len(AGE_BANDS)
    total_population = 0
    weighted_age = 0
    total_80 = 0
    total_85 = 0

    for row in metric['rows']:
        detail = age_rows(snapshot, row['town'])
        total = sum(int(item['total']) for item in detail)
        if total <= 0:
            raise RuntimeError(f"{row['town']}: popolazione POSAS 2026 non valida")
        parts = []
        for idx, (label, selector, lower, upper) in enumerate(AGE_BANDS):
            count = sum(int(item['total']) for item in detail if lower <= int(item['age']) <= upper)
            total_counts[idx] += count
            parts.append({
                'label': label,
                'selectorLabel': selector,
                'value': count / total * 100,
                'count': count,
            })
        count80 = sum(int(item['total']) for item in detail if int(item['age']) >= 80)
        count85 = sum(int(item['total']) for item in detail if int(item['age']) >= 85)
        age_mean = sum(int(item['age']) * int(item['total']) for item in detail) / total
        total_population += total
        weighted_age += age_mean * total
        total_80 += count80
        total_85 += count85

        row['parts'] = parts
        # Manteniamo il 20–34 come valore canonico di riga per compatibilità con
        # il renderer esistente; la distribuzione resta il contenuto principale.
        row['value'] = parts[2]['value']
        row['formatted'] = percent(row['value'])
        row['benchmarkValue'] = row['value']
        row['summaryValue'] = age_mean
        row['seniorAgeDetail'] = {
            'year': 2026,
            'population': total,
            'age80Plus': {'count': count80, 'value': count80 / total * 100},
            'age85Plus': {'count': count85, 'value': count85 / total * 100},
        }
        row['ageSexPyramid'] = {
            'year': 2026,
            'sourceGranularity': 'singola età e sesso',
            'displayBands': build_pyramid(detail),
        }

    metric['meta']['year'] = '2026'
    metric['meta']['description'] = (
        'Quota dei residenti nelle fasce 0–14, 15–19, 20–34, 35–49, 50–64, 65–79 e 80 anni e oltre. '
        'L’approfondimento mostra anche la quota 85+ e, nelle schede comunali, la piramide per età e sesso.'
    )
    metric['meta']['detailLabel'] = 'Grandi anziani · 80+ e 85+'
    metric['meta']['pyramidLabel'] = 'Piramide per età e sesso'
    metric.setdefault('method', {})['detail'] = (
        'Distribuzione, 80+, 85+ e piramide derivano dal POSAS Istat al 1° gennaio 2026. '
        'La piramide visualizza classi quinquennali per leggibilità, mantenendo nello snapshot il dato per singola età e sesso.'
    )
    metric['aggregate'] = {
        'value': total_counts[2] / total_population * 100,
        'label': 'Versilia · 20–34 anni',
        'note': 'Quota calcolata sul totale dei residenti dei sette comuni; nel dettaglio sono mostrate tutte le fasce.',
        'parts': [
            {'label': label, 'count': total_counts[idx], 'value': total_counts[idx] / total_population * 100}
            for idx, (label, _selector, _lower, _upper) in enumerate(AGE_BANDS)
        ],
        'summaryValue': weighted_age / total_population,
        'summaryLabel': 'Età media Versilia',
        'summaryNote': 'Età media ponderata sulla popolazione dei sette comuni; la barra mostra la distribuzione completa per fascia.',
        'seniorAgeDetail': {
            'year': 2026,
            'population': total_population,
            'age80Plus': {'count': total_80, 'value': total_80 / total_population * 100},
            'age85Plus': {'count': total_85, 'value': total_85 / total_population * 100},
        },
    }


def component_series(metric: dict, town: str, label: str | None = None) -> dict[int, float]:
    row = next(item for item in metric['rows'] if item['town'] == town)
    series = row['componentSeries'][label] if label else row['series']
    return {int(year): float(value) for year, value in zip(series['years'], series['values'], strict=True)}


def component_count(metric: dict, town: str, label: str) -> int | None:
    row = next(item for item in metric['rows'] if item['town'] == town)
    part = next((item for item in row.get('parts', []) if item.get('label') == label), None)
    return None if part is None else part.get('count')


def update_population_change_components(site: dict, snapshot: dict) -> None:
    natural = site['metrics']['naturalDemographicDynamics']
    internal = site['metrics']['internalResidentialMobility']
    foreign = site['metrics']['foreignResidentialMobility']
    target = site['metrics']['populationChange']
    common_years = list(range(2019, 2025))

    for row in target['rows']:
        town = row['town']
        natural_map = component_series(natural, town, 'Saldo naturale')
        internal_map = component_series(internal, town)
        foreign_map = component_series(foreign, town)
        if not all(year in natural_map and year in internal_map and year in foreign_map for year in common_years):
            raise RuntimeError(f'{town}: serie componenti non omogenea 2019–2024')
        p2_2024 = next(item for item in snapshot['p02']['towns'][town] if int(item['year']) == 2024)
        parts = [
            {
                'key': 'natural',
                'label': 'Saldo naturale',
                'value': natural_map[2024],
                'unit': 'per1000',
                'count': int(p2_2024['naturalBalance']),
            },
            {
                'key': 'internal',
                'label': 'Saldo migratorio interno',
                'value': internal_map[2024],
                'unit': 'per1000',
                'count': component_count(internal, town, 'Saldo migratorio interno'),
            },
            {
                'key': 'foreign',
                'label': 'Saldo migratorio con l’estero',
                'value': foreign_map[2024],
                'unit': 'per1000',
                'count': component_count(foreign, town, 'Saldo migratorio con l’estero'),
            },
        ]
        row['changeComponents'] = {
            'year': 2024,
            'parts': parts,
            'series': {
                'years': common_years,
                'natural': [natural_map[year] for year in common_years],
                'internal': [internal_map[year] for year in common_years],
                'foreign': [foreign_map[year] for year in common_years],
            },
            'note': (
                'Le tre componenti sono mostrate sul 2024, ultimo anno comune alle serie migratorie pubblicate. '
                'Non vengono forzate a sommare esattamente alla variazione dei residenti, che può includere rettifiche anagrafiche e riallineamenti statistici.'
            ),
        }

    target['meta']['detailLabel'] = 'Componenti della variazione demografica'
    target.setdefault('method', {})['componentDetail'] = (
        'Saldo naturale, saldo migratorio interno e saldo migratorio con l’estero sono confrontati sul 2024, '
        'ultimo anno comune disponibile nelle serie correnti.'
    )


def update_audit(audit: dict) -> None:
    decisions = {
        'share80Plus': 'public_detail_80_85_2026',
        'populationAgeSexDetail': 'public_pyramid_2026',
    }
    for candidate in audit.get('candidates', []):
        if candidate.get('key') in decisions:
            candidate['implementationStatus'] = decisions[candidate['key']]
    audit['demographyV2'] = {
        'ageDistribution2026': 'materialized',
        'share80PlusAnd85Plus': 'public_detail',
        'populationAgeSexPyramid': 'public_town_detail',
        'populationChangeComponents': 'public_town_detail_2024',
        'foreignCitizenshipBirthCountry': 'pending_rcs_probe',
    }


def main() -> None:
    site = load(SITE_PATH)
    audit = load(AUDIT_PATH)
    snapshot = load(SNAPSHOT_PATH)

    if 'naturalDemographicDynamics' not in site['metrics'] or 'dependencyIndices' not in site['metrics']:
        raise RuntimeError('Demografia v2 deve essere eseguita dopo materialize_demography_lotto_a_v4.py')

    update_age_distribution(site, snapshot)
    update_population_change_components(site, snapshot)
    update_audit(audit)

    save(SITE_PATH, site)
    save(AUDIT_PATH, audit)
    print('Demografia v2: ageDistribution 2026, 80+/85+, piramide e componenti variazione materializzate senza nuove card.')


if __name__ == '__main__':
    main()
