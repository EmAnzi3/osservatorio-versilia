#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.4.4 — Sport, LIFE e first-seen.

Estende la v0.4.3 mantenendo il principio coverage-first:
- amplia il discovery del Dipartimento per lo Sport oltre Sport e Periferie;
- rende LIFE/CINEA un presidio topic-by-topic;
- promuove solo opportunità con ruolo comunale documentato;
- versiona la prima rilevazione per poter evidenziare le novità nel pubblico.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v043 as prev

core = prev.core
ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_V044 = ROOT / "data" / "opportunity-discovery-v044.json"
EVIDENCE_V044 = ROOT / "data" / "opportunity-coverage-evidence-v044.json"
SENTINELS_V044 = ROOT / "data" / "opportunity-coverage-sentinels-v044.json"
VERIFIED_V044 = ROOT / "data" / "opportunity-verified-v044.json"
NEW_WINDOW_DAYS = 7

_PREV_COMPOSE = core.compose_runtime_payloads
_PREV_INJECT = core.inject_verified_v04
_PREV_AUDIT = core.build_coverage_audit
_PREV_RUN = core.run_v04
_PREV_RENDER = core.render_markdown
_PREV_EXIT = core._exit_code


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _PREV_COMPOSE()
    extra = core._load(DISCOVERY_V044)
    by_id = {
        str(source.get("id") or ""): source
        for source in config.get("discoverySources") or []
        if source.get("id")
    }
    for source_id, override in (extra.get("sourceOverrides") or {}).items():
        source_id = str(source_id)
        if source_id not in by_id:
            raise RuntimeError(f"Override v0.4.4 riferito a fonte non configurata: {source_id}")
        by_id[source_id].update(dict(override or {}))

    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        current = dict(registry.get(str(source_id)) or {})
        current.update(dict(meta or {}))
        registry[str(source_id)] = current

    config["schemaVersion"] = 4
    coverage["schemaVersion"] = "0.4.4"
    return config, coverage


def _new_state(first_seen: Any, today: date) -> tuple[str, bool]:
    text = str(first_seen or today.isoformat())
    try:
        seen = date.fromisoformat(text)
    except ValueError:
        seen = today
        text = today.isoformat()
    age = (today - seen).days
    return text, 0 <= age < NEW_WINDOW_DAYS


def _inject_verified_v044(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    payload = core._load(VERIFIED_V044)
    max_days = int(payload.get("evidenceFallbackMaxDays") or 7)
    resolved: set[str] = set()
    existing_coverage = {
        str(x.get("coverage_id") or "")
        for x in result.get("opportunities") or []
        if x.get("coverage_id")
    }
    existing_urls = {
        core.radar.v025.normalized_url(str(x.get("url") or ""))
        for x in result.get("opportunities") or []
    }

    for entry in payload.get("entries") or []:
        coverage_id = str(entry.get("coverage_id") or "")
        ok, verification_status, error = core.verify_entry(
            entry,
            today,
            detail_payloads=detail_payloads,
            live=live,
            fallback_max_days=max_days,
        )
        if not ok:
            result.setdefault("coverageHold", []).append({
                "coverage_id": coverage_id,
                "title": entry.get("title"),
                "source_id": entry.get("source_id"),
                "url": entry.get("url"),
                "reason": error,
            })
            continue

        item = core.build_seed_item(entry, today, verification_status)
        item["first_seen_at"], item["is_new"] = _new_state(entry.get("first_seen_at"), today)
        resolved.add(coverage_id)
        if core._is_expired_application(entry, today):
            core._append_archive(result, item)
            continue

        norm_url = core.radar.v025.normalized_url(str(item.get("url") or ""))
        if coverage_id in existing_coverage or (norm_url and norm_url in existing_urls):
            # L'identità può essere già emersa dal collector: completa i metadati first-seen.
            for current in result.get("opportunities") or []:
                current_norm = core.radar.v025.normalized_url(str(current.get("url") or ""))
                if str(current.get("coverage_id") or "") == coverage_id or (norm_url and current_norm == norm_url):
                    current.setdefault("coverage_id", coverage_id)
                    current["first_seen_at"], current["is_new"] = _new_state(entry.get("first_seen_at"), today)
                    break
            continue

        result.setdefault("opportunities", []).append(item)
        existing_coverage.add(coverage_id)
        if norm_url:
            existing_urls.add(norm_url)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    result.setdefault("opportunities", []).sort(
        key=lambda x: (
            order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
            str(x.get("deadline_at") or "9999-99-99"),
            str(x.get("title") or ""),
        )
    )
    return resolved


def inject_verified_v04(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    resolved = set(_PREV_INJECT(result, today, detail_payloads=detail_payloads, live=live))
    resolved.update(_inject_verified_v044(result, today, detail_payloads=detail_payloads, live=live))
    return resolved


def _v044_evidence_audit(result: dict[str, Any], today: date) -> dict[str, Any]:
    cfg = core._load(EVIDENCE_V044)
    max_age = int(cfg.get("maxEvidenceAgeDays") or 45)
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }
    contract = core._load(core.CONTRACT_V04)
    families = {str(x.get("id") or "") for x in contract.get("requiredFamilies") or []}
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    stale: list[str] = []
    for entry in cfg.get("entries") or []:
        source_id = str(entry.get("source_id") or "")
        family = str(entry.get("family") or "")
        try:
            verified = date.fromisoformat(str(entry.get("evidence_verified_at") or ""))
            age = (today - verified).days
        except ValueError:
            age = max_age + 1
        ok = source_id in configured and family in families and bool(entry.get("evidence_url")) and 0 <= age <= max_age
        if source_id not in configured:
            missing.append(source_id)
        if not (0 <= age <= max_age):
            stale.append(source_id)
        rows.append({
            "source_id": source_id,
            "family": family,
            "ageDays": age,
            "configured": source_id in configured,
            "familyInContract": family in families,
            "fresh": 0 <= age <= max_age,
            "verified": ok,
        })
    return {
        "status": "pass" if rows and all(x["verified"] for x in rows) else "fail",
        "sourcesExpected": len(rows),
        "sourcesVerified": sum(bool(x["verified"]) for x in rows),
        "missingSources": sorted(set(missing)),
        "staleEvidence": sorted(set(stale)),
        "rows": rows,
    }


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    audit = _PREV_AUDIT(result, resolved, today)
    sentinels = core._load(SENTINELS_V044).get("cases") or []
    verified = core._load(VERIFIED_V044).get("entries") or []
    verified_by_id = {str(x.get("coverage_id") or ""): x for x in verified}
    missing = list(audit.get("missingCurrentSentinels") or [])
    resolved_count = int(audit.get("currentSentinelsResolved") or 0)
    for case in sentinels:
        coverage_id = str(case.get("coverage_id") or "")
        entry = verified_by_id.get(coverage_id) or {}
        if core._is_expired_application(entry, today):
            continue
        if coverage_id in resolved:
            resolved_count += 1
        else:
            missing.append(str(case.get("id") or coverage_id))
    evidence = _v044_evidence_audit(result, today)
    audit["currentSentinelsResolved"] = resolved_count
    audit["missingCurrentSentinels"] = sorted(set(missing))
    audit["sportLifeCoverage"] = evidence
    if audit["missingCurrentSentinels"] or evidence.get("status") != "pass":
        audit["status"] = "fail"
    return audit


def _ensure_first_seen(result: dict[str, Any], today: date) -> None:
    for item in result.get("opportunities") or []:
        first, is_new = _new_state(item.get("first_seen_at") or item.get("verified_at") or today.isoformat(), today)
        item["first_seen_at"] = first
        item["is_new"] = bool(item.get("is_new", is_new)) and is_new
    result["newOpportunityWindowDays"] = NEW_WINDOW_DAYS
    result.setdefault("counts", {})["new"] = sum(bool(x.get("is_new")) for x in result.get("opportunities") or [])


def run_v04(
    today: date,
    *,
    previous_path: Path | None = None,
    payloads: dict[str, str] | None = None,
    detail_payloads: dict[str, str] | None = None,
    discovery_payloads: dict[str, str] | None = None,
) -> dict[str, Any]:
    result = _PREV_RUN(
        today,
        previous_path=previous_path,
        payloads=payloads,
        detail_payloads=detail_payloads,
        discovery_payloads=discovery_payloads,
    )
    _ensure_first_seen(result, today)
    result["engineVersion"] = "0.4.4"
    result["coverageVersion"] = "0.4.4"
    result["uiVersion"] = "0.4.4"
    return result


def render_markdown(result: dict[str, Any]) -> str:
    text = _PREV_RENDER(result).rstrip()
    coverage = ((result.get("coverageAudit") or {}).get("sportLifeCoverage") or {})
    return text + "\n\n## Sport + LIFE v0.4.4\n\n" + (
        f"Esito: **{str(coverage.get('status', 'unknown')).upper()}** · evidenze ufficiali fresche: "
        f"**{coverage.get('sourcesVerified', 0)}/{coverage.get('sourcesExpected', 0)}** · "
        f"novità correnti: **{(result.get('counts') or {}).get('new', 0)}**.\n"
    )


def _exit_code(result: dict[str, Any]) -> int:
    code = _PREV_EXIT(result)
    if code:
        return code
    coverage = ((result.get("coverageAudit") or {}).get("sportLifeCoverage") or {})
    if coverage.get("status") != "pass":
        return 8
    return 0


core.compose_runtime_payloads = compose_runtime_payloads
core.inject_verified_v04 = inject_verified_v04
core.build_coverage_audit = build_coverage_audit
core.run_v04 = run_v04
core.render_markdown = render_markdown
core._exit_code = _exit_code

_load = core._load
build_seed_item = core.build_seed_item
verify_entry = core.verify_entry
radar = core.radar
CONTRACT_V04 = core.CONTRACT_V04


if __name__ == "__main__":
    raise SystemExit(core.main())
