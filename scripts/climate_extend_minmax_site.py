#!/usr/bin/env python3
"""Build a homogeneous site Tmin/Tmax series for 1975-2025.

ERA5-Land supplies the continuous annual Tmin/Tmax evolution from 1975 to
2025. LaMMA 1995-2015 is retained as an independent gridded reference for the
level calibration, while SIR observations gate the temporal behaviour. Because
SIR supports ERA5-Land over the divergent LaMMA Tmin/Tmax trends, no temporal
slope correction is applied: only a constant municipal level offset derived
from the recent 2011-2015 LaMMA overlap is used across the whole ERA5 series.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {"tmin": "tmin_mean_c", "tmax": "tmax_mean_c"}
OVERLAP_YEARS = list(range(1995, 2016))
ANCHOR_YEARS = list(range(2011, 2016))
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
            "Strict overlap evidence is limited to SIR stations with validated, >=95% "
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
        "version": "poc-5",
        "status": "draft",
        "coverage": {"from": 1975, "to": 2025},
        "source": "Copernicus ERA5-Land ARCO hourly reanalysis; level reference Consorzio LaMMA 1 km; temporal validation SIR Toscana",
        "method": (
            "Serie omogenea ERA5-Land ARCO oraria 1975-2025. Le Tmin/Tmax giornaliere "
            "sono calcolate localmente da 24 campioni UTC e aggregate con pesatura "
            "frazionaria comunale. LaMMA 1995-2015 resta il riferimento grigliato per il "
            "livello, ma non sostituisce ERA5-Land nella serie cinquantennale: un solo offset "
            "comunale costante, calcolato sulla media LaMMA-minus-ERA5 del 2011-2015, viene "
            "applicato a tutta la serie. Nessuna correzione della pendenza viene applicata, "
            "perché il confronto indipendente con SIR supporta l'evoluzione temporale ERA5-Land "
            "rispetto alla deriva osservata nella serie LaMMA Tmin/Tmax."
        ),
        "definition": base.get("definition", {}),
        "sourcePeriods": [
            {
                "from": 1975,
                "to": 2025,
                "class": "CALIBRATED_REANALYSIS",
                "detail": (
                    "Copernicus ERA5-Land ARCO orario; Tmin/Tmax giornaliere calcolate "
                    "localmente dalla temperatura a 2 m; offset di livello comunale 2011-2015"
                ),
            }
        ],
        "calibrationReference": {
            "source": "Consorzio LaMMA, raster giornalieri 1 km",
            "available": [1995, 2015],
            "anchor": [2011, 2015],
            "role": "level reference only; not substituted into the homogeneous 1975-2025 trend series",
        },
        "temporalValidation": {
            "source": "SIR Toscana",
            "role": "independent gate supporting preservation of ERA5-Land temporal evolution",
        },
        "municipalities": {},
    }
    diagnostics = {
        "coverage": [1975, 2025],
        "overlap": [1995, 2015],
        "level_anchor": [2011, 2015],
        "calibration": (
            "constant municipal level offset from mean LaMMA-minus-ERA5 residual in 2011-2015; "
            "applied to the complete ERA5-Land 1975-2025 series; no temporal slope correction"
        ),
        "bias_sign": "estimate minus LaMMA",
        "residual_sign": "LaMMA minus estimate",
        "sir_temporal_gate": sir_gate,
        "municipalities": {},
    }

    overlap_year_array = np.asarray(OVERLAP_YEARS, dtype=float)
    anchor_mask = np.isin(overlap_year_array.astype(int), ANCHOR_YEARS)
    anchor_year_array = overlap_year_array[anchor_mask]

    anchor_rmses = []
    anchor_maes = []
    overlap_residual_trends = []

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
            raw_full = er[csv_key].to_numpy(dtype=float)
            raw_overlap = er[er.year.between(1995, 2015)][csv_key].to_numpy(dtype=float)
            residual = lamma_values - raw_overlap
            full_mean_offset = float(np.mean(residual))
            anchor_offset = float(np.mean(residual[anchor_mask]))
            offsets[site_key] = anchor_offset

            full_mean_corrected = raw_overlap + full_mean_offset
            anchor_corrected_overlap = raw_overlap + anchor_offset
            anchor_metrics = metrics(
                anchor_year_array,
                lamma_values[anchor_mask],
                anchor_corrected_overlap[anchor_mask],
            )
            anchor_rmses.append(anchor_metrics["rmse_c"])
            anchor_maes.append(anchor_metrics["mae_c"])
            overlap_residual_trends.append(
                abs(
                    metrics(
                        overlap_year_array,
                        lamma_values,
                        anchor_corrected_overlap,
                    )["residual_trend_lamma_minus_estimate_c_per_decade"]
                )
            )

            municipality_diag[site_key] = {
                "raw_overlap": metrics(overlap_year_array, lamma_values, raw_overlap),
                "full_overlap_mean_additive": {
                    "offset_c": full_mean_offset,
                    **metrics(overlap_year_array, lamma_values, full_mean_corrected),
                },
                "selected_level_anchor": {
                    "period": [ANCHOR_YEARS[0], ANCHOR_YEARS[-1]],
                    "offset_c": anchor_offset,
                    "metrics_2011_2015": anchor_metrics,
                    "full_overlap_metrics_if_compared_to_lamma": metrics(
                        overlap_year_array, lamma_values, anchor_corrected_overlap
                    ),
                },
                "publication_series": (
                    "continuous ERA5-Land 1975-2025 plus selected constant level offset; "
                    "LaMMA overlap is calibration/reference only"
                ),
            }

            calibrated_full = raw_full + anchor_offset
            result[site_key] = [round(float(value), 3) for value in calibrated_full]

        result["latestComplete"] = {
            "year": 2025,
            "tmin": result["tmin"][-1],
            "tmax": result["tmax"][-1],
        }
        result["calibration"] = {
            "strategy": "continuous ERA5-Land with recent-overlap level anchor; temporal evolution preserved",
            "period": [ANCHOR_YEARS[0], ANCHOR_YEARS[-1]],
            "reference": "LaMMA 1 km",
            "independent_temporal_validation": "SIR Toscana",
            "tmin_offset_c": round(offsets["tmin"], 6),
            "tmax_offset_c": round(offsets["tmax"], 6),
        }
        output["municipalities"][municipality] = result
        diagnostics["municipalities"][municipality] = municipality_diag

    diagnostics["summary"] = {
        "mean_anchor_rmse_c": float(np.mean(anchor_rmses)),
        "max_anchor_rmse_c": float(max(anchor_rmses)),
        "mean_anchor_mae_c": float(np.mean(anchor_maes)),
        "max_abs_lamma_minus_era5_residual_trend_1995_2015_c_per_decade": float(
            max(overlap_residual_trends)
        ),
        "note": (
            "The large 1995-2015 LaMMA-vs-ERA5 residual trend is not injected into the "
            "published 50-year series. SIR anomaly/trend diagnostics support ERA5-Land "
            "temporal evolution, so the publication series remains homogeneous ERA5-Land "
            "1975-2025 with a constant LaMMA-derived level anchor only."
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
        f"homogeneous ERA5-Land 1975-2025 -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
