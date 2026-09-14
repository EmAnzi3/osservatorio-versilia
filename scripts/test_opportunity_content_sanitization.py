#!/usr/bin/env python3
from __future__ import annotations

from opportunity_daily_refresh import _contamination_offset, _sanitize_public_content


def _item(summary: str, beneficiary: str = "I Comuni toscani possono presentare domanda.") -> dict:
    return {
        "id": "opp-parcheggi",
        "coverage_id": "rt-parcheggi-2026",
        "title": "Bando parcheggi 2026",
        "summary": summary,
        "beneficiary_text": beneficiary,
    }


def main() -> int:
    clean_summary = "Contributi regionali per parcheggi pubblici."
    previous = {"opportunities": [_item(clean_summary)]}
    noise = (
        ' function proxyOpenDialog(event, dataId, button) { document.getElementById("x"); } '
        "60 Elementi Per pagina"
    )
    current = {
        "opportunities": [
            _item(clean_summary + noise, "I Comuni toscani possono presentare domanda." + noise),
            {
                "id": "opp-nuovo",
                "title": "Nuova opportunita",
                "summary": "Testo valido prima del codice" + noise,
                "beneficiary_text": "Enti locali",
            },
        ],
        "counts": {},
    }

    repaired = _sanitize_public_content(current, previous)
    assert len(repaired) == 2, repaired
    assert current["opportunities"][0]["summary"] == clean_summary
    assert current["opportunities"][0]["beneficiary_text"] == "I Comuni toscani possono presentare domanda."
    assert current["opportunities"][1]["summary"] == "Testo valido prima del codice"
    assert current["contentSanitization"]["repairedCount"] == 2
    assert current["counts"]["contentSanitized"] == 2
    for item in current["opportunities"]:
        assert _contamination_offset(item.get("summary")) is None
        assert _contamination_offset(item.get("beneficiary_text")) is None

    assert _contamination_offset("Testo istituzionale pulito") is None
    assert _contamination_offset("document.getElementById('x')") == 0
    print("Sanificazione contenuti Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
