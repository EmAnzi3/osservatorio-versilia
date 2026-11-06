#!/usr/bin/env python3
"""Scarica un elenco di URL ufficiali e ne salva copia e manifest.

Serve a collaudare le verifiche di periodo su fonti che si raggiungono solo
dai runner GitHub (Istat, Regione Toscana, …). Non modifica alcun dato: legge
`ci/probe-fetch-list.json` e scrive file e `manifest.json` in una cartella.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST = ROOT / "ci" / "probe-fetch-list.json"
USER_AGENT = "OsservatorioVersilia-source-audit/1.0 (+https://osservatorioversilia.it)"


def safe_name(index: int, url: str) -> str:
    tail = re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("://", 1)[-1])[-120:]
    return f"{index:03d}-{tail}"


def fetch(url: str, timeout: int) -> tuple[int | None, dict, bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read(), response.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read() if exc.fp else b"", url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--list", type=Path, default=LIST)
    parser.add_argument("--max-bytes", type=int, default=150_000_000)
    args = parser.parse_args()
    entries = json.loads(args.list.read_text(encoding="utf-8"))["urls"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, entry in enumerate(entries, 1):
        url = entry["url"] if isinstance(entry, dict) else entry
        timeout = int(entry.get("timeout", 300)) if isinstance(entry, dict) else 300
        started = time.time()
        item = {"url": url}
        try:
            status, headers, body, final = fetch(url, timeout)
            name = safe_name(index, final)
            if len(body) <= args.max_bytes:
                (args.output_dir / name).write_bytes(body)
                item["file"] = name
            item.update(status=status, finalUrl=final, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                        contentType=headers.get("Content-Type"), lastModified=headers.get("Last-Modified"),
                        head=body[:300].decode("utf-8", "replace"))
        except Exception as exc:  # rete, timeout
            item.update(error=f"{type(exc).__name__}: {exc}")
        item["seconds"] = round(time.time() - started, 1)
        manifest.append(item)
        print(json.dumps({k: v for k, v in item.items() if k != "head"}, ensure_ascii=False))
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
