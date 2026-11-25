#!/usr/bin/env python3
"""Aggiunge in build la serie dell'addizionale comunale IRPEF nei tre scenari di reddito.

Legge `data/source-snapshots/mef-irpef-serie.json` (scritto da
`update_source_data.py mef-irpef-history`) e mette la serie di ciascuno scenario in
`componentSeries` (la serie predefinita è lo scenario 20.000 €); l'ultimo anno deve coincidere
con i valori pubblicati.
"""
from __future__ import annotations

import json
from pathlib import Path

import irpef_history as ih

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    path = ROOT / ih.SNAPSHOT
    if not path.exists():
        print("Serie addizionale IRPEF: snapshot assente, nessuna serie")
        return
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Serie addizionale IRPEF: snapshot senza controllo di qualità")
    if str(snapshot["years"][-1]) != str(data["metrics"][ih.METRIC]["meta"]["year"]):
        print("Serie addizionale IRPEF: serie non allineata all'anno pubblicato, non applicata")
        return
    ih.apply(data["metrics"], snapshot, ih.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Serie addizionale IRPEF: {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
