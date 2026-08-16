#!/usr/bin/env python3
"""Materialize and finalize the validated Economy/costs release.

This is the production counterpart of the economy draft pipeline. It applies
all validated transformations to canonical source files, updates release
metadata, cache revisions and regression expectations. The script is
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
APP05 = ROOT / 'assets' / 'app-parts' / '05.txt'
BUILD_SAFE = ROOT / 'scripts' / 'build_static_safe.py'
BUILD_BRAND = ROOT / 'scripts' / 'build_static_brand.py'
SERVICE_WORKER = ROOT / 'service-worker.js'
BRAND_TEST = ROOT / 'scripts' / 'test_brand_identity.py'

TRANSFORMS = [
    'apply_costi_fiscalita_redditi_draft.py',
    'materialize_validated_costs.py',
    'patch_costi_fiscalita_frontend.py',
    'apply_costi_fiscalita_review.py',
    'apply_costi_fiscalita_review_v2.py',
    'patch_fuel_precision.py',
    'fix_income_inflation_legend.py',
    'patch_income_inflation_history.py',
    'fix_income_inflation_tooltip_data.py',
]


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_script(name: str) -> None:
    runpy.run_path(str(ROOT / 'scripts' / name), run_name='__main__')


def replace_any(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if new in text:
            continue
        if old not in text:
            raise RuntimeError(f'Release anchor missing in {path}: {old!r}')
        text = text.replace(old, new, 1)
    path.write_text(text, encoding='utf-8')


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


def patch_release_surface() -> None:
    replace_any(
        BUILD_SAFE,
        [
            ('UX_ASSET_VERSION = "20260814-v111"', 'UX_ASSET_VERSION = "20260816-v113"'),
            ('HISTORY_ASSET_VERSION = "20260814-v111"', 'HISTORY_ASSET_VERSION = "20260816-v113"'),
        ],
    )
    replace_any(
        BUILD_BRAND,
        [('APP_BUNDLE_ASSET_VERSION = "20260814-v111"', 'APP_BUNDLE_ASSET_VERSION = "20260816-v113"')],
    )
    replace_any(
        SERVICE_WORKER,
        [("const VERSION = 'ov-pwa-20260814-v111';", "const VERSION = 'ov-pwa-20260816-v113';")],
    )
    replace_any(
        BRAND_TEST,
        [
            ('assets/app-bundle.js?v=20260814-v111', 'assets/app-bundle.js?v=20260816-v113'),
            ('assets/visual-grammar.js?v=20260814-v111', 'assets/visual-grammar.js?v=20260816-v113'),
        ],
    )

    app = APP05.read_text(encoding='utf-8')
    marker = '    const versions = [\n'
    if marker not in app:
        raise RuntimeError('Elenco versioni progetto non trovato')
    entries = ''
    if '2026.08.16-v1.13.0' not in app:
        entries += (
            "      ['2026.08.16-v1.13.0','16 agosto 2026','127 indicatori complessivi in 11 temi, "
            "inclusi i 4 indicatori climatici. Estesi redditi e costo della vita con serie MEF 2011–2024, "
            "redditi vs inflazione, fiscalità locale standardizzata, carburanti e costo del servizio rifiuti.'],\n"
        )
    if '2026.08.14-v1.12.0' not in app:
        entries += (
            "      ['2026.08.14-v1.12.0','14 agosto 2026','121 indicatori complessivi in 11 temi, "
            "inclusi i 4 indicatori climatici. Rafforzato Sicurezza e territorio con sicurezza stradale, "
            "Missione 03 e proventi del Codice della strada.'],\n"
        )
    if entries:
        APP05.write_text(app.replace(marker, marker + entries, 1), encoding='utf-8')


def main() -> None:
    for transform in TRANSFORMS:
        run_script(transform)
    finalize_metadata()
    patch_release_surface()
    run_script('patch_composite_regression_for_costs.py')
    print('Economy release materialized: v1.13.0 · 127 metrics = 123 inline + 4 external')


if __name__ == '__main__':
    main()
