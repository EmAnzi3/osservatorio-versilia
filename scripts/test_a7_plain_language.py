#!/usr/bin/env python3
"""Ogni codice di avvertenza o rifiuto pubblicato in Chiedi ha una lettura italiana.

Legge il runtime realmente materializzato nella build (dist/chiedi). Un nuovo
codice A6 senza traduzione fa fallire il gate invece di comparire al pubblico
come stringa tecnica. Le traduzioni sono solo di presentazione: i codici
originali restano nell'evidenza completa.
"""
import argparse
import gzip
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMITS = ROOT/'experiments/a7-guided-explorer/limits-it.mjs'
ENGLISH = re.compile(r'\b(the|and|not|of|with|is|are)\b')


def readings():
    text = LIMITS.read_text(encoding='utf-8')
    body = text[text.index('export default ')+len('export default '):].rstrip().rstrip(';')
    return json.loads(body)


def published_codes(dist):
    graphs = sorted((Path(dist)/'chiedi/explorer-preview').glob('*/package/runtime'))
    assert len(graphs) == 1, ('runtime_pubblico_non_trovato', [str(g) for g in graphs])
    codes = dict(warnings=set(), reasons=set())
    for shard in graphs[0].rglob('*.json.gz'):
        data = json.loads(gzip.decompress(shard.read_bytes()))
        for entry in data.get('entries', []) if isinstance(data, dict) else []:
            for key in codes:
                codes[key].update(entry['response'].get(key, []))
    return codes


def public_labels(dist):
    """Ogni dettaglio e ogni periodo mostrato ha un nome leggibile, senza codici."""
    from a7_public_labels import is_public
    graph = sorted((Path(dist)/'chiedi/explorer-preview').glob('*/presentation.mjs'))
    assert len(graph) == 1, 'presentazione_non_trovata'
    text = graph[0].read_text(encoding='utf-8')
    meta = json.loads(text[len('export default '):].rstrip().rstrip(';'))
    runtime = graph[0].parent/'package/runtime'
    views = raw = 0; raw = []; raw_periods = set(); count = 0
    plain = re.compile(r'\d{4}([-/]\d{2,4})?|\d{4}-\d{2}-\d{2}')
    for shard in runtime.rglob('*.json.gz'):
        data = json.loads(gzip.decompress(shard.read_bytes()))
        if not isinstance(data, dict):
            continue
        if 'declaration' in data:
            for view in data['views']:
                count += 1
                if view['dimension'] == 'total':
                    continue
                label = meta['metrics'].get(data['metric'], {}).get('views', {}).get(view['dimension'])
                if not label or not is_public(label):
                    raw.append((data['metric'], view['dimension'], label))
        for entry in data.get('entries', []):
            for observation in entry['response'].get('observations', []):
                period = str(observation.get('period'))
                shown = meta.get('periods', {}).get(period, period)
                if not plain.fullmatch(period) and not is_public(shown):
                    raw_periods.add(period)
    return dict(views=count, raw=raw, rawPeriods=sorted(raw_periods))


def verify(dist):
    texts = readings()
    codes = published_codes(dist)
    assert codes['warnings'] and codes['reasons'], 'runtime_senza_codici'
    missing = {key: sorted(c for c in codes[key] if c not in texts[key] and c not in texts['warnings'])
               for key in codes}
    assert not any(missing.values()), ('codici_senza_lettura_italiana', missing)
    for key, table in texts.items():
        for code, reading in table.items():
            assert isinstance(reading, str) and 15 <= len(reading) <= 220, (code, reading)
            assert (reading[0].isupper() or reading[0] == '«') and reading.endswith('.'), (code, reading)
            assert not ENGLISH.search(reading), ('lettura_non_italiana', code, reading)
    labels = public_labels(dist)
    assert labels['views'] and not labels['raw'], ('dettagli_senza_nome_leggibile', labels['raw'][:10])
    assert not labels['rawPeriods'], ('periodi_in_codice', labels['rawPeriods'][:10])
    # Il browser importa il modulo: deve restare JavaScript valido.
    subprocess.run(['node', '--check', str(LIMITS)], check=True)
    return dict({key: len(codes[key]) for key in codes}, views=labels['views'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=ROOT/'dist')
    counts = verify(parser.parse_args().dist)
    print(f"A7 letture italiane PASS: {counts['warnings']} avvertenze e {counts['reasons']} motivi tradotti; {counts['views']} dettagli con nome leggibile")
