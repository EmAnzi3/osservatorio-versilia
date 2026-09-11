from pathlib import Path

RELEASE = "v1.35.0"
SOURCE_PATH = Path("data/source-snapshots/biometria-comune-v135.json")
MUNICIPALITY_ORDER = [
    "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta",
    "Seravezza", "Stazzema", "Viareggio",
]
BAND_IDS = [
    "0_299", "300_599", "600_899", "900_1199",
    "1200_1499", "1500_1999", "2000_2499", "2500_plus",
]
BAND_SUM_TOLERANCE = 0.2
NEW_METRIC_KEYS = ("municipalSurface", "populationDensity", "altitudeProfile")
SECTION_KEY = "profilo-territoriale"
