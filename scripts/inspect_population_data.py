#!/usr/bin/env python3
"""Inspect the population metric structure used by the site."""
from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "site-data.json"
TOWN_NAMES = {
    "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta",
    "Seravezza", "Stazzema", "Viareggio",
}


def summarize(value, depth: int = 0):
    if depth > 6:
        return "<depth-limit>"
    if isinstance(value, dict):
        return {
            str(key): summarize(item, depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, list):
        if len(value) > 30:
            return [summarize(item, depth + 1) for item in value[:30]] + [f"<{len(value) - 30} more>"]
        return [summarize(item, depth + 1) for item in value]
    return value


def walk(value, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        identity = str(value.get("key") or value.get("id") or value.get("metric") or "")
        keys = {str(key) for key in value}
        has_towns = bool(keys & TOWN_NAMES)
        path_text = "/".join(path).casefold()
        if identity == "population" or has_towns and "population" in path_text:
            print("=== MATCH", "/".join(path), "===")
            print(json.dumps(summarize(value), ensure_ascii=False, indent=2)[:100000])
        for key, item in value.items():
            walk(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, path + (str(index),))


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print("TOP-LEVEL KEYS:", list(data))
    walk(data)


if __name__ == "__main__":
    main()
