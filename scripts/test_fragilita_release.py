#!/usr/bin/env python3
"""Contratto dati/architettura v1.33.0: fragilità nei renderer canonici."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT/'data/source-snapshots/fragilita-comunale-v133.json'
EXPECTED={
 'Camaiore':([4,4,3,2],[10,11,10,9]),
 'Forte dei Marmi':([4,4,4,4],[5,5,6,5]),
 'Massarosa':([4,4,3,4],[10,10,9,11]),
 'Pietrasanta':([4,4,3,3],[9,9,9,8]),
 'Seravezza':([1,2,1,1],[9,10,9,10]),
 'Stazzema':([6,7,7,7],[11,14,12,14]),
 'Viareggio':([3,3,2,2],[10,11,9,9]),
}

def load_materializer():
    path=ROOT/'scripts/materialize_fragilita_release.py'
    spec=importlib.util.spec_from_file_location('frag_v133',path)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)
    return mod

def main():
    snap=json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    assert set(snap['istatByTown'])==set(EXPECTED)==set(snap['hazardsByTown'])
    years=[2018,2019,2021,2022]
    for town,(ifc,low) in EXPECTED.items():
        rows=snap['istatByTown'][town]['series']
        assert [r['year'] for r in rows['COMP_FRAG_INDEX_DECILE']]==years
        assert [r['value'] for r in rows['COMP_FRAG_INDEX_DECILE']]==ifc
        assert [r['value'] for r in rows['PERSEMP_LU_LOW_PRO_INDSERV_VENTILE']]==low
        flood=snap['hazardsByTown'][town]['flood']
        for field in ('areaKm2','areaPct','residents','residentsPct'):
            assert flood['P3'][field] <= flood['P2'][field] + 1e-9 <= flood['P1'][field] + 1e-9, (town,field)
        hist=snap['hazardsByTown'][town]['landslideP3P4History']
        assert [r['year'] for r in hist]==[2017,2020,2024]
    mod=load_materializer(); metrics=mod.build_metrics(snap)
    assert set(metrics)=={'municipalFragility','protectedNaturalAreas','essentialServicesAccessibility','lowProductivityEmployment','landslideExposure','floodExposure'}
    assert metrics['municipalFragility']['meta']['ordinalScale']['max']==10
    assert metrics['lowProductivityEmployment']['meta']['ordinalScale']['max']==20
    assert all(row['series'] is None for row in metrics['protectedNaturalAreas']['rows'])
    assert all(row['series'] is None for row in metrics['essentialServicesAccessibility']['rows'])
    assert metrics['landslideExposure']['meta']['compositeType']=='hydroRisk'
    assert metrics['floodExposure']['meta']['compositeType']=='hydroRisk'
    assert metrics['landslideExposure']['meta']['defaultScenario']=='P3+P4'
    assert metrics['floodExposure']['meta']['defaultScenario']=='P2'
    assert metrics['floodExposure']['meta']['selectorLabel']=='Scenario di pericolosità'
    assert 'Scenari non sommabili' in metrics['floodExposure']['meta']['scenarioNote']
    assert 'P2 comprende le aree P3' in metrics['floodExposure']['meta']['scenarioNote']
    assert metrics['landslideExposure']['meta'].get('scenarioNote') is None
    assert not (ROOT/'confronta/comunita/fragilita').exists()
    assert not (ROOT/'assets/fragilita-v133.css').exists()
    assert not (ROOT/'assets/fragilita-v133.js').exists()
    runtime=(ROOT/'scripts/patch_fragilita_runtime.py').read_text(encoding='utf-8')
    assert "compositeType === 'hydroRisk'" in runtime
    assert 'hydro-risk-indicator-comparison' in runtime
    assert "data-composite-scale" in runtime and "residentsPct" in runtime
    assert 'Come leggere gli scenari.' in runtime
    assert 'scenarioNote' in runtime
    controls_block=runtime.split('def f_controls',1)[1].split('def f_town_markup',1)[0]
    assert 'scenarioNote' not in controls_block, 'La nota scenari non deve stare nel toolbar dei selettori'
    assert 'composite-compare-note' in runtime and 'Come leggere gli scenari:' in runtime
    print('Fragilità v1.33.0: dati 7/7 e architettura canonica OK')
if __name__=='__main__': main()
