#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import run_opportunity_radar_v043 as v043


class RadarV043Test(unittest.TestCase):
    def test_residual_sources_are_configured(self):
        config, coverage = v043.compose_runtime_payloads()
        discovery = {str(x.get("id")) for x in config.get("discoverySources") or []}
        expected = {
            "eu-urbact", "eu-eui", "eu-erasmus", "eu-cef", "eu-horizon",
            "eu-digital", "interreg-europe", "dara-montagna", "protezione-civile",
            "masaf-bandi", "toscana-csr-artea-leader",
        }
        self.assertTrue(expected.issubset(discovery))
        self.assertTrue(expected.issubset(set((coverage.get("sources") or {}).keys())))
        self.assertGreaterEqual(len(discovery), 38)

    def test_contract_has_explicit_european_subfamilies(self):
        contract = v043._load(v043.CONTRACT_V04)
        families = {str(x.get("id")) for x in contract.get("requiredFamilies") or []}
        self.assertGreaterEqual(len(families), 25)
        for family in (
            "eu-urban", "eu-education-youth", "eu-infrastructure-connectivity",
            "eu-research-innovation", "eu-digital", "mountain-territories",
            "rural-territorial-development",
        ):
            self.assertIn(family, families)
        self.assertTrue(contract["publicationRules"]["programmePortfolioCannotPublishAlone"])

    def test_residual_evidence_is_not_just_configuration(self):
        _, coverage = v043.compose_runtime_payloads()
        result = {
            "sourceCoverage": {
                "rows": [{"source_id": source_id} for source_id in (coverage.get("sources") or {})]
            }
        }
        audit = v043._residual_evidence_audit(result, date(2026, 8, 22))
        self.assertEqual(audit["status"], "pass")
        self.assertEqual(audit["sourcesVerified"], 11)
        self.assertEqual(audit["sourcesExpected"], 11)
        self.assertGreaterEqual(audit["familiesVerified"], 9)
        self.assertEqual(audit["missingSources"], [])
        self.assertEqual(audit["staleEvidence"], [])

    def test_residual_evidence_expires_instead_of_becoming_permanent_truth(self):
        _, coverage = v043.compose_runtime_payloads()
        result = {
            "sourceCoverage": {
                "rows": [{"source_id": source_id} for source_id in (coverage.get("sources") or {})]
            }
        }
        audit = v043._residual_evidence_audit(result, date(2026, 11, 1))
        self.assertEqual(audit["status"], "fail")
        self.assertEqual(len(audit["staleEvidence"]), 11)

    def test_every_residual_source_has_official_evidence(self):
        discovery = v043._load(v043.DISCOVERY_V043)
        evidence = v043._load(v043.EVIDENCE_V043)
        source_ids = {str(x.get("id")) for x in discovery.get("discoverySources") or []}
        evidence_by_source = {str(x.get("source_id")): x for x in evidence.get("entries") or []}
        self.assertEqual(source_ids, set(evidence_by_source))
        for source_id, row in evidence_by_source.items():
            with self.subTest(source_id=source_id):
                self.assertTrue(str(row.get("evidence_url") or "").startswith("https://"))
                self.assertEqual(row.get("evidence_verified_at"), "2026-08-22")

    def test_current_broad_eu_calls_stay_in_review_until_municipal_fit_is_proven(self):
        cases = v043._load(v043.SENTINELS_V043).get("cases") or []
        review = {str(x.get("source_id")): x for x in cases if x.get("expected") == "audit_review"}
        for source_id in ("eu-eui", "eu-cef", "eu-erasmus", "eu-horizon", "protezione-civile", "masaf-bandi"):
            self.assertIn(source_id, review)
        self.assertEqual(review["eu-eui"].get("lifecycle_stage"), "rolling_open")
        self.assertEqual(review["eu-cef"].get("deadline_at"), "2026-10-06")

    def test_historical_sentinels_cover_programmes_that_closed_before_v043(self):
        cases = v043._load(v043.SENTINELS_V043).get("cases") or []
        historical = {str(x.get("source_id")) for x in cases if x.get("expected") == "historical_monitored"}
        for source_id in ("eu-urbact", "eu-eui", "eu-digital", "toscana-csr-artea-leader"):
            self.assertIn(source_id, historical)

    def test_start_procurement_remains_outside_opportunity_contract(self):
        contract = v043._load(v043.CONTRACT_V04)
        excluded = set(contract.get("excludedOpportunityKinds") or [])
        self.assertIn("procurement_where_municipality_is_contracting_authority", excluded)
        self.assertIn("supplier_tender", excluded)
        discovery = {str(x.get("id")) for x in v043.compose_runtime_payloads()[0].get("discoverySources") or []}
        self.assertNotIn("start-toscana", discovery)


if __name__ == "__main__":
    unittest.main()
