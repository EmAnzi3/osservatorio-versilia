#!/usr/bin/env python3
"""Audit only: compare the published hybrid climate series with a homogeneous ERA5-Land candidate.

This script never edits site data. It consumes the raw/patched ERA5-Land annual extraction
and the LaMMA overlap produced by the existing POC workflow, then writes a review artifact.

Candidate policy, aligned with the Tmin/Tmax approach:
- continuous ERA5-Land evolution for 1975-2025;
- temperature level: constant additive municipal offset from LaMMA 2011-2015;
- precipitation level: constant multiplicative municipal factor from LaMMA 2011-2015;
- no slope correction;
- 1975-2025 vs 1979-2025 sensitivity reported;
- 2020 transition diagnostic reported, not automatically classified as a break.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

FROM = 1975
TO = 2025
SENSITIVITY_FROM = 1979
ANCHOR_FROM = 2011
ANCHOR_TO = 2015


def trend(years: np.ndarray, values: np.ndarray, start: int, end: int) -> dict:
    mask = (years >= start) & (years <= end) & np.isfinite(values)
    x = years[mask].astype(float)
    y = values[mask].astype(float)
    if len(x) < 3:
        raise ValueError(f"Insufficient points for trend {start}-{end}")
    slope, intercept = np.polyfit(x, y, 1)
    start_value = float(intercept + slope * start)
    end_value = float(intercept + slope * end)
    return {
        "from": start,
        "to": end,
        "n": int(len(x)),
        "per_decade": float(slope * 10.0),
        "delta": float(end_value - start_value),
        "start_value": start_value,
        "end_value": end_value,
    }


def published_lookup(payload: dict, municipality: str, key: str) -> tuple[np.ndarray, np.ndarray]:
    series = payload["municipalities"][municipality]
    return np.asarray(series["years"], dtype=int), np.asarray(series[key], dtype=float)


def transition_2020(years: np.ndarray, values: np.ndarray) -> dict:
    lookup = {int(y): float(v) for y, v in zip(years, values)}
    required = [2018, 2019, 2020, 2021]
    missing = [year for year in required if year not in lookup]
    if missing:
        return {"available": False, "missing": missing}
    observed_step = lookup[2020] - lookup[2019]
    adjacent_mean_step = ((lookup[2019] - lookup[2018]) + (lookup[2021] - lookup[2020])) / 2.0
    return {
        "available": True,
        "delta_2020_minus_2019": observed_step,
        "adjacent_step_mean": adjacent_mean_step,
        "excess_vs_adjacent_step_mean": observed_step - adjacent_mean_step,
        "note": "Diagnostic only: a one-year step is not evidence of an artificial discontinuity.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--published-json", required=True)
    ap.add_argument("--lamma", required=True)
    ap.add_argument("--era5", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    args = ap.parse_args()

    published = json.loads(Path(args.published_json).read_text(encoding="utf-8"))
    lamma = pd.read_csv(args.lamma)
    era5 = pd.read_csv(args.era5)
    required = {"municipality", "year", "tmean_c", "precip_mm"}
    for label, frame in (("LaMMA", lamma), ("ERA5-Land", era5)):
        missing = required - set(frame.columns)
        if missing:
            raise SystemExit(f"{label}: missing columns {sorted(missing)}")
        frame["year"] = frame["year"].astype(int)

    municipalities = sorted(published["municipalities"], key=str.casefold)
    report = {
        "schemaVersion": 1,
        "status": "audit_only",
        "publishedDataset": args.published_json,
        "candidate": {
            "period": [FROM, TO],
            "source": "continuous ERA5-Land",
            "temperatureCalibration": f"additive LaMMA level anchor {ANCHOR_FROM}-{ANCHOR_TO}",
            "precipitationCalibration": f"multiplicative LaMMA level anchor {ANCHOR_FROM}-{ANCHOR_TO}",
            "slopeCorrection": False,
        },
        "municipalities": {},
    }

    for municipality in municipalities:
        l = lamma[(lamma.municipality == municipality) & lamma.year.between(ANCHOR_FROM, ANCHOR_TO)].copy()
        e_anchor = era5[(era5.municipality == municipality) & era5.year.between(ANCHOR_FROM, ANCHOR_TO)].copy()
        paired = l[["year", "tmean_c", "precip_mm"]].merge(
            e_anchor[["year", "tmean_c", "precip_mm"]], on="year", suffixes=("_lamma", "_era5"), how="inner"
        ).dropna()
        if paired.year.astype(int).tolist() != list(range(ANCHOR_FROM, ANCHOR_TO + 1)):
            raise SystemExit(f"{municipality}: incomplete {ANCHOR_FROM}-{ANCHOR_TO} calibration anchor")

        temp_offset = float((paired.tmean_c_lamma - paired.tmean_c_era5).mean())
        positive = paired[(paired.precip_mm_lamma > 0) & (paired.precip_mm_era5 > 0)]
        if len(positive) != len(paired):
            raise SystemExit(f"{municipality}: invalid precipitation anchor values")
        precip_factor = float(np.median(positive.precip_mm_lamma / positive.precip_mm_era5))

        er = era5[(era5.municipality == municipality) & era5.year.between(FROM, TO)].sort_values("year")
        expected = list(range(FROM, TO + 1))
        if er.year.astype(int).tolist() != expected:
            raise SystemExit(f"{municipality}: ERA5 coverage is not continuous {FROM}-{TO}")
        years = er.year.to_numpy(dtype=int)
        candidates = {
            "temperature": er.tmean_c.to_numpy(dtype=float) + temp_offset,
            "precipitation": er.precip_mm.to_numpy(dtype=float) * precip_factor,
        }

        block = {
            "calibration": {"temperature_offset_c": temp_offset, "precipitation_factor": precip_factor},
            "metrics": {},
        }
        for key, candidate_values in candidates.items():
            py, pv = published_lookup(published, municipality, key)
            pub_50 = trend(py, pv, FROM, TO)
            cand_50 = trend(years, candidate_values, FROM, TO)
            cand_1979 = trend(years, candidate_values, SENSITIVITY_FROM, TO)
            pub_latest = float(pv[np.where(py == TO)[0][0]])
            cand_latest = float(candidate_values[np.where(years == TO)[0][0]])
            block["metrics"][key] = {
                "published_trend": pub_50,
                "candidate_trend": cand_50,
                "candidate_sensitivity_1979_2025": cand_1979,
                "trend_delta_candidate_minus_published": cand_50["delta"] - pub_50["delta"],
                "trend_per_decade_delta_candidate_minus_published": cand_50["per_decade"] - pub_50["per_decade"],
                "latest_2025_published": pub_latest,
                "latest_2025_candidate": cand_latest,
                "latest_2025_delta": cand_latest - pub_latest,
                "transition_2020": transition_2020(years, candidate_values),
            }
        report["municipalities"][municipality] = block

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Audit hardening clima — solo revisione",
        "",
        "Questo report **non modifica i dati pubblicati**. Confronta la serie corrente con una candidata ERA5-Land continua 1975–2025, calibrata nel solo livello su LaMMA 2011–2015.",
        "",
        "| Comune | Metrica | Δ trend candidato-attuale | Δ ritmo/decennio | Δ valore 2025 | Sensibilità trend 1979–2025 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for municipality in municipalities:
        for key in ("temperature", "precipitation"):
            m = report["municipalities"][municipality]["metrics"][key]
            unit = "°C" if key == "temperature" else "mm"
            lines.append(
                f"| {municipality} | {key} | {m['trend_delta_candidate_minus_published']:+.3f} {unit} | "
                f"{m['trend_per_decade_delta_candidate_minus_published']:+.3f} {unit}/dec | "
                f"{m['latest_2025_delta']:+.3f} {unit} | "
                f"{m['candidate_sensitivity_1979_2025']['delta'] - m['candidate_trend']['delta']:+.3f} {unit} |"
            )
    lines += [
        "",
        "## Criterio di decisione",
        "",
        "La candidata non deve essere pubblicata automaticamente. Il report serve a valutare stabilità del trend, impatto sui valori 2025 e diagnostica 2020; la validazione SIR resta un controllo indipendente separato.",
    ]
    Path(args.output_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[climate-hardening] wrote {out_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
