#!/usr/bin/env python3
"""Probe live non distruttivo delle fonti che hanno mostrato falsi offline.

Il probe serve alla PR/diagnostica: non pubblica opportunità e non modifica dati.
Un recupero tramite reader proxy è esplicitamente ``degraded``: dimostra che il
canale discovery resta leggibile, ma non equivale a una connessione diretta alla
fonte ufficiale e non può essere usato come verifica per la pubblicazione.

Nella quality gate il probe è bloccante se anche una sola fonte critica resta
``error`` o ``not_configured``. Una fonte ``degraded`` è accettata soltanto perché
il reader mantiene il discovery e la successiva promozione richiede comunque una
verifica diretta della fonte primaria.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import opportunity_daily_refresh_resilient as h4
import opportunity_discovery_resilient as transport


TARGET_SOURCE_IDS = (
    "anci-nazionale",
    "gse",
    "pcm-stato-citta",
    "pcm-politiche-mare",
    "pcm-pari-opportunita",
    "pcm-politiche-giovanili-scu",
    "mim-enti-locali",
    "funzione-pubblica",
)

REPORT_PATH = Path("reports/runtime/opportunity-transport-smoke.json")


def _source_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for bucket in ("sources", "discoverySources"):
        for source in config.get(bucket) or []:
            mapped[str(source.get("id") or "")] = source
    return mapped


def _urls(source: dict[str, Any]) -> list[str]:
    values: list[str] = []
    primary = str(source.get("url") or "").strip()
    if primary:
        values.append(primary)
    values.extend(str(url).strip() for url in source.get("urls") or [] if str(url).strip())
    return list(dict.fromkeys(values))


def _probe_source(source_id: str, source: dict[str, Any] | None) -> dict[str, Any]:
    if source is None:
        return {
            "sourceId": source_id,
            "status": "not_configured",
            "endpointCount": 0,
            "endpointOk": 0,
            "fallbackSuccessCount": 0,
            "proxySuccessCount": 0,
            "failureClasses": ["not_configured"],
            "endpoints": [],
        }

    endpoints: list[dict[str, Any]] = []
    for url in _urls(source):
        try:
            _, diagnostics = transport.fetch_with_diagnostics(
                url,
                timeout=min(20, int(source.get("fetchTimeoutSeconds") or 18)),
                attempts=2,
            )
            endpoints.append({"url": url, **diagnostics})
        except Exception as exc:  # rete live: il report deve sopravvivere al failure
            diagnostics = dict(getattr(exc, "diagnostics", {}) or {})
            endpoints.append({
                "url": url,
                "status": "error",
                "transport": diagnostics.get("transport") or "failed",
                "fallbackUsed": bool(diagnostics.get("fallbackUsed")),
                "proxyUsed": bool(diagnostics.get("proxyUsed")),
                "initialFailureClass": diagnostics.get("initialFailureClass"),
                "browserFailureClass": diagnostics.get("browserFailureClass"),
                "failureClass": diagnostics.get("failureClass") or transport.classify_fetch_error(exc),
                "resolvedUrl": diagnostics.get("resolvedUrl"),
                "redirected": bool(diagnostics.get("redirected")),
                "errors": diagnostics.get("errors") or [str(exc)],
            })

    ok = sum(row.get("status") == "ok" for row in endpoints)
    proxy = sum(
        row.get("status") == "ok" and row.get("transport") == "reader_proxy"
        for row in endpoints
    )
    if endpoints and ok == len(endpoints) and not proxy:
        status = "ok"
    elif ok:
        status = "degraded"
    else:
        status = "error"

    return {
        "sourceId": source_id,
        "status": status,
        "endpointCount": len(endpoints),
        "endpointOk": ok,
        "fallbackSuccessCount": sum(
            row.get("status") == "ok" and row.get("transport") in {"chromium", "reader_proxy"}
            for row in endpoints
        ),
        "proxySuccessCount": proxy,
        "failureClasses": sorted({
            str(row.get("failureClass"))
            for row in endpoints
            if row.get("failureClass")
        }),
        "endpoints": endpoints,
    }


def main() -> int:
    config, _ = h4._compose_runtime_hardened()
    sources = _source_map(config)
    transport.reset_trace()
    rows = [_probe_source(source_id, sources.get(source_id)) for source_id in TARGET_SOURCE_IDS]

    report = {
        "schemaVersion": "1.1",
        "targetSourceIds": list(TARGET_SOURCE_IDS),
        "summary": {
            "targets": len(rows),
            "healthy": sum(row["status"] == "ok" for row in rows),
            "degraded": sum(row["status"] == "degraded" for row in rows),
            "error": sum(row["status"] == "error" for row in rows),
            "notConfigured": sum(row["status"] == "not_configured" for row in rows),
            "fallbackSuccesses": sum(int(row["fallbackSuccessCount"]) for row in rows),
            "proxySuccesses": sum(int(row["proxySuccessCount"]) for row in rows),
        },
        "sources": rows,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for row in rows:
        classes = ",".join(row["failureClasses"]) or "-"
        print(
            f"{row['sourceId']}: {row['status']} · "
            f"endpoint {row['endpointOk']}/{row['endpointCount']} · "
            f"fallback {row['fallbackSuccessCount']} · proxy {row['proxySuccessCount']} · "
            f"cause {classes}"
        )
    print("SUMMARY", json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 1 if report["summary"]["error"] or report["summary"]["notConfigured"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
