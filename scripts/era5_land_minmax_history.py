#!/usr/bin/env python3
"""Build raw annual mean daily Tmin/Tmax series from ERA5-Land daily statistics.

The output is RAW REANALYSIS. It is intentionally built for the LaMMA overlap
and the post-LaMMA period, then calibrated additively against LaMMA 1995-2015.

Definitions match the LaMMA indicators:
- tmin_mean_c = annual mean of daily minimum 2 m temperature;
- tmax_mean_c = annual mean of daily maximum 2 m temperature.

Daily minima/maxima are requested from Copernicus' official post-processed
ERA5-Land daily-statistics product, using 1-hour sampling of the native hourly
2 m temperature. Municipal aggregation uses fractional intersection weights
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
    choose_var,
    download,
    extract_zip,
    find_municipal_layer,
    fractional_weights,
    normalize_coords,
    open_download,
    weighted_grid_value,
)
from era5_land_ytd import DAILY_DATASET, retrieve_with_retry


def annual_daily_request(year: int, statistic: str) -> dict:
    return {
        "variable": ["2m_temperature"],
        "year": str(year),
        "month": [f"{month:02d}" for month in range(1, 13)],
        "day": [f"{day:02d}" for day in range(1, 32)],
        "daily_statistic": statistic,
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": AREA,
    }


def retrieve_daily_year(
    client: cdsapi.Client,
    year: int,
    statistic: str,
    target: Path,
) -> None:
    retrieve_with_retry(
        client,
        DAILY_DATASET,
        annual_daily_request(year, statistic),
        target,
        f"{statistic} 2m temperature {year}",
        attempts=3,
    )


def read_daily_temperature(path: Path) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    ds = open_download(path)
    try:
        da = normalize_coords(
            choose_var(ds, ("t2m", "2m_temperature", "2 metre temperature"))
        ).transpose("time", "latitude", "longitude")
        times = pd.DatetimeIndex(pd.to_datetime(da["time"].values))
        values = np.asarray(da.values, dtype=float)
        latitudes = np.asarray(da["latitude"].values, dtype=float)
        longitudes = np.asarray(da["longitude"].values, dtype=float)
    finally:
        ds.close()

    order = np.argsort(times.values)
    return times[order], values[order], latitudes, longitudes


def annual_stat_grid(
    client: cdsapi.Client,
    year: int,
    statistic: str,
    tmp: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    target = tmp / f"{statistic}-{year}.download"
    print(f"[era5-minmax] retrieving official {statistic} for {year}", flush=True)
    retrieve_daily_year(client, year, statistic, target)
    times, values_kelvin, latitudes, longitudes = read_daily_temperature(target)

    expected_days = 366 if calendar.isleap(year) else 365
    expected_index = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    naive = times.tz_localize(None) if times.tz is not None else times
    normalized = naive.normalize()
    if len(normalized) != expected_days or not normalized.equals(expected_index):
        missing = expected_index.difference(normalized)
        duplicates = int(normalized.duplicated().sum())
        raise RuntimeError(
            f"ERA5-Land {statistic} {year}: expected {expected_days} daily values, "
            f"got {len(normalized)}; missing={len(missing)}, duplicates={duplicates}"
        )

    celsius = values_kelvin - 273.15
    return np.nanmean(celsius, axis=0), latitudes, longitudes


def annual_grids(
    client: cdsapi.Client,
    year: int,
    tmp: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    min_grid, min_lat, min_lon = annual_stat_grid(client, year, "daily_minimum", tmp)
    max_grid, max_lat, max_lon = annual_stat_grid(client, year, "daily_maximum", tmp)
    if not (np.array_equal(min_lat, max_lat) and np.array_equal(min_lon, max_lon)):
        raise RuntimeError(f"ERA5-Land daily min/max grid mismatch in {year}")
    return min_grid, max_grid, min_lat, min_lon


def write_output(rows: list[dict], output: Path, start_year: int, end_year: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).sort_values(["municipality", "year"])
    frame.to_csv(output, index=False)
    output.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "dataset": DAILY_DATASET,
                "years": [start_year, end_year],
                "status": "raw ERA5-Land reanalysis; calibrate against LaMMA 1995-2015 before publication",
                "definitions": {
                    "tmin_mean_c": "annual mean of official daily minimum 2m temperature",
                    "tmax_mean_c": "annual mean of official daily maximum 2m temperature",
                },
                "temporal_method": (
                    "Copernicus ERA5-Land post-processed daily minimum/maximum from native hourly "
                    "2m temperature, 1-hour sampling, UTC+00:00; annual mean computed locally"
                ),
                "frequency": "1_hourly source sampling; daily post-processing",
                "time_zone": "UTC+00:00",
                "municipal_weighting": "fractional intersection of ERA5 cells with ISTAT 2026 municipal polygons",
                "area": AREA,
                "municipalities": TARGETS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[era5-minmax] wrote {len(frame)} rows -> {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1995)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--chunk-years", type=int, default=1, help="Compatibility option; processing remains year-by-year.")
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-minmax-annual-raw.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")
    if args.end_year < args.start_year:
        raise SystemExit("end-year must be >= start-year")

    client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=token)
    rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="era5-minmax-daily-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()

        weights = None
        lat_ref = lon_ref = None

        for year in range(args.start_year, args.end_year + 1):
            min_grid, max_grid, latitudes, longitudes = annual_grids(client, year, tmp)
            if lat_ref is None:
                lat_ref, lon_ref = latitudes, longitudes
                weights = fractional_weights(subset, name_col, lat_ref, lon_ref)
            elif not (
                np.array_equal(lat_ref, latitudes)
                and np.array_equal(lon_ref, longitudes)
            ):
                raise RuntimeError("ERA5-Land grid changed between years")

            assert weights is not None
            for name in TARGETS:
                rows.append(
                    {
                        "municipality": name,
                        "year": year,
                        "period_status": "complete",
                        "source": "Copernicus ERA5-Land post-processed daily statistics",
                        "method": (
                            "official daily min/max from 1-hourly 2m-temperature sampling; "
                            "fractional municipal area weighting; raw reanalysis"
                        ),
                        "request_mode": "daily-statistics-annual",
                        "tmin_mean_c": weighted_grid_value(min_grid, weights[name]),
                        "tmax_mean_c": weighted_grid_value(max_grid, weights[name]),
                    }
                )
            write_output(rows, Path(args.output), args.start_year, year)

    expected = len(TARGETS) * (args.end_year - args.start_year + 1)
    if len(rows) != expected:
        raise RuntimeError(f"Expected {expected} municipality-years, got {len(rows)}")
    write_output(rows, Path(args.output), args.start_year, args.end_year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
