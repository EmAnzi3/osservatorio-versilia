"""Snapshot ASIA-UL in uso: l'anno più recente versionato per ciascuna famiglia.

L'aggiornatore `update_source_data.py istat-asia --year AAAA` scrive tre file per anno
(serie comunali, benchmark Toscana/Italia, classi dimensionali); build, companion e
adattatore A6 leggono qui quale usare, senza anni scritti nel codice.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = "data/source-snapshots/"


def latest(prefix: str, fallback: str | None = None) -> str:
    """Percorso relativo del file `<prefix>AAAA.json` con l'anno più alto (o `fallback`)."""
    years = [int(m.group(1)) for p in (ROOT / SNAP).glob(prefix + "*.json")
             if (m := re.fullmatch(re.escape(prefix) + r"(\d{4})\.json", p.name))]
    if years:
        return f"{SNAP}{prefix}{max(years)}.json"
    if fallback is None:
        raise FileNotFoundError(f"nessuno snapshot {prefix}AAAA.json")
    return SNAP + fallback


TOWNS = latest("istat-asia-ul-", "agid-asia-agcom-2026-08.json")
BUSINESS = latest("a3-istat-business-benchmark-")
MICRO = latest("a3-istat-micro-units-benchmark-")
