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
from concurrent.futures import ThreadPoolExecutor


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
        self.lock = threading.Condition()
        self.pending = set()
        self.source_reserved = {}
        self.host_reserved = {}

    def _progress(self, row):
        with self.lock:
            with self.journal.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
            print("RADAR TRANSPORT: " + json.dumps(row, ensure_ascii=False), flush=True)

    def prefetch(self, config):
        """Fetch configured endpoints with four workers; reuse in normal collectors.

        This changes only scheduling. Classifiers and verification still consume
        the original endpoint payloads and apply their existing content gates.
        """
        requests = {}
        for category, default_timeout in (("sources", 30), ("discoverySources", 25)):
            for source in config.get(category) or []:
                if source.get("deferDiscoveryCheck"):
                    continue
                for url in [source.get("url"), *(source.get("urls") or [])]:
                    if url:
                        requests.setdefault(url, (int(source.get("fetchTimeoutSeconds") or default_timeout),
                                                  int(source.get("fetchAttempts") or 2)))
        def fetch_one(row):
            url, (timeout, attempts) = row
            return self.fetch(url, timeout=timeout, attempts=attempts)
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="radar-transport") as pool:
            # Consume every future; exceptions cannot silently disappear.
            list(pool.map(fetch_one, requests.items()))

    def fetch(self, url, *, timeout=30, attempts=2, kind="discovery", options=None, max_seconds=None):
        options = options or {}
        key = (kind, url, json.dumps(options, sort_keys=True))
        host = urlsplit(url).netloc
        ids = self.hosts.get(host, set())
        source = self.sources.get(url) or (next(iter(ids)) if len(ids) == 1 else host)
        # Lock only shared accounting. I/O must never hold this lock.
        with self.lock:
            while key in self.pending:
                self.lock.wait(timeout=max(0.01, self.deadline - time.monotonic()))
            if key in self.cache:
                return self.cache[key]
            while True:
                remaining_scan = self.deadline - time.monotonic()
                remaining_source = self.source_seconds - max(self.spent.get(source, 0), self.host_spent.get(host, 0))
                available = min(
                    self.source_seconds - self.spent.get(source, 0) - self.source_reserved.get(source, 0),
                    self.source_seconds - self.host_spent.get(host, 0) - self.host_reserved.get(host, 0),
                )
                wanted = min(self.endpoint_seconds, remaining_source, remaining_scan,
                             max_seconds if max_seconds is not None else self.endpoint_seconds)
                # Active requests reserve budget. Wait for their actual cost
                # instead of prematurely failing or overspending a shared host.
                if remaining_scan > 0 and wanted > 0 and available + 1e-6 < wanted:
                    self.lock.wait(timeout=remaining_scan)
                    continue
                allowance = max(0, min(wanted, available))
                break
            scope = "scan" if remaining_scan <= min(self.endpoint_seconds, remaining_source) else (
                "source" if remaining_source <= self.endpoint_seconds else "endpoint")
            self.pending.add(key)
            self.source_reserved[source] = self.source_reserved.get(source, 0) + allowance
            self.host_reserved[host] = self.host_reserved.get(host, 0) + allowance
            if scope == "scan" and allowance <= 0:
                self.scan_exhausted = True
            self._progress({"event": "start", "sourceId": source, "url": url,
                            "kind": kind, "budgetSeconds": round(allowance, 3)})
        started = time.monotonic()
        payload = None
        diagnostics = {"status": "error", "transport": "failed", "failureClass": "timeout_client",
                       "budgetScope": scope, "fallbackUsed": False, "proxyUsed": False,
                       "resolvedUrl": None, "errors": [f"{scope} transport budget exhausted"]}
        worker = None
        try:
            if allowance > 0:
                worker = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "--worker"],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, start_new_session=os.name != "nt",
                )
                output, error = worker.communicate(json.dumps({"url": url, "timeout": timeout,
                                                              "attempts": attempts, "kind": kind, "options": options}),
                                                   timeout=allowance)
                if worker.returncode != 0:
                    raise RuntimeError(error[-2000:] or f"worker exit {worker.returncode}")
                payload, diagnostics = json.loads(output)
        except subprocess.TimeoutExpired:
            if scope == "scan":
                with self.lock:
                    self.scan_exhausted = True
        except Exception as exc:
            diagnostics = {**diagnostics, "failureClass": "fetch_error", "errors": [str(exc)]}
        finally:
            if worker is not None:
                # A worker can exit while descendants linger: clean its group.
                if os.name != "nt":
                    try:
                        os.killpg(worker.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif worker.poll() is None:
                    worker.kill()
                worker.communicate()
            elapsed = time.monotonic() - started
            with self.lock:
                self.source_reserved[source] = max(0, self.source_reserved[source] - allowance)
                self.host_reserved[host] = max(0, self.host_reserved[host] - allowance)
                self.spent[source] = self.spent.get(source, 0) + elapsed
                self.host_spent[host] = self.host_spent.get(host, 0) + elapsed
                diagnostics = {**diagnostics, "elapsedSeconds": round(elapsed, 3), "sourceId": source}
                self._progress({"event": "end", "url": url, "kind": kind, **diagnostics})
                self.cache[key] = (payload, diagnostics)
                self.pending.remove(key)
                self.lock.notify_all()
        return payload, diagnostics


def _worker():
    request = json.load(sys.stdin)
    import opportunity_discovery_resilient as discovery
    try:
        kind = request["kind"]
        if kind in {"promotion_document", "promotion_page", "review_page"}:
            from opportunity_document_promotion import fetch_receipt
            payload = fetch_receipt(request["url"], document=kind == "promotion_document", timeout=request["timeout"],
                                    allowed_hosts=set(request["options"]["allowedHosts"]) if kind == "review_page" else None)
            result = (payload, {"status": "ok", "transport": "direct_https", "proxyUsed": False,
                                "fallbackUsed": False, "failureClass": None, "resolvedUrl": payload["resolvedUrl"], "errors": []})
        elif kind == "continuity":
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
