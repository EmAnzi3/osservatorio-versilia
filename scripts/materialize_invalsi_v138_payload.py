#!/usr/bin/env python3
"""Reconstruct and run the validated INVALSI v1.38 snapshot transactionally."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_DIR = ROOT / "data" / "source-snapshots" / "invalsi-v138-b64"
TARGET = ROOT / "data" / "source-snapshots" / "invalsi-v138-official.json"
MATERIALIZER = ROOT / "scripts" / "materialize_invalsi_v138.py"
EXPECTED_PARTS = 5
EXPECTED_SHA256 = "bee5b0021704b2053277aa19df35d77ed0aa4b9e2cfc4dfa3d64c16a61c1fd65"
EXPECTED_SIZE = 70859


def reconstruct() -> bytes:
    parts = [PART_DIR / f"part-{index:02d}.b64" for index in range(EXPECTED_PARTS)]
    missing = [path.name for path in parts if not path.exists()]
    if missing:
        raise RuntimeError(f"v1.38: frammenti snapshot mancanti: {', '.join(missing)}")
    encoded = "".join(path.read_text(encoding="ascii").strip() for path in parts)
    try:
        payload = gzip.decompress(base64.b64decode(encoded, validate=True))
    except Exception as exc:
        raise RuntimeError("v1.38: payload snapshot gzip/base64 non valido") from exc
    if len(payload) != EXPECTED_SIZE:
        raise RuntimeError(f"v1.38: dimensione snapshot {len(payload)}, attesa {EXPECTED_SIZE}")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"v1.38: SHA-256 snapshot {digest}, atteso {EXPECTED_SHA256}")
    parsed = json.loads(payload)
    if parsed.get("release") != "v1.38.0" or parsed.get("schemaVersion") != 1:
        raise RuntimeError("v1.38: release/schema snapshot ricostruito inatteso")
    return payload


def main() -> None:
    payload = reconstruct()
    existed = TARGET.exists()
    previous = TARGET.read_bytes() if existed else None
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(payload)
    try:
        runpy.run_path(str(MATERIALIZER), run_name="__main__")
    finally:
        if existed:
            TARGET.write_bytes(previous or b"")
        else:
            TARGET.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
