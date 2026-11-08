#!/usr/bin/env python3
"""Ricognizione delle pagine fonte usate dalle verifiche del solo periodo.

Strumento di collaudo, non di produzione: per ogni regola `sourceChecks` di
`ci/release-probe-coverage.json` scarica la pagina dai runner GitHub come la scarica la
verifica e stampa nel log esito, anni citati con il contesto e periodi catturati dalla
regola. Serve a calibrare le regole; non modifica nulla.

    python scripts/source_period_survey.py --catalog /tmp/ov-public/site-data.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import release_period_probes as probes  # noqa: E402

ROOT = SCRIPT_DIR.parent
YEAR = re.compile(r"(?<!\d)(20[0-3]\d)(?!\d)")


def survey_check(name: str, check: dict, metric: dict) -> list[str]:
    """Pagina di una regola `sourceChecks`, scaricata come la scarica la verifica."""
    published = probes.published_period(metric, {"name": name, **check})
    url = probes.check_url(check["url"], published)
    out = [f"=== [{name}] {url}", f"  modo: {check.get('mode', 'latest')} · regola: {check.get('pattern', '')[:120]}"]
    try:
        raw = probes.http_fetch("QUICK " + url)
    except probes.ProbeError as error:
        return out + [f"  esito: {error.reason}: {error.detail[:200]}"]
    try:
        txt = probes.page_text(raw, check.get("text", "auto"))
    except Exception as error:  # noqa: BLE001
        return out + [f"  esito: {len(raw)} byte, testo illeggibile: {error}"]
    years = collections.Counter(YEAR.findall(txt))
    out.append(f"  esito: {len(raw)} byte · anni: {sorted(years.items(), reverse=True)[:10]}")
    if check.get("pattern"):
        found = [m.group(1) for m in re.finditer(check["pattern"], txt)][:8]
        out.append(f"  catturati: {found}")
    for y in sorted(years, reverse=True)[:3]:
        for m in list(re.finditer(rf"(?<!\d){y}(?!\d)", txt))[:3]:
            out.append(f"  [{y}] …{txt[max(0, m.start() - 110): m.end() + 50]}…".replace("\n", " "))
    if not years:
        out.append(f"  inizio: {txt[:500]!r}")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--only", help="nomi di regole separati da virgola")
    a = p.parse_args()
    site = json.loads(a.catalog.read_text(encoding="utf-8"))["metrics"]
    cov = json.loads((ROOT / "ci/release-probe-coverage.json").read_text(encoding="utf-8"))
    wanted = set(a.only.split(",")) if a.only else None
    for name, check in cov.get("sourceChecks", {}).items():
        if wanted and name not in wanted:
            continue
        key = next(k for k, v in cov["metrics"].items() if name in v.get("checks", []))
        print("\n".join(survey_check(name, check, site.get(key, {"meta": {}}))), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
