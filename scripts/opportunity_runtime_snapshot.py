#!/usr/bin/env python3
"""Seleziona l'ultimo snapshot Radar verificato per refresh e deploy.

Il codice applicativo resta su ``main``; lo stato giornaliero verificato vive sul
branch tecnico ``automation/opportunity-radar-daily``. Questo modulo impedisce
che un branch corrotto, futuro o fermo a un run fallito possa sostituire lo
snapshot incluso nel checkout.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Snapshot non valido: {path}")
    return payload


def _reference_date(payload: dict[str, Any]) -> date | None:
    try:
        return date.fromisoformat(str(payload.get("referenceDate") or ""))
    except ValueError:
        return None


def validation_errors(payload: dict[str, Any], today: date) -> list[str]:
    errors: list[str] = []
    reference = _reference_date(payload)
    if payload.get("releaseVersion") != "0.4.4":
        errors.append("releaseVersion")
    if payload.get("dailyHardeningVersion") != "0.4.4-h5":
        errors.append("dailyHardeningVersion")
    if reference is None:
        errors.append("referenceDate")
    elif reference > today:
        errors.append("referenceDate futura")
    if not isinstance(payload.get("opportunities"), list) or not payload.get("opportunities"):
        errors.append("opportunities")
    if payload.get("continuityHold"):
        errors.append("continuityHold")
    if payload.get("coverageHold"):
        errors.append("coverageHold")
    coverage = payload.get("coverageAudit") or {}
    if coverage and coverage.get("status") != "pass":
        errors.append("coverageAudit")
    if (coverage.get("runtimeUncoveredFamilies") or []):
        errors.append("runtimeUncoveredFamilies")
    backtest = payload.get("backtest") or {}
    if backtest and backtest.get("passed") is not True:
        errors.append("backtest")
    regional = payload.get("regionalCompleteness") or {}
    if regional and regional.get("status") not in {"pass", "degraded"}:
        errors.append("regionalCompleteness")
    reconciliation = payload.get("continuityReconciliation") or {}
    if reconciliation and int(reconciliation.get("remaining") or 0) != 0:
        errors.append("continuityReconciliation")
    return errors


def select_snapshot(
    main_path: Path,
    candidate_path: Path | None,
    *,
    today: date,
) -> tuple[Path, dict[str, Any], str]:
    main = _load(main_path)
    main_errors = validation_errors(main, today)
    if main_errors:
        raise RuntimeError("Snapshot main non verificato: " + ", ".join(main_errors))

    if candidate_path is None or not candidate_path.is_file():
        return main_path, main, "main"

    try:
        candidate = _load(candidate_path)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Snapshot runtime ignorato: {exc}")
        return main_path, main, "main"

    candidate_errors = validation_errors(candidate, today)
    if candidate_errors:
        print("Snapshot runtime ignorato: " + ", ".join(candidate_errors))
        return main_path, main, "main"

    main_date = _reference_date(main)
    candidate_date = _reference_date(candidate)
    if candidate_date is not None and main_date is not None and candidate_date >= main_date:
        return candidate_path, candidate, "runtime"
    return main_path, main, "main"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    selected_path, payload, source = select_snapshot(
        args.main,
        args.candidate,
        today=args.today,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(selected_path, args.output)
    print(f"Snapshot Radar selezionato: {source} · {payload.get('referenceDate')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
