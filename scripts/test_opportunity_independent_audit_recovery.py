#!/usr/bin/env python3
"""Blocco regressione: il recupero holdout pubblica SOLO su fonte primaria verificata."""
from __future__ import annotations

from datetime import date

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
    assert all(x["source_verification"]["type"] == "official_primary_webpage" for x in result["opportunities"])
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
    print("Recupero indipendente Radar: 5 contratti PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
