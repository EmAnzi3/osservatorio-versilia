#!/usr/bin/env python3
from __future__ import annotations

import unittest

import build_opportunity_preview as preview


def opportunity(title: str, status: str, towns: dict[str, str], role: str = "direct_applicant") -> dict:
    return {
        "title": title,
        "source_name": "Regione Toscana",
        "url": "https://example.test/bando",
        "deadline_at": "2026-09-30",
        "eligibility": status,
        "applicant_type": "comune",
        "municipality_role": role,
        "geographic_scope": "Toscana",
        "final_beneficiaries": "comunita locale",
        "project_requirements": "Requisito specifico" if status == "conditional" else "",
        "eligibility_evidence": {"text": "Comuni ammessi secondo l'avviso.", "source_url": "https://example.test/atto"},
        "municipality_eligibility": {
            town: {"status": towns.get(town, "not_eligible"), "reason": f"Motivazione {town}"}
            for town in preview.TOWNS
        },
    }


class OpportunityPreviewTest(unittest.TestCase):
    def test_render_page_is_noindex_and_special(self) -> None:
        payload = {
            "referenceDate": "2026-08-21",
            "counts": {"reviewInternal": 0},
            "opportunities": [opportunity("Bando test", "eligible", {"Massarosa": "eligible"})],
        }
        page = preview.render_page(payload)
        self.assertIn('name="robots" content="noindex,nofollow,noarchive"', page)
        self.assertIn('data-page="special"', page)
        self.assertIn('id="site-header-mount"', page)
        self.assertIn('id="site-footer-mount"', page)
        self.assertNotIn('rel="canonical"', page)

    def test_only_actionable_towns_are_filterable(self) -> None:
        item = opportunity(
            "Toscana Diffusa",
            "eligible",
            {"Camaiore": "conditional", "Seravezza": "eligible", "Stazzema": "eligible"},
        )
        markup = preview.card_markup(item)
        self.assertIn('data-towns="camaiore|seravezza|stazzema"', markup)
        self.assertIn('data-town-chip="massarosa" data-town-status="not_eligible"', markup)

    def test_conditional_card_explains_requirement(self) -> None:
        item = opportunity("Bando condizionato", "conditional", {"Viareggio": "conditional"})
        markup = preview.card_markup(item)
        self.assertIn("Condizioni da verificare", markup)
        self.assertIn("Requisito specifico", markup)
        self.assertIn("Da verificare", markup)

    def test_role_is_translated_for_human_reading(self) -> None:
        item = opportunity("Buoni scuola", "eligible", {"Massarosa": "eligible"}, role="implementing_body")
        markup = preview.card_markup(item)
        self.assertIn("Ente attuatore / proponente", markup)
        self.assertNotIn(">implementing_body<", markup)

    def test_cards_are_sorted_by_deadline(self) -> None:
        late = opportunity("Bando tardi", "eligible", {"Massarosa": "eligible"})
        late["deadline_at"] = "2026-11-30"
        early = opportunity("Bando presto", "eligible", {"Massarosa": "eligible"})
        early["deadline_at"] = "2026-08-31"
        page = preview.render_page({"referenceDate": "2026-08-21", "counts": {}, "opportunities": [late, early]})
        self.assertLess(page.index("Bando presto"), page.index("Bando tardi"))


if __name__ == "__main__":
    unittest.main()
