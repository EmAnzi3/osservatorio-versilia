from pathlib import Path

RELEASE = "v1.35.0"
METRIC_ID = "biometria-comune"
SOURCE_PATH = Path("data/sources/territorio/biometria-comune.json")
OUTPUT_PATH = Path("data/generated/biometria-comune.json")
MUNICIPALITY_ORDER = [
    "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta",
    "Seravezza", "Stazzema", "Viareggio",
]
BAND_IDS = [
    "0_299", "300_599", "600_899", "900_1199",
    "1200_1499", "1500_1999", "2000_2499", "2500_plus",
]
BAND_SUM_TOLERANCE = 0.2
