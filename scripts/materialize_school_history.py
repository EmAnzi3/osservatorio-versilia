#!/usr/bin/env python3
"""Aggiunge in build le serie MIM per anno scolastico di alunni, alunni per classe e tempo pieno.

Legge `data/source-snapshots/mim-alunni-serie.json` (scritto da
`update_source_data.py mim-students-history`) e mette le serie nelle righe comunali;
l'ultimo anno deve coincidere con i valori pubblicati.
"""
from __future__ import annotations

import json
from pathlib import Path

import school_history as sh

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / sh.SNAPSHOT).read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Scuole: serie senza controllo di qualità")
    current = data["metrics"]["schoolStudents"]["meta"]["year"].removeprefix("a.s. ")
    if snapshot["schoolYears"][-1] != current:
        print("Scuole: serie non allineata all'anno pubblicato, non applicata")
        return
    sh.apply(data["metrics"], snapshot, sh.SNAPSHOT)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scuole: serie {snapshot['schoolYears'][0]}–{snapshot['schoolYears'][-1]} materializzata")


if __name__ == "__main__":
    main()
