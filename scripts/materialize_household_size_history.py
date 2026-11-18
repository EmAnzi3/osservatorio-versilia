#!/usr/bin/env python3
"""Sostituisce in build il numero medio di componenti per famiglia con la serie comunale Istat.

Fonte unica per Comuni, Versilia, Toscana e Italia: il workbook «A misura di Comune ·
Famiglie» congelato in `data/source-snapshots/istat-famiglie-serie-AAAA.json` (scritto da
`update_source_data.py istat-famiglie`). Prima il valore comunale veniva da un'altra
tavola censuaria e il confronto toscano da questo workbook.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import household_size_history as hh

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"


def latest_snapshot(root: Path | None = None) -> str:
    found = ((root or ROOT) / "data" / "source-snapshots").glob("istat-famiglie-serie-*.json")
    years = sorted((int(m.group(1)), p.name) for p in found if (m := re.fullmatch(r"istat-famiglie-serie-(20\d\d)\.json", p.name)))
    if not years:
        raise RuntimeError("Famiglie: nessuno snapshot della serie")
    return f"data/source-snapshots/{years[-1][1]}"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    path = latest_snapshot()
    snapshot = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if snapshot.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Famiglie: snapshot senza controllo di qualità")
    hh.apply(data["metrics"][hh.METRIC], snapshot, path)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Componenti per famiglia: serie {snapshot['years'][0]}–{snapshot['years'][-1]} materializzata")


if __name__ == "__main__":
    main()
