"""Configurazione v1.36.0 — profilo territoriale e UCS."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "data/source-snapshots/territorio-ucs-v136.json"

MUNICIPALITY_ORDER = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
YEARS = [2007, 2010, 2013, 2016, 2019]
MACRO_KEYS = [
    "artificialized",
    "agricultural",
    "forest_seminatural_total",
    "wetlands",
    "water",
]
DETAIL_KEYS = [
    "forest",
    "seminativi",
    "permanent_crops",
    "seminatural_nonforest",
    "urban_green_cartographic",
]
NEW_METRIC_KEYS = (
    "territorialClassification",
    "statisticalCoastlineLength",
    "landCoverProfile",
)
PROFILE_SECTION_KEY = "profilo-territoriale"
LAND_COVER_SECTION_KEY = "uso-copertura-suolo"
EXPECTED_BASE_METRIC_COUNT = 198
EXPECTED_RELEASE_METRIC_COUNT = 201
MACRO_SUM_TOLERANCE_PCT = 0.01
VALUE_TOLERANCE = 1e-4
