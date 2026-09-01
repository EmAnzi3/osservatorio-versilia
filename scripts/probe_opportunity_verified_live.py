#!/usr/bin/env python3
"""Diagnostica live delle opportunità verificate che alimentano coverageHold.

Esegue lo stesso verificatore resiliente usato dal refresh giornaliero, ma solo
sulle entry versionate dei layer v0.4-v0.4.4. Non pubblica né modifica snapshot.
Le verifiche indipendenti sono parallele per non sommare i timeout dei portali.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import opportunity_daily_refresh_revalidated as hardened

VERIFIED_FILES = (
    ROOT / "data" / "opportunity-verified-v04.json",
    ROOT / "data" / "opportunity-verified-v04-extra.json",
    ROOT / "data" / "opportunity-verified-v042.json",
    ROOT / "data" / "opportunity-verified-v043.json",
    ROOT / "data" / "opportunity-verified-v044.json",
)


def _check(task: tuple[Path, int, dict[str, Any]], today: date) -> dict[str, Any]:
    path, max_days, entry = task
    coverage_id = str(entry.get("coverage_id") or "").strip()
    ok, status, error = hardened.verify_entry_resilient(
        entry,
        today,
        live=True,
        fallback_max_days=max_days,
    )
    return {
        "file": path.name,
        "coverage_id": coverage_id,
        "title": str(entry.get("title") or ""),
        "source_id": str(entry.get("source_id") or ""),
        "url": str(entry.get("url") or ""),
        "ok": bool(ok),
        "status": str(status),
        "reason": str(error or ""),
    }


def main() -> int:
    today = date.today()
    tasks: list[tuple[Path, int, dict[str, Any]]] = []
    for path in VERIFIED_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        max_days = int(payload.get("evidenceFallbackMaxDays") or 7)
        for entry in payload.get("entries") or []:
            if entry.get("coverage_id") and entry.get("url"):
                tasks.append((path, max_days, entry))

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_check, task, today): task for task in tasks}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(
                f"{row['file']} :: {row['coverage_id']} :: ok={row['ok']} :: status={row['status']}",
                flush=True,
            )
            if not row["ok"]:
                print("COVERAGE HOLD DETECTED", flush=True)
                print(json.dumps(row, ensure_ascii=False, indent=2), flush=True)

    rows.sort(key=lambda x: (x["file"], x["coverage_id"]))
    failed = [row for row in rows if not row["ok"]]
    print(f"Verified entries checked: {len(rows)}", flush=True)
    print(f"Coverage holds: {len(failed)}", flush=True)
    if failed:
        print(json.dumps(failed, ensure_ascii=False, indent=2), flush=True)
        return 1
    print("DIRECT VERIFIED COVERAGE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
