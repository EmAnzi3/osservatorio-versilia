#!/usr/bin/env python3
"""Keep v1.5 regression checks strict while accepting richer 7/7 coverage labels."""
from pathlib import Path
import runpy

path = Path(__file__).with_name("test_release_v150.py")
text = path.read_text(encoding="utf-8")
old = 'metric.get("method", {}).get("coverage") == "7/7",'
new = 'str(metric.get("method", {}).get("coverage", "")).startswith("7/7"),'
if new not in text:
    if old not in text:
        raise RuntimeError("Controllo copertura v1.5.0 non riconosciuto")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Compatibilità v1.5.0 aggiornata per etichette di copertura storica 7/7.")

manual_review = Path(__file__).with_name("apply_manual_review_v160.py")
if manual_review.exists():
    runpy.run_path(str(manual_review), run_name="__main__")
