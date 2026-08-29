#!/usr/bin/env python3
"""Contratto dati, fonti e interfaccia per il lotto Costa e mare v1.23.0."""
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYS = (
    "bathingWaterQuality",
    "bathingNonCompliantSamples",
    "blueFlagBeaches",
    "shorelineDynamics",
    "rigidDefenceProtectedCoast",
)
COASTAL = {"046005", "046013", "046024", "046033"}
NOT_APPLICABLE = {"046018", "046028", "046030"}


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def close(actual: float, expected: float, tolerance: float = 1e-9) -> None:
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance), (
        actual,
        expected,
    )


def indexed_rows(metric: dict) -> dict[str, dict]:
    rows = metric["rows"]
    assert len(rows) == 7
    assert {row["code"] for row in rows} == COASTAL | NOT_APPLICABLE
    indexed = {row["code"]: row for row in rows}
    for code in COASTAL:
        row = indexed[code]
        assert row["value"] is not None
        assert not row.get("notApplicable", False)
        assert row.get("formatted") != "n.a."
    for code in NOT_APPLICABLE:
        row = indexed[code]
        assert row["value"] is None
        assert row["formatted"] == "n.a."
        assert row["notApplicable"] is True
        assert "non costiero" in row["applicabilityNote"].lower()
        assert row.get("benchmarkValue") is None
        assert row.get("series") is None
        assert all(part.get("value") is None for part in row.get("parts", []))
    return indexed


def assert_snapshot(snapshot: dict) -> None:
    expected_hashes = {
        "arpatSamples2025": "90d25c2b47ceae7d2222c718948a46fac6d11985eb0df464a30cc6236be4f1bf",
        "arpatQualityHistory": "cfcd5b2b5d48084468b43d0bf9f03fb63fb70239a07cca8b8afae56343633752",
        "arpatControlsHistory": "79fbbc55472fd9cc7a69d631c0826378fa8cb1661fd4b29e622ec9eefe903b90",
        "arpatReport2025": "c190a78c0cf0d8a3e728d84aaa5fd50c7aefc6c0918cb8efa06305d0b965e76a",
        "blueFlag2026": "dbfbb3f4f7ea1397015f69b93b91f0acaa2ec71f7cd2e7a2fcad8f76bbd048fc",
        "ispraShorelineDynamics": "a00fb97649e293c73c923e43fd0ee53ecfa42df9568ec162a9668c2adb4c9b11",
        "ispraProtectedCoast": "9ca2b81cff7375f4af9f86af50543637d23329828d3556ccbe174a16e27d956e",
    }
    assert snapshot["release"] == "v1.23.0"
    assert set(snapshot["scope"]["coastalTownCodes"]) == COASTAL
    assert set(snapshot["scope"]["notApplicableTownCodes"]) == NOT_APPLICABLE
    for source, expected in expected_hashes.items():
        assert snapshot["sources"][source]["sha256"] == expected
    assert snapshot["bathingNonCompliantSamples2025"]["uniqueSamples"] == 167
    assert snapshot["bathingNonCompliantSamples2025"]["deduplicationKey"] == [
        "Codice area",
        "Data",
        "Rout. Suppl.",
    ]
    deferred = snapshot["deferredCandidates"]["beachNourishment"]
    assert deferred["status"] == "deferred"
    assert "codice intervento" in deferred["reason"]
    assert "volume" in deferred["reason"]


def assert_quality(metric: dict, snapshot: dict) -> None:
    rows = indexed_rows(metric)
    expected = {
        "046005": (2, 3, 2.92, 3.24),
        "046013": (3, 3, 5.20, 5.20),
        "046024": (4, 9, 3.56, 4.75),
        "046033": (5, 6, 7.16, 7.43),
    }
    for code, (excellent, total, excellent_km, total_km) in expected.items():
        row = rows[code]
        close(row["value"], excellent / total * 100)
        close(row["parts"][0]["value"], excellent / total * 100)
        close(row["parts"][1]["value"], excellent_km / total_km * 100)
        raw = snapshot["bathingWaterQuality2025"]["towns"][code]
        assert row["coastDetail"] == {"areas": raw["areas"], "kilometres": raw["kilometres"]}
    close(metric["aggregate"]["parts"][0]["value"], 14 / 21 * 100)
    close(metric["aggregate"]["parts"][1]["value"], 18.84 / 20.62 * 100)
    assert [part["key"] for part in metric["aggregate"]["parts"]] == [
        "areas",
        "kilometres",
    ]
    assert "non medie semplici" in metric["aggregate"]["note"]


def assert_samples(metric: dict, snapshot: dict) -> None:
    rows = indexed_rows(metric)
    expected = {
        "046005": ((8, 28), (7, 18, 3, 3), (1, 10)),
        "046013": ((4, 22), (4, 18, 3, 3), (0, 4)),
        "046024": ((17, 73), (12, 54, 9, 9), (5, 19)),
        "046033": ((6, 44), (6, 36, 4, 6), (0, 8)),
    }
    for code, (all_values, routine, supplementary) in expected.items():
        row = rows[code]
        close(row["parts"][0]["value"], all_values[0] / all_values[1] * 100)
        close(row["parts"][1]["value"], routine[0] / routine[1] * 100)
        close(row["parts"][2]["value"], supplementary[0] / supplementary[1] * 100)
        assert row["coastDetail"]["routine"]["affectedAreas"] == routine[2]
        assert row["coastDetail"]["routine"]["areas"] == routine[3]
        assert row["coastDetail"] == snapshot["bathingNonCompliantSamples2025"]["towns"][code]
    aggregate = metric["aggregate"]["parts"]
    close(aggregate[0]["value"], 35 / 167 * 100)
    close(aggregate[1]["value"], 29 / 126 * 100)
    close(aggregate[2]["value"], 6 / 41 * 100)
    assert aggregate[0]["nonCompliant"] == 35 and aggregate[0]["total"] == 167
    assert "campioni" in metric["meta"]["description"].lower()
    assert "episodi" not in metric["meta"]["description"].lower()


def assert_blue_flags(metric: dict, snapshot: dict) -> None:
    rows = indexed_rows(metric)
    expected_series = {
        "046005": [1, 1, 1, 1, 1, 1, 1, 1],
        "046013": [1, 1, 1, 1, 1, 1, 1, 1],
        "046024": [1, 1, 0, 2, 2, 2, 2, 2],
        "046033": [2, 2, 2, 2, 2, 2, 2, 2],
    }
    years = list(range(2019, 2027))
    for code, values in expected_series.items():
        assert rows[code]["series"] == {"years": years, "values": values}
        assert rows[code]["coastDetail"]["localities2026"] == snapshot["blueFlagBeaches"]["towns"][code]["localities2026"]
    assert metric["aggregate"]["series"] == {
        "years": years,
        "values": [5, 5, 4, 6, 6, 6, 6, 6],
    }
    assert metric["meta"]["polarity"] == "neutral"
    assert "Ponente/Levante" in rows["046033"]["coastDetail"]["localities2026"][0]


def assert_dynamics(metric: dict, snapshot: dict) -> None:
    rows = indexed_rows(metric)
    raw_rows = snapshot["shorelineDynamics2006_2020"]["towns"]
    for code, raw in raw_rows.items():
        row = rows[code]
        close(raw["analysedKm"], raw["erosionKm"] + raw["stableKm"] + raw["advanceKm"])
        close(row["parts"][0]["value"], raw["erosionKm"] / raw["analysedKm"] * 100)
        close(row["parts"][1]["value"], raw["stableKm"] / raw["analysedKm"] * 100)
        close(row["parts"][2]["value"], raw["advanceKm"] / raw["analysedKm"] * 100)
        assert row["coastDetail"] == raw
    raw = snapshot["shorelineDynamics2006_2020"]["versilia"]
    parts = metric["aggregate"]["parts"]
    close(parts[0]["value"], raw["erosionKm"] / raw["analysedKm"] * 100)
    close(parts[1]["value"], raw["stableKm"] / raw["analysedKm"] * 100)
    close(parts[2]["value"], raw["advanceKm"] / raw["analysedKm"] * 100)
    assert metric["meta"]["polarity"] == "neutral"


def assert_protected(metric: dict, snapshot: dict) -> None:
    rows = indexed_rows(metric)
    raw_rows = snapshot["rigidDefenceProtectedCoast2020"]["towns"]
    for code, raw in raw_rows.items():
        close(rows[code]["value"], raw["protectedKm"] / raw["coastKm"] * 100)
        assert rows[code]["coastDetail"] == raw
    assert rows["046033"]["value"] == 0
    assert not rows["046033"].get("notApplicable", False)
    raw = snapshot["rigidDefenceProtectedCoast2020"]["versilia"]
    close(metric["aggregate"]["value"], raw["protectedKm"] / raw["coastKm"] * 100)
    assert "ripascimenti" in metric["method"]["caveat"].lower()
    assert metric["meta"]["polarity"] == "neutral"


def assert_registry_and_ui(data: dict) -> None:
    registry = load("data/source-registry.json")
    monitor = load("data/source-monitor-state.json")
    for key in KEYS:
        assert key in registry["metricOverrides"]
        assert monitor["metrics"][key]["status"] == "current"
    assert len(data["themes"]) == 11
    environment = data["themes"]["ambiente"]
    assert any(section["key"] == "costa-mare" and section["metrics"] == list(KEYS) for section in environment["sections"])
    assert all(key in environment["metrics"] for key in KEYS)

    parts = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "assets" / "app-parts").glob("*.txt"))
    )
    for marker in (
        "coastDetailMarkup",
        "Comune non costiero",
        "row.notApplicable",
        "formatMetricRowValue",
        "Dettaglio dei quattro Comuni costieri",
    ):
        assert marker in parts
    assert "n.a." in parts
    export = (ROOT / "assets" / "export-v161.js").read_text(encoding="utf-8")
    assert "function coastRows(" in export
    assert "selected.metric.meta.detailGroup === 'coast'" in export
    assert "row.notApplicable ? 'n.a.'" in export
    assert "Applicabilità" in export


def main() -> None:
    data = load("data/site-data.json")
    snapshot = load("data/source-snapshots/costa-mare-v123.json")
    registry = load("data/source-registry.json")
    assert data["version"] == "v1.23.0"
    assert registry["expectedMetricCount"] == 162
    assert registry["expectedInlineMetricCount"] == 158
    assert registry["expectedExternalMetricCount"] == 4
    assert len(data["metrics"]) == 162
    assert_snapshot(snapshot)
    for key in KEYS:
        assert data["metrics"][key]["meta"]["detailGroup"] == "coast"
        assert data["metrics"][key]["meta"]["theme"] == "ambiente"
        assert data["metrics"][key]["meta"]["sourceMeta"]["snapshot"] == "data/source-snapshots/costa-mare-v123.json"
    for key in (KEYS[0], KEYS[1], KEYS[3], KEYS[4]):
        meta = data["metrics"][key]["meta"]
        assert meta["comparisonReference"] == "aggregate"
        assert meta["comparisonDifference"] == "percentagePoints"
        assert "media semplice" in meta["comparisonNote"]
    assert_quality(data["metrics"][KEYS[0]], snapshot)
    assert_samples(data["metrics"][KEYS[1]], snapshot)
    assert_blue_flags(data["metrics"][KEYS[2]], snapshot)
    assert_dynamics(data["metrics"][KEYS[3]], snapshot)
    assert_protected(data["metrics"][KEYS[4]], snapshot)
    assert_registry_and_ui(data)
    print("Costa e mare v1.23.0: 5 card, fonti, aggregati e 4 costieri + 3 n.a. verificati.")


if __name__ == "__main__":
    main()
