#!/usr/bin/env python3
"""Applica le correzioni emerse dal collaudo UI del Lotto A Demografia.

- rende esplicita la lettura degli indici di dipendenza come rapporto ogni 100
  persone di 15–64 anni, senza presentarli come percentuale della popolazione;
- amplia il margine sinistro del grafico storico canonico per le unità lunghe
  (es. "ogni 1.000"), evitando il taglio delle etichette dell'asse Y sia nel
  confronto territoriale sia nelle schede comunali.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / 'data' / 'site-data.json'
AUDIT_PATH = ROOT / 'data' / 'data-audit-lotto-a.json'
HISTORY_CORE_PATH = ROOT / 'assets' / 'ux-history-core.js'

OLD_HISTORY_GEOMETRY = (
    "const width = 920, height = 390, left = 78, right = 30, top = 26, bottom = 52;"
)
NEW_HISTORY_GEOMETRY = (
    "const width = 920, height = 390, left = "
    "['per100','per1000','per10k','per100k'].includes(metric.meta.unit) ? 132 : 78, "
    "right = 30, top = 26, bottom = 52;"
)


def formatted_per100(value: float) -> str:
    return f'{float(value):.1f}'.replace('.', ',') + ' ogni 100'


def patch_dependency_semantics() -> None:
    site = json.loads(SITE_PATH.read_text(encoding='utf-8'))
    metric = site['metrics'].get('dependencyIndices')
    if not metric:
        raise RuntimeError('dependencyIndices non materializzato')

    metric['meta']['unit'] = 'per100'
    metric['meta']['description'] = (
        'Misura quante persone nelle età 0–14 e 65+ ci sono ogni 100 persone '
        'tra 15 e 64 anni. La voce “Anziani” considera solo i 65+.'
    )

    for row in metric['rows']:
        row['formatted'] = formatted_per100(row['value'])
        for part in row.get('parts', []):
            part['unit'] = 'per100'

    for part in metric.get('aggregate', {}).get('parts', []):
        part['unit'] = 'per100'

    metric['aggregate']['note'] = (
        'Tutti i valori sono rapporti con base 100 sulla popolazione 15–64 anni: '
        'la voce “Strutturale” somma 0–14 e 65+, la voce “Anziani” considera solo i 65+.'
    )
    metric['method']['formula'] = (
        'dipendenza strutturale = (0–14 + 65+) / 15–64 × 100; '
        'dipendenza anziani = 65+ / 15–64 × 100. '
        'Il risultato si legge come persone nella fascia considerata ogni 100 persone di 15–64 anni.'
    )
    metric['method']['caveat'] = (
        'Non è una percentuale della popolazione totale: è un rapporto con base 100 '
        'rispetto alla popolazione 15–64 anni. Non misura direttamente il carico '
        'economico effettivo sulle persone occupate.'
    )

    SITE_PATH.write_text(
        json.dumps(site, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )

    audit = json.loads(AUDIT_PATH.read_text(encoding='utf-8'))
    candidate = next(
        (item for item in audit.get('candidates', []) if item.get('key') == 'dependencyIndices'),
        None,
    )
    if not candidate:
        raise RuntimeError('dependencyIndices assente dalla matrice audit')
    candidate['unit'] = 'per100'
    candidate['unitExplanation'] = (
        'persone nelle fasce considerate ogni 100 persone di 15–64 anni; '
        'non percentuale della popolazione totale'
    )
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )


def patch_history_axis_margin() -> None:
    text = HISTORY_CORE_PATH.read_text(encoding='utf-8')
    if NEW_HISTORY_GEOMETRY in text:
        return
    if OLD_HISTORY_GEOMETRY not in text:
        raise RuntimeError('Anchor geometria grafico storico non trovato')
    text = text.replace(OLD_HISTORY_GEOMETRY, NEW_HISTORY_GEOMETRY, 1)
    HISTORY_CORE_PATH.write_text(text, encoding='utf-8')


def main() -> None:
    patch_dependency_semantics()
    patch_history_axis_margin()
    print(
        'Review Demografia Lotto A applicata: dipendenza = ogni 100 persone 15–64; '
        'margine asse Y ampliato per unità lunghe.'
    )


if __name__ == '__main__':
    main()
