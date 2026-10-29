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
    "anci.lombardia.it",  # co-promotore ANCI–CONAI
    "www.anciliguria.it",  # pagina primaria ufficiale alternativa ANCI
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
        alternates = item.get("alternate_primary_pages") or []
        if not isinstance(alternates, list) or len(alternates) > 2:
            raise RuntimeError(f"Audit Recovery: alternative primarie invalide: {coverage}")
        candidates = {str(item.get("url") or "")}
        for alternate in alternates:
            candidate_url = str(alternate.get("url") or "")
            parts = urlsplit(candidate_url)
            terms = alternate.get("required_terms")
            if (parts.scheme != "https" or parts.hostname not in APPROVED_HOSTS
                    or candidate_url in candidates
                    or not isinstance(terms, list)
                    or len(terms) < len(item["required_terms"])
                    or any(not isinstance(term, str) or not term.strip() for term in terms)):
                raise RuntimeError(f"Audit Recovery: evidenza alternativa non valida: {coverage}")
            candidates.add(candidate_url)
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
    try:
        origin_port = origin.port
        resolved_port = resolved.port
    except ValueError:
        return False, "URL finale con porta non valida"
    if (
        origin.scheme != "https" or resolved.scheme != "https"
        or origin.username or resolved.username
        or origin.password or resolved.password
        or origin_port not in (None, 443) or resolved_port not in (None, 443)
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
        candidate_urls = [url] + [str(x["url"]) for x in entry.get("alternate_primary_pages") or []]
        if key in ids or any(normalized(candidate_url) in urls for candidate_url in candidate_urls):
            already.append(key)
            continue
        if date.fromisoformat(str(entry["deadline_at"])) < today:
            expired.append(key)
            continue

        # L'alternativa ufficiale viene tentata solo dopo un fallimento.
        # Vietati proxy, cache, fixture live e redirect cross-host.
        selected_entry: dict[str, Any] | None = None
        selected_diagnostics: dict[str, Any] | None = None
        failures: list[str] = []
        for primary in [entry, *(entry.get("alternate_primary_pages") or [])]:
            primary_url = str(primary["url"])
            candidate_entry = dict(entry)
            candidate_entry["url"] = primary_url
            candidate_entry["required_terms"] = list(primary["required_terms"])
            if primary.get("source_label"):
                candidate_entry["source_label"] = primary["source_label"]

            raw = (detail_payloads or {}).get(primary_url)
            transport_error = None
            diagnostics: dict[str, Any] | None = None
            if raw is None and live:
                remaining = fetch_until - time.monotonic()
                if remaining > 0.5:
                    try:
                        candidate, diagnostics = discovery.fetch_with_diagnostics(
                            primary_url, timeout=min(4.0, remaining), attempts=1,
                            max_seconds=min(4.0, remaining),
                        )
                        trusted, reason = verification_grade_transport(primary_url, diagnostics)
                        if trusted:
                            raw = candidate
                        else:
                            transport_error = reason
                    except Exception as exc:
                        transport_error = str(exc)
                else:
                    transport_error = "Budget breve holdout esaurito: riprova al prossimo run"

            ok, verification, error = core.verify_entry(
                candidate_entry, today,
                detail_payloads={primary_url: raw} if raw is not None else None,
                live=False, fallback_max_days=0,
            )
            if transport_error or not ok or verification != "live":
                failures.append(f"{primary_url}: {transport_error or error or 'Pagina non verificata'}")
                continue
            selected_entry = candidate_entry
            selected_diagnostics = diagnostics
            break

        if selected_entry is None:
            pending.append({
                "coverage_id": key,
                "title": entry["title"],
                "url": url,
                "deadline_at": entry["deadline_at"],
                "reason": "; ".join(failures)[:900] or "Pagina ufficiale non verificata nel run corrente",
                "stage": "primary_evidence_pending",
            })
            continue

        item = core.build_seed_item(selected_entry, today, "live_official_primary")
        item["source_verification"] = {
            "type": "official_primary_webpage" if live else "offline_test_fixture",
            "url": selected_entry["url"],
            "resolved_url": str((selected_diagnostics or {}).get("resolvedUrl") or selected_entry["url"]),
            "transport": str((selected_diagnostics or {}).get("transport") or "test_fixture"),
            "proxy_used": False if live else None,
            "verified_at": today.isoformat(),
            "required_terms": list(selected_entry.get("required_terms") or []),
        }
        item["first_seen_at"] = today.isoformat()
        if entry.get("municipal_relevance_class") == "partner":
            item["applicant_eligibility"] = "not_direct_applicant"
            item["territorial_relevance"] = "indirect"
        item["municipal_relevance_class"] = str(entry["municipal_relevance_class"])
        result.setdefault("opportunities", []).append(item)
        ids.add(key)
        urls.add(normalized(str(selected_entry["url"])))
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
