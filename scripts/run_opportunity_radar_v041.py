#!/usr/bin/env python3
"""Estensione v0.4.1 del Radar Opportunità coverage-first.

Mantiene intatto il motore v0.4 già collaudato e aggiunge i registri di copertura
trasversali emersi dal secondo audit: famiglia, pari opportunità, Casa Italia,
rete MiC generale e Funding & Tenders UE. Le nuove sentinelle passano dagli
stessi vincoli di verifica primaria, matrice comunale e lifecycle della v0.4.

Il discovery live viene eseguito in parallelo per endpoint: l'ampliamento della
copertura non deve trasformare i timeout dei portali pubblici in una somma
sequenziale di minuti. L'ordine dell'output resta deterministico.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

import run_opportunity_radar_v04 as base

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_EXTRA = ROOT / "data" / "opportunity-discovery-v04-extra.json"
VERIFIED_EXTRA = ROOT / "data" / "opportunity-verified-v04-extra.json"
SENTINELS_EXTRA = ROOT / "data" / "opportunity-coverage-sentinels-v04-extra.json"

_ORIGINAL_COMPOSE = base.compose_runtime_payloads
_ORIGINAL_SOURCE_VISUAL = base._source_visual
_ORIGINAL_INJECT = base.inject_verified_v04
_ORIGINAL_AUDIT = base.build_coverage_audit


def compose_runtime_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _ORIGINAL_COMPOSE()
    extra = base._load(DISCOVERY_EXTRA)
    existing = {str(x.get("id")) for x in config.get("discoverySources") or []}
    for source in extra.get("discoverySources") or []:
        source_id = str(source.get("id") or "")
        if source_id and source_id not in existing:
            config.setdefault("discoverySources", []).append(source)
            existing.add(source_id)
    registry = coverage.setdefault("sources", {})
    for source_id, meta in (extra.get("coverageRegistry") or {}).items():
        registry[str(source_id)] = meta
    coverage["schemaVersion"] = "0.4.1"
    config["schemaVersion"] = 4
    return config, coverage


def _source_visual(source_id: str) -> dict[str, Any]:
    current = _ORIGINAL_SOURCE_VISUAL(source_id)
    meta = (base._load(DISCOVERY_EXTRA).get("coverageRegistry") or {}).get(source_id) or {}
    if meta:
        return {
            "source_label": meta.get("label") or current.get("source_label") or source_id,
            "source_favicon": meta.get("favicon") or current.get("source_favicon") or "",
        }
    return current


def probe_discovery_sources(
    config: dict[str, Any],
    *,
    payloads: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Versione concorrente e deterministica del probe discovery v0.3."""
    payloads = payloads or {}
    sources = list(config.get("discoverySources") or [])
    results: dict[tuple[int, int], tuple[str | None, str | None]] = {}
    jobs: list[tuple[int, int, dict[str, Any], str]] = []

    for source_index, source in enumerate(sources):
        for url_index, url in enumerate(list(source.get("urls") or [])):
            jobs.append((source_index, url_index, source, str(url)))

    def fetch_one(source: dict[str, Any], url: str) -> tuple[str | None, str | None]:
        if url in payloads:
            return payloads[url], None
        try:
            payload = base.radar.v025.v022.fetch_resilient(
                url,
                timeout=int(source.get("fetchTimeoutSeconds") or 25),
                attempts=1,
            )
            return payload, None
        except Exception as exc:  # pragma: no cover - dipende dalla rete live
            return None, str(exc)

    if jobs:
        workers = min(12, max(1, len(jobs)))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="radar-discovery") as pool:
            pending = {
                pool.submit(fetch_one, source, url): (source_index, url_index)
                for source_index, url_index, source, url in jobs
            }
            for future in as_completed(pending):
                results[pending[future]] = future.result()

    queue: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    for source_index, source in enumerate(sources):
        urls = [str(x) for x in source.get("urls") or []]
        endpoint_ok = 0
        endpoint_errors: list[str] = []
        source_candidates: list[dict[str, Any]] = []
        for url_index, url in enumerate(urls):
            payload, error = results.get((source_index, url_index), (None, "endpoint non eseguito"))
            if payload is not None:
                endpoint_ok += 1
                source_candidates.extend(base.radar.discovery_candidates(source, payload, url))
            else:
                endpoint_errors.append(f"{url}: {error}")

        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for item in source_candidates:
            key = (
                base.radar.v025.fold(item.get("title")),
                base.radar.v025.normalized_url(item.get("url")),
            )
            unique[key] = item
        source_candidates = list(unique.values())[:50]
        queue.extend(source_candidates)

        if endpoint_ok == len(urls) and urls:
            runtime = "ok"
        elif endpoint_ok:
            runtime = "degraded"
        else:
            runtime = "error"
        states.append({
            "sourceId": source["id"],
            "status": runtime,
            "endpointCount": len(urls),
            "endpointOk": endpoint_ok,
            "candidateCount": len(source_candidates),
            "errors": endpoint_errors,
            "freshness": {"status": "discovery", "observedDate": None, "ageDays": None},
        })

    queue.sort(key=lambda item: (str(item.get("source_label") or ""), str(item.get("title") or "")))
    return queue, states


def inject_verified_v04(
    result: dict[str, Any],
    today: date,
    *,
    detail_payloads: dict[str, str] | None = None,
    live: bool = True,
) -> set[str]:
    resolved = set(_ORIGINAL_INJECT(
        result, today, detail_payloads=detail_payloads, live=live
    ))
    original_path = base.VERIFIED_V04
    base.VERIFIED_V04 = VERIFIED_EXTRA
    try:
        resolved.update(_ORIGINAL_INJECT(
            result, today, detail_payloads=detail_payloads, live=live
        ))
    finally:
        base.VERIFIED_V04 = original_path
    return resolved


def build_coverage_audit(result: dict[str, Any], resolved: set[str], today: date) -> dict[str, Any]:
    audit = _ORIGINAL_AUDIT(result, resolved, today)
    extra_sentinels = base._load(SENTINELS_EXTRA).get("cases") or []
    extra_verified = base._load(VERIFIED_EXTRA).get("entries") or []
    verified_by_id = {str(x.get("coverage_id")): x for x in extra_verified}
    configured = {
        str(row.get("source_id") or "")
        for row in (result.get("sourceCoverage") or {}).get("rows") or []
    }

    missing_current = list(audit.get("missingCurrentSentinels") or [])
    historical_unmonitored = list(audit.get("historicalUnmonitored") or [])
    current_resolved = int(audit.get("currentSentinelsResolved") or 0)

    for case in extra_sentinels:
        expected = str(case.get("expected") or "")
        if expected == "current":
            entry = verified_by_id.get(str(case.get("coverage_id") or "")) or {}
            if base._is_expired_application(entry, today):
                continue
            coverage_id = str(case.get("coverage_id") or "")
            if coverage_id in resolved:
                current_resolved += 1
            else:
                missing_current.append(str(case.get("id") or coverage_id))
        elif expected == "historical_monitored":
            source_id = str(case.get("source_id") or "")
            if source_id not in configured:
                historical_unmonitored.append(str(case.get("id") or source_id))

    contract = base._load(base.CONTRACT_V04)
    supplier_exclusion = "supplier_tender" in set(contract.get("excludedOpportunityKinds") or [])
    audit["currentSentinelsResolved"] = current_resolved
    audit["missingCurrentSentinels"] = sorted(set(missing_current))
    audit["historicalUnmonitored"] = sorted(set(historical_unmonitored))
    audit["supplierTenderExclusionContract"] = supplier_exclusion
    if audit["missingCurrentSentinels"] or audit["historicalUnmonitored"] or not supplier_exclusion:
        audit["status"] = "fail"
    return audit


# Il main v0.4 risolve questi simboli globalmente al momento dell'esecuzione.
base.compose_runtime_payloads = compose_runtime_payloads
base._source_visual = _source_visual
base.inject_verified_v04 = inject_verified_v04
base.build_coverage_audit = build_coverage_audit
base.radar.probe_discovery_sources = probe_discovery_sources

# API ri-esposta per test e tooling.
_load = base._load
build_seed_item = base.build_seed_item
verify_entry = base.verify_entry
run_v04 = base.run_v04
CONTRACT_V04 = base.CONTRACT_V04
VERIFIED_V04 = base.VERIFIED_V04
SENTINELS_V04 = base.SENTINELS_V04
DEFAULT_BACKTEST = base.radar.DEFAULT_BACKTEST
radar = base.radar


if __name__ == "__main__":
    raise SystemExit(base.main())
