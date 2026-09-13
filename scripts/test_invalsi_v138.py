#!/usr/bin/env python3
"""Gate numerico/source-only per INVALSI v1.38.0."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SHA='bee5b0021704b2053277aa19df35d77ed0aa4b9e2cfc4dfa3d64c16a61c1fd65'
KEYS=['invalsiResults','invalsiCompetence','invalsiImplicitDispersion','invalsiAcademicExcellence']
TOWNS=['Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio']


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def assert_no_pandemic_invention(view):
    assert '2019-20' not in view['years'], view['key']
    if view['grade']==10: assert '2020-21' not in view['years'], view['key']


def main():
    payload=load_module('invalsi_payload',ROOT/'scripts/materialize_invalsi_v138_payload.py')
    raw=payload.reconstruct(); assert len(raw)==70859
    import hashlib
    assert hashlib.sha256(raw).hexdigest()==EXPECTED_SHA
    snap=json.loads(raw)
    assert snap['release']=='v1.38.0' and snap['schemaVersion']==1
    assert snap['municipalityOrder']==TOWNS
    assert snap['selection']['aggregation']=='Totale'
    assert snap['selection']['municipalScale']=='Comune plesso'
    assert snap['selection']['missingCodes']==[888,999]
    assert snap['selection']['versiliaAggregate'].startswith('Non pubblicato')
    assert len(snap['results']['views'])==16
    assert len(snap['competence']['views'])==12
    assert len(snap['implicitDispersion']['views'])==2
    assert len(snap['academicExcellence']['views'])==2
    assert snap['sources']['results']['sha256']=='2d88f9c17c57eb3b1c6c51666a17fca3c2c7830239874bb9359e67a5abe1c474'
    assert snap['sources']['dispersionExcellence']['sha256']=='d6e1889464d40c851e22d4bccc4d2749e4b4b13f0ad1635d188a34f7cb60bff9'

    coverage={v['key']:v['currentCoverage'] for v in snap['results']['views']}
    assert coverage=={
      'g2-italiano':'5/7','g2-matematica':'6/7','g5-italiano':'6/7','g5-matematica':'6/7',
      'g5-inglese-reading':'6/7','g5-inglese-listening':'6/7','g8-italiano':'4/7','g8-matematica':'4/7',
      'g8-inglese-reading':'4/7','g8-inglese-listening':'4/7','g10-italiano':'4/7','g10-matematica':'4/7',
      'g13-italiano':'4/7','g13-matematica':'4/7','g13-inglese-reading':'4/7','g13-inglese-listening':'4/7'}
    for family in ('results','competence','implicitDispersion','academicExcellence'):
        for v in snap[family]['views']:
            assert set(v['municipalities'])==set(TOWNS)
            assert len(v['tuscany']['values'])==len(v['years'])==len(v['italy']['values'])
            assert all(x is not None for x in v['tuscany']['values'])
            assert all(x is not None for x in v['italy']['values'])
            assert_no_pandemic_invention(v)
            if v['grade']==13: assert v['years'][0]=='2018-19'
    g8=next(v for v in snap['results']['views'] if v['key']=='g8-italiano')
    assert g8['municipalities']['Forte dei Marmi']['values'][-1] is None
    assert g8['municipalities']['Stazzema']['values'][-1] is None

    # Il repo conserva la baseline sorgente pre-materializzazioni; il canonical build
    # porta 181→203 con le release precedenti e poi INVALSI applica il contratto 203→207.
    # Qui isoliamo il solo materializzatore INVALSI e verifichiamo quindi un incremento +4.
    mat=load_module('invalsi_materializer',ROOT/'scripts/materialize_invalsi_v138.py')
    assert mat.EXPECTED_BEFORE==203 and mat.EXPECTED_AFTER==207
    baseline=json.loads((ROOT/'data/site-data.json').read_text())
    baseline_count=len(baseline['metrics'])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); site=td/'site-data.json'; reg=td/'source-registry.json'; ss=td/'snapshot.json'
        shutil.copy2(ROOT/'data/site-data.json',site); shutil.copy2(ROOT/'data/source-registry.json',reg); ss.write_bytes(raw)
        mat.SITE_DATA=site; mat.REGISTRY=reg; mat.SNAPSHOT=ss
        mat.EXPECTED_BEFORE=baseline_count; mat.EXPECTED_AFTER=baseline_count+4
        mat.main()
        out=json.loads(site.read_text()); registry=json.loads(reg.read_text())
    assert len(out['metrics'])==baseline_count+4 and out['version']=='v1.38.0'
    assert set(KEYS).issubset(out['metrics'])
    section=next(s for s in out['themes']['istruzione']['sections'] if s['key']=='invalsi')
    assert section['metrics']==KEYS
    assert registry['expectedMetricCount']==baseline_count+4
    for key in KEYS:
        m=out['metrics'][key]
        assert m['meta']['compositeType']=='invalsiProfile'
        assert m['meta']['comparisonReference']=='aggregate'
        assert m['aggregate']['label']=='Toscana'
        assert m['nationalBenchmark']['label']=='Italia'
        assert 'nessuna media' in m['method']['formula'].lower()
        assert 'Versilia' not in m['aggregate']['label']
        assert 'Versilia' not in m['nationalBenchmark']['label']
    forte=next(r for r in out['metrics']['invalsiResults']['rows'] if r['town']=='Forte dei Marmi')
    assert next(p for p in forte['parts'] if p['key']=='g8-italiano')['value'] is None
    print(f'INVALSI v1.38 gate OK: snapshot, coperture, benchmark, n.d. e materializzazione isolata +4; contratto pipeline {203}→{207}.')


if __name__=='__main__': main()
