#!/usr/bin/env python3
"""Bound live Radar I/O; incomplete checks remain transport failures.

Workers isolate HTTP reads, browser startup/cleanup and fallback chains. Killing
an expired worker also kills its browser descendants on the Linux Actions runner.
The journal is append-only and flushed before each request, even if CI cancels.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit


class TransportBudget:
    def __init__(self, config, *, endpoint_seconds=60, source_seconds=180,
                 scan_seconds=1200, journal=Path("reports/runtime/opportunity-transport-progress.jsonl")):
        self.endpoint_seconds = endpoint_seconds
        self.source_seconds = source_seconds
        self.deadline = time.monotonic() + scan_seconds
        self.journal = Path(journal)
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.journal.write_text("", encoding="utf-8")
        self.sources = {}
        self.hosts = {}
        for source in [*(config.get("sources") or []), *(config.get("discoverySources") or [])]:
            source_id = str(source.get("id") or "")
            for url in [source.get("url"), *(source.get("urls") or [])]:
                if url:
                    self.sources[url] = source_id
                    self.hosts.setdefault(urlsplit(url).netloc, set()).add(source_id)
        self.scan_exhausted = False
        self.spent = {}
        self.host_spent = {}
        self.cache = {}
        self.lock = threading.Lock()

    def _progress(self, row):
        with self.journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
        print("RADAR TRANSPORT: " + json.dumps(row, ensure_ascii=False), flush=True)

    def fetch(self, url, *, timeout=30, attempts=2, kind="discovery", options=None):
        # Holdout threads share the same run/source budgets and cache.
        with self.lock:
            return self._fetch(url, timeout=timeout, attempts=attempts, kind=kind, options=options or {})

    def _fetch(self, url, *, timeout, attempts, kind, options):
        key = (kind, url, json.dumps(options, sort_keys=True))
        if key in self.cache:
            return self.cache[key]
        host = urlsplit(url).netloc
        ids = self.hosts.get(host, set())
        source = self.sources.get(url) or (next(iter(ids)) if len(ids) == 1 else host)
        remaining_source = self.source_seconds - max(self.spent.get(source, 0), self.host_spent.get(host, 0))
        remaining_scan = self.deadline - time.monotonic()
        allowance = min(self.endpoint_seconds, remaining_source, remaining_scan)
        scope = "scan" if remaining_scan <= min(self.endpoint_seconds, remaining_source) else (
            "source" if remaining_source <= self.endpoint_seconds else "endpoint")
        started = time.monotonic()
        if scope == "scan" and allowance <= 0:
            self.scan_exhausted = True
        self._progress({"event": "start", "sourceId": source, "url": url,
                        "kind": kind, "budgetSeconds": round(max(0, allowance), 3)})
        payload = None
        diagnostics = {"status": "error", "transport": "failed", "failureClass": "timeout_client",
                       "budgetScope": scope, "fallbackUsed": False, "proxyUsed": False,
                       "resolvedUrl": None, "errors": [f"{scope} transport budget exhausted"]}
        if allowance > 0:
            worker = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--worker"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, start_new_session=os.name != "nt",
            )
            try:
                output, error = worker.communicate(json.dumps({"url": url, "timeout": timeout,
                                                              "attempts": attempts, "kind": kind, "options": options}),
                                                   timeout=allowance)
                if worker.returncode != 0:
                    raise RuntimeError(error[-2000:] or f"worker exit {worker.returncode}")
                payload, diagnostics = json.loads(output)
            except subprocess.TimeoutExpired:
                if scope == "scan":
                    self.scan_exhausted = True
            except Exception as exc:
                diagnostics = {**diagnostics, "failureClass": "fetch_error", "errors": [str(exc)]}
            finally:
                # A worker can exit while descendants linger: always clean its group.
                if os.name != "nt":
                    try:
                        os.killpg(worker.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif worker.poll() is None:
                    worker.kill()
                worker.communicate()
        elapsed = time.monotonic() - started
        self.spent[source] = self.spent.get(source, 0) + elapsed
        self.host_spent[host] = self.host_spent.get(host, 0) + elapsed
        diagnostics = {**diagnostics, "elapsedSeconds": round(elapsed, 3), "sourceId": source}
        self._progress({"event": "end", "url": url, "kind": kind, **diagnostics})
        self.cache[key] = (payload, diagnostics)
        return payload, diagnostics


def _worker():
    request = json.load(sys.stdin)
    import opportunity_discovery_resilient as discovery
    try:
        kind = request["kind"]
        if kind == "continuity":
            import opportunity_daily_refresh_stable as stable
            result = stable._fetch_continuity_detail(request["url"])
        elif kind.startswith("official_"):
            transport = discovery.transport
            if kind == "official_http":
                payload = transport._fetch_browser_html(request["url"], timeout=request["timeout"],
                                                         attempts=request["attempts"])
            elif kind == "official_browser":
                payload = transport._fetch_playwright_text(request["url"], **request["options"])
            elif kind == "official_pdf":
                payload = transport.pdf_evidence.fetch_pdf_text(request["url"], **request["options"])
            else:
                raise ValueError(f"Unknown verification transport: {kind}")
            result = (payload, {"status": "ok", "transport": {"official_http": "http_browser", "official_browser": "chromium", "official_pdf": "http_pdf"}[kind], "proxyUsed": False,
                                "fallbackUsed": kind == "official_browser", "failureClass": None, "resolvedUrl": request["url"],
                                "errors": []})
        else:
            result = discovery.fetch_with_diagnostics(request["url"], timeout=request["timeout"],
                                                      attempts=request["attempts"])
    except Exception as exc:
        diagnostics = getattr(exc, "diagnostics", None) or {
            "status": "error", "transport": "failed", "proxyUsed": False,
            "fallbackUsed": False, "failureClass": discovery.classify_fetch_error(exc),
            "errors": [str(exc)], "resolvedUrl": None,
        }
        result = (None, diagnostics)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    _worker()
