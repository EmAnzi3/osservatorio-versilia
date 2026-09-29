#!/usr/bin/env python3
"""Confronta semanticamente lo snapshot shadow con lo stato pubblicato.

Il confronto riusa lo stesso matching del rapporto giornaliero e ignora i
campi volatili del refresh. Una divergenza non blocca lo shadow run: puo essere
una nuova opportunita reale e deve essere resa leggibile, non nascosta dietro
un diff byte-per-byte.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from opportunity_run_report import build_report, render_markdown


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Snapshot non valido: {path}")
    return payload


def compare_snapshots(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    report = build_report(
        reference,
        candidate,
        phase_statuses={"scan": "success", "validation": "success", "build": "success"},
    )
    counts = report["counts"]
    changed = any(int(counts[key]) > 0 for key in ("added", "modified", "archived", "removed"))
    return {
        "schemaVersion": 1,
        "equivalent": not changed,
        "referenceDate": reference.get("referenceDate"),
        "candidateDate": candidate.get("referenceDate"),
        "referenceCount": len(reference.get("opportunities") or []),
        "candidateCount": len(candidate.get("opportunities") or []),
        "fingerprint": report["fingerprint"],
        "counts": {
            key: int(counts[key])
            for key in ("added", "modified", "archived", "removed", "unchanged")
        },
        "report": report,
    }


def render_comparison(result: dict[str, Any]) -> str:
    status = "EQUIVALENTE" if result["equivalent"] else "DIVERGENTE DA ESAMINARE"
    counts = result["counts"]
    lines = [
        "# Radar v2 shadow · confronto snapshot",
        "",
        f"**Esito semantico: {status}**",
        "",
        f"Stato verificato: **{result.get('referenceDate') or 'n.d.'}** · "
        f"candidato shadow: **{result.get('candidateDate') or 'n.d.'}**",
        "",
        "| Stato verificato | Candidato | Nuove | Modificate | Archiviate | Rimosse | Invariate |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| {result['referenceCount']} | {result['candidateCount']} | "
            f"{counts['added']} | {counts['modified']} | {counts['archived']} | "
            f"{counts['removed']} | {counts['unchanged']} |"
        ),
        "",
        "La divergenza non viene trattata automaticamente come errore: puo rappresentare "
        "un cambiamento reale intercettato dopo l'ultimo stato produttivo.",
        "",
        "---",
        "",
        render_markdown(result["report"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expect-equivalent", action="store_true")
    args = parser.parse_args()

    result = compare_snapshots(_load(args.reference), _load(args.candidate))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "opportunity-shadow-comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "opportunity-shadow-comparison.md").write_text(
        render_comparison(result),
        encoding="utf-8",
    )
    print(
        "Confronto Radar shadow: "
        + ("equivalente" if result["equivalent"] else "divergente")
        + f" · fingerprint {result['fingerprint']}"
    )
    return 1 if args.expect_equivalent and not result["equivalent"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
