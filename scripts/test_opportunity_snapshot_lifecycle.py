#!/usr/bin/env python3
"""Contratto lifecycle-aware per snapshot pubblici e dry-run del Radar."""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

MATRIX_TARGET = 89
REPLAY_SOURCES = {"audit-corpus-v1", "municipal-matrix-v1"}
REQUIRED_COVERAGE_IDS = {
    "pcm-sport-eventi-2026",
    "life-2026-cet-heatcoolplan",
    "life-2026-cet-pda",
    "life-2026-cet-enercom",
    "life-2026-cet-empower",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"Snapshot non-object: {path}")
    return payload


def _assert_no_expired_active(opportunities: list[dict[str, Any]], reference: date) -> None:
    expired: list[tuple[Any, str]] = []
    for item in opportunities:
        if str(item.get("lifecycle_stage") or "application_open") != "application_open":
            continue
        deadline_text = str(item.get("deadline_at") or "")
        if not deadline_text:
            continue
        try:
            deadline = date.fromisoformat(deadline_text)
        except ValueError:
            continue
        if deadline < reference:
            expired.append((item.get("title"), deadline_text))
    assert not expired, expired


def _assert_replay_contract(payload: dict[str, Any], opportunities: list[dict[str, Any]], archive: list[dict[str, Any]]) -> tuple[int, int]:
    replay = payload.get("auditCorpusPromotion") or {}
    replay_current = int(replay.get("currentOrRollingAdded") or 0)
    replay_municipal = int(replay.get("municipalCurrentOrRollingAdded") or 0)
    replay_partnership = int(replay.get("partnershipCurrentOrRollingAdded") or 0)
    replay_municipal_upcoming = int(replay.get("municipalUpcomingAdded") or 0)
    replay_partnership_upcoming = int(replay.get("partnershipUpcomingAdded") or 0)
    replay_added = int(replay.get("added") or 0)
    matrix_target = int(replay.get("matrixCurrentTarget") or 0)

    assert matrix_target == MATRIX_TARGET, replay
    assert replay_current == replay_municipal + replay_partnership, replay
    assert replay_added == replay_current + replay_municipal_upcoming + replay_partnership_upcoming, replay

    retained_ids = {
        str(item.get("coverage_id"))
        for item in opportunities + archive
        if str(item.get("source_id") or "") in REPLAY_SOURCES and item.get("coverage_id")
    }
    # 89 è il pavimento storico delle identità verificate il 7/9. Una scadenza
    # deve spostare una scheda nell'archivio, non diminuire la copertura storica.
    assert len(retained_ids) >= matrix_target, (len(retained_ids), matrix_target)
    return replay_current, len(retained_ids)


def _assert_municipal_contract(payload: dict[str, Any], opportunities: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    municipal = payload.get("municipalRelevance") or {}
    headline_current = int(municipal.get("headlineCurrentOrRolling") or 0)
    headline_upcoming = int(municipal.get("headlineUpcoming") or 0)
    headline_total = int(municipal.get("headlineTotal") or 0)
    partnership_current = int(municipal.get("partnershipCurrentOrRolling") or 0)
    partnership_upcoming = int(municipal.get("partnershipUpcoming") or 0)
    partnership_total = int(municipal.get("partnershipTotal") or 0)
    review_excluded = int(municipal.get("reviewExcluded") or 0)
    assert headline_total == headline_current + headline_upcoming, municipal
    assert partnership_total == partnership_current + partnership_upcoming, municipal
    assert len(opportunities) == headline_total + partnership_total + review_excluded, municipal
    assert headline_current > 0 and partnership_current > 0, municipal
    return headline_current, headline_upcoming, partnership_current, partnership_upcoming


def verify_release(path: Path) -> None:
    payload = _load(path)
    assert payload.get("releaseVersion") == "0.4.4"
    reference = date.fromisoformat(str(payload.get("referenceDate") or ""))
    assert reference >= date(2026, 9, 8), reference
    opportunities = list(payload.get("opportunities") or [])
    archive = list(payload.get("archive") or [])
    assert opportunities
    counts = payload.get("counts") or {}
    assert counts.get("new") == sum(bool(x.get("is_new")) for x in opportunities)
    _assert_no_expired_active(opportunities, reference)
    replay_current, retained = _assert_replay_contract(payload, opportunities, archive)
    headline_current, headline_upcoming, partnership_current, partnership_upcoming = _assert_municipal_contract(payload, opportunities)
    assert not payload.get("continuityHold")
    assert not payload.get("coverageHold")
    backtest = payload.get("backtest") or {}
    if backtest:
        assert backtest.get("passed") is True, backtest
    audit = payload.get("coverageAudit") or {}
    if audit:
        assert audit.get("status") == "pass", audit
    regional = payload.get("regionalCompleteness") or {}
    if regional:
        assert regional.get("status") in {"pass", "degraded"}, regional
    print(
        f"Snapshot pubblico verificato: {len(opportunities)} schede · "
        f"headline current/rolling {headline_current} · headline upcoming {headline_upcoming} · "
        f"partnership current/rolling {partnership_current} · partnership upcoming {partnership_upcoming} · "
        f"replay attivo {replay_current} · identità trattenute {retained}/{MATRIX_TARGET} · "
        f"riferimento {payload.get('referenceDate')}"
    )


def verify_daily(path: Path) -> None:
    payload = _load(path)
    expected = datetime.now(timezone.utc).date()
    assert payload.get("referenceDate") == expected.isoformat(), (payload.get("referenceDate"), expected.isoformat())
    assert payload.get("releaseVersion") == "0.4.4"
    assert payload.get("dailyHardeningVersion") == "0.4.4-h5"
    assert payload.get("sourceHealthGraceDays") == 2
    assert not payload.get("continuityHold")
    assert not payload.get("coverageHold")
    assert (payload.get("backtest") or {}).get("passed") is True
    assert (payload.get("coverageAudit") or {}).get("status") == "pass"
    assert not ((payload.get("coverageAudit") or {}).get("runtimeUncoveredFamilies") or [])
    assert (payload.get("regionalCompleteness") or {}).get("status") in {"pass", "degraded"}
    assert (payload.get("continuityReconciliation") or {}).get("remaining") == 0

    opportunities = list(payload.get("opportunities") or [])
    archive = list(payload.get("archive") or [])
    assert opportunities
    _assert_no_expired_active(opportunities, expected)

    transport = payload.get("transportAudit") or {}
    assert transport.get("schemaVersion") == "1.2", transport
    summary = transport.get("summary") or {}
    assert int(summary.get("configuredSources") or 0) > 0
    assert int(summary.get("configuredEndpoints") or 0) > 0
    assert int(summary.get("sourceHealthGraceDays") or 0) == 2

    replay_current, retained = _assert_replay_contract(payload, opportunities, archive)
    headline_current, _, partnership_current, _ = _assert_municipal_contract(payload, opportunities)

    ids = {item.get("coverage_id") for item in opportunities + archive}
    assert REQUIRED_COVERAGE_IDS <= ids, sorted(REQUIRED_COVERAGE_IDS - ids)
    print(
        "Dry-run daily validato:", len(opportunities), "schede ·",
        headline_current, "comunali current/rolling ·",
        partnership_current, "partnership current/rolling ·",
        "replay attivo", replay_current, "· identità trattenute", retained, "/", MATRIX_TARGET, "·",
        "fallback", summary.get("fallbackSuccesses", 0), "· grace", summary.get("sourcesInGrace", 0),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--mode", choices=("release", "daily"), required=True)
    args = parser.parse_args()
    if args.mode == "release":
        verify_release(args.file)
    else:
        verify_daily(args.file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
