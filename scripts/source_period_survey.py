#!/usr/bin/env python3
"""Ricognizione delle pagine fonte degli indicatori ancora senza verifica di periodo.

Strumento di collaudo, non di produzione: per ogni URL fonte degli indicatori con
`pendingLot` in `ci/release-probe-coverage.json` scarica la pagina dai runner GitHub
e stampa nel log, in forma compatta, stato HTTP, tipo, dimensione, gli anni citati
più recenti con il contesto e i link che contengono un anno. Serve a scrivere le
verifiche di periodo; non modifica nulla.

    python scripts/source_period_survey.py --catalog /tmp/ov-public/site-data.json
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import monthly_data_check as base  # noqa: E402

ROOT = SCRIPT_DIR.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
YEAR = re.compile(r"(?<!\d)(20[0-3]\d)(?!\d)")
HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)


def fetch(url: str) -> tuple[str, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return str(r.status), r.headers.get("Content-Type", ""), r.read(25_000_000)
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}", e.headers.get("Content-Type", "") if e.headers else "", b""
    except Exception as e:  # noqa: BLE001
        return f"ERR {type(e).__name__}: {str(e)[:80]}", "", b""


def text_of(raw: bytes) -> str:
    t = raw.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


def survey(url: str, keys: list[str], periods: list[str]) -> list[str]:
    status, ctype, raw = fetch(url)
    out = [f"=== {url}", f"  metriche: {' '.join(keys)[:300]}", f"  pubblicato: {sorted(set(periods))}",
           f"  esito: {status} · {ctype[:40]} · {len(raw)} byte"]
    if not raw:
        return out
    if "html" not in ctype and not raw.lstrip()[:1] in (b"<",):
        sample = raw[:400].decode("utf-8", "replace").replace("\n", " ⏎ ")
        years = collections.Counter(YEAR.findall(raw[:3_000_000].decode("latin-1")))
        out.append(f"  anni: {sorted(years.items(), reverse=True)[:8]}")
        out.append(f"  inizio: {sample[:300]}")
        return out
    page = raw.decode("utf-8", "replace")
    txt = text_of(raw)
    years = collections.Counter(YEAR.findall(txt))
    out.append(f"  anni nel testo: {sorted(years.items(), reverse=True)[:8]}")
    for y in sorted(years, reverse=True)[:2]:
        for m in list(re.finditer(rf"(?<!\d){y}(?!\d)", txt))[:2]:
            out.append(f"  [{y}] …{txt[max(0, m.start() - 90): m.end() + 60]}…")
    links = [h for h in HREF.findall(page) if YEAR.search(h)]
    for h in sorted(set(links), key=lambda h: max(YEAR.findall(h)), reverse=True)[:6]:
        out.append(f"  link: {h[:160]}")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--only", help="sottostringa dell'URL")
    a = p.parse_args()
    site = json.loads(a.catalog.read_text(encoding="utf-8"))["metrics"]
    cov = json.loads((ROOT / "ci/release-probe-coverage.json").read_text(encoding="utf-8"))["metrics"]
    by_url: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for key, spec in cov.items():
        if "probe" in spec or key not in site:
            continue
        for _, url in base.iter_metric_sources(site[key]):
            by_url[url].append((key, str(site[key]["meta"].get("year"))))
    for url in sorted(by_url):
        if a.only and a.only not in url:
            continue
        print("\n".join(survey(url, [k for k, _ in by_url[url]], [y for _, y in by_url[url]])), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
