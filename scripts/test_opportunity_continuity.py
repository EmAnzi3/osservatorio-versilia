#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest
from datetime import date

import reconcile_opportunity_continuity as continuity


URL = "https://cultura.gov.it/comunicato/bando-per-la-promozione-della-musica-jazz-anno-2027-avviso-pubblico-e-apertura-dei-termini-di-presentazione-delle-domande"


def fixtures():
    prior = {
        "rule_id": "mic-jazz-2027",
        "source_id": "mic-spettacolo",
        "title": "Bando per la promozione della musica Jazz 2027",
        "url": URL,
        "deadline_at": "2026-09-10",
        "deadline_time": "16:00",
        "verified_direct": True,
        "quality_gate": {"status": "pass", "missing": [], "reasons": []},
        "eligibility": "conditional",
        "municipality_eligibility": {"Massarosa": {"status": "conditional", "reason": "Autonomia territoriale ammessa."}},
    }
    current = {
        "opportunities": [],
        "continuityHold": [{
            "identity_key": "rule:mic-jazz-2027",
            "title": prior["title"],
            "source_id": prior["source_id"],
            "deadline_at": prior["deadline_at"],
            "url": URL,
        }],
        "counts": {"public": 0, "continuityHold": 1},
        "municipalitySummary": {"Massarosa": {"eligible": 0, "conditional": 0}},
        "sources": [{"sourceId": "mic-spettacolo", "publicCount": 0}],
    }
    previous = {"opportunities": [prior]}
    evidence = {
        "maxEvidenceAgeDays": 7,
        "entries": [{
            "identity_key": "rule:mic-jazz-2027",
            "rule_id": "mic-jazz-2027",
            "source_id": "mic-spettacolo",
            "url": URL,
            "deadline_at": "2026-09-10",
            "evidence_verified_at": "2026-08-23",
            "evidence_url": URL,
        }],
    }
    return current, previous, evidence


class ContinuityReconcileTest(unittest.TestCase):
    def test_recent_verified_item_is_recovered(self):
        current, previous, evidence = fixtures()
        recovered = continuity.reconcile(current, previous, evidence, date(2026, 8, 23))
        self.assertEqual(len(recovered), 1)
        self.assertEqual(current["continuityHold"], [])
        self.assertEqual(current["counts"]["public"], 1)
        self.assertEqual(current["counts"]["continuityHold"], 0)
        self.assertEqual(current["sources"][0]["publicCount"], 1)
        item = current["opportunities"][0]
        self.assertTrue(item["continuity_recovered"])
        self.assertEqual(item["verification_status"], "cached_recent_continuity")
        self.assertEqual(item["lifecycle_stage"], "application_open")
        self.assertEqual(current["municipalitySummary"]["Massarosa"]["conditional"], 1)

    def test_stale_evidence_does_not_recover(self):
        current, previous, evidence = fixtures()
        recovered = continuity.reconcile(copy.deepcopy(current), previous, evidence, date(2026, 9, 1))
        self.assertEqual(recovered, [])
        stale = copy.deepcopy(current)
        continuity.reconcile(stale, previous, evidence, date(2026, 9, 1))
        self.assertEqual(len(stale["continuityHold"]), 1)
        self.assertEqual(stale["opportunities"], [])

    def test_expired_deadline_never_recovers_even_with_fresh_evidence(self):
        current, previous, evidence = fixtures()
        evidence["entries"][0]["evidence_verified_at"] = "2026-09-11"
        recovered = continuity.reconcile(current, previous, evidence, date(2026, 9, 11))
        self.assertEqual(recovered, [])
        self.assertEqual(len(current["continuityHold"]), 1)


if __name__ == "__main__":
    unittest.main()
