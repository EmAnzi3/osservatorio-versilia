#!/usr/bin/env python3
"""Modello canonico dello stato di aggiornamento degli indicatori.

Il modulo non modifica i valori pubblicati. Combina il periodo pubblicato in
site-data, la politica della fonte e l'ultimo stato del monitor per produrre una
vista per indicatore. L'assenza di evidenza sul periodo più recente non viene
mai trasformata in una falsa conferma di attualità.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any
import urllib.parse

from source_policy import resolve_metric_policy

STATUS_META = {
    "current": {
        "label": "Ultimo dato disponibile",
        "publicLabel": "Ultimo dato disponibile",
        "severity": "ok",
        "description": "Il periodo pubblicato coincide con l'ultimo periodo verificato presso la fonte.",
    },
    "new_release_to_review": {
        "label": "Nuovo rilascio da verificare",
        "publicLabel": "Nuovo rilascio da verificare",
        "severity": "attention",
        "description": "La fonte segnala un periodo più recente, non ancora validato e pubblicato dall'Osservatorio.",
    },
    "release_expected": {
        "label": "Aggiornamento atteso",
        "publicLabel": "Aggiornamento atteso",
        "severity": "attention",
        "description": "È stata raggiunta una finestra di rilascio documentata, ma non è ancora confermato un nuovo dato.",
    },
    "source_unavailable": {
        "label": "Fonte temporaneamente non verificabile",
        "publicLabel": "Fonte temporaneamente non verificabile",
        "severity": "warning",
        "description": "Il controllo più recente non è riuscito a verificare la fonte. Il dato pubblicato non viene modificato.",
    },
    "verification_required": {
        "label": "Verifica necessaria",
        "publicLabel": "Verifica necessaria",
        "severity": "neutral",
        "description": "Non c'è ancora evidenza sufficiente per certificare automaticamente che il periodo pubblicato sia l'ultimo disponibile.",
    },
}

VALID_NEXT_RELEASE_BASES = {"official_calendar", "documented_schedule"}
PARTIAL_PERIOD_TOKENS = ("ytd", "parziale", "partial", "in corso")


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(str(value or "").strip())
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(
        sorted(
            (key, item)
            for key, item in query_pairs
            if key.lower() not in {"v", "cache", "cachebust", "timestamp", "_"}
        )
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", query, "")
    )


def parse_period_rank(value: Any) -> tuple[int, ...] | None:
    """Confronta periodi semplici senza pretendere di interpretare ogni formato."""
    text = str(value or "").strip().lower()
    if not text or any(token in text for token in PARTIAL_PERIOD_TOKENS):
        return None
    if text.isdigit() and len(text) == 4:
        return (int(text),)
    normalized = text.replace("–", "-").replace("/", "-")
    parts = [part.strip() for part in normalized.split("-") if part.strip()]
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        first = int(parts[0])
        second = int(parts[1])
        if len(parts[1]) == 2:
            second = (first // 100) * 100 + second
        return (first, second)
    tokens = text.replace("-", " ").replace("/", " ").split()
    if tokens and tokens[0].isdigit() and len(tokens[0]) == 4:
        suffix = 0
        if len(tokens) > 1:
            marker = tokens[1].upper()
            if marker.startswith(("S", "Q")) and marker[1:].isdigit():
                suffix = int(marker[1:])
        return (int(tokens[0]), suffix)
    return None


def exact_next_release(policy: dict[str, Any]) -> dict[str, Any] | None:
    candidate = policy.get("nextExpectedRelease")
    if not isinstance(candidate, dict):
        return None
    value = str(candidate.get("value") or "").strip()
    basis = str(candidate.get("basis") or "").strip()
    precision = str(candidate.get("precision") or "").strip()
    if not value or basis not in VALID_NEXT_RELEASE_BASES:
        return None
    result = {"value": value, "basis": basis}
    if precision:
        result["precision"] = precision
    evidence = str(candidate.get("evidenceUrl") or "").strip()
    if evidence:
        result["evidenceUrl"] = evidence
    verified_at = str(candidate.get("verifiedAt") or "").strip()
    if verified_at:
        result["verifiedAt"] = verified_at
    return result


def _probe_for_metric(metric: dict[str, Any], monitor_state: dict[str, Any]) -> dict[str, Any] | None:
    sources = monitor_state.get("sources")
    if not isinstance(sources, dict):
        return None
    raw = str(metric.get("sourceUrl") or "")
    if raw in sources and isinstance(sources[raw], dict):
        return sources[raw]
    canonical = canonical_url(raw)
    if canonical in sources and isinstance(sources[canonical], dict):
        return sources[canonical]
    return None


def _previous_metric_state(metric_key: str, monitor_state: dict[str, Any]) -> dict[str, Any]:
    metrics = monitor_state.get("metrics")
    if isinstance(metrics, dict) and isinstance(metrics.get(metric_key), dict):
        return metrics[metric_key]
    return {}


def _source_changed(metric_key: str, report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
        return False
    sources = report.get("sources")
    changes = report.get("changes")
    if not isinstance(sources, dict) or not isinstance(changes, dict):
        return False
    changed_urls = {
        str(item.get("url") or "")
        for key in ("added", "removed", "content", "redirect")
        for item in (changes.get(key) or [])
        if isinstance(item, dict)
    }
    for url in changed_urls:
        item = sources.get(url)
        if isinstance(item, dict) and metric_key in (item.get("metrics") or []):
            return True
    return False


def metric_status(
    metric_key: str,
    metric: dict[str, Any],
    registry: dict[str, Any],
    monitor_state: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = resolve_metric_policy(metric_key, metric, registry)
    previous = _previous_metric_state(metric_key, monitor_state)
    probe = _probe_for_metric(metric, monitor_state)
    published_period = str(metric.get("meta", {}).get("year") or "").strip()
    observed_period = previous.get("observedLatestPeriod")
    if observed_period is not None:
        observed_period = str(observed_period).strip() or None

    is_climate = metric.get("dataStorage", {}).get("type") == "external-climate"
    if is_climate and observed_period and any(
        token in observed_period.lower() for token in PARTIAL_PERIOD_TOKENS
    ):
        observed_period = None

    source_status = "not_checked"
    checked_at = None
    if probe is not None:
        checked_at = str(monitor_state.get("checkedAt") or "") or None
        source_status = "reachable" if probe.get("ok") else "unavailable"

    changed = _source_changed(metric_key, report)
    published_rank = parse_period_rank(published_period)
    observed_rank = parse_period_rank(observed_period)

    if source_status == "unavailable":
        status = "source_unavailable"
        reason = "source_unavailable"
    elif changed:
        status = "verification_required"
        reason = "source_change_detected"
    elif observed_period and published_rank and observed_rank:
        if observed_rank == published_rank:
            status = "current"
            reason = "verified_same_period"
        elif observed_rank > published_rank:
            status = "new_release_to_review"
            reason = "newer_period_observed"
        else:
            status = "verification_required"
            reason = "observed_period_precedes_published"
    elif observed_period == published_period and observed_period:
        status = "current"
        reason = "verified_same_period"
    else:
        status = "verification_required"
        reason = "latest_period_not_observed"

    next_release = exact_next_release(policy)
    return {
        "metricKey": metric_key,
        "theme": metric.get("meta", {}).get("theme"),
        "label": metric.get("meta", {}).get("label"),
        "publishedPeriod": published_period,
        "observedLatestPeriod": observed_period,
        "checkedAt": checked_at,
        "checkMode": str(monitor_state.get("mode") or "") or None,
        "sourceStatus": source_status,
        "status": status,
        "statusLabel": STATUS_META[status]["publicLabel"],
        "statusDescription": STATUS_META[status]["description"],
        "statusSeverity": STATUS_META[status]["severity"],
        "statusReason": reason,
        "publisher": policy.get("publisher") or metric.get("meta", {}).get("source"),
        "sourceUrl": metric.get("sourceUrl"),
        "frequency": policy.get("frequency"),
        "frequencyLabel": policy.get("frequencyLabel") or "Secondo la fonte",
        "releaseCadenceLabel": policy.get("expectedRelease") or "Non determinabile",
        "nextExpectedRelease": next_release,
        "monitorMode": policy.get("monitorMode") or "availability",
        "climateCompleteYearsOnly": bool(is_climate),
    }


def build_metric_statuses(
    data: dict[str, Any],
    registry: dict[str, Any],
    monitor_state: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return {}
    return {
        key: metric_status(key, metric, registry, monitor_state, report)
        for key, metric in metrics.items()
        if isinstance(metric, dict)
    }


def summarize_metric_statuses(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(item.get("status") or "verification_required") for item in metrics.values())
    checked = sum(1 for item in metrics.values() if item.get("checkedAt"))
    return {
        "metricCount": len(metrics),
        "checkedMetricCount": checked,
        "statusCounts": {key: counts.get(key, 0) for key in STATUS_META},
    }


def build_public_payload(
    data: dict[str, Any],
    registry: dict[str, Any],
    monitor_state: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = build_metric_statuses(data, registry, monitor_state, report)
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "lastGeneralCheckAt": monitor_state.get("checkedAt"),
        "monitorMode": monitor_state.get("mode"),
        "summary": summarize_metric_statuses(metrics),
        "statuses": STATUS_META,
        "metrics": metrics,
    }


def upgrade_monitor_state(
    data: dict[str, Any],
    registry: dict[str, Any],
    monitor_state: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    upgraded = dict(monitor_state)
    upgraded["schemaVersion"] = 2
    upgraded["metrics"] = build_metric_statuses(data, registry, monitor_state, report)
    return upgraded


def markdown_status_addendum(metrics: dict[str, dict[str, Any]]) -> str:
    summary = summarize_metric_statuses(metrics)
    counts = summary["statusCounts"]
    return "\n".join(
        [
            "### Stato degli indicatori",
            "",
            "Il monitor distingue il periodo pubblicato dalla verifica della fonte. "
            "In assenza di evidenza sul periodo più recente non presume che il dato sia aggiornato.",
            "",
            "| Stato | Indicatori |",
            "|---|---:|",
            f"| Ultimo dato disponibile | {counts['current']} |",
            f"| Nuovo rilascio da verificare | {counts['new_release_to_review']} |",
            f"| Aggiornamento atteso | {counts['release_expected']} |",
            f"| Fonte temporaneamente non verificabile | {counts['source_unavailable']} |",
            f"| Verifica necessaria | {counts['verification_required']} |",
            "",
            f"Indicatori con controllo fonte registrato: **{summary['checkedMetricCount']}/{summary['metricCount']}**.",
            "",
        ]
    )
