#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.4.2 — independent coverage audit.

Estende la v0.4.1 con un controllo non autoreferenziale della copertura:
- nuove famiglie istituzionali emerse da uno sweep esterno;
- fonti holdout che NON alimentano il collector di produzione;
- falsi negativi noti versionati e chiusura misurabile dei gap;
- capture rate prospettico, pubblicabile solo dopo un campione minimo;
- detection lag separato dal recall del classificatore.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

import run_opportunity_radar_v041 as prev

core = prev.base
ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_V042 = ROOT / "data" / "opportunity-discovery-v042.json"
VERIFIED_V042 = ROOT / "data" / "opportunity-verified-v042.json"
SENTINELS_V042 = ROOT / "data" / "opportunity-coverage-sentinels-v042.json"
INDEPENDENT_AUDIT_V042 = ROOT / "data" / "opportunity-independent-audit-v042.json"

_PREV_COMPOSE = core.compose_runtime_payloads
_PREV_SOURCE_VISUAL = core._source_visual
_PREV_INJECT = core.inject_verified_v04
_PREV_AUDIT = core.build_coverage_audit
_PREV_RUN = core.run_v04
_PREV_RENDER = core.render_markdown
_PREV_EXIT = core._exit_code


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _PREV_COMPOSE()
    extra = core._load(DISCOVERY_V042)
    existing = {str(x.get("id")) for x in config.get("discoverySources") or []}
    for source in extra.get("discoverySources") or []:
        source_id = str(source.get("id") or "")
        if source_id and source_id not in existing:
            config.setdefault("discoverySources", []).append(source)
            existing.add(source_id)
    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        registry[str(source_id)] = meta
    coverage["schemaVersion"] = "0.4.2"
    config["schemaVersion"] = 4
    return config, coverage


def _source_visual(source_id: str) -> dict[str, Any]:
    current = _PREV_SOURCE_VISUAL(source_id)
    meta = (core._load(DISCOVERY_V042).get("coverageRegistry") or {}).get(source_id) or {}
    if not meta:
        return current
    return {
        "source_label": meta.get("label") or current.get("source_label") or source_id,
        "source_favicon": meta.get("favicon") or current.get("source_favicon") or "",
    }


def inject_verified_v04(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    resolved = set(_PREV_INJECT(result, today, detail_payloads=detail_payloads, live=live))
    original_path = core.VERIFIED_V04
    core.VERIFIED_V04 = VERIFIED_V042
    try:
        resolved.update(prev._ORIGINAL_INJECT(
            result, today, detail_payloads=detail_payloads, live=live
        ))
    finally:
        core.VERIFIED_V04 = original_path
    return resolved


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    audit = _PREV_AUDIT(result, resolved, today)
    sentinels = core._load(SENTINELS_V042).get("cases") or []
    verified = core._load(VERIFIED_V042).get("entries") or []
    verified_by_id = {str(x.get("coverage_id")): x for x in verified}
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }
    missing_current = list(audit.get("missingCurrentSentinels") or [])
    historical_unmonitored = list(audit.get("historicalUnmonitored") or [])
    current_resolved = int(audit.get("currentSentinelsResolved") or 0)
    audit_review = []

    for case in sentinels:
        expected = str(case.get("expected") or "")
        if expected == "current":
            entry = verified_by_id.get(str(case.get("coverage_id") or "")) or {}
            if core._is_expired_application(entry, today):
                continue
            coverage_id = str(case.get("coverage_id") or "")
            if coverage_id in resolved:
                current_resolved += 1
            else:
                missing_current.append(str(case.get("id") or coverage_id))
        elif expected == "historical_monitored":
            source_id = str(case.get("source_id") or "")
            if source_id not in configured:
                historical_unmonitored.append(str(case.get("id") or source_id))
        elif expected == "audit_review":
            audit_review.append({
                "id": case.get("id"),
                "title": case.get("title"),
                "source_id": case.get("source_id"),
                "reason": case.get("reason"),
            })

    audit["currentSentinelsResolved"] = current_resolved
    audit["missingCurrentSentinels"] = sorted(set(missing_current))
    audit["historicalUnmonitored"] = sorted(set(historical_unmonitored))
    audit["auditReview"] = audit_review
    if audit["missingCurrentSentinels"] or audit["historicalUnmonitored"]:
        audit["status"] = "fail"
    return audit


def _probe_holdouts(live: bool) -> list[dict[str, Any]]:
    cfg = core._load(INDEPENDENT_AUDIT_V042)
    sources = list(cfg.get("holdoutSources") or [])
    if not live:
        return [
            {"id": x.get("id"), "label": x.get("label"), "status": "not_run", "feedsProduction": False}
            for x in sources
        ]

    def probe(source: dict[str, Any]) -> dict[str, Any]:
        try:
            payload = core.radar.v025.v022.fetch_resilient(
                str(source.get("url") or ""), timeout=10, attempts=1
            )
            ok = bool(str(payload or "").strip())
            return {
                "id": source.get("id"), "label": source.get("label"),
                "status": "ok" if ok else "error", "feedsProduction": False,
                "error": None if ok else "risposta vuota",
            }
        except Exception as exc:  # pragma: no cover - rete live
            return {
                "id": source.get("id"), "label": source.get("label"),
                "status": "error", "feedsProduction": False, "error": str(exc),
            }

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(3, len(sources))), thread_name_prefix="radar-holdout") as pool:
        pending = {pool.submit(probe, source): source for source in sources}
        for future in as_completed(pending):
            rows.append(future.result())
    return sorted(rows, key=lambda x: str(x.get("id") or ""))


def build_independent_audit(result: dict[str, Any], *, live: bool) -> dict[str, Any]:
    cfg = core._load(INDEPENDENT_AUDIT_V042)
    cases = list(cfg.get("cases") or [])
    active_ids = {
        str(item.get("coverage_id") or "")
        for item in list(result.get("opportunities") or []) + list(result.get("archive") or [])
        if item.get("coverage_id")
    }
    current = [x for x in cases if x.get("expected") == "current"]
    baseline_total = len(current)
    baseline_captured = sum(str(x.get("baselineRadarStatus")) != "missed" for x in current)
    closed = [x for x in current if str(x.get("coverage_id") or "") in active_ids]
    missing = [str(x.get("id") or x.get("coverage_id")) for x in current if x not in closed]

    lags = []
    for case in current:
        try:
            start = date.fromisoformat(str(case.get("published_at") or ""))
            found = date.fromisoformat(str(case.get("audit_found_at") or ""))
        except ValueError:
            continue
        lags.append((found - start).days)

    prospective = [x for x in cases if x.get("expected") == "prospective_current"]
    prospective_captured = sum(str(x.get("coverage_id") or "") in active_ids for x in prospective)
    min_sample = int(cfg.get("minimumProspectiveSample") or 20)
    prospective_rate = (prospective_captured / len(prospective)) if prospective else None
    prospective_status = "measurable" if len(prospective) >= min_sample else "pending_minimum_sample"
    holdouts = _probe_holdouts(live)
    holdout_healthy = sum(row.get("status") == "ok" for row in holdouts)

    status = "pass"
    if missing:
        status = "fail"
    if live and holdouts and holdout_healthy == 0:
        status = "fail"

    return {
        "status": status,
        "claim": "independent_audit_established_not_exhaustive_web_claim",
        "baselineDate": cfg.get("baselineDate"),
        "baselineRepresentative": bool(cfg.get("baselineIsRepresentative")),
        "baselinePreFix": {
            "auditedCurrent": baseline_total,
            "capturedByRadar": baseline_captured,
            "missedByRadar": baseline_total - baseline_captured,
            "captureRate": (baseline_captured / baseline_total) if baseline_total else None,
            "note": "Campione mirato ai buchi: non è un KPI rappresentativo.",
        },
        "knownGapClosure": {
            "total": baseline_total,
            "closed": len(closed),
            "missing": missing,
            "closureRate": (len(closed) / baseline_total) if baseline_total else None,
        },
        "targetedDetectionLagDays": {
            "sampleSize": len(lags),
            "median": median(lags) if lags else None,
            "note": "Misura retrospettiva dei falsi negativi scoperti il 22/08/2026; non è il KPI prospettico.",
        },
        "prospective": {
            "sampleSize": len(prospective),
            "captured": prospective_captured,
            "captureRate": prospective_rate,
            "status": prospective_status,
            "minimumSample": min_sample,
            "targetCaptureRate": cfg.get("targetCaptureRate"),
            "targetMedianDetectionLagDays": cfg.get("targetMedianDetectionLagDays"),
        },
        "holdouts": {
            "configured": len(holdouts),
            "healthy": holdout_healthy,
            "feedsProduction": False,
            "rows": holdouts,
        },
        "auditReview": [
            {"id": x.get("id"), "title": x.get("title"), "reason": x.get("reason")}
            for x in cases if x.get("expected") == "audit_review"
        ],
    }


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
    result["independentAudit"] = build_independent_audit(result, live=payloads is None)
    result["engineVersion"] = "0.4.2"
    result["coverageVersion"] = "0.4.2"
    result["uiVersion"] = "0.4.2"
    return result


def render_markdown(result: dict[str, Any]) -> str:
    text = _PREV_RENDER(result).rstrip()
    audit = result.get("independentAudit") or {}
    gap = audit.get("knownGapClosure") or {}
    prospective = audit.get("prospective") or {}
    holdouts = audit.get("holdouts") or {}
    rate = prospective.get("captureRate")
    rate_label = "non ancora misurabile" if rate is None else f"{float(rate):.1%}"
    return text + "\n\n## Audit indipendente v0.4.2\n\n" + (
        f"Esito: **{str(audit.get('status', 'unknown')).upper()}** · buchi noti chiusi: "
        f"**{gap.get('closed', 0)}/{gap.get('total', 0)}** · holdout sani: "
        f"**{holdouts.get('healthy', 0)}/{holdouts.get('configured', 0)}**.\n\n"
        f"Capture rate prospettico: **{rate_label}** "
        f"(campione {prospective.get('sampleSize', 0)}/{prospective.get('minimumSample', 0)}).\n"
        "Il campione baseline è stato costruito cercando falsi negativi e non viene usato per dichiarare una copertura percentuale del web.\n"
    )


def _exit_code(result: dict[str, Any]) -> int:
    code = _PREV_EXIT(result)
    if code:
        return code
    if (result.get("independentAudit") or {}).get("status") != "pass":
        return 6
    return 0


core.compose_runtime_payloads = compose_runtime_payloads
core._source_visual = _source_visual
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
VERIFIED_V04 = core.VERIFIED_V04
SENTINELS_V04 = core.SENTINELS_V04
VERIFIED_EXTRA = prev.VERIFIED_EXTRA
SENTINELS_EXTRA = prev.SENTINELS_EXTRA


if __name__ == "__main__":
    raise SystemExit(core.main())
