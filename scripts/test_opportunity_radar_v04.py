#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date

import run_opportunity_radar_v042 as v04


class RadarV04Test(unittest.TestCase):
    def test_discovery_expansion_covers_new_families(self):
        config, coverage = v04.compose_runtime_payloads()
        discovery_ids = {str(x.get("id")) for x in config.get("discoverySources") or []}
        for required in (
            "pcm-stato-citta", "mic-dgcc", "pcm-politiche-mare", "pcm-sport",
            "mit-enti-locali", "mase-bandi", "cinea-life", "eu-neb",
            "interreg-marittimo", "politiche-coesione", "pa-digitale-current",
            "pcm-famiglia", "pcm-pari-opportunita", "pcm-casa-italia",
            "mic-generale", "eu-funding-tenders", "pcm-disabilita",
            "ministero-turismo", "pcm-politiche-giovanili-scu",
            "mlps-social-services", "mim-enti-locali", "funzione-pubblica", "eu-cerv",
        ):
            self.assertIn(required, discovery_ids)
            self.assertIn(required, coverage.get("sources") or {})
        self.assertGreaterEqual(len(discovery_ids), 27)

    def test_holdouts_do_not_feed_production(self):
        config, _ = v04.compose_runtime_payloads()
        production = {str(x.get("id")) for x in config.get("discoverySources") or []}
        audit = v04._load(v04.INDEPENDENT_AUDIT_V042)
        holdouts = {str(x.get("id")) for x in audit.get("holdoutSources") or []}
        self.assertTrue(holdouts)
        self.assertFalse(production.intersection(holdouts))

    def test_parallel_discovery_preserves_candidate_semantics(self):
        config = {
            "discoverySources": [
                {"id":"alpha","label":"Alpha","urls":["https://example.test/a","https://example.test/b"],"includeTerms":["bando"],"municipalTerms":["comune"]},
                {"id":"beta","label":"Beta","urls":["https://example.test/c"],"includeTerms":["avviso"],"municipalTerms":["enti locali"]},
            ]
        }
        payloads = {
            "https://example.test/a": '<article><a href="/uno">Bando Comune Uno</a><p>Contributo al Comune</p></article>',
            "https://example.test/b": '<article><a href="/due">Bando Comune Due</a><p>Finanziamento al Comune</p></article>',
            "https://example.test/c": '<article><a href="/tre">Avviso Enti locali</a><p>Opportunità per enti locali</p></article>',
        }
        queue, states = v04.prev.probe_discovery_sources(config, payloads=payloads)
        self.assertEqual([x["sourceId"] for x in states], ["alpha", "beta"])
        self.assertTrue(all(x["status"] == "ok" for x in states))
        self.assertGreaterEqual(len(queue), 3)

    def test_contract_separates_classifier_recall_from_web_coverage(self):
        contract = v04._load(v04.CONTRACT_V04)
        self.assertTrue(contract["classifierRecallIsNotWebCoverage"])
        self.assertIn("procurement_where_municipality_is_contracting_authority", contract["excludedOpportunityKinds"])
        self.assertIn("supplier_tender", contract["excludedOpportunityKinds"])
        self.assertIn("operational_opportunity", contract["acceptedOpportunityKinds"])
        self.assertEqual(set(contract["lifecycleStages"]), {"application_open", "rolling_open", "announced_upcoming"})
        backtest = v04._load(v04.radar.DEFAULT_BACKTEST)
        self.assertIn("non la completezza dell'intero web", backtest.get("scope", ""))

    def test_every_required_family_has_at_least_one_configured_source(self):
        _, coverage = v04.compose_runtime_payloads()
        configured = set((coverage.get("sources") or {}).keys())
        contract = v04._load(v04.CONTRACT_V04)
        self.assertGreaterEqual(len(contract.get("requiredFamilies") or []), 18)
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

    def test_vita_opportunita_distinguishes_stazzema_from_partner_role(self):
        entry = next(x for x in v04._load(v04.VERIFIED_V042)["entries"] if x["coverage_id"] == "pcm-disabilita-vita-opportunita-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        self.assertEqual(item["municipality_eligibility"]["Stazzema"]["status"], "eligible")
        self.assertEqual(item["municipality_eligibility"]["Massarosa"]["status"], "conditional")
        self.assertEqual(item["deadline_time"], "17:00")

    def test_cerv_town_twinning_requires_transnational_partnership(self):
        entry = next(x for x in v04._load(v04.VERIFIED_V042)["entries"] if x["coverage_id"] == "eu-cerv-town-twinning-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        self.assertTrue(all(row["status"] == "conditional" for row in item["municipality_eligibility"].values()))
        self.assertIn("due Paesi", item["project_requirements"])

    def test_mlps_social_workers_is_operational_opportunity_for_all_towns(self):
        entry = next(x for x in v04._load(v04.VERIFIED_V042)["entries"] if x["coverage_id"] == "mlps-assistenti-sociali-2026")
        item = v04.build_seed_item(entry, date(2026, 8, 22), "live")
        self.assertTrue(all(row["status"] == "conditional" for row in item["municipality_eligibility"].values()))
        self.assertEqual(item["deadline_at"], "2026-09-11")

    def test_scu_stays_in_audit_review_not_public_verified(self):
        verified_titles = {x.get("title") for x in v04._load(v04.VERIFIED_V042).get("entries") or []}
        self.assertNotIn("Servizio civile universale — programmi e progetti 2026", verified_titles)
        review = [x for x in v04._load(v04.SENTINELS_V042).get("cases") or [] if x.get("expected") == "audit_review"]
        self.assertEqual(len(review), 1)

    def test_independent_audit_closes_known_gaps_without_faking_kpi(self):
        ids = ["pcm-disabilita-vita-opportunita-2026", "eu-cerv-town-twinning-2026", "mlps-assistenti-sociali-2026"]
        result = {"opportunities": [{"coverage_id": x} for x in ids], "archive": []}
        audit = v04.build_independent_audit(result, live=False)
        self.assertEqual(audit["status"], "pass")
        self.assertEqual(audit["baselinePreFix"]["capturedByRadar"], 0)
        self.assertEqual(audit["baselinePreFix"]["missedByRadar"], 3)
        self.assertFalse(audit["baselineRepresentative"])
        self.assertEqual(audit["knownGapClosure"]["closed"], 3)
        self.assertEqual(audit["knownGapClosure"]["total"], 3)
        self.assertEqual(audit["prospective"]["status"], "pending_minimum_sample")
        self.assertIsNone(audit["prospective"]["captureRate"])
        self.assertFalse(audit["holdouts"]["feedsProduction"])

    def test_independent_audit_fails_when_known_gap_is_still_missing(self):
        result = {"opportunities": [{"coverage_id": "pcm-disabilita-vita-opportunita-2026"}], "archive": []}
        audit = v04.build_independent_audit(result, live=False)
        self.assertEqual(audit["status"], "fail")
        self.assertEqual(len(audit["knownGapClosure"]["missing"]), 2)

    def test_historical_sentinels_cover_sport_interreg_resilience_and_new_families(self):
        cases = []
        for path in (v04.SENTINELS_V04, v04.SENTINELS_EXTRA, v04.SENTINELS_V042):
            cases.extend(v04._load(path).get("cases") or [])
        historical = {x.get("source_id") for x in cases if x.get("expected") == "historical_monitored"}
        for expected in ("pcm-sport", "interreg-marittimo", "pcm-casa-italia", "ministero-turismo", "mim-enti-locali", "funzione-pubblica"):
            self.assertIn(expected, historical)

    def test_final_continuity_drops_v04_items_recovered_after_base_run(self):
        result = {
            "opportunities": [{"rule_id":"coverage:mic-cultura-piccoli-comuni-2026","source_id":"mic-dgcc","title":"Cultura nei piccoli comuni — Edizione 1","url":"https://example.test/cultura"}],
            "continuityHold": [
                {"identity_key":"rule:coverage:mic-cultura-piccoli-comuni-2026","title":"Cultura nei piccoli comuni — Edizione 1"},
                {"identity_key":"rule:still-missing","title":"Caso realmente assente"},
            ],
            "counts": {"continuityHold": 2},
        }
        v04.prev._reconcile_v04_continuity(result)
        self.assertEqual(len(result["continuityHold"]), 1)
        self.assertEqual(result["continuityHold"][0]["identity_key"], "rule:still-missing")


if __name__ == "__main__":
    unittest.main()
