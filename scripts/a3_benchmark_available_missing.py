#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DIMENSION = "benchmark_toscana_italia"
BASELINE_AVAILABLE_MISSING = 182


def build_report(matrix: dict) -> dict:
    rows = [
        row for row in matrix.get("rows", [])
        if row.get("dimension") == DIMENSION and row.get("state") == "AVAILABLE_MISSING"
    ]
    rows.sort(key=lambda row: ((row.get("sourceProfileId") or ""), row.get("metricId") or ""))
    profiles = defaultdict(list)
    for row in rows:
        profiles[row.get("sourceProfileId") or "unprofiled"].append(row)

    return {
        "schemaVersion": 1,
        "dimension": DIMENSION,
        "baselineAvailableMissing": BASELINE_AVAILABLE_MISSING,
        "summary": {
            "availableMissing": len(rows),
            "closedSinceBaseline": BASELINE_AVAILABLE_MISSING - len(rows),
            "sourceProfiles": len(profiles),
            "classificationOrigins": dict(sorted(Counter(
                row.get("classificationOrigin") or "unknown" for row in rows
            ).items())),
        },
        "profiles": [
            {
                "sourceProfileId": profile,
                "count": len(items),
                "pairs": [
                    {
                        "metricId": row.get("metricId"),
                        "sourceUrl": row.get("sourceUrl"),
                        "sourceReference": row.get("sourceReference"),
                        "evidence": row.get("evidence"),
                        "classificationOrigin": row.get("classificationOrigin"),
                    }
                    for row in items
                ],
            }
            for profile, items in sorted(profiles.items(), key=lambda item: (-len(item[1]), item[0]))
        ],
    }


def markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# A3 Toscana/Italia benchmark AVAILABLE_MISSING workstream",
        "",
        f"- Dimension: \`{DIMENSION}\`",
        f"- Baseline backlog: **{report['baselineAvailableMissing']}** pairs",
        f"- Current backlog: **{summary['availableMissing']}** pairs",
        f"- Closed since baseline: **{summary['closedSinceBaseline']}** pairs",
        f"- Source profiles involved: **{summary['sourceProfiles']}**",
        "",
        "The list below is derived from the A3 effective matrix. It is not a hand-maintained indicator inventory.",
        "",
    ]
    for bundle in report["profiles"]:
        lines.extend([
            f"## {bundle['sourceProfileId']} · {bundle['count']}",
            "",
        ])
        for pair in bundle["pairs"]:
            ref = pair.get("sourceReference") or pair.get("sourceUrl") or "-"
            lines.append(f"- \`{pair['metricId']}\` — {ref}")
            if pair.get("evidence"):
                lines.append(f"  - Evidence: {pair['evidence']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()

    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    report = build_report(matrix)
    current = report["summary"]["availableMissing"]
    if current > BASELINE_AVAILABLE_MISSING:
        raise SystemExit(
            f"Benchmark AVAILABLE_MISSING backlog grew: {current} > {BASELINE_AVAILABLE_MISSING}"
        )
    Path(args.json_output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(markdown(report), encoding="utf-8")
    print(
        f"A3 benchmark workstream: {current} AVAILABLE_MISSING across "
        f"{report['summary']['sourceProfiles']} source profiles; "
        f"{report['summary']['closedSinceBaseline']} closed since baseline."
    )


if __name__ == "__main__":
    main()
