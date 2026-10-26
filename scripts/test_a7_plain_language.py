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
    # Il browser importa il modulo: deve restare JavaScript valido.
    subprocess.run(['node', '--check', str(LIMITS)], check=True)
    return {key: len(codes[key]) for key in codes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=ROOT/'dist')
    counts = verify(parser.parse_args().dist)
    print(f"A7 letture italiane PASS: {counts['warnings']} avvertenze e {counts['reasons']} motivi pubblicati, tutti tradotti")
