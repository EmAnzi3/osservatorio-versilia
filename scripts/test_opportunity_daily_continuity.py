#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from opportunity_daily_refresh import _reconcile_final_continuity, _write_continuity_diagnostic


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
                "source_id": "source-test",
                "url": "https://example.test/bando-missing",
                "deadline_at": "2026-10-15",
                "reason": "Opportunità non più rilevata.",
            },
        ],
        "counts": {"continuityHold": 3},
        "referenceDate": "2026-08-28",
    }

    reconciled = _reconcile_final_continuity(result)
    assert len(reconciled["continuityHold"]) == 1, reconciled["continuityHold"]
    assert reconciled["continuityHold"][0]["title"] == "Bando davvero scomparso"
    assert reconciled["counts"]["continuityHold"] == 1
    audit = reconciled["continuityReconciliation"]
    assert audit["before"] == 3
    assert audit["reconciled"] == 2
    assert audit["remaining"] == 1

    with tempfile.TemporaryDirectory() as tmp:
        diagnostic_path = Path(tmp) / "continuity.json"
        written = _write_continuity_diagnostic(reconciled, diagnostic_path)
        assert written == diagnostic_path
        payload = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        assert payload["referenceDate"] == "2026-08-28"
        assert payload["count"] == 1
        hold = payload["holds"][0]
        assert hold["title"] == "Bando davvero scomparso"
        assert hold["source_id"] == "source-test"
        assert hold["identity_key"] == "rule:missing"
        assert hold["deadline_at"] == "2026-10-15"
        assert hold["url"] == "https://example.test/bando-missing"
        assert hold["reason"] == "Opportunità non più rilevata."

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
    print("Diagnostica continuity hold Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
