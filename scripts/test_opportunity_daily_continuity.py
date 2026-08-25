#!/usr/bin/env python3
from __future__ import annotations

from opportunity_daily_refresh import _reconcile_final_continuity


def main() -> int:
    result = {
        "opportunities": [
            {
                "id": "opp-current",
                "coverage_id": "current-coverage",
                "rule_id": "coverage:current-coverage",
                "title": "Bando corrente",
                "url": "https://example.test/bando-corrente?utm_source=test",
                "deadline_at": "2026-09-30",
            }
        ],
        "archive": [
            {
                "id": "opp-expired",
                "coverage_id": "expired-coverage",
                "title": "Bando scaduto",
                "url": "https://example.test/bando-scaduto",
                "deadline_at": "2026-08-20",
            }
        ],
        "continuityHold": [
            {
                "identity_key": "rule:coverage:current-coverage",
                "title": "Bando corrente",
                "url": "https://example.test/bando-corrente",
                "deadline_at": "2026-09-30",
            },
            {
                "identity_key": "rule:coverage:expired-coverage",
                "title": "Bando scaduto",
                "url": "https://example.test/bando-scaduto",
                "deadline_at": "2026-08-20",
            },
            {
                "identity_key": "rule:missing",
                "title": "Bando davvero scomparso",
                "url": "https://example.test/bando-missing",
                "deadline_at": "2026-10-15",
            },
        ],
        "counts": {"continuityHold": 3},
    }

    reconciled = _reconcile_final_continuity(result)
    assert len(reconciled["continuityHold"]) == 1, reconciled["continuityHold"]
    assert reconciled["continuityHold"][0]["title"] == "Bando davvero scomparso"
    assert reconciled["counts"]["continuityHold"] == 1
    audit = reconciled["continuityReconciliation"]
    assert audit["before"] == 3
    assert audit["reconciled"] == 2
    assert audit["remaining"] == 1

    # Un titolo simile da solo non deve cancellare un HOLD: serve una identità
    # deterministica (rule/coverage/id/url oppure titolo+stessa scadenza).
    second = {
        "opportunities": [
            {"title": "Bando quasi uguale", "url": "", "deadline_at": "2026-11-01"}
        ],
        "archive": [],
        "continuityHold": [
            {"title": "Bando quasi uguale", "url": "", "deadline_at": "2026-11-02"}
        ],
        "counts": {},
    }
    _reconcile_final_continuity(second)
    assert len(second["continuityHold"]) == 1

    print("Riconciliazione finale continuità Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
