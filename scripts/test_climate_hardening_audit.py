#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("climate_hardening_audit.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def synthetic():
    towns = ["A", "B"]
    years = list(range(1975, 2026))
    current = {"municipalities": {}}
    era_rows, lamma_rows = [], []
    for i, town in enumerate(towns):
        temperature = [12 + i + 0.02 * (year - 1975) for year in years]
        precipitation = [1000 + i * 100 + 2 * (year - 1975) for year in years]
        current["municipalities"][town] = {
            "years": years,
            "temperature": [value + 0.3 for value in temperature],
            "precipitation": [value * 1.1 for value in precipitation],
        }
        for year, tmean, precip in zip(years, temperature, precipitation):
            era_rows.append({"municipality": town, "year": year, "tmean_c": tmean, "precip_mm": precip})
            if 1995 <= year <= 2015:
                lamma_rows.append({"municipality": town, "year": year, "tmean_c": tmean + 0.3, "precip_mm": precip * 1.1})
    return pd.DataFrame(lamma_rows), pd.DataFrame(era_rows), current


def main():
    lamma, era5, current = synthetic()
    candidate, diagnostics, rows = audit.build_candidate(lamma, era5, current)
    assert candidate["coverage"] == {"from": 1975, "to": 2025}
    assert set(candidate["municipalities"]) == {"A", "B"}
    assert len(rows) == 102
    for town in ("A", "B"):
        calibration = candidate["municipalities"][town]["calibration"]
        assert abs(calibration["temperature_offset_full_overlap_c"] - 0.3) < 1e-6
        assert abs(calibration["precipitation_ratio_full_overlap"] - 1.1) < 1e-6
        assert abs(diagnostics["municipalities"][town]["temperature"]["trend_delta_change_c"]) < 1e-8
    summary = audit.overall_summary(diagnostics)
    assert summary["publication_decision"] == "manual_review_required"
    print("climate hardening synthetic audit OK")


if __name__ == "__main__":
    main()
