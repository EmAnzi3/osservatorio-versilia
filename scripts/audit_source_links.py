#!/usr/bin/env python3
"""Audit the official source links exposed by indicator cards.

The audit is intentionally diagnostic: institutional portals can block automated
clients even when they remain usable in a browser. Hard failures and apparently
empty HTML pages are printed separately from access restrictions.
"""
from __future__ import annotations

import concurrent.futures
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
REPORT_PATH = Path("/tmp/osservatorio-versilia-source-link-audit.json")
TIMEOUT = (8, 18)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,application/json,text/plain,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
}


def collect_links(data: dict) -> dict[str, list[str]]:
    links: dict[str, list[str]] = defaultdict(list)
    for key, metric in data.get("metrics", {}).items():
        url = metric.get("sourceUrl")
        if isinstance(url, str) and url.startswith("http"):
            links[html.unescape(url)].append(f"metrics.{key}.sourceUrl")
        benchmark = metric.get("meta", {}).get("benchmark")
        if isinstance(benchmark, dict):
            url = benchmark.get("url")
            if isinstance(url, str) and url.startswith("http"):
                links[html.unescape(url)].append(f"metrics.{key}.meta.benchmark.url")
    for key in ("businessSource", "arsSource"):
        url = data.get(key)
        if isinstance(url, str) and url.startswith("http"):
            links[html.unescape(url)].append(key)
    return dict(sorted(links.items()))


def visible_text(payload: bytes, encoding: str | None) -> tuple[str, str]:
    text = payload.decode(encoding or "utf-8", errors="replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else ""
    without_scripts = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", " ", without_scripts)
    plain = re.sub(r"\s+", " ", html.unescape(plain)).strip()
    return title, plain


def inspect(url: str) -> dict:
    result = {
        "url": url,
        "status": None,
        "classification": "error",
        "final_url": None,
        "content_type": None,
        "bytes": 0,
        "title": "",
        "visible_text_length": 0,
        "error": None,
    }
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            payload = response.content[:600_000]
            content_type = response.headers.get("content-type", "").lower()
            result.update(
                status=response.status_code,
                final_url=response.url,
                content_type=content_type,
                bytes=len(response.content),
            )
            if response.status_code in {401, 403, 429}:
                result["classification"] = "blocked"
                return result
            if response.status_code in {404, 410} or 400 <= response.status_code < 500:
                result["classification"] = "broken"
                return result
            if response.status_code >= 500:
                result["classification"] = "unavailable"
                return result
            if not payload:
                result["classification"] = "empty"
                return result
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                result["classification"] = "ok"
                return result

            title, plain = visible_text(payload, response.encoding)
            result["title"] = title
            result["visible_text_length"] = len(plain)
            error_markers = (
                "pagina non trovata",
                "page not found",
                "errore 404",
                "404 not found",
                "contenuto non disponibile",
            )
            sample = f"{title} {plain[:1500]}".lower()
            if any(marker in sample for marker in error_markers):
                result["classification"] = "broken"
            elif len(plain) < 80:
                script_count = len(re.findall(r"<script\b", payload.decode(response.encoding or "utf-8", errors="ignore"), flags=re.I))
                result["classification"] = "interactive_shell" if script_count >= 2 else "empty"
            else:
                result["classification"] = "ok"
            return result
        except requests.RequestException as exc:
            last_error = exc
    result["error"] = str(last_error) if last_error else "errore sconosciuto"
    host = urlparse(url).netloc
    if "siope.it" in host or "openbdap.rgs.mef.gov.it" in host:
        result["classification"] = "blocked_or_unavailable"
    return result


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    links = collect_links(data)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        inspected = list(executor.map(inspect, links))
    for item in inspected:
        item["references"] = links[item["url"]]

    counts: dict[str, int] = defaultdict(int)
    for item in inspected:
        counts[item["classification"]] += 1
    report = {
        "checked": len(inspected),
        "counts": dict(sorted(counts.items())),
        "results": inspected,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Audit link fonte: {len(inspected)} URL unici")
    print("Esito: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    for item in inspected:
        if item["classification"] != "ok":
            print(
                "LINK_AUDIT\t{classification}\t{status}\t{url}\t{final_url}\t{title}\t{references}".format(
                    references=",".join(item["references"]),
                    **item,
                )
            )
    print(f"Report completo: {REPORT_PATH}")


if __name__ == "__main__":
    main()
