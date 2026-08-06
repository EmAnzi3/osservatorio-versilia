#!/usr/bin/env python3
"""Inspect current SIOPE metric rows and display formatting."""
from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "site-data.json"
METRICS = [
    "siopePayments",
    "currentPayments",
    "capitalPayments",
    "cashReceiptsPerResident",
    "cashBalancePerResident",
]


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    payload = {
        key: {
            "meta": data["metrics"][key].get("meta"),
            "rows": data["metrics"][key].get("rows"),
            "aggregate": data["metrics"][key].get("aggregate"),
            "method": data["metrics"][key].get("method"),
        }
        for key in METRICS
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
