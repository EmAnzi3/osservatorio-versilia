#!/usr/bin/env python3
"""Build the site Tmin/Tmax series for 1975-2025.

LaMMA remains the primary source for 1995-2015. ERA5-Land supplies 1975-1994
and 2016-2025. Independent SIR observations are used as a gate on temporal
behaviour: when SIR supports ERA5-Land over the divergent LaMMA Tmin/Tmax
trends, the ERA5 trend is preserved and only the level is anchored to the
recent LaMMA overlap.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {"tmin": "tmin_mean_c", "tmax": "tmax_mean_c"}
OVERLAP_YEARS = list(range(1995, 2016))
HANDOVER_YEARS = list(range(2011, 2016))
FULL_YEARS = list(range(1975, 2026))


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


def metrics(years: np.ndarray, observed: np.ndarray, estimate: np.ndarray) -> dict:
    residual = observed - estimate
    return {
        "n": int(len(years)),
        "mean_bias_estimate_minus_lamma_c": float(np.mean(estimate - observed)),
        "rmse_c": float(np.sqrt(np.mean(residual**2))),
        "mae_c": float(np.mean(np.abs(residual))),
        "residual_trend_lamma_minus_estimate_c_per_decade": linear_slope_per_decade(
            years, residual
        ),
        "correlation": float(np.corrcoef(observed, estimate)[0, 1]) if len(years) > 1 else None,
    }


def lamma_overlap(series: dict, site_key: str) -> np.ndarray:
    years = [int(year) for year in series["years"]]
    values = series[site_key]
    lookup = {year: float(value) for year, value in zip(years, values)}
    missing = [year for year in OVERLAP_YEARS if year not in lookup]
    if missing:
        raise SystemExit(f"LaMMA reference missing overlap years: {missing}")
    return np.asarray([lookup[year] for year in OVERLAP_YEARS], dtype=float)


def load_sir_gate(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    station_years = int(payload.get("strict_station_years", 0))
    stations = int(payload.get("strict_stations", 0))
    if station_years < 20 or stations < 2:
        raise SystemExit(
            f"Independent SIR gate too small: station_years={station_years}, stations={stations}"
        )

    summary = {
        "strict_station_years": station_years,
        "strict_stations": stations,
        "period": payload.get("period"),
        "variables": {},
        "spatial_caveat": (
            "Strict overlap evidence is limited to the SIR stations with validated, >=95% "
            "complete Tmin/Tmax series; it validates temporal behaviour, not municipal level."
        ),
    }
    for variable in VARS:
        block = payload.get("variables", {}).get(variable, {})
        preferred_trend = block.get("preferred_by_abs_residual_trend")
        preferred_rmse = block.get("preferred_by_anomaly_rmse")
        if preferred_trend != "ERA5-Land" or preferred_rmse != "ERA5-Land":
            raise SystemExit(
                f"SIR gate does not support preserving ERA5-Land {variable} temporal evolution: "
                f"trend={preferred_trend}, rmse={preferred_rmse}"
            )
        summary["variables"][variable] = {
            "preferred_by_abs_residual_trend": preferred_trend,
            "preferred_by_anomaly_rmse": preferred_rmse,
            "LaMMA": {
                "rmse_anomaly_c": block["LaMMA"]["rmse_anomaly_c"],
                "fixed_effect_residual_trend_c_per_decade": block["LaMMA"][
                    "fixed_effect_residual_trend_c_per_decade"
                ],
            },
            "ERA5-Land": {
                "rmse_anomaly_c": block["ERA5-Land"]["rmse_anomaly_c"],
                "fixed_effect_residual_trend_c_per_decade": block["ERA5-Land"][
                    "fixed_effect_residual_trend_c_per_decade"
                ],
            },
        }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lamma-json", default="data/meteo-clima-minmax-poc.json")
    ap.add_argument("--era5", required=True)
    ap.add_argument("--sir-comparison", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    base = json.loads(Path(args.lamma_json).read_text(encoding="utf-8"))
    era5 = pd.read_csv(args.era5)
    required = {"municipality", "year", *VARS.values()}
    missing = required - set(era5.columns)
    if missing:
        raise SystemExit(f"ERA5 file missing columns: {sorted(missing)}")
    era5["year"] = era5["year"].astype(int)
    sir_gate = load_sir_gate(args.sir_comparison)

    output = {
        "version": "poc-4",
        "status": "draft",
        "coverage": {"from": 1975, "to": 2025},
        "source": "Consorzio LaMMA 1 km + Copernicus ERA5-Land ARCO hourly reanalysis",
        "method": (
            "1975-1994 e 2016-2025 ERA5-Land ARCO orario; 1995-2015 LaMMA con "
            "pesatura frazionaria. Le Tmin/Tmax giornaliere ERA5-Land sono calcolate "
            "localmente da 24 campioni UTC e aggregate con pesatura frazionaria comunale. "
            "Il trend temporale ERA5-Land viene preservato perché il confronto indipendente "
            "con SIR lo supporta rispetto alla deriva LaMMA; il solo livello ERA5-Land viene "
            "raccordato con un offset comunale medio sul quinquennio 2011-2015, applicato "
            "in modo costante sia al tratto precedente al 1995 sia a quello successivo al 2015."
        ),
        "definition": base.get("definition", {}),
        "sourcePeriods": [
            {
                "from": 1975,
                "to": 1994,
                "class": "CALIBRATED_REANALYSIS",
                "detail": (
                    "Copernicus ERA5-Land ARCO orario; Tmin/Tmax giornaliere calcolate "
                    "localmente dalla temperatura a 2 m; offset di livello 2011-2015"
                ),
            },
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
                    "Copernicus ERA5-Land ARCO orario; Tmin/Tmax giornaliere calcolate "
                    "localmente dalla temperatura a 2 m; offset di livello 2011-2015"
                ),
            },
        ],
        "municipalities": {},
    }
    diagnostics = {
        "coverage": [1975, 2025],
        "overlap": [1995, 2015],
        "handover_anchor": [2011, 2015],
        "calibration": (
            "constant municipal level offset from mean LaMMA-minus-ERA5 residual in 2011-2015; "
            "the same offset is applied to ERA5-Land in 1975-1994 and 2016-2025; ERA5 temporal "
            "evolution is preserved after independent SIR validation"
        ),
        "bias_sign": "estimate minus LaMMA",
        "residual_sign": "LaMMA minus estimate",
        "sir_temporal_gate": sir_gate,
        "municipalities": {},
    }

    overlap_year_array = np.asarray(OVERLAP_YEARS, dtype=float)
    handover_mask = np.isin(overlap_year_array.astype(int), HANDOVER_YEARS)
    handover_year_array = overlap_year_array[handover_mask]

    endpoint_gaps = []
    handover_rmses = []
    handover_maes = []

    for municipality, series in base["municipalities"].items():
        er = era5[
            (era5.municipality == municipality) & era5.year.between(1975, 2025)
        ].sort_values("year")
        if er.year.tolist() != FULL_YEARS:
            raise SystemExit(f"{municipality}: ERA5 coverage is not 1975-2025")

        offsets = {}
        municipality_diag = {}
        result = {"years": FULL_YEARS.copy()}
        for site_key, csv_key in VARS.items():
            lamma_values = lamma_overlap(series, site_key)
            raw_overlap = er[er.year.between(1995, 2015)][csv_key].to_numpy(dtype=float)
            residual = lamma_values - raw_overlap
            full_mean_offset = float(np.mean(residual))
            handover_offset = float(np.mean(residual[handover_mask]))
            offsets[site_key] = handover_offset

            full_mean_corrected = raw_overlap + full_mean_offset
            handover_corrected = raw_overlap + handover_offset
            endpoint_gap = float(handover_corrected[-1] - lamma_values[-1])
            endpoint_gaps.append(abs(endpoint_gap))

            handover_metrics = metrics(
                handover_year_array,
                lamma_values[handover_mask],
                handover_corrected[handover_mask],
            )
            handover_rmses.append(handover_metrics["rmse_c"])
            handover_maes.append(handover_metrics["mae_c"])

            municipality_diag[site_key] = {
                "full_overlap_raw": metrics(overlap_year_array, lamma_values, raw_overlap),
                "full_overlap_full_mean_additive": {
                    "offset_c": full_mean_offset,
                    **metrics(overlap_year_array, lamma_values, full_mean_corrected),
                },
                "selected_handover_anchor": {
                    "period": [HANDOVER_YEARS[0], HANDOVER_YEARS[-1]],
                    "offset_c": handover_offset,
                    "metrics_2011_2015": handover_metrics,
                    "same_year_gap_2015_corrected_era5_minus_lamma_c": endpoint_gap,
                    "full_overlap_metrics_if_applied_retroactively": metrics(
                        overlap_year_array, lamma_values, handover_corrected
                    ),
                },
            }

            pre = er[er.year <= 1994][csv_key].to_numpy(dtype=float) + handover_offset
            post = er[er.year >= 2016][csv_key].to_numpy(dtype=float) + handover_offset
            values = np.concatenate([pre, lamma_values, post])
            result[site_key] = [round(float(value), 3) for value in values]

        result["latestComplete"] = {
            "year": 2025,
            "tmin": result["tmin"][-1],
            "tmax": result["tmax"][-1],
        }
        result["calibration"] = {
            "strategy": "recent-overlap level anchor; ERA5 temporal evolution preserved",
            "period": [HANDOVER_YEARS[0], HANDOVER_YEARS[-1]],
            "independent_temporal_validation": "SIR Toscana",
            "tmin_offset_c": round(offsets["tmin"], 6),
            "tmax_offset_c": round(offsets["tmax"], 6),
        }
        output["municipalities"][municipality] = result
        diagnostics["municipalities"][municipality] = municipality_diag

    diagnostics["summary"] = {
        "mean_handover_rmse_c": float(np.mean(handover_rmses)),
        "max_handover_rmse_c": float(max(handover_rmses)),
        "mean_handover_mae_c": float(np.mean(handover_maes)),
        "max_abs_same_year_gap_2015_c": float(max(endpoint_gaps)),
        "note": (
            "The large 1995-2015 LaMMA-vs-ERA5 residual trend is not propagated outside the "
            "LaMMA interval. Independent SIR anomaly/trend diagnostics support ERA5-Land "
            "temporal evolution; LaMMA therefore anchors the ERA5 level over 2011-2015 only, "
            "with one constant municipal offset used for both 1975-1994 and 2016-2025."
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
        f"1975-2025 -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
