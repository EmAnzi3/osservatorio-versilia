#!/usr/bin/env python3
"""Materialize the native 2024–2025 RCS history without changing current values."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data/source-snapshots/a3-simple-rcs-history-2024-2025.json"
RCS_PATH = ROOT / "data/source-snapshots/istat-rcs-demography-2025.json"
DEMOGRAPHY_PATH = ROOT / "data/source-snapshots/istat-demography-lotto-a-2026-08.json"
YEARS = [2024, 2025]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def integer(value: object, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise RuntimeError(f"RCS: invalid native count {value!r}")
    return value


def equal(actual: object, expected: float, label: str) -> None:
    if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual):
        raise RuntimeError(f"RCS: invalid numeric value for {label}")
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10):
        raise RuntimeError(f"RCS: mismatch {label}: {actual} != {expected}")


def apply_history(site: dict) -> None:
    snapshot, rcs, demographic = load(SNAPSHOT_PATH), load(RCS_PATH), load(DEMOGRAPHY_PATH)
    if snapshot.get("metricId") != "foreignResidents" or snapshot.get("years") != YEARS:
        raise RuntimeError("RCS: incompatible metric or period")
    sources = snapshot.get("sources", {})
    native_source = sources.get("2024", {})
    if (native_source.get("url") != "https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2024.zip"
            or native_source.get("archiveMember") != "Dati_cittadinanza_2024.csv"
            or native_source.get("sha256") != "dccda782f833ff8e3a60fbaf8ee9f7e77adba15036c76e8d2740c97c07d91876"
            or native_source.get("bytes") != 1935553
            or native_source.get("memberSha256") != "23064341ad8f89be0dc9945a7c657e54b533bf96f9731184b0a1ff5943f4b717"):
        raise RuntimeError("RCS: uncertified 2024 source")
    if sources.get("2025", {}).get("snapshotSha256") != hashlib.sha256(RCS_PATH.read_bytes()).hexdigest():
        raise RuntimeError("RCS: changed 2025 reference snapshot")
    metric = site["metrics"]["foreignResidents"]
    if str(metric["meta"].get("year")) != "2025" or metric["meta"].get("unit") != "percent":
        raise RuntimeError("RCS: current year or unit changed")
    towns = rcs["towns"]
    candidates = snapshot.get("towns", {})
    codes = {town: raw["code"] for town, raw in towns.items()}
    if len(codes) != 7 or len(set(codes.values())) != 7 or set(candidates) != set(codes):
        raise RuntimeError("RCS: incomplete or duplicated native scope")
    rows = metric.get("rows", [])
    if len(rows) != 7 or {row.get("town") for row in rows} != set(codes):
        raise RuntimeError("RCS: public municipal scope mismatch")
    native = snapshot.get("nativeCitizenship2024", {})
    if set(native) != set(codes.values()):
        raise RuntimeError("RCS: missing native citizenship records")
    series_by_town, components_by_town = {}, {}
    sums_foreign, sums_population = [0, 0], [0, 0]
    for row in rows:
        town = row["town"]
        candidate = candidates[town]
        code = codes[town]
        if candidate.get("code") != code or row.get("code") != code or candidate.get("years") != YEARS:
            raise RuntimeError(f"RCS: municipal identity or period mismatch: {town}")
        totals, foreigners, seen = 0, 0, set()
        for cell in native[code]:
            citizenship = cell.get("citizenshipCode")
            if not isinstance(citizenship, str) or not citizenship.isdigit() or citizenship in seen:
                raise RuntimeError(f"RCS: citizenship duplicate or invalid: {town}")
            seen.add(citizenship)
            count = integer(cell.get("total"))
            if integer(cell.get("men")) + integer(cell.get("women")) != count:
                raise RuntimeError(f"RCS: inconsistent citizenship sex counts: {town}")
            totals += count
            if citizenship != "100":
                foreigners += count
        if "100" not in seen:
            raise RuntimeError(f"RCS: incomplete native citizenship population: {town}")
        annual = demographic["p02"]["towns"][town]
        population = []
        for year in YEARS:
            observations = [item for item in annual if item["year"] == year]
            if len(observations) != 1:
                raise RuntimeError(f"RCS: population year missing or duplicated: {town}/{year}")
            population.append(integer(observations[0]["populationJan1"], positive=True))
        foreign = [foreigners, integer(towns[town]["citizenshipTotal"])]
        if totals != population[0] or candidate.get("population") != population or candidate.get("foreignCitizens") != foreign:
            raise RuntimeError(f"RCS: native counts or denominator mismatch: {town}")
        values = [foreign[i] / population[i] * 100 for i in range(2)]
        if not isinstance(candidate.get("values"), list) or len(candidate["values"]) != 2:
            raise RuntimeError(f"RCS: incomplete candidate series: {town}")
        for actual, expected in zip(candidate["values"], values):
            equal(actual, expected, town)
        equal(row.get("value"), values[-1], f"{town}/current")
        if row.get("count") != foreign[-1] or row.get("population") != population[-1]:
            raise RuntimeError(f"RCS: current components mismatch: {town}")
        series_by_town[town] = make_series(values)
        components_by_town[town] = {"share": make_series(values), "count": make_series(foreign)}
        for i in range(2):
            sums_foreign[i] += foreign[i]
            sums_population[i] += population[i]
    aggregate = metric.get("aggregate", {})
    aggregate_series = make_series([sums_foreign[i] / sums_population[i] * 100 for i in range(2)])
    aggregate_components = {"share": aggregate_series, "count": make_series(sums_foreign)}
    equal(aggregate.get("value"), aggregate_series["values"][-1], "aggregate/current")
    if aggregate.get("count") != sums_foreign[-1]:
        raise RuntimeError("RCS: aggregate count mismatch")
    # Validate all conflicts before writing any public field.
    for row in rows:
        if row.get("series") is not None and row["series"] != series_by_town[row["town"]]:
            raise RuntimeError(f"RCS: conflicting history: {row['town']}")
        if row.get("componentSeries") is not None and row["componentSeries"] != components_by_town[row["town"]]:
            raise RuntimeError(f"RCS: conflicting component history: {row['town']}")
    if aggregate.get("series") is not None and aggregate["series"] != aggregate_series:
        raise RuntimeError("RCS: conflicting aggregate history")
    if aggregate.get("componentSeries") is not None and aggregate["componentSeries"] != aggregate_components:
        raise RuntimeError("RCS: conflicting aggregate component history")
    for row in rows:
        row["series"] = series_by_town[row["town"]]
        row["componentSeries"] = components_by_town[row["town"]]
    aggregate["series"] = aggregate_series
    aggregate["componentSeries"] = aggregate_components


def make_series(values: list[float | int]) -> dict:
    return {"years": list(YEARS), "values": values,
            "source": "Istat RCS — popolazione residente per cittadinanza",
            "sourceUrl": "https://demo.istat.it/app/?i=RCS&l=it",
            "sourceSnapshot": "data/source-snapshots/a3-simple-rcs-history-2024-2025.json",
            "note": "Residenti di cittadinanza non italiana al 1° gennaio: quota e conteggi nativi; dati di fonte censuaria. Il valore Versilia usa la somma dei conteggi e dei residenti dei sette comuni."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=ROOT / "dist/data/site-data.json")
    args = parser.parse_args()
    apply_history(load(args.site))
    print("RCS history PASS: 2024–2025, 7/7 municipalities and weighted aggregate; check only")
