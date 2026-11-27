#!/usr/bin/env python3
"""Aggiunge in build le serie annuali acquisite nella chiusura degli storici (un modulo per fonte).

Ogni modulo elencato in `MODULES` espone `SNAPSHOT`, `METRIC` e `apply(metrics, snapshot, path)`; lo
snapshot deve avere qualityGate PASS e l'ultimo anno deve coincidere con il valore pubblicato
(controllato da `apply`). Uno snapshot assente lascia l'indicatore senza serie.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
MODULES = ("waste_cost_history", "seasonality_history", "fiscal_recovery_history")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    applied = []
    for name in MODULES:
        module = importlib.import_module(name)
        path = ROOT / module.SNAPSHOT
        if not path.exists():
            continue
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        if snapshot.get("qualityGate", {}).get("status") != "PASS":
            raise RuntimeError(f"{name}: snapshot senza controllo di qualità")
        module.apply(data["metrics"], snapshot, module.SNAPSHOT)
        applied.append(f"{module.METRIC} {snapshot['years'][0]}–{snapshot['years'][-1]}")
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Serie annuali: " + (", ".join(applied) or "nessuna"))


if __name__ == "__main__":
    main()
