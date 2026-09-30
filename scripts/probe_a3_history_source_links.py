#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import requests

FILE_RE = re.compile(r"""(?:href|src)=["']([^"']+\.(?:csv|json|zip|xlsx?|ods)(?:\?[^"']*)?)["']""", re.I)
ABS_RE = re.compile(r"""https?://[^\s"'<>]+\.(?:csv|json|zip|xlsx?|ods)(?:\?[^\s"'<>]*)?""", re.I)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}(?:[-_/]?(?:19|20)?\d{2})?\b")


def probe(url: str) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "OsservatorioVersilia-A3-history-source-probe/1.0"
    response = session.get(url, timeout=120)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    text = response.text if "text" in content_type or "json" in content_type or "html" in content_type else ""
    links = set()
    for match in FILE_RE.findall(text):
        links.add(urljoin(response.url, unescape(match)))
    links.update(unescape(match) for match in ABS_RE.findall(text))
    years = sorted(set(YEAR_RE.findall(text)))
    return {
        "requestedUrl": url,
        "resolvedUrl": response.url,
        "status": response.status_code,
        "contentType": content_type,
        "bytes": len(response.content),
        "yearsMentioned": years,
        "fileLinks": sorted(links),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--url", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = {
        "schemaVersion": 1,
        "profile": args.profile,
        "sources": [],
    }
    failures = []
    for url in args.url:
        try:
            report["sources"].append(probe(url))
        except Exception as exc:
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    report["failures"] = failures

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "profile": args.profile,
        "sourceCount": len(report["sources"]),
        "failureCount": len(failures),
        "discoveredFileLinks": sum(len(item["fileLinks"]) for item in report["sources"]),
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    if not report["sources"]:
        raise SystemExit(f"{args.profile}: nessuna fonte raggiungibile")


if __name__ == "__main__":
    main()
