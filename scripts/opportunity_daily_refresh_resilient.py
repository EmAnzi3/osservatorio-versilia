#!/usr/bin/env python3
"""Refresh giornaliero h3: discovery resiliente e gate runtime obbligatori.

Estende l'hardening h2 senza modificare classificatore o criteri di pubblicazione:
- applica il trasporto resiliente anche a listing primari e canali discovery;
- registra la diagnostica endpoint nel risultato del discovery;
- rimuove dal runtime il vecchio feed PA Digitale stale, mantenuto nel catalogo
  come fonte degradata sostituita dalla pagina corrente;
- corregge difensivamente l'endpoint SCU anche se il catalogo non fosse aggiornato;
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

    # Il vecchio dataset GitHub di PA Digitale resta documentato nel registry
    # come degraded/replacementNeeded, ma non viene più interrogato come fonte
    # primaria corrente: il presidio attivo è pa-digitale-current.
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
        # degraded significa almeno un endpoint raggiunto: la famiglia non è
        # completa, ma non è totalmente cieca. Error/not_run su tutti è invece
        # una perdita reale di copertura e deve fermare il publish giornaliero.
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


def _prepare_public_hardened(result: dict[str, Any], today):
    result = _ORIGINAL_PREPARE(result, today)
    result["dailyHardeningVersion"] = "0.4.4-h3"
    return result


def _probe_hardened(config: dict[str, Any], *, payloads: dict[str, str] | None = None):
    return discovery.probe_discovery_sources(radar_module, config, payloads=payloads)


def main() -> int:
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
