#!/usr/bin/env python3
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
overlay=json.loads((ROOT/'data/agricoltura-ii-draft.json').read_text(encoding='utf-8'))
snap=json.loads((ROOT/'data/source-snapshots/istat-agricoltura-ii-2020.json').read_text(encoding='utf-8'))

assert overlay['metricOrder']==['agriculturalRenewalAndLeadership','agriculturalDiversificationAndModernization']
assert snap['rules']['universes']=={'generalFarms':959,'excludingCollectiveProperties':957,'farmsWithHolder':944}

expected={
    'youngManagers':(69,957),
    'femaleHolders':(334,944),
    'connectedActivities':(74,959),
    'informatization':(202,957),
    'innovation':(110,957),
}

for key,(num,den) in expected.items():
    a=snap['aggregates'][key]
    assert (a['numerator'],a['denominator'])==(num,den)
    assert math.isclose(a['value'],num/den*100,rel_tol=0,abs_tol=1e-12)
    vals=[t[key]['value'] for t in snap['towns'].values()]
    simple=sum(vals)/len(vals)
    if not math.isclose(simple,a['value'],abs_tol=1e-12):
        assert not math.isclose(simple,a['value'],abs_tol=1e-6)

assert snap['towns']['046013']['connectedActivities']['numerator']==0
assert snap['towns']['046013']['connectedActivities']['explicitZero'] is True
assert snap['flows']['managerSexUnavailable']['constraintTownCoverage']=={c:False for c in snap['towns']}

text=(ROOT/'data/agricoltura-ii-draft.json').read_text(encoding='utf-8')
assert 'Donne capo azienda' not in text
assert 'conduttrice donna' in text.lower()

for metric in overlay['metrics'].values():
    assert len(metric['rows'])==7
    assert metric['meta']['compositeType']=='agricultureProfile'
    assert 'media semplice' in metric['aggregate']['note'].lower()

css=(ROOT/'assets/agricoltura-ii-draft.css').read_text(encoding='utf-8')
assert 'padding:' in css
assert '.composite-town-mobility article' in css

print('OK — Agricoltura II draft: gate dati, aggregati e padding verificati')
