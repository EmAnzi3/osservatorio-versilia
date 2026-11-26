#!/usr/bin/env python3
"""Aggiunge in build la serie semestrale delle medie OMI per Comune (vendita e affitto).

Legge `data/source-snapshots/omi-residential-serie.json` (scritto da
`update_source_data.py omi-history`) e mette in `componentSeries` le serie `sale` e `rent`
(la serie predefinita è la vendita); il semestre pubblicato deve coincidere con le medie del catalogo.
"""
from __future__ import annotations

import json
from pathlib import Path

import omi_history as ih

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    path = ROOT / ih.SNAPSHOT
    if not path.exists():
        print("Serie OMI: snapshot assente, nessuna serie")
        return
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Serie OMI: snapshot senza controllo di qualità")
    import update_omi as omi
    if snapshot["lastSemester"] != omi.label_semester(data["metrics"][ih.METRIC]["meta"]["year"]):
        print("Serie OMI: serie non allineata al semestre pubblicato, non applicata")
        return
    ih.apply(data["metrics"], snapshot, ih.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Serie OMI: semestri comuni {snapshot['commonSemesters'][0]}–{snapshot['commonSemesters'][-1]} materializzati")


if __name__ == "__main__":
    main()
