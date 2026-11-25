#!/usr/bin/env python3
"""Aggiunge in build la serie delle quote di dichiaranti nelle quattro fasce di reddito.

Legge `data/source-snapshots/mef-fasce-reddito-serie.json` (scritto da
`update_source_data.py mef-income-distribution-history`) e mette la serie di ciascuna fascia in
`componentSeries` (`part-0`…`part-3`; la serie predefinita è «fino a 15.000 €»); l'ultimo anno deve
coincidere con le quote pubblicate.
"""
from __future__ import annotations

import json
from pathlib import Path

import income_distribution_history as ih

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    path = ROOT / ih.SNAPSHOT
    if not path.exists():
        print("Serie fasce di reddito: snapshot assente, nessuna serie")
        return
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Serie fasce di reddito: snapshot senza controllo di qualità")
    if str(snapshot["years"][-1]) != str(data["metrics"][ih.METRIC]["meta"]["year"]):
        print("Serie fasce di reddito: serie non allineata all'anno pubblicato, non applicata")
        return
    ih.apply(data["metrics"], snapshot, ih.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Serie fasce di reddito: {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
