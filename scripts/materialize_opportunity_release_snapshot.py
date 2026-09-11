#!/usr/bin/env python3
"""Ricostruisce lo snapshot pubblico verificato del Radar Opportunità v0.4.4.

La release base v0.4.3 resta immutabile e riproducibile. Sopra di essa vengono
applicate le opportunità Sport/LIFE v0.4.4, l'eventuale snapshot giornaliero e,
infine, il replay completo della matrice municipale finale. In questo modo la
build pubblica non resta ferma al vecchio conteggio mentre il refresh giornaliero
recepisce tutte le opportunità verificate dall'audit.
"""
from __future__ import annotations

import base64
import json
import zlib
from datetime import date, datetime, timezone
from pathlib import Path

import opportunity_matrix_promotions as audit_promotions
import opportunity_municipal_relevance as relevance
import run_opportunity_radar_v044 as radar_v044

ROOT = Path(__file__).resolve().parents[1]
PARTS = (
    ROOT / "data" / "opportunity-release-v043.part1.b85",
    ROOT / "data" / "opportunity-release-v043.part2.b85",
)
VERIFIED_V044 = ROOT / "data" / "opportunity-verified-v044.json"
DAILY = ROOT / "data" / "opportunity-daily-public.json"
TARGET = ROOT / "data" / "opportunity-release.json"


def _decode_base() -> dict:
    encoded = b"".join(path.read_bytes().strip() for path in PARTS)
    payload = zlib.decompress(base64.b85decode(encoded))
    data = json.loads(payload.decode("utf-8"))
    assert data.get("referenceDate") == "2026-08-24", data.get("referenceDate")
    assert data.get("releaseVersion") == "0.4.3", data.get("releaseVersion")
    assert len(data.get("opportunities") or []) == 25, len(data.get("opportunities") or [])
    assert len(((data.get("sourceCoverage") or {}).get("rows") or [])) == 47
    return data


def _merge_v044(base: dict) -> dict:
    data = json.loads(json.dumps(base))
    reference = date.fromisoformat(str(data["referenceDate"]))
    existing_ids = {
        str(item.get("coverage_id") or "")
        for item in data.get("opportunities") or []
        if item.get("coverage_id")
    }
    existing_urls = {
        radar_v044.radar.v025.normalized_url(str(item.get("url") or ""))
        for item in data.get("opportunities") or []
    }

    for item in data.get("opportunities") or []:
        item.setdefault("is_new", False)

    verified = radar_v044._load(VERIFIED_V044)
    for entry in verified.get("entries") or []:
        coverage_id = str(entry.get("coverage_id") or "")
        norm_url = radar_v044.radar.v025.normalized_url(str(entry.get("url") or ""))
        if coverage_id in existing_ids or (norm_url and norm_url in existing_urls):
            continue
        item = radar_v044.build_seed_item(entry, reference, "release_verified")
        first_seen = str(entry.get("first_seen_at") or data["referenceDate"])
        item["first_seen_at"] = first_seen
        try:
            age = (reference - date.fromisoformat(first_seen)).days
        except ValueError:
            age = 999
        item["is_new"] = 0 <= age < radar_v044.NEW_WINDOW_DAYS
        data.setdefault("opportunities", []).append(item)
        existing_ids.add(coverage_id)
        if norm_url:
            existing_urls.add(norm_url)

    order = {"application_open": 0, "rolling_open": 1, "announced_upcoming": 2}
    data["opportunities"].sort(
        key=lambda x: (
            order.get(str(x.get("lifecycle_stage") or "application_open"), 9),
            str(x.get("deadline_at") or "9999-99-99"),
            str(x.get("title") or ""),
        )
    )
    radar_v044.core._recompute_v04_counts(data)
    data["newOpportunityWindowDays"] = radar_v044.NEW_WINDOW_DAYS
    data.setdefault("counts", {})["new"] = sum(bool(x.get("is_new")) for x in data["opportunities"])
    data["releaseVersion"] = "0.4.4"
    data["engineVersion"] = "0.4.4"
    data["coverageVersion"] = "0.4.4"
    data["uiVersion"] = "0.4.4"
    return data


def _daily_is_publishable(candidate: dict, baseline: dict) -> bool:
    try:
        candidate_date = date.fromisoformat(str(candidate.get("referenceDate") or ""))
        baseline_date = date.fromisoformat(str(baseline.get("referenceDate") or ""))
    except ValueError:
        return False
    if candidate_date < baseline_date:
        return False
    if candidate.get("releaseVersion") != "0.4.4":
        return False
    if candidate.get("continuityHold") or candidate.get("coverageHold"):
        return False
    backtest = candidate.get("backtest") or {}
    if backtest and not backtest.get("passed", False):
        return False
    audit = candidate.get("coverageAudit") or {}
    if audit and audit.get("status") != "pass":
        return False
    regional = candidate.get("regionalCompleteness") or {}
    if regional and regional.get("status") not in {"pass", "degraded"}:
        return False
    opportunities = candidate.get("opportunities")
    if not isinstance(opportunities, list) or not opportunities:
        return False
    return True


def _archive_expired_opportunities(data: dict, today: date) -> None:
    """Applica la transizione temporale anche a snapshot già accettati."""
    active = []
    for item in data.get("opportunities") or []:
        if radar_v044.core._is_expired_application(item, today):
            radar_v044.core._append_archive(data, item)
        else:
            active.append(item)
    data["opportunities"] = active


def _apply_public_audit_replay(data: dict) -> dict:
    today = date.today()
    audit_promotions.apply_complete_promotions(data, today)
    _archive_expired_opportunities(data, today)
    radar_v044.core._recompute_v04_counts(data)
    relevance.apply_to_payload(data, drop_review=True)
    # Il replay viene applicato dopo il normale calcolo dei contatori v0.4.4.
    # Riallineiamo esplicitamente il numero di badge "Nuova" alle schede reali.
    data.setdefault("counts", {})["new"] = sum(
        bool(item.get("is_new")) for item in data.get("opportunities") or []
    )
    replay = data.get("auditCorpusPromotion") or {}
    if int(replay.get("added") or 0) > 0:
        # La build è stata aggiornata dal replay audit in data odierna: la data
        # pubblica deve dirlo, anche se il file daily persistente è del giorno prima.
        data["referenceDate"] = today.isoformat()
        data["generatedAt"] = datetime.now(timezone.utc).isoformat()
    data["auditCorpusPromotionVersion"] = audit_promotions.PROMOTION_VERSION
    return data


def main() -> None:
    baseline = _merge_v044(_decode_base())
    data = baseline
    source = "baseline v0.4.4"
    if DAILY.exists():
        try:
            candidate = json.loads(DAILY.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            candidate = {}
        if isinstance(candidate, dict) and _daily_is_publishable(candidate, baseline):
            data = candidate
            source = "snapshot giornaliero verificato"

    data = _apply_public_audit_replay(data)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = len(data.get("opportunities") or [])
    monitored = len(((data.get("sourceCoverage") or {}).get("rows") or []))
    new_count = int((data.get("counts") or {}).get("new") or 0)
    municipal = data.get("municipalRelevance") or {}
    replay = data.get("auditCorpusPromotion") or {}
    print(
        f"Snapshot Radar pubblico: {total} schede · "
        f"{municipal.get('headlineCurrentOrRolling', 0)} comunali current/rolling + "
        f"{municipal.get('headlineUpcoming', 0)} comunali upcoming · "
        f"{municipal.get('partnershipCurrentOrRolling', 0)} partnership current/rolling + "
        f"{municipal.get('partnershipUpcoming', 0)} partnership upcoming · "
        f"{new_count} nuove · {monitored} fonti · riferimento {data.get('referenceDate')} · "
        f"replay audit +{replay.get('added', 0)} · v0.4.4 · {source}"
    )


if __name__ == "__main__":
    main()
