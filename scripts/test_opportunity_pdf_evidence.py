#!/usr/bin/env python3
from __future__ import annotations

import unittest

import opportunity_pdf_evidence as pdf


class OpportunityPdfEvidenceTest(unittest.TestCase):
    def test_prefers_bando_pdf(self):
        html = '''<a href="/docs/nota.pdf">Nota</a><a href="/docs/bando.pdf">Bando completo</a>'''
        links = pdf.pdf_links(html, "https://example.test/pagina")
        self.assertEqual(links[0], "https://example.test/docs/bando.pdf")

    def test_extracts_applicant_section_from_document_text(self):
        text = "Articolo 1 finalità. Soggetti beneficiari: possono presentare domanda i Comuni toscani e le Unioni di Comuni. Articolo 4 interventi."
        section = pdf.document_audience(text)
        self.assertIn("Comuni toscani", section)

    def test_attached_pdf_uses_injected_text_loader(self):
        html = '<a href="/allegati/avviso.pdf">Avviso pubblico</a>'
        section, url = pdf.attached_pdf_audience(
            html,
            "https://example.test/bando",
            text_loader=lambda _: "Soggetti ammissibili: Comuni della Toscana. Requisiti e modalità.",
        )
        self.assertEqual(url, "https://example.test/allegati/avviso.pdf")
        self.assertIn("Comuni della Toscana", section)


if __name__ == "__main__":
    unittest.main()
