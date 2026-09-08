#!/usr/bin/env python3
"""Contratto: il totale comunale non deve includere partnership o review interne."""
from __future__ import annotations

import copy

import build_opportunity_preview_v04 as preview
import opportunity_municipal_relevance as relevance


def _item(title: str, relevance_class: str, *, stage: str = "application_open") -> dict:
    return {
        "id": title.lower().replace(" ", "-"),
        "title": title,
        "source_id": "test-source",
        "publisher": "Fonte test",
        "url": "https://example.invalid/test",
        "lifecycle_stage": stage,
        "deadline_at": "2026-10-01" if stage == "application_open" else None,
        "eligibility": "conditional",
        "municipality_role": "direct_applicant",
        "municipal_relevance_class": relevance_class,
        "applicant_type": "Comune",
        "geographic_scope": "Italia",
        "final_beneficiaries": "Comunità locale",
        "project_requirements": "Requisiti del test",
        "municipality_eligibility": {
            "Camaiore": {"status": "conditional", "reason": "Caso sintetico"},
        },
    }


def main() -> int:
    payload = {
        "referenceDate": "2026-09-08",
        "opportunities": [
            _item("Diretta", relevance.DIRECT),
            _item("Diretta condizionata", relevance.DIRECT_CONDITIONAL),
            _item("Supporto", relevance.SUPPORT_FINANCE, stage="rolling_open"),
            _item("Route", relevance.ROUTED),
            _item("Partner", relevance.PARTNER),
            _item("Da escludere", relevance.REVIEW_EXCLUDE),
        ],
        "archive": [],
        "sourceCoverage": {"summary": {}, "rows": []},
        "coverageAudit": {},
        "independentAudit": {},
    }

    result = relevance.apply_to_payload(copy.deepcopy(payload), drop_review=True)
    summary = result["municipalRelevance"]
    counts = result["counts"]

    assert len(result["opportunities"]) == 5
    assert len(result.get("municipalRelevanceReview") or []) == 1
    assert summary["headlineCurrentOrRolling"] == 4, summary
    assert summary["partnershipCurrentOrRolling"] == 1, summary
    assert counts["municipalHeadlineCurrentOrRolling"] == 4, counts
    assert counts["partnershipCurrentOrRolling"] == 1, counts
    assert counts["municipalReviewExcluded"] == 1, counts

    html = preview.render_page(result)
    assert 'data-municipal-headline="4"' in html
    assert 'data-partnership="1"' in html
    assert 'data-op-list="municipal"' in html
    assert 'data-op-list="partner"' in html
    assert 'data-relevance="partner"' in html
    assert "Partnership e consorzi" in html
    assert "Da escludere" not in html
    assert html.count("data-opportunity-card") == 5

    municipal_pos = html.index('data-op-list="municipal"')
    partner_pos = html.index('data-op-list="partner"')
    assert municipal_pos < partner_pos

    print("Rilevanza comunale OK: headline=4 · partnership=1 · review esclusa=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
