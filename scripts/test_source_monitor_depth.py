#!/usr/bin/env python3
"""Regressione A2.3: separazione tra controllo light e deep."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import monthly_data_check as base
import monthly_data_check_status as status
import source_monitor_runner as runner


def test_runtime_switch() -> None:
    original_should_hash = base.should_hash
    original_fuel = status.run_fuel_verification
    original_pnrr = status.run_pnrr_verification

    assert base.should_hash("https://example.test/data.csv", "text/csv", {}) is True
    with runner.monitor_depth("light"):
        assert base.should_hash("https://example.test/data.csv", "text/csv", {}) is False
        assert status.run_fuel_verification({}, {}, {}, "") == (None, "")
        assert status.run_pnrr_verification({}, {}, "") == (None, "")

    assert base.should_hash is original_should_hash
    assert status.run_fuel_verification is original_fuel
    assert status.run_pnrr_verification is original_pnrr

    with runner.monitor_depth("deep"):
        assert base.should_hash("https://example.test/data.csv", "text/csv", {}) is True
        assert status.run_fuel_verification is original_fuel
        assert status.run_pnrr_verification is original_pnrr


def test_output_annotation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report_json = root / "report.json"
        state_json = root / "state.json"
        report_md = root / "report.md"
        report_json.write_text(json.dumps({"status": "no_changes"}), encoding="utf-8")
        state_json.write_text(json.dumps({"schemaVersion": 2}), encoding="utf-8")
        report_md.write_text(
            "@EmAnzi3\n\n## Controllo dati\n\n**Esito:** `no_changes`  \n**Modalità:** `live`\n",
            encoding="utf-8",
        )

        forwarded = [
            "--report-json", str(report_json),
            "--next-state", str(state_json),
            "--report-md", str(report_md),
        ]
        runner.annotate_outputs(forwarded, "light")

        assert json.loads(report_json.read_text(encoding="utf-8"))["depth"] == "light"
        assert json.loads(state_json.read_text(encoding="utf-8"))["depth"] == "light"
        markdown = report_md.read_text(encoding="utf-8")
        assert "**Profondità:** `light`" in markdown
        assert "senza hash" in markdown


if __name__ == "__main__":
    test_runtime_switch()
    test_output_annotation()
    print("Source monitor light/deep regression passed.")
