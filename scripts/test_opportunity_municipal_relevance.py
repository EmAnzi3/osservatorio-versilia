#!/usr/bin/env python3
"""Contratto: il totale comunale non deve includere partnership o review interne."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import build_opportunity_preview_v04 as preview
import opportunity_municipal_relevance as relevance

ROOT = Path(__file__).resolve().parents[1]


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


def _synthetic_contract() -> None:
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
    assert html.index('data-op-list="municipal"') < html.index('data-op-list="partner"')


def _real_snapshot_contract() -> dict:
    path = ROOT / "data" / "opportunity-daily-public.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    original = list(payload.get("opportunities") or [])
    classified = relevance.apply_to_payload(copy.deepcopy(payload), drop_review=True)
    summary = classified["municipalRelevance"]
    visible = list(classified.get("opportunities") or [])
    excluded = list(classified.get("municipalRelevanceReview") or [])

    assert not excluded, [item.get("title") for item in excluded]
    assert len(visible) == len(original), (len(visible), len(original))
    assert summary["headlineTotal"] + summary["partnershipTotal"] == len(original), summary
    assert summary["headlineCurrentOrRolling"] + summary["headlineUpcoming"] == summary["headlineTotal"]
    assert summary["partnershipCurrentOrRolling"] + summary["partnershipUpcoming"] == summary["partnershipTotal"]
    return summary


def _audit_fix_contract() -> None:
    payload = json.loads((ROOT / "data" / "opportunity-audit-fixes-v1.json").read_text(encoding="utf-8"))
    entries = list(payload.get("verifiedEntries") or [])
    assert entries
    invalid = [
        entry.get("coverage_id")
        for entry in entries
        if str(entry.get("municipal_relevance_class") or "") not in relevance.VALID_CLASSES
    ]
    assert not invalid, f"Verified audit entries senza municipal_relevance_class valida: {invalid}"


def main() -> int:
    _synthetic_contract()
    _audit_fix_contract()
    real = _real_snapshot_contract()
    print(
        "Rilevanza comunale OK: sintetico headline=4 · partnership=1 · review esclusa=1; "
        f"snapshot headline={real['headlineTotal']} "
        f"({real['headlineCurrentOrRolling']} correnti/rolling + {real['headlineUpcoming']} upcoming) · "
        f"partnership={real['partnershipTotal']} "
        f"({real['partnershipCurrentOrRolling']} correnti/rolling + {real['partnershipUpcoming']} upcoming)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
