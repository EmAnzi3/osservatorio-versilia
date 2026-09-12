#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'scripts' / 'finalize_territorio_v137.py'
s = p.read_text(encoding='utf-8')
old = '    raise SystemExit(f"metriche v1.37 mancanti: {sorted(expected - set(metrics))}\n'
new = '    raise SystemExit(f"metriche v1.37 mancanti: {sorted(expected - set(metrics))}")\n'
if s.count(old) != 1:
    raise SystemExit(f'quote verifier writer: attesa 1 occorrenza, trovate {s.count(old)}')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('Verifier writer quote repaired.')
