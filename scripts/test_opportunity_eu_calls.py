#!/usr/bin/env python3
"""Fonte UE strutturata: ricerca ufficiale e schede topic, con errori espliciti e mai zeri silenziosi."""
import json
from datetime import date

import opportunity_eu_calls as eu
import opportunity_qualifier as q

SOURCE = {"id": "eu-funding-tenders", "label": "UE · Funding & Tenders"}


def search_payload(*rows):
    return json.dumps({"totalResults": len(rows), "results": [
        {"title": r[1], "summary": "Call summary", "metadata": {
            "identifier": [r[0]], "title": [r[1]], "callTitle": ["CERV-2026-DAPHNE"],
            "deadlineDate": [r[2] + "T17:00:00.000+0000"], "startDate": ["2026-07-07T00:00:00.000+0000"],
            "status": ["31094502"]}} for r in rows]}).encode()


DETAILS = {
    "cerv-2026-daphne-children": {"TopicDetails": {"title": "Integrated child protection",
        "description": "<p>Projects funded under this topic support integrated child protection systems.</p>" * 4
                       + "<p>Eligible applicants: public authorities, including local authorities and municipalities, "
                         "and non-profit organisations.</p>"}},
    "smp-2026-xyz": {"TopicDetails": {"title": "Quantum materials",
        "description": "<p>Research on quantum materials for advanced sensors and computing platforms.</p>" * 4
                       + "<p>Eligible applicants: any legal entity, public or private bodies, universities.</p>"}},
}


def poster_for(payload):
    calls = []
    def poster(url, fields, timeout):
        calls.append((url, fields))
        assert "apiKey=SEDIA" in url and json.loads(fields["query"])["bool"]["must"][1]["terms"]["status"]
        return payload
    return poster, calls


def getter(url, timeout):
    key = url.rsplit("/", 1)[-1].removesuffix(".json")
    return json.dumps(DETAILS[key]).encode()


def test_candidates_from_api_and_qualification():
    poster, calls = poster_for(search_payload(
        ("CERV-2026-DAPHNE-CHILDREN", "Integrated child protection", "2026-11-05"),
        ("SMP-2026-XYZ", "Quantum materials", "2026-12-01"),
        ("CERV-2025-OLD", "Closed topic", "2025-04-01"),
        ("EURATOM-2026-X", "Fusion materials", "2026-12-01")))
    DETAILS["cerv-2025-old"] = DETAILS["smp-2026-xyz"]
    DETAILS["euratom-2026-x"] = DETAILS["smp-2026-xyz"]
    out, state = eu.candidates(SOURCE, date(2026, 10, 1), poster=poster, getter=getter)
    assert state["status"] == "ok" and state["rawResults"] == 4 and len(calls) == 1
    titles = {c["title"]: c for c in out}
    assert "CERV-2025-OLD · Closed topic" not in titles, "topic scaduti esclusi"
    assert "EURATOM-2026-X · Fusion materials" not in titles, "programmi senza ruolo comunale esclusi"
    child = titles["CERV-2026-DAPHNE-CHILDREN · Integrated child protection"]
    assert child["deadline_at"] == "2026-11-05" and child["strict_municipal"] and child["url"].endswith("CERV-2026-DAPHNE-CHILDREN")
    assert q.qualify(child, child["structured_text"], {}, date(2026, 10, 1)).status == "qualified"
    quantum = titles["SMP-2026-XYZ · Quantum materials"]
    assert q.qualify(quantum, quantum["structured_text"], {}, date(2026, 10, 1)).status == "rejected", \
        "«public bodies» generico non basta per i programmi UE"


def test_api_failure_is_an_error_not_zero():
    def broken(url, fields, timeout):
        raise TimeoutError("timeout")
    try:
        eu.candidates(SOURCE, date(2026, 10, 1), poster=broken, getter=getter)
    except RuntimeError as exc:
        assert "timeout" in str(exc)
    else:
        raise AssertionError("una ricerca fallita deve essere un errore")


def test_empty_api_is_degraded():
    poster, _ = poster_for(search_payload())
    out, state = eu.candidates(SOURCE, date(2026, 10, 1), poster=poster, getter=getter)
    assert out == [] and state["status"] == "degraded"


def test_silent_zero_tracking_and_lag():
    previous = {"discoverySources": [{"sourceId": "a", "zeroStreak": 13}, {"sourceId": "b", "zeroStreak": 4}]}
    result = {"discoverySources": [
        {"sourceId": "a", "status": "ok", "silentZero": True, "listingChars": 9000},
        {"sourceId": "b", "status": "ok", "silentZero": True, "listingChars": 600},
        {"sourceId": "c", "status": "ok", "silentZero": False, "listingChars": 9000},
        {"sourceId": "d", "status": "error"}],
        "opportunities": [{"title": "X", "url": "u", "published_at": "2026-07-07", "first_seen_at": "2026-10-28"},
                          {"title": "Y", "url": "v", "published_at": "2026-10-20", "first_seen_at": "2026-10-21"}]}
    broken = {row["sourceId"]: row for row in q.track_silent_zero(result, previous)}
    assert set(broken) == {"a", "b", "d"} and broken["a"]["zeroStreak"] == 14
    assert "JavaScript" in broken["b"]["reason"]
    lag = q.detection_lag(result, date(2026, 10, 30))
    assert lag["sample"] == 2 and [r["title"] for r in lag["late"]] == ["X"] and lag["late"][0]["lagDays"] == 113


def test_blocked_source_covered_by_others_is_not_to_repair():
    waf = {"sourceId": "gse", "status": "error", "failureClasses": ["http_403_waf"],
           "endpointResults": [{"failureClass": "http_403_waf", "terminalFailureClass": "http_401"}]}
    result = {"discoverySources": [dict(waf), {"sourceId": "mase-bandi", "status": "ok"}]}
    assert q.track_silent_zero(result, None) == []
    assert result["sourcesBlockedCovered"][0]["coveredBy"] == ["mase-bandi"]
    # Senza fonti di copertura raggiungibili il blocco resta da riparare.
    alone = {"discoverySources": [dict(waf), {"sourceId": "mase-bandi", "status": "degraded"}]}
    assert [row["sourceId"] for row in q.track_silent_zero(alone, None)] == ["gse"]
    assert alone["sourcesBlockedCovered"] == []
    # Un errore che non è un blocco del sito (timeout) resta da riparare.
    timeout = dict(waf, failureClasses=["timeout_client"], endpointResults=[{"failureClass": "timeout_client"}])
    other = {"discoverySources": [timeout, {"sourceId": "mase-bandi", "status": "ok"}]}
    assert [row["sourceId"] for row in q.track_silent_zero(other, None)] == ["gse"]


FICHE_HEADER = "Call: CERV-2026-DAPHNE: Call for proposals to prevent and combat gender -based violence \nagainst children \n"
FICHE_PAGES = [
    "Priority 3 - Targeted actions for the prevention of gender-based violence [Topic CERV-2026-DAPHNE-PREVENTION] "
    "Projects should prevent violence. " + "Awareness raising and education activities are funded. " * 20,
    "Applicants are encouraged to also involve a public authority in support of their project. "
    "These public authorities can be national, regional or local Ministries/agencies/equality bodies "
    "responsible for gender equality. Involvement of a public authority in the consortium (either as beneficiary "
    "or as associated partner) will be taken into account. "
    # La priorità successiva apre con la frase sui coordinatori, prima del suo marcatore.
    "Priority 4 - Supporting the Convention objectives. While the coordinators of proposals to be submitted "
    "under this Priority must be public authorities (relevant national, regional or local authorities), we "
    "encourage consortium partners. [Topic CERV-2026-DAPHNE-CONVENTION-DIR] " + "Training of professionals. " * 20,
    "Priority 5 – Strengthening integrated child protection systems [Topic CERV-2026-DAPHNE-CHILDREN] "
    "The involvement of stakeholders – and notably public authorities at local level - in the project is "
    "essential under this priority. The participation of a public authority is mandatory under this priority. "
    "The call emphasises collaboration between public authorities (local, regional, national) and other "
    "key stakeholders. " + "Child protection systems are strengthened. " * 20,
]


def fiche_document():
    return eu.strip_running_headers([f"{FICHE_HEADER}  \n{n} \n{page}" for n, page in enumerate(FICHE_PAGES, 12)])


def test_running_header_does_not_enter_citations():
    document = fiche_document()
    assert "Call: CERV-2026-DAPHNE" not in document and " 13 " not in document, document[:200]
    assert document.startswith("Priority 3 - Targeted actions")
    # Un PDF senza intestazione ripetuta resta intatto.
    assert eu.strip_running_headers(["Uno due tre.", "Quattro cinque.", "Sei sette."]) == \
        "Uno due tre. Quattro cinque. Sei sette."


def test_topic_section_stops_at_next_priority_heading():
    """Un topic non eredita i requisiti della priorità vicina nello stesso documento."""
    document = fiche_document()
    prevention = eu.topic_section(document, "CERV-2026-DAPHNE-PREVENTION")
    convention = eu.topic_section(document, "CERV-2026-DAPHNE-CONVENTION-DIR")
    children = eu.topic_section(document, "CERV-2026-DAPHNE-CHILDREN")
    assert "coordinators of proposals" not in prevention and "encouraged to also involve" in prevention
    assert convention.startswith("Priority 4") and "coordinators of proposals" in convention
    assert children.startswith("Priority 5") and "coordinators of proposals" not in children
    assert eu.topic_section(document, "CERV-2026-DAPHNE-REGRANTING") == ""
    today = date(2026, 11, 1)

    def decide(identifier, section):
        candidate = {"title": identifier, "deadline_at": "2026-11-05", "strict_municipal": True}
        return q.qualify(candidate, f"{identifier}. {section}", {}, today)

    assert (decide("CERV-2026-DAPHNE-PREVENTION", prevention).role, decide("CERV-2026-DAPHNE-CONVENTION-DIR", convention).role,
            decide("CERV-2026-DAPHNE-CHILDREN", children).role) == ("partner", "direct_applicant", "partner"), \
        "autorità pubblica raccomandata o obbligatoria = partner; capofila solo dove il testo lo richiede"
    # Con la vecchia finestra fissa di 1.500 caratteri CHILDREN citava la frase
    # sui coordinatori della priorità 4 e risultava richiedente diretto.
    assert "coordinators" not in decide("CERV-2026-DAPHNE-CHILDREN", children).applicant


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
    print(f"Fonte UE strutturata e salute delle fonti Radar PASS: {len(tests)} casi")
