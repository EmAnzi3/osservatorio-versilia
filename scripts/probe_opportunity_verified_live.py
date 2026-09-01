#!/usr/bin/env python3
"""Diagnostica live delle opportunità verificate che alimentano coverageHold.

Esegue lo stesso verificatore resiliente usato dal refresh giornaliero, ma solo
sulle entry versionate dei layer v0.4-v0.4.4. Non pubblica né modifica snapshot.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

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


def main() -> int:
    today = date.today()
    failed: list[dict[str, str]] = []
    checked = 0

    for path in VERIFIED_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        max_days = int(payload.get("evidenceFallbackMaxDays") or 7)
        for entry in payload.get("entries") or []:
            coverage_id = str(entry.get("coverage_id") or "").strip()
            url = str(entry.get("url") or "").strip()
            if not coverage_id or not url:
                continue
            checked += 1
            result = hardened.verify_entry_resilient(
                entry,
                today,
                live=True,
                fallback_max_days=max_days,
            )
            ok, status, error = result
            print(f"{path.name} :: {coverage_id} :: ok={ok} :: status={status}", flush=True)
            if not ok:
                row = {
                    "file": path.name,
                    "coverage_id": coverage_id,
                    "title": str(entry.get("title") or ""),
                    "source_id": str(entry.get("source_id") or ""),
                    "url": url,
                    "reason": str(error or "verifica fallita"),
                }
                failed.append(row)
                print("COVERAGE HOLD DETECTED", flush=True)
                print(json.dumps(row, ensure_ascii=False, indent=2), flush=True)

    print(f"Verified entries checked: {checked}", flush=True)
    print(f"Coverage holds: {len(failed)}", flush=True)
    if failed:
        print(json.dumps(failed, ensure_ascii=False, indent=2), flush=True)
        return 1
    print("DIRECT VERIFIED COVERAGE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
