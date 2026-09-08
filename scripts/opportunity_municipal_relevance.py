#!/usr/bin/env python3
"""Classificazione pubblica del ruolo comunale nel Radar Opportunità.

Il contratto separa le opportunità che entrano nel conteggio principale da quelle
in cui il Comune opera soltanto come partner/beneficiario di consorzio. Le
classi esplicite presenti nei dati hanno sempre precedenza; il fallback serve
solo a mantenere compatibili le schede v0.4.4 già pubblicate.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

SCHEMA_VERSION = "1.0"

DIRECT = "direct"
DIRECT_CONDITIONAL = "direct_conditional"
SUPPORT_FINANCE = "support_finance"
ROUTED = "routed"
PARTNER = "partner"
REVIEW_EXCLUDE = "review_exclude"

VALID_CLASSES = {
    DIRECT,
    DIRECT_CONDITIONAL,
    SUPPORT_FINANCE,
    ROUTED,
    PARTNER,
    REVIEW_EXCLUDE,
}
HEADLINE_CLASSES = {DIRECT, DIRECT_CONDITIONAL, SUPPORT_FINANCE, ROUTED}
PUBLIC_CLASSES = HEADLINE_CLASSES | {PARTNER}
CURRENT_STAGES = {"application_open", "rolling_open"}

LABELS = {
    DIRECT: "Diretta",
    DIRECT_CONDITIONAL: "Diretta con requisiti",
    SUPPORT_FINANCE: "Supporto / finanza",
    ROUTED: "Route nazionale",
    PARTNER: "Partnership / consorzio",
    REVIEW_EXCLUDE: "Revisione interna",
}

# Overlay minimo per schede già note in cui il vecchio municipality_role non
# distingue bene una vera route di supporto da una candidatura classica.
KNOWN_CLASS_BY_COVERAGE_ID = {
    "eib-elena-rolling": SUPPORT_FINANCE,
    "eu-eui-city-to-city-exchanges-2026": SUPPORT_FINANCE,
}


def _normalized_explicit(value: Any) -> str | None:
    raw = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "direct": DIRECT,
        "direct_conditional": DIRECT_CONDITIONAL,
        "support": SUPPORT_FINANCE,
        "support_finance": SUPPORT_FINANCE,
        "finance": SUPPORT_FINANCE,
        "routed": ROUTED,
        "national_route": ROUTED,
        "partner": PARTNER,
        "partnership": PARTNER,
        "review": REVIEW_EXCLUDE,
        "exclude": REVIEW_EXCLUDE,
        "review_exclude": REVIEW_EXCLUDE,
    }
    return aliases.get(raw)


def classify_item(item: dict[str, Any]) -> str:
    """Restituisce la classe municipale pubblica di una scheda.

    Le nuove promozioni devono valorizzare ``municipal_relevance_class``. Il
    fallback è deliberatamente conservativo e serve alle sole schede legacy.
    """
    explicit = _normalized_explicit(item.get("municipal_relevance_class"))
    if explicit:
        return explicit

    coverage_id = str(item.get("coverage_id") or "").strip()
    if coverage_id in KNOWN_CLASS_BY_COVERAGE_ID:
        return KNOWN_CLASS_BY_COVERAGE_ID[coverage_id]

    role = str(item.get("municipality_role") or "").strip().lower()
    eligibility = str(item.get("eligibility") or "").strip().lower()
    access = str(item.get("access_mode") or "").strip().lower()

    routed_tokens = ("managing_authority", "coordinating_authority", "national_route", "via_national")
    if any(token in role for token in routed_tokens):
        return ROUTED

    support_tokens = (
        "borrower",
        "advisory",
        "technical_assistance",
        "support_request",
        "requester",
        "matchmaking",
        "asset_transfer",
    )
    if any(token in role for token in support_tokens):
        return SUPPORT_FINANCE

    if "partner" in role and "direct" not in role and "applicant" not in role:
        return PARTNER
    if role in {"partner", "consortium_partner", "demo_partner", "public_procurer"}:
        return PARTNER

    direct_tokens = ("direct", "applicant", "lead_applicant", "proponent")
    if any(token in role for token in direct_tokens):
        if eligibility == "eligible" and access != "specific_requirement":
            return DIRECT
        return DIRECT_CONDITIONAL

    # Compatibilità v0.4.4: una scheda già pubblica con ammissibilità positiva
    # resta nel conteggio comunale, ma non viene promossa come "diretta" se il
    # vecchio schema non documentava un ruolo abbastanza preciso.
    if eligibility in {"eligible", "conditional"}:
        return DIRECT_CONDITIONAL
    return REVIEW_EXCLUDE


def annotate_item(item: dict[str, Any]) -> str:
    relevance = classify_item(item)
    item["municipal_relevance_class"] = relevance
    item["municipal_relevance_label"] = LABELS[relevance]
    item["municipal_headline"] = relevance in HEADLINE_CLASSES
    return relevance


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    classes = Counter()
    headline_current = headline_upcoming = partner_current = partner_upcoming = 0
    for item in items:
        relevance = classify_item(item)
        classes[relevance] += 1
        stage = str(item.get("lifecycle_stage") or "application_open")
        if relevance in HEADLINE_CLASSES:
            if stage in CURRENT_STAGES:
                headline_current += 1
            elif stage == "announced_upcoming":
                headline_upcoming += 1
        elif relevance == PARTNER:
            if stage in CURRENT_STAGES:
                partner_current += 1
            elif stage == "announced_upcoming":
                partner_upcoming += 1

    return {
        "schemaVersion": SCHEMA_VERSION,
        "headlineCurrentOrRolling": headline_current,
        "headlineUpcoming": headline_upcoming,
        "headlineTotal": headline_current + headline_upcoming,
        "partnershipCurrentOrRolling": partner_current,
        "partnershipUpcoming": partner_upcoming,
        "partnershipTotal": partner_current + partner_upcoming,
        "reviewExcluded": classes[REVIEW_EXCLUDE],
        "byClass": {key: classes[key] for key in sorted(VALID_CLASSES)},
    }


def apply_to_payload(result: dict[str, Any], *, drop_review: bool = True) -> dict[str, Any]:
    items = list(result.get("opportunities") or [])
    public_items: list[dict[str, Any]] = []
    review_items: list[dict[str, Any]] = []
    for item in items:
        relevance = annotate_item(item)
        if relevance == REVIEW_EXCLUDE and drop_review:
            review_items.append(item)
        else:
            public_items.append(item)

    if drop_review:
        result["opportunities"] = public_items
        if review_items:
            result.setdefault("municipalRelevanceReview", []).extend(review_items)

    summary = summarize(public_items)
    result["municipalRelevance"] = summary
    counts = result.setdefault("counts", {})
    counts["municipalHeadline"] = summary["headlineTotal"]
    counts["municipalHeadlineCurrentOrRolling"] = summary["headlineCurrentOrRolling"]
    counts["municipalHeadlineUpcoming"] = summary["headlineUpcoming"]
    counts["partnership"] = summary["partnershipTotal"]
    counts["partnershipCurrentOrRolling"] = summary["partnershipCurrentOrRolling"]
    counts["partnershipUpcoming"] = summary["partnershipUpcoming"]
    counts["municipalReviewExcluded"] = summary["reviewExcluded"] + len(review_items)
    counts["public"] = len(public_items)
    return result


def visible_partitions(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    municipal: list[dict[str, Any]] = []
    partner: list[dict[str, Any]] = []
    for item in items:
        relevance = annotate_item(item)
        if relevance in HEADLINE_CLASSES:
            municipal.append(item)
        elif relevance == PARTNER:
            partner.append(item)
    return municipal, partner
