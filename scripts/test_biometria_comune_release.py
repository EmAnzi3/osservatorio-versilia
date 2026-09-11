#!/usr/bin/env python3
"""Contratto dati e architettura v1.35.0 — Biometria del comune."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from biometria_comune_config import (
    BAND_IDS,
    BAND_SUM_TOLERANCE,
    MUNICIPALITY_ORDER,
    NEW_METRIC_KEYS,
    SECTION_KEY,
    SOURCE_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / SOURCE_PATH


def load_materializer():
    path = ROOT / "scripts" / "materialize_biometria_comune_release.py"
    spec = importlib.util.spec_from_file_location("biometria_v135", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert list(snapshot["municipalities"]) == MUNICIPALITY_ORDER
    for town, row in snapshot["municipalities"].items():
        bands = row["altitudeBandsPct"]
        assert list(bands) == BAND_IDS, town
        values = list(bands.values())
        assert all(0 <= value <= 100 for value in values), town
        assert abs(sum(values) - 100) <= BAND_SUM_TOLERANCE + 1e-9, (town, sum(values))
        assert round(sum(values[:2]), 1) == row["below600Pct"], town
        assert round(sum(values[1:]), 1) == row["from300Pct"], town
        assert row["altitudeMinM"] is None and row["altitudeMeanM"] is None and row["altitudeMaxM"] is None
        assert row["altitudeStatus"] == "pending-istat-2021-xlsx"

    site = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    module = load_materializer()
    metrics = module.build_metrics(site, snapshot)
    assert tuple(metrics) == NEW_METRIC_KEYS
    assert metrics["municipalSurface"]["meta"]["theme"] == "ambiente"
    assert metrics["populationDensity"]["meta"]["unit"] == "peoplePerSquareKm"
    altitude = metrics["altitudeProfile"]
    assert altitude["meta"]["compositeType"] == "distribution"
    assert altitude["meta"]["summaryLabel"] == "Territorio da 300 m in su"
    assert all(len(row["parts"]) == 8 for row in altitude["rows"])
    assert all(row["altitudeStats"]["minM"] is None for row in altitude["rows"])

    population = {row["town"]: float(row["value"]) for row in site["metrics"]["population"]["rows"]}
    for row in metrics["populationDensity"]["rows"]:
        area = snapshot["municipalities"][row["town"]]["surfaceKm2"]
        assert abs(row["value"] - population[row["town"]] / area) < 1e-9

    total_area = sum(item["surfaceKm2"] for item in snapshot["municipalities"].values())
    expected_first = sum(
        item["surfaceKm2"] * item["altitudeBandsPct"]["0_299"] / 100
        for item in snapshot["municipalities"].values()
    ) / total_area * 100
    assert abs(altitude["aggregate"]["parts"][0]["value"] - expected_first) < 1e-9

    test_site = json.loads(json.dumps(site))
    test_site["metrics"].update(metrics)
    module.install_environment_section(test_site)
    environment = test_site["themes"]["ambiente"]
    assert environment["sections"][0]["key"] == SECTION_KEY
    assert environment["sections"][0]["metrics"] == list(NEW_METRIC_KEYS)
    assert all(key in environment["metrics"] for key in NEW_METRIC_KEYS)

    runtime = (ROOT / "scripts" / "patch_biometria_runtime.py").read_text(encoding="utf-8")
    assert "squareKm" in runtime and "peoplePerSquareKm" in runtime
    assert not (ROOT / "assets" / "biometria-v135.css").exists()
    assert not (ROOT / "assets" / "biometria-v135.js").exists()
    assert not (ROOT / "confronta" / "ambiente" / "biometria").exists()
    print("Biometria v1.35.0: dati 7/7, aggregazioni e architettura canonica OK")


if __name__ == "__main__":
    main()
