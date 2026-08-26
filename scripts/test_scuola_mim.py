#!/usr/bin/env python3
from __future__ import annotations
import json
import math
from pathlib import Path

# Trigger branch materialization after the workflow definition is present.
ROOT = Path(__file__).resolve().parents[1]
KEYS = [
    'schoolBuildingSafetyDocs',
    'schoolBuildingAccessibility',
    'schoolBuildingFacilities',
    'schoolBuildingAge',
    'schoolBuildingTransport',
]

def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def main():
    site = load('data/site-data.json')
    snap = load('data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json')
    assert snap['schoolYear'] == '2024/25' and snap['uniqueBuildingsVersilia'] == 109
    assert sum(v['buildings'] for v in snap['towns'].values()) == 109
    for key in KEYS:
        metric = site['metrics'][key]
        assert metric['meta']['theme'] == 'istruzione'
        assert metric['meta']['year'] == '2024/25'
        assert len(metric['rows']) == 7
        assert metric['method']['coverage'].startswith('7/7')
        assert metric['aggregate']['buildings'] == 109
    section = next(s for s in site['themes']['istruzione']['sections'] if s['key'] == 'edilizia-scolastica')
    assert section['metrics'] == KEYS
    assert all(k in site['themes']['istruzione']['metrics'] for k in KEYS)

    safety = site['metrics']['schoolBuildingSafetyDocs']
    agg = {p['selectorLabel']: p for p in safety['aggregate']['parts']}
    assert agg['Agibilità']['count'] == 26 and agg['Agibilità']['defined'] == 109
    assert agg['CPI']['count'] == 34 and agg['CPI']['unknown'] == 9 and agg['CPI']['defined'] == 100
    assert agg['SCIA']['count'] == 16 and agg['SCIA']['unknown'] == 24 and agg['SCIA']['defined'] == 85
    assert math.isclose(agg['CPI']['value'], 34.0, abs_tol=1e-9)

    access = site['metrics']['schoolBuildingAccessibility']['aggregate']['parts']
    assert access[0]['count'] == 101 and access[0]['defined'] == 105 and access[0]['unknown'] == 4
    assert access[2]['count'] == 4

    facilities = {p['selectorLabel']: p for p in site['metrics']['schoolBuildingFacilities']['aggregate']['parts']}
    assert facilities['Mensa']['count'] == 81 and facilities['Palestra']['count'] == 56

    age = {p['selectorLabel']: p for p in site['metrics']['schoolBuildingAge']['aggregate']['parts']}
    assert age['Entro 1970']['count'] == 60
    assert age['Non definito']['count'] == 9

    transport = {p['selectorLabel']: p for p in site['metrics']['schoolBuildingTransport']['aggregate']['parts']}
    assert transport['Scuolabus']['count'] == 80
    assert transport['TPL urbano']['count'] == 73
    assert transport['TPL interurbano']['count'] == 37

    registry = load('data/source-registry.json')
    # Il gate Scuola verifica il contratto globale corrente senza congelarlo
    # alla release in cui il lotto MIM è stato introdotto.
    external = sum(
        metric.get('dataStorage', {}).get('type') == 'external-climate'
        for metric in site['metrics'].values()
    )
    assert registry['expectedMetricCount'] == len(site['metrics'])
    assert registry['expectedExternalMetricCount'] == external == 4
    assert registry['expectedInlineMetricCount'] == len(site['metrics']) - external
    for key in KEYS:
        assert registry['metricOverrides'][key]['profile'] == 'mim-school-year'

    print('Lotto Scuola MIM verificato: 5 indicatori, 7/7 Comuni, 109 edifici; NON DEFINITO preservato.')

if __name__ == '__main__':
    main()
