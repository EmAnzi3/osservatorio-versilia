#!/usr/bin/env python3
"""Aggiunge in build la serie 2018–2025 di motorizzazione e quota Euro 0–3 (archivi ACI).

Legge `data/source-snapshots/aci-autovetture-serie.json` (scritto da
`update_source_data.py aci-vehicles-history`) e mette la serie nelle righe comunali; l'ultimo
anno deve coincidere con il valore pubblicato.
"""
from __future__ import annotations

import json
from pathlib import Path

import vehicles_history as vh

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / vh.SNAPSHOT).read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Parco autovetture: serie senza controllo di qualità")
    if str(snapshot["years"][-1]) != str(data["metrics"]["motorization"]["meta"]["year"]):
        print("Parco autovetture: serie non allineata all'anno pubblicato, non applicata")
        return
    vh.apply(data["metrics"], snapshot, vh.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Parco autovetture: serie {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
