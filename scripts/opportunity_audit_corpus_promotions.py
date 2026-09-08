#!/usr/bin/env python3
"""Promuove nel Radar pubblico i finding verificati del corpus audit v1.

Le Wave sono evidenza di discovery già verificata: questo modulo le trasforma in
schede pubbliche senza trasformare scope-review, storici o casi già catturati in
opportunità. Il replay è deterministico, deduplica per identità/titolo e conserva
la distinzione fra opportunità comunali e partnership.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import opportunity_municipal_relevance as relevance

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MUNICIPALITIES = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
PROMOTION_VERSION = "audit-corpus-v1-20260908"

_FORCE_INCLUDE_IDS = {
    "eu-beactive-sport-awards-2026",
    "trunsport-open-call-1-2026",
    "eit-umx-cutoff2-2026",
}

_NEGATIVE_CLASS_MARKERS = (
    "historical",
    "prelaunch",
    "pre_launch",
    "scope_excluded",
    "review_exclude",
    "not_actionable",
    "negative_control",
    "calendar_sentinel",
    "closed",
)

_POSITIVE_CLASS_MARKERS = (
    "current_false_negative",
    "false_negative",
    "rolling_structural_gap",
    "promotion_gap",
    "indirect_route_gap",
    "qualification_access_gap",
    "current_national_route",
    "current_actionable_gap",
    "current_actionable",
    "known_current_gap_not_new",
    "known_rolling_structural_gap_not_new",
)

_SUPPORT_TITLE_MARKERS = (
    "elena",
    "citizen energy advisory hub",
    "smart cities marketplace",
    "eib adapt",
    "circular city centre",
    "sinfi",
    "cultura missione comune",
    "citizen engagement hotline",
    "sport missione comune",
    "green assist",
    "roster of experts",
    "peer reviewer",
    "cities & regions network",
    "cities and regions network",
    "co-waters coalition",
    "eeef",
    "investeu portal",
    "council of europe development bank",
)
_ROUTED_TITLE_MARKERS = (
    "amif specific action",
    "integration at local level",
    "technical support instrument",
)
_PARTNER_TITLE_MARKERS = (
    "interreg euro-med call 7",
    "interreg next med",
    "trunsport",
    "multilevel climate",
    "horizon",
    "mission adaptation cultural",
    "mission ocean",
    "new european bauhaus",
    "neb facility",
    "co-create neb",
    "enerpov",
    "circbio",
    "zeropollution",
    "cities mission pcp",
    "ssri-03",
    "ssri-02",
    "i3 inv",
    "betterreno",
    "skills infrastructure",
)


def _wave_number(path: Path) -> int:
    match = re.search(r"wave(\d+)", path.name)
    return int(match.group(1)) if match else 1


def _audit_paths() -> list[Path]:
    paths = list(DATA_DIR.glob("opportunity-eu-audit*.json"))
    return sorted(paths, key=lambda p: (_wave_number(p), p.name))


def _walk(node: Any, inherited: dict[str, Any] | None = None) -> Iterable[dict[str, Any]]:
    inherited = dict(inherited or {})
    if isinstance(node, dict):
        context = dict(inherited)
        for key in (
            "officialUrl", "officialSources", "url", "publishedAt", "publishedOrOpenedAt",
            "opensAt", "deadlineAt", "auditDate", "municipalityRole", "auditClass",
            "funding", "eligibilityEvidence", "formalApplicabilityToSevenMunicipalities",
            "geographicScope", "conditions", "note",
        ):
            value = node.get(key)
            if value not in (None, "", [], {}):
                context[key] = value
        merged = dict(context)
        merged.update(node)
        if merged.get("id") and merged.get("title") and merged.get("auditClass"):
            yield merged
        for value in node.values():
            yield from _walk(value, context)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value, inherited)


def _parse_day(value: Any) -> date | None:
    text = str(value or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _normalized_title(value: Any) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"[^a-z0-9à-ÿ]+", " ", text)
    return " ".join(text.split())


def _class_is_publishable(item: dict[str, Any], today: date) -> bool:
    item_id = str(item.get("id") or "")
    audit_class = str(item.get("auditClass") or "").casefold()
    if item_id in _FORCE_INCLUDE_IDS:
        return True
    if any(marker in audit_class for marker in _NEGATIVE_CLASS_MARKERS):
        return False
    if "captured" in audit_class:
        return False
    if any(marker in audit_class for marker in _POSITIVE_CLASS_MARKERS):
        return True
    opens = _parse_day(item.get("opensAt"))
    if opens and opens > today and "upcoming" in audit_class:
        return True
    return False


def _first_url(item: dict[str, Any]) -> str | None:
    for key in ("officialUrl", "url", "sourceUrl", "fundingPortalUrl", "callUrl", "applyUrl"):
        value = str(item.get(key) or "").strip()
        if value.startswith("http://") or value.startswith("https://"):
            return value
    sources = item.get("officialSources")
    if isinstance(sources, list):
        for value in sources:
            value = str(value or "").strip()
            if value.startswith("http://") or value.startswith("https://"):
                return value
    return None


def _source_publisher(item: dict[str, Any], url: str) -> str:
    title = str(item.get("title") or "")
    for sep in (" · ", " — ", " - "):
        if sep in title:
            prefix = title.split(sep, 1)[0].strip()
            if 2 <= len(prefix) <= 80:
                return prefix
    host = urlsplit(url).netloc.removeprefix("www.")
    return host or "Fonte ufficiale"


def _relevance_class(item: dict[str, Any]) -> str:
    title = _normalized_title(item.get("title"))
    role = str(item.get("municipalityRole") or "").casefold()
    audit_class = str(item.get("auditClass") or "").casefold()

    if "european capitals of small retail" in title:
        return relevance.DIRECT
    if any(marker in title for marker in _ROUTED_TITLE_MARKERS):
        return relevance.ROUTED
    if "indirect_route" in audit_class or any(
        token in role for token in ("managing_authority", "coordinating_authority", "via_national", "national_route")
    ):
        return relevance.ROUTED
    if any(marker in title for marker in _SUPPORT_TITLE_MARKERS):
        return relevance.SUPPORT_FINANCE
    if "rolling_structural_gap" in audit_class or any(
        token in role for token in (
            "advisory", "technical_assistance", "borrower", "support_request", "requesting",
            "matchmaking", "asset_transfer", "portal", "roster", "finance",
        )
    ):
        return relevance.SUPPORT_FINANCE
    if any(marker in title for marker in _PARTNER_TITLE_MARKERS):
        return relevance.PARTNER
    if any(token in role for token in ("partner", "consortium", "procurer", "demo_")):
        return relevance.PARTNER
    return relevance.DIRECT_CONDITIONAL


def _summary(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("funding", "eligibilityEvidence", "note"):
        value = str(item.get(key) or "").strip()
        if value and value not in parts:
            parts.append(value)
    conditions = item.get("conditions")
    if isinstance(conditions, list) and conditions:
        parts.append("Condizioni: " + "; ".join(str(x) for x in conditions if x))
    text = " ".join(parts).strip()
    if not text:
        text = "Opportunità verificata nel corpus indipendente del Radar; consultare la fonte ufficiale per requisiti e modalità operative."
    return text[:1200]


def _category(title: str) -> str:
    text = _normalized_title(title)
    mapping = (
        (("sport",), "sport"),
        (("cinema", "cultura", "heritage", "museum", "muse"), "cultura"),
        (("energy", "energia", "climate", "clima", "green", "net zero", "life cet"), "energia"),
        (("mobility", "transport", "trasport"), "mobilita"),
        (("digital", "connectivity", "ai ", "data "), "digitale"),
        (("social", "integration", "youth", "erasmus", "solidarity"), "sociale"),
        (("nature", "ocean", "water", "environment", "circular", "biodiversity"), "ambiente"),
    )
    for terms, category in mapping:
        if any(term in text for term in terms):
            return category
    return "amministrazione"


def _eligibility_reason(item: dict[str, Any]) -> str:
    for key in ("eligibilityEvidence", "formalApplicabilityToSevenMunicipalities", "note"):
        value = str(item.get(key) or "").strip()
        if value:
            return value[:900]
    conditions = item.get("conditions")
    if isinstance(conditions, list) and conditions:
        return "; ".join(str(x) for x in conditions if x)[:900]
    return "Ruolo comunale verificato nell'audit; ammissibilità concreta subordinata ai requisiti della fonte ufficiale."


def _municipality_map(title: str, reason: str) -> dict[str, dict[str, str]]:
    mapped = {name: {"status": "conditional", "reason": reason} for name in MUNICIPALITIES}
    if "European Capitals of Small Retail" in title:
        mapped["Stazzema"] = {
            "status": "ineligible",
            "reason": "La competizione richiede una città con almeno 5.000 abitanti; Stazzema non raggiunge la soglia.",
        }
    return mapped


def _candidate_to_item(item: dict[str, Any], today: date) -> dict[str, Any] | None:
    url = _first_url(item)
    if not url:
        return None
    deadline = _parse_day(item.get("deadlineAt"))
    opens = _parse_day(item.get("opensAt"))
    if deadline and deadline < today:
        return None

    audit_class = str(item.get("auditClass") or "").casefold()
    if opens and opens > today:
        lifecycle = "announced_upcoming"
    elif deadline is None and "rolling" in audit_class:
        lifecycle = "rolling_open"
    elif deadline is None:
        lifecycle = "rolling_open"
    else:
        lifecycle = "application_open"

    title = str(item.get("title") or "").strip()
    raw_id = str(item.get("id") or title)
    coverage_id = raw_id
    relevance_class = _relevance_class(item)
    publisher = _source_publisher(item, url)
    reason = _eligibility_reason(item)
    category = _category(title)
    summary = _summary(item)
    role = str(item.get("municipalityRole") or "municipal_role_verified_by_audit")
    first_seen = str(item.get("auditDate") or today.isoformat())[:10]
    digest = hashlib.sha1(coverage_id.encode("utf-8")).hexdigest()[:14]

    return {
        "id": f"opp-audit-{digest}",
        "coverage_id": coverage_id,
        "source_id": "audit-corpus-v1",
        "source_name": publisher,
        "publisher": publisher,
        "title": title,
        "url": url,
        "summary": summary,
        "status": "open" if lifecycle != "announced_upcoming" else "upcoming",
        "opens_at": opens.isoformat() if opens else None,
        "deadline_at": deadline.isoformat() if deadline else None,
        "published_at": str(item.get("publishedAt") or item.get("publishedOrOpenedAt") or "")[:10] or None,
        "beneficiary_text": reason,
        "municipalities": list(MUNICIPALITIES),
        "eligibility": "conditional",
        "eligibility_reason": reason,
        "municipality_eligibility": _municipality_map(title, reason),
        "applicant_eligibility": "conditional",
        "applicant_type": role.replace("_", " "),
        "municipality_role": role,
        "municipal_relevance_class": relevance_class,
        "final_beneficiaries": str(item.get("finalBeneficiaries") or "Comuni e comunità locali interessati dal progetto o servizio"),
        "partnership_required": relevance_class == relevance.PARTNER or "partner" in role.casefold(),
        "project_requirements": reason,
        "geographic_scope": str(item.get("geographicScope") or "Italia / Unione europea secondo la call"),
        "geographic_eligibility": "conditional",
        "territorial_relevance": "partner" if relevance_class == relevance.PARTNER else "direct",
        "actionable_for_municipality": True,
        "decision_class": "audit_verified_partner" if relevance_class == relevance.PARTNER else "audit_verified_municipal",
        "themes": [category],
        "verified_direct": relevance_class != relevance.PARTNER,
        "verified_at": today.isoformat(),
        "audit_class": item.get("auditClass"),
        "audit_promotion_version": PROMOTION_VERSION,
        "presentation": {
            "source_label": publisher,
            "source_mark": "UE" if ".eu" in urlsplit(url).netloc or "europa.eu" in url else publisher[:12],
            "source_class": "eu" if ".eu" in urlsplit(url).netloc or "europa.eu" in url else "istituzionale",
            "category": category,
            "description": summary[:320],
            "condition_label": "Partnership / consorzio" if relevance_class == relevance.PARTNER else "Verificare i requisiti specifici",
        },
        "access_mode": "specific_requirement" if relevance_class not in {relevance.SUPPORT_FINANCE, relevance.ROUTED} else "support_route",
        "quality_gate": {"status": "pass", "missing": [], "reasons": []},
        "lifecycle_stage": lifecycle,
        "is_new": True,
        "first_seen_at": first_seen,
    }


def discover_promotions(today: date) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for path in _audit_paths():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        audit_date = str(payload.get("auditDate") or "")
        for candidate in _walk(payload, {"auditDate": audit_date}):
            item_id = str(candidate.get("id") or "").strip()
            if not item_id:
                continue
            previous = latest.get(item_id, {})
            merged = dict(previous)
            merged.update({k: v for k, v in candidate.items() if v not in (None, "", [], {})})
            latest[item_id] = merged

    output: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for candidate in latest.values():
        if not _class_is_publishable(candidate, today):
            continue
        item = _candidate_to_item(candidate, today)
        if item is None:
            continue
        title_key = _normalized_title(item.get("title"))
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        output.append(item)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    output.sort(key=lambda x: (
        order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
        str(x.get("deadline_at") or "9999-99-99"),
        str(x.get("title") or ""),
    ))
    return output


def apply_audit_corpus_promotions(result: dict[str, Any], today: date) -> dict[str, Any]:
    promotions = discover_promotions(today)
    opportunities = result.setdefault("opportunities", [])
    existing_ids = {str(x.get("coverage_id") or x.get("rule_id") or "") for x in opportunities}
    existing_titles = {_normalized_title(x.get("title")) for x in opportunities}

    added: list[dict[str, Any]] = []
    for item in promotions:
        coverage_id = str(item.get("coverage_id") or "")
        title_key = _normalized_title(item.get("title"))
        if coverage_id in existing_ids or title_key in existing_titles:
            continue
        opportunities.append(item)
        added.append(item)
        existing_ids.add(coverage_id)
        existing_titles.add(title_key)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    opportunities.sort(key=lambda x: (
        order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
        str(x.get("deadline_at") or "9999-99-99"),
        str(x.get("title") or ""),
    ))

    added_summary = relevance.summarize(added)
    result["auditCorpusPromotionVersion"] = PROMOTION_VERSION
    result["auditCorpusPromotion"] = {
        "discovered": len(promotions),
        "added": len(added),
        "municipalCurrentOrRollingAdded": added_summary["headlineCurrentOrRolling"],
        "municipalUpcomingAdded": added_summary["headlineUpcoming"],
        "partnershipCurrentOrRollingAdded": added_summary["partnershipCurrentOrRolling"],
        "partnershipUpcomingAdded": added_summary["partnershipUpcoming"],
    }
    result.setdefault("counts", {})["auditPromotionsAdded"] = len(added)
    return result
