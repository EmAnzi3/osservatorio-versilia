#!/usr/bin/env python3
"""Stitch LaMMA 1995-2015 Tmin/Tmax with calibrated ERA5-Land 2016-2025.

LaMMA remains the primary source in its native daily-raster period. ERA5-Land
annual means of daily minima/maxima are corrected additively per municipality
using the full 1995-2015 overlap, then used only after 2015.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

TARGETS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
VARS = ["tmin_mean_c", "tmax_mean_c"]


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a - b)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lamma", required=True)
    parser.add_argument("--era5", required=True)
    parser.add_argument("--output", default="reports/runtime/final/municipal-climate-minmax-1995-2025.csv")
    args = parser.parse_args()

    lamma = pd.read_csv(args.lamma)
    era5 = pd.read_csv(args.era5)
    for frame, label in ((lamma, "LaMMA"), (era5, "ERA5")):
        missing = {"municipality", "year", *VARS} - set(frame.columns)
        if missing:
            raise SystemExit(f"{label} missing columns: {sorted(missing)}")
        frame["year"] = frame["year"].astype(int)

    rows: list[dict] = []
    diagnostics: dict[str, dict] = {}

    for municipality in TARGETS:
        lm = lamma[(lamma.municipality == municipality) & lamma.year.between(1995, 2015)].copy()
        er = era5[(era5.municipality == municipality) & era5.year.between(1995, 2025)].copy()
        overlap = lm[["year", *VARS]].merge(er[["year", *VARS]], on="year", suffixes=("_lamma", "_era5"))
        if len(overlap) != 21:
            raise SystemExit(f"{municipality}: expected 21 overlap years, got {len(overlap)}")

        offsets: dict[str, float] = {}
        diag_vars: dict[str, dict] = {}
        for var in VARS:
            observed = overlap[f"{var}_lamma"].to_numpy(dtype=float)
            raw = overlap[f"{var}_era5"].to_numpy(dtype=float)
            offset = float(np.mean(observed - raw))
            corrected = raw + offset
            offsets[var] = offset
            diag_vars[var] = {
                "offset_c": offset,
                "overlap_years": [1995, 2015],
                "n": int(len(overlap)),
                "raw_rmse_c": rmse(observed, raw),
                "corrected_rmse_c": rmse(observed, corrected),
                "raw_mae_c": mae(observed, raw),
                "corrected_mae_c": mae(observed, corrected),
                "correlation": float(np.corrcoef(observed, corrected)[0, 1]),
            }
        diagnostics[municipality] = diag_vars

        for _, row in lm.sort_values("year").iterrows():
            rows.append({
                "municipality": municipality,
                "year": int(row.year),
                "period_status": "complete",
                "tmin_mean_c": float(row.tmin_mean_c),
                "tmax_mean_c": float(row.tmax_mean_c),
                "source_class": "INTERPOLATED_OBSERVATIONS",
                "source_detail": "Consorzio LaMMA daily 1 km rasters",
                "calibration": "none",
            })
        post = er[er.year.between(2016, 2025)].sort_values("year")
        if len(post) != 10:
            raise SystemExit(f"{municipality}: expected 10 ERA5 post-LaMMA years, got {len(post)}")
        for _, row in post.iterrows():
            rows.append({
                "municipality": municipality,
                "year": int(row.year),
                "period_status": "complete",
                "tmin_mean_c": float(row.tmin_mean_c) + offsets["tmin_mean_c"],
                "tmax_mean_c": float(row.tmax_mean_c) + offsets["tmax_mean_c"],
                "source_class": "CALIBRATED_REANALYSIS",
                "source_detail": "Copernicus ERA5-Land daily statistics",
                "calibration": "additive municipal bias correction on LaMMA overlap 1995-2015",
            })

    frame = pd.DataFrame(rows).sort_values(["municipality", "year"])
    expected = len(TARGETS) * 31
    if len(frame) != expected:
        raise SystemExit(f"Expected {expected} rows, got {len(frame)}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    diag_path = out.with_suffix(".diagnostics.json")
    diag_path.write_text(
        json.dumps(
            {
                "coverage": [1995, 2025],
                "primary_period": "LaMMA 1995-2015",
                "reanalysis_period": "calibrated ERA5-Land 2016-2025",
                "calibration": "additive per municipality and variable over 1995-2015",
                "diagnostics": diagnostics,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[minmax-stitch] wrote {len(frame)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
