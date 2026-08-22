#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import build_opportunity_preview_v04 as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "reports" / "runtime" / "opportunities-v04.json"
DEFAULT_DIST = ROOT / "dist"


def build(payload_path: Path, dist: Path) -> Path:
    target = base.build(payload_path, dist)
    text = target.read_text(encoding="utf-8")
    text = text.replace("v0.4.2", "v0.4.3")
    target.write_text(text, encoding="utf-8")
    check = target.read_text(encoding="utf-8")
    if "Anteprima v0.4.3" not in check:
        raise SystemExit("Preview v0.4.3 non materializzata correttamente")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    print(f"Preview opportunità v0.4.3 materializzata: {build(args.data, args.dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
