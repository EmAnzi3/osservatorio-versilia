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
- lo snapshot conserva lastSuccessfulFetch, consecutiveFailures ed effectiveStatus;
- se il gate blocca una famiglia obbligatoria, persiste una diagnostica completa
  prima dell'eccezione, così il run fallito resta investigabile;
- un falso negativo del listing può essere recuperato soltanto riconfermando
  live la pagina di dettaglio canonica con trasporto diretto/Chromium, identità,
  stato aperto e scadenza coerenti.

La grace riguarda soltanto la copertura del discovery. Non promuove bandi, non
sostituisce la verifica primaria e non modifica i criteri di ammissibilità.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import opportunity_daily_refresh_resilient as h4


SOURCE_HEALTH_GRACE_DAYS = 2
SOURCE_HEALTH_MAX_CONSECUTIVE_FAILURES = 2
CONTINUITY_DETAIL_HTTP_TIMEOUT_SECONDS = 8
CONTINUITY_DETAIL_BROWSER_TIMEOUT_MS = 15_000
CONTINUITY_DETAIL_MAX_ATTEMPTS = 3
PUBLISHABILITY_DIAGNOSTIC_PATH = Path("reports/runtime/opportunity-publishability-diagnostic.json")
SOURCE_HEALTH_SEED_ENV = "OPPORTUNITY_SOURCE_HEALTH_SEED"
_PREVIOUS_HEALTH: dict[str, dict[str, Any]] = {}
_RUN_DATE: date | None = None

_BASE_BUILD_AUDIT = h4._build_transport_audit
_BASE_PREPARE = h4._prepare_public_hardened
_BASE_RUNTIME_UNCOVERED = h4._runtime_uncovered_families
_BASE_RESTORE_CONTINUITY = h4.daily._restore_recent_verified_continuity

_CONTINUITY_OPEN_MARKERS = (
    "stato aperto",
    "status open",
    "application open",
    "applications open",
    "call open",
    "open call",
    "presenta domanda",
    "presentare domanda",
    "aperte le candidature",
    "apertura dei termini",
    "apply now",
    "submit application",
)
_CONTINUITY_CLOSED_MARKERS = (
    "stato chiuso",
    "status closed",
    "application closed",
    "applications closed",
    "call closed",
    "bando chiuso",
    "avviso chiuso",
    "procedura chiusa",
    "procedura sospesa",
    "bando revocato",
    "avviso revocato",
    "revoked",
    "cancelled",
)
_IT_MONTHS = (
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
)
_EN_MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


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


def _seed_health_with_failed_run(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Overlay the latest failed-run health on the accepted snapshot.

    Failed runs cannot update the public snapshot.  Without this separate seed,
    their consecutive failure counter would restart forever from the last green
    run, silently turning a two-run grace into an unlimited grace.
    """
    seeded = _seed_previous_health(snapshot)
    raw = str(os.environ.get(SOURCE_HEALTH_SEED_ENV) or "").strip()
    if not raw:
        return seeded
    failed = _load_previous_snapshot(Path(raw))
    if not failed:
        return seeded
    accepted_date = _safe_date(snapshot.get("referenceDate"))
    failed_date = _safe_date(failed.get("referenceDate"))
    if accepted_date and failed_date and failed_date < accepted_date:
        return seeded
    seeded.update(_seed_previous_health(failed))
    return seeded


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


def _write_publishability_diagnostic(result: dict[str, Any], uncovered: list[str]) -> None:
    """Persiste la salute endpoint prima che il gate interrompa il refresh."""
    payload = {
        "schemaVersion": "1.0",
        "referenceDate": _today_for_result(result).isoformat(),
        "runtimeUncoveredFamilies": list(uncovered),
        "coverageAudit": dict(result.get("coverageAudit") or {}),
        "transportAudit": _build_transport_audit_stable(result),
    }
    PUBLISHABILITY_DIAGNOSTIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLISHABILITY_DIAGNOSTIC_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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

    uncovered = sorted(uncovered)
    if uncovered:
        _write_publishability_diagnostic(result, uncovered)
    return uncovered


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


def _rule_id_from_hold(hold: dict[str, Any]) -> str:
    identity = str(hold.get("identity_key") or "")
    if identity.startswith("rule:"):
        return identity[5:]
    return str(hold.get("rule_id") or "")


def _normalized_url(value: Any) -> str:
    return h4.radar_module.v025.normalized_url(str(value or ""))


def _same_host(first: str, second: str) -> bool:
    def host(value: str) -> str:
        raw = str(urlsplit(value).hostname or "").casefold()
        return raw[4:] if raw.startswith("www.") else raw

    return bool(host(first)) and host(first) == host(second)


def _deadline_markers(value: Any) -> set[str]:
    deadline = _safe_date(value)
    if deadline is None:
        return set()
    day = deadline.day
    month = deadline.month
    year = deadline.year
    raw = {
        deadline.isoformat(),
        f"{day:02d}/{month:02d}/{year}",
        f"{day}/{month}/{year}",
        f"{day:02d}-{month:02d}-{year}",
        f"{day}-{month}-{year}",
        f"{day} {_IT_MONTHS[month - 1]} {year}",
        f"{day} {_EN_MONTHS[month - 1]} {year}",
        f"{_EN_MONTHS[month - 1]} {day} {year}",
    }
    return {h4.radar_module.v025.fold(item) for item in raw}


def _fetch_continuity_detail(url: str) -> tuple[str | None, dict[str, Any]]:
    """Fetch verification-grade: HTTP diretto, poi Chromium; mai reader proxy."""
    discovery = h4.discovery
    errors: list[str] = []
    try:
        payload, resolved_url = discovery._fetch_browser_html_with_url(
            url,
            timeout=CONTINUITY_DETAIL_HTTP_TIMEOUT_SECONDS,
            attempts=1,
        )
        diagnostics = {
            "status": "ok",
            "transport": "http_browser",
            "fallbackUsed": False,
            "proxyUsed": False,
            "initialFailureClass": None,
            "browserFailureClass": None,
            "failureClass": None,
            "resolvedUrl": resolved_url,
            "redirected": resolved_url != url,
            "errors": [],
        }
        discovery._record_trace(url, diagnostics)
        return payload, diagnostics
    except Exception as http_error:  # pragma: no cover - rete live
        failure_class = discovery.classify_fetch_error(http_error)
        errors.append(f"HTTP [{failure_class}]: {http_error}")

    if not discovery._browser_fallback_allowed(failure_class):
        diagnostics = {
            "status": "error",
            "transport": "failed",
            "fallbackUsed": False,
            "proxyUsed": False,
            "initialFailureClass": failure_class,
            "browserFailureClass": None,
            "failureClass": failure_class,
            "resolvedUrl": None,
            "redirected": False,
            "errors": errors,
        }
        discovery._record_trace(url, diagnostics)
        return None, diagnostics

    try:
        payload, resolved_url = discovery._fetch_playwright_html(
            url,
            timeout_ms=CONTINUITY_DETAIL_BROWSER_TIMEOUT_MS,
        )
        diagnostics = {
            "status": "ok",
            "transport": "chromium",
            "fallbackUsed": True,
            "proxyUsed": False,
            "initialFailureClass": failure_class,
            "browserFailureClass": None,
            "failureClass": None,
            "resolvedUrl": resolved_url,
            "redirected": resolved_url != url,
            "errors": errors,
        }
        discovery._record_trace(url, diagnostics)
        return payload, diagnostics
    except Exception as browser_error:  # pragma: no cover - rete live
        browser_class = discovery.classify_fetch_error(browser_error)
        errors.append(f"Chromium [{browser_class}]: {browser_error}")
        diagnostics = {
            "status": "error",
            "transport": "failed",
            "fallbackUsed": True,
            "proxyUsed": False,
            "initialFailureClass": failure_class,
            "browserFailureClass": browser_class,
            "failureClass": browser_class,
            "resolvedUrl": None,
            "redirected": False,
            "errors": errors,
        }
        discovery._record_trace(url, diagnostics)
        return None, diagnostics


def _detail_evidence_valid(
    rule: dict[str, Any],
    previous_item: dict[str, Any],
    payload: str | None,
    diagnostics: dict[str, Any],
    today: date,
    requested_url: str,
) -> bool:
    if not payload or diagnostics.get("status") != "ok":
        return False
    if diagnostics.get("proxyUsed") or diagnostics.get("transport") not in {"http_browser", "chromium"}:
        return False
    resolved_url = str(diagnostics.get("resolvedUrl") or requested_url)
    if not _same_host(requested_url, resolved_url):
        return False

    title = str(previous_item.get("title") or "").strip()
    if len(title) < 7:
        return False
    pattern = str(rule.get("title_pattern") or "")
    if pattern:
        try:
            if re.search(pattern, title, flags=re.I) is None:
                return False
        except re.error:
            return False

    text = h4.radar_module.base.visible(payload)
    folded = h4.radar_module.v025.fold(text)
    if h4.radar_module.v025.fold(title) not in folded:
        return False

    if any(h4.radar_module.v025.fold(marker) in folded for marker in _CONTINUITY_CLOSED_MARKERS):
        return False
    if not any(h4.radar_module.v025.fold(marker) in folded for marker in _CONTINUITY_OPEN_MARKERS):
        return False

    deadline_text = str(previous_item.get("deadline_at") or rule.get("deadline_override") or "")
    if deadline_text:
        deadline = _safe_date(deadline_text)
        if deadline is None or deadline < today:
            return False
        markers = _deadline_markers(deadline_text)
        if not markers or not any(marker in folded for marker in markers):
            return False

    gate = previous_item.get("quality_gate") or {}
    if gate and gate.get("status") != "pass":
        return False
    if str(previous_item.get("lifecycle_stage") or "application_open") not in {"application_open", "rolling_open"}:
        return False
    if rule.get("actionable") is False:
        return False
    return True


def _revalidate_unresolved_continuity_details(
    result: dict[str, Any],
    previous: dict[str, Any],
    today: date,
) -> list[dict[str, Any]]:
    """Recupera falsi negativi del listing solo tramite dettaglio canonico live."""
    holds = list(result.get("continuityHold") or [])
    if not holds:
        return []

    rules, _, _ = h4.radar_module.load_rules()
    rules_by_id = {str(rule.get("id") or ""): rule for rule in rules if rule.get("id")}
    previous_items = list(previous.get("opportunities") or [])
    by_rule = {
        str(item.get("rule_id") or ""): item
        for item in previous_items
        if item.get("rule_id")
    }
    by_url = {
        _normalized_url(item.get("url")): item
        for item in previous_items
        if item.get("url")
    }
    runtime_by_source = {
        str(row.get("source_id") or ""): str(row.get("runtimeStatus") or "not_run")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }

    restored: list[dict[str, Any]] = []
    attempts = 0
    for hold in holds:
        if attempts >= CONTINUITY_DETAIL_MAX_ATTEMPTS:
            break
        if hold.get("kind") not in {None, "", "existing_opportunity"}:
            continue

        rule_id = _rule_id_from_hold(hold)
        rule = rules_by_id.get(rule_id)
        if not rule:
            continue

        hold_url = _normalized_url(hold.get("url"))
        old = by_rule.get(rule_id) if rule_id else None
        if old is None and hold_url:
            old = by_url.get(hold_url)
        if old is None:
            continue

        source_id = str(old.get("source_id") or "")
        rule_source_id = str(rule.get("source_id") or "")
        if not source_id or (rule_source_id and rule_source_id != source_id):
            continue
        if runtime_by_source.get(source_id) not in {"ok", "degraded"}:
            continue

        evidence_url = str(rule.get("evidence_url") or old.get("url") or "").strip()
        if not evidence_url.startswith(("http://", "https://")):
            continue
        if evidence_url.casefold().split("?", 1)[0].endswith(".pdf"):
            continue

        attempts += 1
        payload, diagnostics = _fetch_continuity_detail(evidence_url)
        if not _detail_evidence_valid(rule, old, payload, diagnostics, today, evidence_url):
            continue

        item = json.loads(json.dumps(old, ensure_ascii=False))
        item["verified_direct"] = True
        item["verified_at"] = today.isoformat()
        item["verification_status"] = "live_detail_revalidated"
        item.pop("continuity_fallback", None)
        item["continuity_revalidation"] = {
            "restored_at": today.isoformat(),
            "rule_id": rule_id,
            "url": evidence_url,
            "transport": diagnostics.get("transport"),
            "reason": "Listing corrente incompleto; pagina di dettaglio canonica riconfermata live prima della scadenza.",
        }
        result.setdefault("opportunities", []).append(item)
        restored.append(item)

    if not restored:
        return []

    h4.daily._reconcile_final_continuity(result)
    h4.daily._recompute_after_continuity_restore(result)
    result.setdefault("counts", {})["continuityLiveDetailRevalidated"] = len(restored)
    print(f"CONTINUITY LIVE DETAIL: {len(restored)} opportunità riconfermate dalla pagina canonica")
    for item in restored:
        evidence = item.get("continuity_revalidation") or {}
        print(
            f"  {item.get('title')} · fonte {item.get('source_id')} · "
            f"trasporto {evidence.get('transport')} · verifica {item.get('verified_at')}"
        )
    return restored


def _restore_continuity_stable(
    result: dict[str, Any],
    previous: dict[str, Any],
    today: date,
    *,
    max_age_days: int = h4.daily.CONTINUITY_VERIFIED_GRACE_DAYS,
) -> list[dict[str, Any]]:
    """Preferisce una riconferma live; usa la cache recente solo se resta un hold."""
    live = _revalidate_unresolved_continuity_details(result, previous, today)
    cached = _BASE_RESTORE_CONTINUITY(
        result,
        previous,
        today,
        max_age_days=max_age_days,
    )
    return live + cached


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
    _PREVIOUS_HEALTH = _seed_health_with_failed_run(previous)

    original_runtime = h4._runtime_uncovered_families
    original_build = h4._build_transport_audit
    original_prepare = h4._prepare_public_hardened
    original_restore = h4.daily._restore_recent_verified_continuity
    h4._runtime_uncovered_families = _runtime_uncovered_families_stable
    h4._build_transport_audit = _build_transport_audit_stable
    h4._prepare_public_hardened = _prepare_public_stable
    h4.daily._restore_recent_verified_continuity = _restore_continuity_stable
    try:
        return h4.main()
    finally:
        h4._runtime_uncovered_families = original_runtime
        h4._build_transport_audit = original_build
        h4._prepare_public_hardened = original_prepare
        h4.daily._restore_recent_verified_continuity = original_restore


if __name__ == "__main__":
    from opportunity_daily_refresh_audit_fixed import main as audit_fixed_main

    raise SystemExit(audit_fixed_main())
