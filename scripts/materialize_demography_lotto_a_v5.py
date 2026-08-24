#!/usr/bin/env python3
"""Completa gli approfondimenti Demografia Lotto A senza creare nuove card.

Prerequisito: `materialize_demography_lotto_a_v4.py` deve avere già creato lo
snapshot POSAS/P02 e i compositi demografici.

Questa fase:
- riallinea `ageDistribution` al POSAS 2026;
- rende 85+ una vera fascia della distribuzione, scindendo 80+ in 80–84 e 85+;
- prepara una piramide per età e sesso in classi quinquennali, derivata dal
  dettaglio per singola età già acquisito, sia per i comuni sia per la Versilia;
- NON duplica dentro `populationChange` saldi naturale/migratori già pubblicati
  come indicatori autonomi della stessa tematica.
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
    ('80–84 anni', '80–84', 80, 84),
    ('85 anni e oltre', '85+', 85, 120),
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
    weighted_age = 0.0
    versilia_detail: list[dict] = []

    for row in metric['rows']:
        detail = age_rows(snapshot, row['town'])
        versilia_detail.extend(detail)
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

        age_mean = sum(int(item['age']) * int(item['total']) for item in detail) / total
        total_population += total
        weighted_age += age_mean * total

        row['parts'] = parts
        # Manteniamo il 20–34 come valore canonico di riga per compatibilità con
        # il renderer esistente; la distribuzione resta il contenuto principale.
        row['value'] = parts[2]['value']
        row['formatted'] = percent(row['value'])
        row['benchmarkValue'] = row['value']
        row['summaryValue'] = age_mean
        row.pop('seniorAgeDetail', None)
        row.pop('age85PlusDetail', None)
        row['ageSexPyramid'] = {
            'year': 2026,
            'sourceGranularity': 'singola età e sesso',
            'displayBands': build_pyramid(detail),
        }

    metric['meta']['year'] = '2026'
    metric['meta']['description'] = (
        'Quota dei residenti nelle fasce 0–14, 15–19, 20–34, 35–49, 50–64, 65–79, 80–84 e 85 anni e oltre. '
        'La piramide per età e sesso è disponibile sia nelle schede comunali sia per l’intera Versilia.'
    )
    metric['meta'].pop('detailLabel', None)
    metric['meta']['pyramidLabel'] = 'Piramide per età e sesso'
    method = metric.setdefault('method', {})
    method['type'] = 'Elaborazione Osservatorio su dati Istat POSAS'
    method['formula'] = (
        'residenti della fascia / popolazione residente totale × 100; '
        'età media = somma(età × residenti alla singola età) / residenti totali'
    )
    method['caveat'] = (
        'Distribuzione, piramide ed età media sono calcolate sulla stessa popolazione POSAS '
        'al 1° gennaio 2026. L’età media è un’elaborazione Osservatorio sui conteggi per singola età.'
    )
    method['coverage'] = '7/7'
    method['detail'] = (
        'Distribuzione e piramide derivano dal POSAS Istat al 1° gennaio 2026. '
        'Per rendere il dato 85+ una componente confrontabile senza sovrapposizioni, la precedente fascia 80+ è scissa in 80–84 e 85 anni e oltre. '
        'La piramide visualizza classi quinquennali per leggibilità, mantenendo nello snapshot il dato per singola età e sesso. '
        'La piramide Versilia è ottenuta sommando uomini e donne dei sette comuni per ciascuna classe d’età.'
    )
    metric['aggregate'] = {
        'value': total_counts[2] / total_population * 100,
        'label': 'Versilia · 20–34 anni',
        'note': 'Quota calcolata sul totale dei residenti dei sette comuni; la barra mostra tutte le fasce senza sovrapposizioni.',
        'parts': [
            {'label': label, 'count': total_counts[idx], 'value': total_counts[idx] / total_population * 100}
            for idx, (label, _selector, _lower, _upper) in enumerate(AGE_BANDS)
        ],
        'summaryValue': weighted_age / total_population,
        'summaryLabel': 'Età media Versilia',
        'summaryNote': 'Età media ponderata sulla popolazione dei sette comuni; la barra mostra la distribuzione completa per fascia.',
        'ageSexPyramid': {
            'year': 2026,
            'sourceGranularity': 'somma dei sette comuni per singola età e sesso',
            'displayBands': build_pyramid(versilia_detail),
        },
    }


def remove_duplicate_population_change_detail(site: dict) -> None:
    target = site['metrics']['populationChange']
    for row in target['rows']:
        row.pop('changeComponents', None)
    target['meta'].pop('detailLabel', None)
    target.setdefault('method', {}).pop('componentDetail', None)


def update_audit(audit: dict) -> None:
    decisions = {
        'share80Plus': 'public_distribution_split_80_84_85_plus_2026',
        'populationAgeSexDetail': 'public_pyramid_2026_towns_and_versilia',
    }
    for candidate in audit.get('candidates', []):
        if candidate.get('key') in decisions:
            candidate['implementationStatus'] = decisions[candidate['key']]
    previous_v2 = audit.get('demographyV2') if isinstance(audit.get('demographyV2'), dict) else {}
    foreign_detail = previous_v2.get('foreignCitizenshipBirthCountry', 'pending_rcs_probe')
    audit['demographyV2'] = {
        'ageDistribution2026': 'materialized_8_non_overlapping_bands',
        'share80PlusAnd85Plus': 'public_distribution_80_84_85_plus',
        'populationAgeSexPyramid': 'public_town_and_versilia_native_tooltip',
        'populationChangeComponents': 'not_added_duplicate_existing_metrics',
        'foreignCitizenshipBirthCountry': foreign_detail,
    }


def main() -> None:
    site = load(SITE_PATH)
    audit = load(AUDIT_PATH)
    snapshot = load(SNAPSHOT_PATH)

    if 'naturalDemographicDynamics' not in site['metrics'] or 'dependencyIndices' not in site['metrics']:
        raise RuntimeError('Demografia v2 deve essere eseguita dopo materialize_demography_lotto_a_v4.py')

    update_age_distribution(site, snapshot)
    remove_duplicate_population_change_detail(site)
    update_audit(audit)

    save(SITE_PATH, site)
    save(AUDIT_PATH, audit)
    print('Demografia v2: 85+ integrato nella distribuzione; piramide comuni + Versilia pronta; componenti variazione duplicate rimosse.')


if __name__ == '__main__':
    main()
