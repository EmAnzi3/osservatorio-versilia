#!/usr/bin/env python3
from __future__ import annotations

import re
import unittest
from datetime import date

import build_opportunity_preview_v04 as preview
import run_opportunity_radar_v04 as v04


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
            "sourceCoverage": {
                "rows": [],
                "summary": {"configured": 23, "active": 22, "degraded": 1},
            },
            "coverageAudit": {"requiredFamilies": 10, "missingFamilies": []},
            "lifecycleSummary": {
                "application_open": 1,
                "rolling_open": 1,
                "announced_upcoming": 1,
            },
        }

    def test_render_exposes_three_lifecycle_states(self):
        page = preview.render_page(self._payload())
        self.assertIn("Anteprima v0.4", page)
        self.assertIn('data-op-lifecycle', page)
        for stage in ("application_open", "rolling_open", "announced_upcoming"):
            self.assertIn(f'data-lifecycle="{stage}"', page)
        self.assertIn("A sportello", page)
        self.assertIn("In arrivo", page)
        self.assertEqual(len(re.findall(r'class="op-stat(?:\s|\")', page)), 6)

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
