#!/usr/bin/env python3
"""Build raw annual mean daily Tmin/Tmax series from ERA5-Land hourly data.

The output is RAW REANALYSIS. It is intentionally built for the LaMMA overlap
and the post-LaMMA period, then calibrated additively against LaMMA 1995-2015.

Definitions match the LaMMA indicators:
- tmin_mean_c = annual mean of daily minimum 2 m temperature;
- tmax_mean_c = annual mean of daily maximum 2 m temperature.

ERA5-Land 2 m temperature is retrieved from the native hourly reanalysis.
Daily minima/maxima are computed locally from the 24 hourly UTC samples.
Municipal aggregation uses fractional intersection weights against ISTAT 2026
boundaries, consistently with the other ERA5-Land scripts.
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
from era5_land_ytd import HOURLY_DATASET, retrieve_with_retry


def days_for_month(year: int, month: int) -> list[str]:
    return [f"{day:02d}" for day in range(1, calendar.monthrange(year, month)[1] + 1)]


def hourly_request(year: int, months: list[int]) -> dict:
    request = {
        "variable": ["2m_temperature"],
        "year": [str(year)],
        "month": [f"{month:02d}" for month in months],
        "day": [f"{day:02d}" for day in range(1, 32)],
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    if len(months) == 1:
        request["day"] = days_for_month(year, months[0])
    return request


def retrieve_hourly(
    client: cdsapi.Client,
    year: int,
    months: list[int],
    target: Path,
    attempts: int = 3,
) -> None:
    label = f"hourly 2m temperature {year} months {months[0]:02d}-{months[-1]:02d}"
    retrieve_with_retry(
        client,
        HOURLY_DATASET,
        hourly_request(year, months),
        target,
        label,
        attempts=attempts,
    )


def read_hourly_temperature(path: Path) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray]:
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


def period_daily_sums(
    times: pd.DatetimeIndex,
    values_kelvin: np.ndarray,
    year: int,
    expected_months: list[int],
) -> tuple[np.ndarray, np.ndarray, int]:
    expected_days = sum(calendar.monthrange(year, month)[1] for month in expected_months)
    expected_hours = expected_days * 24
    if len(times) != expected_hours or values_kelvin.shape[0] != expected_hours:
        raise RuntimeError(
            f"ERA5 hourly temperature {year} months {expected_months[0]:02d}-{expected_months[-1]:02d}: "
            f"expected {expected_hours} hourly values, got {len(times)}"
        )

    naive = times.tz_localize(None) if times.tz is not None else times
    expected = []
    for month in expected_months:
        expected.extend(
            pd.date_range(
                f"{year}-{month:02d}-01 00:00",
                f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d} 23:00",
                freq="h",
            ).tolist()
        )
    expected_index = pd.DatetimeIndex(expected)
    if not naive.equals(expected_index):
        missing = expected_index.difference(naive)
        duplicate_count = int(naive.duplicated().sum())
        raise RuntimeError(
            f"ERA5 hourly temperature {year}: unexpected timestamps; "
            f"missing={len(missing)}, duplicates={duplicate_count}"
        )

    celsius = values_kelvin - 273.15
    shape = (expected_days, 24, *celsius.shape[1:])
    daily = celsius.reshape(shape)
    daily_min = np.nanmin(daily, axis=1)
    daily_max = np.nanmax(daily, axis=1)
    return np.nansum(daily_min, axis=0), np.nansum(daily_max, axis=0), expected_days


def annual_grids(
    client: cdsapi.Client,
    year: int,
    tmp: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]:
    annual_target = tmp / f"hourly-temperature-{year}.download"
    try:
        print(f"[era5-minmax] retrieving native hourly 2m temperature {year}", flush=True)
        retrieve_hourly(client, year, list(range(1, 13)), annual_target, attempts=1)
        times, values, latitudes, longitudes = read_hourly_temperature(annual_target)
        sum_min, sum_max, days = period_daily_sums(
            times, values, year, list(range(1, 13))
        )
        return sum_min / days, sum_max / days, latitudes, longitudes, "annual-request"
    except Exception as exc:
        message = str(exc).casefold()
        if "cost limits exceeded" not in message and "request is too large" not in message:
            raise
        print(
            f"[era5-minmax] annual request {year} exceeded CDS cost limits; "
            "falling back to monthly native-hourly requests",
            flush=True,
        )

    total_min = total_max = None
    total_days = 0
    lat_ref = lon_ref = None
    for month in range(1, 13):
        target = tmp / f"hourly-temperature-{year}-{month:02d}.download"
        retrieve_hourly(client, year, [month], target, attempts=3)
        times, values, latitudes, longitudes = read_hourly_temperature(target)
        sum_min, sum_max, days = period_daily_sums(times, values, year, [month])
        if total_min is None:
            total_min = np.zeros_like(sum_min, dtype=float)
            total_max = np.zeros_like(sum_max, dtype=float)
            lat_ref, lon_ref = latitudes, longitudes
        elif not (
            np.array_equal(lat_ref, latitudes)
            and np.array_equal(lon_ref, longitudes)
        ):
            raise RuntimeError(f"ERA5 grid changed between monthly requests in {year}")
        total_min += sum_min
        total_max += sum_max
        total_days += days

    assert total_min is not None and total_max is not None
    assert lat_ref is not None and lon_ref is not None
    expected_days = 366 if calendar.isleap(year) else 365
    if total_days != expected_days:
        raise RuntimeError(f"ERA5 hourly temperature {year}: expected {expected_days} days, got {total_days}")
    return total_min / total_days, total_max / total_days, lat_ref, lon_ref, "monthly-fallback"


def write_output(rows: list[dict], output: Path, start_year: int, end_year: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).sort_values(["municipality", "year"])
    frame.to_csv(output, index=False)
    output.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "dataset": HOURLY_DATASET,
                "years": [start_year, end_year],
                "status": "raw ERA5-Land reanalysis; calibrate against LaMMA 1995-2015 before publication",
                "definitions": {
                    "tmin_mean_c": "annual mean of daily minimum 2m temperature",
                    "tmax_mean_c": "annual mean of daily maximum 2m temperature",
                },
                "temporal_method": "daily minimum/maximum computed locally from native ERA5-Land hourly 2m temperature at 1-hour UTC sampling",
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
    print(f"[era5-minmax] wrote {len(frame)} rows -> {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1995)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--chunk-years",
        type=int,
        default=1,
        help="Compatibility option. CDS retrieval is always one year per request.",
    )
    parser.add_argument("--output", default="reports/runtime/era5/era5-land-minmax-annual-raw.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required")
    if args.end_year < args.start_year:
        raise SystemExit("end-year must be >= start-year")
    if args.chunk_years != 1:
        raise SystemExit("Tmin/Tmax acquisition requires --chunk-years 1 to keep CDS requests bounded")

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

        weights = None
        lat_ref = lon_ref = None

        for year in range(args.start_year, args.end_year + 1):
            min_grid, max_grid, latitudes, longitudes, request_mode = annual_grids(
                client, year, tmp
            )
            if lat_ref is None:
                lat_ref, lon_ref = latitudes, longitudes
                weights = fractional_weights(subset, name_col, lat_ref, lon_ref)
            elif not (
                np.array_equal(lat_ref, latitudes)
                and np.array_equal(lon_ref, longitudes)
            ):
                raise RuntimeError("ERA5 grid changed between years")

            assert weights is not None
            for name in TARGETS:
                rows.append(
                    {
                        "municipality": name,
                        "year": year,
                        "period_status": "complete",
                        "source": "Copernicus ERA5-Land native hourly reanalysis",
                        "method": (
                            "daily min/max computed locally from 24 hourly UTC 2m-temperature samples; "
                            "fractional municipal area weighting; raw reanalysis"
                        ),
                        "request_mode": request_mode,
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
