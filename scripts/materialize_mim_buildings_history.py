#!/usr/bin/env python3
"""Aggiunge in build la serie dei cinque indicatori dell'edilizia scolastica MIM.

Legge `data/source-snapshots/mim-edilizia-scolastica-serie.json` (scritto da
`update_source_data.py mim-buildings-history`) e mette in `componentSeries` la serie di ciascuna
voce del selettore (la serie predefinita è la prima voce); l'anno 2024/25 deve coincidere con i
valori pubblicati.
"""
from __future__ import annotations

import json
from pathlib import Path

import mim_buildings_history as mh

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    path = ROOT / mh.SNAPSHOT
    if not path.exists():
        print("Serie edilizia scolastica: snapshot assente, nessuna serie")
        return
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Serie edilizia scolastica: snapshot senza controllo di qualità")
    mh.apply(data["metrics"], snapshot, mh.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Serie edilizia scolastica: " + ", ".join(f"{k} {v[0]}–{v[-1]}" for k, v in snapshot["years"].items()))


if __name__ == "__main__":
    main()
