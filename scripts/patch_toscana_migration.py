#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "update_toscana_indicators_v150.py"
text = path.read_text(encoding="utf-8")
old = "landslideExposure: ['frane', 'rischio frana', 'dissesto']"
new = "landslideExposure: ['frane', 'rischio geomorfologico']"
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise RuntimeError("Pattern ambientale non trovato nella migrazione")
path.write_text(text, encoding="utf-8")
print("Migrazione Toscana allineata ai sorgenti correnti.")
