#!/usr/bin/env python3
from __future__ import annotations

from opportunity_issue_notification import build_payload, render_markdown


def _item(title: str, coverage_id: str, url: str, deadline: str = "2026-09-18"):
    return {
        "id": "opp-" + coverage_id,
        "coverage_id": coverage_id,
        "title": title,
        "url": url,
        "deadline_at": deadline,
        "access_mode": "direct",
        "source_name": "Regione Toscana",
        "municipality_eligibility": {
            "Massarosa": {"status": "eligible", "reason": "test"},
            "Viareggio": {"status": "conditional", "reason": "test"},
            "Camaiore": {"status": "not_eligible", "reason": "test"},
        },
    }


def main() -> int:
    old = {
        "referenceDate": "2026-08-24",
        "opportunities": [
            _item("Bando esistente", "existing", "https://example.test/existing")
        ],
    }
    current = {
        "referenceDate": "2026-08-25",
        "opportunities": [
            _item("Bando esistente", "existing", "https://example.test/existing?utm=1"),
            _item("Celebrazioni storiche 2026", "rt-celebrazioni", "https://example.test/celebrazioni"),
        ],
    }

    payload = build_payload(old, current)
    assert payload["count"] == 1, payload
    assert payload["fingerprint"], payload
    assert payload["marker"] == f"<!-- radar-new:{payload['fingerprint']} -->"
    assert payload["issueTitle"] == "Nuove opportunità Radar · 25/08/2026"
    assert payload["items"][0]["title"] == "Celebrazioni storiche 2026"
    assert [row["name"] for row in payload["items"][0]["municipalities"]] == ["Massarosa", "Viareggio"]

    body = render_markdown(payload)
    assert payload["marker"] in body
    assert "Celebrazioni storiche 2026" in body
    assert "Massarosa (ammissibile)" in body
    assert "Viareggio (condizionale)" in body
    assert "Camaiore" not in body
    assert "18/09/2026" in body

    repeat = build_payload(old, current)
    assert repeat["fingerprint"] == payload["fingerprint"]

    no_change = build_payload(current, {**current, "referenceDate": "2026-08-26"})
    assert no_change["count"] == 0
    assert no_change["fingerprint"] is None
    assert render_markdown(no_change) == ""

    print("Notifiche Issue Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
