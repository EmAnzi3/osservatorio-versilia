#!/usr/bin/env python3
"""Materialize and finalize the validated Economy/costs release.

This is the production counterpart of the economy draft pipeline. It applies
all validated transformations to canonical source files, updates release
metadata and aligns regression expectations. The script is intentionally
idempotent so it can be used both by CI before deployment and by the one-shot
canonicalization workflow on main.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'site-data.json'
REGISTRY = ROOT / 'data' / 'source-registry.json'

TRANSFORMS = [
    'apply_costi_fiscalita_redditi_draft.py',
    'materialize_validated_costs.py',
    'patch_costi_fiscalita_frontend.py',
    'apply_costi_fiscalita_review.py',
    'apply_costi_fiscalita_review_v2.py',
    'patch_fuel_precision.py',
    'fix_income_inflation_legend.py',
    'patch_income_inflation_history.py',
]


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_script(name: str) -> None:
    runpy.run_path(str(ROOT / 'scripts' / name), run_name='__main__')


def finalize_metadata() -> None:
    data = load(DATA)
    registry = load(REGISTRY)

    data['version'] = 'v1.13.0'
    data['updated'] = '16 agosto 2026'

    state = data.setdefault('costsFiscalDraft', {})
    state.update({
        'status': 'published',
        'releaseVersion': 'v1.13.0',
        'releaseDate': '2026-08-16',
        'publishedInDraft': [
            'municipalIrpef',
            'tariStandardHousehold',
            'municipalImuStandard',
            'fuelPrices',
            'wasteServiceCost',
            'incomeVsInflation',
        ],
        'contextViews': ['incomeLongHistory', 'incomeInflationContext'],
        'notPublished': ['schoolMeals'],
        'note': (
            'Release v1.13.0: reddito imponibile medio 2011–2024, redditi vs inflazione con NIC Italia, '
            'addizionale comunale IRPEF, TARI standardizzata, IMU standardizzata, prezzi carburanti e costo '
            'del servizio rifiuti. Lo storico redditi/inflazione mostra reddito nominale e prezzi su base '
            '2016=0%; i tooltip riportano la variazione reale calcolata come rapporto tra i due indici.'
        ),
    })

    total = len(data['metrics'])
    external = 4
    if total != 127:
        raise RuntimeError(f'Catalogo release inatteso: {total} indicatori, attesi 127')
    registry['expectedMetricCount'] = total
    registry['expectedInlineMetricCount'] = total - external
    registry['expectedExternalMetricCount'] = external

    save(DATA, data)
    save(REGISTRY, registry)


def main() -> None:
    for transform in TRANSFORMS:
        run_script(transform)
    finalize_metadata()
    run_script('patch_composite_regression_for_costs.py')
    print('Economy release materialized: v1.13.0 · 127 metrics = 123 inline + 4 external')


if __name__ == '__main__':
    main()
