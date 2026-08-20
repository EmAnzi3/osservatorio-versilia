#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import opportunity_radar as radar


REGIONE_HTML = """
<html><body>
<h3><a href="/bando-amianto">Bando Amianto Edifici Pubblici 2026</a></h3>
<p>Contributi destinati agli Enti Locali per la rimozione di amianto negli edifici pubblici.</p>
<p>Pubblicato il 22.06.2026</p><p>Stato: Aperto</p>
<p>Scadenza presentazione domande 31.08.2026 16:00</p>
<h3><a href="/voucher">Voucher formativi individuali</a></h3>
<p>Bando rivolto ai liberi professionisti. Scadenza presentazione domande 15.09.2026.</p>
<h3><a href="/generico">Premialità ai Poli Tecnici Professionali 2026</a></h3>
<p>Stato: Aperto. Scadenza presentazione domande 12.10.2026.</p>
</body></html>
"""

FONDAZIONE_HTML = """
<html><body>
<h2>Bandi in corso e in arrivo</h2>
<h3><a href="/bandi/bando-2026-progettazione-opere-pubbliche">Bando 2026 Progettare per il futuro – opere pubbliche</a></h3>
<p>dal 15 Giugno 2026 al 11 Settembre 2026</p>
<p>Riservata alle Amministrazioni pubbliche locali della Provincia di Lucca. Opere pubbliche e ambiente.</p>
<h3><a href="/bandi/bando-2026-progett-azioni">Bando 2026 Progett-Azioni</a></h3>
<p>dal 16 Giugno 2026 al 11 Settembre 2026</p>
<p>Partnership di soggetti pubblici e privati per progettazione sociale.</p>
</body></html>
"""

PADIGITALE_JSON = json.dumps([
    {
        "titolo": "1.2 Abilitazione al Cloud - Comuni - settembre 2026",
        "misura": "1.2 Abilitazione e facilitazione migrazione al Cloud",
        "data_inizio_bando": "2026-09-01",
        "data_fine_bando": "2026-11-30",
        "stato": "APERTO",
        "totale_importo_stanziato": 10000000,
        "soggetti_destinatari": "Comuni"
    },
    {
        "titolo": "1.2 Abilitazione al Cloud - Scuole",
        "misura": "Cloud",
        "data_inizio_bando": "2026-09-01",
        "data_fine_bando": "2026-11-30",
        "stato": "APERTO",
        "totale_importo_stanziato": 1000000,
        "soggetti_destinatari": "Scuole"
    },
    {
        "titolo": "1.4.3 app IO - Comuni - vecchio",
        "misura": "App IO",
        "data_inizio_bando": "2025-01-01",
        "data_fine_bando": "2025-02-01",
        "stato": "TERMINATO",
        "totale_importo_stanziato": 1000000,
        "soggetti_destinatari": "Comuni"
    }
])


class OpportunityRadarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.municipalities = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
        self.today = date(2026, 8, 21)

    def test_italian_date(self) -> None:
        self.assertEqual(radar.parse_date_token("11 Settembre 2026"), date(2026, 9, 11))
        self.assertEqual(radar.parse_date_token("31.08.2026"), date(2026, 8, 31))

    def test_regione_filter_is_conservative(self) -> None:
        source = {"id": "rt", "name": "RT", "publisher": "Regione Toscana", "url": "https://example.test/list"}
        items = radar.collect_html_cards(source, self.municipalities, self.today, REGIONE_HTML)
        self.assertEqual([item.title for item in items], ["Bando Amianto Edifici Pubblici 2026", "Premialità ai Poli Tecnici Professionali 2026"])
        amianto = items[0]
        self.assertEqual(amianto.eligibility, "eligible")
        self.assertEqual(amianto.deadline_at, "2026-08-31")
        self.assertEqual(amianto.municipalities, self.municipalities)
        generic = items[1]
        self.assertEqual(generic.eligibility, "review")
        self.assertEqual(generic.municipalities, [])

    def test_fondazione_extracts_direct_and_conditional(self) -> None:
        source = {"id": "fcrl", "name": "FCRL", "publisher": "Fondazione CRL", "url": "https://example.test/bandi"}
        items = radar.collect_html_cards(source, self.municipalities, self.today, FONDAZIONE_HTML)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].deadline_at, "2026-09-11")
        self.assertEqual(items[0].eligibility, "eligible")
        self.assertEqual(items[1].eligibility, "conditional")

    def test_padigitale_uses_official_beneficiary_field(self) -> None:
        source = {"id": "pad26", "name": "PAD26", "publisher": "DTD", "url": "https://example.test/avvisi.json"}
        items = radar.collect_padigitale(source, self.municipalities, self.today, PADIGITALE_JSON)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].eligibility, "eligible")
        self.assertEqual(items[0].funding_total_eur, 10000000.0)
        self.assertEqual(items[0].themes, ["digitale"])

    def test_run_combines_sources(self) -> None:
        config = {
            "schemaVersion": 1,
            "municipalities": self.municipalities,
            "sources": [
                {"id": "rt", "name": "RT", "type": "html_cards", "url": "https://example.test/rt", "publisher": "RT", "territory": "Toscana"},
                {"id": "fcrl", "name": "FCRL", "type": "html_cards", "url": "https://example.test/fcrl", "publisher": "FCRL", "territory": "Lucca"},
                {"id": "pad26", "name": "PAD26", "type": "padigitale_json", "url": "https://example.test/pad26", "publisher": "DTD", "territory": "Italia"}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            result = radar.run(path, self.today, payloads={"rt": REGIONE_HTML, "fcrl": FONDAZIONE_HTML, "pad26": PADIGITALE_JSON})
        self.assertEqual(result["counts"]["total"], 5)
        self.assertEqual(result["counts"]["eligible"], 3)
        self.assertEqual(result["counts"]["conditional"], 1)
        self.assertEqual(result["counts"]["review"], 1)
        self.assertTrue(all(source["status"] == "ok" for source in result["sources"]))


if __name__ == "__main__":
    unittest.main()
