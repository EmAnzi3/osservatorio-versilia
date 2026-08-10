#!/usr/bin/env python3
"""Build year-by-year municipal climate history from official LaMMA 1 km daily rasters.

POC scope: 1995-2015, the full daily period exposed by the LaMMA CKAN datasets.
The output is one row per municipality/year and is intentionally source-labelled.
Municipal aggregation currently uses raster cells whose centres fall in each ISTAT
municipal polygon; production must move to fractional-area weighting.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import json
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask

ISTAT_URL = "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip"
CKAN_SHOW = "https://dati.lamma.toscana.it/api/3/action/package_show?id={}"
PACKAGES = {
    "precip": "precipitazioni-spazializzazione",
    "tmax": "temperature-massime-giornaliere-toscana",
    "tmin": "temperature-minime-giornaliere-toscana",
}
TARGETS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
YEAR_RE = re.compile(r"(?:19|20)\d{2}")


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"})
    with urllib.request.urlopen(req, timeout=300) as response, dest.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def extract_zip(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)


def resources_for(package: str) -> dict[int, str]:
    payload = request_json(CKAN_SHOW.format(package))
    if not payload.get("success"):
        raise RuntimeError(f"LaMMA package_show failed: {package}")
    result: dict[int, str] = {}
    for resource in payload.get("result", {}).get("resources", []):
        text = f"{resource.get('name') or ''} {resource.get('url') or ''}"
        match = YEAR_RE.search(text)
        url = resource.get("url")
        if match and url:
            result[int(match.group(0))] = url
    return result


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


def clean(src: rasterio.io.DatasetReader) -> np.ndarray:
    arr = src.read(1).astype("float64")
    invalid = ~np.isfinite(arr)
    if src.nodata is not None:
        invalid |= np.isclose(arr, float(src.nodata), rtol=0, atol=1e-8)
    arr[invalid] = np.nan
    return arr


def build_masks(subset: gpd.GeoDataFrame, name_col: str, crs, shape, transform) -> dict[str, np.ndarray]:
    projected = subset.to_crs(crs) if subset.crs != crs else subset
    masks: dict[str, np.ndarray] = {}
    for _, row in projected.iterrows():
        mask = geometry_mask([row.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False)
        if not mask.any():
            raise RuntimeError(f"No raster cells for {row[name_col]}")
        masks[str(row[name_col])] = mask
    return masks


def municipal_mean(arr: np.ndarray, mask: np.ndarray) -> float | None:
    values = arr[mask & np.isfinite(arr)]
    return float(values.mean()) if values.size else None


def inspect_grid(tif: Path):
    with rasterio.open(tif) as src:
        return src.crs, src.shape, src.transform


def process_precip(root: Path, masks: dict[str, np.ndarray], expected_days: int) -> dict[str, dict[str, float]]:
    tiffs = sorted(root.rglob("*.tif"))
    if len(tiffs) != expected_days:
        raise RuntimeError(f"precip: expected {expected_days} rasters, found {len(tiffs)}")
    annual = None
    wet = None
    ge20 = None
    ge50 = None
    municipal_daily_max = {name: float("-inf") for name in masks}
    valid_days = None
    for tif in tiffs:
        with rasterio.open(tif) as src:
            arr = clean(src)
        if annual is None:
            annual = np.zeros(arr.shape, dtype="float64")
            wet = np.zeros(arr.shape, dtype="uint16")
            ge20 = np.zeros(arr.shape, dtype="uint16")
            ge50 = np.zeros(arr.shape, dtype="uint16")
            valid_days = np.zeros(arr.shape, dtype="uint16")
        valid = np.isfinite(arr)
        annual[valid] += arr[valid]
        valid_days[valid] += 1
        wet[valid & (arr >= 1.0)] += 1
        ge20[valid & (arr >= 20.0)] += 1
        ge50[valid & (arr >= 50.0)] += 1
        for name, mask in masks.items():
            day_mean = municipal_mean(arr, mask)
            if day_mean is not None:
                municipal_daily_max[name] = max(municipal_daily_max[name], day_mean)
    assert annual is not None and wet is not None and ge20 is not None and ge50 is not None and valid_days is not None
    annual[valid_days < expected_days] = np.nan
    out: dict[str, dict[str, float]] = {}
    for name, mask in masks.items():
        out[name] = {
            "precip_mm": municipal_mean(annual, mask),
            "wet_days_ge_1mm": municipal_mean(wet.astype("float64"), mask),
            "rain_days_ge_20mm": municipal_mean(ge20.astype("float64"), mask),
            "rain_days_ge_50mm": municipal_mean(ge50.astype("float64"), mask),
            "max_municipal_daily_precip_mm": municipal_daily_max[name],
        }
    return out


def process_temperature(root: Path, masks: dict[str, np.ndarray], expected_days: int, kind: str) -> dict[str, dict[str, float]]:
    tiffs = sorted(root.rglob("*.tif"))
    if len(tiffs) != expected_days:
        raise RuntimeError(f"{kind}: expected {expected_days} rasters, found {len(tiffs)}")
    total = None
    count = None
    threshold = None
    for tif in tiffs:
        with rasterio.open(tif) as src:
            arr = clean(src)
        if total is None:
            total = np.zeros(arr.shape, dtype="float64")
            count = np.zeros(arr.shape, dtype="uint16")
            threshold = np.zeros(arr.shape, dtype="uint16")
        valid = np.isfinite(arr)
        total[valid] += arr[valid]
        count[valid] += 1
        if kind == "tmax":
            threshold[valid & (arr >= 30.0)] += 1
        else:
            threshold[valid & (arr > 20.0)] += 1
    assert total is not None and count is not None and threshold is not None
    mean_arr = np.full(total.shape, np.nan, dtype="float64")
    complete = count >= expected_days
    mean_arr[complete] = total[complete] / count[complete]
    out: dict[str, dict[str, float]] = {}
    for name, mask in masks.items():
        out[name] = {
            f"{kind}_mean_c": municipal_mean(mean_arr, mask),
            ("hot_days_tmax_ge_30" if kind == "tmax" else "tropical_nights_tmin_gt_20"): municipal_mean(threshold.astype("float64"), mask),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/runtime/meteo-poc/annual-history")
    parser.add_argument("--years", default="1995-2015", help="Range YYYY-YYYY or comma-separated years")
    args = parser.parse_args()

    if "-" in args.years and "," not in args.years:
        start, end = [int(x) for x in args.years.split("-", 1)]
        years = list(range(start, end + 1))
    else:
        years = sorted({int(x.strip()) for x in args.years.split(",") if x.strip()})

    resource_maps = {kind: resources_for(package) for kind, package in PACKAGES.items()}
    available = set.intersection(*(set(mapping) for mapping in resource_maps.values()))
    missing = [year for year in years if year not in available]
    if missing:
        raise RuntimeError(f"Requested years unavailable in all three LaMMA datasets: {missing}; common={min(available)}-{max(available)}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="versilia-history-") as tmp_name:
        tmp = Path(tmp_name)
        istat_zip = tmp / "istat.zip"
        download(ISTAT_URL, istat_zip)
        istat_dir = tmp / "istat"
        extract_zip(istat_zip, istat_dir)
        municipalities, name_col = find_municipal_layer(istat_dir)
        municipalities[name_col] = municipalities[name_col].astype(str).str.strip()
        subset = municipalities[municipalities[name_col].isin(TARGETS)].copy()
        if len(subset) != len(TARGETS):
            raise RuntimeError(f"Expected {len(TARGETS)} municipalities, got {subset[name_col].tolist()}")

        masks = None
        grid_signature = None

        for year in years:
            expected_days = 366 if calendar.isleap(year) else 365
            print(f"[history] year={year} ({expected_days} days)")
            year_results = {name: {} for name in TARGETS}
            year_dir = tmp / str(year)
            year_dir.mkdir()

            extracted: dict[str, Path] = {}
            for kind in ("precip", "tmax", "tmin"):
                archive = year_dir / f"{kind}.zip"
                target = year_dir / kind
                url = resource_maps[kind][year]
                print(f"[history] downloading {kind} {year}: {url}")
                download(url, archive)
                extract_zip(archive, target)
                extracted[kind] = target
                archive.unlink(missing_ok=True)

            first_tif = next(iter(sorted(extracted["precip"].rglob("*.tif"))), None)
            if first_tif is None:
                raise RuntimeError(f"No precipitation TIFF found for {year}")
            crs, shape, transform = inspect_grid(first_tif)
            signature = (str(crs), shape, tuple(transform))
            if masks is None:
                masks = build_masks(subset, name_col, crs, shape, transform)
                grid_signature = signature
            elif signature != grid_signature:
                raise RuntimeError(f"Raster grid changed in {year}; masks must be rebuilt safely")

            precip = process_precip(extracted["precip"], masks, expected_days)
            tmax = process_temperature(extracted["tmax"], masks, expected_days, "tmax")
            tmin = process_temperature(extracted["tmin"], masks, expected_days, "tmin")

            for name in TARGETS:
                tmax_mean = tmax[name]["tmax_mean_c"]
                tmin_mean = tmin[name]["tmin_mean_c"]
                tmean = (tmax_mean + tmin_mean) / 2.0 if tmax_mean is not None and tmin_mean is not None else None
                row = {
                    "municipality": name,
                    "year": year,
                    "period_status": "complete",
                    "source": "LaMMA 1 km daily interpolation",
                    "method": "municipal cell-centre mean POC",
                    "tmean_c": tmean,
                    **tmax[name],
                    **tmin[name],
                    **precip[name],
                }
                rows.append(row)
                print(f"[history] {name} {year}: T={tmean:.2f} C, P={precip[name]['precip_mm']:.0f} mm")

            # Free extracted rasters before the next year.
            for kind in extracted:
                for path in sorted(extracted[kind].rglob("*"), reverse=True):
                    if path.is_file() or path.is_symlink():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                extracted[kind].rmdir()

    fields = [
        "municipality", "year", "period_status", "source", "method",
        "tmean_c", "tmax_mean_c", "tmin_mean_c",
        "hot_days_tmax_ge_30", "tropical_nights_tmin_gt_20",
        "precip_mm", "wet_days_ge_1mm", "rain_days_ge_20mm", "rain_days_ge_50mm",
        "max_municipal_daily_precip_mm",
    ]
    csv_path = out_dir / "lamma-annual-history.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    meta = {
        "status": "POC; year-by-year municipal history; cell-centre aggregation",
        "years": years,
        "rows": len(rows),
        "municipalities": TARGETS,
        "boundaries": {"source": "ISTAT", "reference_date": "2026-01-01", "url": ISTAT_URL},
        "source": {
            "provider": "Consorzio LaMMA",
            "packages": PACKAGES,
            "spatial_resolution": "1 km",
            "daily_period_available_common": [min(available), max(available)],
        },
        "output": csv_path.name,
    }
    (out_dir / "lamma-annual-history.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[history] wrote {len(rows)} rows to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
