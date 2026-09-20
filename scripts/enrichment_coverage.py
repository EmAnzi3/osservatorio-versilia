#!/usr/bin/env python3
"""A3.6 — copertura enrichment derivata dalla matrice A3.

Misura quanta parte delle opportunità ufficialmente acquisibili è già
materializzata: ACQUIRED / (ACQUIRED + AVAILABLE_MISSING).
SOURCE_UNAVAILABLE e NOT_APPLICABLE non entrano nel denominatore.

Non è un voto di qualità del prodotto e non ha un target implicito del 100%.
Il residuo AVAILABLE_MISSING resta il backlog governato A3.4.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

VALID_STATES = {"ACQUIRED", "AVAILABLE_MISSING", "SOURCE_UNAVAILABLE", "NOT_APPLICABLE"}
ELIGIBLE_STATES = {"ACQUIRED", "AVAILABLE_MISSING"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _coverage(counts: Counter[str]) -> dict[str, Any]:
    acquired = int(counts["ACQUIRED"])
    missing = int(counts["AVAILABLE_MISSING"])
    eligible = acquired + missing
    ratio = acquired / eligible if eligible else None
    return {
        "acquiredPairCount": acquired,
        "availableMissingPairCount": missing,
        "eligiblePairCount": eligible,
        "coverageRatio": ratio,
        "coveragePercent": None if ratio is None else ratio * 100.0,
        "sourceUnavailablePairCount": int(counts["SOURCE_UNAVAILABLE"]),
        "notApplicablePairCount": int(counts["NOT_APPLICABLE"]),
        "totalPairCount": sum(int(counts[state]) for state in VALID_STATES),
    }


def build_coverage(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix.get("rows")
    summary = matrix.get("summary")
    if not isinstance(rows, list) or not isinstance(summary, dict):
        raise RuntimeError("Matrice A3 non valida")

    expected_pairs = int(summary.get("pairCount", -1))
    if len(rows) != expected_pairs:
        raise RuntimeError(f"Matrice A3 incompleta: rows={len(rows)} pairCount={expected_pairs}")

    global_counts: Counter[str] = Counter()
    dimension_counts: dict[str, Counter[str]] = defaultdict(Counter)
    profile_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"Riga A3 non-oggetto: {index}")
        state = row.get("state")
        if state not in VALID_STATES:
            raise RuntimeError(f"Stato A3 non valido/non classificato alla riga {index}: {state!r}")
        dimension = row.get("dimension")
        profile = row.get("sourceProfileId")
        if not isinstance(dimension, str) or not dimension:
            raise RuntimeError(f"Dimensione A3 mancante alla riga {index}")
        if not isinstance(profile, str) or not profile:
            raise RuntimeError(f"Source profile A3 mancante alla riga {index}")
        global_counts[state] += 1
        dimension_counts[dimension][state] += 1
        profile_counts[profile][state] += 1

    global_summary = _coverage(global_counts)
    if global_summary["totalPairCount"] != expected_pairs:
        raise RuntimeError("Conteggio globale A3 non riconciliato")

    dimensions = [
        {"dimension": key, **_coverage(counts)}
        for key, counts in sorted(dimension_counts.items())
    ]
    profiles = [
        {"sourceProfileId": key, **_coverage(counts)}
        for key, counts in sorted(profile_counts.items())
    ]

    dimensions.sort(
        key=lambda item: (
            item["coverageRatio"] is None,
            item["coverageRatio"] if item["coverageRatio"] is not None else 1.0,
            item["dimension"],
        )
    )
    profiles.sort(
        key=lambda item: (
            -item["availableMissingPairCount"],
            item["coverageRatio"] if item["coverageRatio"] is not None else 1.0,
            item["sourceProfileId"],
        )
    )

    return {
        "schemaVersion": 1,
        "definition": {
            "name": "A3 enrichment acquisition coverage",
            "formula": "ACQUIRED / (ACQUIRED + AVAILABLE_MISSING)",
            "eligibleStates": sorted(ELIGIBLE_STATES),
            "excludedStates": ["SOURCE_UNAVAILABLE", "NOT_APPLICABLE"],
            "interpretation": (
                "Quota delle opportunità di enrichment che la matrice A3 considera "
                "ufficialmente disponibili e che sono già materializzate nella pipeline."
            ),
            "caveat": (
                "Non è un voto di qualità e non implica un obiettivo del 100%. "
                "Le opportunità residue restano nel backlog A3.4 e possono essere "
                "sviluppate in futuri lotti di prodotto senza bloccare il consolidamento."
            ),
        },
        "summary": {
            "publicMetricCount": int(summary["publicMetricCount"]),
            "sourceProfileCount": int(summary["sourceProfileCount"]),
            "dimensionCount": int(summary["dimensionCount"]),
            "classifiedPairCount": int(summary["classifiedPairCount"]),
            "unclassifiedPairCount": int(summary["unclassifiedPairCount"]),
            **global_summary,
        },
        "dimensions": dimensions,
        "sourceProfiles": profiles,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    definition = report["definition"]
    pct = summary["coveragePercent"]
    lines = [
        "# A3.6 — Copertura enrichment",
        "",
        f"Formula: {definition['formula']}",
        "",
        (
            f"Copertura globale: {summary['acquiredPairCount']} / "
            f"{summary['eligiblePairCount']} opportunità acquisibili"
            + (f" = {pct:.1f}%" if pct is not None else "")
        ),
        "",
        f"- AVAILABLE_MISSING: {summary['availableMissingPairCount']}",
        f"- SOURCE_UNAVAILABLE: {summary['sourceUnavailablePairCount']}",
        f"- NOT_APPLICABLE: {summary['notApplicablePairCount']}",
        f"- coppie classificate: {summary['classifiedPairCount']} / {summary['totalPairCount']}",
        "",
        f"> {definition['caveat']}",
        "",
        "## Per dimensione",
        "",
        "| Dimensione | Acquisite | Mancanti disponibili | Copertura |",
        "|---|---:|---:|---:|",
    ]
    for item in report["dimensions"]:
        ratio = item["coveragePercent"]
        text = "n.d." if ratio is None else f"{ratio:.1f}%"
        lines.append(
            f"| {item['dimension']} | {item['acquiredPairCount']} | "
            f"{item['availableMissingPairCount']} | {text} |"
        )

    lines.extend([
        "",
        "## Profili con più opportunità residue",
        "",
        "| Profilo fonte | Acquisite | Mancanti disponibili | Copertura |",
        "|---|---:|---:|---:|",
    ])
    for item in report["sourceProfiles"]:
        if item["availableMissingPairCount"] <= 0:
            continue
        ratio = item["coveragePercent"]
        text = "n.d." if ratio is None else f"{ratio:.1f}%"
        lines.append(
            f"| {item['sourceProfileId']} | {item['acquiredPairCount']} | "
            f"{item['availableMissingPairCount']} | {text} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args(argv)

    report = build_coverage(load(args.matrix))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")

    s = report["summary"]
    print(
        "A3.6 enrichment coverage: "
        f"{s['acquiredPairCount']}/{s['eligiblePairCount']} = "
        f"{s['coveragePercent']:.1f}% · "
        f"{s['availableMissingPairCount']} AVAILABLE_MISSING · "
        f"{s['classifiedPairCount']}/{s['totalPairCount']} classified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
