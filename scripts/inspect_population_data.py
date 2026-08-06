#!/usr/bin/env python3
"""Inspect the full population metric structure used by the site."""
from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "site-data.json"


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    population = data["metrics"]["population"]
    print(json.dumps(population, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
