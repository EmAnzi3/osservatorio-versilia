#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
site = json.loads((ROOT / "data/site-data.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "data/source-registry.json").read_text(encoding="utf-8"))
snapshot = json.loads((ROOT / "data/source-snapshots/istat-agricoltura-territorio-2020.json").read_text(encoding="utf-8"))

KEYS = [
    "agriculturalFarms",
    "agriculturalUsedArea",
    "averageAgriculturalFarmSize",
    "cropProfile",
    "irrigatedAgriculturalArea",
]

assert site["version"] == "v1.20.0"
assert len(site["metrics"]) == 154
assert registry["expectedMetricCount"] == 154
assert registry["expectedInlineMetricCount"] == 150
assert registry["expectedExternalMetricCount"] == 4
assert all(key in site["metrics"] for key in KEYS)
assert "organicAgriculturalAreaShare" in site["metrics"]

section = next(s for s in site["themes"]["ambiente"]["sections"] if s["key"] == "agricoltura")
assert section["label"] == "Agricoltura e territorio"
assert section["metrics"] == KEYS + ["organicAgriculturalAreaShare"]
assert site["themes"]["ambiente"]["metrics"].count("organicAgriculturalAreaShare") == 1
for key in KEYS:
    assert site["themes"]["ambiente"]["metrics"].count(key) == 1

by_code = {row["code"]: row for row in site["metrics"]["agriculturalFarms"]["rows"]}
assert by_code["046005"]["value"] == 319
assert by_code["046018"]["value"] == 192
assert by_code["046033"]["value"] == 146
assert site["metrics"]["agriculturalFarms"]["aggregate"]["value"] == 959

sau = site["metrics"]["agriculturalUsedArea"]
sau_by_code = {row["code"]: row for row in sau["rows"]}
assert math.isclose(sau_by_code["046018"]["value"], 1370.61)
expected_massarosa_share = 1370.61 / (68.2379 * 100) * 100
assert math.isclose(sau_by_code["046018"]["normalized"]["value"], expected_massarosa_share, rel_tol=1e-12)
expected_area_sum = sum(item["municipalAreaKm2"] for item in snapshot["towns"].values())
expected_local_sau = sum(item["sauLocalizedHa"] for item in snapshot["towns"].values())
assert math.isclose(sau["normalizedAggregate"]["value"], expected_local_sau / (expected_area_sum * 100) * 100, rel_tol=1e-12)
assert "31/12/2020" in sau["method"]["formula"]
assert "localizzazione dei terreni" in sau["method"]["caveat"]

avg = site["metrics"]["averageAgriculturalFarmSize"]
avg_by_code = {row["code"]: row for row in avg["rows"]}
assert math.isclose(avg_by_code["046018"]["value"], 985.12 / 191, rel_tol=1e-12)
expected_center_sau = sum(item["sauCenterHa"] for item in snapshot["towns"].values())
expected_farms_sau = sum(item["farmsWithSau"] for item in snapshot["towns"].values())
assert math.isclose(avg["aggregate"]["value"], expected_center_sau / expected_farms_sau, rel_tol=1e-12)
assert avg["meta"]["unit"] == "hectaresPerFarm"

crop = site["metrics"]["cropProfile"]
assert crop["meta"]["compositeType"] == "agricultureProfile"
crop_rows = {row["code"]: row for row in crop["rows"]}
def part(code: str, key: str):
    return next(p for p in crop_rows[code]["parts"] if p["key"] == key)

assert {p["key"] for p in crop_rows["046005"]["parts"]} == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}
assert part("046013", "VINEY")["value"] is None
assert sum(part(code, "VINEY")["value"] is not None for code in crop_rows) == 6
agg_parts = {p["key"]: p for p in crop["aggregate"]["parts"]}
assert set(agg_parts) == {"ARLAND", "OLIVOOILTR", "OLIVTTR", "VINEY", "PGRAPM"}
assert math.isclose(agg_parts["VINEY"]["value"], sum(part(code, "VINEY")["value"] for code in crop_rows if part(code, "VINEY")["value"] is not None), rel_tol=1e-12)
assert agg_parts["VINEY"]["coverage"] == "6/7"
assert math.isclose(agg_parts["OLIVTTR"]["value"], 1.63, rel_tol=1e-12) and agg_parts["OLIVTTR"]["coverage"] == "4/7"
assert part("046013", "OLIVTTR")["value"] is None
assert part("046030", "OLIVTTR")["value"] is None
assert part("046033", "OLIVTTR")["value"] is None
assert agg_parts["ARLAND"]["coverage"] == "7/7"
assert agg_parts["OLIVOOILTR"]["coverage"] == "7/7"
assert agg_parts["PGRAPM"]["coverage"] == "7/7"
assert all(int(p["coverage"].split("/")[0]) >= 6 for key,p in agg_parts.items() if key != "OLIVTTR")

irr = site["metrics"]["irrigatedAgriculturalArea"]
irr_by_code = {row["code"]: row for row in irr["rows"]}
assert math.isclose(irr_by_code["046018"]["value"], 241.67)
assert math.isclose(irr_by_code["046018"]["normalized"]["value"], 241.67 / 985.12 * 100, rel_tol=1e-12)
expected_irrig = sum(item["irrigatedAreaHa"] for item in snapshot["towns"].values())
assert math.isclose(irr["normalizedAggregate"]["value"], expected_irrig / expected_center_sau * 100, rel_tol=1e-12)
assert "centro aziendale" in irr["method"]["caveat"]

for key in KEYS:
    assert all(row.get("slug") for row in site["metrics"][key]["rows"]), key
for metric_key in ("agriculturalUsedArea", "irrigatedAgriculturalArea"):
    for row in site["metrics"][metric_key]["rows"]:
        assert row["normalized"]["unit"] == "percent"
        assert row["normalized"]["label"]


for key in KEYS:
    assert site["metrics"][key]["method"]["snapshot"].endswith("istat-agricoltura-territorio-2020.json")
    assert registry["metricOverrides"][key]["profile"] == "istat-agriculture-census-2020"
assert registry["sourceProfiles"]["istat-agriculture-census-2020"]["publisher"] == "Istat"

app00 = (ROOT / "assets/app-parts/00.txt").read_text(encoding="utf-8")
app03 = (ROOT / "assets/app-parts/03.txt").read_text(encoding="utf-8")
assert "hectaresPerFarm" in app00
assert "agricultureProfile" in app03
assert "'securityMeasures','agricultureProfile'" in app03
assert "a.displayValue===null||a.displayValue===undefined" in app03
assert "compare-chart-toolbar scale-toolbar" in app03
assert "Media comuni Versilia" in app03
visual = (ROOT / "assets/visual-grammar.js").read_text(encoding="utf-8")
assert "agricultureProfile" in visual
assert "Media semplice dei ${values.length} comuni" in visual
assert "hectares-per-farm" in visual

finalizer = (ROOT / "scripts/finalize_catalog_release.py").read_text(encoding="utf-8")
assert 'VERSION = "v1.20.0"' in finalizer
assert "EXPECTED_METRICS = 154" in finalizer
assert "EXPECTED_INLINE = 150" in finalizer

print("Agricoltura e territorio v1.20.0 verificata: media Versilia nei confronti; Vite 6/7 e olive da tavola 4/7 come eccezione approvata.")
