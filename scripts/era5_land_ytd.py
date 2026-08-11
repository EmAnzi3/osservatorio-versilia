#!/usr/bin/env python3
"""Build current-year YTD municipal climate indicators from official ERA5-Land data.

The output is deliberately kept separate from complete annual series.
The effective coverage end is the earliest of:
- UTC today minus a configurable safety lag;
- the latest ERA5-Land daily-statistics date (temperature);
- the latest ERA5-Land hourly date minus one day (precipitation needs next-day 00 UTC).

YTD temperature uses official ERA5-Land post-processed DAILY MEAN 2m temperature
at 1-hour sampling. YTD precipitation is reconstructed from ERA5-Land total
precipitation at 00:00 UTC, representing the previous calendar day's 24-hour
accumulation.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import cdsapi
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
    open_download,
    weighted_grid_value,
)

HOURLY_DATASET = "reanalysis-era5-land"
DAILY_DATASET = "derived-era5-land-daily-statistics"
CATALOGUE = "https://cds.climate.copernicus.eu/api/catalogue/v1/collections/{dataset}"


def valid_days(year: int, month: int, end_date: dt.date) -> list[str]:
    last = calendar.monthrange(year, month)[1]
    if year == end_date.year and month == end_date.month:
        last = min(last, end_date.day)
    return [f"{d:02d}" for d in range(1, last + 1)]


def catalogue_latest(dataset: str) -> dt.date:
    url = CATALOGUE.format(dataset=dataset)
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-ERA5/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    value = payload["extent"]["temporal"]["interval"][0][1]
    if not value:
        raise RuntimeError(f"CDS catalogue has no temporal end for {dataset}")
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def retrieve_with_retry(
    client: cdsapi.Client,
    dataset: str,
    request: dict,
    target: Path,
    label: str,
    attempts: int = 3,
) -> None:
    """Retry valid CDS jobs rejected by temporary dataset queue limits."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        target.unlink(missing_ok=True)
        try:
            client.retrieve(dataset, request, str(target))
            return
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            delay = 10 * attempt
            print(
                f"[era5-ytd] CDS retrieval failed for {label} "
                f"(attempt {attempt}/{attempts}): {exc!r}; retrying in {delay}s",
                flush=True,
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def retrieve_temperature_month(client: cdsapi.Client, year: int, month: int, end_date: dt.date, target: Path) -> None:
    request = {
        "product_type": "reanalysis",
        "variable": ["2m_temperature"],
        "year": str(year),
        "month": [f"{month:02d}"],
        "day": valid_days(year, month, end_date),
        "daily_statistic": "daily_mean",
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": AREA,
    }
    retrieve_with_retry(client, DAILY_DATASET, request, target, f"temperature {year}-{month:02d}")


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
    retrieve_with_retry(client, HOURLY_DATASET, request, current_target, f"precipitation {year}-{month:02d}")

    month_last = min(
        calendar.monthrange(year, month)[1],
        end_date.day if month == end_date.month else calendar.monthrange(year, month)[1],
    )
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
    retrieve_with_retry(
        client,
        HOURLY_DATASET,
        next_request,
        next_target,
        f"precipitation carry-over {next_date.isoformat()} 00UTC",
    )


def normalize_keep_axes(da: xr.DataArray) -> xr.DataArray:
    """Normalize coordinates without dropping singleton time/spatial axes."""
    renames = {}
    for name in da.coords:
        folded = name.casefold()
        if folded in {"valid_time", "date"}:
            renames[name] = "time"
        elif folded == "lat":
            renames[name] = "latitude"
        elif folded == "lon":
            renames[name] = "longitude"
    if renames:
        da = da.rename(renames)
    required = {"time", "latitude", "longitude"}
    for name in required:
        if name not in da.coords:
            raise RuntimeError(f"Missing coordinate {name}; coords={list(da.coords)} dims={list(da.dims)}")
    extras = [dim for dim in da.dims if dim not in required and da.sizes.get(dim, 0) == 1]
    if extras:
        da = da.squeeze(extras, drop=True)
    return da


def read_field(path: Path, candidates: tuple[str, ...]) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
    ds = open_download(path)
    try:
        da = normalize_keep_axes(choose_var(ds, candidates))
        times = pd.DatetimeIndex(pd.to_datetime(da["time"].values))
        lat = np.asarray(da["latitude"].values, dtype="float64")
        lon = np.asarray(da["longitude"].values, dtype="float64")
        values = np.asarray(da.values, dtype="float64")
        if values.ndim == 2 and len(times) == 1:
            values = values[None, :, :]
        if values.ndim != 3 or values.shape[0] != len(times):
            raise RuntimeError(f"Unexpected field shape {values.shape} for {len(times)} timestamps; dims={list(da.dims)}")
        return times, values, lat, lon
    finally:
        ds.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=dt.datetime.now(dt.timezone.utc).year)
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD; explicit upper bound")
    parser.add_argument("--lag-days", type=int, default=7)
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-ytd.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")

    today_utc = dt.datetime.now(dt.timezone.utc).date()
    requested_end = dt.date.fromisoformat(args.end_date) if args.end_date else today_utc - dt.timedelta(days=args.lag_days)
    if requested_end.year != args.year:
        raise SystemExit(f"end-date {requested_end} must be in requested year {args.year}")

    hourly_latest = catalogue_latest(HOURLY_DATASET)
    daily_latest = catalogue_latest(DAILY_DATASET)
    precip_latest_complete = hourly_latest - dt.timedelta(days=1)
    end_date = min(requested_end, daily_latest, precip_latest_complete)
    if end_date.year != args.year:
        raise SystemExit(
            f"No complete YTD coverage for {args.year}; requested={requested_end}, "
            f"daily_latest={daily_latest}, hourly_latest={hourly_latest}"
        )
    start_date = dt.date(args.year, 1, 1)
    print(
        f"[era5-ytd] requested through {requested_end}; using {end_date} "
        f"(daily latest {daily_latest}; hourly latest {hourly_latest})"
    )

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
            temp_path = tmp / f"t2m-daily-{args.year}-{month:02d}.download"
            print(f"[era5-ytd] daily-mean temperature {args.year}-{month:02d}")
            retrieve_temperature_month(client, args.year, month, end_date, temp_path)
            _, t_values, lat, lon = read_field(temp_path, ("t2m", "2m_temperature", "2 metre temperature"))
            expected_temp_days = len(valid_days(args.year, month, end_date))
            if t_values.shape[0] != expected_temp_days:
                raise RuntimeError(
                    f"{args.year}-{month:02d}: expected {expected_temp_days} daily temperature fields, got {t_values.shape[0]}"
                )
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
            if not (
                np.array_equal(lat_ref, p_lat1)
                and np.array_equal(lon_ref, p_lon1)
                and np.array_equal(lat_ref, p_lat2)
                and np.array_equal(lon_ref, p_lon2)
            ):
                raise RuntimeError("ERA5 grid changed during YTD precipitation retrieval")

            p_times = p_t1.append(p_t2) - pd.Timedelta(days=1)
            p_values = np.concatenate([p_v1, p_v2], axis=0)
            keep = np.asarray((p_times.date >= start_date) & (p_times.date <= end_date))
            shifted = p_times[keep]
            p_values = p_values[keep]
            month_keep = np.asarray(shifted.month == month)
            p_values = p_values[month_keep]
            expected_days = len(valid_days(args.year, month, end_date))
            if p_values.shape[0] != expected_days:
                raise RuntimeError(
                    f"{args.year}-{month:02d}: expected {expected_days} daily precipitation fields, got {p_values.shape[0]}"
                )
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
                "source": "ERA5-Land daily mean temperature + hourly precipitation",
                "method": "fractional municipal area weighting; YTD, separate from complete annual series",
                "tmean_ytd_c": weighted_grid_value(temp_grid, weights[name]),
                "precip_ytd_mm": weighted_grid_value(precip_sum, weights[name]),
            })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    out.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "requested_end": requested_end.isoformat(),
                "coverage_end": end_date.isoformat(),
                "daily_temperature_latest": daily_latest.isoformat(),
                "hourly_latest": hourly_latest.isoformat(),
                "cds_retrieval": "up to 3 attempts per request for transient queue/backend failures",
                "note": "Partial current-year values; do not compare directly with complete annual totals.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[era5-ytd] wrote {len(rows)} rows through {end_date} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
