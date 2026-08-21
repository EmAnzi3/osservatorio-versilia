#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
REGISTRY_PATH = ROOT / 'data' / 'source-registry.json'
MONITOR_PATH = ROOT / 'data' / 'source-monitor-state.json'
SNAPSHOT_PATH = ROOT / 'data' / 'source-snapshots' / 'fiscal-lotto-b-2025.json'

METRIC_KEY = 'fiscalRecoveryActivity'
SIOPE_SOURCE = 'https://bdap-opendata.rgs.mef.gov.it/opendata/spd_rnd_ent_sio_reg09_01_2025?metadati=showall'
DAIT_SOURCE = 'https://dait.interno.gov.it/documenti/com-fl-03-12-2025-all.pdf'


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(site: dict) -> dict[str, dict]:
    rows = site['metrics']['income']['rows']
    return {row['town']: {'code': row['code'], 'slug': row['slug']} for row in rows}


def part(label: str, selector: str, value: float, *, note: str = '') -> dict:
    return {
        'label': label,
        'selectorLabel': selector,
        'value': round(float(value), 2),
        'unit': 'currency',
        'note': note,
    }


def build_metric(site: dict, snapshot: dict) -> dict:
    ids = identity(site)
    order = [row['town'] for row in site['metrics']['income']['rows']]
    rows = []
    total_receipts = 0.0
    total_population = 0
    total_dait = 0.0

    for town in order:
        raw = snapshot['towns'][town]
        total = float(raw['verificationControlReceiptsEuro'])
        population = int(raw['populationIstat'])
        per_resident = total / population
        dait = float(raw['daitContribution2025Euro'])
        total_receipts += total
        total_population += population
        total_dait += dait
        rows.append({
            'town': town,
            'code': ids[town]['code'],
            'slug': ids[town]['slug'],
            'value': per_resident,
            'formatted': '',
            'series': {'years': [2025], 'values': [per_resident]},
            'normalized': None,
            'benchmarkValue': per_resident,
            'summaryValue': per_resident,
            'parts': [
                part(
                    'Incassi da verifica e controllo per residente',
                    'Recupero €/residente',
                    per_resident,
                    note='Incassi SIOPE 2025 classificati come riscossi a seguito di attività di verifica e controllo, divisi per la popolazione ISTAT riportata nello stesso dataset.',
                ),
                part(
                    'Incassi da verifica e controllo · totale',
                    'Recupero totale',
                    total,
                    note='Importo cumulato a dicembre 2025. È cassa effettivamente riscossa, non accertamenti contabili e non una stima dell’evasione.',
                ),
                part(
                    'Contributo per partecipazione all’accertamento fiscale/contributivo',
                    'Contributo accertamento',
                    dait,
                    note='Contributo DAIT 2025 riferito a riscossioni 2024 di tributi erariali, interessi e sanzioni avvenute a seguito di segnalazioni comunali.',
                ),
            ],
            'breakdownEuro': raw['breakdownEuro'],
            'sourceCodes': raw['codes'],
            'populationIstat': population,
        })

    aggregate_per_resident = total_receipts / total_population
    aggregate_parts = [
        part('Incassi da verifica e controllo per residente', 'Recupero €/residente', aggregate_per_resident),
        part('Incassi da verifica e controllo · totale', 'Recupero totale', total_receipts),
        part('Contributo per partecipazione all’accertamento fiscale/contributivo', 'Contributo accertamento', total_dait),
    ]

    return {
        'meta': {
            'key': METRIC_KEY,
            'theme': 'economia',
            'label': 'Recupero tributario e accertamento',
            'shortLabel': 'Recupero e accertamento',
            'description': (
                'Due letture distinte dell’attività fiscale comunale: gli incassi di tributi locali che SIOPE classifica '
                'come riscossi a seguito di verifica e controllo e il contributo statale DAIT riconosciuto ai Comuni per '
                'la partecipazione all’accertamento fiscale e contributivo. Non è un tasso di evasione fiscale.'
            ),
            'unit': 'currency',
            'year': '2025',
            'source': 'RGS — OpenBDAP/SIOPE · Ministero dell’Interno — DAIT',
            'polarity': 'neutral',
            'compositeType': 'securityMeasures',
            'selectorLabel': 'Lettura',
            'summaryLabel': 'Recupero tributario per residente',
            'summaryUnit': 'currency',
            'searchTerms': [
                'recupero tributario', 'verifica e controllo', 'evasione', 'accertamento fiscale',
                'accertamento contributivo', 'segnalazioni comuni', 'siope', 'dait',
            ],
        },
        'sourceUrl': SIOPE_SOURCE,
        'rows': rows,
        'aggregate': {
            'value': aggregate_per_resident,
            'summaryValue': aggregate_per_resident,
            'label': 'Versilia · recupero tributario per residente',
            'note': (
                'Versilia calcolata come somma degli incassi dei sette Comuni divisa per la popolazione complessiva '
                'riportata da SIOPE. Il contributo DAIT è la somma degli importi attribuiti ai beneficiari della Versilia.'
            ),
            'parts': aggregate_parts,
        },
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione Osservatorio su dati ufficiali RGS/OpenBDAP-SIOPE e DAIT',
            'formula': (
                'Recupero: somma, al mese 2025/12, degli importi cumulati dei codici SIOPE la cui descrizione ufficiale '
                'riporta “riscossa/o a seguito di attività di verifica e controllo”. Il valore pro capite divide il totale '
                'per la popolazione ISTAT riportata dal dataset. Contributo accertamento: importo netto DAIT 2025; '
                'i Comuni assenti dall’elenco dei beneficiari sono rappresentati con 0 €.'
            ),
            'caveat': (
                'Gli incassi da verifica e controllo non misurano l’evasione fiscale né l’efficacia complessiva dell’ufficio '
                'tributi: dipendono da basi imponibili, arretrati, tempi di riscossione e scelte amministrative. Il contributo '
                'DAIT riguarda invece riscossioni erariali 2024 generate da segnalazioni comunali ed è una dimensione separata.'
            ),
            'coverage': '7/7 per SIOPE 2025; elenco DAIT 2025 completo, con 2/7 Comuni beneficiari',
            'additionalSource': DAIT_SOURCE,
            'siopeReferenceMonth': '2025/12',
            'daitReferenceYear': 'riscossioni 2024 · contributo 2025',
        },
    }


def insert_metric(site: dict, metric: dict) -> None:
    metrics = site['metrics']
    if METRIC_KEY in metrics:
        metrics[METRIC_KEY] = metric
    else:
        out = OrderedDict()
        inserted = False
        for key, value in metrics.items():
            out[key] = value
            if key == 'municipalImuStandard':
                out[METRIC_KEY] = metric
                inserted = True
        if not inserted:
            out[METRIC_KEY] = metric
        site['metrics'] = out

    theme = site['themes']['economia']
    if METRIC_KEY not in theme['metrics']:
        anchor = theme['metrics'].index('municipalImuStandard') + 1 if 'municipalImuStandard' in theme['metrics'] else len(theme['metrics'])
        theme['metrics'].insert(anchor, METRIC_KEY)

    section = next(section for section in theme['sections'] if section.get('key') == 'costi-fiscalita')
    if METRIC_KEY not in section['metrics']:
        anchor = section['metrics'].index('municipalImuStandard') + 1 if 'municipalImuStandard' in section['metrics'] else len(section['metrics'])
        section['metrics'].insert(anchor, METRIC_KEY)
    section['description'] = (
        'Confronti standardizzati su tributi comunali, costi osservabili sul territorio e attività di recupero/accertamento fiscale.'
    )


def update_registry(registry: dict) -> None:
    total = 133
    registry['expectedMetricCount'] = total
    registry['expectedInlineMetricCount'] = total - 4
    registry['expectedExternalMetricCount'] = 4
    registry.setdefault('sourceProfiles', {})['dait-fiscal-assessment-annual'] = {
        'publisher': 'Ministero dell’Interno — DAIT / Dipartimento delle Finanze — MEF',
        'frequency': 'annual',
        'frequencyLabel': 'Annuale',
        'expectedRelease': 'Dopo il consolidamento delle riscossioni dell’anno precedente',
        'acquisitionMethod': 'Prospetto ufficiale DAIT dei Comuni beneficiari del contributo per la partecipazione all’accertamento fiscale e contributivo.',
        'licenseName': 'Condizioni indicate dalla fonte ufficiale',
        'licenseUrl': 'https://dait.interno.gov.it/',
    }
    mapping = registry.setdefault('sourceProfileByUrl', {})
    mapping[SIOPE_SOURCE] = 'siope-monthly'
    mapping[DAIT_SOURCE] = 'dait-fiscal-assessment-annual'
    registry.setdefault('metricOverrides', {})[METRIC_KEY] = {'profile': 'siope-monthly'}


def upsert_monitor_source(monitor: dict, url: str, *, profile: str, frequency: str, role: str = 'primary') -> None:
    sources = monitor.setdefault('sources', {})
    source = sources.setdefault(url, {
        'url': url,
        'ok': True,
        'status': 200,
        'finalUrl': url,
        'contentType': '',
        'contentLength': None,
        'etag': '',
        'lastModified': '',
        'contentSha256': '',
        'hashTruncated': False,
        'error': '',
        'metrics': [],
        'roles': [],
        'profileIds': [],
        'frequencies': [],
    })
    for key, value in (
        ('metrics', METRIC_KEY), ('roles', role), ('profileIds', profile), ('frequencies', frequency)
    ):
        values = source.setdefault(key, [])
        if value not in values:
            values.append(value)
            values.sort()


def main() -> None:
    site = load(SITE_PATH)
    registry = load(REGISTRY_PATH)
    monitor = load(MONITOR_PATH)
    snapshot = load(SNAPSHOT_PATH)

    metric = build_metric(site, snapshot)
    insert_metric(site, metric)
    update_registry(registry)
    upsert_monitor_source(monitor, SIOPE_SOURCE, profile='siope-monthly', frequency='monthly')
    upsert_monitor_source(monitor, DAIT_SOURCE, profile='dait-fiscal-assessment-annual', frequency='annual', role='additional')

    if len(site['metrics']) != 133:
        raise RuntimeError(f'Catalogo Lotto B inatteso: {len(site["metrics"])} indicatori, attesi 133')

    save(SITE_PATH, site)
    save(REGISTRY_PATH, registry)
    save(MONITOR_PATH, monitor)
    print('Fiscalità Lotto B materializzata: 133 indicatori complessivi = 129 inline + 4 esterni')


if __name__ == '__main__':
    main()
