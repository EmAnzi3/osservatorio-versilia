#!/usr/bin/env python3
"""Estensione v0.4.1 del Radar Opportunità coverage-first.

Mantiene intatto il motore v0.4 già collaudato e aggiunge i registri di copertura
trasversali emersi dal secondo audit: famiglia, pari opportunità, Casa Italia,
rete MiC generale e Funding & Tenders UE. Le nuove sentinelle passano dagli
stessi vincoli di verifica primaria, matrice comunale e lifecycle della v0.4.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v04 as base

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_EXTRA = ROOT / "data" / "opportunity-discovery-v04-extra.json"
VERIFIED_EXTRA = ROOT / "data" / "opportunity-verified-v04-extra.json"
SENTINELS_EXTRA = ROOT / "data" / "opportunity-coverage-sentinels-v04-extra.json"

_ORIGINAL_COMPOSE = base.compose_runtime_payloads
_ORIGINAL_SOURCE_VISUAL = base._source_visual
_ORIGINAL_INJECT = base.inject_verified_v04
_ORIGINAL_AUDIT = base.build_coverage_audit


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _ORIGINAL_COMPOSE()
    extra = base._load(DISCOVERY_EXTRA)
    existing = {str(x.get("id")) for x in config.get("discoverySources") or []}
    for source in extra.get("discoverySources") or []:
        source_id = str(source.get("id") or "")
        if source_id and source_id not in existing:
            config.setdefault("discoverySources", []).append(source)
            existing.add(source_id)
    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        registry[str(source_id)] = meta
    coverage["schemaVersion"] = "0.4.1"
    config["schemaVersion"] = 4
    return config, coverage


def _source_visual(source_id: str) -> dict[str, Any]:
    current = _ORIGINAL_SOURCE_VISUAL(source_id)
    meta = (base._load(DISCOVERY_EXTRA).get("coverageRegistry") or {}).get(source_id) or {}
    if meta:
        return {
            "source_label": meta.get("label") or current.get("source_label") or source_id,
            "source_favicon": meta.get("favicon") or current.get("source_favicon") or "",
        }
    return current


def inject_verified_v04(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    resolved = set(_ORIGINAL_INJECT(
        result, today, detail_payloads=detail_payloads, live=live
    ))
    original_path = base.VERIFIED_V04
    base.VERIFIED_V04 = VERIFIED_EXTRA
    try:
        resolved.update(_ORIGINAL_INJECT(
            result, today, detail_payloads=detail_payloads, live=live
        ))
    finally:
        base.VERIFIED_V04 = original_path
    return resolved


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    audit = _ORIGINAL_AUDIT(result, resolved, today)
    extra_sentinels = base._load(SENTINELS_EXTRA).get("cases") or []
    extra_verified = base._load(VERIFIED_EXTRA).get("entries") or []
    verified_by_id = {str(x.get("coverage_id")): x for x in extra_verified}
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }

    missing_current = list(audit.get("missingCurrentSentinels") or [])
    historical_unmonitored = list(audit.get("historicalUnmonitored") or [])
    current_resolved = int(audit.get("currentSentinelsResolved") or 0)

    for case in extra_sentinels:
        expected = str(case.get("expected") or "")
        if expected == "current":
            entry = verified_by_id.get(str(case.get("coverage_id") or "")) or {}
            if base._is_expired_application(entry, today):
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

    contract = base._load(base.CONTRACT_V04)
    supplier_exclusion = "supplier_tender" in set(contract.get("excludedOpportunityKinds") or [])
    audit["currentSentinelsResolved"] = current_resolved
    audit["missingCurrentSentinels"] = sorted(set(missing_current))
    audit["historicalUnmonitored"] = sorted(set(historical_unmonitored))
    audit["supplierTenderExclusionContract"] = supplier_exclusion
    if audit["missingCurrentSentinels"] or audit["historicalUnmonitored"] or not supplier_exclusion:
        audit["status"] = "fail"
    return audit


# Il main v0.4 risolve questi simboli globalmente al momento dell'esecuzione.
base.compose_runtime_payloads = compose_runtime_payloads
base._source_visual = _source_visual
base.inject_verified_v04 = inject_verified_v04
base.build_coverage_audit = build_coverage_audit

# API ri-esposta per test e tooling.
_load = base._load
build_seed_item = base.build_seed_item
verify_entry = base.verify_entry
run_v04 = base.run_v04
CONTRACT_V04 = base.CONTRACT_V04
VERIFIED_V04 = base.VERIFIED_V04
SENTINELS_V04 = base.SENTINELS_V04
DEFAULT_BACKTEST = base.radar.DEFAULT_BACKTEST
radar = base.radar


if __name__ == "__main__":
    raise SystemExit(base.main())
