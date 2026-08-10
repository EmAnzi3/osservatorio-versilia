#!/usr/bin/env python3
"""Extend the site Tmin/Tmax JSON from LaMMA 1995-2015 to 2025.

The committed 1995-2015 JSON is the LaMMA reference. Raw ERA5-Land annual
means of daily minima/maxima are calibrated additively per municipality on the
full 1995-2015 overlap and used for 2016-2025 only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {"tmin": "tmin_mean_c", "tmax": "tmax_mean_c"}


def score(observed: np.ndarray, raw: np.ndarray, offset: float) -> dict:
    corrected = raw + offset
    return {
        "offset_c": float(offset),
        "raw_rmse_c": float(np.sqrt(np.mean((observed - raw) ** 2))),
        "corrected_rmse_c": float(np.sqrt(np.mean((observed - corrected) ** 2))),
        "raw_mae_c": float(np.mean(np.abs(observed - raw))),
        "corrected_mae_c": float(np.mean(np.abs(observed - corrected))),
        "correlation": float(np.corrcoef(observed, corrected)[0, 1]),
    }


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
        "source": "Consorzio LaMMA 1 km + Copernicus ERA5-Land daily statistics",
        "method": "1995-2015 LaMMA con pesatura frazionaria; 2016-2025 ERA5-Land con pesatura frazionaria e correzione additiva del bias comunale sul periodo 1995-2015.",
        "definition": base.get("definition", {}),
        "sourcePeriods": [
            {"from": 1995, "to": 2015, "class": "INTERPOLATED_OBSERVATIONS", "detail": "Consorzio LaMMA, raster giornalieri 1 km"},
            {"from": 2016, "to": 2025, "class": "CALIBRATED_REANALYSIS", "detail": "Copernicus ERA5-Land, statistiche giornaliere da temperatura oraria"},
        ],
        "municipalities": {},
    }
    diagnostics = {
        "overlap": [1995, 2015],
        "calibration": "additive per municipality and variable",
        "municipalities": {},
    }

    for municipality, series in base["municipalities"].items():
        years = [int(y) for y in series["years"]]
        if years != list(range(1995, 2016)):
            raise SystemExit(f"{municipality}: unexpected LaMMA years {years[:2]}...{years[-2:]}")
        er = era5[(era5.municipality == municipality) & era5.year.between(1995, 2025)].sort_values("year")
        if er.year.tolist() != list(range(1995, 2026)):
            raise SystemExit(f"{municipality}: ERA5 coverage is not 1995-2025")

        offsets = {}
        municipality_diag = {}
        result = {"years": list(range(1995, 2026))}
        for site_key, csv_key in VARS.items():
            lamma_values = np.asarray(series[site_key], dtype=float)
            raw_overlap = er[er.year <= 2015][csv_key].to_numpy(dtype=float)
            offset = float(np.mean(lamma_values - raw_overlap))
            offsets[site_key] = offset
            municipality_diag[site_key] = score(lamma_values, raw_overlap, offset)
            post = er[er.year >= 2016][csv_key].to_numpy(dtype=float) + offset
            values = np.concatenate([lamma_values, post])
            result[site_key] = [round(float(value), 3) for value in values]

        result["calibration"] = {
            "period": [1995, 2015],
            "tmin_offset_c": round(offsets["tmin"], 6),
            "tmax_offset_c": round(offsets["tmax"], 6),
        }
        output["municipalities"][municipality] = result
        diagnostics["municipalities"][municipality] = municipality_diag

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    out.with_suffix(".diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[minmax-site] wrote {len(output['municipalities'])} municipalities, 1995-2025 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
