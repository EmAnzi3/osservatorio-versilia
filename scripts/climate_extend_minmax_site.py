#!/usr/bin/env python3
"""Extend the site Tmin/Tmax JSON from LaMMA 1995-2015 to 2025.

LaMMA remains the primary source for 1995-2015. Raw ERA5-Land annual means of
daily minima/maxima are built from native hourly 2 m temperature, calibrated
additively per municipality on the full 1995-2015 overlap, and used for
2016-2025 only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {"tmin": "tmin_mean_c", "tmax": "tmax_mean_c"}
OVERLAP_YEARS = list(range(1995, 2016))
FULL_YEARS = list(range(1995, 2026))


def linear_slope_per_decade(years: np.ndarray, values: np.ndarray) -> float:
    x = years.astype(float)
    y = values.astype(float)
    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    denominator = float(np.sum((x - mean_x) ** 2))
    if denominator == 0:
        return 0.0
    slope = float(np.sum((x - mean_x) * (y - mean_y)) / denominator)
    return slope * 10.0


def score(years: np.ndarray, observed: np.ndarray, raw: np.ndarray, offset: float) -> dict:
    corrected = raw + offset
    raw_residual = observed - raw
    corrected_residual = observed - corrected
    return {
        "n": int(len(years)),
        "offset_c": float(offset),
        "before": {
            "mean_bias_era5_minus_lamma_c": float(np.mean(raw - observed)),
            "rmse_c": float(np.sqrt(np.mean((observed - raw) ** 2))),
            "mae_c": float(np.mean(np.abs(observed - raw))),
            "residual_trend_c_per_decade": linear_slope_per_decade(years, raw_residual),
        },
        "after": {
            "mean_bias_era5_minus_lamma_c": float(np.mean(corrected - observed)),
            "rmse_c": float(np.sqrt(np.mean((observed - corrected) ** 2))),
            "mae_c": float(np.mean(np.abs(observed - corrected))),
            "residual_trend_c_per_decade": linear_slope_per_decade(years, corrected_residual),
        },
        "correlation": float(np.corrcoef(observed, corrected)[0, 1]),
    }


def lamma_overlap(series: dict, site_key: str) -> np.ndarray:
    years = [int(year) for year in series["years"]]
    values = series[site_key]
    lookup = {year: float(value) for year, value in zip(years, values)}
    missing = [year for year in OVERLAP_YEARS if year not in lookup]
    if missing:
        raise SystemExit(f"LaMMA reference missing overlap years: {missing}")
    return np.asarray([lookup[year] for year in OVERLAP_YEARS], dtype=float)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lamma-json", default="data/meteo-clima-minmax-poc.json")
    ap.add_argument("--era5", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    base = json.loads(Path(args.lamma_json).read_text(encoding="utf-8"))
    era5 = pd.read_csv(args.era5)
    required = {"municipality", "year", *VARS.values()}
    missing = required - set(era5.columns)
    if missing:
        raise SystemExit(f"ERA5 file missing columns: {sorted(missing)}")
    era5["year"] = era5["year"].astype(int)

    output = {
        "version": "poc-2",
        "status": "draft",
        "coverage": {"from": 1995, "to": 2025},
        "source": "Consorzio LaMMA 1 km + Copernicus ERA5-Land hourly reanalysis",
        "method": (
            "1995-2015 LaMMA con pesatura frazionaria; 2016-2025 ERA5-Land orario, "
            "Tmin/Tmax giornaliere calcolate localmente da 24 campioni UTC, pesatura "
            "frazionaria e correzione additiva del bias comunale sul periodo 1995-2015."
        ),
        "definition": base.get("definition", {}),
        "sourcePeriods": [
            {
                "from": 1995,
                "to": 2015,
                "class": "INTERPOLATED_OBSERVATIONS",
                "detail": "Consorzio LaMMA, raster giornalieri 1 km",
            },
            {
                "from": 2016,
                "to": 2025,
                "class": "CALIBRATED_REANALYSIS",
                "detail": (
                    "Copernicus ERA5-Land orario; Tmin/Tmax giornaliere calcolate "
                    "localmente dalla temperatura a 2 m"
                ),
            },
        ],
        "municipalities": {},
    }
    diagnostics = {
        "overlap": [1995, 2015],
        "calibration": "additive per municipality and variable",
        "bias_sign": "ERA5-Land minus LaMMA",
        "residual_sign": "LaMMA minus ERA5-Land",
        "municipalities": {},
    }

    overlap_year_array = np.asarray(OVERLAP_YEARS, dtype=float)

    for municipality, series in base["municipalities"].items():
        er = era5[
            (era5.municipality == municipality) & era5.year.between(1995, 2025)
        ].sort_values("year")
        if er.year.tolist() != FULL_YEARS:
            raise SystemExit(f"{municipality}: ERA5 coverage is not 1995-2025")

        offsets = {}
        municipality_diag = {}
        result = {"years": FULL_YEARS.copy()}
        for site_key, csv_key in VARS.items():
            lamma_values = lamma_overlap(series, site_key)
            raw_overlap = er[er.year <= 2015][csv_key].to_numpy(dtype=float)
            offset = float(np.mean(lamma_values - raw_overlap))
            offsets[site_key] = offset
            municipality_diag[site_key] = score(
                overlap_year_array, lamma_values, raw_overlap, offset
            )
            post = er[er.year >= 2016][csv_key].to_numpy(dtype=float) + offset
            values = np.concatenate([lamma_values, post])
            result[site_key] = [round(float(value), 3) for value in values]

        result["latestComplete"] = {
            "year": 2025,
            "tmin": result["tmin"][-1],
            "tmax": result["tmax"][-1],
        }
        result["calibration"] = {
            "period": [1995, 2015],
            "tmin_offset_c": round(offsets["tmin"], 6),
            "tmax_offset_c": round(offsets["tmax"], 6),
        }
        output["municipalities"][municipality] = result
        diagnostics["municipalities"][municipality] = municipality_diag

    corrected_rmse = []
    corrected_mae = []
    residual_trends = []
    for municipality_diag in diagnostics["municipalities"].values():
        for variable_diag in municipality_diag.values():
            corrected_rmse.append(variable_diag["after"]["rmse_c"])
            corrected_mae.append(variable_diag["after"]["mae_c"])
            residual_trends.append(abs(variable_diag["after"]["residual_trend_c_per_decade"]))
    diagnostics["summary"] = {
        "max_corrected_rmse_c": float(max(corrected_rmse)),
        "mean_corrected_rmse_c": float(np.mean(corrected_rmse)),
        "max_corrected_mae_c": float(max(corrected_mae)),
        "max_abs_residual_trend_c_per_decade": float(max(residual_trends)),
        "note": (
            "La correzione additiva azzera il bias medio sul periodo comune. "
            "RMSE/MAE e trend dei residui restano diagnostici di adeguatezza, "
            "senza forzare artificialmente pendenza o variabilità della rianalisi."
        ),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    out.with_suffix(".diagnostics.json").write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"[minmax-site] wrote {len(output['municipalities'])} municipalities, "
        f"1995-2025 -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
