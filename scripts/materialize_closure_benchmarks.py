#!/usr/bin/env python3
"""Aggiunge in build i confronti Toscana/Italia acquisiti nella chiusura dei confronti (un modulo per fonte).

Ogni modulo in `MODULES` espone `SNAPSHOT` (con `{year}`), `METRIC` e `apply(metric, snapshot, path)`; si usa
lo snapshot dell'anno pubblicato dell'indicatore, con qualityGate PASS. Snapshot assente: nessun confronto.
Un modulo con più indicatori espone invece `BENCHMARK` (con `{year}`), `METRICS` e
`apply_benchmark(key, metric, snapshot, path)`.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
MODULES = ("income_distribution_benchmark", "rgs_staff_history")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    applied = []
    for name in MODULES:
        module = importlib.import_module(name)
        multi = hasattr(module, "METRICS")
        for key in (module.METRICS if multi else (module.METRIC,)):
            metric = data["metrics"][key]
            rel = (module.BENCHMARK if multi else module.SNAPSHOT).format(year=metric["meta"]["year"])
            path = ROOT / rel
            if not path.exists():
                continue
            snapshot = json.loads(path.read_text(encoding="utf-8"))
            if snapshot.get("qualityGate", {}).get("status") != "PASS":
                raise RuntimeError(f"{name}: snapshot senza controllo di qualità")
            if multi:
                module.apply_benchmark(key, metric, snapshot, rel)
            else:
                module.apply(metric, snapshot, rel)
            applied.append(key)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Confronti della chiusura: " + (", ".join(applied) or "nessuno"))


if __name__ == "__main__":
    main()
