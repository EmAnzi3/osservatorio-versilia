#!/usr/bin/env python3
from __future__ import annotations

import unittest
from datetime import date, timedelta

import run_opportunity_radar_v043 as v043


class RadarV043Test(unittest.TestCase):
    def test_residual_sources_are_configured(self):
        config, coverage = v043.compose_runtime_payloads()
        discovery = {str(x.get("id")) for x in config.get("discoverySources") or []}
        expected = {
            "eu-urbact", "eu-eui", "eu-eucf", "eu-erasmus", "eu-cef", "eu-horizon",
            "eu-digital", "interreg-europe", "dara-montagna", "protezione-civile",
            "masaf-bandi", "toscana-csr-artea-leader",
        }
        self.assertTrue(expected.issubset(discovery))
        self.assertTrue(expected.issubset(set((coverage.get("sources") or {}).keys())))
        # 38: la fonte ANCI nazionale è stata tolta perché irraggiungibile dalla CI (ce84d64e); i lead ANCI arrivano da ANCI Toscana.
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
        evidence = v043._load(v043.EVIDENCE_V043)
        audit = v043._residual_evidence_audit(result, date.fromisoformat(evidence["referenceDate"]))
        self.assertEqual(audit["status"], "pass")
        self.assertEqual(audit["sourcesVerified"], 12)
        self.assertEqual(audit["sourcesExpected"], 12)
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
        evidence = v043._load(v043.EVIDENCE_V043)
        latest = max(date.fromisoformat(x["evidence_verified_at"]) for x in evidence["entries"])
        audit = v043._residual_evidence_audit(result, latest + timedelta(days=evidence["maxEvidenceAgeDays"] + 1))
        self.assertEqual(audit["status"], "fail")
        self.assertEqual(len(audit["staleEvidence"]), 12)

    def test_active_source_renews_residual_evidence_silent_one_does_not(self):
        _, coverage = v043.compose_runtime_payloads()
        evidence = v043._load(v043.EVIDENCE_V043)
        late = date.fromisoformat(evidence["referenceDate"]) + timedelta(days=evidence["maxEvidenceAgeDays"] + 1)
        silent = {"eu-erasmus", "eu-cef", "eu-horizon"}
        rows = []
        for source_id in coverage.get("sources") or {}:
            if source_id in silent:
                rows.append({"source_id": source_id, "runtimeStatus": "ok", "candidateCount": 0})
            else:
                rows.append({"source_id": source_id, "runtimeStatus": "ok", "candidateCount": 2})
        audit = v043._residual_evidence_audit({"sourceCoverage": {"rows": rows}}, late)
        self.assertEqual(audit["status"], "fail")
        self.assertEqual(set(audit["staleEvidence"]), silent)
        renewed = {r["source_id"] for r in audit["rows"] if r["renewedByRuntime"]}
        self.assertEqual(len(renewed), 9)
        failed = [dict(r, runtimeStatus="failed") for r in rows]
        self.assertEqual(len(v043._residual_evidence_audit({"sourceCoverage": {"rows": failed}}, late)["staleEvidence"]), 12)

    def test_evidence_page_read_today_renews_silent_sources(self):
        """Erasmus+, CEF e Horizon sorvegliano la pagina della prova: letta con successo oggi, la prova è rinnovata."""
        import opportunity_discovery_resilient as discovery
        _, coverage = v043.compose_runtime_payloads()
        evidence = v043._load(v043.EVIDENCE_V043)
        late = date.fromisoformat(evidence["referenceDate"]) + timedelta(days=evidence["maxEvidenceAgeDays"] + 1)
        by_id = {e["source_id"]: e for e in evidence["entries"]}
        silent = {"eu-erasmus", "eu-cef", "eu-horizon"}
        rows = [{"source_id": s, "runtimeStatus": "ok", "candidateCount": 0 if s in silent else 2} for s in coverage.get("sources") or {}]
        saved = dict(discovery.FETCH_TRACE)
        try:
            discovery.FETCH_TRACE.clear()
            for s in silent:
                # Erasmus+: URL configurato diverso, URL finale = pagina della prova.
                discovery.FETCH_TRACE["https://configured/" + s] = {"url": "https://configured/" + s, "status": "ok",
                                                                    "resolvedUrl": by_id[s]["evidence_url"]}
            audit = v043._residual_evidence_audit({"sourceCoverage": {"rows": rows}}, late)
            self.assertEqual(audit["status"], "pass", audit["staleEvidence"])
            self.assertEqual({r["source_id"] for r in audit["rows"] if r["renewedBy"] == "evidence_page"}, silent)
            # Pagina letta con errore, o fonte in errore: nessun rinnovo.
            for s in silent:
                discovery.FETCH_TRACE["https://configured/" + s]["status"] = "error"
            self.assertEqual(set(v043._residual_evidence_audit({"sourceCoverage": {"rows": rows}}, late)["staleEvidence"]), silent)
            for s in silent:
                discovery.FETCH_TRACE["https://configured/" + s]["status"] = "ok"
            failed = [dict(r, runtimeStatus="failed") if r["source_id"] in silent else r for r in rows]
            self.assertEqual(set(v043._residual_evidence_audit({"sourceCoverage": {"rows": failed}}, late)["staleEvidence"]), silent)
        finally:
            discovery.FETCH_TRACE.clear()
            discovery.FETCH_TRACE.update(saved)

    def test_every_residual_source_has_official_evidence(self):
        source_ids = set()
        for discovery in v043._discovery_layers():
            source_ids.update(str(x.get("id")) for x in discovery.get("discoverySources") or [])
        evidence = v043._load(v043.EVIDENCE_V043)
        evidence_by_source = {str(x.get("source_id")): x for x in evidence.get("entries") or []}
        self.assertEqual(source_ids, set(evidence_by_source))
        for source_id, row in evidence_by_source.items():
            with self.subTest(source_id=source_id):
                self.assertTrue(str(row.get("evidence_url") or "").startswith("https://"))
                verified = date.fromisoformat(str(row.get("evidence_verified_at") or ""))
                self.assertLessEqual(verified, date.fromisoformat(evidence["referenceDate"]))
                self.assertGreaterEqual(verified, date.fromisoformat(evidence["referenceDate"]) - timedelta(days=evidence["maxEvidenceAgeDays"]))

    def test_eui_city_to_city_is_verified_after_degurb_check(self):
        entry = next(
            x for x in v043._load(v043.VERIFIED_V043).get("entries") or []
            if x.get("coverage_id") == "eu-eui-city-to-city-exchanges-2026"
        )
        item = v043.build_seed_item(entry, date(2026, 8, 23), "live")
        self.assertEqual(item["lifecycle_stage"], "rolling_open")
        self.assertIsNone(item["deadline_at"])
        for town in ("Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Viareggio"):
            self.assertEqual(item["municipality_eligibility"][town]["status"], "conditional", town)
        self.assertEqual(item["municipality_eligibility"]["Stazzema"]["status"], "not_eligible")

    def test_eucf_eighth_call_is_upcoming_for_all_towns_conditionally(self):
        entry = next(
            x for x in v043._load(v043.VERIFIED_V043).get("entries") or []
            if x.get("coverage_id") == "eu-eucf-call-8-2026"
        )
        item = v043.build_seed_item(entry, date(2026, 8, 23), "live")
        self.assertEqual(item["lifecycle_stage"], "announced_upcoming")
        self.assertIsNone(item["deadline_at"])
        self.assertFalse(item["actionable_for_municipality"])
        self.assertTrue(all(row["status"] == "conditional" for row in item["municipality_eligibility"].values()))

    def test_current_broad_eu_calls_stay_in_review_until_municipal_fit_is_proven(self):
        cases = v043._load(v043.SENTINELS_V043).get("cases") or []
        review = {str(x.get("source_id")): x for x in cases if x.get("expected") == "audit_review"}
        for source_id in ("eu-cef", "eu-erasmus", "eu-horizon", "protezione-civile", "masaf-bandi"):
            self.assertIn(source_id, review)
        current = {str(x.get("source_id")): x for x in cases if x.get("expected") == "current"}
        self.assertIn("eu-eui", current)
        self.assertIn("eu-eucf", current)
        self.assertEqual(current["eu-eui"].get("lifecycle_stage"), "rolling_open")
        self.assertEqual(current["eu-eucf"].get("lifecycle_stage"), "announced_upcoming")
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
