#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import opportunity_radar_v022 as radar

TODAY = date(2026, 8, 21)
PROFILES = {
    "Camaiore": {"province": "Lucca", "toscanaDiffusa": "partial"},
    "Forte dei Marmi": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Massarosa": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Pietrasanta": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Seravezza": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Stazzema": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Viareggio": {"province": "Lucca", "toscanaDiffusa": "no"},
}


def candidate(title: str, eligibility: str = "review", source_id: str = "regione-toscana") -> dict:
    return {
        "id": "test-item",
        "source_id": source_id,
        "source_name": "Regione Toscana",
        "publisher": "Regione Toscana",
        "title": title,
        "url": "https://example.test/bando",
        "summary": "",
        "deadline_at": "2026-09-30",
        "beneficiary_text": "",
        "eligibility": eligibility,
        "eligibility_reason": "Da verificare",
        "themes": ["opere-pubbliche"],
        "priority": "low",
    }


class OpportunityRadarV022Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rules, policy = radar.load_policy()
        radar.v021.ACTIVE_RULES = rules
        radar.ACTIVE_POLICY = policy

    def setUp(self) -> None:
        radar.v021.RULE_STATS = {}
        radar.V022_STATS = {}

    def test_overlay_keeps_base_rules_and_updates_buoni_deadline(self) -> None:
        rules, _ = radar.load_policy()
        by_id = {rule["id"]: rule for rule in rules}
        self.assertIn("rt-amianto-2026", by_id)
        self.assertEqual(by_id["rt-buoni-scuola-2026"]["deadline_override"], "2026-09-25")
        self.assertTrue(by_id["rt-buoni-scuola-2026"]["_v022"])

    def test_buoni_scuola_gets_documented_deadline(self) -> None:
        item = candidate('Contributi per la frequenza delle scuole paritarie dell\'infanzia 3-6 anni: bando "Buoni scuola anno 2026"', eligibility="eligible")
        item["deadline_at"] = None
        resolved = radar.resolve_municipalities(item, PROFILES, TODAY)
        self.assertEqual(resolved["deadline_at"], "2026-09-25")
        self.assertEqual(resolved["municipality_role"], "implementing_body")

    def test_toscanaincontemporanea_is_promoted_as_conditional(self) -> None:
        resolved = radar.resolve_municipalities(candidate("Toscanaincontemporanea 2026"), PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "conditional")
        self.assertEqual(resolved["municipality_role"], "direct_applicant")
        self.assertTrue(resolved["actionable_for_municipality"])
        self.assertTrue(all(entry["status"] == "conditional" for entry in resolved["municipality_eligibility"].values()))

    def test_forest_resources_are_conditional_on_asset_title(self) -> None:
        resolved = radar.resolve_municipalities(
            candidate("Risorse genetiche forestali, contributi per conservazione, uso e sviluppo sostenibile: il bando 2026"),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["eligibility"], "conditional")
        self.assertEqual(resolved["decision_class"], "conditional_asset_holder")
        self.assertIn("titolarità", resolved["project_requirements"])

    def test_museum_system_uses_indirect_municipality_map(self) -> None:
        resolved = radar.resolve_municipalities(candidate("Bando Sistemi museali 2026"), PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "conditional")
        self.assertEqual(resolved["applicant_eligibility"], "not_direct_applicant")
        self.assertEqual(resolved["municipality_role"], "system_member")
        self.assertEqual(resolved["municipality_eligibility"]["Forte dei Marmi"]["status"], "not_eligible")
        self.assertEqual(resolved["municipality_eligibility"]["Massarosa"]["status"], "conditional")
        self.assertNotIn("Forte dei Marmi", resolved["municipalities"])

    def test_non_financial_award_is_not_operational(self) -> None:
        resolved = radar.resolve_municipalities(candidate("Premio Impresa più sicura 2026"), PROFILES, TODAY)
        self.assertEqual(resolved["applicant_eligibility"], "eligible")
        self.assertEqual(resolved["eligibility"], "not_relevant")
        self.assertEqual(resolved["opportunity_type"], "non_financial_award")
        self.assertFalse(resolved["actionable_for_municipality"])

    def test_implementation_deadline_is_not_new_application_deadline(self) -> None:
        resolved = radar.resolve_municipalities(
            candidate("Sostegno a progetti di produzione di spettacolo dal vivo 2026"),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["eligibility"], "not_relevant")
        self.assertEqual(resolved["lifecycle_stage"], "implementation_only")
        self.assertEqual(resolved["exclusion_code"], "application_closed")

    def test_wrong_applicant_review_is_suppressed(self) -> None:
        resolved = radar.resolve_municipalities(candidate("Bando aiuti per le sentinelle Blue Tongue"), PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "not_relevant")
        self.assertEqual(resolved["municipality_role"], "none")
        self.assertEqual(resolved["exclusion_code"], "wrong_applicant")

    def test_quality_gate_holds_missing_deadline(self) -> None:
        item = self._quality_ready_item()
        item["deadline_at"] = None
        gate = radar._quality_gate(item, self._current_source(), radar.ACTIVE_POLICY, TODAY)
        self.assertEqual(gate["status"], "hold")
        self.assertIn("deadline_at", gate["missing"])

    def test_quality_gate_holds_stale_source(self) -> None:
        item = self._quality_ready_item()
        source = self._current_source()
        source["freshness"]["status"] = "stale"
        gate = radar._quality_gate(item, source, radar.ACTIVE_POLICY, TODAY)
        self.assertEqual(gate["status"], "hold")
        self.assertTrue(any("fonte non current" in reason for reason in gate["reasons"]))

    def test_quality_gate_accepts_documented_indirect_role(self) -> None:
        item = self._quality_ready_item()
        item["applicant_eligibility"] = "not_direct_applicant"
        item["municipality_role"] = "system_member"
        item["eligibility"] = "conditional"
        item["project_requirements"] = "La domanda è presentata dal Sistema Museale."
        gate = radar._quality_gate(item, self._current_source(), radar.ACTIVE_POLICY, TODAY)
        self.assertEqual(gate["status"], "pass")

    @staticmethod
    def _current_source() -> dict:
        return {"freshness": {"status": "current"}}

    @staticmethod
    def _quality_ready_item() -> dict:
        return {
            "rule_id": "test-rule",
            "eligibility": "eligible",
            "applicant_eligibility": "eligible",
            "municipality_role": "direct_applicant",
            "geographic_scope": "Toscana",
            "geographic_eligibility": "eligible",
            "territorial_relevance": "direct",
            "eligibility_evidence": {"source_url": "https://example.test/atto"},
            "deadline_at": "2026-09-30",
            "actionable_for_municipality": True,
            "municipality_eligibility": {
                "Massarosa": {"status": "eligible", "reason": "test"}
            },
            "project_requirements": None,
        }


if __name__ == "__main__":
    unittest.main()
