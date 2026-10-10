#!/usr/bin/env python3
"""Real ministry documents, future calls, transport failures and daily replay."""
import hashlib
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from datetime import date
from pathlib import Path

import opportunity_document_promotion as promotion
import opportunity_radar_v03 as discovery

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/mim-notices"
TODAY = date(2026, 10, 10)
URL = "https://anci.lombardia.it/documenti/avviso.pdf"
PAGE = "https://anci.lombardia.it/dettaglio-circolari/avviso/"


def receipt(name="otto-per-mille.txt", url=URL):
    text = (FIXTURES / name).read_text()
    return {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "resolvedUrl": url, "document": True, "transport": "direct_https"}


class PromotionTests(unittest.TestCase):
    def test_real_notices(self):
        for name, deadline, clock in [("otto-per-mille.txt", "2026-10-23", "23:59"),
                                       ("vulnerabilita-sismica.txt", "2026-10-14", "14:00")]:
            item = promotion.parse_notice(receipt(name), URL, TODAY)
            self.assertEqual((item["deadline_at"], item["deadline_time"]), (deadline, clock))
            self.assertEqual(item["municipal_relevance_class"], "direct_conditional")
            self.assertEqual(item["source_id"], "mim-enti-locali")
            self.assertEqual(len(item["municipality_eligibility"]), 7)
            self.assertTrue(all(v["status"] == "conditional" for v in item["municipality_eligibility"].values()))
            self.assertIn("nulla osta", item["project_requirements"])
            if "vulnerabilita" in name:
                self.assertIn("PEC", item["project_requirements"])
            self.assertNotIn("2028", item["deadline_at"])

    def test_future_notice_without_seed(self):
        r = receipt()
        r["text"] = r["text"].replace("2026", "2027").replace("23 ottobre", "27 ottobre")
        item = promotion.parse_notice(r, URL, date(2027, 10, 10))
        self.assertEqual(item["deadline_at"], "2027-10-27")
        self.assertNotEqual(item["coverage_id"], promotion.parse_notice(receipt(), URL, TODAY)["coverage_id"])

    def test_rejects_unsafe_ambiguous_and_inapplicable(self):
        for old, new in [("Tutti gli Enti locali", "Le sole istituzioni scolastiche"),
                         ("Toscana", "Lombardia"),
                         ("e fino alle ore 23.59", "e fino a esaurimento risorse"),
                         ("IL DIRETTORE GENERALE", ""),
                         ("Tutti gli Enti locali", "Tutti gli Enti locali situati in Lombardia")]:
            r = receipt(); r["text"] = r["text"].replace(old, new)
            with self.assertRaises(ValueError): promotion.parse_notice(r, URL, TODAY)
        r = receipt(); r["transport"] = "reader_proxy"
        with self.assertRaises(ValueError): promotion.parse_notice(r, URL, TODAY)
        r = receipt(); r["resolvedUrl"] = "https://example.com/doc.pdf"
        with self.assertRaises(ValueError): promotion.parse_notice(r, URL, TODAY)

    def test_dedup_replay_and_expiry(self):
        result = {"opportunities": [], "discoveryQueue": [
            {"url": PAGE, "title": "Edilizia scolastica MIM"},
            {"url": PAGE + "copia/", "title": "Edilizia scolastica MIM"}]}
        calls = []
        def loader(url, document):
            calls.append((url, document))
            return receipt(url=url) if document else {"text": f'<a href="{URL}">Avviso MIM</a>'}
        promotion.apply_promotions(result, TODAY, loader=loader)
        self.assertEqual(result["documentPromotion"]["added"], 1)
        self.assertEqual(result["discoveryQueue"], [])
        self.assertEqual(calls.count((URL, True)), 1)
        next_day = {"opportunities": [], "discoveryQueue": []}
        promotion.apply_promotions(next_day, date(2026, 10, 11), previous=result, loader=loader)
        self.assertEqual(next_day["documentPromotion"]["revalidated"], 1)
        self.assertEqual(next_day["opportunities"][0]["coverage_id"], result["opportunities"][0]["coverage_id"])
        closed = {"opportunities": [], "discoveryQueue": []}
        promotion.apply_promotions(closed, date(2026, 10, 24), previous=result, loader=loader)
        self.assertEqual(len(closed["archive"]), 1)
        self.assertEqual(closed["opportunities"], [])

    def test_failed_fetch_is_not_a_new_verified_item(self):
        result = {"opportunities": [], "discoveryQueue": [{"url": PAGE, "title": "Avviso MIM"}]}
        def failed(url, document): raise TimeoutError("runner timeout")
        promotion.apply_promotions(result, TODAY, loader=failed)
        self.assertEqual(result["opportunities"], [])
        self.assertEqual(len(result["discoveryQueue"]), 1)
        self.assertIn("runner timeout", result["documentPromotion"]["checks"][0]["errors"])

    def test_institutional_feed_discovers_future_school_notices(self):
        source = {"id": "anci-abruzzo-national-leads", "includeTerms": ["MIM"], "municipalTerms": ["sismic"]}
        payload = f'<rss><channel><item><title>Avviso MIM vulnerabilità sismica</title><link>{PAGE}</link></item></channel></rss>'
        items = discovery.discovery_candidates(source, payload, "https://www.anciabruzzo.it/feed/")
        self.assertEqual(items[0]["url"], PAGE)

    def test_daily_hook_adds_before_continuity_and_annotation(self):
        import opportunity_daily_refresh_audit_fixed as daily
        result = {"opportunities": [], "discoveryQueue": [{"url": PAGE, "title": "Avviso MIM"}]}
        original = promotion.apply_promotions
        def loader(url, document):
            return receipt(url=url) if document else {"text": f'<a href="{URL}">Avviso</a>'}
        def apply(payload, today, **kwargs):
            return original(payload, today, loader=loader, **kwargs)
        with patch.object(daily, "_BASE_RUN_V04", return_value=result), \
             patch.object(daily.audit_promotions, "apply_complete_promotions"), \
             patch.object(promotion, "apply_promotions", side_effect=apply):
            candidate = daily._run_v04_with_audit_promotions(TODAY)
        self.assertEqual(candidate["counts"]["public"], 1)
        self.assertEqual(candidate["opportunities"][0]["municipal_relevance_class"], "direct_conditional")

    def test_live_page_invalid_charset_and_non_pdf(self):
        from email.message import Message
        from io import BytesIO
        headers = Message(); headers["Content-Type"] = "text/html; charset=utf-8,text/html"
        response = BytesIO(b'<a href="avviso.pdf">Avviso</a>')
        response.headers = headers; response.geturl = lambda: PAGE
        with patch("urllib.request.OpenerDirector.open", return_value=response):
            self.assertIn("avviso.pdf", promotion.fetch_receipt(PAGE, document=False)["text"])
        response = BytesIO(b"<html>403</html>")
        response.headers = headers; response.geturl = lambda: URL
        with patch("urllib.request.OpenerDirector.open", return_value=response), self.assertRaises(ValueError):
            promotion.fetch_receipt(URL, document=True)

    def test_public_renderer_resolves_mim_document_copies_offline(self):
        import materialize_opportunity_release_favicons as icons
        items = [promotion.parse_notice(receipt(name), URL, TODAY)
                 for name in ("otto-per-mille.txt", "vulnerabilita-sismica.txt")]
        with TemporaryDirectory() as tmp:
            payload = {"opportunities": items}
            provenance = icons.materialize(payload, Path(tmp))
            icons.apply_to_payload(payload, provenance)
            for item in items:
                asset = Path(tmp) / item["presentation"]["source_favicon"].replace("../", "")
                self.assertTrue(asset.exists())
                self.assertIn("MIM", asset.read_text())


if __name__ == "__main__":
    unittest.main()
