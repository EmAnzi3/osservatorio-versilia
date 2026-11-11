"""Regola unica di rilettura delle pagine ufficiali del Radar (nessuna rete)."""
from __future__ import annotations

import copy
from datetime import date

import opportunity_official_recheck as recheck

TODAY = date(2026, 11, 10)
FILLER = " Informazioni generali sul programma, documentazione e modulistica disponibili. " * 4

# Testi ricalcati sulle pagine ufficiali lette il 10/11/2026.
SAI_PAGE = (
    "Sistema di Accoglienza e Integrazione SAI. 05/11/2026 Proroga del termine per la presentazione "
    "delle istanze per il finanziamento di nuovi progetti SAI. Prorogato al 10 dicembre 2026, ore 18:00, "
    "il termine per la presentazione delle domande di finanziamento. 21/10/2026 Dal 22 ottobre 2026 le "
    "richieste di assistenza al ServiceDesk vanno inviate via mail. 15/09/2026 Proroga del termine per la "
    "presentazione delle istanze di prosecuzione – Progetti SAI in scadenza al 31 dicembre 2026." + FILLER
)
EUCF_PAGE = (
    "European City Facility. The eighth call of the European City Facility is open for applications from "
    "today, 26 October 2026. It closes on 21 December 2026 at 17:00 Brussels time. The European City "
    "Facility's next call for applications opens on 26 October 2026, the programme has announced." + FILLER
)
C3_PAGE = (
    "Circular City Centre (C3). New call for C3 advisory programmes – Submit your Expression of Interest "
    "for the CCA programme by 13 November 2026. The next C3 Q&A session will be announced soon. "
    "© European Investment Bank 2025" + FILLER
)


def _item(**kw):
    base = {
        "id": "opp-x", "coverage_id": "cov-x", "source_id": "municipal-matrix-v1", "title": "Titolo",
        "url": "https://example.org/x", "status": "open", "lifecycle_stage": "application_open",
        "opens_at": None, "deadline_at": None, "deadline_time": None, "verified_at": TODAY.isoformat(),
    }
    base.update(kw)
    return base


def _run(items, texts, previous=None, errors=None):
    return recheck.apply(items, TODAY, previous=previous,
                         pages={"texts": texts, "errors": errors or {}})


def test_sai_extension_replaces_static_deadline():
    item = _item(coverage_id="sai-2026-ordinary-2402", title="Ministero dell'Interno · SAI 2026 · 2.402 posti ordinari",
                 url="https://fnasilo.dlci.interno.it/sprar/", opens_at="2026-09-15", deadline_at="2026-11-10")
    summary = _run([item], {item["url"]: SAI_PAGE})
    assert item["deadline_at"] == "2026-12-10" and item["deadline_time"] == "18:00", item
    assert item["opens_at"] == "2026-09-15" and item["lifecycle_stage"] == "application_open"
    assert item["official_recheck"]["outcome"] == "updated" and summary["updated"] == 1
    assert item["verified_at"] == TODAY.isoformat()


def test_eucf_window_opens_announced_call():
    item = _item(source_id="eu-eucf", title="European City Facility — 8ª call", status="upcoming",
                 lifecycle_stage="announced_upcoming")
    _run([item], {item["url"]: EUCF_PAGE})
    assert (item["opens_at"], item["deadline_at"], item["deadline_time"]) == ("2026-10-26", "2026-12-21", "17:00"), item
    assert item["lifecycle_stage"] == "application_open" and item["status"] == "open"


def test_c3_single_page_deadline_closes_rolling_entry():
    item = _item(source_id="audit-corpus-v1", title="EIB Circular City Centre - C3", lifecycle_stage="rolling_open")
    _run([item], {item["url"]: C3_PAGE})
    assert item["deadline_at"] == "2026-11-13" and item["lifecycle_stage"] == "application_open", item


def test_confirmed_deadline_and_time_from_page():
    item = _item(title="Bando parcheggi 2026", deadline_at="2026-11-30")
    page = "Bando parcheggi 2026: le domande vanno presentate entro il 30 novembre 2026 ore 13:00." + FILLER
    _run([item], {item["url"]: page})
    assert item["deadline_at"] == "2026-11-30" and item["deadline_time"] == "13:00"
    assert item["official_recheck"]["outcome"] == "updated"


def test_range_with_implicit_year():
    item = _item(title="Avviso Famiglia spazi giovani", lifecycle_stage="announced_upcoming", status="upcoming")
    page = "Avviso Famiglia: domande dal 11 novembre al 13 novembre 2026 ore 12:00." + FILLER
    _run([item], {item["url"]: page})
    assert (item["opens_at"], item["deadline_at"], item["deadline_time"]) == ("2026-11-11", "2026-11-13", "12:00"), item
    assert item["lifecycle_stage"] == "announced_upcoming"


def test_ambiguous_page_keeps_item_and_flags_it():
    item = _item(title="Horizon Europe cluster", deadline_at="2026-12-01")
    page = ("Horizon Europe cluster topics: deadline 15 January 2027 for topic A; deadline 20 February 2027 "
            "for topic B." + FILLER)
    _run([item], {item["url"]: page})
    assert item["deadline_at"] == "2026-12-01"
    assert item["official_recheck"]["outcome"] == "unconfirmed"


def test_news_dates_do_not_borrow_keywords():
    facts = recheck.extract_facts("Progetti in scadenza al 31.12.2026 21/10/2026 Notizia generica.")
    roles = {row["date"].isoformat(): row["role"] for row in facts["dates"]}
    assert roles == {"2026-12-31": "deadline", "2026-10-21": None}, roles


def test_unreachable_static_item_keeps_last_real_read():
    item = _item(coverage_id="sai-2026-ordinary-2402", title="SAI 2026", deadline_at="2026-11-10")
    previous = {"opportunities": [dict(copy.deepcopy(item), official_recheck={
        "last_ok_at": "2026-11-08",
        "facts": {"deadline_at": "2026-12-10", "deadline_time": "18:00", "opens_at": "2026-09-15",
                  "lifecycle_stage": "application_open", "status": "open"},
    })]}
    summary = _run([item], {}, previous=previous, errors={item["url"]: "timeout"})
    assert item["verified_at"] == "2026-11-08", item
    assert item["deadline_at"] == "2026-12-10" and item["official_recheck"]["outcome"] == "unreachable"
    assert summary["unreachable"] == 1 and summary["stale"] == 0


def test_never_read_static_item_is_not_marked_verified_today():
    item = _item(title="CINEA Green Assist")
    summary = _run([item], {}, errors={item["url"]: "HTTP 403"})
    assert item["verified_at"] is None and summary["stale"] == 1


def test_live_scanned_item_keeps_engine_verification_when_page_fails():
    item = _item(source_id="regione-toscana", title="Bando parcheggi 2026", verified_at="2026-11-10")
    _run([item], {}, errors={item["url"]: "timeout"})
    assert item["verified_at"] == "2026-11-10"


def test_error_page_is_not_a_reading():
    item = _item(title="SAI 2026", deadline_at="2026-11-10")
    _run([item], {item["url"]: "404 Page not found" + " x" * 120})
    assert item["official_recheck"]["outcome"] == "unreachable" and item["verified_at"] is None


def test_extension_on_alternate_official_url():
    item = _item(title="SAI 2026 MSNA", deadline_at="2026-11-10",
                 official_urls=["https://fnasilo.dlci.interno.it/sprar/"])
    _run([item], {"https://fnasilo.dlci.interno.it/sprar/": SAI_PAGE}, errors={item["url"]: "timeout"})
    assert item["deadline_at"] == "2026-12-10"


def test_expired_item_is_not_revived_by_other_future_dates():
    item = _item(title="Erasmus Accreditation KA120", deadline_at="2026-09-29")
    page = "Erasmus accreditation KA120: accreditations are valid until 31 December 2027." + FILLER
    _run([item], {item["url"]: page})
    assert item["deadline_at"] == "2026-09-29", item


def test_expired_item_is_revived_by_explicit_extension():
    item = _item(title="Cultura Missione Comune 2026", deadline_at="2026-11-05")
    page = "Cultura Missione Comune 2026: termine prorogato al 5 dicembre 2026 ore 12:00." + FILLER
    _run([item], {item["url"]: page})
    assert item["deadline_at"] == "2026-12-05" and item["deadline_time"] == "12:00"


def test_section_page_extension_reaches_notice_url():
    item = _item(title="Ministero dell'Interno · SAI 2026 · 500 posti MSNA", deadline_at="2026-11-10",
                 url="https://fnasilo.dlci.interno.it/sprar/secure/notiziaVisualizza/64")
    notice = "Avviso SAI 2026 MSNA: domande entro il 10 novembre 2026." + FILLER
    texts = {item["url"]: notice, "https://fnasilo.dlci.interno.it/sprar/": SAI_PAGE}
    assert recheck.section_root(item["url"]) == "https://fnasilo.dlci.interno.it/sprar/"
    _run([item], texts)
    assert item["deadline_at"] == "2026-12-10" and item["deadline_time"] == "18:00", item


def test_section_page_extension_of_another_call_is_ignored():
    item = _item(title="Bando parcheggi 2026", deadline_at="2026-11-30",
                 url="https://www.regione.toscana.it/bandi/parcheggi")
    notice = "Bando parcheggi 2026: domande entro il 30 novembre 2026." + FILLER
    section = "Contributi alle imprese agricole: termine prorogato al 20 dicembre 2026." + FILLER
    _run([item], {item["url"]: notice, "https://www.regione.toscana.it/bandi/": section})
    assert item["deadline_at"] == "2026-11-30"


def test_existing_deadline_is_not_replaced_by_another_phase_date():
    item = _item(title="Assistenti sociali · Adesione di Comuni e ATS al concorso nazionale",
                 deadline_at=TODAY.isoformat())
    page = ("Assistenti sociali, adesione di Comuni e ATS: le assunzioni dei vincitori del concorso "
            "dovranno avvenire entro il 5 febbraio 2027." + FILLER)
    _run([item], {item["url"]: page})
    assert item["deadline_at"] == TODAY.isoformat(), item
    assert item["official_recheck"]["outcome"] == "unconfirmed"


def test_recheck_uses_own_budget_and_returns_scan_time():
    import threading
    import time
    import types

    class Budget:
        def __init__(self):
            self.deadline, self.lock = 100.0, threading.Condition()

    main_budget, seen = Budget(), []
    discovery = types.SimpleNamespace(LIVE_BUDGET=main_budget)

    def work():
        seen.append(discovery.LIVE_BUDGET)
        time.sleep(0.05)
        return "ok"

    assert recheck.run_with_own_budget(discovery, work, make_budget=Budget) == "ok"
    assert seen[0] is not main_budget and discovery.LIVE_BUDGET is main_budget
    assert main_budget.deadline >= 100.05
    offline = types.SimpleNamespace(LIVE_BUDGET=None)
    assert recheck.run_with_own_budget(offline, lambda: 1, make_budget=Budget) == 1


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
    print(f"OFFICIAL RECHECK PASS: {len(tests)} casi")


if __name__ == "__main__":
    main()
