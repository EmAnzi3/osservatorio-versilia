#!/usr/bin/env python3
"""Compare LaMMA and ERA5-Land Tmin/Tmax trends against independent SIR observations.

The comparison is intentionally anomaly-based because SIR stations are points
while the climate series are municipality-wide areal means. For each station,
the mean station-vs-source level offset is removed before RMSE/MAE and pooled
correlation are computed. Trend mismatch is estimated with station fixed
effects by regressing the demeaned residual on demeaned year.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {
    "tmin": ("tmin_mean_c_observed", "tmin_mean_c"),
    "tmax": ("tmax_mean_c_observed", "tmax_mean_c"),
}
OVERLAP_FROM = 1995
OVERLAP_TO = 2015
MIN_COMPLETENESS = 0.95


def lamma_frame(path: str) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for municipality, series in payload["municipalities"].items():
        for year, tmin, tmax in zip(series["years"], series["tmin"], series["tmax"]):
            rows.append(
                {
                    "municipality": municipality,
                    "year": int(year),
                    "tmin_mean_c": float(tmin),
                    "tmax_mean_c": float(tmax),
                }
            )
    return pd.DataFrame(rows)


def fixed_effect_residual_trend_per_decade(frame: pd.DataFrame, residual_col: str) -> float:
    xs = []
    ys = []
    for _, station in frame.groupby("station_id"):
        x = station["year"].to_numpy(dtype=float)
        y = station[residual_col].to_numpy(dtype=float)
        xs.append(x - np.mean(x))
        ys.append(y - np.mean(y))
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    denominator = float(np.sum(x * x))
    if denominator == 0:
        return 0.0
    return float(np.sum(x * y) / denominator * 10.0)


def station_adjusted_metrics(frame: pd.DataFrame, observed_col: str, source_col: str) -> dict:
    work = frame.copy()
    work["residual"] = work[observed_col] - work[source_col]
    work["station_offset"] = work.groupby("station_id")["residual"].transform("mean")
    work["source_aligned"] = work[source_col] + work["station_offset"]
    work["anomaly_residual"] = work[observed_col] - work["source_aligned"]
    work["obs_anomaly"] = work[observed_col] - work.groupby("station_id")[observed_col].transform("mean")
    work["src_anomaly"] = work[source_col] - work.groupby("station_id")[source_col].transform("mean")

    per_station = []
    for station_id, station in work.groupby("station_id"):
        years = station["year"].to_numpy(dtype=float)
        obs = station[observed_col].to_numpy(dtype=float)
        src = station[source_col].to_numpy(dtype=float)
        residual = obs - src
        n = len(station)
        if n >= 3 and len(np.unique(years)) >= 2:
            obs_slope = float(np.polyfit(years, obs, 1)[0] * 10.0)
            src_slope = float(np.polyfit(years, src, 1)[0] * 10.0)
            residual_slope = float(np.polyfit(years, residual, 1)[0] * 10.0)
        else:
            obs_slope = src_slope = residual_slope = None
        per_station.append(
            {
                "station_id": station_id,
                "station_label": str(station["station_label"].iloc[0]),
                "municipality": str(station["municipality"].iloc[0]),
                "n": int(n),
                "from": int(station["year"].min()),
                "to": int(station["year"].max()),
                "station_level_offset_c": float(station["station_offset"].iloc[0]),
                "observed_trend_c_per_decade": obs_slope,
                "source_trend_c_per_decade": src_slope,
                "residual_trend_c_per_decade": residual_slope,
            }
        )

    corr = float(np.corrcoef(work["obs_anomaly"], work["src_anomaly"])[0, 1])
    return {
        "n_station_years": int(len(work)),
        "stations": int(work["station_id"].nunique()),
        "rmse_anomaly_c": float(np.sqrt(np.mean(work["anomaly_residual"] ** 2))),
        "mae_anomaly_c": float(np.mean(np.abs(work["anomaly_residual"]))),
        "correlation_pooled_anomalies": corr,
        "fixed_effect_residual_trend_c_per_decade": fixed_effect_residual_trend_per_decade(
            work, "residual"
        ),
        "per_station": per_station,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sir", required=True)
    ap.add_argument("--lamma-json", required=True)
    ap.add_argument("--era5", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    sir = pd.read_csv(args.sir)
    era5 = pd.read_csv(args.era5)
    lamma = lamma_frame(args.lamma_json)
    for frame in (sir, era5, lamma):
        frame["year"] = frame["year"].astype(int)

    strict = sir[
        sir["year"].between(OVERLAP_FROM, OVERLAP_TO)
        & (sir["validation_status_table"] == "VALIDATED")
        & (sir["temperature_completeness"] >= MIN_COMPLETENESS)
    ].copy()
    if strict.empty:
        raise SystemExit("No strict SIR Tmin/Tmax observations available for 1995-2015")

    output = {
        "period": [OVERLAP_FROM, OVERLAP_TO],
        "sir_filter": {
            "validation_status_table": "VALIDATED",
            "minimum_temperature_completeness": MIN_COMPLETENESS,
        },
        "method": (
            "Point-vs-area level offsets are removed per SIR station. RMSE/MAE and pooled "
            "correlation use station anomalies. Trend mismatch uses station fixed effects "
            "on observed-minus-source residuals."
        ),
        "strict_station_years": int(len(strict)),
        "strict_stations": int(strict["station_id"].nunique()),
        "variables": {},
    }

    for variable, (observed_col, source_col) in VARS.items():
        if observed_col not in strict.columns:
            raise SystemExit(f"SIR file missing {observed_col}")
        base = strict[
            ["municipality", "station_label", "station_id", "year", observed_col]
        ].dropna()
        joined = base.merge(
            lamma[["municipality", "year", source_col]],
            on=["municipality", "year"],
            how="inner",
        ).rename(columns={source_col: "lamma_value"})
        joined = joined.merge(
            era5[["municipality", "year", source_col]],
            on=["municipality", "year"],
            how="inner",
        ).rename(columns={source_col: "era5_value"})
        if len(joined) != len(base):
            raise SystemExit(
                f"{variable}: source coverage mismatch; strict={len(base)}, joined={len(joined)}"
            )

        lamma_metrics = station_adjusted_metrics(joined, observed_col, "lamma_value")
        era5_metrics = station_adjusted_metrics(joined, observed_col, "era5_value")
        lamma_abs_trend = abs(lamma_metrics["fixed_effect_residual_trend_c_per_decade"])
        era5_abs_trend = abs(era5_metrics["fixed_effect_residual_trend_c_per_decade"])
        preferred_trend = "LaMMA" if lamma_abs_trend < era5_abs_trend else "ERA5-Land"
        preferred_rmse = (
            "LaMMA"
            if lamma_metrics["rmse_anomaly_c"] < era5_metrics["rmse_anomaly_c"]
            else "ERA5-Land"
        )
        output["variables"][variable] = {
            "LaMMA": lamma_metrics,
            "ERA5-Land": era5_metrics,
            "preferred_by_abs_residual_trend": preferred_trend,
            "preferred_by_anomaly_rmse": preferred_rmse,
        }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
