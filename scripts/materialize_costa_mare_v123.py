#!/usr/bin/env python3
"""Compatibility wrapper for the Costa e mare v1.23 materializer.

The original v1.23 materializer is preserved in
materialize_costa_mare_v123_legacy.py. On v1.23 it behaves exactly as before;
on later catalog releases the coast lot is already materialized, so this
wrapper validates its snapshot and exits without rewriting release metadata.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from materialize_costa_mare_v123_legacy import *  # noqa: F401,F403
import materialize_costa_mare_v123_legacy as legacy

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "costa-mare-v123.json"


def version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(item) for item in re.findall(r"\d+", str(value or ""))]
    return tuple(numbers[:3]) if numbers else (0,)


def main() -> int:
    site = json.loads(SITE_PATH.read_text(encoding="utf-8"))
    current = version_tuple(site.get("version"))
    target = version_tuple(legacy.VERSION)
    if current > target:
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        legacy.validate_snapshot(snapshot, site)
        missing = [key for key in legacy.KEYS if key not in site.get("metrics", {})]
        if missing:
            raise RuntimeError(f"Costa e mare v1.23 non incorporata nella release successiva: {missing}")
        print(f"Costa e mare {legacy.VERSION} già incorporata in {site.get('version')}: no-op verificato.")
        return 0
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
