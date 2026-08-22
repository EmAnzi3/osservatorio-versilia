#!/usr/bin/env python3
"""Radar Opportunità Versilia v0.4.3 — residual coverage.

Estende la v0.4.2 senza allargare indiscriminatamente l'output pubblico:
- aggiunge programmi UE dedicati (URBACT, EUI, EUCF, Erasmus+, CEF, Horizon, DIGITAL, Interreg Europe);
- presidia montagna, protezione civile, MASAF e CSR/ARTEA/LEADER;
- distingue una fonte configurata da una famiglia supportata da evidenza ufficiale recente;
- promuove una call soltanto dopo verifica del ruolo comunale specifico.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v042 as prev

core = prev.core
ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_V043 = ROOT / "data" / "opportunity-discovery-v043.json"
DISCOVERY_EUCF_V043 = ROOT / "data" / "opportunity-discovery-v043-eucf.json"
EVIDENCE_V043 = ROOT / "data" / "opportunity-coverage-evidence-v043.json"
SENTINELS_V043 = ROOT / "data" / "opportunity-coverage-sentinels-v043.json"
VERIFIED_V043 = ROOT / "data" / "opportunity-verified-v043.json"

_PREV_COMPOSE = core.compose_runtime_payloads
_PREV_SOURCE_VISUAL = core._source_visual
_PREV_INJECT = core.inject_verified_v04
_PREV_AUDIT = core.build_coverage_audit
_PREV_RUN = core.run_v04
_PREV_RENDER = core.render_markdown
_PREV_EXIT = core._exit_code


def _discovery_layers() -> list[dict[str, Any]]:
    return [core._load(DISCOVERY_V043), core._load(DISCOVERY_EUCF_V043)]


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _PREV_COMPOSE()
    existing = {str(x.get("id") or "") for x in config.get("discoverySources") or []}
    registry = coverage.setdefault("sources", {})
    for extra in _discovery_layers():
        for source in extra.get("discoverySources") or []:
            source_id = str(source.get("id") or "")
            if source_id and source_id not in existing:
                config.setdefault("discoverySources", []).append(source)
                existing.add(source_id)
        for source_id, meta in (extra.get("coverageRegistry") or {}).items():
            registry[str(source_id)] = meta
    coverage["schemaVersion"] = "0.4.3"
    config["schemaVersion"] = 4
    return config, coverage


def _source_visual(source_id: str) -> dict[str, Any]:
    current = _PREV_SOURCE_VISUAL(source_id)
    meta: dict[str, Any] = {}
    for extra in _discovery_layers():
        candidate = (extra.get("coverageRegistry") or {}).get(source_id) or {}
        if candidate:
            meta = candidate
            break
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
    core.VERIFIED_V04 = VERIFIED_V043
    try:
        resolved.update(prev.prev._ORIGINAL_INJECT(
            result, today, detail_payloads=detail_payloads, live=live
        ))
    finally:
        core.VERIFIED_V04 = original_path
    return resolved


def _residual_evidence_audit(result: dict[str, Any], today: date) -> dict[str, Any]:
    cfg = core._load(EVIDENCE_V043)
    entries = list(cfg.get("entries") or [])
    max_age = int(cfg.get("maxEvidenceAgeDays") or 45)
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }
    contract = core._load(core.CONTRACT_V04)
    required_families = {str(x.get("id") or "") for x in contract.get("requiredFamilies") or []}

    missing_sources: list[str] = []
    stale_evidence: list[str] = []
    invalid_families: list[str] = []
    verified_sources: list[str] = []
    verified_families: set[str] = set()
    rows: list[dict[str, Any]] = []

    for entry in entries:
        source_id = str(entry.get("source_id") or "")
        family = str(entry.get("family") or "")
        verified_at = str(entry.get("evidence_verified_at") or "")
        age_days = None
        fresh = False
        try:
            evidence_date = date.fromisoformat(verified_at)
            age_days = (today - evidence_date).days
            fresh = 0 <= age_days <= max_age
        except ValueError:
            fresh = False

        configured_ok = source_id in configured
        family_ok = family in required_families
        evidence_ok = bool(entry.get("evidence_url")) and fresh
        if not configured_ok:
            missing_sources.append(source_id)
        if not family_ok:
            invalid_families.append(family)
        if not evidence_ok:
            stale_evidence.append(source_id)
        if configured_ok and family_ok and evidence_ok:
            verified_sources.append(source_id)
            verified_families.add(family)
        rows.append({
            "source_id": source_id,
            "family": family,
            "title": entry.get("title"),
            "evidence_url": entry.get("evidence_url"),
            "evidence_class": entry.get("evidence_class"),
            "evidence_verified_at": verified_at,
            "ageDays": age_days,
            "configured": configured_ok,
            "familyInContract": family_ok,
            "fresh": evidence_ok,
        })

    expected_families = {str(x.get("family") or "") for x in entries if x.get("family")}
    missing_families = sorted(expected_families - verified_families)
    status = "pass"
    if missing_sources or stale_evidence or invalid_families or missing_families:
        status = "fail"
    return {
        "status": status,
        "sourcesExpected": len(entries),
        "sourcesVerified": len(set(verified_sources)),
        "familiesExpected": len(expected_families),
        "familiesVerified": len(verified_families),
        "maxEvidenceAgeDays": max_age,
        "missingSources": sorted(set(missing_sources)),
        "staleEvidence": sorted(set(stale_evidence)),
        "invalidFamilies": sorted(set(invalid_families)),
        "missingFamilies": missing_families,
        "rows": rows,
        "claim": "configured_source_plus_recent_official_evidence_not_exhaustive_web_claim",
    }


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    audit = _PREV_AUDIT(result, resolved, today)
    sentinels = core._load(SENTINELS_V043).get("cases") or []
    verified = core._load(VERIFIED_V043).get("entries") or []
    verified_by_id = {str(x.get("coverage_id") or ""): x for x in verified}
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }
    missing_current = list(audit.get("missingCurrentSentinels") or [])
    historical_unmonitored = list(audit.get("historicalUnmonitored") or [])
    audit_review = list(audit.get("auditReview") or [])
    current_resolved = int(audit.get("currentSentinelsResolved") or 0)

    for case in sentinels:
        expected = str(case.get("expected") or "")
        source_id = str(case.get("source_id") or "")
        if expected == "current":
            coverage_id = str(case.get("coverage_id") or "")
            entry = verified_by_id.get(coverage_id) or {}
            if core._is_expired_application(entry, today):
                continue
            if coverage_id in resolved:
                current_resolved += 1
            else:
                missing_current.append(str(case.get("id") or coverage_id))
        elif expected == "historical_monitored":
            if source_id not in configured:
                historical_unmonitored.append(str(case.get("id") or source_id))
        elif expected == "audit_review":
            audit_review.append({
                "id": case.get("id"),
                "title": case.get("title"),
                "source_id": source_id,
                "reason": case.get("reason"),
            })

    audit["currentSentinelsResolved"] = current_resolved
    audit["missingCurrentSentinels"] = sorted(set(missing_current))
    audit["historicalUnmonitored"] = sorted(set(historical_unmonitored))
    audit["auditReview"] = audit_review
    residual = _residual_evidence_audit(result, today)
    audit["residualCoverage"] = residual
    if audit["missingCurrentSentinels"] or audit["historicalUnmonitored"] or residual.get("status") != "pass":
        audit["status"] = "fail"
    return audit


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
    result["engineVersion"] = "0.4.3"
    result["coverageVersion"] = "0.4.3"
    result["uiVersion"] = "0.4.3"
    return result


def render_markdown(result: dict[str, Any]) -> str:
    text = _PREV_RENDER(result).rstrip()
    residual = ((result.get("coverageAudit") or {}).get("residualCoverage") or {})
    return text + "\n\n## Copertura residua v0.4.3\n\n" + (
        f"Esito: **{str(residual.get('status', 'unknown')).upper()}** · fonti con evidenza ufficiale recente: "
        f"**{residual.get('sourcesVerified', 0)}/{residual.get('sourcesExpected', 0)}** · famiglie residue validate: "
        f"**{residual.get('familiesVerified', 0)}/{residual.get('familiesExpected', 0)}**.\n\n"
        "Il controllo non dichiara completezza del web: dimostra che le famiglie aggiunte non esistono soltanto nel file di configurazione ma hanno evidenza ufficiale versionata e recente.\n"
    )


def _exit_code(result: dict[str, Any]) -> int:
    code = _PREV_EXIT(result)
    if code:
        return code
    residual = ((result.get("coverageAudit") or {}).get("residualCoverage") or {})
    if residual.get("status") != "pass":
        return 7
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
VERIFIED_V042 = prev.VERIFIED_V042
SENTINELS_V042 = prev.SENTINELS_V042
INDEPENDENT_AUDIT_V042 = prev.INDEPENDENT_AUDIT_V042


if __name__ == "__main__":
    raise SystemExit(core.main())
