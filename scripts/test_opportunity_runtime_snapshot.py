#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

from opportunity_runtime_snapshot import select_snapshot, validation_errors


def _snapshot(reference: str) -> dict:
    return {
        "referenceDate": reference,
        "releaseVersion": "0.4.4",
        "dailyHardeningVersion": "0.4.4-h5",
        "opportunities": [{"id": "one"}],
        "continuityHold": [],
        "coverageHold": [],
        "coverageAudit": {"status": "pass", "runtimeUncoveredFamilies": []},
        "backtest": {"passed": True},
        "regionalCompleteness": {"status": "pass"},
        "continuityReconciliation": {"remaining": 0},
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> int:
    today = date(2026, 9, 15)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        main_path = root / "main.json"
        runtime_path = root / "runtime.json"
        _write(main_path, _snapshot("2026-09-07"))
        _write(runtime_path, _snapshot("2026-09-15"))

        selected, payload, source = select_snapshot(main_path, runtime_path, today=today)
        assert selected == runtime_path
        assert payload["referenceDate"] == "2026-09-15"
        assert source == "runtime"

        broken = _snapshot("2026-09-15")
        broken["coverageHold"] = [{"id": "blocked"}]
        _write(runtime_path, broken)
        selected, _, source = select_snapshot(main_path, runtime_path, today=today)
        assert selected == main_path and source == "main"

        future = _snapshot("2026-09-16")
        _write(runtime_path, future)
        assert "referenceDate futura" in validation_errors(future, today)
        selected, _, source = select_snapshot(main_path, runtime_path, today=today)
        assert selected == main_path and source == "main"

        older = _snapshot("2026-09-06")
        _write(runtime_path, older)
        selected, _, source = select_snapshot(main_path, runtime_path, today=today)
        assert selected == main_path and source == "main"

    print("Selezione snapshot runtime Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
