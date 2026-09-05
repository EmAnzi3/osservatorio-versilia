#!/usr/bin/env python3
"""Refresh giornaliero h4: discovery resiliente e gate runtime obbligatori.

Estende l'hardening h3 senza modificare classificatore o criteri di pubblicazione:
- applica il trasporto resiliente a listing primari e canali discovery;
- consente un reader proxy solo come ultimo fallback di discovery, marcandolo
  sempre come copertura degradata e mai come verifica/promozione;
- registra la diagnostica endpoint nel risultato e nello snapshot;
- rimuove dal runtime il vecchio feed PA Digitale stale;
- corregge difensivamente l'endpoint SCU;
- blocca la pubblicazione quando una famiglia obbligatoria è realmente priva di
  qualsiasi endpoint eseguito con successo nel run.
"""
from __future__ import annotations

from typing import Any

import opportunity_daily_refresh_revalidated as revalidated
import opportunity_discovery_resilient as discovery


daily = revalidated.daily
radar_module = daily.radar.radar
core = daily.radar.core

_ORIGINAL_PROBE = radar_module.probe_discovery_sources
_ORIGINAL_V022_FETCH = radar_module.v025.v022.fetch_resilient
_ORIGINAL_V02_FETCH = radar_module.v025.v022.v02.fetch_resilient
_ORIGINAL_ASSERT = daily._assert_publishable
_ORIGINAL_PREPARE = daily._prepare_public
_ORIGINAL_COMPOSE = core.compose_runtime_payloads

_SCU_CURRENT_URL = (
    "https://www.politichegiovanili.gov.it/servizio-civile/"
    "bandi-e-avvisi-di-servizio-civile/avvisi-di-presentazione-programmi-e-progetti/"
)


def _compose_runtime_hardened() -> tuple[dict[str, Any], dict[str, Any]]:
    config, coverage = _ORIGINAL_COMPOSE()

    config["sources"] = [
        source for source in config.get("sources") or []
        if str(source.get("id") or "") != "pa-digitale-2026"
    ]

    for source in config.get("discoverySources") or []:
        if str(source.get("id") or "") == "pcm-politiche-giovanili-scu":
            source["urls"] = [_SCU_CURRENT_URL]
    return config, coverage


def _runtime_uncovered_families(result: dict[str, Any]) -> list[str]:
    """Famiglie obbligatorie senza neppure un endpoint ok/degraded nel run."""
    contract = core._load(core.CONTRACT_V04)
    rows = list((result.get("sourceCoverage") or {}).get("rows") or [])
    by_id = {str(row.get("source_id") or ""): row for row in rows}
    uncovered: list[str] = []

    for family in contract.get("requiredFamilies") or []:
        source_ids = [str(value) for value in family.get("sourceIds") or []]
        states = [str((by_id.get(source_id) or {}).get("runtimeStatus") or "not_run") for source_id in source_ids]
        if not any(state in {"ok", "degraded"} for state in states):
            uncovered.append(str(family.get("id") or ""))
    return sorted(filter(None, uncovered))


def _assert_publishable_hardened(result: dict[str, Any]) -> None:
    _ORIGINAL_ASSERT(result)
    uncovered = _runtime_uncovered_families(result)
    audit = result.setdefault("coverageAudit", {})
    audit["runtimeUncoveredFamilies"] = uncovered
    if uncovered:
        audit["status"] = "fail"
        raise RuntimeError(
            "Snapshot giornaliero non pubblicabile: famiglie obbligatorie senza copertura runtime="
            + ", ".join(uncovered)
        )


def _configured_endpoint_map() -> dict[str, list[str]]:
    config, _ = _compose_runtime_hardened()
    mapped: dict[str, list[str]] = {}
    for source in config.get("sources") or []:
        source_id = str(source.get("id") or "")
        urls = [str(source.get("url") or "").strip()]
        urls.extend(str(url).strip() for url in source.get("urls") or [])
        mapped[source_id] = [url for url in urls if url]
    for source in config.get("discoverySources") or []:
        source_id = str(source.get("id") or "")
        urls = [str(url).strip() for url in source.get("urls") or [] if str(url).strip()]
        mapped[source_id] = urls
    return mapped


def _build_transport_audit(result: dict[str, Any]) -> dict[str, Any]:
    runtime_by_id: dict[str, str] = {}
    for row in result.get("sources") or []:
        runtime_by_id[str(row.get("sourceId") or "")] = str(row.get("status") or "unknown")
    for row in result.get("discoverySources") or []:
        runtime_by_id[str(row.get("sourceId") or "")] = str(row.get("status") or "unknown")

    rows: list[dict[str, Any]] = []
    fallback_successes = 0
    proxy_successes = 0
    endpoint_failures = 0
    redirected = 0

    for source_id, urls in _configured_endpoint_map().items():
        endpoints: list[dict[str, Any]] = []
        for url in urls:
            trace = discovery.FETCH_TRACE.get(url)
            if trace is None:
                endpoint = {
                    "url": url,
                    "status": "not_run",
                    "transport": None,
                    "fallbackUsed": False,
                    "proxyUsed": False,
                    "initialFailureClass": None,
                    "browserFailureClass": None,
                    "failureClass": None,
                    "resolvedUrl": None,
                    "redirected": False,
                    "errors": [],
                }
            else:
                endpoint = dict(trace)
                if endpoint.get("status") == "ok" and endpoint.get("transport") in {"chromium", "reader_proxy"}:
                    fallback_successes += 1
                if endpoint.get("status") == "ok" and endpoint.get("transport") == "reader_proxy":
                    proxy_successes += 1
                if endpoint.get("status") == "error":
                    endpoint_failures += 1
                if endpoint.get("redirected"):
                    redirected += 1
            endpoints.append(endpoint)

        rows.append({
            "sourceId": source_id,
            "runtimeStatus": runtime_by_id.get(source_id, "not_run"),
            "endpointCount": len(endpoints),
            "endpointOk": sum(endpoint.get("status") == "ok" for endpoint in endpoints),
            "fallbackSuccessCount": sum(
                endpoint.get("status") == "ok" and endpoint.get("transport") in {"chromium", "reader_proxy"}
                for endpoint in endpoints
            ),
            "proxySuccessCount": sum(
                endpoint.get("status") == "ok" and endpoint.get("transport") == "reader_proxy"
                for endpoint in endpoints
            ),
            "failureClasses": sorted({
                str(endpoint.get("failureClass"))
                for endpoint in endpoints
                if endpoint.get("failureClass")
            }),
            "endpoints": endpoints,
        })

    assigned_urls = {
        endpoint["url"]
        for row in rows
        for endpoint in row.get("endpoints") or []
    }
    extra_fetches = [
        dict(trace)
        for url, trace in discovery.FETCH_TRACE.items()
        if url not in assigned_urls
    ]
    return {
        "schemaVersion": "1.1",
        "summary": {
            "configuredSources": len(rows),
            "configuredEndpoints": sum(row.get("endpointCount", 0) for row in rows),
            "fallbackSuccesses": fallback_successes,
            "proxySuccesses": proxy_successes,
            "endpointFailures": endpoint_failures,
            "redirectedEndpoints": redirected,
            "extraFetches": len(extra_fetches),
        },
        "sources": rows,
        "extraFetches": extra_fetches,
    }


def _prepare_public_hardened(result: dict[str, Any], today):
    result = _ORIGINAL_PREPARE(result, today)
    result["dailyHardeningVersion"] = "0.4.4-h4"
    result["transportAudit"] = _build_transport_audit(result)
    summary = result["transportAudit"]["summary"]
    result.setdefault("counts", {})["transportFallbacks"] = int(summary.get("fallbackSuccesses") or 0)
    result.setdefault("counts", {})["transportProxyFallbacks"] = int(summary.get("proxySuccesses") or 0)
    result.setdefault("counts", {})["transportFailures"] = int(summary.get("endpointFailures") or 0)
    return result


def _probe_hardened(config: dict[str, Any], *, payloads: dict[str, str] | None = None):
    return discovery.probe_discovery_sources(radar_module, config, payloads=payloads)


def main() -> int:
    discovery.reset_trace()
    radar_module.probe_discovery_sources = _probe_hardened
    radar_module.v025.v022.fetch_resilient = discovery.fetch_resilient
    radar_module.v025.v022.v02.fetch_resilient = discovery.fetch_resilient
    daily._assert_publishable = _assert_publishable_hardened
    daily._prepare_public = _prepare_public_hardened
    core.compose_runtime_payloads = _compose_runtime_hardened
    try:
        return revalidated.main()
    finally:
        radar_module.probe_discovery_sources = _ORIGINAL_PROBE
        radar_module.v025.v022.fetch_resilient = _ORIGINAL_V022_FETCH
        radar_module.v025.v022.v02.fetch_resilient = _ORIGINAL_V02_FETCH
        daily._assert_publishable = _ORIGINAL_ASSERT
        daily._prepare_public = _ORIGINAL_PREPARE
        core.compose_runtime_payloads = _ORIGINAL_COMPOSE


if __name__ == "__main__":
    raise SystemExit(main())
