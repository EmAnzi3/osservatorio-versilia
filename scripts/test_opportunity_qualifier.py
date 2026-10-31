#!/usr/bin/env python3
"""Qualificazione automatica: regole generali su testi realistici, nessun bando citato per nome."""
from datetime import date

import opportunity_qualifier as q

TOWNS = ("Camaiore", "Massarosa")


def candidate(title, url="https://www.example.gov.it/avviso", **extra):
    return {"title": title, "url": url, "source_id": "mim-enti-locali", "source_label": "MIM", **extra}


def decide(title, text, today=date(2026, 10, 1), **extra):
    return q.qualify(candidate(title, **extra), text, {}, today)


PAD = " Il presente avviso disciplina le modalità di accesso al finanziamento. " * 6

SEISMIC = (PAD + "Art. 2 – Soggetti ammessi. Possono presentare candidatura gli enti locali proprietari di edifici "
           "pubblici adibiti ad uso scolastico. Art. 3 – Modalità e termini. Le candidature devono essere presentate "
           "dalle ore 10:00 del 7 ottobre 2026 ed entro le ore 15:00 del 16 ottobre 2026 tramite PEC.")


def test_ministerial_notice_qualified_and_expired():
    d = decide("Avviso pubblico n. 79378 del 6 ottobre 2026 – prevenzione sismica", SEISMIC)
    assert d.status == "qualified", d
    assert d.deadline == "2026-10-16" and "enti locali" in d.applicant
    assert d.role == "direct_applicant"
    later = decide("Avviso pubblico n. 79378 del 6 ottobre 2026 – prevenzione sismica", SEISMIC, today=date(2026, 10, 30))
    assert later.status == "expired" and later.deadline == "2026-10-16"


def test_extension_uses_latest_deadline():
    text = SEISMIC + " Il termine di presentazione è prorogato al 5 dicembre 2026."
    assert decide("Avviso sismica – proroga dei termini", text).deadline == "2026-12-05"


def test_business_only_call_rejected():
    text = (PAD + "Soggetti beneficiari: possono presentare domanda esclusivamente le imprese con sede legale nel "
            "Comune di Lucca. Scadenza: 30/11/2026.")
    assert decide("Bando contributi alle imprese 2026", text).status == "rejected"


def test_news_and_results_rejected():
    for title in ("Graduatoria beneficiari contributi progettazione", "Chiarimenti relativi all'Avviso pubblico",
                  "Comunicazione orari front office", "Ripartizione di risorse ai comuni"):
        assert decide(title, SEISMIC).status == "rejected", title


def test_other_region_rejected():
    text = (PAD + "Possono partecipare i Comuni lombardi con meno di 5.000 abitanti. Le domande vanno presentate "
            "entro il 15 dicembre 2026.")
    assert decide("Bando Regione Lombardia per i piccoli comuni", text).status == "rejected"


def test_rolling_call_qualified():
    text = (PAD + "Beneficiari: possono presentare domanda i Comuni e le Unioni di Comuni. Le domande sono "
            "valutate a sportello fino ad esaurimento delle risorse disponibili.")
    d = decide("Avviso sport e rigenerazione urbana", text)
    assert d.status == "qualified" and d.rolling and d.deadline is None


def test_partner_role():
    text = (PAD + "Soggetti ammessi: associazioni del terzo settore, che possono presentare il progetto in "
            "partenariato con i Comuni del territorio. Le domande devono essere presentate entro il 20/12/2026.")
    d = decide("Avviso per progetti di inclusione sociale", text)
    assert d.status == "qualified" and d.role == "partner", d


def test_structured_eu_deadline():
    text = (PAD + "Eligible applicants: public authorities, including local authorities and municipalities, "
            "and non-profit organisations established in EU Member States.")
    d = decide("CERV-2026-DAPHNE · Protection of children", text,
               url="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/X",
               deadline_at="2026-11-05")
    assert d.status == "qualified" and d.deadline == "2026-11-05"


def test_execution_deadline_is_not_the_call_deadline():
    text = (PAD + "Possono presentare candidatura gli enti locali. Le candidature potranno essere presentate entro le ore "
            "18.00 del 15 dicembre 2025. I lavori devono essere aggiudicati e conclusi entro il 31 dicembre 2026.")
    d = decide("Avviso antincendio scuole", text, today=date(2026, 3, 1))
    assert d.status == "expired" and d.deadline == "2025-12-15", d


def test_obligation_notice_rejected():
    text = (PAD + "I Comuni beneficiari dei contributi relativi alle annualità 2021-2025 sono tenuti a concludere i "
            "lavori entro il 31 dicembre 2026, trasmettendo la certificazione sulla piattaforma.")
    assert decide("Comunicato contributi investimenti", text).status == "rejected"


def test_subject_before_verb_and_regional_relay():
    text = (PAD + "ANCI Lombardia informa che gli enti locali potranno presentare, dalle ore 10.00 del giorno 5 ottobre "
            "2026 alle ore 23.59 del giorno 23 ottobre 2026, le candidature relative all'allegato Avviso.")
    d = decide("Edilizia scolastica – Interventi urgenti", text, today=date(2026, 10, 6))
    assert d.status == "qualified" and d.deadline == "2026-10-23", d


def test_richest_container_is_read():
    page = ("<html><body><article><p>Anteprima breve</p></article><div class='entry-content'><p>"
            + "Possono presentare domanda i Comuni della Toscana. " * 20 + "</p></div></body></html>")
    assert "Possono presentare domanda" in q.visible_text(page)


def test_old_years_are_skipped_without_download():
    def loader(url, document):
        raise AssertionError("non deve scaricare")
    old = candidate("Avviso pubblico finanziamenti Enti Locali 2018", url="https://x.gov.it/avviso-2018")
    result = {"opportunities": [], "discoveryQueue": [old]}
    q.apply(result, date(2026, 10, 1), loader=loader, build_item=lambda *a: {}, towns=TOWNS)
    assert result["autoQualification"]["rejected"] == 1 and result["autoQualification"]["unreadable"] == 0


def test_eu_city_as_context_or_reserved_is_not_applicant():
    context = (PAD + "Expected outcome: waterfront cities and islands are provided with innovative solutions. "
               "The consortium could include partners supporting knowledge uptake in regions.")
    assert decide("HORIZON-MISS-2027-OCEAN · Coastal resilience", context, deadline_at="2027-09-21",
                  strict_municipal=True).status == "rejected"
    reserved = (PAD + "Applicants: at least one entity in each project must be from one of the 112 cities selected for "
                "the EU Mission on Climate-neutral and Smart Cities; local authorities should be involved.")
    assert decide("HORIZON-MISS-2027-CIT · Wastewater", reserved, deadline_at="2027-09-22",
                  strict_municipal=True).status == "rejected"


def test_curated_previous_entry_is_not_duplicated():
    url = "https://ec.europa.eu/topic-details/CERV-X"
    previous = {"opportunities": [{"url": url, "title": "CERV · scheda curata", "verification_status": "verified"}]}
    result = {"opportunities": [], "discoveryQueue": [candidate("CERV-X · Topic", url=url, structured_text="x")]}
    q.apply(result, date(2026, 10, 1), loader=None, previous=previous, build_item=lambda *a: {}, towns=TOWNS)
    assert result["autoQualification"]["checked"] == 0 and result["opportunities"] == []


def test_recent_rejections_are_not_reread():
    calls = []
    def loader(url, document):
        calls.append(url)
        return "<html><body><main>" + "Comunicato stampa sulla sicurezza. " * 30 + "</main></body></html>"
    queue = [candidate("Notizia varia", url="https://x.gov.it/n1")]
    first = {"opportunities": [], "discoveryQueue": list(queue)}
    q.apply(first, date(2026, 10, 1), loader=loader, build_item=lambda *a: {}, towns=TOWNS)
    assert first["autoQualificationCache"]["https://x.gov.it/n1"]["status"] == "rejected"
    second = {"opportunities": [], "discoveryQueue": list(queue)}
    q.apply(second, date(2026, 10, 3), loader=loader, previous=first, build_item=lambda *a: {}, towns=TOWNS)
    assert len(calls) == 1 and second["autoQualification"]["skippedRecent"] == 1
    third = {"opportunities": [], "discoveryQueue": list(queue)}
    q.apply(third, date(2026, 10, 9), loader=loader, previous=second, build_item=lambda *a: {}, towns=TOWNS)
    assert len(calls) == 2


def test_facility_operator_topic_rejected():
    text = (PAD + "Proposals are expected to run a facility which offers financial support to cities, municipalities "
            "or their groupings. Applicants should mobilise local authorities. The Commission intends to select one "
            "single proposal under this topic.")
    d = decide("LIFE-2026-CET-FACILITY · City facility", text, deadline_at="2026-12-01")
    assert d.status == "rejected" and "gestore" in d.reason


def test_municipality_as_place_is_not_applicant():
    text = (PAD + "Destinatari: le persone fisiche residenti nel comune di Viareggio. Termine: 30 novembre 2026.")
    assert decide("Avviso contributi per l'affitto", text).status == "rejected"


def test_apply_publishes_carries_and_dedups():
    seen = []

    def loader(url, document):
        seen.append((url, document))
        return "<html><body><main>" + SEISMIC + "</main></body></html>"

    def build_item(entry, today, status):
        return {"coverage_id": entry["coverage_id"], "title": entry["title"], "url": entry["url"],
                "deadline_at": entry["deadline_at"], "verification_status": status,
                "presentation": {"condition_label": entry["condition_label"]},
                "municipality_role": entry["municipality_role"]}

    carried = {"coverage_id": "auto-old", "url": "https://x.gov.it/old", "title": "Vecchio avviso",
               "deadline_at": "2026-12-31", "verification_status": q.VERIFICATION_STATUS}
    expired = dict(carried, coverage_id="auto-expired", deadline_at="2026-09-01")
    result = {"opportunities": [{"url": "https://www.example.gov.it/gia", "title": "Già pubblicato"}],
              "discoveryQueue": [candidate("Avviso pubblico prevenzione sismica", url="https://www.example.gov.it/a"),
                                 candidate("Già pubblicato", url="https://www.example.gov.it/gia")]}
    q.apply(result, date(2026, 10, 1), loader=loader, previous={"opportunities": [carried, expired]},
            build_item=build_item, towns=TOWNS)
    ids = [x.get("coverage_id") for x in result["opportunities"]]
    assert "auto-old" in ids and "auto-expired" not in ids
    new = [x for x in result["opportunities"] if x.get("discovery_url") == "https://www.example.gov.it/a"]
    assert len(new) == 1 and new[0]["presentation"]["condition_label"] == q.LABEL
    assert new[0]["municipal_relevance_class"] == "direct_conditional"
    assert [x["url"] for x in result["discoveryQueue"]] == ["https://www.example.gov.it/gia"]
    assert result["autoQualification"]["qualified"] == 1 and result["autoQualification"]["carried"] == 1
    assert ("https://www.example.gov.it/gia", False) not in seen


def test_unreachable_page_is_reported_not_published():
    def loader(url, document):
        raise TimeoutError("timeout")
    result = {"opportunities": [], "discoveryQueue": [candidate("Avviso pubblico", url="https://x.gov.it/b")]}
    q.apply(result, date(2026, 10, 1), loader=loader, build_item=lambda *a: {}, towns=TOWNS)
    assert result["opportunities"] == [] and result["autoQualification"]["unreadable"] == 1
    assert len(result["discoveryQueue"]) == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
    print(f"Qualificazione automatica Radar PASS: {len(tests)} casi")
