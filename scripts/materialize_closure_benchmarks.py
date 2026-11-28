#!/usr/bin/env python3
"""Aggiunge in build i confronti Toscana/Italia acquisiti nella chiusura dei confronti (un modulo per fonte).

Ogni modulo in `MODULES` espone `SNAPSHOT` (con `{year}`), `METRIC` e `apply(metric, snapshot, path)`; si usa
lo snapshot dell'anno pubblicato dell'indicatore, con qualityGate PASS. Snapshot assente: nessun confronto.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
MODULES = ("income_distribution_benchmark",)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    applied = []
    for name in MODULES:
        module = importlib.import_module(name)
        metric = data["metrics"][module.METRIC]
        rel = module.SNAPSHOT.format(year=metric["meta"]["year"])
        path = ROOT / rel
        if not path.exists():
            continue
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        if snapshot.get("qualityGate", {}).get("status") != "PASS":
            raise RuntimeError(f"{name}: snapshot senza controllo di qualità")
        module.apply(metric, snapshot, rel)
        applied.append(module.METRIC)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Confronti della chiusura: " + (", ".join(applied) or "nessuno"))


if __name__ == "__main__":
    main()
