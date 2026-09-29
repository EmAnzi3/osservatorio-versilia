#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

from opportunity_shadow_compare import compare_snapshots


def _snapshot() -> dict:
    return {
        "referenceDate": "2026-09-27",
        "opportunities": [
            {
                "id": "microzonazione",
                "title": "Microzonazione sismica",
                "url": "https://example.test/microzonazione",
                "deadline_at": "2026-10-17",
                "summary": "Studi comunali",
            }
        ],
        "archive": [],
    }


def main() -> int:
    reference = _snapshot()

    volatile = deepcopy(reference)
    volatile["referenceDate"] = "2026-09-28"
    volatile["generatedAt"] = "2026-09-28T07:45:00Z"
    volatile["opportunities"][0]["is_new"] = False
    result = compare_snapshots(reference, volatile)
    assert result["equivalent"] is True
    assert result["counts"]["modified"] == 0

    changed = deepcopy(volatile)
    changed["opportunities"][0]["deadline_at"] = "2026-10-18"
    result = compare_snapshots(reference, changed)
    assert result["equivalent"] is False
    assert result["counts"]["modified"] == 1

    added = deepcopy(volatile)
    added["opportunities"].append({
        "id": "mercati-rionali",
        "title": "Mercati rionali",
        "url": "https://example.test/mercati",
        "deadline_at": "2026-10-15",
    })
    result = compare_snapshots(reference, added)
    assert result["equivalent"] is False
    assert result["counts"]["added"] == 1

    print("Confronto semantico snapshot shadow: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
