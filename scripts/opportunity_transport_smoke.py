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
import argparse
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
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


def diagnose_routes(config: dict[str, Any]) -> int:
    """Read-only default/IPv4 comparison; never changes source health or snapshots."""
    sources = _source_map(config)
    requests = [(source_id, url, route)
                for source_id in ("anci-toscana", "anci-nazionale", "mim-enti-locali")
                for url in _urls(sources[source_id])
                if source_id != "anci-toscana" or url.endswith("/categorie/bandi/")
                for route in ("default", "ipv4")]

    def probe(request):
        source_id, url, route = request
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "body"
            command = ["curl", "--silent", "--show-error", "--location",
                       "--proto", "=https", "--proto-redir", "=https",
                       "--connect-timeout", "4", "--max-time", "8",
                       "--user-agent", transport.transport._BROWSER_UA,
                       "--header", "Accept-Language: it-IT,it;q=0.9,en;q=0.7",
                       "--header", "Cache-Control: no-cache",
                       "--output", str(output), "--write-out", "%{json}"]
            if route == "ipv4":
                command.append("--ipv4")
            command.append(url)
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=12)
                metrics = json.loads(result.stdout or "{}")
                payload = output.read_text(errors="replace") if output.exists() else ""
                candidates = h4.radar_module.discovery_candidates(sources[source_id], payload, url) if result.returncode == 0 and metrics.get("http_code") == 200 else []
                row = {"sourceId": source_id, "url": url, "route": route,
                       "proxyConfigured": any(os.environ.get(key) for key in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy")),
                       "exitCode": result.returncode, "error": result.stderr[-1000:],
                       "candidateCount": len(candidates),
                       **{key: metrics.get(key) for key in (
                           "http_code", "remote_ip", "http_version", "url_effective", "num_redirects",
                           "time_namelookup", "time_connect", "time_appconnect", "time_starttransfer",
                           "time_total", "size_download", "content_type", "ssl_verify_result")}}
            except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
                row = {"sourceId": source_id, "url": url, "route": route, "error": str(exc), "exitCode": None}
            print("RADAR ROUTE PROBE: " + json.dumps(row, ensure_ascii=False), flush=True)
            return row

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(probe, requests))
    path = Path("reports/runtime/opportunity-route-diagnostic.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schemaVersion": "1.0", "diagnosticOnly": True,
                               "sources": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


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
            payload, diagnostics = transport.fetch_with_diagnostics(
                url,
                timeout=min(20, int(source.get("fetchTimeoutSeconds") or 18)),
                attempts=2,
            )
            transport._enforce_endpoint_content_signature(h4.radar_module, source, url, payload, diagnostics)
            endpoints.append({"url": url, **diagnostics, "role": transport.endpoint_role(source, url)})
        except Exception as exc:  # rete live: il report deve sopravvivere al failure
            diagnostics = dict(getattr(exc, "diagnostics", {}) or {})
            endpoints.append({
                "url": url,
                "role": transport.endpoint_role(source, url),
                "httpAttempts": int(diagnostics.get("httpAttempts") or 0),
                "status": "error",
                "transport": diagnostics.get("transport") or "failed",
                "fallbackUsed": bool(diagnostics.get("fallbackUsed")),
                "proxyUsed": bool(diagnostics.get("proxyUsed")),
                "initialFailureClass": diagnostics.get("initialFailureClass"),
                "rootFailureClass": diagnostics.get("rootFailureClass"),
                "browserFailureClass": diagnostics.get("browserFailureClass"),
                "readerFailureClass": diagnostics.get("readerFailureClass"),
                "terminalFailureClass": diagnostics.get("terminalFailureClass"),
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
    status = transport.coverage_status(endpoints)

    return {
        "sourceId": source_id,
        "status": status,
        "endpointCount": len(endpoints),
        "endpointOk": ok,
        "coverageEndpointOk": sum(row.get("status") == "ok" and row["role"] == "listing" for row in endpoints),
        "supplementaryEndpointOk": sum(row.get("status") == "ok" and row["role"] == "supplementary" for row in endpoints),
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnose-routes", action="store_true")
    args = parser.parse_args()
    config, _ = h4._compose_runtime_hardened()
    if args.diagnose_routes:
        return diagnose_routes(config)
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
