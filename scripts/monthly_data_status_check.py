#!/usr/bin/env python3
"""Esegue il monitor mensile esistente e aggiunge lo stato canonico per indicatore."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import monthly_data_check_coverage as coverage
from data_status import markdown_status_addendum, upgrade_monitor_state


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--registry", type=Path, default=Path("data/source-registry.json"))
    parser.add_argument("--state", type=Path, default=Path("data/source-monitor-state.json"))
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--next-state", type=Path, required=True)
    parser.add_argument("--mode", choices=("live", "offline"), default="live")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = coverage.main([
        "--data", str(args.data),
        "--registry", str(args.registry),
        "--state", str(args.state),
        "--report-md", str(args.report_md),
        "--report-json", str(args.report_json),
        "--next-state", str(args.next_state),
        "--mode", args.mode,
    ])
    if result != 0:
        return result

    data = load_json(args.data)
    registry = load_json(args.registry)
    report = load_json(args.report_json)
    next_state = load_json(args.next_state)

    upgraded_state = upgrade_monitor_state(data, registry, next_state, report)
    report["metricStatusSchemaVersion"] = 1
    report["metrics"] = upgraded_state["metrics"]
    report["summary"]["metricStatusCount"] = len(upgraded_state["metrics"])

    write_json(args.next_state, upgraded_state)
    write_json(args.report_json, report)
    existing = args.report_md.read_text(encoding="utf-8").rstrip()
    args.report_md.write_text(existing + "\n\n" + markdown_status_addendum(upgraded_state["metrics"]) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
