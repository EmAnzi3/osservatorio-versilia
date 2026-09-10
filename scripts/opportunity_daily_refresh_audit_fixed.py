#!/usr/bin/env python3
"""Overlay giornaliero sui gap emersi dall'audit indipendente.

Estende h5 senza modificare il classificatore storico né la versione del gate
trasporto:
- mantiene i fix puntuali C4T/CERV/Toscana già verificati;
- promuove nel Radar pubblico il replay completo della matrice municipale finale,
  limitandosi a opportunità correnti, rolling o upcoming realmente azionabili;
- scarta storici, captured, scope-review ed esclusioni;
- classifica ogni scheda pubblica per rilevanza comunale e separa il conteggio
  principale dalle opportunità di partnership/consorzio;
- persiste una diagnostica completa prima di qualsiasi blocco publishability,
  inclusi coverageHold, regionalCompleteness, famiglie runtime e backtest.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import opportunity_matrix_promotions as audit_promotions
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
_BASE_RUN_V04 = radar_module.run_v04
_BASE_PREPARE_STABLE = stable._prepare_public_stable
_BASE_RENDER_REPORT = h4.daily._render_report
_BASE_PUBLISH_ASSERT = h4._ORIGINAL_ASSERT
_BASE_STABLE_DIAGNOSTIC = stable._write_publishability_diagnostic


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


def _run_v04_with_audit_promotions(today: date, **kwargs: Any) -> dict[str, Any]:
    """Porta il replay deterministico dentro l'output prima del gate continuità.

    Se lo snapshot precedente contiene già le schede della matrice, il motore live
    non deve interpretarle come scomparse solo perché vengono aggiunte dall'overlay
    audit dopo il collector. Rendendole presenti prima della riconciliazione finale
    il gate continua a bloccare soltanto vere sparizioni.
    """
    result = _BASE_RUN_V04(today, **kwargs)
    audit_promotions.apply_complete_promotions(result, today)
    if hasattr(core, "_recompute_v04_counts"):
        core._recompute_v04_counts(result)
    relevance.apply_to_payload(result, drop_review=True)
    return result


def _diagnostic_gate_summary(result: dict[str, Any]) -> dict[str, Any]:
    backtest = result.get("backtest") or {}
    audit = result.get("coverageAudit") or {}
    regional = result.get("regionalCompleteness") or {}
    return {
        "continuityHoldCount": len(result.get("continuityHold") or []),
        "coverageHoldCount": len(result.get("coverageHold") or []),
        "backtestPassed": bool(backtest.get("passed", False)),
        "coverageAuditStatus": audit.get("status"),
        "regionalCompletenessStatus": regional.get("status"),
        "runtimeUncoveredFamilyCount": len(audit.get("runtimeUncoveredFamilies") or []),
        "opportunityCount": len(result.get("opportunities") or []),
    }


def _write_full_publishability_diagnostic(
    result: dict[str, Any],
    uncovered: list[str],
    *,
    error: BaseException | str | None = None,
    runtime_evaluation: dict[str, Any] | None = None,
) -> None:
    """Scrive lo stato sufficiente a spiegare ogni blocco del publishability gate."""
    try:
        transport = stable._build_transport_audit_stable(result)
    except Exception as transport_error:  # diagnostica best-effort, mai mascherare il gate reale
        transport = {
            "schemaVersion": "diagnostic-error",
            "error": f"{type(transport_error).__name__}: {transport_error}",
        }

    payload = {
        "schemaVersion": "1.2",
        "referenceDate": stable._today_for_result(result).isoformat(),
        "error": str(error) if error is not None else None,
        "gateSummary": _diagnostic_gate_summary(result),
        "runtimeUncoveredFamilies": list(uncovered),
        "runtimeCoverageEvaluation": runtime_evaluation or {"evaluated": True, "error": None},
        "continuityHold": list(result.get("continuityHold") or []),
        "coverageHold": list(result.get("coverageHold") or []),
        "regionalCompleteness": dict(result.get("regionalCompleteness") or {}),
        "coverageAudit": dict(result.get("coverageAudit") or {}),
        "sourceCoverage": dict(result.get("sourceCoverage") or {}),
        "backtest": dict(result.get("backtest") or {}),
        "transportAudit": transport,
    }
    path = stable.PUBLISHABILITY_DIAGNOSTIC_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "PUBLISHABILITY DIAGNOSTIC: "
        f"{path} · continuityHold={payload['gateSummary']['continuityHoldCount']} · "
        f"coverageHold={payload['gateSummary']['coverageHoldCount']} · "
        f"regionalCompleteness={payload['gateSummary']['regionalCompletenessStatus']} · "
        f"runtimeUncoveredFamilies={len(payload['runtimeUncoveredFamilies'])}"
    )


def _evaluate_runtime_coverage_for_diagnostic(
    result: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    """Valuta h5 anche se un gate base ha già fallito, senza scrivere due artifact."""
    original_writer = stable._write_publishability_diagnostic
    try:
        stable._write_publishability_diagnostic = lambda _result, _uncovered: None
        uncovered = list(stable._runtime_uncovered_families_stable(result))
        result.setdefault("coverageAudit", {})["runtimeUncoveredFamilies"] = uncovered
        return uncovered, {"evaluated": True, "error": None}
    except Exception as exc:  # diagnostica best-effort, non mascherare il gate originario
        existing = list((result.get("coverageAudit") or {}).get("runtimeUncoveredFamilies") or [])
        return existing, {
            "evaluated": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        stable._write_publishability_diagnostic = original_writer


def _assert_base_with_full_diagnostic(result: dict[str, Any]) -> None:
    """Intercetta i gate base che altrimenti terminano prima della diagnostica h5."""
    try:
        _BASE_PUBLISH_ASSERT(result)
    except Exception as exc:
        uncovered, runtime_evaluation = _evaluate_runtime_coverage_for_diagnostic(result)
        _write_full_publishability_diagnostic(
            result,
            uncovered,
            error=exc,
            runtime_evaluation=runtime_evaluation,
        )
        raise


def _prepare_public_audit_fixed(result: dict[str, Any], today: date) -> dict[str, Any]:
    result = _BASE_PREPARE_STABLE(result, today)
    if result.get("auditCorpusPromotionVersion") != audit_promotions.PROMOTION_VERSION:
        audit_promotions.apply_complete_promotions(result, today)
    # Il replay aggiunge schede dopo il normale classificatore h5: riallineiamo
    # prima i contatori legacy e poi il contratto comunale/partnership.
    if hasattr(core, "_recompute_v04_counts"):
        core._recompute_v04_counts(result)
    relevance.apply_to_payload(result, drop_review=True)
    result["dailyHardeningVersion"] = DAILY_HARDENING_VERSION
    result["auditGapFixVersion"] = FIX_VERSION
    result["auditCorpusPromotionVersion"] = audit_promotions.PROMOTION_VERSION
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
    original_h4_assert = h4._ORIGINAL_ASSERT
    original_stable_diagnostic = stable._write_publishability_diagnostic
    original_core_compose = core.compose_runtime_payloads
    original_core_inject = core.inject_verified_v04
    original_radar_inject = getattr(radar_module, "inject_verified_v04", None)
    original_radar_run = radar_module.run_v04
    original_prepare = stable._prepare_public_stable
    original_report = h4.daily._render_report

    h4._ORIGINAL_COMPOSE = _compose_with_audit_fixes
    h4._ORIGINAL_ASSERT = _assert_base_with_full_diagnostic
    stable._write_publishability_diagnostic = _write_full_publishability_diagnostic
    core.inject_verified_v04 = _inject_with_audit_fixes
    if _BASE_RADAR_INJECT is not None:
        radar_module.inject_verified_v04 = _inject_with_audit_fixes
    radar_module.run_v04 = _run_v04_with_audit_promotions
    stable._prepare_public_stable = _prepare_public_audit_fixed
    h4.daily._render_report = _render_report_relevance
    try:
        return stable.main()
    finally:
        h4._ORIGINAL_COMPOSE = original_h4_compose
        h4._ORIGINAL_ASSERT = original_h4_assert
        stable._write_publishability_diagnostic = original_stable_diagnostic
        core.compose_runtime_payloads = original_core_compose
        core.inject_verified_v04 = original_core_inject
        if original_radar_inject is not None:
            radar_module.inject_verified_v04 = original_radar_inject
        radar_module.run_v04 = original_radar_run
        stable._prepare_public_stable = original_prepare
        h4.daily._render_report = original_report


if __name__ == "__main__":
    raise SystemExit(main())
