#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'audit-artifacts' / 'demography-canonical-schema.json'
site = json.loads((ROOT / 'data/site-data.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'data/source-registry.json').read_text(encoding='utf-8'))
monitor = json.loads((ROOT / 'data/source-monitor-state.json').read_text(encoding='utf-8'))
keys = [
    'population','ageDistribution','oldAgeIndex','foreignResidents',
    'internalResidentialMobility','foreignResidentialMobility',
    'totalResidentialMobility','populationChange','roadSafety','omiResidential'
]
report = {
    'version': site.get('version'),
    'theme': site.get('themes', {}).get('demografia'),
    'metrics': {k: site.get('metrics', {}).get(k) for k in keys},
    'sourceProfiles': {k:v for k,v in registry.get('sourceProfiles',{}).items() if 'istat' in k.lower()},
    'registryMetrics': {k: registry.get('metrics',{}).get(k) for k in keys if k in registry.get('metrics',{})},
    'monitorDemoSources': {u:v for u,v in monitor.get('sources',{}).items() if 'demo.istat.it' in u},
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
