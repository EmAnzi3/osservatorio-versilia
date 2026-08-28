#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

from opportunity_daily_refresh import (
    _reconcile_final_continuity,
    _restore_recent_verified_continuity,
    _write_continuity_diagnostic,
)


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

    # Una verifica diretta del run precedente può sopravvivere per massimo due
    # giorni a una mancata riconferma live, ma resta marcata cached_recent.
    previous = {
        "referenceDate": "2026-08-27",
        "municipalities": ["Massarosa"],
        "opportunities": [
            {
                "id": "opp-jazz",
                "rule_id": "mic-jazz-2027",
                "source_id": "mic-spettacolo",
                "title": "Bando Jazz 2027",
                "url": "https://example.test/jazz",
                "deadline_at": "2026-09-10",
                "eligibility": "conditional",
                "municipality_eligibility": {
                    "Massarosa": {"status": "conditional", "reason": "test"}
                },
                "verified_direct": True,
                "verified_at": "2026-08-27",
                "verification_status": "live",
                "first_seen_at": "2026-08-25",
            }
        ],
    }
    transient = {
        "referenceDate": "2026-08-28",
        "municipalities": ["Massarosa"],
        "opportunities": [],
        "archive": [],
        "continuityHold": [
            {
                "identity_key": "rule:mic-jazz-2027",
                "title": "Bando Jazz 2027",
                "source_id": "mic-spettacolo",
                "url": "https://example.test/jazz",
                "deadline_at": "2026-09-10",
            }
        ],
        "counts": {"continuityHold": 1},
        "sources": [{"sourceId": "mic-spettacolo", "publicCount": 0}],
        "sourceCoverage": {"rows": [{"source_id": "mic-spettacolo", "publicCount": 0}]},
        "municipalitySummary": {"Massarosa": {"eligible": 0, "conditional": 0}},
    }
    restored = _restore_recent_verified_continuity(transient, previous, date(2026, 8, 28))
    assert len(restored) == 1
    assert transient["continuityHold"] == []
    assert transient["opportunities"][0]["verification_status"] == "cached_recent"
    assert transient["counts"]["continuityFallback"] == 1
    assert transient["counts"]["public"] == 1
    assert transient["municipalitySummary"]["Massarosa"]["conditional"] == 1
    assert transient["sources"][0]["publicCount"] == 1
    assert transient["sourceCoverage"]["rows"][0]["publicCount"] == 1

    # Oltre la grace il gate deve restare attivo: niente trascinamento indefinito.
    stale = json.loads(json.dumps(transient))
    stale["opportunities"] = []
    stale["continuityHold"] = [
        {
            "identity_key": "rule:mic-jazz-2027",
            "title": "Bando Jazz 2027",
            "source_id": "mic-spettacolo",
            "url": "https://example.test/jazz",
            "deadline_at": "2026-09-10",
        }
    ]
    stale["counts"] = {"continuityHold": 1}
    previous_stale = json.loads(json.dumps(previous))
    previous_stale["opportunities"][0]["verified_at"] = "2026-08-20"
    assert _restore_recent_verified_continuity(stale, previous_stale, date(2026, 8, 28)) == []
    assert len(stale["continuityHold"]) == 1

    print("Riconciliazione finale continuità Radar: PASS")
    print("Diagnostica continuity hold Radar: PASS")
    print("Fallback continuità verificata: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
