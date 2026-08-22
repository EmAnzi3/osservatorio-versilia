#!/usr/bin/env python3
from __future__ import annotations

import unittest

import build_opportunity_preview as preview


def opportunity(
    title: str,
    status: str,
    towns: dict[str, str],
    role: str = "direct_applicant",
    source_id: str = "regione-toscana",
) -> dict:
    return {
        "title": title,
        "source_id": source_id,
        "source_name": "Regione Toscana",
        "publisher": "Regione Toscana",
        "url": "https://example.test/bando",
        "deadline_at": "2026-09-30",
        "deadline_time": "13:00",
        "eligibility": status,
        "access_mode": "specific_requirement" if status == "conditional" else "direct",
        "applicant_type": "comune",
        "municipality_role": role,
        "geographic_scope": "toscana",
        "final_beneficiaries": "comunita locale",
        "project_requirements": "requisito specifico" if status == "conditional" else "",
        "presentation": {
            "source_label": "Regione Toscana",
            "source_mark": "RT",
            "source_class": "regione",
            "category": "ambiente",
            "description": "breve descrizione del finanziamento",
            "condition_label": "richiede requisito concreto" if status == "conditional" else "",
        },
        "quality_gate": {"status": "pass"},
        "eligibility_evidence": {"text": "Comuni ammessi secondo l'avviso.", "source_url": "https://example.test/atto"},
        "municipality_eligibility": {
            town: {"status": towns.get(town, "not_eligible"), "reason": f"Motivazione {town}"}
            for town in preview.TOWNS
        },
    }


class OpportunityPreviewTest(unittest.TestCase):
    def test_render_page_is_noindex_and_hides_internal_concepts(self) -> None:
        payload = {
            "referenceDate": "2026-08-21",
            "counts": {"reviewInternal": 0},
            "opportunities": [opportunity("Bando test", "eligible", {"Massarosa": "eligible"})],
            "archive": [],
        }
        page = preview.render_page(payload)
        self.assertIn('name="robots" content="noindex,nofollow,noarchive"', page)
        self.assertIn('data-page="special"', page)
        self.assertNotIn("Quality gate", page)
        self.assertNotIn("Perché compare:", page)
        self.assertNotIn(">Da verificare<", page)
        self.assertNotIn("Review residua", page)

    def test_source_filter_and_source_mark_are_rendered(self) -> None:
        payload = {
            "referenceDate": "2026-08-21",
            "opportunities": [opportunity("Bando test", "eligible", {"Massarosa": "eligible"})],
            "archive": [],
        }
        page = preview.render_page(payload)
        self.assertIn("data-op-source", page)
        self.assertIn('value="regione-toscana"', page)
        self.assertIn("Regione Toscana", page)
        self.assertIn(">RT<", page)

    def test_only_actionable_towns_are_filterable(self) -> None:
        item = opportunity(
            "Toscana Diffusa",
            "eligible",
            {"Camaiore": "conditional", "Seravezza": "eligible", "Stazzema": "eligible"},
        )
        markup = preview.card_markup(item)
        self.assertIn('data-towns="camaiore|seravezza|stazzema"', markup)
        self.assertIn('data-town-chip="massarosa" data-town-status="not_eligible"', markup)

    def test_specific_requirement_is_explicit_not_uncertain(self) -> None:
        item = opportunity("Bando con requisito", "conditional", {"Viareggio": "conditional"})
        markup = preview.card_markup(item)
        self.assertIn("Richiede requisito concreto", markup)
        self.assertIn("Requisito specifico", markup)
        self.assertNotIn("Da verificare", markup)

    def test_visible_values_start_uppercase(self) -> None:
        item = opportunity("Bando test", "eligible", {"Massarosa": "eligible"})
        markup = preview.card_markup(item)
        self.assertIn(">Comune<", markup)
        self.assertIn(">Toscana<", markup)
        self.assertIn("Comunita locale", markup)
        self.assertNotIn(">comune<", markup)

    def test_deadline_includes_time(self) -> None:
        markup = preview.card_markup(opportunity("Bando test", "eligible", {"Massarosa": "eligible"}))
        self.assertIn("30/09/2026 · ore 13:00", markup)

    def test_cards_are_sorted_by_deadline(self) -> None:
        late = opportunity("Bando tardi", "eligible", {"Massarosa": "eligible"})
        late["deadline_at"] = "2026-11-30"
        early = opportunity("Bando presto", "eligible", {"Massarosa": "eligible"})
        early["deadline_at"] = "2026-08-31"
        page = preview.render_page({"referenceDate": "2026-08-21", "counts": {}, "opportunities": [late, early], "archive": []})
        self.assertLess(page.index("Bando presto"), page.index("Bando tardi"))

    def test_archive_is_minimal_and_keeps_source_link(self) -> None:
        archived = {
            "title": "Bando chiuso",
            "source_label": "Regione Toscana",
            "source_mark": "RT",
            "source_class": "regione",
            "deadline_at": "2026-08-20",
            "url": "https://example.test/chiuso",
        }
        page = preview.render_page({"referenceDate": "2026-08-21", "opportunities": [], "archive": [archived]})
        self.assertIn("Bando chiuso", page)
        self.assertIn("Fonte ufficiale", page)
        self.assertNotIn("Destinatari finali", page)


if __name__ == "__main__":
    unittest.main()
