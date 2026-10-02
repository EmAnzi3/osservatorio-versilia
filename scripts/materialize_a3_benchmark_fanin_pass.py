#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
AGRICULTURE_PUBLIC_SOURCE = ROOT / "data" / "source-snapshots" / "istat-agricoltura-territorio-2020.json"
SNAPSHOTS = (
    ROOT / "data" / "source-snapshots" / "a3-istat-agriculture-benchmark-2020.json",
    ROOT / "data" / "source-snapshots" / "a3-regione-toscana-tourism-benchmark-2025.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-environment-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-agriculture-benchmark-2020-v2.json",
    ROOT / "data" / "source-snapshots" / "a3-agcom-benchmark-2025.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-environment-benchmark-2024-v2.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-demography-mobility-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-soil-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-regione-toscana-libraries-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-business-benchmark-2023.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-social-services-benchmark-2022.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-coast-benchmark-2020.json",
    ROOT / "data" / "source-snapshots" / "a3-fee-blue-flag-benchmark-2026.json",
)

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON non-oggetto")
    return value

def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result

ALLOW_MISSING_PUBLIC = {
    "libraryActiveBorrowersPer100",
    "libraryLoansPerResident",
    "libraryWeeklyOpeningHours",
}

def same_optional_number(left: Any, right: Any, label: str) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(finite(left, f"{label}/existing"), finite(right, f"{label}/candidate"), rel_tol=0.0, abs_tol=.011)

def public_rows(metric: dict[str, Any], metric_id: str) -> list[dict[str, Any]]:
    rows = metric.get("rows") or []
    if len(rows) != 7:
        raise RuntimeError(f"{metric_id}: righe pubbliche {len(rows)} != 7")
    if metric_id == "rigidDefenceProtectedCoast":
        validate_coast_public(rows)
        return rows
    if metric_id == "blueFlagBeaches":
        coastal = {"046005", "046013", "046024", "046033"}
        na = {"046018", "046028", "046030"}
        if {r.get("code") for r in rows} != coastal | na:
            raise RuntimeError("FEE: public perimeter mismatch")
        for row in rows:
            if row["code"] in na:
                if row.get("value") is not None or row.get("notApplicable") is not True:
                    raise RuntimeError("FEE: explicit n.a. required")
            else:
                finite(row.get("value"), f"FEE/{row['code']}")
        return rows
    for row in rows:
        value=row.get("value")
        if metric_id in ALLOW_MISSING_PUBLIC and value is None:
            continue
        finite(value, f"{metric_id}/{row.get('code') or row.get('town')}")
    return rows

def validate_blue_flag_public(metric: dict[str, Any], snapshot: dict[str, Any]) -> None:
    records = snapshot.get("records") or []
    if not records or len(records) != snapshot.get("scope", {}).get("listedMunicipalities"):
        raise RuntimeError("FEE: incomplete listing")
    normal = lambda text: " ".join(text.split()).casefold()
    keys = [(r["region"], normal(r["town"])) for r in records]
    if len(set(keys)) != len(keys):
        raise RuntimeError("FEE: duplicate town entries")
    benchmark = snapshot["benchmarks"]["blueFlagBeaches"]
    if metric["meta"].get("year") != benchmark["year"] or metric["meta"].get("unit") != benchmark["unit"]:
        raise RuntimeError("FEE: year/unit mismatch")
    for scope in ("tuscany", "italy"):
        expected = sum(len(r["localities"]) for r in records if not r["revoked"] and (scope == "italy" or r["region"] == "Toscana"))
        if finite(benchmark[scope], f"FEE/{scope}") != expected:
            raise RuntimeError("FEE: aggregate listing mismatch")
    for row in public_rows(metric, "blueFlagBeaches"):
        matching = [r for r in records if r["region"] == "Toscana" and normal(r["town"]) == normal(row["town"])]
        if row.get("notApplicable"):
            if matching: raise RuntimeError("FEE: unexpected listing for n.a. town")
            continue
        if len(matching) != 1 or matching[0]["revoked"]:
            raise RuntimeError("FEE: missing/revoked coastal town")
        names = matching[0]["localities"]
        public_names = row.get("coastDetail", {}).get("localities2026") or []
        if row["value"] != len(names) or {normal(n) for n in names} != {normal(n) for n in public_names}:
            raise RuntimeError("FEE: public locality count/names mismatch")

def validate_coast_public(rows: list[dict[str, Any]]) -> None:
    coastal = {"046005", "046013", "046024", "046033"}
    not_applicable = {"046018", "046028", "046030"}
    codes = [str(row.get("code") or "") for row in rows]
    if len(set(codes)) != 7 or set(codes) != coastal | not_applicable:
        raise RuntimeError("rigidDefenceProtectedCoast: perimetro pubblico diverso da 4 costieri + 3 n.a.")
    source = load(ROOT / "data/source-snapshots/costa-mare-v123.json")
    towns = (source.get("rigidDefenceProtectedCoast2020") or {}).get("towns") or {}
    if set(towns) != coastal:
        raise RuntimeError("rigidDefenceProtectedCoast: perimetro snapshot costiero inatteso")
    for row in rows:
        code = str(row["code"])
        if code in not_applicable:
            if row.get("value") is not None or row.get("notApplicable") is not True:
                raise RuntimeError(f"rigidDefenceProtectedCoast/{code}: n.a. esplicito richiesto")
            continue
        raw = towns[code]
        denominator = finite(raw.get("coastKm"), f"coastKm/{code}")
        if denominator <= 0:
            raise RuntimeError(f"rigidDefenceProtectedCoast/{code}: denominatore non positivo")
        expected = finite(raw.get("protectedKm"), f"protectedKm/{code}") / denominator * 100
        observed = finite(row.get("value"), f"rigidDefenceProtectedCoast/{code}")
        if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=.011):
            raise RuntimeError(f"rigidDefenceProtectedCoast/{code}: {observed} != {expected}")

def validate_agriculture_public(site: dict[str, Any]) -> None:
    source = load(AGRICULTURE_PUBLIC_SOURCE)
    towns = source.get("towns") or {}
    checks = {
        "agriculturalFarms": lambda row: finite(row.get("farms"), "farms"),
        "agriculturalUsedArea": lambda row: finite(row.get("sauLocalizedHa"), "sauLocalizedHa"),
        "averageAgriculturalFarmSize": lambda row: (
            finite(row.get("sauCenterHa"), "sauCenterHa")
            / finite(row.get("farmsWithSau"), "farmsWithSau")
        ),
        "irrigatedAgriculturalArea": lambda row: finite(row.get("irrigatedAreaHa"), "irrigatedAreaHa"),
    }
    for metric_id, expected_value in checks.items():
        metric = (site.get("metrics") or {}).get(metric_id) or {}
        rows = public_rows(metric, metric_id)
        for row in rows:
            code = str(row.get("code") or "")
            src = towns.get(code)
            if not isinstance(src, dict):
                raise RuntimeError(f"{metric_id}/{code}: snapshot agricolo assente")
            expected = expected_value(src)
            observed = finite(row.get("value"), f"{metric_id}/{code}")
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=.02):
                raise RuntimeError(f"{metric_id}/{code}: {observed} != {expected}")

def main() -> None:
    site = load(SITE)
    validate_agriculture_public(site)
    metrics = site.get("metrics") or {}
    published: list[str] = []
    already_present: list[str] = []

    for snapshot_path in SNAPSHOTS:
        snapshot = load(snapshot_path)
        gate = snapshot.get("qualityGate") or {}
        if gate.get("status") != "PASS" or gate.get("errors") not in (None, []):
            raise RuntimeError(f"{snapshot_path.name}: quality gate non PASS")
        benchmarks = snapshot.get("benchmarks") or {}
        if not benchmarks:
            raise RuntimeError(f"{snapshot_path.name}: benchmark vuoti")
        source_url = str(snapshot.get("sourceUrl") or "").strip()
        if not source_url:
            raise RuntimeError(f"{snapshot_path.name}: sourceUrl assente")

        for metric_id, benchmark in benchmarks.items():
            metric = metrics.get(metric_id)
            if not isinstance(metric, dict):
                raise RuntimeError(f"{metric_id}: metrica pubblica assente")
            public_rows(metric, metric_id)
            if metric_id == "blueFlagBeaches":
                validate_blue_flag_public(metric, snapshot)
            meta = metric.setdefault("meta", {})
            year = str(benchmark.get("year") or "").strip()
            unit = str(benchmark.get("unit") or "").strip()
            if not year or not unit:
                raise RuntimeError(f"{metric_id}: year/unit benchmark assenti")
            tuscany = benchmark.get("tuscany")
            italy = benchmark.get("italy")
            if tuscany is None and italy is None:
                raise RuntimeError(f"{metric_id}: entrambi gli scope benchmark sono null")
            if tuscany is not None:
                finite(tuscany, f"{metric_id}/tuscany")
            if italy is not None:
                finite(italy, f"{metric_id}/italy")

            snapshot_ref = str(snapshot_path.relative_to(ROOT)).replace("\\", "/")
            existing = meta.get("benchmark")
            if isinstance(existing, dict) and any(
                isinstance(existing.get(scope), (int, float)) and not isinstance(existing.get(scope), bool)
                for scope in ("tuscany", "italy")
            ):
                same = (
                    str(existing.get("year") or "").strip() == year
                    and same_optional_number(existing.get("tuscany"), tuscany, f"{metric_id}/tuscany")
                    and same_optional_number(existing.get("italy"), italy, f"{metric_id}/italy")
                    and str(existing.get("sourceSnapshot") or snapshot_ref) == snapshot_ref
                    and str(existing.get("url") or source_url) == source_url
                )
                if not same:
                    raise RuntimeError(f"{metric_id}: benchmark già materializzato ma in conflitto col candidato")
                already_present.append(metric_id)
                continue

            meta["benchmark"] = {
                "year": year,
                "tuscany": tuscany,
                "italy": italy,
                "source": snapshot.get("publisher"),
                "url": source_url,
                "sourceSnapshot": snapshot_ref,
                "note": (snapshot["scope"]["note"] if metric_id == "blueFlagBeaches" else "Benchmark A3 materializzato da artifact di acquisizione con quality gate metric-level PASS."),
            }
            published.append(metric_id)

    SITE.write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"A3 benchmark fan-in materialized: {len(published)} new metrics :: {', '.join(sorted(published))} | "
        f"{len(already_present)} already present verified :: {', '.join(sorted(already_present))}"
    )

if __name__ == "__main__":
    main()
