#!/usr/bin/env python3
"""Build raw annual mean daily Tmin/Tmax series from ERA5-Land daily statistics.

The output is RAW REANALYSIS. It is intentionally built for the LaMMA overlap
and the post-LaMMA period, then calibrated additively against LaMMA 1995-2015.

Definitions match the LaMMA indicators:
- tmin_mean_c = annual mean of daily minimum 2 m temperature;
- tmax_mean_c = annual mean of daily maximum 2 m temperature.

ERA5-Land daily statistics are derived from the hourly 2 m temperature at
1-hour sampling. Municipal aggregation uses fractional intersection weights
against ISTAT 2026 boundaries, consistently with the other ERA5-Land scripts.
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
import tempfile
from pathlib import Path

import cdsapi
import numpy as np
import pandas as pd

from era5_land_annual_history import (
    AREA,
    ISTAT_URL,
    TARGETS,
    download,
    extract_zip,
    find_municipal_layer,
    fractional_weights,
    weighted_grid_value,
)
from era5_land_ytd import DAILY_DATASET, read_field, retrieve_with_retry


def retrieve_stat_chunk(
    client: cdsapi.Client,
    years: list[int],
    statistic: str,
    target: Path,
) -> None:
    request = {
        "product_type": "reanalysis",
        "variable": ["2m_temperature"],
        "year": [str(year) for year in years],
        "month": [f"{month:02d}" for month in range(1, 13)],
        "day": [f"{day:02d}" for day in range(1, 32)],
        "daily_statistic": statistic,
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": AREA,
    }
    label = f"{statistic} {years[0]}-{years[-1]}"
    retrieve_with_retry(client, DAILY_DATASET, request, target, label, attempts=3)


def annual_grid(times: pd.DatetimeIndex, values: np.ndarray, year: int) -> np.ndarray:
    keep = np.asarray(times.year == year)
    annual = values[keep]
    expected = 366 if calendar.isleap(year) else 365
    if annual.shape[0] != expected:
        raise RuntimeError(f"ERA5 daily statistics {year}: expected {expected} days, got {annual.shape[0]}")
    return np.nanmean(annual - 273.15, axis=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1995)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--chunk-years", type=int, default=5)
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-minmax-annual-raw.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")
    if args.end_year < args.start_year:
        raise SystemExit("end-year must be >= start-year")
    if args.chunk_years < 1:
        raise SystemExit("chunk-years must be >= 1")

    client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=token)
    rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="era5-minmax-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()

        years_all = list(range(args.start_year, args.end_year + 1))
        weights = None
        lat_ref = lon_ref = None

        for offset in range(0, len(years_all), args.chunk_years):
            years = years_all[offset:offset + args.chunk_years]
            paths = {
                "tmin": tmp / f"daily-min-{years[0]}-{years[-1]}.download",
                "tmax": tmp / f"daily-max-{years[0]}-{years[-1]}.download",
            }
            print(f"[era5-minmax] retrieving daily minimum {years[0]}-{years[-1]}", flush=True)
            retrieve_stat_chunk(client, years, "daily_minimum", paths["tmin"])
            print(f"[era5-minmax] retrieving daily maximum {years[0]}-{years[-1]}", flush=True)
            retrieve_stat_chunk(client, years, "daily_maximum", paths["tmax"])

            tmin_times, tmin_values, lat_min, lon_min = read_field(
                paths["tmin"], ("t2m", "2m_temperature", "2 metre temperature")
            )
            tmax_times, tmax_values, lat_max, lon_max = read_field(
                paths["tmax"], ("t2m", "2m_temperature", "2 metre temperature")
            )
            if not (np.array_equal(lat_min, lat_max) and np.array_equal(lon_min, lon_max)):
                raise RuntimeError("ERA5 daily minimum/maximum grids differ")
            if lat_ref is None:
                lat_ref, lon_ref = lat_min, lon_min
                weights = fractional_weights(subset, name_col, lat_ref, lon_ref)
            elif not (np.array_equal(lat_ref, lat_min) and np.array_equal(lon_ref, lon_min)):
                raise RuntimeError("ERA5 grid changed between chunks")

            assert weights is not None
            for year in years:
                min_grid = annual_grid(tmin_times, tmin_values, year)
                max_grid = annual_grid(tmax_times, tmax_values, year)
                for name in TARGETS:
                    rows.append({
                        "municipality": name,
                        "year": year,
                        "period_status": "complete",
                        "source": "ERA5-Land post-processed daily statistics",
                        "method": "daily min/max from hourly 2m temperature; fractional municipal area weighting; raw reanalysis",
                        "tmin_mean_c": weighted_grid_value(min_grid, weights[name]),
                        "tmax_mean_c": weighted_grid_value(max_grid, weights[name]),
                    })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).sort_values(["municipality", "year"])
    frame.to_csv(out, index=False)
    out.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "dataset": DAILY_DATASET,
                "years": [args.start_year, args.end_year],
                "status": "raw ERA5-Land reanalysis; calibrate against LaMMA 1995-2015 before publication",
                "definitions": {
                    "tmin_mean_c": "annual mean of daily minimum 2m temperature",
                    "tmax_mean_c": "annual mean of daily maximum 2m temperature",
                },
                "daily_statistics": ["daily_minimum", "daily_maximum"],
                "frequency": "1_hourly",
                "time_zone": "UTC+00:00",
                "municipal_weighting": "fractional intersection of ERA5 cells with ISTAT 2026 municipal polygons",
                "municipalities": TARGETS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[era5-minmax] wrote {len(frame)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
