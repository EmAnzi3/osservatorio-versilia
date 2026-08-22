#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import run_opportunity_radar_v041 as v04


class RadarV04Test(unittest.TestCase):
    def test_discovery_expansion_covers_new_families(self):
        config, coverage = v04.compose_runtime_payloads()
        discovery_ids = {str(x.get("id")) for x in config.get("discoverySources") or []}
        for required in (
            "pcm-stato-citta", "mic-dgcc", "pcm-politiche-mare", "pcm-sport",
            "mit-enti-locali", "mase-bandi", "cinea-life", "eu-neb",
            "interreg-marittimo", "politiche-coesione", "pa-digitale-current",
            "pcm-famiglia", "pcm-pari-opportunita", "pcm-casa-italia",
            "mic-generale", "eu-funding-tenders",
        ):
            self.assertIn(required, discovery_ids)
            self.assertIn(required, coverage.get("sources") or {})
        self.assertGreaterEqual(len(discovery_ids), 20)

    def test_contract_separates_classifier_recall_from_web_coverage(self):
        contract = v04._load(v04.CONTRACT_V04)
        self.assertTrue(contract["classifierRecallIsNotWebCoverage"])
        self.assertIn("procurement_where_municipality_is_contracting_authority", contract["excludedOpportunityKinds"])
        self.assertIn("supplier_tender", contract["excludedOpportunityKinds"])
        self.assertEqual(set(contract["lifecycleStages"]), {"application_open", "rolling_open", "announced_upcoming"})
        backtest = v04._load(v04.radar.DEFAULT_BACKTEST)
        self.assertIn("non la completezza dell'intero web", backtest.get("scope", ""))

    def test_every_required_family_has_at_least_one_configured_source(self):
        _, coverage = v04.compose_runtime_payloads()
        configured = set((coverage.get("sources") or {}).keys())
        contract = v04._load(v04.CONTRACT_V04)
        self.assertGreaterEqual(len(contract.get("requiredFamilies") or []), 12)
        for family in contract.get("requiredFamilies") or []:
            with self.subTest(family=family.get("id")):
                self.assertTrue(configured.intersection(family.get("sourceIds") or []))

    def test_recent_verified_seed_can_survive_transient_fetch_failure(self):
        entry = (v04._load(v04.VERIFIED_V04).get("entries") or [])[0]
        ok, status, _ = v04.verify_entry(entry, date(2026, 8, 22), live=False, fallback_max_days=7)
        self.assertTrue(ok)
        self.assertEqual(status, "cached_recent")
        ok, status, _ = v04.verify_entry(entry, date(2026, 9, 5), live=False, fallback_max_days=7)
        self.assertFalse(ok)
        self.assertEqual(status, "failed")

    def test_cultura_piccoli_comuni_matrix_is_not_all_towns(self):
        entry = next(x for x in v04._load(v04.VERIFIED_V04)["entries"] if x["coverage_id"] == "mic-cultura-piccoli-comuni-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        matrix = item["municipality_eligibility"]
        self.assertEqual(matrix["Camaiore"]["status"], "not_eligible")
        self.assertEqual(matrix["Viareggio"]["status"], "not_eligible")
        self.assertEqual(matrix["Massarosa"]["status"], "eligible")
        self.assertEqual(item["lifecycle_stage"], "application_open")

    def test_capitale_mare_is_limited_to_coastal_towns(self):
        entry = next(x for x in v04._load(v04.VERIFIED_V04)["entries"] if x["coverage_id"] == "pcm-capitale-mare-2027")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        matrix = item["municipality_eligibility"]
        for town in ("Camaiore", "Forte dei Marmi", "Pietrasanta", "Viareggio"):
            self.assertEqual(matrix[town]["status"], "eligible", town)
        for town in ("Massarosa", "Seravezza", "Stazzema"):
            self.assertEqual(matrix[town]["status"], "not_eligible", town)

    def test_rolling_and_upcoming_are_first_class_states(self):
        entries = {x["coverage_id"]: x for x in v04._load(v04.VERIFIED_V04)["entries"]}
        rolling = v04.build_seed_item(entries["gse-conto-termico-3-2026"], date(2026, 8, 22), "live")
        upcoming = v04.build_seed_item(entries["mit-fondo-piccoli-comuni-2026"], date(2026, 8, 22), "live")
        self.assertEqual(rolling["lifecycle_stage"], "rolling_open")
        self.assertIsNone(rolling["deadline_at"])
        self.assertEqual(upcoming["lifecycle_stage"], "announced_upcoming")
        self.assertFalse(upcoming["actionable_for_municipality"])

    def test_family_small_towns_is_stazzema_only(self):
        entry = next(x for x in v04._load(v04.VERIFIED_EXTRA)["entries"] if x["coverage_id"] == "pcm-famiglia-crescere-piccoli-comuni-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        matrix = item["municipality_eligibility"]
        self.assertEqual(matrix["Stazzema"]["status"], "eligible")
        for town in ("Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Viareggio"):
            self.assertEqual(matrix[town]["status"], "not_eligible", town)

    def test_equal_opportunities_bando_keeps_all_towns_conditional(self):
        entry = next(x for x in v04._load(v04.VERIFIED_EXTRA)["entries"] if x["coverage_id"] == "pcm-pari-tratta-bando-8-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        self.assertTrue(all(row["status"] == "conditional" for row in item["municipality_eligibility"].values()))

    def test_historical_sentinels_cover_sport_interreg_and_resilience(self):
        base_cases = v04._load(v04.SENTINELS_V04).get("cases") or []
        extra_cases = v04._load(v04.SENTINELS_EXTRA).get("cases") or []
        historical = {x.get("source_id") for x in base_cases + extra_cases if x.get("expected") == "historical_monitored"}
        self.assertIn("pcm-sport", historical)
        self.assertIn("interreg-marittimo", historical)
        self.assertIn("pcm-casa-italia", historical)


if __name__ == "__main__":
    unittest.main()
