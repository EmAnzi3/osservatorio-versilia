#!/usr/bin/env python3
"""A3.4 enrichment backlog derived from the strict A3 matrix and A3.3 audit."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import enrichment_audit_matrix_core as matrix_core

MODEL_VERSION = 1

DIMENSION_VALUE = {
    "serie_storica": 5,
    "dettaglio_territoriale": 5,
    "benchmark_toscana_italia": 5,
    "numeratore_denominatore": 5,
    "sesso": 4,
    "eta": 4,
    "assoluto_normalizzato": 4,
    "frequenza_infra_annuale": 3,
    "categorie_specifiche": 3,
}

COST_LABELS = {
    1: "molto_basso",
    2: "basso",
    3: "medio",
    4: "alto",
    5: "molto_alto",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _pair_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("sourceProfileId") or "").strip(),
        str(row.get("metricId") or "").strip(),
        str(row.get("dimension") or "").strip(),
    )


def _source_audit_available_pairs(source_audit: dict[str, Any]) -> set[tuple[str, str, str]]:
    pairs: set[tuple[str, str, str]] = set()
    profiles = source_audit.get("profiles")
    if not isinstance(profiles, list):
        raise RuntimeError("A3.3 source audit senza profiles")
    for profile in profiles:
        if not isinstance(profile, dict):
            raise RuntimeError("Profilo A3.3 non-oggetto")
        profile_id = str(profile.get("profileId") or "").strip()
        if not profile_id:
            raise RuntimeError("Profilo A3.3 senza profileId")
        entries = profile.get("availableMissing")
        if not isinstance(entries, list):
            raise RuntimeError(f"A3.3 {profile_id} senza availableMissing")
        for entry in entries:
            if not isinstance(entry, dict):
                raise RuntimeError(f"A3.3 {profile_id}: availableMissing non-oggetto")
            key = (
                profile_id,
                str(entry.get("metricId") or "").strip(),
                str(entry.get("dimension") or "").strip(),
            )
            if not all(key):
                raise RuntimeError(f"A3.3 availableMissing incompleto: {profile_id}: {entry}")
            if key in pairs:
                raise RuntimeError(f"Coppia A3.3 duplicata: {key}")
            pairs.add(key)
    return pairs


def _profile_map(source_audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles = source_audit.get("profiles")
    if not isinstance(profiles, list):
        raise RuntimeError("A3.3 source audit senza profiles")
    out: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            raise RuntimeError("Profilo A3.3 non-oggetto")
        profile_id = str(profile.get("profileId") or "").strip()
        if not profile_id:
            raise RuntimeError("Profilo A3.3 senza profileId")
        if profile_id in out:
            raise RuntimeError(f"Profilo A3.3 duplicato: {profile_id}")
        out[profile_id] = profile
    return out


def _estimate_cost(
    *,
    available_rows: list[dict[str, Any]],
    same_dimension_rows: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    cost = 3
    signals: list[str] = []

    acquired_same_dimension = sum(
        1 for row in same_dimension_rows if row.get("state") == "ACQUIRED"
    )
    if acquired_same_dimension:
        cost -= 1
        signals.append("riuso_dimensione_gia_acquisita_nel_profilo")

    origins = {
        str(row.get("classificationOrigin") or "").strip()
        for row in available_rows
    }
    origins.discard("")
    if origins == {"source_profile"}:
        cost -= 1
        signals.append("evidenza_disponibilita_valida_per_intero_profilo")
    elif "metric_override" in origins:
        cost += 1
        signals.append("evidenza_metric_specific")

    references = {
        str(row.get("sourceReference") or "").strip()
        for row in available_rows
        if str(row.get("sourceReference") or "").strip()
    }
    if len(references) > 1:
        cost += 1
        signals.append("riferimenti_fonte_multipli")

    cost = max(1, min(5, cost))
    if not signals:
        signals.append("costo_base_senza_segnali_di_riuso_o_complessita")
    return cost, signals


def build_backlog(
    matrix: dict[str, Any],
    source_audit: dict[str, Any],
) -> dict[str, Any]:
    matrix_core.validate_matrix(matrix, require_complete=True)

    rows = matrix.get("rows")
    summary = matrix.get("summary")
    dimensions = matrix.get("dimensions")
    if not isinstance(rows, list) or not isinstance(summary, dict) or not isinstance(dimensions, list):
        raise RuntimeError("Matrice A3 non valida per A3.4")

    missing_weights = sorted(set(str(d) for d in dimensions) - set(DIMENSION_VALUE))
    extra_weights = sorted(set(DIMENSION_VALUE) - set(str(d) for d in dimensions))
    if missing_weights or extra_weights:
        raise RuntimeError(
            "Pesi A3.4 non allineati alla tassonomia A3: "
            f"missing={missing_weights} extra={extra_weights}"
        )

    source_summary = source_audit.get("summary")
    if not isinstance(source_summary, dict):
        raise RuntimeError("A3.3 source audit senza summary")

    expected_missing = int(summary.get("state_AVAILABLE_MISSING") or 0)
    if int(source_summary.get("availableMissingPairCount") or 0) != expected_missing:
        raise RuntimeError(
            "A3.3/A3.4 non allineati sugli AVAILABLE_MISSING: "
            f"{source_summary.get('availableMissingPairCount')} != {expected_missing}"
        )

    available_rows = [
        row for row in rows
        if isinstance(row, dict) and row.get("state") == "AVAILABLE_MISSING"
    ]
    if len(available_rows) != expected_missing:
        raise RuntimeError(
            f"Matrice A3: {len(available_rows)} AVAILABLE_MISSING != {expected_missing}"
        )

    matrix_pairs: set[tuple[str, str, str]] = set()
    for row in available_rows:
        key = _pair_key(row)
        if not all(key):
            raise RuntimeError(f"AVAILABLE_MISSING incompleto: {row}")
        if key in matrix_pairs:
            raise RuntimeError(f"AVAILABLE_MISSING duplicato: {key}")
        if not str(row.get("sourceReference") or "").strip():
            raise RuntimeError(f"AVAILABLE_MISSING senza sourceReference: {key}")
        matrix_pairs.add(key)

    audit_pairs = _source_audit_available_pairs(source_audit)
    if audit_pairs != matrix_pairs:
        missing = sorted(matrix_pairs - audit_pairs)[:10]
        extra = sorted(audit_pairs - matrix_pairs)[:10]
        raise RuntimeError(
            "A3.3/A3.4 divergenza sulle coppie AVAILABLE_MISSING: "
            f"missing={missing} extra={extra}"
        )

    profiles = _profile_map(source_audit)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_by_profile_dimension: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for raw in rows:
        if not isinstance(raw, dict):
            continue
        profile_id = str(raw.get("sourceProfileId") or "").strip()
        dimension = str(raw.get("dimension") or "").strip()
        if profile_id and dimension:
            all_by_profile_dimension[(profile_id, dimension)].append(raw)

    for row in available_rows:
        grouped[
            (
                str(row["sourceProfileId"]),
                str(row["dimension"]),
            )
        ].append(row)

    bundles: list[dict[str, Any]] = []
    for (profile_id, dimension), bundle_rows in grouped.items():
        profile = profiles.get(profile_id)
        if profile is None:
            raise RuntimeError(f"Profilo A3.3 assente per backlog: {profile_id}")

        same_dimension_rows = all_by_profile_dimension[(profile_id, dimension)]
        cost_points, cost_signals = _estimate_cost(
            available_rows=bundle_rows,
            same_dimension_rows=same_dimension_rows,
        )
        pair_count = len(bundle_rows)
        value_per_pair = DIMENSION_VALUE[dimension]
        information_value = value_per_pair * pair_count
        priority_index = information_value / cost_points
        origins = Counter(
            str(row.get("classificationOrigin") or "")
            for row in bundle_rows
        )
        references = sorted(
            {
                str(row.get("sourceReference") or "").strip()
                for row in bundle_rows
                if str(row.get("sourceReference") or "").strip()
            }
        )
        metrics = sorted({str(row.get("metricId") or "") for row in bundle_rows})
        if len(metrics) != pair_count:
            raise RuntimeError(
                f"Bundle con metrica duplicata {profile_id}/{dimension}: "
                f"{len(metrics)} != {pair_count}"
            )

        bundles.append(
            {
                "bundleId": f"{profile_id}::{dimension}",
                "profileId": profile_id,
                "publisher": str(profile.get("publisher") or ""),
                "dimension": dimension,
                "metricCount": len(metrics),
                "pairCount": pair_count,
                "metricIds": metrics,
                "sourceReferences": references,
                "classificationOriginCounts": dict(sorted(origins.items())),
                "acquiredSameDimensionCount": sum(
                    1 for row in same_dimension_rows if row.get("state") == "ACQUIRED"
                ),
                "informationValuePerPair": value_per_pair,
                "informationValuePoints": information_value,
                "costPoints": cost_points,
                "costLabel": COST_LABELS[cost_points],
                "costSignals": cost_signals,
                "priorityIndex": round(priority_index, 6),
                "pairs": sorted(
                    [
                        {
                            "metricId": str(row.get("metricId") or ""),
                            "dimension": dimension,
                            "evidence": str(row.get("evidence") or ""),
                            "sourceReference": str(row.get("sourceReference") or ""),
                            "classificationOrigin": str(row.get("classificationOrigin") or ""),
                        }
                        for row in bundle_rows
                    ],
                    key=lambda item: item["metricId"],
                ),
            }
        )

    bundles.sort(
        key=lambda item: (
            -float(item["priorityIndex"]),
            -int(item["informationValuePoints"]),
            int(item["costPoints"]),
            -int(item["pairCount"]),
            str(item["profileId"]),
            str(item["dimension"]),
        )
    )
    for index, item in enumerate(bundles, start=1):
        item["rank"] = index

    covered_pairs = {
        (
            item["profileId"],
            pair["metricId"],
            item["dimension"],
        )
        for item in bundles
        for pair in item["pairs"]
    }
    if covered_pairs != matrix_pairs:
        raise RuntimeError("Backlog A3.4 non copre esattamente tutti gli AVAILABLE_MISSING")

    return {
        "schemaVersion": 1,
        "priorityModelVersion": MODEL_VERSION,
        "generatedFrom": matrix.get("generatedFrom", {}),
        "rubric": {
            "dimensionValue": dict(DIMENSION_VALUE),
            "costScale": dict(COST_LABELS),
            "formula": "priorityIndex = (informationValuePerPair * pairCount) / costPoints",
            "costSignals": {
                "reuseSameDimension": "-1 se il profilo ha almeno una coppia ACQUIRED sulla stessa dimensione",
                "sourceProfileEvidence": "-1 se tutte le opportunita del bundle derivano da evidenza source_profile",
                "metricSpecificEvidence": "+1 se almeno una opportunita deriva da metric_override",
                "multipleReferences": "+1 se il bundle richiede piu sourceReference distinti",
                "bounds": "costPoints limitato a 1..5",
            },
        },
        "summary": {
            "publicMetricCount": int(summary.get("publicMetricCount") or 0),
            "sourceProfileCount": int(summary.get("sourceProfileCount") or 0),
            "availableMissingPairCount": expected_missing,
            "bundleCount": len(bundles),
            "dimensionCount": len(dimensions),
            "profilesWithBacklog": len({item["profileId"] for item in bundles}),
        },
        "bundles": bundles,
    }


def validate_backlog(
    backlog: dict[str, Any],
    matrix: dict[str, Any],
    source_audit: dict[str, Any],
) -> None:
    rebuilt = build_backlog(matrix, source_audit)
    if backlog != rebuilt:
        raise RuntimeError("Backlog A3.4 non riproducibile dal modello dichiarato")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rubric = payload["rubric"]
    lines = [
        "# A3.4 — Backlog enrichment",
        "",
        "Backlog derivato dagli AVAILABLE_MISSING della matrice A3 strict e dall'audit A3.3. "
        "Non e un inventario canonico e non va mantenuto manualmente.",
        "",
        "## Sintesi",
        "",
        f"- Coppie AVAILABLE_MISSING: **{summary['availableMissingPairCount']}**",
        f"- Pacchetti fonte x dimensione: **{summary['bundleCount']}**",
        f"- Profili fonte con backlog: **{summary['profilesWithBacklog']}**",
        "",
        "## Modello di priorita",
        "",
        f"- Formula: {rubric['formula']}",
        "- Il valore informativo per coppia e una policy A3.4 esplicita, non un fatto della fonte.",
        "- Il costo e un proxy deterministico 1..5 basato esclusivamente su segnali gia presenti nella matrice/audit.",
        "- Nessun tempo di sviluppo o costo economico viene stimato.",
        "",
        "### Valore informativo per dimensione",
        "",
        "| Dimensione | Valore |",
        "| --- | ---: |",
    ]
    for dimension, value in DIMENSION_VALUE.items():
        lines.append(f"| {dimension} | {value} |")

    lines.extend(
        [
            "",
            "## Backlog ordinato",
            "",
            "| Rank | Profilo | Dimensione | Coppie | Valore | Costo | Indice |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["bundles"]:
        lines.append(
            f"| {item['rank']} | {item['profileId']} | {item['dimension']} | "
            f"{item['pairCount']} | {item['informationValuePoints']} | "
            f"{item['costPoints']} ({item['costLabel']}) | {item['priorityIndex']:.3f} |"
        )

    lines.extend(["", "## Dettaglio pacchetti", ""])
    for item in payload["bundles"]:
        lines.extend(
            [
                f"### #{item['rank']} — {item['profileId']} x {item['dimension']}",
                "",
                f"- Publisher: {item['publisher']}",
                f"- Coppie: {item['pairCount']}",
                f"- Valore informativo: {item['informationValuePoints']}",
                f"- Costo proxy: {item['costPoints']} ({item['costLabel']})",
                f"- Indice priorita: {item['priorityIndex']:.3f}",
                f"- Segnali costo: {', '.join(item['costSignals'])}",
                f"- Metriche: {', '.join(item['metricIds'])}",
                f"- Riferimenti: {', '.join(item['sourceReferences'])}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def write_backlog(
    matrix_path: Path,
    source_audit_path: Path,
    json_output: Path | None,
    markdown_output: Path | None,
) -> dict[str, Any]:
    matrix = load(matrix_path)
    source_audit = load(source_audit_path)
    payload = build_backlog(matrix, source_audit)
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
    parser.add_argument("--source-audit", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = write_backlog(
        args.matrix,
        args.source_audit,
        args.json_output,
        args.markdown_output,
    )
    summary = payload["summary"]
    top = payload["bundles"][:5]
    print(
        "A3.4 enrichment backlog: "
        f"{summary['availableMissingPairCount']} coppie -> "
        f"{summary['bundleCount']} pacchetti su "
        f"{summary['profilesWithBacklog']} profili."
    )
    for item in top:
        print(
            "A3_BACKLOG "
            f"#{item['rank']} {item['profileId']} :: {item['dimension']} :: "
            f"{item['pairCount']} coppie :: value={item['informationValuePoints']} "
            f"cost={item['costPoints']} priority={item['priorityIndex']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
