#!/usr/bin/env python3
"""Ricostruisce lo snapshot pubblico verificato del Radar Opportunità v0.4.4.

La release base v0.4.3 resta immutabile e riproducibile. Sopra di essa vengono
applicate le opportunità Sport/LIFE v0.4.4; quando esiste uno snapshot prodotto
dalla routine giornaliera e supera i gate minimi, quello diventa la sorgente
pubblica della build.
"""
from __future__ import annotations

import base64
import json
import zlib
from datetime import date
from pathlib import Path

import run_opportunity_radar_v044 as radar_v044

ROOT = Path(__file__).resolve().parents[1]
PARTS = (
    ROOT / "data" / "opportunity-release-v043.part1.b85",
    ROOT / "data" / "opportunity-release-v043.part2.b85",
)
VERIFIED_V044 = ROOT / "data" / "opportunity-verified-v044.json"
DAILY = ROOT / "data" / "opportunity-daily-public.json"
TARGET = ROOT / "data" / "opportunity-release.json"


def _decode_base() -> dict:
    encoded = b"".join(path.read_bytes().strip() for path in PARTS)
    payload = zlib.decompress(base64.b85decode(encoded))
    data = json.loads(payload.decode("utf-8"))
    assert data.get("referenceDate") == "2026-08-24", data.get("referenceDate")
    assert data.get("releaseVersion") == "0.4.3", data.get("releaseVersion")
    assert len(data.get("opportunities") or []) == 25, len(data.get("opportunities") or [])
    assert len(((data.get("sourceCoverage") or {}).get("rows") or [])) == 47
    return data


def _merge_v044(base: dict) -> dict:
    data = json.loads(json.dumps(base))
    reference = date.fromisoformat(str(data["referenceDate"]))
    existing_ids = {
        str(item.get("coverage_id") or "")
        for item in data.get("opportunities") or []
        if item.get("coverage_id")
    }
    existing_urls = {
        radar_v044.radar.v025.normalized_url(str(item.get("url") or ""))
        for item in data.get("opportunities") or []
    }

    for item in data.get("opportunities") or []:
        item.setdefault("is_new", False)

    verified = radar_v044._load(VERIFIED_V044)
    for entry in verified.get("entries") or []:
        coverage_id = str(entry.get("coverage_id") or "")
        norm_url = radar_v044.radar.v025.normalized_url(str(entry.get("url") or ""))
        if coverage_id in existing_ids or (norm_url and norm_url in existing_urls):
            continue
        item = radar_v044.build_seed_item(entry, reference, "release_verified")
        first_seen = str(entry.get("first_seen_at") or data["referenceDate"])
        item["first_seen_at"] = first_seen
        try:
            age = (reference - date.fromisoformat(first_seen)).days
        except ValueError:
            age = 999
        item["is_new"] = 0 <= age < radar_v044.NEW_WINDOW_DAYS
        data.setdefault("opportunities", []).append(item)
        existing_ids.add(coverage_id)
        if norm_url:
            existing_urls.add(norm_url)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    data["opportunities"].sort(
        key=lambda x: (
            order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
            str(x.get("deadline_at") or "9999-99-99"),
            str(x.get("title") or ""),
        )
    )
    radar_v044.core._recompute_v04_counts(data)
    data["newOpportunityWindowDays"] = radar_v044.NEW_WINDOW_DAYS
    data.setdefault("counts", {})["new"] = sum(bool(x.get("is_new")) for x in data["opportunities"])
    data["releaseVersion"] = "0.4.4"
    data["engineVersion"] = "0.4.4"
    data["coverageVersion"] = "0.4.4"
    data["uiVersion"] = "0.4.4"
    return data


def _daily_is_publishable(candidate: dict, baseline: dict) -> bool:
    try:
        candidate_date = date.fromisoformat(str(candidate.get("referenceDate") or ""))
        baseline_date = date.fromisoformat(str(baseline.get("referenceDate") or ""))
    except ValueError:
        return False
    if candidate_date < baseline_date:
        return False
    if candidate.get("releaseVersion") != "0.4.4":
        return False
    if candidate.get("continuityHold") or candidate.get("coverageHold"):
        return False
    backtest = candidate.get("backtest") or {}
    if backtest and not backtest.get("passed", False):
        return False
    audit = candidate.get("coverageAudit") or {}
    if audit and audit.get("status") != "pass":
        return False
    regional = candidate.get("regionalCompleteness") or {}
    if regional and regional.get("status") not in {"pass", "degraded"}:
        return False
    opportunities = candidate.get("opportunities")
    if not isinstance(opportunities, list) or not opportunities:
        return False
    return True


def main() -> None:
    baseline = _merge_v044(_decode_base())
    data = baseline
    source = "baseline v0.4.4"
    if DAILY.exists():
        try:
            candidate = json.loads(DAILY.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            candidate = {}
        if isinstance(candidate, dict) and _daily_is_publishable(candidate, baseline):
            data = candidate
            source = "snapshot giornaliero verificato"

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = len(data.get("opportunities") or [])
    monitored = len(((data.get("sourceCoverage") or {}).get("rows") or []))
    new_count = int((data.get("counts") or {}).get("new") or 0)
    print(
        f"Snapshot Radar pubblico: {total} opportunità · {new_count} nuove · "
        f"{monitored} fonti · riferimento {data.get('referenceDate')} · v0.4.4 · {source}"
    )


if __name__ == "__main__":
    main()
