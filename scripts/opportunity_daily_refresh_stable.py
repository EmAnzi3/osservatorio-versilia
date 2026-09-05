#!/usr/bin/env python3
"""Refresh giornaliero h5: salute fonti persistente e gate anti-flaky.

La raggiungibilità di un portale istituzionale da un singolo runner GitHub non è
sinonimo di disponibilità della fonte. Questo wrapper mantiene intatto il
collector h4 e aggiunge una memoria di salute per fonte:

- un successo corrente azzera i fallimenti consecutivi;
- un timeout/403 isolato usa l'ultimo successo recente o una breve finestra di
  fallimenti consecutivi come grace tecnica;
- una famiglia obbligatoria blocca il publish solo dopo una perdita persistente
  di copertura, non per un singolo runner o durante la migrazione pre-h5;
- lo snapshot conserva lastSuccessfulFetch, consecutiveFailures ed effectiveStatus.

La grace riguarda soltanto la copertura del discovery. Non promuove bandi, non
sostituisce la verifica primaria e non modifica i criteri di ammissibilità.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import opportunity_daily_refresh_resilient as h4


SOURCE_HEALTH_GRACE_DAYS = 2
SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES = 2
_PREVIOUS_HEALTH: dict[str, dict[str, Any]] = {}
_RUN_DATE: date | None = None

_BASE_BUILD_AUDIT = h4._build_transport_audit
_BASE_PREPARE = h4._prepare_public_hardened
_BASE_RUNTIME_UNCOVERED = h4._runtime_uncovered_families


def _arg_value(name: str) -> str | None:
    prefix = name + "="
    for index, value in enumerate(sys.argv[1:]):
        if value.startswith(prefix):
            return value[len(prefix):]
        if value == name:
            absolute = index + 1
            if absolute + 1 < len(sys.argv):
                return sys.argv[absolute + 1]
    return None


def _daily_path_from_argv() -> Path:
    raw = _arg_value("--daily")
    return Path(raw) if raw else h4.daily.DEFAULT_DAILY


def _run_date_from_argv() -> date:
    raw = _arg_value("--date")
    return date.fromisoformat(raw) if raw else date.today()


def _safe_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or ""))
    except ValueError:
        return None


def _load_previous_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _seed_previous_health(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Ricostruisce la memoria anche dagli snapshot pre-h5.

    Per uno snapshot legacy che conosce soltanto ``runtimeStatus=error`` non
    fingiamo un successo passato: inizializziamo un singolo fallimento noto. Il
    primo run h5 può così osservare il secondo fallimento senza bloccare subito;
    dal terzo fallimento consecutivo la sorgente esce dalla grace.
    """
    reference = str(snapshot.get("referenceDate") or "")
    seeded: dict[str, dict[str, Any]] = {}

    for row in (snapshot.get("transportAudit") or {}).get("sources") or []:
        source_id = str(row.get("sourceId") or "")
        if not source_id:
            continue
        last_success = str(row.get("lastSuccessfulFetch") or "") or None
        runtime = str(row.get("runtimeStatus") or "unknown")
        if not last_success and runtime in {"ok", "degraded"} and reference:
            last_success = reference
        persisted_failures = row.get("consecutiveFailures")
        if persisted_failures is None:
            persisted_failures = 0 if runtime in {"ok", "degraded"} else 1
        seeded[source_id] = {
            "lastSuccessfulFetch": last_success,
            "consecutiveFailures": int(persisted_failures or 0),
            "effectiveStatus": row.get("effectiveStatus") or runtime,
        }

    for row in (snapshot.get("sourceCoverage") or {}).get("rows") or []:
        source_id = str(row.get("source_id") or "")
        if not source_id or source_id in seeded:
            continue
        runtime = str(row.get("runtimeStatus") or "unknown")
        seeded[source_id] = {
            "lastSuccessfulFetch": reference if runtime in {"ok", "degraded"} and reference else None,
            "consecutiveFailures": 0 if runtime in {"ok", "degraded"} else 1,
            "effectiveStatus": runtime,
        }
    return seeded


def _health_state(source_id: str, current_status: str, today: date) -> dict[str, Any]:
    previous = _PREVIOUS_HEALTH.get(source_id) or {}
    current_ok = current_status in {"ok", "degraded"}
    if current_ok:
        return {
            "lastSuccessfulFetch": today.isoformat(),
            "consecutiveFailures": 0,
            "effectiveStatus": current_status,
            "graceUsed": False,
            "graceReason": None,
            "lastSuccessAgeDays": 0,
        }

    last_success_text = str(previous.get("lastSuccessfulFetch") or "")
    last_success = _safe_date(last_success_text)
    age_days = (today - last_success).days if last_success else None
    failures = int(previous.get("consecutiveFailures") or 0) + 1
    recent_success = age_days is not None and 0 <= age_days <= SOURCE_HEALTH_GRACE_DAYS
    failure_window = failures <= SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES
    in_grace = recent_success or failure_window
    grace_reason = "recent_success" if recent_success else "consecutive_failure_window" if failure_window else None
    return {
        "lastSuccessfulFetch": last_success_text or None,
        "consecutiveFailures": failures,
        "effectiveStatus": "grace" if in_grace else "error",
        "graceUsed": in_grace,
        "graceReason": grace_reason,
        "lastSuccessAgeDays": age_days,
    }


def _today_for_result(result: dict[str, Any]) -> date:
    if _RUN_DATE is not None:
        return _RUN_DATE
    return _safe_date(result.get("referenceDate")) or date.today()


def _runtime_uncovered_families_stable(result: dict[str, Any]) -> list[str]:
    contract = h4.core._load(h4.core.CONTRACT_V04)
    rows = list((result.get("sourceCoverage") or {}).get("rows") or [])
    by_id = {str(row.get("source_id") or ""): row for row in rows}
    today = _today_for_result(result)
    uncovered: list[str] = []
    grace_families: list[dict[str, Any]] = []

    for family in contract.get("requiredFamilies") or []:
        family_id = str(family.get("id") or "")
        source_ids = [str(value) for value in family.get("sourceIds") or []]
        current_states = {
            source_id: str((by_id.get(source_id) or {}).get("runtimeStatus") or "not_run")
            for source_id in source_ids
        }
        if any(state in {"ok", "degraded"} for state in current_states.values()):
            continue

        grace_sources: list[dict[str, Any]] = []
        for source_id, current_status in current_states.items():
            state = _health_state(source_id, current_status, today)
            if state["effectiveStatus"] == "grace":
                grace_sources.append({
                    "sourceId": source_id,
                    "consecutiveFailures": state["consecutiveFailures"],
                    "lastSuccessfulFetch": state["lastSuccessfulFetch"],
                    "graceReason": state["graceReason"],
                })

        if grace_sources:
            grace_families.append({
                "familyId": family_id,
                "sources": grace_sources,
                "graceDays": SOURCE_HEALTH_GRACE_DAYS,
                "maxConsecutiveFailures": SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES,
            })
        elif family_id:
            uncovered.append(family_id)

    audit = result.setdefault("coverageAudit", {})
    audit["runtimeGraceFamilies"] = grace_families
    audit["sourceHealthGraceDays"] = SOURCE_HEALTH_GRACE_DAYS
    audit["sourceHealthMaxConsecutiveFailures"] = SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES
    return sorted(uncovered)


def _build_transport_audit_stable(result: dict[str, Any]) -> dict[str, Any]:
    audit = _BASE_BUILD_AUDIT(result)
    today = _today_for_result(result)
    in_grace = 0
    unhealthy = 0

    for row in audit.get("sources") or []:
        source_id = str(row.get("sourceId") or "")
        runtime = str(row.get("runtimeStatus") or "unknown")
        state = _health_state(source_id, runtime, today)
        row.update(state)
        if state["effectiveStatus"] == "grace":
            in_grace += 1
        elif state["effectiveStatus"] == "error":
            unhealthy += 1

    summary = audit.setdefault("summary", {})
    summary["sourcesInGrace"] = in_grace
    summary["unhealthySources"] = unhealthy
    summary["sourceHealthGraceDays"] = SOURCE_HEALTH_GRACE_DAYS
    summary["sourceHealthMaxConsecutiveFailures"] = SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES
    audit["schemaVersion"] = "1.2"
    return audit


def _prepare_public_stable(result: dict[str, Any], today: date) -> dict[str, Any]:
    result = _BASE_PREPARE(result, today)
    result["dailyHardeningVersion"] = "0.4.4-h5"
    result["sourceHealthGraceDays"] = SOURCE_HEALTH_GRACE_DAYS
    result["sourceHealthMaxConsecutiveFailures"] = SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES
    return result


def main() -> int:
    global _PREVIOUS_HEALTH, _RUN_DATE
    _RUN_DATE = _run_date_from_argv()
    previous = _load_previous_snapshot(_daily_path_from_argv())
    _PREVIOUS_HEALTH = _seed_previous_health(previous)

    original_runtime = h4._runtime_uncovered_families
    original_build = h4._build_transport_audit
    original_prepare = h4._prepare_public_hardened
    h4._runtime_uncovered_families = _runtime_uncovered_families_stable
    h4._build_transport_audit = _build_transport_audit_stable
    h4._prepare_public_hardened = _prepare_public_stable
    try:
        return h4.main()
    finally:
        h4._runtime_uncovered_families = original_runtime
        h4._build_transport_audit = original_build
        h4._prepare_public_hardened = original_prepare


if __name__ == "__main__":
    raise SystemExit(main())
