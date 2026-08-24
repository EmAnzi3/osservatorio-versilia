#!/usr/bin/env python3
"""Ricostruisce lo snapshot pubblico verificato del Radar Opportunità v0.4.3."""
from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = (
    ROOT / "data" / "opportunity-release-v043.part1.b85",
    ROOT / "data" / "opportunity-release-v043.part2.b85",
)
TARGET = ROOT / "data" / "opportunity-release.json"


def main() -> None:
    encoded = b"".join(path.read_bytes().strip() for path in PARTS)
    payload = zlib.decompress(base64.b85decode(encoded))
    data = json.loads(payload.decode("utf-8"))
    assert data.get("referenceDate") == "2026-08-24", data.get("referenceDate")
    assert data.get("releaseVersion") == "0.4.3", data.get("releaseVersion")
    assert len(data.get("opportunities") or []) == 25, len(data.get("opportunities") or [])
    assert len(((data.get("sourceCoverage") or {}).get("rows") or [])) == 47
    TARGET.write_bytes(payload)
    print("Snapshot Radar pubblico: 25 opportunità · 47 fonti · riferimento 2026-08-24 · v0.4.3")


if __name__ == "__main__":
    main()
