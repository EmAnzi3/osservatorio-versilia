#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import opportunity_radar_v021 as radar

PROFILES = {
    "Camaiore": {"province": "Lucca", "toscanaDiffusa": "partial"},
    "Forte dei Marmi": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Massarosa": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Pietrasanta": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Seravezza": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Stazzema": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Viareggio": {"province": "Lucca", "toscanaDiffusa": "no"},
}
TODAY = date(2026, 8, 21)


def item(title: str, eligibility: str = "review", beneficiary: str = "") -> dict:
    return {
        "id": "opp-test",
        "source_id": "regione-toscana",
        "source_name": "Regione Toscana",
        "publisher": "Regione Toscana",
        "title": title,
        "url": "https://example.test/bando",
        "summary": "",
        "deadline_at": "2026-11-30",
        "beneficiary_text": beneficiary,
        "eligibility": eligibility,
        "eligibility_reason": "Motivazione base",
        "themes": ["opere-pubbliche"],
        "priority": "low",
    }


class OpportunityRadarV021Test(unittest.TestCase):
    def test_parcheggi_is_promoted_from_review(self) -> None:
        resolved = radar.resolve_municipalities(item("Bando parcheggi 2026"), PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "eligible")
        self.assertEqual(resolved["applicant_eligibility"], "eligible")
        self.assertEqual(resolved["municipality_role"], "direct_applicant")
        self.assertTrue(resolved["actionable_for_municipality"])
        self.assertTrue(all(v["status"] == "eligible" for v in resolved["municipality_eligibility"].values()))

    def test_biotrituratori_is_suppressed_by_role_and_geography(self) -> None:
        resolved = radar.resolve_municipalities(
            item(
                "Bando biotrituratori elettrici 2026",
                eligibility="eligible",
                beneficiary="Contributi nei Comuni della Piana lucchese",
            ),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["eligibility"], "not_relevant")
        self.assertEqual(resolved["applicant_eligibility"], "not_eligible")
        self.assertEqual(resolved["municipality_role"], "none")
        self.assertEqual(resolved["geographic_eligibility"], "not_eligible")
        self.assertFalse(resolved["actionable_for_municipality"])

    def test_celebration_without_versilia_nexus_is_not_operational(self) -> None:
        resolved = radar.resolve_municipalities(
            item(
                "Sostegno a progetti dedicati a San Francesco, Collodi e Alluvione di Firenze",
                eligibility="eligible",
                beneficiary="Comuni toscani",
            ),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["applicant_eligibility"], "eligible")
        self.assertEqual(resolved["eligibility"], "not_relevant")
        self.assertEqual(resolved["territorial_relevance"], "none")
        self.assertFalse(resolved["versilia_nexus"])

    def test_celebration_can_reemerge_with_documented_versilia_nexus(self) -> None:
        candidate = item(
            "Sostegno a progetti dedicati a San Francesco, Collodi e Alluvione di Firenze",
            eligibility="eligible",
            beneficiary="Comuni toscani",
        )
        candidate["summary"] = "Progetto documentato nel Comune di Viareggio."
        resolved = radar.resolve_municipalities(candidate, PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "eligible")
        self.assertEqual(resolved["territorial_relevance"], "conditional")
        self.assertTrue(resolved["versilia_nexus"])
        self.assertTrue(resolved["actionable_for_municipality"])

    def test_buoni_scuola_distinguishes_implementer_from_final_beneficiary(self) -> None:
        resolved = radar.resolve_municipalities(
            item('Contributi per la frequenza delle scuole paritarie dell\'infanzia 3-6 anni: bando "Buoni scuola anno 2026"'),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["municipality_role"], "implementing_body")
        self.assertIn("famiglie", resolved["final_beneficiaries"])
        self.assertEqual(resolved["eligibility"], "eligible")

    def test_housing_manifestation_is_promoted_as_conditional(self) -> None:
        resolved = radar.resolve_municipalities(
            item("Manifestazione di interesse per il reperimento di patrimonio immobiliare da destinare ad emergenza abitativa e/o residenza sociale"),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["eligibility"], "conditional")
        self.assertEqual(resolved["municipality_role"], "direct_applicant")
        self.assertIn("beni confiscati", resolved["project_requirements"])

    def test_progett_azioni_keeps_partnership_role(self) -> None:
        candidate = item("Bando 2026 Progett-Azioni", eligibility="conditional", beneficiary="Partnership di soggetti pubblici e privati")
        candidate["source_id"] = "fondazione-cr-lucca"
        resolved = radar.resolve_municipalities(candidate, PROFILES, TODAY)
        self.assertEqual(resolved["eligibility"], "conditional")
        self.assertEqual(resolved["municipality_role"], "partner")
        self.assertTrue(resolved["partnership_required"])

    def test_unruled_generic_eligible_case_returns_to_internal_review(self) -> None:
        resolved = radar.resolve_municipalities(
            item("Nuovo bando generico per Comuni", eligibility="eligible", beneficiary="Comuni toscani"),
            PROFILES,
            TODAY,
        )
        self.assertEqual(resolved["applicant_eligibility"], "eligible")
        self.assertEqual(resolved["eligibility"], "review")
        self.assertEqual(resolved["municipality_role"], "unknown")
        self.assertFalse(resolved["actionable_for_municipality"])


if __name__ == "__main__":
    unittest.main()
