#!/usr/bin/env python3
"""Safety net di completezza per i bandi di Regione Toscana.

Il collector principale resta l'unica via di pubblicazione automatica. Questo
modulo usa un secondo passaggio sul listing regionale per impedire che un bando
recente con un ruolo comunale esplicito scompaia tra listing e classificatore:
se non e' gia' pubblico o contabilizzato, entra nella discovery queue; se resta
irrisolto oltre la finestra di grazia, genera un coverage hold.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Any, Callable
from urllib.parse import urljoin

import run_opportunity_radar_v03 as runtime_v03

radar = runtime_v03.radar
base = radar.base

LISTING_URL = "https://www.regione.toscana.it/it/bandi-tutti?delta=60&sortBy=desc&start=1"
RECENT_WINDOW_DAYS = 21
REVIEW_GRACE_DAYS = 7

_MUNICIPAL_AUDIENCE_TERMS = (
    "enti locali",
    "comuni della toscana",
    "comuni toscani",
    "comuni della regione toscana",
    "unioni di comuni",
    "comune capofila",
    "amministrazioni comunali",
)
_AUDIENCE_MARKERS = (
    "beneficiari",
    "a chi si rivolge",
    "soggetti beneficiari",
    "soggetti ammessi",
    "possono presentare domanda",
    "possono presentare istanza",
)


def _fold(value: Any) -> str:
    return radar.v025.fold(value)


def _publication_date(text: str) -> date | None:
    patterns = (
        r"(?:pubblicato il|pubblicazione[^\n:]{0,40})\s*:?[\s\xa0]*(\d{1,2}[./]\d{1,2}[./]\d{4})",
        r"data di pubblicazione bando su burt\s*:?[\s\xa0]*(\d{1,2}[./]\d{1,2}[./]\d{4})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        parsed = base.parse_date(match.group(1))
        if parsed:
            return parsed
    return None


def _deadline_date(text: str) -> date | None:
    match = re.search(
        r"scadenza(?: presentazione domande)?\s*:?[\s\xa0]*(\d{1,2}[./]\d{1,2}[./]\d{4})",
        text,
        flags=re.I,
    )
    return base.parse_date(match.group(1)) if match else None


def _audience_context(text: str) -> str:
    folded = _fold(text)
    starts = [folded.find(marker) for marker in _AUDIENCE_MARKERS if folded.find(marker) >= 0]
    if not starts:
        return folded[:5000]
    start = min(starts)
    return folded[start : start + 3500]


def _has_explicit_municipal_audience(text: str) -> bool:
    context = _audience_context(text)
    if not any(marker in context for marker in _AUDIENCE_MARKERS):
        return False
    return any(term in context for term in _MUNICIPAL_AUDIENCE_TERMS)


def _stable_key(url: str, title: str) -> str:
    raw = radar.v025.normalized_url(url) or _fold(title)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]


def _account_state(result: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    wanted_url = radar.v025.normalized_url(candidate.get("url"))
    wanted_title = _fold(candidate.get("title"))
    fields = (
        ("opportunities", "public"),
        ("qualityHold", "quality_hold"),
        ("reviewQueue", "review"),
        ("discoveryQueue", "discovery"),
        ("coverageHold", "coverage_hold"),
        ("continuityHold", "continuity_hold"),
    )
    for field, state in fields:
        for item in result.get(field) or []:
            item_url = radar.v025.normalized_url(item.get("url"))
            if wanted_url and item_url and wanted_url == item_url:
                return state
            item_title = _fold(item.get("title"))
            if wanted_title and item_title:
                if wanted_title == item_title:
                    return state
                shorter, longer = sorted((wanted_title, item_title), key=len)
                if len(shorter) >= 24 and shorter in longer:
                    return state
    return None


def _default_fetch(url: str) -> str:
    return radar.v025.v022.fetch_resilient(url, timeout=30, attempts=1)


def scan_recent_municipal_candidates(
    today: date,
    *,
    listing_payload: str | None = None,
    detail_payloads: dict[str, str] | None = None,
    fetcher: Callable[[str], str] | None = None,
    known_result: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    fetcher = fetcher or _default_fetch
    detail_payloads = detail_payloads or {}
    errors: list[str] = []
    try:
        payload = listing_payload if listing_payload is not None else fetcher(LISTING_URL)
    except Exception as exc:  # pragma: no cover - dipende dalla rete live
        return [], [f"listing Regione Toscana: {exc}"]

    parser = base.Cards()
    parser.feed(payload)
    parser.close()
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_title, href, raw_body in parser.out:
        title = base.clean(raw_title)
        body = base.clean(raw_body)
        if len(title) < 8 or not href:
            continue
        url = urljoin(LISTING_URL, href)
        if "regione.toscana.it" not in url or "/-/" not in url:
            continue
        published = _publication_date(body)
        if not published:
            continue
        age_days = (today - published).days
        if age_days < 0 or age_days > RECENT_WINDOW_DAYS:
            continue
        deadline = _deadline_date(body)
        openish = "stato aperto" in _fold(body) or (deadline is not None and deadline >= today)
        if not openish:
            continue
        norm_url = radar.v025.normalized_url(url)
        if norm_url in seen:
            continue
        seen.add(norm_url)

        stub = {
            "title": title,
            "url": url,
            "summary": body[:600],
            "published_at": published.isoformat(),
            "age_days": age_days,
            "deadline_at": deadline.isoformat() if deadline else None,
        }
        # Le schede gia' pubblicate non richiedono un secondo fetch di dettaglio.
        if known_result is not None and _account_state(known_result, stub) == "public":
            continue

        try:
            detail = detail_payloads[url] if url in detail_payloads else fetcher(url)
            visible = base.visible(detail)
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            errors.append(f"{title}: {exc}")
            continue
        if not _has_explicit_municipal_audience(visible):
            continue
        candidates.append(stub)

    candidates.sort(key=lambda item: (item.get("published_at") or "", item.get("title") or ""), reverse=True)
    return candidates, errors


def apply(
    result: dict[str, Any],
    today: date,
    *,
    listing_payload: str | None = None,
    detail_payloads: dict[str, str] | None = None,
    fetcher: Callable[[str], str] | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggiunge accounting/discovery e coverage hold per gap regionali maturi."""
    errors: list[str] = []
    if candidates is None:
        candidates, errors = scan_recent_municipal_candidates(
            today,
            listing_payload=listing_payload,
            detail_payloads=detail_payloads,
            fetcher=fetcher,
            known_result=result,
        )

    queue = result.setdefault("discoveryQueue", [])
    holds = result.setdefault("coverageHold", [])
    added = 0
    unresolved: list[dict[str, Any]] = []
    overdue: list[dict[str, Any]] = []

    for candidate in candidates:
        state = _account_state(result, candidate)
        if state is None:
            queue.append(
                {
                    "source_id": "regione-toscana-safety-net",
                    "source_label": "Regione Toscana · safety net Enti locali",
                    "publisher": "Regione Toscana",
                    "territory": "Toscana",
                    "title": candidate.get("title"),
                    "url": candidate.get("url"),
                    "summary": candidate.get("summary"),
                    "published_at": candidate.get("published_at"),
                    "deadline_at": candidate.get("deadline_at"),
                    "discovery_only": True,
                    "status": "internal_review",
                    "reason": (
                        "Safety net Regione Toscana: la fonte primaria indica esplicitamente un possibile "
                        "ruolo di Enti locali/Comuni, ma il candidato non era contabilizzato dal flusso principale."
                    ),
                }
            )
            added += 1
            state = "discovery"

        if state in {"public", "coverage_hold", "continuity_hold"}:
            continue

        row = {**candidate, "account_state": state}
        unresolved.append(row)
        age_days = candidate.get("age_days")
        if isinstance(age_days, int) and age_days > REVIEW_GRACE_DAYS:
            overdue.append(row)
            hold_id = "rt-completeness-" + _stable_key(str(candidate.get("url") or ""), str(candidate.get("title") or ""))
            if not any(str(item.get("coverage_id") or "") == hold_id for item in holds):
                holds.append(
                    {
                        "coverage_id": hold_id,
                        "title": candidate.get("title"),
                        "source_id": "regione-toscana",
                        "url": candidate.get("url"),
                        "reason": (
                            "Bando regionale recente con ruolo comunale esplicito ancora non risolto dopo "
                            f"{REVIEW_GRACE_DAYS} giorni: qualificare o escludere documentalmente prima della pubblicazione."
                        ),
                    }
                )

    status = "fail" if overdue else "degraded" if errors else "pass"
    result["regionalCompleteness"] = {
        "status": status,
        "source": "Regione Toscana",
        "recentWindowDays": RECENT_WINDOW_DAYS,
        "reviewGraceDays": REVIEW_GRACE_DAYS,
        "municipalCandidates": len(candidates),
        "safetyNetAdded": added,
        "unresolved": unresolved,
        "overdue": overdue,
        "errors": errors,
    }
    result.setdefault("counts", {})["regionalSafetyNetAdded"] = added
    result.setdefault("counts", {})["regionalUnresolved"] = len(unresolved)
    result.setdefault("counts", {})["regionalOverdue"] = len(overdue)
    return result


if __name__ == "__main__":
    raise SystemExit("Modulo di supporto: usare opportunity_daily_refresh.py o i test dedicati.")
