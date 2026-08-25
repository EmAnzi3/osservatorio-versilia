#!/usr/bin/env python3
from pathlib import Path
import json

src = Path('data/site-data.json')
data = json.loads(src.read_text(encoding='utf-8'))
out = Path('artifacts/mobilita-v6-review/current-mobilita.json')
out.parent.mkdir(parents=True, exist_ok=True)

# Individua il tema Mobilità senza assumere la forma interna del catalogo.
themes = data.get('themes')
if isinstance(themes, dict):
    theme = themes.get('mobilita')
elif isinstance(themes, list):
    theme = next((x for x in themes if x.get('key') == 'mobilita'), None)
else:
    theme = None

if not theme:
    raise SystemExit('Tema mobilita non trovato in data/site-data.json')

metric_keys = theme.get('metrics', [])
metrics = data.get('metrics', {})
selected = {}
if isinstance(metrics, dict):
    for key in metric_keys:
        if key in metrics:
            selected[key] = metrics[key]
elif isinstance(metrics, list):
    for m in metrics:
        key = (m.get('meta') or {}).get('key') or m.get('key')
        if key in metric_keys:
            selected[key] = m

payload = {
    'topLevelKeys': list(data.keys()),
    'theme': theme,
    'metricKeys': metric_keys,
    'metrics': selected,
    'towns': data.get('towns'),
}
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Dump Mobilità: {len(metric_keys)} chiavi tema, {len(selected)} metriche risolte')
