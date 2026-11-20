#!/usr/bin/env python3
"""Aggiunge in build la serie 2018–2024 della quota di unità locali con meno di 10 addetti.

Legge `data/source-snapshots/istat-micro-unita-serie.json` (scritto da
`update_source_data.py asia-micro-units-history`); i totali devono coincidere con la serie
pubblicata delle unità locali e l'ultimo anno con il valore corrente.
"""
from __future__ import annotations

import json
from pathlib import Path

import micro_units_history as mu

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / mu.SNAPSHOT).read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Micro unità: serie senza controllo di qualità")
    if str(snapshot["years"][-1]) != str(data["metrics"][mu.METRIC]["meta"]["year"]):
        print("Micro unità: serie non allineata all'anno pubblicato, non applicata")
        return
    mu.apply(data["metrics"], snapshot, mu.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Micro unità: serie {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
