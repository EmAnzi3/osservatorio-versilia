"""Configurazione v1.36.0 — Foreste in Comune / CFI-SINFor."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOREST_SOURCE_PATH = "data/source-snapshots/foreste-in-comune-v136.json"
FOREST_METRIC_KEY = "forestCoverIndex"
FOREST_SECTION_KEY = "copertura-forestale"
EXPECTED_INPUT_METRIC_COUNT = 201
EXPECTED_RELEASE_METRIC_COUNT = 202
FOREST_RATIO_TOLERANCE_PCT = 0.0006

MUNICIPALITY_ORDER = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
