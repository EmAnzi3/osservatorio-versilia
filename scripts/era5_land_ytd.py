#!/usr/bin/env python3
"""Build current-year YTD municipal climate indicators from official ERA5-Land hourly data.

The output is deliberately kept separate from complete annual series.
Default end date is UTC today minus a safety lag (7 days), because ERA5-Land
normally trails real time by several days. Coverage dates are written explicitly.

YTD temperature is the mean of all hourly 2m-temperature fields in the period.
YTD precipitation is reconstructed from total precipitation at 00:00 UTC, which
represents the 24-hour accumulation ending at 00:00 (the previous calendar day).
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
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

DATASET = "reanalysis-era5-land"
ALL_HOURS = [f"{h:02d}:00" for h in range(24)]


def valid_days(year: int, month: int, end_date: dt.date) -> list[str]:
    last = calendar.monthrange(year, month)[1]
    if year == end_date.year and month == end_date.month:
        last = min(last, end_date.day)
    return [f"{d:02d}" for d in range(1, last + 1)]


def retrieve_temperature_month(client: cdsapi.Client, year: int, month: int, end_date: dt.date, target: Path) -> None:
    request = {
        "variable": ["2m_temperature"],
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": valid_days(year, month, end_date),
        "time": ALL_HOURS,
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client.retrieve(DATASET, request, str(target))


def retrieve_precip_month(client: cdsapi.Client, year: int, month: int, end_date: dt.date, current_target: Path, next_target: Path) -> None:
    request = {
        "variable": ["total_precipitation"],
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": valid_days(year, month, end_date),
        "time": ["00:00"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client.retrieve(DATASET, request, str(current_target))

    # The last target day is represented by 00:00 UTC on the following day.
    month_last = min(calendar.monthrange(year, month)[1], end_date.day if month == end_date.month else 31)
    last_date = dt.date(year, month, month_last)
    next_date = last_date + dt.timedelta(days=1)
    next_request = {
        "variable": ["total_precipitation"],
        "year": [str(next_date.year)],
        "month": [f"{next_date.month:02d}"],
        "day": [f"{next_date.day:02d}"],
        "time": ["00:00"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client.retrieve(DATASET, next_request, str(next_target))


def read_field(path: Path, candidates: tuple[str, ...]) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    ds = open_download(path)
    try:
        da = normalize_coords(choose_var(ds, candidates))
        times = pd.DatetimeIndex(pd.to_datetime(da["time"].values))
        lat = np.asarray(da["latitude"].values, dtype="float64")
        lon = np.asarray(da["longitude"].values, dtype="float64")
        values = np.asarray(da.values, dtype="float64")
        return times, values, lat, lon
    finally:
        ds.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=dt.datetime.now(dt.timezone.utc).year)
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD; default UTC today minus lag-days")
    parser.add_argument("--lag-days", type=int, default=7)
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-ytd.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")

    if args.end_date:
        end_date = dt.date.fromisoformat(args.end_date)
    else:
        end_date = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=args.lag_days)
    if end_date.year != args.year:
        raise SystemExit(f"end-date {end_date} must be in requested year {args.year}")
    start_date = dt.date(args.year, 1, 1)

    client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=token)

    with tempfile.TemporaryDirectory(prefix="era5-ytd-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()

        temp_sum = None
        temp_count = None
        precip_sum = None
        lat_ref = lon_ref = None

        for month in range(1, end_date.month + 1):
            temp_path = tmp / f"t2m-{args.year}-{month:02d}.download"
            print(f"[era5-ytd] temperature {args.year}-{month:02d}")
            retrieve_temperature_month(client, args.year, month, end_date, temp_path)
            t_times, t_values, lat, lon = read_field(temp_path, ("t2m", "2m_temperature", "2 metre temperature"))
            if lat_ref is None:
                lat_ref, lon_ref = lat, lon
                temp_sum = np.zeros(t_values.shape[1:], dtype="float64")
                temp_count = np.zeros(t_values.shape[1:], dtype="uint32")
                precip_sum = np.zeros(t_values.shape[1:], dtype="float64")
            elif not (np.array_equal(lat_ref, lat) and np.array_equal(lon_ref, lon)):
                raise RuntimeError("ERA5 grid changed during YTD temperature retrieval")

            valid_t = np.isfinite(t_values)
            temp_sum += np.nansum(t_values - 273.15, axis=0)
            temp_count += valid_t.sum(axis=0).astype("uint32")

            p_current = tmp / f"tp-{args.year}-{month:02d}.download"
            p_next = tmp / f"tp-next-{args.year}-{month:02d}.download"
            print(f"[era5-ytd] precipitation {args.year}-{month:02d}")
            retrieve_precip_month(client, args.year, month, end_date, p_current, p_next)
            p_t1, p_v1, p_lat1, p_lon1 = read_field(p_current, ("tp", "total_precipitation", "total precipitation"))
            p_t2, p_v2, p_lat2, p_lon2 = read_field(p_next, ("tp", "total_precipitation", "total precipitation"))
            if not (np.array_equal(lat_ref, p_lat1) and np.array_equal(lon_ref, p_lon1) and np.array_equal(lat_ref, p_lat2) and np.array_equal(lon_ref, p_lon2)):
                raise RuntimeError("ERA5 grid changed during YTD precipitation retrieval")

            p_times = p_t1.append(p_t2) - pd.Timedelta(days=1)
            p_values = np.concatenate([p_v1, p_v2], axis=0)
            keep = np.asarray((p_times.date >= start_date) & (p_times.date <= end_date))
            # Avoid double-counting previous months: retain only target calendar month.
            shifted = p_times[keep]
            p_values = p_values[keep]
            month_keep = np.asarray(shifted.month == month)
            p_values = p_values[month_keep]
            expected_days = month_last = min(calendar.monthrange(args.year, month)[1], end_date.day if month == end_date.month else calendar.monthrange(args.year, month)[1])
            if p_values.shape[0] != expected_days:
                raise RuntimeError(f"{args.year}-{month:02d}: expected {expected_days} daily precipitation fields, got {p_values.shape[0]}")
            precip_sum += np.nansum(p_values * 1000.0, axis=0)

        assert temp_sum is not None and temp_count is not None and precip_sum is not None and lat_ref is not None and lon_ref is not None
        temp_grid = np.divide(temp_sum, temp_count, out=np.full(temp_sum.shape, np.nan), where=temp_count > 0)
        weights = fractional_weights(subset, name_col, lat_ref, lon_ref)
        rows = []
        for name in TARGETS:
            rows.append({
                "municipality": name,
                "year": args.year,
                "period_status": "YTD_PARTIAL",
                "coverage_start": start_date.isoformat(),
                "coverage_end": end_date.isoformat(),
                "days_covered": (end_date - start_date).days + 1,
                "source": "ERA5-Land hourly",
                "method": "fractional municipal area weighting; YTD, separate from complete annual series",
                "tmean_ytd_c": weighted_grid_value(temp_grid, weights[name]),
                "precip_ytd_mm": weighted_grid_value(precip_sum, weights[name]),
            })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[era5-ytd] wrote {len(rows)} rows through {end_date} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
