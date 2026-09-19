#!/usr/bin/env python3
"""A3.3 source-by-source audit derived from the strict enrichment matrix.

The report is a disposable/readable view, never a second source inventory.
Source profiles and metric membership are derived from the Effective Public
Catalog through the A3 matrix and enriched only with metadata already present
in data/source-registry.json.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import enrichment_audit_matrix_core as matrix_core

REQUIRED_PROFILE_FIELDS = (
    "publisher",
    "frequency",
    "frequencyLabel",
    "expectedRelease",
    "acquisitionMethod",
    "licenseName",
    "licenseUrl",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _profile_metadata(profile_id: str, registry: dict[str, Any]) -> dict[str, str]:
    profiles = registry.get("sourceProfiles")
    if not isinstance(profiles, dict):
        raise RuntimeError("sourceProfiles assente dal registry")
    profile = profiles.get(profile_id)
    if not isinstance(profile, dict):
        raise RuntimeError(f"Profilo fonte non censito nel registry: {profile_id}")

    metadata: dict[str, str] = {}
    missing: list[str] = []
    for field in REQUIRED_PROFILE_FIELDS:
        value = str(profile.get(field) or "").strip()
        if not value:
            missing.append(field)
        metadata[field] = value
    if missing:
        raise RuntimeError(
            f"Metadati fonte incompleti per {profile_id}: {', '.join(missing)}"
        )
    return metadata


def _pair_view(row: dict[str, Any]) -> dict[str, str]:
    return {
        "metricId": str(row.get("metricId") or ""),
        "dimension": str(row.get("dimension") or ""),
        "evidence": str(row.get("evidence") or ""),
        "sourceReference": str(row.get("sourceReference") or ""),
    }


def build_source_audit(
    matrix: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    matrix_core.validate_matrix(matrix, require_complete=True)

    rows = matrix.get("rows")
    dimensions = matrix.get("dimensions")
    summary = matrix.get("summary")
    if not isinstance(rows, list) or not isinstance(dimensions, list) or not isinstance(summary, dict):
        raise RuntimeError("Matrice A3 non valida per audit fonte")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metric_profile: dict[str, str] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise RuntimeError("Riga A3 non-oggetto")
        metric_id = str(raw.get("metricId") or "").strip()
        profile_id = str(raw.get("sourceProfileId") or "").strip()
        state = str(raw.get("state") or "").strip()
        if not metric_id or not profile_id:
            raise RuntimeError(f"Riga A3 senza metrica/profilo: {raw}")
        if state not in matrix_core.FINAL_STATES:
            raise RuntimeError(
                f"Stato non finale in A3.3: {metric_id}/{raw.get('dimension')} -> {state}"
            )

        previous = metric_profile.setdefault(metric_id, profile_id)
        if previous != profile_id:
            raise RuntimeError(
                f"Metrica risolta su più profili fonte: {metric_id}: {previous} / {profile_id}"
            )
        grouped[profile_id].append(raw)

    profiles_registry = registry.get("sourceProfiles")
    if not isinstance(profiles_registry, dict):
        raise RuntimeError("sourceProfiles assente dal registry")

    profiles_out: list[dict[str, Any]] = []
    global_states: Counter[str] = Counter()
    global_origins: Counter[str] = Counter()

    for profile_id in sorted(grouped):
        profile_rows = grouped[profile_id]
        metadata = _profile_metadata(profile_id, registry)
        metric_ids = sorted({str(row["metricId"]) for row in profile_rows})
        expected_pairs = len(metric_ids) * len(dimensions)
        if len(profile_rows) != expected_pairs:
            raise RuntimeError(
                f"Copertura fonte incoerente {profile_id}: "
                f"{len(profile_rows)} righe != {len(metric_ids)} x {len(dimensions)}"
            )

        states = Counter(str(row.get("state") or "") for row in profile_rows)
        origins = Counter(str(row.get("classificationOrigin") or "") for row in profile_rows)
        if sum(states.values()) != expected_pairs:
            raise RuntimeError(f"Conteggio stati incoerente per {profile_id}")

        dimension_states: dict[str, dict[str, int]] = {}
        for dimension in dimensions:
            drows = [row for row in profile_rows if row.get("dimension") == dimension]
            if len(drows) != len(metric_ids):
                raise RuntimeError(
                    f"Copertura dimensione incoerente {profile_id}/{dimension}: "
                    f"{len(drows)} != {len(metric_ids)}"
                )
            dimension_states[str(dimension)] = dict(
                sorted(Counter(str(row.get("state") or "") for row in drows).items())
            )

        global_states.update(states)
        global_origins.update(origins)
        profiles_out.append(
            {
                "profileId": profile_id,
                **metadata,
                "metricCount": len(metric_ids),
                "pairCount": expected_pairs,
                "metricIds": metric_ids,
                "stateCounts": dict(sorted(states.items())),
                "classificationOriginCounts": dict(sorted(origins.items())),
                "dimensionStates": dimension_states,
                "availableMissing": sorted(
                    (_pair_view(row) for row in profile_rows if row.get("state") == "AVAILABLE_MISSING"),
                    key=lambda item: (item["metricId"], item["dimension"]),
                ),
                "sourceUnavailable": sorted(
                    (_pair_view(row) for row in profile_rows if row.get("state") == "SOURCE_UNAVAILABLE"),
                    key=lambda item: (item["metricId"], item["dimension"]),
                ),
                "notApplicable": sorted(
                    (_pair_view(row) for row in profile_rows if row.get("state") == "NOT_APPLICABLE"),
                    key=lambda item: (item["metricId"], item["dimension"]),
                ),
            }
        )

    matrix_state_counts = {
        state: int(summary.get(f"state_{state}") or 0)
        for state in sorted(matrix_core.FINAL_STATES)
    }
    observed_states = dict(sorted(global_states.items()))
    expected_states = {
        key: value for key, value in sorted(matrix_state_counts.items()) if value
    }
    if observed_states != expected_states:
        raise RuntimeError(
            f"Conteggi stato A3.3 non allineati alla matrice: "
            f"{observed_states} != {expected_states}"
        )

    if len(metric_profile) != int(summary.get("publicMetricCount") or 0):
        raise RuntimeError("Copertura metriche A3.3 non allineata alla matrice")
    if len(profiles_out) != int(summary.get("sourceProfileCount") or 0):
        raise RuntimeError("Copertura profili fonte A3.3 non allineata alla matrice")
    if sum(item["pairCount"] for item in profiles_out) != int(summary.get("pairCount") or 0):
        raise RuntimeError("Copertura coppie A3.3 non allineata alla matrice")

    unused_profiles = sorted(set(profiles_registry) - set(grouped))
    return {
        "schemaVersion": 1,
        "generatedFrom": matrix.get("generatedFrom", {}),
        "summary": {
            "publicMetricCount": len(metric_profile),
            "sourceProfileCount": len(profiles_out),
            "registryProfileCount": len(profiles_registry),
            "unusedRegistryProfileCount": len(unused_profiles),
            "pairCount": len(rows),
            "dimensionCount": len(dimensions),
            "availableMissingPairCount": global_states.get("AVAILABLE_MISSING", 0),
            "sourceUnavailablePairCount": global_states.get("SOURCE_UNAVAILABLE", 0),
            "notApplicablePairCount": global_states.get("NOT_APPLICABLE", 0),
            "acquiredPairCount": global_states.get("ACQUIRED", 0),
            "profilesWithAvailableMissing": sum(
                1 for item in profiles_out if item["availableMissing"]
            ),
            "classificationOriginCounts": dict(sorted(global_origins.items())),
        },
        "unusedRegistryProfiles": unused_profiles,
        "profiles": profiles_out,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# A3.3 — Audit fonte per fonte",
        "",
        "Report derivato dalla matrice A3 strict dell'Effective Public Catalog. "
        "Non e un inventario canonico e non va mantenuto manualmente.",
        "",
        "## Sintesi",
        "",
        f"- Indicatori pubblici: **{summary['publicMetricCount']}**",
        f"- Profili fonte usati: **{summary['sourceProfileCount']}**",
        f"- Coppie indicatore x dimensione: **{summary['pairCount']}**",
        f"- ACQUIRED: **{summary['acquiredPairCount']}**",
        f"- AVAILABLE_MISSING: **{summary['availableMissingPairCount']}**",
        f"- SOURCE_UNAVAILABLE: **{summary['sourceUnavailablePairCount']}**",
        f"- NOT_APPLICABLE: **{summary['notApplicablePairCount']}**",
        "",
        "## Copertura per fonte",
        "",
        "| Profilo | Publisher | Metriche | Coppie | ACQUIRED | AVAILABLE_MISSING | SOURCE_UNAVAILABLE | N/A |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["profiles"]:
        counts = item["stateCounts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    item["profileId"],
                    item["publisher"].replace("|", "\\|"),
                    str(item["metricCount"]),
                    str(item["pairCount"]),
                    str(counts.get("ACQUIRED", 0)),
                    str(counts.get("AVAILABLE_MISSING", 0)),
                    str(counts.get("SOURCE_UNAVAILABLE", 0)),
                    str(counts.get("NOT_APPLICABLE", 0)),
                ]
            )
            + " |"
        )

    for item in payload["profiles"]:
        lines.extend(
            [
                "",
                f"## {item['profileId']}",
                "",
                f"- Publisher: {item['publisher']}",
                f"- Frequenza: {item['frequencyLabel']} ({item['frequency']})",
                f"- Release attesa: {item['expectedRelease']}",
                f"- Metodo acquisizione: {item['acquisitionMethod']}",
                f"- Licenza: {item['licenseName']} — {item['licenseUrl']}",
                "- Origini classificazione: " + ", ".join(
                    f"{key}={value}"
                    for key, value in item["classificationOriginCounts"].items()
                ),
                f"- Metriche: {', '.join(item['metricIds'])}",
                f"- Coppie: {item['pairCount']}",
            ]
        )
        for title, key in (
            ("AVAILABLE_MISSING", "availableMissing"),
            ("SOURCE_UNAVAILABLE", "sourceUnavailable"),
            ("NOT_APPLICABLE", "notApplicable"),
        ):
            entries = item[key]
            lines.append(f"- {title}: {len(entries)}")
            for entry in entries:
                reference = (
                    f" — {entry['sourceReference']}"
                    if entry["sourceReference"]
                    else ""
                )
                lines.append(
                    f"  - {entry['metricId']} x {entry['dimension']}{reference}"
                )
    return "\n".join(lines) + "\n"


def write_source_audit(
    matrix_path: Path,
    registry_path: Path,
    json_output: Path | None,
    markdown_output: Path | None,
) -> dict[str, Any]:
    payload = build_source_audit(load(matrix_path), load(registry_path))
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if markdown_output is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = write_source_audit(
        args.matrix,
        args.registry,
        args.json_output,
        args.markdown_output,
    )
    summary = payload["summary"]
    print(
        "A3.3 source audit: "
        f"{summary['sourceProfileCount']} profili fonte · "
        f"{summary['publicMetricCount']} indicatori · "
        f"{summary['pairCount']} coppie · "
        f"{summary['availableMissingPairCount']} AVAILABLE_MISSING."
    )
    for item in payload["profiles"]:
        counts = item["stateCounts"]
        print(
            "A3_SOURCE "
            f"{item['profileId']} :: {item['metricCount']} metriche :: "
            f"A={counts.get('ACQUIRED', 0)} "
            f"M={counts.get('AVAILABLE_MISSING', 0)} "
            f"U={counts.get('SOURCE_UNAVAILABLE', 0)} "
            f"N={counts.get('NOT_APPLICABLE', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
