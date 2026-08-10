#!/usr/bin/env python3
"""Replace ERA5-Land annual precipitation for 2022-2024 using hourly accumulations.

ECMWF documents incorrect accumulated fields in the ERA5-Land
"monthly averaged reanalysis" product from September 2022 through February 2024.
Those values remain accessible via the CDS API. To ensure no contaminated annual
precipitation enters the reconstructed series, this script recomputes the FULL
calendar years 2022, 2023 and 2024 from the official hourly product.

ERA5-Land total precipitation at 00:00 UTC represents the 24-hour accumulation
ending at 00:00, i.e. the previous calendar day. Therefore each timestamp is
shifted back one day before annual aggregation.
"""
from __future__ import annotations

import argparse
import calendar
import os
import tempfile
from pathlib import Path

import cdsapi
import geopandas as gpd
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
    open_download,
    weighted_grid_value,
)

DATASET = "reanalysis-era5-land"
PATCH_YEARS = (2022, 2023, 2024)


def retrieve_year(client: cdsapi.Client, year: int, target: Path) -> None:
    request = {
        "variable": ["total_precipitation"],
        "year": [str(year)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": ["00:00"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client.retrieve(DATASET, request, str(target))


def retrieve_next_jan1(client: cdsapi.Client, year: int, target: Path) -> None:
    request = {
        "variable": ["total_precipitation"],
        "year": [str(year + 1)],
        "month": ["01"],
        "day": ["01"],
        "time": ["00:00"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client.retrieve(DATASET, request, str(target))


def read_precip(path: Path) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    ds = open_download(path)
    try:
        tp = normalize_coords(choose_var(ds, ("tp", "total_precipitation", "total precipitation")))
        times = pd.DatetimeIndex(pd.to_datetime(tp["time"].values))
        lat = np.asarray(tp["latitude"].values, dtype="float64")
        lon = np.asarray(tp["longitude"].values, dtype="float64")
        values = np.asarray(tp.values, dtype="float64")
        return times, values, lat, lon
    finally:
        ds.close()


def annual_grid(client: cdsapi.Client, year: int, tmp: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    current = tmp / f"precip-{year}.download"
    next_day = tmp / f"precip-{year + 1}-01-01.download"
    print(f"[era5-precip-patch] retrieving {year} daily accumulations via 00UTC hourly fields")
    retrieve_year(client, year, current)
    retrieve_next_jan1(client, year, next_day)

    t1, v1, lat1, lon1 = read_precip(current)
    t2, v2, lat2, lon2 = read_precip(next_day)
    if not (np.array_equal(lat1, lat2) and np.array_equal(lon1, lon2)):
        raise RuntimeError(f"ERA5 grid changed while patching {year}")

    times = t1.append(t2) - pd.Timedelta(days=1)
    values = np.concatenate([v1, v2], axis=0)
    keep = np.asarray(times.year == year)
    values = values[keep]
    expected = 366 if calendar.isleap(year) else 365
    if values.shape[0] != expected:
        raise RuntimeError(f"{year}: expected {expected} daily precipitation fields, got {values.shape[0]}")

    # Hourly ERA5-Land accumulation at 00 UTC is the previous day's total, in metres.
    grid_mm = np.nansum(values * 1000.0, axis=0)
    return grid_mm, lat1, lon1, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="Raw annual ERA5-Land CSV")
    parser.add_argument("--output", required=True, help="Patched annual ERA5-Land CSV")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")

    raw = pd.read_csv(args.raw)
    required = {"municipality", "year", "precip_mm"}
    missing = required - set(raw.columns)
    if missing:
        raise SystemExit(f"Raw ERA5 CSV missing columns: {sorted(missing)}")

    client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=token)

    with tempfile.TemporaryDirectory(prefix="era5-precip-patch-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()

        weights = None
        patch_rows: list[dict] = []
        for year in PATCH_YEARS:
            grid, lat, lon, days = annual_grid(client, year, tmp)
            if weights is None:
                weights = fractional_weights(subset, name_col, lat, lon)
            for name in TARGETS:
                patch_rows.append({
                    "municipality": name,
                    "year": year,
                    "precip_mm_patch": weighted_grid_value(grid, weights[name]),
                    "precip_patch_days": days,
                })

    patch = pd.DataFrame(patch_rows)
    result = raw.merge(patch, on=["municipality", "year"], how="left")
    affected = result["precip_mm_patch"].notna()
    result.loc[affected, "precip_mm"] = result.loc[affected, "precip_mm_patch"]
    result["precip_source_note"] = "ERA5-Land monthly means"
    result.loc[affected, "precip_source_note"] = "ERA5-Land hourly 00UTC daily accumulations (ECMWF monthly-precipitation defect bypass)"
    result = result.drop(columns=["precip_mm_patch"])

    expected_rows = len(TARGETS) * len(PATCH_YEARS)
    if int(affected.sum()) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} patched municipality-years, got {int(affected.sum())}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    print(f"[era5-precip-patch] patched {int(affected.sum())} municipality-years -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
