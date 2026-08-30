#!/usr/bin/env python3
"""Forward-compatible regression contract for Costa e mare v1.23.

The original v1.23 test is preserved in test_costa_mare_v123_legacy.py.
This wrapper runs it unchanged on v1.23 and, on later releases, verifies that
the v1.23 coast dataset and UI contract are still intact without requiring the
whole catalog to remain frozen at 162 indicators.
"""
from __future__ import annotations

import re

import test_costa_mare_v123_legacy as legacy


def version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(item) for item in re.findall(r"\d+", str(value or ""))]
    return tuple(numbers[:3]) if numbers else (0,)


def main() -> None:
    data = legacy.load("data/site-data.json")
    if version_tuple(data.get("version")) == (1, 23, 0):
        legacy.main()
        return

    assert version_tuple(data.get("version")) > (1, 23, 0), data.get("version")
    snapshot = legacy.load("data/source-snapshots/costa-mare-v123.json")
    registry = legacy.load("data/source-registry.json")
    assert registry["expectedMetricCount"] >= 162
    assert registry["expectedInlineMetricCount"] >= 158
    assert registry["expectedExternalMetricCount"] == 4
    assert len(data["metrics"]) >= 162

    legacy.assert_snapshot(snapshot)
    for key in legacy.KEYS:
        assert data["metrics"][key]["meta"]["detailGroup"] == "coast"
        assert data["metrics"][key]["meta"]["theme"] == "ambiente"
        assert data["metrics"][key]["meta"]["sourceMeta"]["snapshot"] == "data/source-snapshots/costa-mare-v123.json"
    for key in (legacy.KEYS[0], legacy.KEYS[1], legacy.KEYS[3], legacy.KEYS[4]):
        meta = data["metrics"][key]["meta"]
        assert meta["comparisonReference"] == "aggregate"
        assert meta["comparisonDifference"] == "percentagePoints"
        assert "media semplice" in meta["comparisonNote"]

    legacy.assert_quality(data["metrics"][legacy.KEYS[0]], snapshot)
    legacy.assert_samples(data["metrics"][legacy.KEYS[1]], snapshot)
    legacy.assert_blue_flags(data["metrics"][legacy.KEYS[2]], snapshot)
    legacy.assert_dynamics(data["metrics"][legacy.KEYS[3]], snapshot)
    legacy.assert_protected(data["metrics"][legacy.KEYS[4]], snapshot)
    legacy.assert_monitor_state_preservation()
    legacy.assert_registry_and_ui(data)
    print(f"Costa e mare v1.23 preservata nella release {data['version']}: regressione verificata.")


if __name__ == "__main__":
    main()
