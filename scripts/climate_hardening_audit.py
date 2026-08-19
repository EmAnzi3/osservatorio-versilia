#!/usr/bin/env python3
"""Audit a homogeneous ERA5-Land alternative for the published climate series.

This script is deliberately non-publishing: it produces a candidate dataset and
machine/human-readable diagnostics, but never edits data/meteo-clima-poc.json.

Candidate strategy:
- one continuous ERA5-Land annual series for 1975-2025;
- temperature level aligned to LaMMA with an additive municipal offset;
- precipitation level aligned to LaMMA with a multiplicative municipal ratio;
- no slope/trend correction;
- SIR validated station data used only as independent temporal evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

OVERLAP = (1995, 2015)
RECENT_ANCHOR = (2011, 2015)
TREND = (1975, 2025)
SENSITIVITY_TREND = (1979, 2025)


def linear_stats(years: Iterable[int], values: Iterable[float], start: int, end: int) -> dict:
    frame = pd.DataFrame({"year": list(years), "value": list(values)})
    frame = frame[frame.year.between(start, end)].dropna()
    if len(frame) < 3:
        raise ValueError(f"Insufficient points for trend {start}-{end}: {len(frame)}")
    x = frame.year.to_numpy(dtype=float)
    y = frame.value.to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum((y - fitted) ** 2))
    start_value = float(intercept + slope * start)
    end_value = float(intercept + slope * end)
    return {
        "from": start,
        "to": end,
        "n": int(len(frame)),
        "slope_per_decade": float(slope * 10.0),
        "delta": float(end_value - start_value),
        "start_value": start_value,
        "end_value": end_value,
        "r2": 0.0 if ss_tot == 0 else float(max(0.0, 1.0 - ss_res / ss_tot)),
    }


def station_adjusted_metrics(frame: pd.DataFrame, observed_col: str, source_col: str) -> dict:
    work = frame[["station_id", "year", observed_col, source_col]].dropna().copy()
    if work.empty:
        return {"n": 0, "stations": 0}
    work["residual"] = work[observed_col] - work[source_col]
    work["station_offset"] = work.groupby("station_id")["residual"].transform("mean")
    work["aligned"] = work[source_col] + work["station_offset"]
    work["anomaly_residual"] = work[observed_col] - work["aligned"]
    work["obs_anomaly"] = work[observed_col] - work.groupby("station_id")[observed_col].transform("mean")
    work["src_anomaly"] = work[source_col] - work.groupby("station_id")[source_col].transform("mean")

    xs, ys = [], []
    for _, station in work.groupby("station_id"):
        x = station.year.to_numpy(dtype=float)
        y = station.residual.to_numpy(dtype=float)
        xs.append(x - np.mean(x))
        ys.append(y - np.mean(y))
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    denominator = float(np.sum(x * x))
    residual_trend = 0.0 if denominator == 0 else float(np.sum(x * y) / denominator * 10.0)
    corr = None
    if len(work) > 1 and np.std(work.obs_anomaly) > 0 and np.std(work.src_anomaly) > 0:
        corr = float(np.corrcoef(work.obs_anomaly, work.src_anomaly)[0, 1])
    return {
        "n": int(len(work)),
        "stations": int(work.station_id.nunique()),
        "rmse_anomaly": float(np.sqrt(np.mean(work.anomaly_residual ** 2))),
        "mae_anomaly": float(np.mean(np.abs(work.anomaly_residual))),
        "correlation_anomalies": corr,
        "fixed_effect_residual_trend_per_decade": residual_trend,
    }


def current_frame(payload: dict) -> pd.DataFrame:
    rows = []
    for municipality, series in payload["municipalities"].items():
        for year, temperature, precipitation in zip(series["years"], series["temperature"], series["precipitation"]):
            rows.append({
                "municipality": municipality,
                "year": int(year),
                "temperature_current": float(temperature),
                "precipitation_current": float(precipitation),
            })
    return pd.DataFrame(rows)


def build_candidate(lamma: pd.DataFrame, era5: pd.DataFrame, current: dict) -> tuple[dict, dict, pd.DataFrame]:
    required = {"municipality", "year", "tmean_c", "precip_mm"}
    for label, frame in (("LaMMA", lamma), ("ERA5", era5)):
        missing = required - set(frame.columns)
        if missing:
            raise SystemExit(f"{label} missing columns: {sorted(missing)}")
    lamma = lamma.copy(); era5 = era5.copy()
    lamma["year"] = lamma.year.astype(int); era5["year"] = era5.year.astype(int)
    current_df = current_frame(current)
    municipalities = sorted(current["municipalities"])
    out = {
        "version": "candidate-homogeneous-era5-1",
        "status": "audit-only-not-published",
        "coverage": {"from": TREND[0], "to": TREND[1]},
        "method": (
            "Continuous ERA5-Land 1975-2025; additive municipal temperature level calibration "
            "and multiplicative precipitation level calibration against LaMMA 1995-2015. "
            "No temporal slope correction. The candidate is diagnostic only."
        ),
        "municipalities": {},
    }
    diagnostics = {"municipalities": {}}
    candidate_rows = []

    for municipality in municipalities:
        l = lamma[(lamma.municipality == municipality) & lamma.year.between(*OVERLAP)].sort_values("year")
        e = era5[(era5.municipality == municipality) & era5.year.between(*TREND)].sort_values("year")
        expected_years = list(range(TREND[0], TREND[1] + 1))
        if e.year.tolist() != expected_years:
            raise SystemExit(f"{municipality}: ERA5 coverage is not {TREND[0]}-{TREND[1]}")
        paired = l[["year", "tmean_c", "precip_mm"]].merge(
            e[["year", "tmean_c", "precip_mm"]], on="year", suffixes=("_lamma", "_era5"), how="inner"
        ).dropna()
        if len(paired) < 15:
            raise SystemExit(f"{municipality}: insufficient LaMMA/ERA5 overlap: {len(paired)}")

        temp_offset_full = float(np.mean(paired.tmean_c_lamma - paired.tmean_c_era5))
        recent = paired[paired.year.between(*RECENT_ANCHOR)]
        temp_offset_recent = float(np.mean(recent.tmean_c_lamma - recent.tmean_c_era5))
        valid_p = paired[(paired.precip_mm_lamma > 0) & (paired.precip_mm_era5 > 0)]
        precip_ratio = float(np.median(valid_p.precip_mm_lamma / valid_p.precip_mm_era5))

        temperature = e.tmean_c.to_numpy(dtype=float) + temp_offset_full
        precipitation = e.precip_mm.to_numpy(dtype=float) * precip_ratio
        years = e.year.astype(int).tolist()
        out["municipalities"][municipality] = {
            "years": years,
            "temperature": [round(float(v), 3) for v in temperature],
            "precipitation": [round(float(v), 1) for v in precipitation],
            "latestComplete": {
                "year": TREND[1],
                "temperature": round(float(temperature[-1]), 3),
                "precipitation": round(float(precipitation[-1]), 1),
            },
            "calibration": {
                "temperature_offset_full_overlap_c": round(temp_offset_full, 6),
                "temperature_offset_recent_anchor_c": round(temp_offset_recent, 6),
                "precipitation_ratio_full_overlap": round(precip_ratio, 8),
                "overlap": list(OVERLAP),
                "recent_temperature_anchor": list(RECENT_ANCHOR),
            },
        }
        for year, t, p in zip(years, temperature, precipitation):
            candidate_rows.append({"municipality": municipality, "year": year, "temperature_candidate": t, "precipitation_candidate": p})

        current_m = current_df[current_df.municipality == municipality]
        candidate_m = pd.DataFrame(candidate_rows)
        candidate_m = candidate_m[candidate_m.municipality == municipality]
        joined = current_m.merge(candidate_m, on=["municipality", "year"], how="inner")
        trend_current_t = linear_stats(joined.year, joined.temperature_current, *TREND)
        trend_candidate_t = linear_stats(joined.year, joined.temperature_candidate, *TREND)
        trend_current_p = linear_stats(joined.year, joined.precipitation_current, *TREND)
        trend_candidate_p = linear_stats(joined.year, joined.precipitation_candidate, *TREND)
        sensitivity_t = linear_stats(joined.year, joined.temperature_candidate, *SENSITIVITY_TREND)
        sensitivity_p = linear_stats(joined.year, joined.precipitation_candidate, *SENSITIVITY_TREND)
        pre = joined[joined.year.between(2017, 2019)]
        post = joined[joined.year.between(2020, 2022)]
        diagnostics["municipalities"][municipality] = {
            "calibration": out["municipalities"][municipality]["calibration"],
            "temperature": {
                "current_trend": trend_current_t,
                "candidate_trend": trend_candidate_t,
                "candidate_1979_2025": sensitivity_t,
                "trend_delta_change_c": float(trend_candidate_t["delta"] - trend_current_t["delta"]),
                "latest_change_c": float(joined.iloc[-1].temperature_candidate - joined.iloc[-1].temperature_current),
                "temperature_offset_anchor_sensitivity_c": float(temp_offset_recent - temp_offset_full),
                "mean_2017_2019": float(pre.temperature_candidate.mean()),
                "mean_2020_2022": float(post.temperature_candidate.mean()),
                "step_2020_window_c": float(post.temperature_candidate.mean() - pre.temperature_candidate.mean()),
            },
            "precipitation": {
                "current_trend": trend_current_p,
                "candidate_trend": trend_candidate_p,
                "candidate_1979_2025": sensitivity_p,
                "trend_delta_change_mm": float(trend_candidate_p["delta"] - trend_current_p["delta"]),
                "latest_change_mm": float(joined.iloc[-1].precipitation_candidate - joined.iloc[-1].precipitation_current),
                "mean_2017_2019": float(pre.precipitation_candidate.mean()),
                "mean_2020_2022": float(post.precipitation_candidate.mean()),
                "step_2020_window_mm": float(post.precipitation_candidate.mean() - pre.precipitation_candidate.mean()),
            },
        }
    return out, diagnostics, pd.DataFrame(candidate_rows)


def add_sir_validation(diagnostics: dict, candidate: pd.DataFrame, sir: pd.DataFrame | None) -> None:
    if sir is None or sir.empty:
        diagnostics["sir_validation"] = {"available": False}
        return
    strict_p = sir[(sir.sensor == "pluvio") & (sir.validation_status_table == "VALIDATED")].copy()
    strict_t = sir[(sir.sensor == "termo") & (sir.validation_status_table == "VALIDATED") & (sir.temperature_completeness >= 0.95)].copy()
    joined_t = strict_t.merge(candidate[["municipality", "year", "temperature_candidate"]], on=["municipality", "year"], how="inner")
    joined_p = strict_p.merge(candidate[["municipality", "year", "precipitation_candidate"]], on=["municipality", "year"], how="inner")
    diagnostics["sir_validation"] = {
        "available": True,
        "temperature": station_adjusted_metrics(joined_t, "tmean_c_observed", "temperature_candidate"),
        "precipitation": station_adjusted_metrics(joined_p, "precip_mm_observed", "precipitation_candidate"),
        "note": "Point-vs-area level offsets are removed per station; this tests temporal behaviour, not municipal absolute level.",
    }


def overall_summary(diagnostics: dict) -> dict:
    items = diagnostics["municipalities"]
    t_changes = [abs(v["temperature"]["trend_delta_change_c"]) for v in items.values()]
    p_changes = [abs(v["precipitation"]["trend_delta_change_mm"]) for v in items.values()]
    t_anchor = [abs(v["temperature"]["temperature_offset_anchor_sensitivity_c"]) for v in items.values()]
    t_sensitivity = [abs(v["temperature"]["candidate_trend"]["delta"] - v["temperature"]["candidate_1979_2025"]["delta"]) for v in items.values()]
    p_sensitivity = [abs(v["precipitation"]["candidate_trend"]["delta"] - v["precipitation"]["candidate_1979_2025"]["delta"]) for v in items.values()]
    return {
        "max_abs_temperature_trend_change_c": float(max(t_changes)),
        "max_abs_precipitation_trend_change_mm": float(max(p_changes)),
        "max_abs_temperature_anchor_sensitivity_c": float(max(t_anchor)),
        "max_abs_temperature_1975_vs_1979_delta_c": float(max(t_sensitivity)),
        "max_abs_precipitation_1975_vs_1979_delta_mm": float(max(p_sensitivity)),
        "publication_decision": "manual_review_required",
    }


def markdown_report(diag: dict) -> str:
    summary = diag["summary"]
    lines = [
        "# Climate hardening audit",
        "",
        "This report compares the currently published stitched climate series with a diagnostic homogeneous ERA5-Land candidate. It does **not** authorize publication.",
        "",
        "## Global checks",
        "",
        f"- max |temperature trend change|: **{summary['max_abs_temperature_trend_change_c']:.3f} °C** over 1975–2025",
        f"- max |precipitation trend change|: **{summary['max_abs_precipitation_trend_change_mm']:.1f} mm** over 1975–2025",
        f"- max temperature calibration sensitivity (1995–2015 vs 2011–2015 anchor): **{summary['max_abs_temperature_anchor_sensitivity_c']:.3f} °C**",
        f"- max temperature trend sensitivity 1975 vs 1979 start: **{summary['max_abs_temperature_1975_vs_1979_delta_c']:.3f} °C**",
        f"- max precipitation trend sensitivity 1975 vs 1979 start: **{summary['max_abs_precipitation_1975_vs_1979_delta_mm']:.1f} mm**",
        "",
        "## Municipal detail",
        "",
        "| Comune | Δ trend T candidato-attuale | Δ T 2025 | Δ trend P candidato-attuale | Δ P 2025 |",
        "|---|---:|---:|---:|---:|",
    ]
    for municipality, item in sorted(diag["municipalities"].items()):
        t = item["temperature"]; p = item["precipitation"]
        lines.append(f"| {municipality} | {t['trend_delta_change_c']:+.3f} °C | {t['latest_change_c']:+.3f} °C | {p['trend_delta_change_mm']:+.1f} mm | {p['latest_change_mm']:+.1f} mm |")
    sir = diag.get("sir_validation", {})
    lines += ["", "## SIR independent check", ""]
    if not sir.get("available"):
        lines.append("SIR validation input was not available in this run.")
    else:
        for label in ("temperature", "precipitation"):
            block = sir.get(label, {})
            lines.append(f"- **{label}**: {block.get('n', 0)} station-years, {block.get('stations', 0)} stations; anomaly RMSE {block.get('rmse_anomaly', float('nan')):.3f}; residual trend/decade {block.get('fixed_effect_residual_trend_per_decade', float('nan')):+.3f}.")
        lines.append("- Point-vs-area offsets are removed per station: this is temporal evidence, not an absolute municipal-level validation.")
    lines += ["", "## Decision", "", "**Manual review required.** No canonical climate value is changed by this audit.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lamma", required=True)
    ap.add_argument("--era5", required=True)
    ap.add_argument("--current-json", default="data/meteo-clima-poc.json")
    ap.add_argument("--sir")
    ap.add_argument("--candidate-json", required=True)
    ap.add_argument("--report-json", required=True)
    ap.add_argument("--report-md", required=True)
    args = ap.parse_args()

    current = json.loads(Path(args.current_json).read_text(encoding="utf-8"))
    lamma = pd.read_csv(args.lamma)
    era5 = pd.read_csv(args.era5)
    sir = pd.read_csv(args.sir) if args.sir and Path(args.sir).exists() else None
    candidate, diagnostics, candidate_rows = build_candidate(lamma, era5, current)
    add_sir_validation(diagnostics, candidate_rows, sir)
    diagnostics["summary"] = overall_summary(diagnostics)

    for path in (Path(args.candidate_json), Path(args.report_json), Path(args.report_md)):
        path.parent.mkdir(parents=True, exist_ok=True)
    Path(args.candidate_json).write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.report_json).write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.report_md).write_text(markdown_report(diagnostics), encoding="utf-8")
    print(json.dumps(diagnostics["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
