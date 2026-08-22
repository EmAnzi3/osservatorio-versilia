#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import opportunity_radar_v02 as radar


TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]
PROFILES = {
    "Camaiore": {"province": "Lucca", "toscanaDiffusa": "partial"},
    "Forte dei Marmi": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Massarosa": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Pietrasanta": {"province": "Lucca", "toscanaDiffusa": "no"},
    "Seravezza": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Stazzema": {"province": "Lucca", "toscanaDiffusa": "full"},
    "Viareggio": {"province": "Lucca", "toscanaDiffusa": "no"},
}


def item(title: str, eligibility: str = "eligible", beneficiary: str = "Comuni") -> dict:
    return {
        "id": "opp-test",
        "source_id": "rt",
        "source_name": "Regione Toscana",
        "publisher": "Regione Toscana",
        "title": title,
        "url": "https://example.test/bando",
        "summary": "",
        "deadline_at": "2026-10-30",
        "beneficiary_text": beneficiary,
        "eligibility": eligibility,
        "eligibility_reason": "Motivazione base",
        "themes": ["opere-pubbliche"],
        "priority": "high",
    }


class OpportunityRadarV02Test(unittest.TestCase):
    def test_toscana_diffusa_is_resolved_per_municipality(self) -> None:
        resolved = radar.resolve_municipalities(
            item(
                "Avviso pubblico Comuni Toscana Diffusa",
                beneficiary="Comuni ricadenti nei territori della Toscana Diffusa",
            ),
            PROFILES,
            date(2026, 8, 21),
        )
        matrix = resolved["municipality_eligibility"]
        self.assertEqual(matrix["Seravezza"]["status"], "eligible")
        self.assertEqual(matrix["Stazzema"]["status"], "eligible")
        self.assertEqual(matrix["Camaiore"]["status"], "conditional")
        self.assertEqual(matrix["Massarosa"]["status"], "not_eligible")
        self.assertEqual(matrix["Viareggio"]["status"], "not_eligible")
        self.assertEqual(resolved["municipalities"], ["Camaiore", "Seravezza", "Stazzema"])

    def test_generic_comuni_are_not_artificially_restricted(self) -> None:
        resolved = radar.resolve_municipalities(
            item("Bando Amianto Edifici Pubblici 2026", beneficiary="Enti locali e Comuni"),
            PROFILES,
            date(2026, 8, 21),
        )
        self.assertTrue(
            all(entry["status"] == "eligible" for entry in resolved["municipality_eligibility"].values())
        )

    def test_partnership_remains_conditional(self) -> None:
        resolved = radar.resolve_municipalities(
            item(
                "Progett-Azioni",
                eligibility="conditional",
                beneficiary="Partnership di soggetti pubblici e privati",
            ),
            PROFILES,
            date(2026, 8, 21),
        )
        self.assertTrue(
            all(entry["status"] == "conditional" for entry in resolved["municipality_eligibility"].values())
        )
        self.assertEqual(resolved["eligibility"], "conditional")

    def test_clear_business_review_is_discardable(self) -> None:
        business = item(
            "Bando PMI per investimenti produttivi",
            eligibility="review",
            beneficiary="PMI e imprese toscane",
        )
        self.assertTrue(radar.obvious_non_municipal(business))

    def test_stale_machine_readable_source_is_flagged(self) -> None:
        source = {"freshnessMaxDays": 45}
        payload = json.dumps(
            [
                {
                    "data_inizio_bando": "2025-12-01",
                    "data_fine_bando": "2026-01-30",
                }
            ]
        )
        freshness = radar.source_freshness(source, payload, [], date(2026, 8, 21))
        self.assertEqual(freshness["status"], "stale")
        self.assertEqual(freshness["observedDate"], "2026-01-30")

    def test_review_queue_is_separate_from_operational_output(self) -> None:
        config = {
            "schemaVersion": 2,
            "municipalities": TOWNS,
            "municipalityProfiles": PROFILES,
            "sources": [
                {
                    "id": "rt",
                    "name": "RT",
                    "publisher": "RT",
                    "type": "html_cards",
                    "url": "https://example.test/list",
                    "detailEnrichment": True,
                    "freshnessMaxDays": 45,
                }
            ],
        }
        listing = (
            '<h3><a href="/ok">Bando Amianto Edifici Pubblici 2026</a></h3>'
            '<p>Pubblicato il 20.08.2026. Scadenza presentazione domande 31.08.2026.</p>'
            '<h3><a href="/review">Bando Sistemi museali 2026</a></h3>'
            '<p>Pubblicato il 19.08.2026. Scadenza presentazione domande 25.09.2026.</p>'
        )
        details = {
            "https://example.test/ok": '<h2>Soggetti beneficiari</h2><p>Enti locali e Comuni.</p>',
            "https://example.test/review": '<h2>Finalità</h2><p>Sostegno ai sistemi museali.</p>',
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            result = radar.run(
                path,
                date(2026, 8, 21),
                payloads={"rt": listing},
                detail_payloads=details,
            )
        self.assertEqual(result["counts"]["public"], 1)
        self.assertEqual(result["counts"]["reviewInternal"], 1)
        self.assertEqual(result["opportunities"][0]["title"], "Bando Amianto Edifici Pubblici 2026")
        self.assertEqual(result["reviewQueue"][0]["title"], "Bando Sistemi museali 2026")


if __name__ == "__main__":
    unittest.main()
