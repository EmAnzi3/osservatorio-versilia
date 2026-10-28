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
    """An apparent matching source page is not enough to establish provenance."""
    entries = recovery._entries()
    fixtures = {e["url"]: _fixture(e) for e in entries}

    def simulated_response(url, *, transport, proxy, final_url=None):
        return (fixtures[url], {
            "status": "ok", "transport": transport, "proxyUsed": proxy,
            "resolvedUrl": final_url or url,
        })

    for transport, proxy, redirect in (
        ("reader_proxy", True, None),
        ("reader_proxy", False, None),  # Unknown/unsupported transport is never accepted.
        ("http_browser", True, None),  # Contradictory diagnostics must fail closed.
        ("http_browser", False, "https://r.jina.ai/https://anci.lombardia.it/"),
        ("http_browser", False, "http://anci.lombardia.it/"),
        ("http_browser", False, "https://anci.lombardia.it:invalid/path"),
    ):
        result = {"opportunities": [], "coverageHold": []}
        with patch.object(recovery.discovery, "fetch_with_diagnostics",
                          side_effect=lambda url, **kw: simulated_response(
                              url, transport=transport, proxy=proxy, final_url=redirect)):
            recovery.apply(result, date(2026, 10, 28), live=True)
        assert not result["opportunities"], (transport, proxy, redirect)
        assert len(result["auditRecovery"]["pending"]) == len(entries)
        assert result["coverageHold"] == []

    result = {"opportunities": [], "coverageHold": []}
    with patch.object(recovery.discovery, "fetch_with_diagnostics",
                      side_effect=lambda url, **kw: simulated_response(
                          url, transport="http_browser", proxy=False)):
        recovery.apply(result, date(2026, 10, 28), live=True)
    assert len(result["opportunities"]) == len(entries)
    assert all(x["source_verification"]["type"] == "official_primary_webpage"
               and x["source_verification"]["proxy_used"] is False
               and x["source_verification"]["transport"] == "http_browser"
               for x in result["opportunities"])


def test_bounded_live_fetch_passes_transport_deadline() -> None:
    """The 18-second holdout budget must also reach the subprocess transport."""
    entries = recovery._entries()
    fixtures = {e["url"]: _fixture(e) for e in entries}
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
        recovery.apply(result, date(2026, 10, 28), live=True)
    assert len(result["opportunities"]) == len(entries)
    assert len(calls) == len(entries)
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


def main() -> int:
    test_offline_pending_does_not_block_or_publish()
    test_documented_live_promotion_and_dedup()
    test_modified_deadline_or_municipality_evidence_never_promotes()
    test_expired_never_promotes_and_host_contract()
    test_anci_favicon_local_in_full_release()
    test_reader_proxy_and_external_redirect_never_promote()
    test_live_fixture_override_is_rejected()
    test_bounded_live_fetch_passes_transport_deadline()
    print("Recupero indipendente Radar: 8 contratti PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
