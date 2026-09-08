#!/usr/bin/env python3
"""Gate del replay audit: il corpus verificato deve diventare Radar pubblico."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import opportunity_matrix_promotions as promotions
import opportunity_municipal_relevance as relevance

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = date(2026, 9, 8)


def _print_diagnostics(items: list[dict]) -> None:
    by_class: dict[str, list[str]] = {}
    for item in items:
        cls = relevance.classify_item(item)
        by_class.setdefault(cls, []).append(f"{item.get('coverage_id')} :: {item.get('title')}")
    print("AUDIT REPLAY DIAGNOSTIC START")
    for cls in sorted(by_class):
        print(f"[{cls}] {len(by_class[cls])}")
        for title in sorted(by_class[cls]):
            print("  -", title)
    print("AUDIT REPLAY DIAGNOSTIC END")


def main() -> int:
    baseline = json.loads((ROOT / "data" / "opportunity-daily-public.json").read_text(encoding="utf-8"))
    before_ids = {str(x.get("coverage_id") or x.get("id") or "") for x in baseline.get("opportunities") or []}
    before = relevance.summarize(list(baseline.get("opportunities") or []))
    result = promotions.apply_complete_promotions(copy.deepcopy(baseline), REFERENCE)
    added_items = [
        item for item in result.get("opportunities") or []
        if str(item.get("coverage_id") or item.get("id") or "") not in before_ids
        and item.get("audit_promotion_version") == promotions.PROMOTION_VERSION
    ]
    _print_diagnostics(added_items)
    relevance.apply_to_payload(result, drop_review=True)
    after = result["municipalRelevance"]
    replay = result["auditCorpusPromotion"]

    # La matrice finale certifica 52 nuove opportunità comunali correnti/rolling
    # e 37 partnership rispetto allo snapshot del 7 settembre. Il gate non
    # consente di pubblicare una preview che ne perda anche solo un intero gruppo.
    assert replay["municipalCurrentOrRollingAdded"] >= 52, replay
    assert replay["partnershipCurrentOrRollingAdded"] >= 37, replay
    assert replay["currentOrRollingAdded"] >= promotions.MATRIX_CURRENT_TARGET, replay
    assert replay["added"] >= promotions.MATRIX_CURRENT_TARGET, replay
    assert after["headlineCurrentOrRolling"] > before["headlineCurrentOrRolling"], (before, after)
    assert after["partnershipCurrentOrRolling"] > before["partnershipCurrentOrRolling"], (before, after)
    assert not result.get("municipalRelevanceReview"), [
        x.get("title") for x in result.get("municipalRelevanceReview") or []
    ]

    print(
        "Replay audit corpus completo: "
        f"scoperte={replay['discovered']} · aggiunte={replay['added']} · "
        f"nuove comunali current/rolling={replay['municipalCurrentOrRollingAdded']} · "
        f"nuove comunali upcoming={replay['municipalUpcomingAdded']} · "
        f"nuove partnership current/rolling={replay['partnershipCurrentOrRollingAdded']} · "
        f"nuove partnership upcoming={replay['partnershipUpcomingAdded']} · "
        f"totale finale headline={after['headlineTotal']} · partnership={after['partnershipTotal']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
