#!/usr/bin/env python3
"""Real ministry documents, future calls, transport failures and daily replay."""
import hashlib
import json
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
    def culture_receipts(self):
        root = FIXTURES.parent / "cepell-notices"
        provenance = json.loads((root / "provenance.json").read_text())
        return {name:{"text":(root / (name+".txt")).read_text(),"sha256":meta["sha256"],
                      "resolvedUrl":meta["url"],"document":True,"transport":"direct_https",
                      "pages":meta["pages"],"pagesWithoutText":[]} for name,meta in provenance.items()}

    def test_reading_call_uses_complete_qualification_list(self):
        receipts=self.culture_receipts();b,q,a=[receipts[n] for n in ("reading-call","qualified-towns","evaluation-criteria")]
        self.assertEqual(q["pages"],30)
        item=promotion.parse_reading_notice(b,b["resolvedUrl"],q,a,date(2026,10,12))
        self.assertEqual(item["deadline_at"],"2026-10-30")
        self.assertEqual(item["deadline_time"],"13:00")
        self.assertEqual({t for t,v in item["municipality_eligibility"].items() if v["status"]=="conditional"},
                         {"Forte dei Marmi","Pietrasanta","Seravezza","Viareggio"})
        self.assertEqual(item["municipality_eligibility"]["Massarosa"]["status"],"not_eligible")
        self.assertIn("nessun finanziamento",item["project_requirements"])
        self.assertIn("mai partner",item["project_requirements"])
        from build_opportunity_preview import card_markup
        card=card_markup(item)
        self.assertIn('Documenti ufficiali',card)
        self.assertIn(q["resolvedUrl"],card)
        self.assertIn(a["resolvedUrl"],card)
        refused_tail={**q,"text":q["text"]+"\n5 2024-QCL-99999 MASSAROSA\nNon ammissibile"}
        excluded=promotion.parse_reading_notice(b,b["resolvedUrl"],refused_tail,a,TODAY)
        self.assertEqual(excluded["municipality_eligibility"]["Massarosa"]["status"],"not_eligible")
        for old,new in (("almeno il 51%","almeno il 40%"),("è volontario","è obbligatorio"),("inferiore al 50%","inferiore al 30%")):
            with self.assertRaises(ValueError):
                promotion.parse_reading_notice({**b,"text":b["text"].replace(old,new)},b["resolvedUrl"],q,a,TODAY)
        with self.assertRaises(promotion.NoticeWindowClosed):
            promotion.parse_reading_notice(b,b["resolvedUrl"],q,a,date(2026,11,1))
        for changed in ({**q,"text":q["text"].replace("2024-2025-2026","2021-2022-2023")},
                        {**q,"pagesWithoutText":[30]},
                        {**q,"text":q["text"].replace("320 2024-QCL-00904 FORTE DEI MARMI","")},
                        {**q,"transport":"reader_proxy"}):
            with self.assertRaises(ValueError):
                promotion.parse_reading_notice(b,b["resolvedUrl"],changed,a,TODAY)

    def test_culture_call_promotes_and_revalidates_without_duplicate(self):
        receipts=self.culture_receipts();by_url={r["resolvedUrl"]:r for r in receipts.values()}
        page_url="https://cultura.gov.it/comunicato/avviso-lettura"
        page='<main>'+''.join(f'<a href="{u}">Bando o Allegato</a>' for u in by_url)+'</main>'
        def loader(url,document):return by_url[url] if document else {"text":page}
        first={"opportunities":[],"discoveryQueue":[{"url":page_url,"title":"Bando Città che legge"}]}
        promotion.apply_promotions(first,TODAY,loader=loader)
        self.assertEqual(len(first["opportunities"]),1)
        next_run={"opportunities":[],"discoveryQueue":[]}
        promotion.apply_promotions(next_run,TODAY,previous=first,loader=loader)
        self.assertEqual(len(next_run["opportunities"]),1)
        self.assertEqual(next_run["documentPromotion"]["revalidated"],1)
        missing={"opportunities":[],"discoveryQueue":[{"url":page_url,"title":"Bando Città che legge"}]}
        promotion.apply_promotions(missing,TODAY,loader=lambda u,d:by_url[u] if d else {"text":f'<a href="{receipts["reading-call"]["resolvedUrl"]}">Bando</a>'})
        self.assertEqual(missing["opportunities"],[])

    def test_daily_preserves_unresolved_call_absent_from_current_listing(self):
        import opportunity_daily_refresh_audit_fixed as daily
        receipts = self.culture_receipts()
        by_url = {r["resolvedUrl"]: r for r in receipts.values()}
        page_url = "https://cultura.gov.it/comunicato/29352"
        reopening_url = "https://ancitoscana.it/avviso-energia/"
        covered_url = "https://ancitoscana.it/avviso-gia-pubblico/"
        previous = {"referenceDate": "2026-10-09", "opportunities": [{"url": covered_url}],
                    "discoveryQueue": [
                        {"url": page_url, "source_id": "mic-generale", "title": "Bando Città che legge"},
                        {"url": reopening_url, "title": "Bando energia", "deadline_at": "2026-10-01"},
                        {"url": "https://example.test/closed", "title": "Avviso chiuso", "deadline_at": "2026-10-01"},
                        {"url": "https://example.test/closed-yesterday", "title": "Avviso concluso ieri", "deadline_at": "2026-10-09"},
                        {"url": "https://prefettura.interno.gov.it/it/chiusura", "title": "AVVISO: Chiusura temporanea degli uffici della Prefettura"},
                        {"url": covered_url, "title": "Avviso già pubblico"}]}
        previous["reviewDocumentLookup"] = [{"url": page_url, "status": "ok", "checkedAt": "2026-10-09",
                                             "documents": [{"url": u, "status": "located"} for u in by_url]}]
        fresh = {"url": reopening_url, "title": "Proroga bando energia", "deadline_at": "2026-11-30"}
        result = {"opportunities": [], "discoveryQueue": [fresh]}
        calls = []
        def loader(url, document):
            calls.append(url)
            if not document:
                raise TimeoutError("Ministry listing/detail inaccessible")
            return by_url[url]
        original = promotion.apply_promotions
        def apply(payload, today, **kwargs):
            carried = next(x for x in payload["discoveryQueue"] if x["url"] == page_url)
            self.assertEqual(carried["discovery_last_checked_at"], "2026-10-09")
            return original(payload, today, loader=loader, **kwargs)
        with TemporaryDirectory() as directory:
            path = Path(directory)/"previous.json"
            path.write_text(json.dumps(previous))
            with patch.object(daily, "_BASE_RUN_V04", return_value=result), \
                 patch.object(daily.audit_promotions, "apply_complete_promotions"), \
                 patch.object(promotion, "apply_promotions", side_effect=apply):
                candidate = daily._run_v04_with_audit_promotions(TODAY, previous_path=path, payloads={})
        self.assertEqual(candidate["counts"]["public"], 1)
        self.assertIn("Città che legge", candidate["opportunities"][0]["title"])
        self.assertEqual(candidate["discoveryQueue"], [fresh])
        self.assertEqual(set(calls), {page_url, *by_url})
        self.assertEqual(candidate["documentPromotion"]["checks"][0]["sourcePageFallback"], "recent_attachment_references")

    def test_slow_complete_annexes_fit_existing_transport_caps(self):
        import opportunity_discovery_resilient as transport
        receipts = self.culture_receipts()
        by_url = {r["resolvedUrl"]: r for r in receipts.values()}
        page_url = "https://cultura.gov.it/comunicato/29352"
        page = '<main>'+''.join(f'<a href="{u}">Bando o Allegato</a>' for u in by_url)+'</main>'
        class SlowSource:
            spent = 0
            def fetch(self, url, *, kind, timeout, attempts):
                if kind == "promotion_page":
                    return {"text": page}, {}
                # A valid source responds after the old 15-second allowance,
                # while remaining inside the real 60/180-second budget caps.
                delay = 25
                self.spent += min(timeout, delay)
                if timeout < delay:
                    return None, {"errors": ["urlopen timed out"]}
                return by_url[url], {}
        budget = SlowSource()
        result = {"opportunities": [], "discoveryQueue": [{"url": page_url, "title": "Bando Città che legge"}]}
        with patch.object(transport, "LIVE_BUDGET", budget):
            promotion.apply_promotions(result, TODAY)
        self.assertEqual(result["documentPromotion"]["added"], 1)
        self.assertEqual(result["opportunities"][0]["qualification_evidence"]["pages"], 30)
        self.assertLessEqual(budget.spent, 180)

    def test_inaccessible_national_pdf_uses_fresh_exact_protocol_copy(self):
        original="https://www.anci.it/wp-content/uploads/2026/10/m_pi.AOODGFIESD.REGISTRO-UFFICIALEU.0078918.01-10-2026.pdf"
        copy="https://anci.lombardia.it/documenti/24093-Avviso%20MIM%20n.%2078918%20del%201%20ottobre%202026.pdf"
        self.assertEqual(promotion.notice_reference(original),promotion.notice_reference(copy))
        self.assertNotEqual(promotion.notice_reference(original.replace("0078918","0079594")),promotion.notice_reference(copy))
        old=promotion.parse_notice(receipt(url=copy),copy,TODAY)
        result={"opportunities":[old],"discoveryQueue":[{"url":PAGE,"title":"Avviso MIM"}]}
        calls=[]
        def loader(url,document):
            calls.append(url)
            if not document:return {"text":f'<a href="{original}">Avviso MIM</a>'}
            if url==copy:return receipt(url=copy)
            raise TimeoutError("national timeout")
        promotion.apply_promotions(result,TODAY,loader=loader)
        self.assertEqual(len(result["opportunities"]),1)
        self.assertNotIn(original,calls)
        check=result["documentPromotion"]["checks"][0]["documents"][0]
        self.assertEqual(check["originalUrl"],original)
        self.assertEqual(check["url"],copy)
        self.assertEqual(check["status"],"verified")
        wrong={**receipt(url=copy),"text":"Not an official notice"}
        refused={"opportunities":[old],"discoveryQueue":[{"url":PAGE,"title":"Avviso MIM"}]}
        promotion.apply_promotions(refused,TODAY,loader=lambda u,d:wrong if d else {"text":f'<a href="{original}">Avviso</a>'})
        self.assertEqual(refused["documentPromotion"]["added"],0)
        self.assertNotEqual(refused["documentPromotion"]["checks"][0]["status"],"published_candidate")

    def test_faq_is_read_without_creating_a_call_and_failure_stays_visible(self):
        faq_url="https://www.anci.it/documenti/faq.pdf"
        faq=receipt("otto-per-mille-faq.txt",faq_url)
        item=promotion.parse_notice(receipt(),URL,TODAY)
        self.assertTrue(promotion.supporting_faq(faq,item))
        self.assertFalse(promotion.supporting_faq({**faq,"transport":"reader_proxy"},item))
        self.assertFalse(promotion.supporting_faq({**faq,"text":faq["text"]+"\nProroga delle domande"},item))
        def loader(url,document):
            if not document:return {"text":f'<a href="{URL}">Avviso</a><a href="{faq_url}">FAQ</a>'}
            return faq if url==faq_url else receipt()
        result={"opportunities":[],"discoveryQueue":[{"url":PAGE,"title":"Avviso MIM"}]}
        promotion.apply_promotions(result,TODAY,loader=loader)
        self.assertEqual(len(result["opportunities"]),1)
        self.assertEqual(len(result["opportunities"][0]["supplementary_documents"]),1)
        self.assertEqual(result["documentPromotion"]["checks"][0]["documents"][1]["status"],"verified_support")
        def failed(url,document):
            if url==faq_url:raise TimeoutError("FAQ timeout")
            return loader(url,document)
        pending={"opportunities":[item],"discoveryQueue":[{"url":PAGE,"title":"Avviso MIM"}]}
        promotion.apply_promotions(pending,TODAY,loader=failed)
        self.assertEqual(pending["documentPromotion"]["checks"][0]["status"],"review")
        self.assertEqual(len(pending["discoveryQueue"]),1)

    def test_deferred_notices_get_a_turn_next_run(self):
        leads = [{"url": f"https://anci.lombardia.it/avviso/{n}", "title": f"Avviso MIM {n}"} for n in range(13)]
        loader = lambda url, document: {"text": "Nessun allegato"}
        first = {"discoveryQueue": leads.copy(), "opportunities": []}
        promotion.apply_promotions(first, TODAY, loader=loader)
        self.assertEqual(first["documentPromotion"]["checks"][-1]["status"], "deferred")
        second = {"discoveryQueue": leads.copy(), "opportunities": []}
        promotion.apply_promotions(second, TODAY, previous=first, loader=loader)
        self.assertEqual(second["documentPromotion"]["checks"][0]["url"], leads[-1]["url"])

    def test_layout_variants_and_conflicting_or_compound_notices(self):
        r = receipt()
        r["text"] = r["text"].replace("ART.", "Articolo").replace(" – ", " — ").replace("del giorno", "del")
        item = promotion.parse_notice(r, URL, TODAY)
        self.assertEqual(item["deadline_at"], "2026-10-23")
        r["text"] += "\nArticolo 3 — Seconda procedura\n"
        with self.assertRaisesRegex(ValueError, "ripetuti"):
            promotion.parse_notice(r, URL, TODAY)
        r = receipt()
        r["text"] = r["text"].replace("ART. 4", "dalle ore 10.00 del giorno 5 ottobre 2026 e fino alle ore 12.00 del giorno 20 ottobre 2026.\nART. 4")
        with self.assertRaisesRegex(ValueError, "ambigua"):
            promotion.parse_notice(r, URL, TODAY)

    def test_direct_pdf_and_failed_attachment_are_visible(self):
        result = {"opportunities": [], "discoveryQueue": [{"url": URL, "title": "Avviso MIM"}]}
        calls = []
        def loader(url, document):
            calls.append((url, document))
            return receipt(url=url)
        promotion.apply_promotions(result, TODAY, loader=loader)
        self.assertEqual(calls, [(URL, True)])
        self.assertEqual(result["documentPromotion"]["checks"][0]["documents"][0]["status"], "verified")
        def failed(url, document):
            if document:
                raise ValueError("PDF scansionato o testo non estraibile")
            return {"text": f'<a href="{URL}">Avviso</a>'}
        result = {"opportunities": [], "discoveryQueue": [{"url": PAGE, "title": "Avviso MIM"}]}
        promotion.apply_promotions(result, TODAY, loader=failed)
        document = result["documentPromotion"]["checks"][0]["documents"][0]
        self.assertEqual(document["url"], URL)
        self.assertIn("scansionato", document["error"])
        self.assertEqual(result["opportunities"], [])

    def test_past_window_is_classified_without_inventing_eligibility(self):
        r = receipt(); r["text"] = r["text"].replace("2026", "2025").replace("OTTO PER MILLE", "FONDO NON SUPPORTATO")
        result = {"opportunities": [], "discoveryQueue": [{"url": URL, "title": "Avviso MIM"}]}
        promotion.apply_promotions(result, TODAY, loader=lambda url, document: r)
        check = result["documentPromotion"]["checks"][0]
        self.assertEqual(check["status"], "expired")
        self.assertEqual(check["documents"][0]["deadline"], "2025-10-23")
        self.assertEqual(result["opportunities"], [])

    def test_graduatoria_is_not_a_new_application_window(self):
        result = {"opportunities": [], "discoveryQueue": [{"url": PAGE, "title": "Edilizia scolastica"}]}
        calls = []
        def loader(url, document):
            calls.append(document)
            return {"text": f'<p>È stata approvata la graduatoria definitiva.</p><a href="{URL}">Decreto</a>'}
        promotion.apply_promotions(result, TODAY, loader=loader)
        self.assertEqual(calls, [False])
        self.assertEqual(result["documentPromotion"]["checks"][0]["status"], "administrative_update")
        self.assertEqual(result["documentPromotion"]["checks"][0]["documents"][0]["url"], URL)

    def test_signed_proroga_matches_original_call_and_does_not_create_new_one(self):
        original_url = "https://www.anciabruzzo.it/wp-content/uploads/2026/10/Avviso-Pubblico-n.-79378-del-6-ottobre-2026.pdf"
        note_url = "https://anci.lombardia.it/documenti/24173-MIM%20-%20Nota%20n.%2081468%20del%2012%20ottobre%202026%20-%20Proroga.pdf"
        original_receipt = receipt("vulnerabilita-sismica.txt", original_url)
        original = promotion.parse_notice(original_receipt, original_url, date(2026, 10, 13))
        self.assertEqual(promotion.notice_reference(original_url), (79378, "2026-10-06"))
        text = """
Ministero dell’istruzione e del merito
Direzione generale per l’edilizia scolastica
AVVISO PUBBLICO PER LA VERIFICA DI VULNERABILITÀ SISMICA
Oggetto: Proroga del termine di presentazione delle candidature.
Con riferimento all’Avviso pubblico prot. n. 79378 del 6 ottobre 2026,
il termine di presentazione delle stesse, originariamente fissato alle ore 14:00 del 14 ottobre 2026
dall’articolo 3, comma 6, è prorogato alle ore 12:00 del 16 ottobre 2026.
Restano ferme tutte le ulteriori disposizioni, modalità e condizioni previste dall’Avviso.
IL DIRETTORE GENERALE
"""
        note = {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "resolvedUrl": note_url, "document": True, "transport": "direct_https"}
        changed = promotion.verified_deadline_extension(note, original)
        self.assertEqual((changed["deadline_at"], changed["deadline_time"]), ("2026-10-16", "12:00"))
        self.assertEqual(changed["coverage_id"], original["coverage_id"])
        self.assertIsNone(promotion.verified_deadline_extension({**note, "transport": "reader_proxy"}, original))
        self.assertIsNone(promotion.verified_deadline_extension({**note, "text": text.replace("79378", "78918")}, original))
        self.assertIsNone(promotion.verified_deadline_extension({**note, "text": text.replace("IL DIRETTORE GENERALE", "")}, original))
        self.assertIsNone(promotion.verified_deadline_extension({**note, "text": text.replace("14:00", "13:00")}, original))

        page = "https://anci.lombardia.it/dettaglio-circolari/202610131510-edilizia-scolastica-proroga/"
        previous = {"opportunities": [original], "discoveryQueue": []}
        def loader(url, document):
            if not document:
                return {"text": f'<main><a href="{note_url}">Nota MIM proroga</a></main>'}
            return note if url == note_url else original_receipt
        candidate = {"opportunities": [], "discoveryQueue": [
            {"url": page, "title": "Edilizia scolastica – Vulnerabilità sismica - Proroga"}]}
        promotion.apply_promotions(candidate, date(2026, 10, 13), previous=previous, loader=loader)
        self.assertEqual(len(candidate["opportunities"]), 1)
        self.assertEqual(candidate["opportunities"][0]["coverage_id"], original["coverage_id"])
        self.assertEqual(candidate["opportunities"][0]["deadline_at"], "2026-10-16")
        self.assertEqual(candidate["documentPromotion"]["checks"][-1]["status"], "published_candidate")
        self.assertEqual(candidate["discoveryQueue"], [])
        from opportunity_pdf_evidence import verified_document_links
        urls = [url for _, url in verified_document_links(candidate["opportunities"][0])]
        self.assertIn(note_url, urls)
        expired = {"opportunities": [], "discoveryQueue": [
            {"url": page, "title": "Edilizia scolastica – Vulnerabilità sismica - Proroga"}]}
        promotion.apply_promotions(expired, date(2026, 10, 18), previous=previous, loader=loader)
        self.assertFalse(expired["opportunities"])
        self.assertEqual(expired["documentPromotion"]["checks"][-1]["status"], "expired")
        self.assertEqual(expired["discoveryQueue"], [])

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
        culture=self.culture_receipts()
        items.append(promotion.parse_reading_notice(culture["reading-call"],culture["reading-call"]["resolvedUrl"],
                                                    culture["qualified-towns"],culture["evaluation-criteria"],TODAY))
        with TemporaryDirectory() as tmp:
            payload = {"opportunities": items}
            provenance = icons.materialize(payload, Path(tmp))
            icons.apply_to_payload(payload, provenance)
            for item in items:
                asset = Path(tmp) / item["presentation"]["source_favicon"].replace("../", "")
                self.assertTrue(asset.exists())
                if item["coverage_id"].startswith("mim-"):
                    self.assertIn("MIM", asset.read_text())


if __name__ == "__main__":
    unittest.main()
