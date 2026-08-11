#!/usr/bin/env python3
"""Build annual mean daily Tmin/Tmax from direct ERA5-Land ARCO hourly data.

The output is RAW REANALYSIS and is calibrated separately against LaMMA
1995-2015 before publication. The geo-chunked ARCO store is used because it is
optimised for long time series over a limited area and avoids CDS retrieval
queue processing.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

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
    weighted_grid_value,
)

ARCO_2M_TEMPERATURE_GEO = (
    "https://arco.datastores.ecmwf.int/cadl-arco-geo-007/arco/"
    "reanalysis_era5_land/sfc-2m-temperature/geoChunked.zarr"
)


def coord_slice(values: np.ndarray, low: float, high: float) -> slice:
    return slice(low, high) if len(values) < 2 or values[0] <= values[-1] else slice(high, low)


def open_subset(token: str, start_year: int, end_year: int) -> xr.DataArray:
    print("[era5-minmax] opening direct ERA5-Land ARCO geo-chunked store", flush=True)
    ds = xr.open_zarr(
        ARCO_2M_TEMPERATURE_GEO,
        consolidated=True,
        storage_options={"headers": {"Authorization": f"Bearer {token}"}},
    )
    da = normalize_coords(
        choose_var(ds, ("2m_temperature", "t2m", "2 metre temperature"))
    ).transpose("time", "latitude", "longitude")

    north, west, south, east = AREA
    lat = np.asarray(da["latitude"].values, dtype=float)
    lon = np.asarray(da["longitude"].values, dtype=float)
    subset = da.sel(
        time=slice(f"{start_year}-01-01T00:00:00", f"{end_year}-12-31T23:00:00"),
        latitude=coord_slice(lat, south, north),
        longitude=coord_slice(lon, west, east),
    )
    if subset.sizes.get("latitude", 0) < 2 or subset.sizes.get("longitude", 0) < 2:
        raise RuntimeError(f"ARCO area subset too small: {dict(subset.sizes)}")
    return subset


def load_hourly(da: xr.DataArray, start_year: int, end_year: int):
    expected = pd.date_range(
        f"{start_year}-01-01 00:00", f"{end_year}-12-31 23:00", freq="h"
    )
    times = pd.DatetimeIndex(pd.to_datetime(da["time"].values))
    if times.tz is not None:
        times = times.tz_localize(None)
    if not times.equals(expected):
        missing = expected.difference(times)
        extra = times.difference(expected)
        duplicates = int(times.duplicated().sum())
        raise RuntimeError(
            "ARCO hourly coverage mismatch: "
            f"expected={len(expected)}, got={len(times)}, missing={len(missing)}, "
            f"extra={len(extra)}, duplicates={duplicates}"
        )

    lat = np.asarray(da["latitude"].values, dtype=float)
    lon = np.asarray(da["longitude"].values, dtype=float)
    print(
        f"[era5-minmax] loading {len(times):,} hourly steps over "
        f"{len(lat)}x{len(lon)} grid points",
        flush=True,
    )
    values = np.asarray(da.values, dtype=np.float32)
    expected_shape = (len(times), len(lat), len(lon))
    if values.shape != expected_shape:
        raise RuntimeError(f"Unexpected ARCO array shape {values.shape}; expected {expected_shape}")
    print(
        f"[era5-minmax] loaded {values.size:,} values "
        f"({values.nbytes / 1024 / 1024:.1f} MiB)",
        flush=True,
    )
    return times, values, lat, lon


def annual_grids(values_kelvin: np.ndarray, start_year: int, end_year: int):
    if values_kelvin.shape[0] % 24:
        raise RuntimeError("Hourly sample count is not divisible by 24")
    celsius = values_kelvin - np.float32(273.15)
    day_count = values_kelvin.shape[0] // 24
    daily = celsius.reshape(day_count, 24, *celsius.shape[1:])
    daily_min = np.nanmin(daily, axis=1)
    daily_max = np.nanmax(daily, axis=1)
    dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="D")
    if len(dates) != day_count:
        raise RuntimeError(f"Daily reshape mismatch: expected {len(dates)}, got {day_count}")
    years = dates.year.to_numpy()
    return {
        year: (
            np.nanmean(daily_min[years == year], axis=0),
            np.nanmean(daily_max[years == year], axis=0),
        )
        for year in range(start_year, end_year + 1)
    }


def write_output(rows: list[dict], output: Path, start_year: int, end_year: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).sort_values(["municipality", "year"])
    frame.to_csv(output, index=False)
    output.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "dataset": "ERA5-Land ARCO geo-chunked hourly 2m temperature",
                "arco_store": ARCO_2M_TEMPERATURE_GEO,
                "years": [start_year, end_year],
                "status": "raw ERA5-Land reanalysis; calibrate against LaMMA 1995-2015 before publication",
                "definitions": {
                    "tmin_mean_c": "annual mean of daily minimum 2m temperature",
                    "tmax_mean_c": "annual mean of daily maximum 2m temperature",
                },
                "temporal_method": (
                    "daily min/max computed locally from 24 hourly UTC ERA5-Land "
                    "2m-temperature samples read directly from the Copernicus "
                    "geo-chunked ARCO Zarr datacube"
                ),
                "frequency": "1_hourly",
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
    print(f"[era5-minmax] wrote {len(frame)} rows -> {output}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1995)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--chunk-years", type=int, default=1, help="Deprecated compatibility option")
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-minmax-annual-raw.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")
    if args.end_year < args.start_year:
        raise SystemExit("end-year must be >= start-year")

    da = open_subset(token, args.start_year, args.end_year)
    _, values, latitudes, longitudes = load_hourly(da, args.start_year, args.end_year)
    grids = annual_grids(values, args.start_year, args.end_year)

    with tempfile.TemporaryDirectory(prefix="era5-minmax-arco-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()
        weights = fractional_weights(subset, name_col, latitudes, longitudes)

    rows: list[dict] = []
    for year in range(args.start_year, args.end_year + 1):
        min_grid, max_grid = grids[year]
        for name in TARGETS:
            rows.append(
                {
                    "municipality": name,
                    "year": year,
                    "period_status": "complete",
                    "source": "Copernicus ERA5-Land ARCO hourly reanalysis",
                    "method": (
                        "daily min/max computed locally from 24 hourly UTC "
                        "2m-temperature samples; fractional municipal area weighting; raw reanalysis"
                    ),
                    "request_mode": "arco-geo-direct",
                    "tmin_mean_c": weighted_grid_value(min_grid, weights[name]),
                    "tmax_mean_c": weighted_grid_value(max_grid, weights[name]),
                }
            )

    expected_rows = len(TARGETS) * (args.end_year - args.start_year + 1)
    if len(rows) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} municipality-years, got {len(rows)}")
    write_output(rows, Path(args.output), args.start_year, args.end_year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
