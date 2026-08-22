#!/usr/bin/env python3
from __future__ import annotations

import re
import unittest
from datetime import date

import build_opportunity_preview_v04 as preview
import run_opportunity_radar_v042 as v04


class OpportunityPreviewV04Test(unittest.TestCase):
    def _payload(self):
        entries = v04._load(v04.VERIFIED_V04).get("entries") or []
        wanted = (
            "mic-cultura-piccoli-comuni-2026",
            "gse-conto-termico-3-2026",
            "mit-fondo-piccoli-comuni-2026",
        )
        by_id = {x["coverage_id"]: x for x in entries}
        items = [v04.build_seed_item(by_id[key], date(2026, 8, 22), "live") for key in wanted]
        return {
            "referenceDate": "2026-08-22",
            "opportunities": items,
            "archive": [],
            "sourceCoverage": {"rows": [], "summary": {"configured": 35, "active": 34, "degraded": 1}},
            "coverageAudit": {"requiredFamilies": 18, "missingFamilies": []},
            "independentAudit": {
                "knownGapClosure": {"closed": 3, "total": 3},
                "prospective": {"sampleSize": 0, "minimumSample": 20, "captureRate": None},
                "holdouts": {"configured": 3, "healthy": 2},
            },
            "lifecycleSummary": {"application_open": 1, "rolling_open": 1, "announced_upcoming": 1},
        }

    def test_render_exposes_three_lifecycle_states(self):
        page = preview.render_page(self._payload())
        self.assertIn("Anteprima v0.4.2", page)
        self.assertIn('data-op-lifecycle', page)
        for stage in ("application_open", "rolling_open", "announced_upcoming"):
            self.assertIn(f'data-lifecycle="{stage}"', page)
        self.assertIn("A sportello", page)
        self.assertIn("In arrivo", page)
        self.assertEqual(len(re.findall(r'class="op-stat(?:\s|\")', page)), 6)

    def test_render_replaces_source_buffets_with_compact_audit_summary(self):
        page = preview.render_page(self._payload())
        self.assertIn("Audit indipendente", page)
        self.assertIn("3/3 buchi baseline chiusi", page)
        self.assertIn("18/18", page)
        self.assertNotIn("op-monitor-list", page)
        self.assertNotIn("op-monitor-source", page)
        self.assertNotIn("data-op-source-quick", page)
        self.assertIn("data-op-source", page)

    def test_render_uses_single_v04_filter_script(self):
        page = preview.render_page(self._payload())
        self.assertIn("opportunity-preview-v04.js", page)
        self.assertNotIn('src="../assets/opportunity-preview.js"', page)
        self.assertNotIn('src="../assets/opportunity-preview-v03.js"', page)

    def test_internal_quality_terms_remain_hidden(self):
        page = preview.render_page(self._payload())
        for token in ("Quality gate", "discoveryQueue", "coverageHold", ">Da verificare<"):
            self.assertNotIn(token, page)


if __name__ == "__main__":
    unittest.main()
