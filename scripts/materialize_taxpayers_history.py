#!/usr/bin/env python3
"""Aggiunge in build la serie per anno d'imposta dei contribuenti MEF ogni 100 maggiorenni.

Legge `data/source-snapshots/mef-contribuenti-serie.json` (scritto da
`update_source_data.py mef-taxpayers-history`) e mette la serie nelle righe comunali;
l'ultimo anno deve coincidere con il valore pubblicato.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import taxpayers_history as tx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / tx.SNAPSHOT).read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Contribuenti: serie senza controllo di qualità")
    current = re.search(r"a\.i\. (20\d\d)", data["metrics"][tx.METRIC]["meta"]["year"]).group(1)
    if str(snapshot["years"][-1]) != current:
        print("Contribuenti: serie non allineata all'anno pubblicato, non applicata")
        return
    tx.apply(data["metrics"], snapshot, tx.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Contribuenti: serie {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
