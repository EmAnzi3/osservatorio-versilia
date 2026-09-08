#!/usr/bin/env python3
"""Overlay giornaliero sui gap emersi dall'audit indipendente.

Estende h5 senza modificare il classificatore storico né la versione del gate
trasporto:
- aggiunge il presidio C4T GROUNDWORK come canale UE dedicato;
- inietta la call 2026 solo dopo verifica primaria, con ammissibilità comunale
  condizionata al ruolo effettivo nell'attuazione di investimenti PO2;
- conserva CERV Town Twinning nel circuito già protetto dalle sentinelle v0.4.2;
- usa la riconciliazione cross-source del safety net Regione Toscana per evitare
  che Mercati rionali resti unresolved quando la stessa misura è già pubblica
  da Sviluppo Toscana;
- classifica ogni scheda pubblica per rilevanza comunale e separa il conteggio
  principale dalle opportunità di sola partnership/consorzio.

L'overlay è deliberatamente separato dai dataset storici v0.4.x: rende il fix
reversibile e testabile senza riscrivere le baseline congelate.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import opportunity_daily_refresh_stable as stable
import opportunity_municipal_relevance as relevance


ROOT = Path(__file__).resolve().parents[1]
FIXES_PATH = ROOT / "data" / "opportunity-audit-fixes-v1.json"
FIX_VERSION = "2026-09-07"
DAILY_HARDENING_VERSION = "0.4.4-h5"

h4 = stable.h4
core = h4.core
radar_module = h4.daily.radar

_BASE_COMPOSE = h4._ORIGINAL_COMPOSE
_BASE_INJECT = core.inject_verified_v04
_BASE_RADAR_INJECT = getattr(radar_module, "inject_verified_v04", None)
_BASE_PREPARE_STABLE = stable._prepare_public_stable
_BASE_RENDER_REPORT = h4.daily._render_report


def _load_fixes() -> dict[str, Any]:
    payload = core._load(FIXES_PATH)
    if str(payload.get("fixVersion") or "") != FIX_VERSION:
        raise RuntimeError("Versione overlay audit inattesa")
    return payload


def _compose_with_audit_fixes() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _BASE_COMPOSE()
    extra = _load_fixes()

    configured = {
        str(source.get("id") or "")
        for source in config.get("discoverySources") or []
        if source.get("id")
    }
    for source in extra.get("discoverySources") or []:
        source_id = str(source.get("id") or "")
        if not source_id:
            raise RuntimeError("Fonte audit fix senza id")
        if source_id not in configured:
            config.setdefault("discoverySources", []).append(dict(source))
            configured.add(source_id)

    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        current = dict(registry.get(str(source_id)) or {})
        current.update(dict(meta or {}))
        registry[str(source_id)] = current
    return config, coverage


def _inject_fix_entries(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    payload = _load_fixes()
    max_days = int(payload.get("evidenceFallbackMaxDays") or 7)
    resolved: set[str] = set()
    existing_coverage = {
        str(item.get("coverage_id") or "")
        for item in result.get("opportunities") or []
        if item.get("coverage_id")
    }
    existing_urls = {
        core.radar.v025.normalized_url(str(item.get("url") or ""))
        for item in result.get("opportunities") or []
    }

    for entry in payload.get("verifiedEntries") or []:
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
        item["first_seen_at"] = str(entry.get("first_seen_at") or today.isoformat())
        resolved.add(coverage_id)
        if core._is_expired_application(entry, today):
            core._append_archive(result, item)
            continue

        norm_url = core.radar.v025.normalized_url(str(item.get("url") or ""))
        if coverage_id in existing_coverage or (norm_url and norm_url in existing_urls):
            for current in result.get("opportunities") or []:
                current_norm = core.radar.v025.normalized_url(str(current.get("url") or ""))
                if str(current.get("coverage_id") or "") == coverage_id or (norm_url and current_norm == norm_url):
                    current.setdefault("coverage_id", coverage_id)
                    current.setdefault("first_seen_at", item["first_seen_at"])
                    if entry.get("municipal_relevance_class"):
                        current["municipal_relevance_class"] = entry["municipal_relevance_class"]
                    break
            continue

        result.setdefault("opportunities", []).append(item)
        existing_coverage.add(coverage_id)
        if norm_url:
            existing_urls.add(norm_url)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    result.setdefault("opportunities", []).sort(
        key=lambda item: (
            order.get(str(item.get("lifecycle_stage") or "application_open"), 9),
            str(item.get("deadline_at") or "9999-99-99"),
            str(item.get("title") or ""),
        )
    )
    return resolved


def _inject_with_audit_fixes(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    resolved = set(_BASE_INJECT(result, today, detail_payloads=detail_payloads, live=live))
    resolved.update(
        _inject_fix_entries(
            result,
            today,
            detail_payloads=detail_payloads,
            live=live,
        )
    )
    return resolved


def _prepare_public_audit_fixed(result: dict[str, Any], today: date) -> dict[str, Any]:
    result = _BASE_PREPARE_STABLE(result, today)
    relevance.apply_to_payload(result, drop_review=True)
    result["dailyHardeningVersion"] = DAILY_HARDENING_VERSION
    result["auditGapFixVersion"] = FIX_VERSION
    result["municipalRelevanceVersion"] = relevance.SCHEMA_VERSION
    return result


def _render_report_relevance(result: dict[str, Any], new_items: list[dict[str, Any]]) -> str:
    text = _BASE_RENDER_REPORT(result, new_items)
    counts = result.get("counts") or {}
    public = int(counts.get("public") or len(result.get("opportunities") or []))
    headline = int(counts.get("municipalHeadlineCurrentOrRolling") or 0)
    upcoming = int(counts.get("municipalHeadlineUpcoming") or 0)
    partners = int(counts.get("partnershipCurrentOrRolling") or 0)
    partner_upcoming = int(counts.get("partnershipUpcoming") or 0)
    old = f"Opportunità correnti: **{public}** · evidenziate come nuove: **{counts.get('new', 0)}**."
    new = (
        f"Opportunità comunali correnti/a sportello: **{headline}** · in arrivo: **{upcoming}** · "
        f"partnership correnti/a sportello: **{partners}** · partnership in arrivo: **{partner_upcoming}** · "
        f"evidenziate come nuove: **{counts.get('new', 0)}**."
    )
    return text.replace(old, new, 1)


def main() -> int:
    original_h4_compose = h4._ORIGINAL_COMPOSE
    original_core_compose = core.compose_runtime_payloads
    original_core_inject = core.inject_verified_v04
    original_radar_inject = getattr(radar_module, "inject_verified_v04", None)
    original_prepare = stable._prepare_public_stable
    original_report = h4.daily._render_report

    h4._ORIGINAL_COMPOSE = _compose_with_audit_fixes
    core.inject_verified_v04 = _inject_with_audit_fixes
    if _BASE_RADAR_INJECT is not None:
        radar_module.inject_verified_v04 = _inject_with_audit_fixes
    stable._prepare_public_stable = _prepare_public_audit_fixed
    h4.daily._render_report = _render_report_relevance
    try:
        return stable.main()
    finally:
        h4._ORIGINAL_COMPOSE = original_h4_compose
        core.compose_runtime_payloads = original_core_compose
        core.inject_verified_v04 = original_core_inject
        if original_radar_inject is not None:
            radar_module.inject_verified_v04 = original_radar_inject
        stable._prepare_public_stable = original_prepare
        h4.daily._render_report = original_report


if __name__ == "__main__":
    raise SystemExit(main())
