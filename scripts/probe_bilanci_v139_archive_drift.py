#!/usr/bin/env python3
"""Verifica il drift degli ZIP OpenBDAP senza accettarlo implicitamente.

Confronta SHA del contenitore e, soprattutto, dei due CSV usati da v1.39
(spese per missione e Allegato A risultato di amministrazione) con gli SHA
congelati nella baseline v1.6.0. Il processo fallisce se cambia un CSV target.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/source-snapshots/bilanci-v1.6.0.json"
MISSION_SUFFIX = "Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv"
RESULT_SUFFIX = "Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv"
TIMEOUT = 240


def member_digest(archive: zipfile.ZipFile, suffix: str) -> tuple[str, int, str]:
    hits = [info for info in archive.infolist() if info.filename.endswith(suffix)]
    if len(hits) != 1:
        raise RuntimeError(f"{suffix}: atteso un file, trovati {len(hits)}")
    raw = archive.read(hits[0])
    return hashlib.sha256(raw).hexdigest(), len(raw), hits[0].filename


def main() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers["User-Agent"] = "OsservatorioVersilia/1.39-archive-drift-probe"
    report = {"years": {}, "hard_failures": []}

    for year in sorted(baseline["source"]["years"]):
        meta = baseline["source"]["years"][year]
        scheme = meta["schemi"]
        response = session.get(scheme["url"], timeout=TIMEOUT)
        response.raise_for_status()
        raw = response.content
        container_sha = hashlib.sha256(raw).hexdigest()

        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            mission_sha, mission_bytes, mission_name = member_digest(archive, MISSION_SUFFIX)
            result_sha, result_bytes, result_name = member_digest(archive, RESULT_SUFFIX)

        expected_mission = meta["selected_files"]["spese_missioni"]["sha256"]
        expected_result = meta["selected_files"]["risultato"]["sha256"]
        target_match = mission_sha == expected_mission and result_sha == expected_result
        container_match = container_sha == scheme["sha256"]
        report["years"][year] = {
            "container": {
                "current_sha256": container_sha,
                "baseline_sha256": scheme["sha256"],
                "match": container_match,
            },
            "spese_missioni": {
                "name": mission_name,
                "bytes": mission_bytes,
                "current_sha256": mission_sha,
                "baseline_sha256": expected_mission,
                "match": mission_sha == expected_mission,
            },
            "risultato": {
                "name": result_name,
                "bytes": result_bytes,
                "current_sha256": result_sha,
                "baseline_sha256": expected_result,
                "match": result_sha == expected_result,
            },
            "classification": "identical" if container_match else ("container-only-drift" if target_match else "target-data-drift"),
        }
        if not target_match:
            report["hard_failures"].append(year)

    out = ROOT / "reports/bilanci-v139-archive-drift.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["hard_failures"]:
        print("Target OpenBDAP changed for years: " + ", ".join(report["hard_failures"]), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
