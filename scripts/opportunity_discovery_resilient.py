#!/usr/bin/env python3
"""Trasporto resiliente e diagnostica strutturata per il discovery del Radar.

Il collector storico distingueva soltanto successo/errore e usava un fetch HTTP
semplice. Questo modulo mantiene invariati parser e regole di ammissibilità ma
rende il trasporto più adatto ai portali istituzionali: HTTP browser-like con
retry, fallback Chromium selettivo e classificazione esplicita dei fallimenti.
"""
from __future__ import annotations

import socket
import urllib.error
from typing import Any

import opportunity_daily_refresh_revalidated as transport


class DiscoveryFetchError(RuntimeError):
    """Errore di trasporto con diagnostica serializzabile nel risultato Radar."""

    def __init__(self, message: str, diagnostics: dict[str, Any]):
        super().__init__(message)
        self.diagnostics = diagnostics


def classify_fetch_error(exc: BaseException) -> str:
    """Classifica la causa tecnica senza confonderla con un outage della fonte."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 403:
            return "http_403_waf"
        if exc.code == 429:
            return "http_429_rate_limit"
        if exc.code in {404, 410}:
            return "endpoint_missing"
        if 500 <= exc.code <= 599:
            return "http_5xx"
        return f"http_{exc.code}"

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout_client"

    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "timeout_client"
        folded = str(reason or exc).casefold()
        if "timed out" in folded or "timeout" in folded:
            return "timeout_client"
        if "name or service not known" in folded or "temporary failure in name resolution" in folded:
            return "dns_error"
        return "network_error"

    folded = str(exc).casefold()
    if "timed out" in folded or "timeout" in folded:
        return "timeout_client"
    return "fetch_error"


def _browser_fallback_allowed(failure_class: str) -> bool:
    return failure_class in {
        "http_403_waf",
        "http_429_rate_limit",
        "http_5xx",
        "timeout_client",
        "dns_error",
        "network_error",
        "fetch_error",
    }


def fetch_with_diagnostics(
    url: str,
    timeout: int = 30,
    attempts: int = 2,
) -> tuple[str, dict[str, Any]]:
    """Scarica una pagina e restituisce anche il percorso di trasporto seguito."""
    http_attempts = max(2, int(attempts or 1))
    errors: list[str] = []
    try:
        payload = transport._fetch_browser_html(url, timeout=timeout, attempts=http_attempts)
        return payload, {
            "status": "ok",
            "transport": "http_browser",
            "httpAttempts": http_attempts,
            "fallbackUsed": False,
            "initialFailureClass": None,
            "errors": [],
        }
    except Exception as http_error:  # pragma: no cover - dipende dalla rete live
        failure_class = classify_fetch_error(http_error)
        errors.append(f"HTTP [{failure_class}]: {http_error}")

    if _browser_fallback_allowed(failure_class):
        try:
            payload = transport._fetch_playwright_text(
                url,
                timeout_ms=max(20_000, min(45_000, timeout * 1000)),
            )
            if not str(payload or "").strip():
                raise RuntimeError("Chromium ha restituito un payload vuoto")
            return payload, {
                "status": "ok",
                "transport": "chromium",
                "httpAttempts": http_attempts,
                "fallbackUsed": True,
                "initialFailureClass": failure_class,
                "errors": errors,
            }
        except Exception as browser_error:  # pragma: no cover - dipende dalla rete/browser live
            browser_class = classify_fetch_error(browser_error)
            errors.append(f"Chromium [{browser_class}]: {browser_error}")
            diagnostics = {
                "status": "error",
                "transport": "failed",
                "httpAttempts": http_attempts,
                "fallbackUsed": True,
                "initialFailureClass": failure_class,
                "failureClass": browser_class if browser_class != "fetch_error" else failure_class,
                "errors": errors,
            }
            raise DiscoveryFetchError("; ".join(errors), diagnostics) from browser_error

    diagnostics = {
        "status": "error",
        "transport": "failed",
        "httpAttempts": http_attempts,
        "fallbackUsed": False,
        "initialFailureClass": failure_class,
        "failureClass": failure_class,
        "errors": errors,
    }
    raise DiscoveryFetchError("; ".join(errors), diagnostics)


def fetch_resilient(url: str, timeout: int = 30, attempts: int = 2) -> str:
    """Compatibilità drop-in con il fetch del motore storico."""
    payload, _ = fetch_with_diagnostics(url, timeout=timeout, attempts=attempts)
    return payload


def probe_discovery_sources(
    radar_module: Any,
    config: dict[str, Any],
    *,
    payloads: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Versione resiliente del probe v0.3, con diagnostica endpoint per endpoint."""
    payloads = payloads or {}
    queue: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []

    for source in config.get("discoverySources") or []:
        urls = list(source.get("urls") or [])
        endpoint_ok = 0
        endpoint_errors: list[str] = []
        endpoint_results: list[dict[str, Any]] = []
        source_candidates: list[dict[str, Any]] = []

        for url in urls:
            try:
                if url in payloads:
                    payload = payloads[url]
                    diagnostics = {
                        "status": "ok",
                        "transport": "fixture",
                        "httpAttempts": 0,
                        "fallbackUsed": False,
                        "initialFailureClass": None,
                        "errors": [],
                    }
                else:
                    payload, diagnostics = fetch_with_diagnostics(
                        url,
                        timeout=int(source.get("fetchTimeoutSeconds") or 25),
                        attempts=int(source.get("fetchAttempts") or 2),
                    )
                endpoint_ok += 1
                endpoint_results.append({"url": url, **diagnostics})
                source_candidates.extend(radar_module.discovery_candidates(source, payload, url))
            except Exception as exc:  # pragma: no cover - dipende dalla rete live
                diagnostics = dict(getattr(exc, "diagnostics", {}) or {})
                failure_class = str(diagnostics.get("failureClass") or classify_fetch_error(exc))
                endpoint_errors.append(f"{url} [{failure_class}]: {exc}")
                endpoint_results.append({
                    "url": url,
                    "status": "error",
                    "transport": diagnostics.get("transport") or "failed",
                    "fallbackUsed": bool(diagnostics.get("fallbackUsed")),
                    "initialFailureClass": diagnostics.get("initialFailureClass"),
                    "failureClass": failure_class,
                    "errors": diagnostics.get("errors") or [str(exc)],
                })

        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for item in source_candidates:
            key = (
                radar_module.v025.fold(item.get("title")),
                radar_module.v025.normalized_url(item.get("url")),
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
            "fallbackSuccessCount": sum(
                row.get("status") == "ok" and row.get("transport") == "chromium"
                for row in endpoint_results
            ),
            "failureClasses": sorted({
                str(row.get("failureClass"))
                for row in endpoint_results
                if row.get("failureClass")
            }),
            "endpointResults": endpoint_results,
            "candidateCount": len(source_candidates),
            "errors": endpoint_errors,
            "freshness": {"status": "discovery", "observedDate": None, "ageDays": None},
        })

    queue.sort(key=lambda item: (str(item.get("source_label") or ""), str(item.get("title") or "")))
    return queue, states
