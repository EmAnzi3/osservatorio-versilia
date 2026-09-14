#!/usr/bin/env python3
"""Regression contract for the frozen Salute demographic enrichment."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_MATERIALIZER = ROOT / "scripts" / "materialize_salute_v140.py"
DEMOGRAPHIC_MATERIALIZER = ROOT / "scripts" / "materialize_salute_demographics_v140.py"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "ars-salute-demographics-v140.json"

EXPECTED = {
    "lifeExpectancy",
    "mortalityAll",
    "mortalityCancer",
    "mortalityCirculatory",
    "mortalityRespiratory",
    "hypertensionPrevalence",
    "copdPrevalence",
    "ischemicHeartDiseasePrevalence",
    "heartFailurePrevalence",
    "priorStrokePrevalence",
    "diabetes",
    "dementia",
    "permanentRsaAssisted",
    "emergencyAccess",
    "specialistVisits7Psr",
    "diagnosticImagingServices",
    "elderlyHomeCare",
}
AGE_METRICS = {
    "hypertensionPrevalence",
    "copdPrevalence",
    "ischemicHeartDiseasePrevalence",
    "heartFailurePrevalence",
    "priorStrokePrevalence",
    "diabetes",
    "dementia",
}
AGE_KEYS = ["totale", "16-44", "45-64", "65-84", "85+"]
SEX_KEYS = ["totale", "maschi", "femmine"]
EXCLUDED_UNRECONCILED = {"chronicTotal", "hospitalizedAll"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossibile caricare {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def part_key(has_age: bool) -> str:
    return "totale|totale" if has_age else "totale"


def assert_close(left, right, tolerance=0.051) -> None:
    assert left is not None and right is not None
    assert abs(float(left) - float(right)) <= tolerance, (left, right)


def assert_age_specific_raw(parts: list[dict], key: str, scope: str) -> None:
    """Guard against ARS structural standardized=0 leaking into age strata."""
    age_parts = [part for part in parts if part.get("ageKey") not in (None, "totale")]
    assert len(age_parts) == 12, (key, scope, len(age_parts))
    for part in age_parts:
        assert part["measurement"] == "raw", (key, scope, part["key"], part["measurement"])
        assert part["value"] is not None, (key, scope, part["key"])
        num = part.get("numerator")
        den = part.get("denominator")
        assert num is not None and den not in (None, 0), (key, scope, part["key"], num, den)
        expected = float(num) / float(den) * 1000.0
        assert abs(float(part["value"]) - expected) <= 0.011, (
            key,
            scope,
            part["key"],
            part["value"],
            expected,
        )
        assert not (float(part["value"]) == 0.0 and float(num) > 0), (key, scope, part["key"])
        assert part.get("ci95Low") is None and part.get("ci95High") is None, (
            key,
            scope,
            part["key"],
            part.get("ci95Low"),
            part.get("ci95High"),
        )


def main() -> int:
    snapshot = load(SNAPSHOT)
    assert snapshot["release"] == "v1.40.0"
    source_keys = {item["key"] for item in snapshot["indicators"].values()}
    assert source_keys == EXPECTED, sorted(source_keys ^ EXPECTED)

    for item in snapshot["indicators"].values():
        key = item["key"]
        rows = item["rows"]
        geos = {str(row["geoCode"]) for row in rows}
        assert "202M" in geos and "90" in geos, key
        municipality_geos = geos - {"202M", "90"}
        assert len(municipality_geos) == 7, (key, municipality_geos)
        assert set(item["sexValues"]) == set(SEX_KEYS), key
        if key in AGE_METRICS:
            assert set(item["strato1Values"]) == set(AGE_KEYS), key
            # In the official ARS export the standardized field of non-total age
            # strata is structural zero while the crude field carries the actual
            # age-specific rate. Keep this source fact explicit in the contract.
            age_source_rows = [
                row for row in rows if str(row.get("strato1") or "").casefold() not in ("", "totale")
            ]
            assert age_source_rows, key
            assert all(float(row.get("standardized") or 0) == 0.0 for row in age_source_rows), key
            assert any(float(row.get("raw") or 0) > 0 for row in age_source_rows), key
        else:
            assert item["strato1Values"] == [], (key, item["strato1Values"])

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        tmp_data = tmp_root / "data"
        tmp_data.mkdir()
        site_path = tmp_data / "site-data.json"
        registry_path = tmp_data / "source-registry.json"
        shutil.copy2(ROOT / "data" / "site-data.json", site_path)
        shutil.copy2(ROOT / "data" / "source-registry.json", registry_path)

        core = load_module("salute_core_for_demographics", CORE_MATERIALIZER)
        core.DATA = site_path
        core.REGISTRY = registry_path
        core.apply_overlay()

        before = load(site_path)
        before_count = len(before["metrics"])
        baseline_values = {
            key: {
                "rows": {row["town"]: row["value"] for row in before["metrics"][key]["rows"]},
                "aggregate": before["metrics"][key]["aggregate"]["value"],
            }
            for key in EXPECTED
        }

        demographics = load_module("salute_demographics_contract", DEMOGRAPHIC_MATERIALIZER)
        demographics.DATA = site_path
        demographics.SNAPSHOT = SNAPSHOT
        demographics.main()

        data = load(site_path)
        assert len(data["metrics"]) == before_count
        enriched = {
            key
            for key, metric in data["metrics"].items()
            if (metric.get("meta") or {}).get("demographicSource")
        }
        assert EXPECTED <= enriched, sorted(EXPECTED - enriched)
        assert not (EXCLUDED_UNRECONCILED & enriched), sorted(EXCLUDED_UNRECONCILED & enriched)

        for key in EXPECTED:
            metric = data["metrics"][key]
            meta = metric["meta"]
            has_age = key in AGE_METRICS
            assert meta["compositeType"] == ("demographicBreakdown" if has_age else "sexBreakdown"), key
            assert meta["demographicSource"]["publisher"] == "ARS Toscana", key
            assert metric["tuscany"]["source"] == "ARS Toscana", key
            assert meta["benchmark"]["tuscany"] is not None, key
            assert meta["benchmark"]["italy"] is None, key

            if has_age:
                assert [item["key"] for item in meta["ageOptions"]] == AGE_KEYS, key
                assert [item["key"] for item in meta["genderOptions"]] == SEX_KEYS, key
                assert "misura_grezza (fasce d’età)" in meta["demographicSource"]["measurement"], key
                expected_parts = 15
            else:
                assert [item["key"] for item in meta["sexOptions"]] == SEX_KEYS, key
                expected_parts = 3

            for row in metric["rows"]:
                assert baseline_values[key]["rows"][row["town"]] == row["value"], (key, row["town"])
                assert len(row["parts"]) == expected_parts, (key, row["town"], len(row["parts"]))
                default = next(part for part in row["parts"] if part["key"] == part_key(has_age))
                assert_close(row["value"], default["value"])
                if has_age:
                    assert default["measurement"] == "standardized", (key, row["town"])
                    assert_age_specific_raw(row["parts"], key, row["town"])

            assert metric["aggregate"]["value"] == baseline_values[key]["aggregate"], key
            assert len(metric["aggregate"]["parts"]) == expected_parts, key
            assert len(metric["tuscany"]["parts"]) == expected_parts, key
            aggregate_default = next(
                part for part in metric["aggregate"]["parts"] if part["key"] == part_key(has_age)
            )
            assert_close(metric["aggregate"]["value"], aggregate_default["value"])
            if has_age:
                assert aggregate_default["measurement"] == "standardized", key
                assert_age_specific_raw(metric["aggregate"]["parts"], key, "Versilia 202M")
                assert_age_specific_raw(metric["tuscany"]["parts"], key, "Toscana")

        life = data["metrics"]["lifeExpectancy"]
        life_total = next(part for part in life["rows"][0]["parts"] if part["key"] == "totale")
        assert life_total["measurement"] == "raw"
        assert life_total["value"] > 70
        assert life_total.get("series", {}).get("values"), "Lo storico per sesso già pubblicato non deve andare perso"

    print(
        "Salute demographics v1.40: 17 metriche riconciliate, sesso/età dove disponibili, "
        "fasce MaCro su misura grezza ARS, Toscana omogenea, Italia non inferita, catalogo invariato"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
