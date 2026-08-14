#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/site-data.json').read_text(encoding='utf-8')); r=json.loads((R/'data/source-registry.json').read_text(encoding='utf-8'))
e={k for k,m in d['metrics'].items() if m.get('dataStorage',{}).get('type')=='external-climate'}
assert d['version']=='v1.11.0' and len(d['metrics'])==119 and len(e)==4 and len(d['metrics'])-len(e)==115
assert {'foreignResidents','foreignResidentialMobility','totalResidentialMobility','omiResidential'} <= set(d['metrics'])
assert (r['expectedMetricCount'],r['expectedInlineMetricCount'],r['expectedExternalMetricCount'])==(119,115,4)
print('v1.11.0: 119 indicatori = 115 inline + 4 climatici esterni')
