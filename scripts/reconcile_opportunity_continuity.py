#!/usr/bin/env python3
"""Riconcilia falsi negativi di continuità usando evidenza ufficiale a TTL breve.

Non disattiva il gate di continuità: una scheda del run precedente può essere
ripristinata solo se esiste un'evidenza versionata esplicita, ancora fresca e
con scadenza futura. Alla scadenza del TTL il gate torna rosso finché la fonte
non viene verificata di nuovo.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v043 as v043

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "data" / "opportunity-continuity-evidence-v1.json"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON non valido: {path}")
    return payload


def _identity(item: dict[str, Any]) -> str:
    rule_id = str(item.get("rule_id") or "")
    if rule_id:
        return f"rule:{rule_id}"
    return str(v043.radar.v025.identity_key(item))


def _fresh(entry: dict[str, Any], today: date, max_days: int) -> bool:
    try:
        verified = date.fromisoformat(str(entry.get("evidence_verified_at") or ""))
    except ValueError:
        return False
    age = (today - verified).days
    if age < 0 or age > max_days:
        return False
    deadline_text = str(entry.get("deadline_at") or "")
    if deadline_text:
        try:
            if date.fromisoformat(deadline_text) < today:
                return False
        except ValueError:
            return False
    return bool(entry.get("evidence_url"))


def _refresh_summaries(result: dict[str, Any]) -> None:
    opportunities = list(result.get("opportunities") or [])
    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    opportunities.sort(
        key=lambda item: (
            order.get(str(item.get("lifecycle_stage") or "application_open"), 9),
            str(item.get("deadline_at") or "9999-99-99"),
            str(item.get("title") or ""),
        )
    )
    result["opportunities"] = opportunities
    counts = result.setdefault("counts", {})
    counts["public"] = len(opportunities)
    counts["eligible"] = sum(item.get("eligibility") == "eligible" for item in opportunities)
    counts["conditional"] = sum(item.get("eligibility") == "conditional" for item in opportunities)
    counts["continuityHold"] = len(result.get("continuityHold") or [])
    counts["applicationOpen"] = sum(str(item.get("lifecycle_stage") or "application_open") == "application_open" for item in opportunities)
    counts["rollingOpen"] = sum(str(item.get("lifecycle_stage") or "application_open") == "rolling_open" for item in opportunities)
    counts["announcedUpcoming"] = sum(str(item.get("lifecycle_stage") or "application_open") == "announced_upcoming" for item in opportunities)
    result["lifecycleSummary"] = {
        "application_open": counts["applicationOpen"],
        "rolling_open": counts["rollingOpen"],
        "announced_upcoming": counts["announcedUpcoming"],
    }
    for state in result.get("sources") or []:
        sid = str(state.get("sourceId") or "")
        state["publicCount"] = sum(str(item.get("source_id") or "") == sid for item in opportunities)
    # Il motore dispone già del calcolo canonico del riepilogo per Comune.
    v043.radar.v025._recompute_summary(result)


def reconcile(
    result: dict[str, Any],
    previous: dict[str, Any] | None,
    evidence: dict[str, Any],
    today: date,
) -> list[dict[str, Any]]:
    holds = list(result.get("continuityHold") or [])
    if not holds or not previous:
        _refresh_summaries(result)
        return []

    max_days = int(evidence.get("maxEvidenceAgeDays") or 7)
    by_identity = {
        str(entry.get("identity_key") or ""): entry
        for entry in evidence.get("entries") or []
        if entry.get("identity_key")
    }
    previous_by_identity = {
        _identity(item): item for item in previous.get("opportunities") or []
    }
    current_identities = {_identity(item) for item in result.get("opportunities") or []}
    remaining: list[dict[str, Any]] = []
    recovered: list[dict[str, Any]] = []

    for hold in holds:
        key = str(hold.get("identity_key") or "")
        entry = by_identity.get(key)
        prior = previous_by_identity.get(key)
        if not entry or not prior or not _fresh(entry, today, max_days):
            remaining.append(hold)
            continue
        if str(entry.get("source_id") or "") != str(prior.get("source_id") or ""):
            remaining.append(hold)
            continue
        if str(entry.get("url") or "") != str(prior.get("url") or ""):
            remaining.append(hold)
            continue
        if not prior.get("verified_direct") or (prior.get("quality_gate") or {}).get("status") != "pass":
            remaining.append(hold)
            continue
        if key in current_identities:
            continue

        item = copy.deepcopy(prior)
        item.setdefault("lifecycle_stage", "application_open")
        item.setdefault("lifecycle_label", "Aperta")
        item["verification_status"] = "cached_recent_continuity"
        item["continuity_recovered"] = True
        item["continuity_evidence_verified_at"] = entry.get("evidence_verified_at")
        item["continuity_evidence_url"] = entry.get("evidence_url")
        result.setdefault("opportunities", []).append(item)
        current_identities.add(key)
        recovered.append({
            "identity_key": key,
            "title": item.get("title"),
            "source_id": item.get("source_id"),
            "evidence_verified_at": entry.get("evidence_verified_at"),
        })

    result["continuityHold"] = remaining
    result["continuityRecovered"] = recovered
    _refresh_summaries(result)
    return recovered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--date", dest="reference_date", default=date.today().isoformat())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    today = date.fromisoformat(args.reference_date)
    result = _load(args.current)
    previous = _load(args.previous) if args.previous and args.previous.exists() else None
    evidence = _load(args.evidence)
    recovered = reconcile(result, previous, evidence, today)
    args.current.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report:
        args.report.write_text(v043.render_markdown(result), encoding="utf-8")
    code = v043._exit_code(result)
    print(f"Continuità riconciliata: {len(recovered)} recuperate · {len(result.get('continuityHold') or [])} hold residui · exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
