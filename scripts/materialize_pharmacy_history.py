#!/usr/bin/env python3
"""Aggiunge in build la serie 2019–2025 delle farmacie ogni 1.000 residenti.

Legge `data/source-snapshots/salute-farmacie-serie.json` (scritto da `update_source_data.py
salute-pharmacies-history`): sedi valide al 31 dicembre per Comune, con il 2025 identico ai conteggi
pubblicati. Il denominatore è la serie pubblicata dei residenti al 1° gennaio dell'anno successivo;
l'ultimo anno deve coincidere con il valore pubblicato. Senza snapshot la serie non si applica.
"""
from __future__ import annotations

import json
from pathlib import Path

import pharmacy_history as ph

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    path = ROOT / ph.SNAPSHOT
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if ph.METRIC not in data["metrics"] or not path.exists():
        print("Farmacie: snapshot della serie assente, serie non applicata")
        return
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot["qualityGate"]["status"] != "PASS":
        raise RuntimeError("Farmacie: snapshot della serie non valido")
    published = ph.published_counts(json.loads((ROOT / ph.PUBLISHED).read_text(encoding="utf-8")))
    if {c: v[-1] for c, v in snapshot["counts"].items()} != published:
        raise RuntimeError("Farmacie: 2025 della serie diverso dai conteggi pubblicati")
    ph.apply(data["metrics"], snapshot, ph.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Farmacie: serie {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
