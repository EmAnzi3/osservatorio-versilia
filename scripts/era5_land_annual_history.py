#!/usr/bin/env python3
"""Build raw municipal annual climate series from official Copernicus ERA5-Land monthly means.

This script deliberately requires a CDS personal access token via CDS_API_TOKEN.
It never embeds credentials. Output is RAW REANALYSIS and must be calibrated on
the 1995-2015 overlap with LaMMA before being exposed as the reconstructed
municipal series.

Annual temperature is the day-weighted mean of monthly 2m temperature.
Annual precipitation follows the ECMWF conversion for monthly means of daily
accumulations: tp[m/day] * 1000 * days_in_month, summed over 12 months.
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

import cdsapi
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.geometry
import xarray as xr

DATASET = "reanalysis-era5-land-monthly-means"
ISTAT_URL = "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip"
TARGETS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
# N/W/S/E; includes a margin around all seven municipalities.
AREA = [44.25, 9.95, 43.65, 10.85]


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-ERA5/1.0"})
    with urllib.request.urlopen(req, timeout=300) as response, dest.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def extract_zip(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)


def find_municipal_layer(root: Path) -> tuple[gpd.GeoDataFrame, str]:
    wanted = {name.casefold() for name in TARGETS}
    for shp in root.rglob("*.shp"):
        try:
            gdf = gpd.read_file(shp)
        except Exception:
            continue
        for column in gdf.columns:
            if column == gdf.geometry.name:
                continue
            values = {str(x).strip().casefold() for x in gdf[column].dropna().tolist()}
            if wanted.issubset(values):
                return gdf, column
    raise RuntimeError("Could not identify ISTAT municipal layer")


def choose_var(ds: xr.Dataset, candidates: tuple[str, ...]) -> xr.DataArray:
    lower = {name.casefold(): name for name in ds.data_vars}
    for candidate in candidates:
        if candidate.casefold() in lower:
            return ds[lower[candidate.casefold()]]
    for name, var in ds.data_vars.items():
        attrs = " ".join(str(var.attrs.get(k, "")) for k in ("standard_name", "long_name")).casefold()
        if any(candidate.replace("_", " ").casefold() in attrs for candidate in candidates):
            return var
    raise RuntimeError(f"Could not identify variable among {list(ds.data_vars)} for {candidates}")


def normalize_coords(da: xr.DataArray) -> xr.DataArray:
    renames = {}
    for name in da.coords:
        folded = name.casefold()
        if folded in {"valid_time", "date"}:
            renames[name] = "time"
        elif folded in {"lat"}:
            renames[name] = "latitude"
        elif folded in {"lon"}:
            renames[name] = "longitude"
    if renames:
        da = da.rename(renames)
    for required in ("time", "latitude", "longitude"):
        if required not in da.coords:
            raise RuntimeError(f"Missing coordinate {required}; coords={list(da.coords)}")
    return da.squeeze(drop=True)


def grid_cells(latitudes: np.ndarray, longitudes: np.ndarray) -> list[tuple[int, int, shapely.geometry.Polygon]]:
    if len(latitudes) < 2 or len(longitudes) < 2:
        raise RuntimeError("ERA5 subset must contain at least 2x2 grid points")
    dlat = float(np.median(np.abs(np.diff(latitudes))))
    dlon = float(np.median(np.abs(np.diff(longitudes))))
    cells = []
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            cells.append((i, j, shapely.geometry.box(float(lon - dlon / 2), float(lat - dlat / 2), float(lon + dlon / 2), float(lat + dlat / 2))))
    return cells


def fractional_weights(municipalities: gpd.GeoDataFrame, name_col: str, latitudes: np.ndarray, longitudes: np.ndarray) -> dict[str, list[tuple[int, int, float]]]:
    cells = grid_cells(latitudes, longitudes)
    cell_gdf = gpd.GeoDataFrame(
        {"i": [c[0] for c in cells], "j": [c[1] for c in cells]},
        geometry=[c[2] for c in cells], crs="EPSG:4326",
    ).to_crs("EPSG:3035")
    muni = municipalities.to_crs("EPSG:4326").to_crs("EPSG:3035")
    weights: dict[str, list[tuple[int, int, float]]] = {}
    for _, row in muni.iterrows():
        name = str(row[name_col])
        entries = []
        for _, cell in cell_gdf.iterrows():
            area = row.geometry.intersection(cell.geometry).area
            if area > 0:
                entries.append((int(cell["i"]), int(cell["j"]), float(area)))
        total = sum(x[2] for x in entries)
        if total <= 0:
            raise RuntimeError(f"No ERA5 cell intersects {name}")
        weights[name] = [(i, j, area / total) for i, j, area in entries]
    return weights


def weighted_grid_value(grid: np.ndarray, weights: list[tuple[int, int, float]]) -> float:
    vals = []
    ws = []
    for i, j, weight in weights:
        value = float(grid[i, j])
        if np.isfinite(value):
            vals.append(value)
            ws.append(weight)
    if not vals:
        return float("nan")
    total = sum(ws)
    return float(sum(v * w for v, w in zip(vals, ws)) / total)


def retrieve_chunk(client: cdsapi.Client, years: list[int], target: Path, attempts: int = 3) -> None:
    """Retrieve one CDS chunk, retrying backend job failures without hiding them.

    CDS occasionally accepts and runs a valid request and then returns a failed
    job (HTTP 400 on the results endpoint). The exact same request can succeed
    when resubmitted, so retry here rather than forcing a full 1950-2025 rerun.
    """
    request = {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": ["2m_temperature", "total_precipitation"],
        "year": [str(y) for y in years],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": ["00:00"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        target.unlink(missing_ok=True)
        try:
            client.retrieve(DATASET, request, str(target))
            return
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            delay = 10 * attempt
            print(
                f"[era5] CDS retrieval failed for {years[0]}-{years[-1]} "
                f"(attempt {attempt}/{attempts}): {exc!r}; retrying in {delay}s",
                flush=True,
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def open_download(path: Path) -> xr.Dataset:
    if zipfile.is_zipfile(path):
        dest = path.with_suffix("")
        extract_zip(path, dest)
        nc = sorted(dest.rglob("*.nc"))
        if not nc:
            raise RuntimeError("CDS ZIP contained no NetCDF")
        datasets = [xr.open_dataset(p) for p in nc]
        return xr.merge(datasets, compat="override")
    return xr.open_dataset(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--chunk-years", type=int, default=10)
    parser.add_argument("--output", default="reports/runtime/meteo-poc/era5-land-annual-raw.csv")
    args = parser.parse_args()

    token = os.environ.get("CDS_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("CDS_API_TOKEN is required. Create it in the Copernicus CDS profile and provide it as a GitHub Actions secret; never commit it.")
    if args.end_year < args.start_year:
        raise SystemExit("end-year must be >= start-year")

    client = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=token)
    rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="era5-versilia-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()

        all_years = list(range(args.start_year, args.end_year + 1))
        weights = None
        for offset in range(0, len(all_years), args.chunk_years):
            years = all_years[offset:offset + args.chunk_years]
            target = tmp / f"era5-{years[0]}-{years[-1]}.download"
            print(f"[era5] retrieving {years[0]}-{years[-1]}")
            retrieve_chunk(client, years, target)
            ds = open_download(target)
            try:
                t2m = normalize_coords(choose_var(ds, ("t2m", "2m_temperature", "2 metre temperature")))
                tp = normalize_coords(choose_var(ds, ("tp", "total_precipitation", "total precipitation")))
                lat = np.asarray(t2m["latitude"].values, dtype="float64")
                lon = np.asarray(t2m["longitude"].values, dtype="float64")
                if weights is None:
                    weights = fractional_weights(subset, name_col, lat, lon)

                times = pd.to_datetime(t2m["time"].values)
                for year in years:
                    idx = np.where(times.year == year)[0]
                    if len(idx) != 12:
                        raise RuntimeError(f"ERA5 {year}: expected 12 monthly records, got {len(idx)}")
                    t_months = np.asarray(t2m.isel(time=idx).values, dtype="float64")
                    p_months = np.asarray(tp.isel(time=idx).values, dtype="float64")
                    month_numbers = times[idx].month
                    days = np.asarray([calendar.monthrange(year, int(m))[1] for m in month_numbers], dtype="float64")
                    annual_t_grid = ((t_months - 273.15) * days[:, None, None]).sum(axis=0) / days.sum()
                    annual_p_grid = (p_months * (1000.0 * days[:, None, None])).sum(axis=0)
                    for name in TARGETS:
                        rows.append({
                            "municipality": name,
                            "year": year,
                            "period_status": "complete",
                            "source": "ERA5-Land monthly means",
                            "method": "fractional municipal area weighting; raw reanalysis",
                            "tmean_c": weighted_grid_value(annual_t_grid, weights[name]),
                            "precip_mm": weighted_grid_value(annual_p_grid, weights[name]),
                        })
            finally:
                ds.close()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    meta = {
        "dataset": DATASET,
        "years": [args.start_year, args.end_year],
        "status": "raw ERA5-Land reanalysis; calibrate against LaMMA 1995-2015 before publication",
        "municipalities": TARGETS,
        "area": AREA,
        "temperature_aggregation": "day-weighted monthly 2m temperature; K to C",
        "precipitation_aggregation": "sum(monthly tp[m/day] * 1000 * days_in_month)",
        "municipal_weighting": "fractional intersection of 0.1-degree cells with ISTAT 2026 municipal polygons",
        "cds_retrieval": "up to 3 attempts per chunk for transient backend job failures",
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[era5] wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
