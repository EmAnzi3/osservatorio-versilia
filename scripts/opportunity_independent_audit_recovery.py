#!/usr/bin/env python3
"""Recupero delle omissioni indipendenti, senza falsificare verifiche o bloccare il Radar.

Le fonti holdout restano distinte dal discovery produttivo. Solo una pagina
ufficiale verificata live con TUTTI i termini documentali richiesti promuove
una scheda; il mancato recupero non costituisce coverageHold per una scheda
mai pubblicata. Il risultato negativo è tracciato come auditRecovery.pending.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlsplit

import run_opportunity_radar_v04 as core

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_PATH = ROOT / "data" / "opportunity-independent-audit-recovery-v1.json"
APPROVED_HOSTS = {
    "www.conai.org", "conai.org",
    "centroperillibro.cultura.gov.it",
    "www.fondazionecarilucca.it", "fondazionecarilucca.it",
    "ec.europa.eu",
}


def _entries() -> list[dict[str, Any]]:
    payload = json.loads(RECOVERY_PATH.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != "1.0" or not isinstance(payload.get("entries"), list):
        raise RuntimeError("Audit Recovery: schema non valido")
    seen: set[str] = set()
    for item in payload["entries"]:
        coverage = str(item.get("coverage_id") or "")
        host = urlsplit(str(item.get("url") or "")).hostname
        if (not coverage or coverage in seen or host not in APPROVED_HOSTS
                or not item.get("required_terms") or not item.get("deadline_at")
                or item.get("review_policy") != "opportunistic"
                or item.get("allow_recent_evidence_fallback") is not False
                or len(item.get("municipality_status_overrides") or {}) != len(core.TOWNS)):
            raise RuntimeError(f"Audit Recovery: voce priva di evidenza primaria sufficiente: {coverage}")
        seen.add(coverage)
    return list(payload["entries"])


def apply(
    result: dict[str, Any],
    today: date,
    *,
    live: bool = True,
    detail_payloads: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Promuove solo evidenze correnti; su errore non pubblica e registra la lacuna."""
    current = list(result.get("opportunities") or [])
    ids = {str(x.get("coverage_id") or "") for x in current if x.get("coverage_id")}
    normalized = core.radar.v025.normalized_url
    urls = {normalized(str(x.get("url") or "")) for x in current}
    verified = []
    already = []
    pending = []
    expired = []
    # Non usare i retry generici da 30 s x 2 dell'engine: holdout non critici
    # non devono consumare l'intero budget del refresh produttivo.
    fetch_until = time.monotonic() + 18.0
    for entry in _entries():
        key = str(entry["coverage_id"])
        url = str(entry["url"])
        if key in ids or normalized(url) in urls:
            already.append(key)
            continue
        if date.fromisoformat(str(entry["deadline_at"])) < today:
            expired.append(key)
            continue

        raw = (detail_payloads or {}).get(url)
        transport_error = None
        if raw is None and live:
            remaining = fetch_until - time.monotonic()
            if remaining > 0.5:
                try:
                    raw = core.radar.v025.v022.fetch_resilient(
                        url, timeout=min(4.0, remaining), attempts=1
                    )
                except Exception as exc:
                    transport_error = str(exc)
            else:
                transport_error = "Budget breve holdout esaurito: riprova al prossimo run"
        ok, verification, error = core.verify_entry(
            entry, today, detail_payloads={url: raw} if raw is not None else None,
            live=False, fallback_max_days=0
        )
        error = error or transport_error
        if not ok or verification != "live":
            pending.append({
                "coverage_id": key,
                "title": entry["title"],
                "url": url,
                "deadline_at": entry["deadline_at"],
                "reason": error or "Pagina ufficiale non verificata nel run corrente",
                "stage": "primary_evidence_pending",
            })
            continue

        item = core.build_seed_item(entry, today, "live_official_primary")
        item["source_verification"] = {
            "type": "official_primary_webpage",
            "url": url,
            "verified_at": today.isoformat(),
            "required_terms": list(entry.get("required_terms") or []),
        }
        item["first_seen_at"] = today.isoformat()
        if entry.get("municipal_relevance_class") == "partner":
            item["applicant_eligibility"] = "not_direct_applicant"
            item["territorial_relevance"] = "indirect"
        item["municipal_relevance_class"] = str(entry["municipal_relevance_class"])
        result.setdefault("opportunities", []).append(item)
        ids.add(key)
        urls.add(normalized(url))
        verified.append(key)

    result["auditRecovery"] = {
        "schemaVersion": "1.0",
        "source": "independent-holdout-2026-10-28",
        "checked": len(verified) + len(already) + len(pending) + len(expired),
        "promoted": verified,
        "alreadyRepresented": already,
        "pending": pending,
        "expired": expired,
        "blocksPublication": False,
    }
    return result
