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
import opportunity_discovery_resilient as discovery

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_PATH = ROOT / "data" / "opportunity-independent-audit-recovery-v1.json"
APPROVED_HOSTS = {
    "www.conai.org", "conai.org",
    "anci.lombardia.it",  # ANCI già fonte nazionale nel Radar; co-promotore CONAI
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


def verification_grade_transport(url: str, diagnostics: dict[str, Any]) -> tuple[bool, str]:
    """No publisher identity is inferred from a proxied response.

    Discovery may use a reader proxy, but publication requires original-host
    direct HTTP or Chromium with a trustworthy HTTPS final URL. A redirect to
    an unrelated domain is not primary evidence, even if its text matches.
    """
    if diagnostics.get("status") != "ok":
        return False, "Acquisizione primaria non riuscita"
    if diagnostics.get("proxyUsed") is not False or diagnostics.get("transport") not in {
        "http_browser", "chromium", "direct_https"
    }:
        return False, "Trasporto reader/proxy non valido come evidenza primaria"
    origin = urlsplit(url)
    final_url = str(diagnostics.get("resolvedUrl") or "")
    resolved = urlsplit(final_url)
    expected = str(origin.hostname or "").lower().removeprefix("www.")
    actual = str(resolved.hostname or "").lower().removeprefix("www.")
    approved = {host.removeprefix("www.") for host in APPROVED_HOSTS}
    if (
        origin.scheme != "https" or resolved.scheme != "https"
        or origin.username or resolved.username
        or origin.password or resolved.password
        or origin.port not in (None, 443) or resolved.port not in (None, 443)
        or not expected or expected not in approved or actual != expected
    ):
        return False, "Redirect o host finale diverso dalla fonte ufficiale verificata"
    return True, ""


def apply(
    result: dict[str, Any],
    today: date,
    *,
    live: bool = True,
    detail_payloads: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Promuove solo evidenze correnti; su errore non pubblica e registra la lacuna."""
    if live and detail_payloads is not None:
        raise ValueError("I payload di fixture non sono utilizzabili nelle verifiche live")
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
        diagnostics: dict[str, Any] | None = None
        if raw is None and live:
            remaining = fetch_until - time.monotonic()
            if remaining > 0.5:
                try:
                    candidate, diagnostics = discovery.fetch_with_diagnostics(
                        url, timeout=min(4.0, remaining), attempts=1
                    )
                    trusted, reason = verification_grade_transport(url, diagnostics)
                    if trusted:
                        raw = candidate
                    else:
                        transport_error = reason
                except Exception as exc:
                    transport_error = str(exc)
            else:
                transport_error = "Budget breve holdout esaurito: riprova al prossimo run"
        ok, verification, error = core.verify_entry(
            entry, today, detail_payloads={url: raw} if raw is not None else None,
            live=False, fallback_max_days=0
        )
        error = transport_error or error
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
            "type": "official_primary_webpage" if live else "offline_test_fixture",
            "url": url,
            "resolved_url": str((diagnostics or {}).get("resolvedUrl") or url),
            "transport": str((diagnostics or {}).get("transport") or "test_fixture"),
            "proxy_used": False if live else None,
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
