#!/usr/bin/env python3
"""Forward-compatible regression contract for Costa e mare v1.23.

The original v1.23 test is preserved in test_costa_mare_v123_legacy.py.
This wrapper runs it unchanged on v1.23 and, on later releases, verifies that
the v1.23 coast dataset and UI contract are still intact without requiring the
whole catalog or the Costa e mare section to remain frozen at v1.23.
"""
from __future__ import annotations

import copy
import re

import test_costa_mare_v123_legacy as legacy
import test_demanio_marittimo_v127 as demanio


def version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(item) for item in re.findall(r"\d+", str(value or ""))]
    return tuple(numbers[:3]) if numbers else (0,)


def legacy_compatible_view(data: dict) -> dict:
    """Return a v1.23-shaped theme view without mutating the current catalog.

    Later coast lots may append metrics to the same semantic section. The legacy
    UI checks still apply to the original five indicators; only the section
    membership is projected back to the v1.23 subset for that historical check.
    """
    projected = copy.deepcopy(data)
    environment = projected["themes"]["ambiente"]
    section = next(item for item in environment["sections"] if item.get("key") == "costa-mare")
    current = list(section.get("metrics", []))
    assert current[: len(legacy.KEYS)] == list(legacy.KEYS), current
    section["metrics"] = list(legacy.KEYS)
    appended = set(current[len(legacy.KEYS) :])
    environment["metrics"] = [key for key in environment["metrics"] if key not in appended]
    return projected


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
    legacy.assert_registry_and_ui(legacy_compatible_view(data))
    if version_tuple(data.get("version")) >= (1, 27, 0):
        demanio.main()
    print(f"Costa e mare v1.23 preservata nella release {data['version']}: regressione verificata.")


if __name__ == "__main__":
    main()
