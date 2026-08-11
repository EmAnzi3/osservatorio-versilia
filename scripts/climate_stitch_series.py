#!/usr/bin/env python3
"""Stitch LaMMA observations/interpolation with raw ERA5-Land into a continuous annual series.

Temperature: additive bias correction per municipality using the overlap.
Precipitation: multiplicative bias correction per municipality using the overlap.
During the LaMMA overlap, LaMMA remains the published primary value. Outside it,
ERA5-Land is published only as CALIBRATED_REANALYSIS. This prevents a source
switch from creating an artificial step in the time series.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OVERLAP_START = 1995
OVERLAP_END = 2015


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lamma", required=True)
    parser.add_argument("--era5", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lamma = pd.read_csv(args.lamma)
    era5 = pd.read_csv(args.era5)
    required = {"municipality", "year", "tmean_c", "precip_mm"}
    for label, df in (("LaMMA", lamma), ("ERA5", era5)):
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{label} missing columns: {sorted(missing)}")

    diagnostics = {}
    output_rows = []
    municipalities = sorted(set(era5["municipality"]) & set(lamma["municipality"]))
    if not municipalities:
        raise SystemExit("No common municipalities")

    for municipality in municipalities:
        l = lamma[(lamma.municipality == municipality) & lamma.year.between(OVERLAP_START, OVERLAP_END)].copy()
        e = era5[(era5.municipality == municipality) & era5.year.between(OVERLAP_START, OVERLAP_END)].copy()
        paired = l[["year", "tmean_c", "precip_mm"]].merge(
            e[["year", "tmean_c", "precip_mm"]], on="year", suffixes=("_lamma", "_era5"), how="inner"
        ).dropna()
        if len(paired) < 10:
            raise SystemExit(f"{municipality}: insufficient overlap, {len(paired)} years")

        temp_offset = float((paired.tmean_c_lamma - paired.tmean_c_era5).mean())
        valid_p = paired[(paired.precip_mm_era5 > 0) & (paired.precip_mm_lamma > 0)]
        precip_ratio = float((valid_p.precip_mm_lamma / valid_p.precip_mm_era5).median())
        temp_rmse_raw = float(np.sqrt(np.mean((paired.tmean_c_lamma - paired.tmean_c_era5) ** 2)))
        temp_rmse_corrected = float(np.sqrt(np.mean((paired.tmean_c_lamma - (paired.tmean_c_era5 + temp_offset)) ** 2)))
        precip_mape_raw = float(np.mean(np.abs((paired.precip_mm_lamma - paired.precip_mm_era5) / paired.precip_mm_lamma)) * 100)
        precip_mape_corrected = float(np.mean(np.abs((paired.precip_mm_lamma - paired.precip_mm_era5 * precip_ratio) / paired.precip_mm_lamma)) * 100)

        diagnostics[municipality] = {
            "overlap_years": paired.year.astype(int).tolist(),
            "temperature_offset_c": temp_offset,
            "precipitation_ratio": precip_ratio,
            "temperature_rmse_raw_c": temp_rmse_raw,
            "temperature_rmse_corrected_c": temp_rmse_corrected,
            "precipitation_mape_raw_pct": precip_mape_raw,
            "precipitation_mape_corrected_pct": precip_mape_corrected,
        }

        l_all = lamma[lamma.municipality == municipality].set_index("year")
        e_all = era5[era5.municipality == municipality].set_index("year")
        for year in sorted(set(e_all.index.astype(int)) | set(l_all.index.astype(int))):
            if year in l_all.index and OVERLAP_START <= year <= OVERLAP_END:
                row = l_all.loc[year]
                output_rows.append({
                    "municipality": municipality,
                    "year": int(year),
                    "period_status": row.get("period_status", "complete"),
                    "tmean_c": float(row.tmean_c),
                    "precip_mm": float(row.precip_mm),
                    "source_class": "INTERPOLATED_OBSERVATIONS",
                    "source_detail": "LaMMA 1 km",
                    "calibration": "none; primary overlap source",
                })
            elif year in e_all.index:
                row = e_all.loc[year]
                output_rows.append({
                    "municipality": municipality,
                    "year": int(year),
                    "period_status": row.get("period_status", "complete"),
                    "tmean_c": float(row.tmean_c) + temp_offset,
                    "precip_mm": float(row.precip_mm) * precip_ratio,
                    "source_class": "CALIBRATED_REANALYSIS",
                    "source_detail": "ERA5-Land calibrated on LaMMA 1995-2015",
                    "calibration": f"T offset {temp_offset:+.3f} C; P ratio {precip_ratio:.4f}",
                })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(output_rows).sort_values(["municipality", "year"])
    result.to_csv(out, index=False)
    out.with_suffix(".diagnostics.json").write_text(
        json.dumps({"overlap": [OVERLAP_START, OVERLAP_END], "municipalities": diagnostics}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[stitch] wrote {len(result)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
