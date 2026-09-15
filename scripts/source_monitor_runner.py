#!/usr/bin/env python3
"""Orchestra il Source Monitor con profondità leggera o profonda."""
from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import monthly_data_check as base
import monthly_data_check_status as status

DEPTH_LABELS = {
    "light": "light — raggiungibilità, redirect e struttura; senza hash o verifiche semantiche profonde",
    "deep": "deep — controllo completo con hash e verifiche semantiche disponibili",
}


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--depth", choices=("light", "deep"), default="deep")
    known, forwarded = parser.parse_known_args(argv)
    return known, forwarded


def _skip_fuel(*_args, **_kwargs):
    return None, ""


def _skip_pnrr(*_args, **_kwargs):
    return None, ""


@contextmanager
def monitor_depth(depth: str) -> Iterator[None]:
    """Applica solo per il processo corrente le differenze tra light e deep."""
    original_should_hash = base.should_hash
    original_fuel = status.run_fuel_verification
    original_pnrr = status.run_pnrr_verification
    previous_depth = os.environ.get("MONITOR_CHECK_DEPTH")

    os.environ["MONITOR_CHECK_DEPTH"] = depth
    try:
        if depth == "light":
            base.should_hash = lambda *_args, **_kwargs: False
            status.run_fuel_verification = _skip_fuel
            status.run_pnrr_verification = _skip_pnrr
        yield
    finally:
        base.should_hash = original_should_hash
        status.run_fuel_verification = original_fuel
        status.run_pnrr_verification = original_pnrr
        if previous_depth is None:
            os.environ.pop("MONITOR_CHECK_DEPTH", None)
        else:
            os.environ["MONITOR_CHECK_DEPTH"] = previous_depth


def _option_path(args: list[str], name: str) -> Path | None:
    prefix = name + "="
    for index, value in enumerate(args):
        if value.startswith(prefix):
            return Path(value[len(prefix):])
        if value == name and index + 1 < len(args):
            return Path(args[index + 1])
    return None


def _write_json_depth(path: Path | None, depth: str) -> None:
    if path is None or not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return
    payload["depth"] = depth
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _annotate_markdown(path: Path | None, depth: str) -> None:
    if path is None or not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "**Profondità:**" in text:
        return
    lines = text.splitlines()
    insert_at = next(
        (index + 1 for index, line in enumerate(lines) if line.startswith("**Modalità:**")),
        min(4, len(lines)),
    )
    lines.insert(insert_at, f"**Profondità:** `{depth}` — {DEPTH_LABELS[depth]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def annotate_outputs(forwarded: list[str], depth: str) -> None:
    report_json = _option_path(forwarded, "--report-json")
    next_state = _option_path(forwarded, "--next-state")
    report_md = _option_path(forwarded, "--report-md")
    _write_json_depth(report_json, depth)
    _write_json_depth(next_state, depth)
    _annotate_markdown(report_md, depth)

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"depth={depth}\n")


def main(argv: list[str] | None = None) -> int:
    args, forwarded = parse_args(argv)
    with monitor_depth(args.depth):
        code = status.main(forwarded)
    if code == 0:
        annotate_outputs(forwarded, args.depth)
    print(f"Source monitor depth: {args.depth}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
