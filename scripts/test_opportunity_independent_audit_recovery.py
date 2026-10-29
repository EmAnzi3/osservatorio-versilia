#!/usr/bin/env python3
"""Blocco regressione: il recupero holdout pubblica SOLO su fonte primaria verificata."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import opportunity_independent_audit_recovery as recovery
import opportunity_municipal_relevance as relevance


def _fixture(entry):
    # Estratto di prova isolato: non è evidenza per la produzione.
    return "<main><p>" + " | ".join(entry["required_terms"]) + "</p></main>"


def test_offline_pending_does_not_block_or_publish() -> None:
    result = {"opportunities": [], "coverageHold": [], "counts": {}}
    recovery.apply(result, date(2026, 10, 28), live=False)
    assert result["opportunities"] == []
    assert result["coverageHold"] == []
    assert result["auditRecovery"]["checked"] == 5
    assert len(result["auditRecovery"]["pending"]) == 5
    assert result["auditRecovery"]["blocksPublication"] is False


def test_documented_live_promotion_and_dedup() -> None:
    entries = recovery._entries()
    assert len(entries) == 5
    payloads = {entry["url"]: _fixture(entry) for entry in entries}
    result = {"opportunities": [], "coverageHold": [], "counts": {}}
    recovery.apply(result, date(2026, 10, 28), live=False, detail_payloads=payloads)
    assert len(result["opportunities"]) == 5
    assert result["auditRecovery"]["pending"] == []
    assert len({x["coverage_id"] for x in result["opportunities"]}) == 5
    assert all(x.get("verified_direct") for x in result["opportunities"])
    assert all(x["source_verification"]["type"] == "offline_test_fixture" for x in result["opportunities"])
    relevance.apply_to_payload(result)
    assert result["municipalRelevance"]["headlineTotal"] == 2
    assert result["municipalRelevance"]["partnershipTotal"] == 3
    # Le partnership non devono diventare candidature comunali dirette.
    for x in result["opportunities"]:
        if x["municipality_role"] == "partner":
            assert x["applicant_eligibility"] == "not_direct_applicant"
            assert x["municipal_headline"] is False
    recovery.apply(result, date(2026, 10, 28), live=False, detail_payloads=payloads)
    assert len(result["opportunities"]) == 5
    assert len(result["auditRecovery"]["alreadyRepresented"]) == 5


def test_modified_deadline_or_municipality_evidence_never_promotes() -> None:
    entries = recovery._entries()
    data = {}
    for entry in entries:
        replacement = _fixture(entry)
        # Nel body primario: se non compare più la scadenza, non pubblicare.
        replacement = replacement.replace(entry["required_terms"][1], "termine aggiornato da verificare")
        data[entry["url"]] = replacement
    result = {"opportunities": [], "coverageHold": []}
    recovery.apply(result, date(2026, 10, 28), live=False, detail_payloads=data)
    assert len(result["opportunities"]) == 0
    assert len(result["auditRecovery"]["pending"]) == 5
    assert result["coverageHold"] == []


def test_expired_never_promotes_and_host_contract() -> None:
    entries = recovery._entries()
    result = {"opportunities": []}
    recovery.apply(result, date(2026, 11, 21), live=False,
                   detail_payloads={e["url"]: _fixture(e) for e in entries})
    assert result["opportunities"] == []
    assert len(result["auditRecovery"]["expired"]) == 5
    assert all(e["review_policy"] == "opportunistic" for e in entries)
    assert all(not e["allow_recent_evidence_fallback"] for e in entries)



def test_reader_proxy_and_external_redirect_never_promote() -> None:
    """Un DOM che sembra corretto non basta a provarne la provenienza."""
    entries = recovery._entries()
    standard = [e for e in entries if not e.get("primary_composite_topic")]
    fixtures = {e["url"]: _fixture(e) for e in standard}
    def simulated_response(url, *, transport, proxy, final_url=None):
        return fixtures[url], {
            "status": "ok", "transport": transport, "proxyUsed": proxy,
            "resolvedUrl": final_url or url,
        }

    for transport, proxy, redirect in (
        ("reader_proxy", True, None),
        ("reader_proxy", False, None),
        ("http_browser", True, None),
        ("http_browser", False, "https://r.jina.ai/https://anci.lombardia.it/"),
        ("http_browser", False, "http://anci.lombardia.it/"),
        ("http_browser", False, "https://anci.lombardia.it:invalid/path"),
    ):
        result = {"opportunities": [], "coverageHold": []}
        with patch.object(recovery.daphne, "verify_live",
                          side_effect=recovery.daphne.PrimaryEvidenceError("prova UE non disponibile")):
            with patch.object(recovery.discovery, "fetch_with_diagnostics",
                              side_effect=lambda url, **kw: simulated_response(
                                  url, transport=transport, proxy=proxy, final_url=redirect)):
                recovery.apply(result, date(2026, 10, 28), live=True)
        assert not result["opportunities"], (transport, proxy, redirect)
        assert len(result["auditRecovery"]["pending"]) == len(entries)
        assert result["coverageHold"] == []

    result = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.daphne, "verify_live",
                      side_effect=recovery.daphne.PrimaryEvidenceError("prova UE non disponibile")):
        with patch.object(recovery.discovery, "fetch_with_diagnostics",
                          side_effect=lambda url, **kw: simulated_response(
                              url, transport="http_browser", proxy=False)):
            recovery.apply(result, date(2026, 10, 28), live=True)
    assert len(result["opportunities"]) == len(standard)
    assert len(result["auditRecovery"]["pending"]) == len(entries) - len(standard)
    assert all(x["source_verification"]["type"] == "official_primary_webpage"
               and x["source_verification"]["proxy_used"] is False
               for x in result["opportunities"])


def test_bounded_live_fetch_passes_transport_deadline() -> None:
    """Il budget holdout ordinario resta invariato; DAPHNE usa due prove a parte."""
    entries = recovery._entries()
    ordinary = [e for e in entries if not e.get("primary_composite_topic")]
    fixtures = {e["url"]: _fixture(e) for e in ordinary}
    calls: list[float] = []

    class FakeBudget:
        def fetch(self, url, **kwargs):
            assert kwargs.get("max_seconds") is not None
            calls.append(float(kwargs["max_seconds"]))
            return fixtures[url], {
                "status": "ok", "transport": "http_browser",
                "proxyUsed": False, "resolvedUrl": url, "errors": [],
            }

    result = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.discovery, "LIVE_BUDGET", FakeBudget()):
        with patch.object(recovery.daphne, "verify_live",
                          side_effect=recovery.daphne.PrimaryEvidenceError("prova UE non disponibile")):
            recovery.apply(result, date(2026, 10, 28), live=True)
    assert len(result["opportunities"]) == len(ordinary)
    assert len(calls) == len(ordinary)
    assert all(0 < value <= 4.0 for value in calls), calls
    assert sum(calls) <= 20.0

def test_live_fixture_override_is_rejected() -> None:
    first = recovery._entries()[0]
    try:
        recovery.apply({"opportunities": []}, date(2026, 10, 28),
                       live=True, detail_payloads={first["url"]: _fixture(first)})
    except ValueError as exc:
        assert "fixture" in str(exc)
    else:
        raise AssertionError("Test payload must not be accepted in production verification")


def test_anci_favicon_local_in_full_release() -> None:
    """La fonte recuperata deve avere un'icona locale prima del gate di build."""
    import tempfile
    from pathlib import Path
    from xml.etree import ElementTree

    import materialize_opportunity_release_favicons as favicons

    entry = next(e for e in recovery._entries()
                 if e["coverage_id"] == "n-anci-conai-comunicazione-locale-2026")
    assert "anci.lombardia.it" in entry["url"]
    payload = {"opportunities": [{"title": entry["title"], "source_id": entry["source_id"],
                                   "url": entry["url"], "presentation": {}}], "archive": []}
    with tempfile.TemporaryDirectory(prefix="radar-anci-icon-") as folder:
        dist = Path(folder)
        provenance = favicons.materialize(payload, dist)
        favicons.apply_to_payload(payload, provenance)
        family = "generated:anci.lombardia.it"
        assert payload["opportunities"][0]["presentation"]["source_favicon_family"] == family
        local = payload["opportunities"][0]["presentation"]["source_favicon"]
        assert local.endswith("source-anci-lombardia-it.svg")
        artifact = dist / "assets" / "source-favicons" / "source-anci-lombardia-it.svg"
        assert artifact.is_file() and artifact.stat().st_size > 0
        assert ElementTree.fromstring(artifact.read_bytes()).tag.endswith("svg")
        assert ">ANCI</text>" in artifact.read_text(encoding="utf-8")



def test_anci_alternate_primary_requires_live_same_host() -> None:
    """Un mirror ufficiale ANCI e' valido solo con prova primaria diretta."""
    entry = next(e for e in recovery._entries()
                 if e["coverage_id"] == "n-anci-conai-comunicazione-locale-2026")
    alternate = entry["alternate_primary_pages"][0]
    assert len(alternate["required_terms"]) >= len(entry["required_terms"])
    attempts = []

    def fetch(url, **kwargs):
        attempts.append(url)
        if url == entry["url"]:
            raise TimeoutError("ANCI Lombardia: timeout nel runner")
        if url == alternate["url"]:
            return _fixture(alternate), {
                "status": "ok", "transport": "http_browser",
                "proxyUsed": False, "resolvedUrl": url,
            }
        raise TimeoutError("Altri holdout non disponibili")

    result = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.daphne, "verify_live", side_effect=recovery.daphne.PrimaryEvidenceError("non disponibile")):
        with patch.object(recovery.discovery, "fetch_with_diagnostics", side_effect=fetch):
            recovery.apply(result, date(2026, 10, 29), live=True)
    recovered = [item for item in result["opportunities"]
                 if item.get("coverage_id") == entry["coverage_id"]]
    assert len(recovered) == 1
    assert recovered[0]["url"] == alternate["url"]
    assert recovered[0]["source_verification"]["url"] == alternate["url"]
    assert recovered[0]["source_verification"]["transport"] == "http_browser"
    assert recovered[0]["presentation"]["source_label"] == alternate["source_label"]
    assert attempts[:2] == [entry["url"], alternate["url"]]

    def wrong_redirect(url, **kwargs):
        if url == entry["url"]:
            raise TimeoutError("ANCI Lombardia: timeout")
        if url == alternate["url"]:
            return _fixture(alternate), {
                "status": "ok", "transport": "http_browser", "proxyUsed": False,
                "resolvedUrl": "https://not-anci.example/other",
            }
        raise TimeoutError("Altri holdout non disponibili")

    rejected = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.daphne, "verify_live", side_effect=recovery.daphne.PrimaryEvidenceError("non disponibile")):
        with patch.object(recovery.discovery, "fetch_with_diagnostics", side_effect=wrong_redirect):
            recovery.apply(rejected, date(2026, 10, 29), live=True)
    assert not any(i.get("coverage_id") == entry["coverage_id"]
                   for i in rejected["opportunities"])
    assert any(p.get("coverage_id") == entry["coverage_id"]
               for p in rejected["auditRecovery"]["pending"])



def test_daphne_two_primary_sources_and_fail_closed() -> None:
    """PDF e portale UE devono attestare topic, ruolo e scadenza, distintamente."""
    daphne = recovery.daphne
    daphne_entries = [e for e in recovery._entries() if e.get("primary_composite_topic")]
    assert len(daphne_entries) == 2
    role_text = (
        "For priority 1 and 4, proposals can be submitted by either a single applicant. "
        "For priority 4: lead applicants must be public authorities either at national, "
        "regional or local level. "
        "For priorities 2, 3, and 5, proposals must be submitted by a consortium of at least 2 applicants. "
        "For priorities 1, 2, 3 and 5: lead applicants must be non-profit making."
    )
    for entry in daphne_entries:
        topic = entry["primary_composite_topic"]
        pages = {
            3: "Call for proposals " + topic,
            14: "The participation of a public authority is mandatory under this priority.",
            31: role_text,
        }
        portal = (topic + " Topic Calls for proposals Open For Submission "
                  "Opening date 07 July 2026 Deadline date 05 November 2026 17:00:00 Brussels time")
        assert daphne.validate_pdf_pages(pages, topic)
        assert daphne.validate_portal_text(portal, topic, date(2026, 11, 5))
        pdf_audit = {"url": daphne.PDF_URL, "resolved_url": daphne.PDF_URL,
                     "transport": "direct_https_pdf", "proxy_used": False, "sha256": "test"}
        portal_audit = {"url": entry["url"], "resolved_url": entry["url"],
                        "transport": "chromium_https", "proxy_used": False, "sha256": "test"}
        with patch.object(daphne, "fetch_pdf_live", return_value=(pages, dict(pdf_audit))):
            with patch.object(daphne, "fetch_portal_live", return_value=(portal, dict(portal_audit))):
                evidence = daphne.verify_live(entry, date(2026, 10, 29))
        assert evidence["type"] == "official_primary_composite"
        assert len(evidence["evidence_sources"]) == 2
        assert evidence["proxy_used"] is False

        for wrong_pdf in ({3: "other topic", 14: pages[14], 31: pages[31]},
                          {3: pages[3], 14: "", 31: ""}):
            try:
                daphne.validate_pdf_pages(wrong_pdf, topic)
            except daphne.PrimaryEvidenceError:
                pass
            else:
                raise AssertionError("PDF incompleto promosso")

        for wrong_portal in (
            topic + " Open For Submission Deadline date 03 November 2026",
            "OTHER-TOPIC Open For Submission Deadline date 05 November 2026",
            topic + " Deadline date 05 November 2026",
        ):
            try:
                daphne.validate_portal_text(wrong_portal, topic, date(2026, 11, 5))
            except daphne.PrimaryEvidenceError:
                pass
            else:
                raise AssertionError("Portale UE incompleto promosso")

        for wrong_audit in (
            dict(portal_audit, proxy_used=True),
            dict(portal_audit, resolved_url="https://reader.example/doc"),
            dict(portal_audit, transport="reader_proxy"),
        ):
            with patch.object(daphne, "fetch_pdf_live", return_value=(pages, dict(pdf_audit))):
                with patch.object(daphne, "fetch_portal_live", return_value=(portal, wrong_audit)):
                    try:
                        daphne.verify_live(entry, date(2026, 10, 29))
                    except daphne.PrimaryEvidenceError:
                        pass
                    else:
                        raise AssertionError("Trasporto UE non primario promosso")

        with patch.object(daphne, "fetch_pdf_live", side_effect=AssertionError("non chiamare")):
            try:
                daphne.verify_live(entry, date(2026, 11, 6))
            except daphne.PrimaryEvidenceError:
                pass
            else:
                raise AssertionError("Scadenza trascorsa promossa")
        for invalid_url in ("http://ec.europa.eu/x",
                            "https://reader.example/x",
                            "https://ec.europa.eu@reader.example/x",
                            "https://ec.europa.eu:invalid/x"):
            try:
                daphne._official_url(invalid_url)
            except daphne.PrimaryEvidenceError:
                pass
            else:
                raise AssertionError("URL non primario accettato")

    # Mancando la seconda prova, non entra alcuna scheda DAPHNE nello snapshot.
    result = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.discovery, "fetch_with_diagnostics",
                      side_effect=TimeoutError("fonti ordinarie non disponibili")):
        with patch.object(daphne, "verify_live",
                          side_effect=daphne.PrimaryEvidenceError("deadline non validata")):
            recovery.apply(result, date(2026, 10, 29), live=True)
    assert not result["opportunities"]
    assert len(result["auditRecovery"]["pending"]) == len(recovery._entries())
    assert sum(1 for e in result["auditRecovery"]["pending"]
               if "daphne" in e["coverage_id"]) == 2


def main() -> int:
    test_offline_pending_does_not_block_or_publish()
    test_documented_live_promotion_and_dedup()
    test_modified_deadline_or_municipality_evidence_never_promotes()
    test_expired_never_promotes_and_host_contract()
    test_anci_favicon_local_in_full_release()
    test_reader_proxy_and_external_redirect_never_promote()
    test_live_fixture_override_is_rejected()
    test_bounded_live_fetch_passes_transport_deadline()
    test_anci_alternate_primary_requires_live_same_host()
    test_daphne_two_primary_sources_and_fail_closed()
    print("Recupero indipendente Radar: 10 contratti PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
