#!/usr/bin/env python3
"""Corregge una sola volta il guard di idempotenza README nel materializzatore agricoltura."""
from pathlib import Path

path = Path(__file__).with_name("materialize_agricoltura_territorio_v120.py")
text = path.read_text(encoding="utf-8")
old = "    text = text.replace(old_cov, new_cov)"
new = "    if new_cov not in text:\n        text = text.replace(old_cov, new_cov)"

if new in text:
    print("Guard idempotenza già presente.")
elif old not in text:
    raise RuntimeError("Pattern README non trovato nel materializzatore agricoltura")
else:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Guard idempotenza applicato al materializzatore agricoltura.")
