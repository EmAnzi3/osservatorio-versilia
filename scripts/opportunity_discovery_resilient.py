#!/usr/bin/env python3
"""Trasporto resiliente e diagnostica strutturata per il discovery del Radar.

Ordine di trasporto: HTTP browser-like, Chromium, quindi Jina Reader soltanto
come fallback di discovery. RSS/Atom e WordPress REST ufficiali vengono
normalizzati in card HTML prima di riusare il parser/classificatore storico.

Un reader proxy non costituisce mai verifica della fonte e non può promuovere
un'opportunità: la sorgente resta ``degraded`` finché il collegamento diretto non
è disponibile.
"""
from __future__ import annotations

import html
import json
import re
import socket
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

import opportunity_daily_refresh_revalidated as transport

FETCH_TRACE: dict[str, dict[str, Any]] = {}
_READER_BASE = "https://r.jina.ai/"
_GENERIC_LINK_LABELS = {
    "scopri", "scopri tutto", "leggi", "leggi tutto", "approfondisci",
    "continua", "vai", "azioni", "dettagli", "more", "read more",
}


class DiscoveryFetchError(RuntimeError):
    def __init__(self, message: str, diagnostics: dict[str, Any]):
        super().__init__(message)
        self.diagnostics = diagnostics


def reset_trace() -> None:
    FETCH_TRACE.clear()


def _record_trace(url: str, diagnostics: dict[str, Any]) -> None:
    FETCH_TRACE[url] = {"url": url, **diagnostics}


def classify_fetch_error(exc: BaseException) -> str:
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
    return "timeout_client" if "timed out" in folded or "timeout" in folded else "fetch_error"


def _browser_fallback_allowed(failure_class: str) -> bool:
    return failure_class in {
        "http_403_waf", "http_429_rate_limit", "http_5xx",
        "timeout_client", "network_error", "fetch_error",
    }


def _reader_fallback_allowed(failure_class: str) -> bool:
    return _browser_fallback_allowed(failure_class)


def _fetch_browser_html_with_url(url: str, timeout: int = 30, attempts: int = 2) -> tuple[str, str]:
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": transport._BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml,application/atom+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace"), response.geturl()
        except Exception as exc:  # pragma: no cover - rete live
            last_error = exc
            if attempt + 1 < max(1, attempts):
                time.sleep(1.0 + attempt)
    assert last_error is not None
    raise last_error


def _fetch_playwright_html(url: str, timeout_ms: int = 45_000) -> tuple[str, str]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=transport._BROWSER_UA,
            locale="it-IT",
            ignore_https_errors=True,
            extra_http_headers={"Accept-Language": "it-IT,it;q=0.9,en;q=0.7", "Cache-Control": "no-cache"},
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightTimeoutError:
                pass
            rendered = page.content()
            if not rendered.strip():
                raise RuntimeError("Chromium ha restituito un DOM vuoto")
            return rendered, page.url
        finally:
            context.close()
            browser.close()


def _fetch_reader_markdown(url: str, timeout: int = 35) -> str:
    request = urllib.request.Request(
        _READER_BASE + url,
        headers={
            "User-Agent": transport._BROWSER_UA,
            "Accept": "text/plain,text/markdown;q=0.9,*/*;q=0.8",
            "X-Engine": "cf-browser-rendering",
        },
    )
    with urllib.request.urlopen(request, timeout=max(15, min(45, timeout))) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _strip_markup(text: Any) -> str:
    value = html.unescape(str(text or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_`>#]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _card(title: str, href: str, body: str) -> str:
    return "<h3><a href=\"{}\">{}</a></h3><p>{}</p>".format(
        html.escape(href, quote=True), html.escape(_strip_markup(title)), html.escape(_strip_markup(body)[:1800])
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def _child_text(node: ET.Element, names: set[str]) -> str:
    for child in list(node):
        if _local_name(child.tag) in names:
            return "".join(child.itertext()).strip()
    return ""


def _syndication_to_html(payload: str, page_url: str) -> str | None:
    stripped = payload.lstrip()
    if not stripped.startswith("<"):
        return None
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return None
    root_name = _local_name(root.tag)
    if root_name not in {"rss", "feed", "rdf"}:
        return None

    cards: list[str] = []
    for node in root.iter():
        if _local_name(node.tag) not in {"item", "entry"}:
            continue
        title = _child_text(node, {"title"})
        href = _child_text(node, {"link"})
        if not href:
            for child in list(node):
                if _local_name(child.tag) == "link" and child.attrib.get("href"):
                    href = str(child.attrib["href"])
                    break
        body = _child_text(node, {"description", "summary", "content", "encoded"})
        published = _child_text(node, {"pubdate", "published", "updated", "date"})
        if title and href:
            cards.append(_card(title, href, f"{published}. {body}"))
    return "<html><body>" + "".join(cards) + "</body></html>" if cards else None


def _wordpress_json_to_html(payload: str) -> str | None:
    stripped = payload.lstrip()
    if not stripped.startswith(("[", "{")):
        return None
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        return None

    if isinstance(raw, dict):
        candidates = raw.get("posts") or raw.get("items") or raw.get("results")
        if candidates is None and {"title", "link"} <= set(raw):
            candidates = [raw]
    else:
        candidates = raw
    if not isinstance(candidates, list):
        return None

    cards: list[str] = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        title_raw = row.get("title")
        title = title_raw.get("rendered") if isinstance(title_raw, dict) else title_raw
        href = row.get("link") or row.get("url")
        excerpt_raw = row.get("excerpt") or row.get("summary") or row.get("content")
        if isinstance(excerpt_raw, dict):
            excerpt = excerpt_raw.get("rendered") or excerpt_raw.get("raw") or ""
        else:
            excerpt = excerpt_raw or ""
        date_text = row.get("date") or row.get("date_gmt") or row.get("modified") or ""
        if title and href:
            cards.append(_card(str(title), str(href), f"{date_text}. {excerpt}"))
    return "<html><body>" + "".join(cards) + "</body></html>" if cards else None


def normalize_discovery_payload(payload: str, page_url: str) -> tuple[str, str]:
    """Converte feed/API ufficiali nel formato già compreso dal parser storico."""
    structured = _syndication_to_html(payload, page_url)
    if structured:
        return structured, "syndication"
    structured = _wordpress_json_to_html(payload)
    if structured:
        return structured, "structured_json"
    return payload, "html"


def _markdown_to_discovery_html(markdown: str, page_url: str) -> str:
    lines = [line.rstrip() for line in markdown.splitlines()]
    cards: list[str] = []
    recent_heading: str | None = None
    recent_heading_at = -99
    link_re = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]+)\)")
    for index, line in enumerate(lines):
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading:
            recent_heading = _strip_markup(heading.group(1))
            recent_heading_at = index
        for match in link_re.finditer(line):
            label = _strip_markup(match.group(1))
            href = match.group(2).strip()
            title = label
            if label.casefold().strip(" .:–—-") in _GENERIC_LINK_LABELS and recent_heading and index - recent_heading_at <= 5:
                title = recent_heading
            if len(title) < 7:
                continue
            context = " ".join(lines[max(0, index - 3):min(len(lines), index + 4)])
            cards.append(_card(title, href, context))
    if not cards:
        visible = _strip_markup(markdown)
        if visible:
            cards.append("<h3>Aggiornamenti dalla fonte ufficiale</h3><p>{}</p>".format(html.escape(visible[:5000])))
    return "<html><body>" + "".join(cards) + "</body></html>"


def fetch_with_diagnostics(url: str, timeout: int = 30, attempts: int = 2) -> tuple[str, dict[str, Any]]:
    http_attempts = max(2, int(attempts or 1))
    errors: list[str] = []
    failure_class = "fetch_error"
    try:
        payload, resolved_url = _fetch_browser_html_with_url(url, timeout=timeout, attempts=http_attempts)
        diagnostics = {
            "status": "ok", "transport": "http_browser", "httpAttempts": http_attempts,
            "fallbackUsed": False, "proxyUsed": False, "initialFailureClass": None,
            "browserFailureClass": None, "failureClass": None, "resolvedUrl": resolved_url,
            "redirected": resolved_url != url, "errors": [],
        }
        _record_trace(url, diagnostics)
        return payload, diagnostics
    except Exception as http_error:  # pragma: no cover
        failure_class = classify_fetch_error(http_error)
        errors.append(f"HTTP [{failure_class}]: {http_error}")

    browser_failure_class: str | None = None
    if _browser_fallback_allowed(failure_class):
        try:
            payload, resolved_url = _fetch_playwright_html(url, timeout_ms=max(20_000, min(45_000, timeout * 1000)))
            diagnostics = {
                "status": "ok", "transport": "chromium", "httpAttempts": http_attempts,
                "fallbackUsed": True, "proxyUsed": False, "initialFailureClass": failure_class,
                "browserFailureClass": None, "failureClass": None, "resolvedUrl": resolved_url,
                "redirected": resolved_url != url, "errors": errors,
            }
            _record_trace(url, diagnostics)
            return payload, diagnostics
        except Exception as browser_error:  # pragma: no cover
            browser_failure_class = classify_fetch_error(browser_error)
            errors.append(f"Chromium [{browser_failure_class}]: {browser_error}")

    if _reader_fallback_allowed(failure_class):
        try:
            markdown = _fetch_reader_markdown(url, timeout=max(20, timeout))
            payload = _markdown_to_discovery_html(markdown, url)
            diagnostics = {
                "status": "ok", "transport": "reader_proxy", "httpAttempts": http_attempts,
                "fallbackUsed": True, "proxyUsed": True, "initialFailureClass": failure_class,
                "browserFailureClass": browser_failure_class, "failureClass": None,
                "resolvedUrl": url, "redirected": False, "errors": errors,
            }
            _record_trace(url, diagnostics)
            return payload, diagnostics
        except Exception as reader_error:  # pragma: no cover
            reader_class = classify_fetch_error(reader_error)
            errors.append(f"Reader [{reader_class}]: {reader_error}")
            final_class = reader_class if reader_class != "fetch_error" else (browser_failure_class or failure_class)
            diagnostics = {
                "status": "error", "transport": "failed", "httpAttempts": http_attempts,
                "fallbackUsed": True, "proxyUsed": True, "initialFailureClass": failure_class,
                "browserFailureClass": browser_failure_class, "failureClass": final_class,
                "resolvedUrl": None, "redirected": False, "errors": errors,
            }
            _record_trace(url, diagnostics)
            raise DiscoveryFetchError("; ".join(errors), diagnostics) from reader_error

    diagnostics = {
        "status": "error", "transport": "failed", "httpAttempts": http_attempts,
        "fallbackUsed": False, "proxyUsed": False, "initialFailureClass": failure_class,
        "browserFailureClass": browser_failure_class, "failureClass": failure_class,
        "resolvedUrl": None, "redirected": False, "errors": errors,
    }
    _record_trace(url, diagnostics)
    raise DiscoveryFetchError("; ".join(errors), diagnostics)


def fetch_resilient(url: str, timeout: int = 30, attempts: int = 2) -> str:
    payload, _ = fetch_with_diagnostics(url, timeout=timeout, attempts=attempts)
    return payload


def probe_discovery_sources(radar_module: Any, config: dict[str, Any], *, payloads: dict[str, str] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
                        "status": "ok", "transport": "fixture", "httpAttempts": 0,
                        "fallbackUsed": False, "proxyUsed": False, "initialFailureClass": None,
                        "browserFailureClass": None, "failureClass": None, "resolvedUrl": url,
                        "redirected": False, "errors": [],
                    }
                else:
                    payload, diagnostics = fetch_with_diagnostics(
                        url,
                        timeout=int(source.get("fetchTimeoutSeconds") or 25),
                        attempts=int(source.get("fetchAttempts") or 2),
                    )
                endpoint_ok += 1
                payload, payload_format = normalize_discovery_payload(payload, str(diagnostics.get("resolvedUrl") or url))
                diagnostics = {**diagnostics, "payloadFormat": payload_format}
                endpoint_results.append({"url": url, **diagnostics})
                page_url = str(diagnostics.get("resolvedUrl") or url)
                source_candidates.extend(radar_module.discovery_candidates(source, payload, page_url))
            except Exception as exc:  # pragma: no cover
                diagnostics = dict(getattr(exc, "diagnostics", {}) or {})
                failure = str(diagnostics.get("failureClass") or classify_fetch_error(exc))
                endpoint_errors.append(f"{url} [{failure}]: {exc}")
                endpoint_results.append({
                    "url": url, "status": "error", "transport": diagnostics.get("transport") or "failed",
                    "fallbackUsed": bool(diagnostics.get("fallbackUsed")), "proxyUsed": bool(diagnostics.get("proxyUsed")),
                    "initialFailureClass": diagnostics.get("initialFailureClass"),
                    "browserFailureClass": diagnostics.get("browserFailureClass"), "failureClass": failure,
                    "resolvedUrl": diagnostics.get("resolvedUrl"), "redirected": bool(diagnostics.get("redirected")),
                    "errors": diagnostics.get("errors") or [str(exc)],
                })

        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for item in source_candidates:
            key = (radar_module.v025.fold(item.get("title")), radar_module.v025.normalized_url(item.get("url")))
            unique[key] = item
        source_candidates = list(unique.values())[:50]
        queue.extend(source_candidates)
        proxy_successes = sum(row.get("status") == "ok" and row.get("transport") == "reader_proxy" for row in endpoint_results)
        if endpoint_ok == len(urls) and urls and not proxy_successes:
            runtime = "ok"
        elif endpoint_ok:
            runtime = "degraded"
        else:
            runtime = "error"
        states.append({
            "sourceId": source["id"], "status": runtime, "endpointCount": len(urls), "endpointOk": endpoint_ok,
            "fallbackSuccessCount": sum(row.get("status") == "ok" and row.get("transport") in {"chromium", "reader_proxy"} for row in endpoint_results),
            "proxySuccessCount": proxy_successes,
            "failureClasses": sorted({str(row.get("failureClass")) for row in endpoint_results if row.get("failureClass")}),
            "endpointResults": endpoint_results, "candidateCount": len(source_candidates), "errors": endpoint_errors,
            "freshness": {"status": "discovery", "observedDate": None, "ageDays": None},
        })
    queue.sort(key=lambda item: (str(item.get("source_label") or ""), str(item.get("title") or "")))
    return queue, states
