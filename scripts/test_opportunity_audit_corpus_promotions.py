#!/usr/bin/env python3
"""Gate del replay audit: il corpus verificato deve diventare Radar pubblico."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import opportunity_audit_corpus_promotions as promotions
import opportunity_municipal_relevance as relevance

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = date(2026, 9, 8)


def main() -> int:
    baseline = json.loads((ROOT / "data" / "opportunity-daily-public.json").read_text(encoding="utf-8"))
    before = relevance.summarize(list(baseline.get("opportunities") or []))
    result = promotions.apply_audit_corpus_promotions(copy.deepcopy(baseline), REFERENCE)
    relevance.apply_to_payload(result, drop_review=True)
    after = result["municipalRelevance"]
    replay = result["auditCorpusPromotion"]

    # Il corpus finale aveva certificato 52 nuove opportunità comunali correnti/
    # rolling e 37 partnership. Il replay può deduplicare contro schede già
    # pubbliche, ma non deve perdere intere famiglie del corpus.
    assert replay["municipalCurrentOrRollingAdded"] >= 45, replay
    assert replay["partnershipCurrentOrRollingAdded"] >= 30, replay
    assert replay["added"] >= 75, replay
    assert after["headlineCurrentOrRolling"] > before["headlineCurrentOrRolling"], (before, after)
    assert after["partnershipCurrentOrRolling"] > before["partnershipCurrentOrRolling"], (before, after)
    assert not result.get("municipalRelevanceReview"), [
        x.get("title") for x in result.get("municipalRelevanceReview") or []
    ]

    print(
        "Replay audit corpus: "
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
