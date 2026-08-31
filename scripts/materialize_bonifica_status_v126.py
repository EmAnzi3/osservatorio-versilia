#!/usr/bin/env python3
"""Materializza gli indicatori di stato lavori del Lotto 6 v1.26.0."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'data/site-data.json'
REGISTRY = ROOT / 'data/source-registry.json'
STATE = ROOT / 'data/source-monitor-state.json'
STATUS = ROOT / 'data/source-snapshots/bonifica-rischio-v126-status.json'
PORTAL_URL = 'https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/'
KEYS = (
    'pabInterventionsInProgress',
    'pabInterventionsCompleted',
    'pabInProgressOperationalGrossValue',
    'pabCompletedOperationalGrossValue',
)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def it(value, digits=0):
    return f'{value:,.{digits}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def town_index(site):
    sample = site['metrics']['landUse']['rows']
    return {row['town']: (row['code'], row['slug']) for row in sample}


def rows(site, values, formatter):
    index = town_index(site)
    return [
        {
            'town': town['name'],
            'code': index[town['name']][0],
            'slug': index[town['name']][1],
            'value': values[town['name']],
            'formatted': formatter(values[town['name']]),
            'series': None,
            'normalized': None,
            'benchmarkValue': values[town['name']],
        }
        for town in site['towns']
    ]


def meta(key, label, short_label, description, unit, note):
    return {
        'key': key,
        'theme': 'ambiente',
        'label': label,
        'shortLabel': short_label,
        'description': description,
        'unit': unit,
        'year': '2026',
        'source': 'Consorzio 1 Toscana Nord — Portale manutenzioni, layer operativo pmo_stato_lavori',
        'polarity': 'neutral',
        'context': 'Stato lavori di manutenzione 2026',
        'searchTerms': ['bonifica', 'manutenzione', 'pab', 'stato lavori', 'in corso', 'completati'],
        'sourceMeta': {
            'snapshot': str(STATUS.relative_to(ROOT)),
            'note': note,
        },
    }


def make_metric(site, key, label, short_label, description, unit, values, total, aggregate_label, aggregate_note, note, formula, caveat):
    formatter = (lambda value: '€ ' + it(value, 2)) if unit == 'currency2' else (lambda value: it(value, 0))
    return {
        'meta': meta(key, label, short_label, description, unit, note),
        'sourceUrl': PORTAL_URL,
        'rows': rows(site, values, formatter),
        'aggregate': {'value': total, 'label': aggregate_label, 'note': aggregate_note},
        'normalizedAggregate': None,
        'method': {
            'type': 'Elaborazione da estrazione WFS massiva del portale manutenzioni Consorzio 1 Toscana Nord',
            'formula': formula,
            'caveat': caveat,
            'coverage': '7/7',
            'snapshot': str(STATUS.relative_to(ROOT)),
        },
    }


def main():
    site = load(SITE)
    registry = load(REGISTRY)
    state = load(STATE)
    status = load(STATUS)

    assert status['matching']['municipalExportRows'] == 1265
    assert status['matching']['matchedRows'] == 1265
    assert status['matching']['uniqueWfsFeatureIds'] == 1265
    assert status['punctualLayer']['sharedIdsWithCbPmoLineare'] == 251
    assert status['aggregateSevenTowns']['in_corso']['features'] == 222
    assert status['aggregateSevenTowns']['completato']['features'] == 248
    assert status['aggregateSevenTowns']['in_corso']['grossAmountEur'] == 644508.15
    assert status['aggregateSevenTowns']['completato']['grossAmountEur'] == 693981.13

    by_town = status['byTown']
    in_progress_count = {town: values['in_corso']['features'] for town, values in by_town.items()}
    completed_count = {town: values['completato']['features'] for town, values in by_town.items()}
    in_progress_value = {town: values['in_corso']['grossAmountEur'] for town, values in by_town.items()}
    completed_value = {town: values['completato']['grossAmountEur'] for town, values in by_town.items()}

    snapshot_note = (
        'Situazione congelata al 31 agosto 2026. Le 1.265 righe degli export comunali sono ricondotte a 1.265 feature distinte '
        'di cb_pmo_lineare. Il layer interventi_puntuali è una rappresentazione alternativa di un sottoinsieme e non viene sommato.'
    )
    count_caveat = (
        'Il conteggio riguarda feature operative del portale, non codici univoci dell’Allegato A-1. Lo snapshot operativo contiene '
        '1.265 feature, mentre l’Allegato A-1 approvato contiene 1.259 codici univoci.'
    )
    value_caveat = (
        'Il valore è il campo operativo importo_lordo del WFS: non coincide con l’importo programmato approvato dell’Allegato A-1 '
        'e non rappresenta spesa pagata, liquidata o certificata.'
    )

    metrics = {
        KEYS[0]: make_metric(
            site, KEYS[0], 'Interventi di manutenzione in corso', 'Interventi in corso',
            'Numero di feature operative associate agli export comunali PAB 2026 che al 31 agosto 2026 hanno lavori_inizio valorizzato e lavori_fine vuoto.',
            'number', in_progress_count, 222, 'Versilia · interventi in corso',
            'Somma delle feature operative classificate in corso nei sette Comuni.', snapshot_note,
            'Conteggio delle feature con lavori_inizio valorizzato e lavori_fine vuoto.', count_caveat,
        ),
        KEYS[1]: make_metric(
            site, KEYS[1], 'Interventi di manutenzione completati', 'Interventi completati',
            'Numero di feature operative associate agli export comunali PAB 2026 che al 31 agosto 2026 hanno lavori_fine valorizzato.',
            'number', completed_count, 248, 'Versilia · interventi completati',
            'Somma delle feature operative classificate completate nei sette Comuni.', snapshot_note,
            'Conteggio delle feature con lavori_fine valorizzato.', count_caveat,
        ),
        KEYS[2]: make_metric(
            site, KEYS[2], 'Valore lordo operativo degli interventi in corso', 'Valore operativo · in corso',
            'Somma del campo operativo importo_lordo delle feature di manutenzione classificate in corso al 31 agosto 2026.',
            'currency2', in_progress_value, 644508.15, 'Versilia · valore lordo operativo in corso',
            'Somma del campo importo_lordo delle feature classificate in corso nei sette Comuni.', snapshot_note,
            'Somma di importo_lordo per le feature con lavori_inizio valorizzato e lavori_fine vuoto.', value_caveat,
        ),
        KEYS[3]: make_metric(
            site, KEYS[3], 'Valore lordo operativo degli interventi completati', 'Valore operativo · completati',
            'Somma del campo operativo importo_lordo delle feature di manutenzione classificate completate al 31 agosto 2026.',
            'currency2', completed_value, 693981.13, 'Versilia · valore lordo operativo completato',
            'Somma del campo importo_lordo delle feature classificate completate nei sette Comuni.', snapshot_note,
            'Somma di importo_lordo per le feature con lavori_fine valorizzato.', value_caveat,
        ),
    }
    site['metrics'].update(metrics)

    ambiente = site['themes']['ambiente']
    territorio = next(section for section in ambiente['sections'] if section['key'] == 'territorio')
    for key in KEYS:
        if key not in ambiente['metrics']:
            ambiente['metrics'].append(key)
        if key not in territorio['metrics']:
            territorio['metrics'].append(key)
    site['version'] = 'v1.26.0'
    site['updated'] = '31 agosto 2026'

    profiles = registry.setdefault('sourceProfiles', {})
    profiles['cb1-pmo-status-2026'] = {
        'publisher': 'Consorzio 1 Toscana Nord',
        'frequency': 'irregular',
        'frequencyLabel': 'Aggiornamento operativo del portale',
        'expectedRelease': 'Durante l’esecuzione del Piano delle Attività di Bonifica 2026',
        'acquisitionMethod': 'Estrazione WFS massiva del progetto pmo_stato_lavori; riconciliazione 1:1 delle 1.265 righe degli export comunali con cb_pmo_lineare; classificazione tramite lavori_inizio e lavori_fine.',
        'licenseName': 'Condizioni indicate dal Consorzio 1 Toscana Nord',
        'licenseUrl': 'https://cbtoscananord.it/',
    }
    for key in KEYS:
        registry.setdefault('metricOverrides', {})[key] = {'profile': 'cb1-pmo-status-2026'}
    registry['expectedMetricCount'] = 175
    registry['expectedInlineMetricCount'] = 171
    registry['expectedExternalMetricCount'] = 4

    source = state.setdefault('sources', {}).setdefault(PORTAL_URL, {})
    source.setdefault('url', PORTAL_URL)
    source['ok'] = True
    source['status'] = 200
    source['finalUrl'] = PORTAL_URL
    source.setdefault('roles', ['primary'])
    source_metrics = source.setdefault('metrics', [])
    for key in KEYS:
        if key not in source_metrics:
            source_metrics.append(key)
    profiles_ids = source.setdefault('profileIds', [])
    if 'cb1-pmo-status-2026' not in profiles_ids:
        profiles_ids.append('cb1-pmo-status-2026')
    frequencies = source.setdefault('frequencies', [])
    if 'irregular' not in frequencies:
        frequencies.append('irregular')

    checked = status['referenceTimestamp']
    for key in KEYS:
        state.setdefault('metrics', {})[key] = {
            'publishedPeriod': '2026',
            'checkedAt': checked,
            'observedLatestPeriod': '2026',
            'status': 'current',
        }
    state['checkedAt'] = checked

    app5 = ROOT / 'assets/app-parts/05.txt'
    text = app5.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    replacement = "      ['2026.08.31-v1.26.0','31 agosto 2026','175 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Lotto Bonifica e rischio idraulico: indicatori PAB 2026, reticolo in gestione DCRT 24/2025, opere idrauliche DGRT 1155/2021 e stato operativo degli interventi al 31 agosto 2026. Restano rinviati soltanto i km fisici unici manutenzionati e la relativa quota di reticolo, perché 49 feature operative non espongono geometria.'],\n"
    for index, line in enumerate(lines):
        if "['2026.08.31-v1.26.0'" in line:
            lines[index] = replacement
            break
    else:
        raise RuntimeError('Voce storico v1.26.0 non trovata')
    app5.write_text(''.join(lines), encoding='utf-8')

    save(SITE, site)
    save(REGISTRY, registry)
    save(STATE, state)
    print('Stato lavori Bonifica v1.26 materializzato: 4 indicatori, 7/7 Comuni.')


if __name__ == '__main__':
    main()
