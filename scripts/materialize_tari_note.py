#!/usr/bin/env python3
"""Nota in build sulla TARI standardizzata: perché non ha un confronto Toscana/Italia.

Decisione del 26/11/2026: non esiste una stima ufficiale della TARI di una famiglia tipo per
Toscana e Italia che copra almeno il 90% dei residenti (le medie Cittadinanzattiva riguardano
solo i capoluoghi). Il confronto ufficiale disponibile è il costo del servizio ISPRA
(`wasteServiceCost`), che misura un'altra grandezza; la scheda lo dice in nota.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
NOTE = ("Non esiste una stima ufficiale della TARI di una famiglia tipo per Toscana e Italia che copra almeno il 90% dei residenti: "
        "per un confronto con Toscana e Italia vedi il costo totale del servizio rifiuti per abitante (ISPRA), che misura il costo "
        "del servizio e non la bolletta.")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    metrics = data["metrics"]
    if "wasteServiceCost" not in metrics or not (metrics["wasteServiceCost"]["meta"].get("benchmark") or {}).get("tuscany"):
        raise RuntimeError("Nota TARI: confronto ISPRA del costo del servizio assente")
    method = metrics["tariStandardHousehold"]["method"]
    if NOTE not in method.get("caveat", ""):
        method["caveat"] = (method.get("caveat", "").rstrip() + " " + NOTE).strip()
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Nota TARI: rimando al costo del servizio ISPRA")


if __name__ == "__main__":
    main()
