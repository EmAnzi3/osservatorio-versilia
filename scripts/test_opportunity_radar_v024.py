#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import opportunity_radar_v024 as v024


class OpportunityRadarV024Test(unittest.TestCase):
    def test_extracts_deadline_time_only_for_same_deadline(self):
        item = {
            "deadline_at": "2026-08-31",
            "summary": "Pubblicato il 22.06.2026. Scadenza presentazione domande 31.08.2026 16:00",
        }
        self.assertEqual(v024.extract_deadline_time(item), "16:00")

    def test_presentation_turns_conditional_into_specific_requirement(self):
        registry = {
            "sources": {"s": {"label": "Regione Toscana", "mark": "RT", "class": "regione"}},
            "rules": {"r": {"category": "cultura", "description": "Descrizione", "conditionLabel": "Richiede partenariato"}},
        }
        item = {
            "source_id": "s", "rule_id": "r", "eligibility": "conditional",
            "municipality_role": "partner", "summary": "x", "themes": [],
        }
        enriched = v024.enrich_item(item, registry)
        self.assertEqual(enriched["access_mode"], "specific_requirement")
        self.assertEqual(enriched["presentation"]["condition_label"], "Richiede partenariato")

    def test_archive_keeps_only_expired_missing_previous_opportunities(self):
        previous = {
            "opportunities": [
                {"id": "old", "title": "Bando chiuso", "source_id": "s", "url": "https://x/old", "deadline_at": "2026-08-20", "presentation": {"source_label": "Fonte"}},
                {"id": "active", "title": "Bando attivo", "source_id": "s", "url": "https://x/active", "deadline_at": "2026-08-30", "presentation": {"source_label": "Fonte"}},
            ],
            "archive": [],
        }
        current = [{"id": "active"}]
        archive = v024.merge_archive(current, previous, date(2026, 8, 21))
        self.assertEqual([item["id"] for item in archive], ["old"])

    def test_run_adds_archive_and_presentation(self):
        base = {
            "schemaVersion": "2.2", "referenceDate": "2026-08-21",
            "counts": {"reviewInternal": 0, "qualityHeld": 0}, "sources": [],
            "opportunities": [{
                "id": "one", "source_id": "regione-toscana", "source_name": "Regione Toscana",
                "publisher": "Regione Toscana", "rule_id": "rt-amianto-2026", "title": "Amianto",
                "url": "https://x", "summary": "Scadenza presentazione domande 31.08.2026 16:00",
                "deadline_at": "2026-08-31", "eligibility": "eligible", "themes": ["ambiente"],
            }], "reviewQueue": [], "qualityHold": []
        }
        with patch.object(v024.v022, "run", return_value=base):
            result = v024.run(v024.DEFAULT_CONFIG, date(2026, 8, 21))
        self.assertEqual(result["schemaVersion"], "2.4")
        self.assertEqual(result["opportunities"][0]["deadline_time"], "16:00")
        self.assertEqual(result["opportunities"][0]["presentation"]["source_mark"], "RT")
        self.assertEqual(result["counts"]["archive"], 0)


if __name__ == "__main__":
    unittest.main()
