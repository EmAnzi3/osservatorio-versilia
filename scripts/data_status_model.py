#!/usr/bin/env python3
"""Modello derivato dello stato pubblico dei dati dell'Osservatorio.

Le autorità restano tre:
- site-data.json: periodo e valori pubblicati;
- source-registry.json: politica della fonte;
- source-monitor-state.json: esito dei controlli realmente eseguiti.

Questo modulo non inventa annualità né date di rilascio.
"""
from __future__ import annotations

import urllib.parse
import re
import hashlib
import json
from datetime import date
from typing import Any

from source_policy import resolve_metric_policy

STATUS_META = {
    "current": {
        "label": "Ultimo dato disponibile",
        "tone": "ok",
        "description": "Il periodo pubblicato coincide con l'ultimo periodo verificato sulla fonte.",
    },
    "source_checked": {
        "label": "Fonte controllata",
        "tone": "neutral",
        "description": "La fonte è stata raggiunta, ma il monitor non può stabilire automaticamente se il periodo pubblicato è l'ultimo disponibile.",
    },
    "source_access_limited": {
        "label": "Controllo automatico limitato",
        "tone": "neutral",
        "description": "Il portale ufficiale limita l'accesso automatizzato. La fonte resta soggetta a verifica manuale e il dato pubblicato non viene modificato.",
    },
    "release_detected": {
        "label": "Nuovo rilascio da verificare",
        "tone": "warn",
        "description": "È stata rilevata una fotografia ufficiale più recente o diversa rispetto ai valori pubblicati. Serve validazione prima di aggiornare il sito.",
    },
    "update_expected": {
        "label": "Aggiornamento atteso",
        "tone": "warn",
        "description": "È arrivata una finestra di rilascio documentata, ma non è ancora stato confermato un nuovo dato.",
    },
    "source_unavailable": {
        "label": "Fonte temporaneamente non verificabile",
        "tone": "problem",
        "description": "Il controllo automatico non è riuscito ad accedere alla fonte. Il dato pubblicato non viene modificato.",
    },
    "verification_required": {
        "label": "Verifica necessaria",
        "tone": "problem",
        "description": "La situazione richiede una verifica umana prima di poter dichiarare l'attualità del dato.",
    },
}

ALLOWED_RELEASE_BASES = {
    "official_calendar",
    "official_schedule",
    "documented_release_window",
    "verified_pattern",
}


def catalog_digest(data: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(str(value or "").strip())
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(
        sorted(
            (key, item)
            for key, item in pairs
            if key.lower() not in {"v", "cache", "cachebust", "timestamp", "_"}
        )
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", query, "")
    )


def published_period(metric: dict[str, Any]) -> str:
    storage = metric.get("dataStorage")
    if isinstance(storage, dict) and storage.get("type") == "external-climate":
        trend_to = storage.get("trendTo")
        if trend_to not in (None, ""):
            return str(trend_to)
    return str(metric.get("meta", {}).get("year") or "")


def probe_for(metric: dict[str, Any], state: dict[str, Any]) -> dict[str, Any] | None:
    sources = state.get("sources")
    if not isinstance(sources, dict):
        return None
    raw = str(metric.get("sourceUrl") or "")
    if raw in sources and isinstance(sources[raw], dict):
        return sources[raw]
    wanted = canonical_url(raw)
    for url, item in sources.items():
        if isinstance(item, dict) and canonical_url(str(url)) == wanted:
            return item
    return None


def safe_next_release(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    release = {key: value.get(key) for key in ("value", "precision", "basis", "evidenceUrl", "verifiedAt")}
    if not release.get("value") or release.get("basis") not in ALLOWED_RELEASE_BASES:
        return None
    return release


def period_key(value: str) -> tuple[int, ...] | None:
    text = str(value or "").strip().casefold()
    if re.fullmatch(r"\d{4}", text):
        return (int(text),)
    if re.fullmatch(r"\d{4}-\d{2}", text):
        year, month = map(int, text.split("-"))
        if 1 <= month <= 12:
            return (year, month)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        try:
            parsed = date.fromisoformat(text)
            return (parsed.year, parsed.month, parsed.day)
        except ValueError:
            return None
    months = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
    match = re.fullmatch(r"(?:(\d{1,2})\s+)?([a-z]+)\s+(\d{4})", text)
    if match and match[2] in months:
        year, month = int(match[3]), months.index(match[2]) + 1
        if match[1] is None:
            return (year, month)
        try:
            parsed = date(year, month, int(match[1]))
            return (parsed.year, parsed.month, parsed.day)
        except ValueError:
            return None
    return None


def compare_periods(published: str, observed: str) -> int | None:
    """Confronta solo periodi con la stessa precisione, senza inferire date."""
    if published and published == observed:
        return 0
    left, right = period_key(published), period_key(observed)
    if left is None or right is None or len(left) != len(right):
        return None
    return (right > left) - (right < left)


def derive_status(
    published: str,
    probe: dict[str, Any] | None,
    operational: dict[str, Any],
) -> str:
    explicit = str(operational.get("status") or "")
    if explicit in {
        "release_detected", "update_expected", "verification_required",
        "source_access_limited",
    }:
        return explicit
    # Un portale primario può limitare i bot, ma un secondo feed ufficiale
    # machine-readable può certificare lo stesso perimetro. `current` viene
    # rispettato solo in presenza dell'evidenza strutturata, mai come flag libero.
    if (
        explicit == "current"
        and isinstance(operational.get("verificationEvidence"), dict)
        and operational.get("observedLatestPeriod") == published
    ):
        return "current"
    if probe is None:
        return "verification_required"
    if probe.get("automationLimited"):
        return "source_access_limited"
    if not probe.get("ok"):
        return "source_unavailable"
    if probe.get("releaseVerification") in {"not_performed", "catalogue_only"}:
        return "source_checked"
    observed = str(operational.get("observedLatestPeriod") or "")
    if observed:
        comparison = compare_periods(published, observed)
        if comparison == 0:
            return "current"
        if comparison == 1:
            return "release_detected"
        return "verification_required"
    return "source_checked"


def build_public_status(
    data: dict[str, Any],
    registry: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
    themes = data.get("themes") if isinstance(data.get("themes"), dict) else {}
    operational_metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
    checked_at = str(state.get("checkedAt") or "")
    rows: list[dict[str, Any]] = []

    for metric_key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        policy = resolve_metric_policy(metric_key, metric, registry)
        probe = probe_for(metric, state)
        operational = operational_metrics.get(metric_key)
        operational = operational if isinstance(operational, dict) else {}
        period = published_period(metric)
        status = derive_status(period, probe, operational)
        status_meta = STATUS_META[status]
        theme_key = str(meta.get("theme") or "")
        theme = themes.get(theme_key) if isinstance(themes.get(theme_key), dict) else {}
        next_release = safe_next_release(
            operational.get("nextExpectedRelease") or policy.get("nextExpectedRelease")
        )
        # La data generale descrive l'esecuzione del monitor, non prova che il
        # singolo indicatore sia stato controllato. Per evitare date retroattive
        # sui nuovi indicatori usiamo soltanto lo stato operativo per metrica.
        row_checked_at = str(operational.get("checkedAt") or "")
        direct_reachable = None
        if probe is not None:
            if probe.get("directReachable") is False:
                direct_reachable = False
            else:
                direct_reachable = bool(probe.get("ok"))
        verification = operational.get("verificationEvidence")
        verification = verification if isinstance(verification, dict) else None
        storage = metric.get("dataStorage")
        is_external_climate = (
            isinstance(storage, dict) and storage.get("type") == "external-climate"
        )
        rows.append(
            {
                "key": metric_key,
                "label": str(meta.get("label") or metric_key),
                "theme": theme_key,
                "themeLabel": str(theme.get("label") or theme_key),
                "publishedPeriod": period,
                "source": str(meta.get("source") or policy.get("publisher") or ""),
                "sourceUrl": str(metric.get("sourceUrl") or ""),
                "frequency": str(policy.get("frequency") or ""),
                "frequencyLabel": str(policy.get("frequencyLabel") or "Secondo la fonte"),
                "cadenceNote": str(policy.get("expectedRelease") or ""),
                "lastChecked": row_checked_at,
                "lastPeriodVerified": str(operational.get("periodVerifiedAt") or ""),
                "observedLatestPeriod": str(operational.get("observedLatestPeriod") or ""),
                "nextExpectedRelease": next_release,
                "status": status,
                "statusLabel": status_meta["label"],
                "statusTone": status_meta["tone"],
                "statusDescription": status_meta["description"],
                "sourceReachable": direct_reachable,
                "sourceAutomationLimited": False if probe is None else bool(probe.get("automationLimited")),
                "sourceProbeMethod": "" if probe is None else str(probe.get("probeMethod") or ""),
                "sourceError": "" if probe is None else str(probe.get("error") or ""),
                "verificationSource": verification,
                "isExternalClimate": is_external_climate,
            }
        )

    rows.sort(key=lambda row: (row["themeLabel"].casefold(), row["label"].casefold()))
    counts = {key: 0 for key in STATUS_META}
    for row in rows:
        counts[row["status"]] += 1

    return {
        "schemaVersion": 1,
        "generatedFrom": {
            "siteDataVersion": data.get("version"),
            "sourceRegistrySchema": registry.get("schemaVersion"),
            "sourceMonitorSchema": state.get("schemaVersion"),
        },
        "lastGeneralCheck": checked_at,
        "lastDeepCheck": str(state.get("lastDeepCheck") or (checked_at if state.get("depth") == "deep" else "")),
        "metricCount": len(rows),
        "counts": counts,
        "metrics": rows,
    }
