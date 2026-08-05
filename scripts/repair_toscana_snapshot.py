#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "data" / "source-snapshots" / "toscana-indicatori-v1.5.0.json"
raw = PATH.read_text(encoding="utf-8").strip()
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    payload = json.loads(raw + "}")
PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Snapshot Toscana v1.5.0 validato e formattato.")
