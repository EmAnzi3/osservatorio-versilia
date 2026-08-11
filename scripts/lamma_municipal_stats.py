#!/usr/bin/env python3
"""Municipal-scale climate checks from official ISTAT polygons + LaMMA 1 km rasters.

This independent check uses the same fractional-area municipal geometry rule as
the annual history, but a different LaMMA product: the 1995-2014 annual mean
temperature climatology raster. It also checks the independently aggregated 2015
precipitation total.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

from lamma_annual_history import fractional_weights, weighted_grid_value

ISTAT_URL = "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip"
TMED_URL = "https://geoportale.lamma.rete.toscana.it/download/spazializzazioni/Tmed_climatologia.zip"
PRECIP_2015_URL = "https://geoportale.lamma.rete.toscana.it/download/spazializzazioni/Prec_giornaliero_2015.zip"
TARGETS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"})
    with urllib.request.urlopen(req, timeout=300) as response, dest.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def unzip(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)


def find_municipal_layer(root: Path) -> tuple[gpd.GeoDataFrame, str]:
    wanted = {x.casefold() for x in TARGETS}
    diagnostics = []
    for shp in root.rglob("*.shp"):
        try:
            gdf = gpd.read_file(shp)
        except Exception as exc:
            diagnostics.append(f"{shp.name}: {exc}")
            continue
        for column in gdf.columns:
            if column == gdf.geometry.name:
                continue
            values = {str(x).strip().casefold() for x in gdf[column].dropna().tolist()}
            if wanted.issubset(values):
                print(f"[municipal] selected {shp.name}, name column={column}, rows={len(gdf)}, crs={gdf.crs}")
                return gdf, column
    raise RuntimeError("Could not identify ISTAT municipal layer. " + " | ".join(diagnostics[:5]))


def clean_array(src: rasterio.io.DatasetReader) -> np.ndarray:
    arr = src.read(1).astype("float64")
    invalid = ~np.isfinite(arr)
    if src.nodata is not None:
        invalid |= np.isclose(arr, float(src.nodata), rtol=0, atol=1e-8)
    arr[invalid] = np.nan
    return arr


def annual_temperature(temp_root: Path):
    candidates = [p for p in temp_root.rglob("*.tif") if "Tmed_annuale" in p.name]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one annual Tmed raster, found {[p.name for p in candidates]}")
    src = rasterio.open(candidates[0])
    return src, clean_array(src)


def annual_precipitation(precip_root: Path):
    tiffs = sorted(precip_root.rglob("*.tif"))
    if len(tiffs) != 365:
        raise RuntimeError(f"Expected 365 precipitation rasters, found {len(tiffs)}")
    total = None
    count = None
    transform = None
    crs = None
    shape = None
    for i, tif in enumerate(tiffs):
        with rasterio.open(tif) as src:
            arr = clean_array(src)
            if total is None:
                total = np.zeros(arr.shape, dtype="float64")
                count = np.zeros(arr.shape, dtype="uint16")
                transform = src.transform
                crs = src.crs
                shape = src.shape
            valid = np.isfinite(arr)
            total[valid] += arr[valid]
            count[valid] += 1
        if (i + 1) % 100 == 0:
            print(f"[municipal] precipitation rasters aggregated: {i+1}/365")
    assert total is not None and count is not None and shape is not None
    total[count < 365] = np.nan
    return total, transform, crs, shape


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/runtime/meteo-poc/lamma-municipal-stats.json")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="versilia-zonal-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip, tmed_zip, pr_zip = tmp / "istat.zip", tmp / "tmed.zip", tmp / "precip.zip"
        print("[municipal] downloading ISTAT 2026 boundaries")
        download(ISTAT_URL, istat_zip)
        print("[municipal] downloading LaMMA Tmed climatology")
        download(TMED_URL, tmed_zip)
        print("[municipal] downloading LaMMA precipitation 2015")
        download(PRECIP_2015_URL, pr_zip)
        istat_dir, tmed_dir, pr_dir = tmp / "istat", tmp / "tmed", tmp / "precip"
        unzip(istat_zip, istat_dir)
        unzip(tmed_zip, tmed_dir)
        unzip(pr_zip, pr_dir)

        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()
        if len(subset) != len(TARGETS):
            raise RuntimeError(f"Expected {len(TARGETS)} municipalities, found {subset[name_col].tolist()}")

        t_src, t_arr = annual_temperature(tmed_dir)
        try:
            t_weights, t_diag = fractional_weights(subset, name_col, t_src.crs, t_src.shape, t_src.transform)
            raster_meta = {
                "crs": t_src.crs.to_string() if t_src.crs else None,
                "resolution": [abs(float(t_src.transform.a)), abs(float(t_src.transform.e))],
                "width": t_src.width,
                "height": t_src.height,
            }
            temp_stats = {}
            for name in TARGETS:
                temp_stats[name] = {
                    "tmean_1995_2014_c": weighted_grid_value(t_arr, t_weights[name]),
                    "intersecting_cells": t_diag[name]["intersecting_cells"],
                    "coverage_ratio": t_diag[name]["coverage_ratio"],
                }
        finally:
            t_src.close()

        p_arr, p_transform, p_crs, p_shape = annual_precipitation(pr_dir)
        p_weights, p_diag = fractional_weights(subset, name_col, p_crs, p_shape, p_transform)
        precip_stats = {}
        for name in TARGETS:
            precip_stats[name] = {
                "precip_2015_mm": weighted_grid_value(p_arr, p_weights[name]),
                "precip_intersecting_cells": p_diag[name]["intersecting_cells"],
                "precip_coverage_ratio": p_diag[name]["coverage_ratio"],
            }

        results = {}
        for name in TARGETS:
            results[name] = {**temp_stats[name], **precip_stats[name]}
            print(f"[municipal] {name}: {results[name]}")

        payload = {
            "status": "independent LaMMA municipal check; fractional-area aggregation",
            "method": "fractional intersection of LaMMA cells with ISTAT 2026 polygons; area measured in EPSG:3035",
            "boundaries": {"source": "ISTAT", "reference_date": "2026-01-01", "url": ISTAT_URL},
            "temperature": {"source": "LaMMA", "period": "1995-2014", "url": TMED_URL},
            "precipitation": {"source": "LaMMA", "period": "2015", "url": PRECIP_2015_URL},
            "raster": raster_meta,
            "municipalities": results,
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
