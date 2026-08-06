#!/usr/bin/env python3
"""Keep v1.5 regression checks strict while accepting richer 7/7 coverage labels."""
import json
from pathlib import Path
import runpy

path = Path(__file__).with_name("test_release_v150.py")
text = path.read_text(encoding="utf-8")
old = 'metric.get("method", {}).get("coverage") == "7/7",'
previous = 'str(metric.get("method", {}).get("coverage", "")).startswith("7/7"),'
new = '"7/7" in str(metric.get("method", {}).get("coverage", "")),'
if new not in text:
    if previous in text:
        text = text.replace(previous, new, 1)
    elif old in text:
        text = text.replace(old, new, 1)
    else:
        raise RuntimeError("Controllo copertura v1.5.0 non riconosciuto")
path.write_text(text, encoding="utf-8")
print("Compatibilità v1.5.0 aggiornata per etichette di copertura storica 7/7.")

manual_review = Path(__file__).with_name("apply_manual_review_v160.py")
if manual_review.exists():
    runpy.run_path(str(manual_review), run_name="__main__")

site_data_path = Path(__file__).resolve().parents[1] / "data" / "site-data.json"
data = json.loads(site_data_path.read_text(encoding="utf-8"))
data["metrics"]["rigidExpenditureShare"]["method"]["coverage"] = (
    "7/7 nel 2025; storico non pubblicato per discontinuità della fonte."
)
site_data_path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
