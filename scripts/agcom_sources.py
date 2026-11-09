"""Snapshot AGCOM FTTH in uso: l'edizione più recente della Broadband Map.

L'aggiornatore `update_source_data.py agcom-ftth` scrive due file per edizione
(record comunali del CSV primario e benchmark Toscana/Italia), con la data di
riferimento AGCOM nel nome; build e adattatore A6 leggono qui quale usare.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = "data/source-snapshots/"


def latest(prefix: str, fallback: str) -> str:
    """Percorso relativo del file `<prefix>AAAA-MM-GG.json` più recente (o `fallback`)."""
    dates = sorted(m.group(1) for p in (ROOT / SNAP).glob(prefix + "*.json")
                   if (m := re.fullmatch(re.escape(prefix) + r"(\d{4}-\d{2}-\d{2})\.json", p.name)))
    return f"{SNAP}{prefix}{dates[-1]}.json" if dates else SNAP + fallback


NATIVE = latest("agcom-ftth-", "agid-asia-agcom-2026-08.json")
BENCHMARK = latest("a3-agcom-benchmark-", "a3-agcom-benchmark-2025.json")
