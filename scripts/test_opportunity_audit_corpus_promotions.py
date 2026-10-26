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


def _italian_texts_contract() -> None:
    """Le traduzioni restano vincolate all'evidenza originale e sostituiscono i testi pubblici."""
    import re
    import opportunity_audit_corpus_promotions as base
    payload = json.loads((ROOT / "data" / "opportunity-audit-italian-texts.json").read_text(encoding="utf-8"))
    entries = payload["entries"]
    assert entries, "Nessuna traduzione registrata"
    original = base.italian_presentation
    base.italian_presentation = lambda *args, **kwargs: None
    try:
        english = {x["coverage_id"]: x for x in base.discover_promotions(date(2026, 10, 26))}
    finally:
        base.italian_presentation = original
    published = {x["coverage_id"]: x for x in base.discover_promotions(date(2026, 10, 26))}
    english_words = re.compile(r"\b(the|and|which|through|authorities|applicant|eligible|requests)\b", re.I)
    for coverage_id, entry in entries.items():
        assert coverage_id in english, f"Traduzione per una voce non più pubblicata: {coverage_id}"
        source = english[coverage_id]
        digest = base._source_text_digest(source["summary"], source["eligibility_reason"])
        assert entry["sourceSha256"] == digest, f"Testo audit cambiato, traduzione da rivedere: {coverage_id}"
        item = published[coverage_id]
        assert item["summary"] == entry["summary"] and item["eligibility_reason"] == entry["reason"]
        assert item["beneficiary_text"] == item["project_requirements"] == entry["reason"]
        assert item["presentation"]["description"] == entry["description"]
        assert all(v["reason"] == entry["reason"] for v in item["municipality_eligibility"].values()
                   if v["status"] == "conditional")
        for text in (entry["summary"], entry["reason"], entry["description"]):
            assert not english_words.search(text), (coverage_id, text)
    # Un cambio del testo originale disattiva la traduzione invece di mostrarla superata.
    cid = next(iter(entries))
    assert base.italian_presentation(cid, english[cid]["summary"] + " (aggiornato)", english[cid]["eligibility_reason"]) is None
    # Una scheda già presente (continuità) riceve il testo corrente.
    stale = copy.deepcopy(english[cid])
    result = {"opportunities": [stale]}
    base.apply_audit_corpus_promotions(result, date(2026, 10, 26))
    assert stale["summary"] == entries[cid]["summary"], "Scheda ripristinata rimasta in inglese"


def main() -> int:
    _italian_texts_contract()
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

    future = promotions.apply_complete_promotions(copy.deepcopy(baseline), date(2026, 9, 18))
    retained = {
        str(item.get("coverage_id") or "")
        for item in list(future.get("opportunities") or []) + list(future.get("archive") or [])
        if str(item.get("source_id") or "") in {"audit-corpus-v1", "municipal-matrix-v1"}
        and item.get("coverage_id")
    }
    assert len(retained) >= promotions.MATRIX_CURRENT_TARGET, (
        len(retained), promotions.MATRIX_CURRENT_TARGET
    )
    assert "horizon-cl6-2026-01-zeropollution-03" in retained

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
