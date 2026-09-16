#!/usr/bin/env python3
"""Derived A3 enrichment classification matrix.

The public metric inventory is always read from the Effective Public Catalog.
This module does not introduce a second canonical list of metrics. It combines
structured acquisition evidence with optional source-profile / metric evidence
stored in the existing source registry.

Only the four final states defined by A3.1 are accepted. A row with ``state``
set to ``None`` is an operationally unclassified pair, not a fifth state; strict
validation rejects such rows before A3.2 can be declared complete.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from source_policy import resolve_metric_policy

DIMENSIONS = (
    "serie_storica",
    "sesso",
    "eta",
    "dettaglio_territoriale",
    "benchmark_toscana_italia",
    "assoluto_normalizzato",
    "frequenza_infra_annuale",
    "numeratore_denominatore",
    "categorie_specifiche",
)
FINAL_STATES = frozenset(
    {"ACQUIRED", "AVAILABLE_MISSING", "SOURCE_UNAVAILABLE", "NOT_APPLICABLE"}
)
PROFILE_ALLOWED_STATES = frozenset({"AVAILABLE_MISSING", "SOURCE_UNAVAILABLE"})
METRIC_ALLOWED_STATES = frozenset(
    {"AVAILABLE_MISSING", "SOURCE_UNAVAILABLE", "NOT_APPLICABLE"}
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _path_text(path: tuple[str, ...]) -> str:
    return ".".join(path) or "$"


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, (*path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, (*path, str(index)))


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _key_matches(path: tuple[str, ...], tokens: set[str]) -> bool:
    if not path:
        return False
    key = _norm(path[-1])
    return any(token == key or token in key for token in tokens)


def _find_key(metric: dict[str, Any], tokens: set[str]) -> str | None:
    for path, value in _walk(metric):
        if _key_matches(path, tokens) and _has_value(value):
            return _path_text(path)
    return None


def _find_series(metric: dict[str, Any]) -> str | None:
    series_tokens = {"series", "serie", "history", "historical", "storico", "trend"}
    period_tokens = {"year", "anno", "period", "periodo", "date", "data"}
    for path, value in _walk(metric):
        if not isinstance(value, list) or len(value) < 2:
            continue
        if _key_matches(path, series_tokens):
            return _path_text(path)
        if all(isinstance(item, dict) for item in value):
            periods: set[str] = set()
            for item in value:
                assert isinstance(item, dict)
                for key, candidate in item.items():
                    normalized = _norm(key)
                    if any(token == normalized or token in normalized for token in period_tokens):
                        if _has_value(candidate):
                            periods.add(str(candidate))
            if len(periods) >= 2:
                return _path_text(path)
    return None


def _find_labeled_dimension(metric: dict[str, Any], tokens: set[str]) -> str | None:
    key_hit = _find_key(metric, tokens)
    if key_hit:
        return key_hit
    label_keys = {
        "dimension",
        "dimensions",
        "category",
        "categories",
        "group",
        "groups",
        "label",
        "labels",
        "scope",
        "geography",
        "territory",
        "breakdown",
    }
    for path, value in _walk(metric):
        if not path or not isinstance(value, str):
            continue
        parent = _norm(path[-1])
        if parent not in label_keys:
            continue
        normalized = _norm(value)
        if any(token in normalized for token in tokens):
            return _path_text(path)
    return None


def _find_benchmark(metric: dict[str, Any]) -> str | None:
    geography_tokens = {"toscana", "italia", "italy", "nazionale", "national", "regionale"}
    for path, value in _walk(metric):
        if not _has_value(value):
            continue
        key = _norm(path[-1]) if path else ""
        if any(token in key for token in geography_tokens):
            return _path_text(path)
        if "benchmark" in key or "reference" in key or "riferimento" in key:
            if isinstance(value, dict):
                flattened = " ".join(_norm(item) for item in value.keys())
                if any(token in flattened for token in geography_tokens):
                    return _path_text(path)
            elif isinstance(value, str):
                normalized = _norm(value)
                if any(token in normalized for token in geography_tokens):
                    return _path_text(path)
    return None


def _find_territorial_detail(metric: dict[str, Any]) -> str | None:
    tokens = {
        "frazione",
        "sezione",
        "quartiere",
        "provincia",
        "province",
        "area_vasta",
        "regione",
        "region",
        "toscana",
        "italia",
        "italy",
        "national",
        "nazionale",
    }
    return _find_labeled_dimension(metric, tokens)


def _find_absolute_normalized(metric: dict[str, Any]) -> str | None:
    absolute_tokens = {
        "absolute",
        "assoluto",
        "count",
        "conteggio",
        "numero",
        "totale",
        "households",
        "famiglie",
        "population",
        "popolazione",
    }
    normalized_tokens = {
        "normalized",
        "normalizzato",
        "per_capita",
        "percapita",
        "rate",
        "tasso",
        "percent",
        "percentage",
        "quota",
        "per_1000",
        "per_10000",
        "per_100000",
    }
    absolute = _find_key(metric, absolute_tokens)
    normalized = _find_key(metric, normalized_tokens)
    if absolute and normalized and absolute != normalized:
        return f"{absolute} + {normalized}"
    return None


def _find_infra_annual(metric: dict[str, Any]) -> str | None:
    tokens = {
        "monthly",
        "mensile",
        "month",
        "mese",
        "quarter",
        "quarterly",
        "trimestre",
        "trimestrale",
        "semester",
        "semestrale",
    }
    direct = _find_labeled_dimension(metric, tokens)
    if direct:
        return direct
    period_pattern = re.compile(r"^(?:20\d{2})[-/](?:0?[1-9]|1[0-2])(?:[-/]\d{1,2})?$")
    quarter_pattern = re.compile(r"^(?:20\d{2})[-_ ]?q[1-4]$", re.IGNORECASE)
    for path, value in _walk(metric):
        if isinstance(value, str):
            text = value.strip()
            if period_pattern.match(text) or quarter_pattern.match(text):
                return _path_text(path)
    return None


def _find_numerator_denominator(metric: dict[str, Any]) -> str | None:
    numerator = _find_key(metric, {"numerator", "numeratore"})
    denominator = _find_key(metric, {"denominator", "denominatore"})
    if numerator and denominator:
        return f"{numerator} + {denominator}"
    return None


def _find_specific_categories(metric: dict[str, Any]) -> str | None:
    tokens = {
        "categories",
        "categorie",
        "breakdown",
        "disaggregation",
        "disaggregazione",
        "classi",
        "classes",
        "tipologie",
        "types",
        "ateco",
        "settore",
        "sector",
        "modalita",
        "specie",
        "ordine_scolastico",
        "classe_potenza",
    }
    return _find_labeled_dimension(metric, tokens)


def acquired_evidence(metric: dict[str, Any], dimension: str) -> str | None:
    if dimension == "serie_storica":
        return _find_series(metric)
    if dimension == "sesso":
        return _find_labeled_dimension(metric, {"sesso", "sex", "gender", "maschi", "femmine", "male", "female"})
    if dimension == "eta":
        return _find_labeled_dimension(metric, {"eta", "age", "fascia_eta", "classe_eta", "age_class"})
    if dimension == "dettaglio_territoriale":
        return _find_territorial_detail(metric)
    if dimension == "benchmark_toscana_italia":
        return _find_benchmark(metric)
    if dimension == "assoluto_normalizzato":
        return _find_absolute_normalized(metric)
    if dimension == "frequenza_infra_annuale":
        return _find_infra_annual(metric)
    if dimension == "numeratore_denominatore":
        return _find_numerator_denominator(metric)
    if dimension == "categorie_specifiche":
        return _find_specific_categories(metric)
    raise RuntimeError(f"Dimensione A3 non riconosciuta: {dimension}")


def _annotation(
    metric_id: str,
    policy: dict[str, Any],
    registry: dict[str, Any],
    dimension: str,
) -> tuple[dict[str, Any] | None, str]:
    overrides = registry.get("metricOverrides")
    overrides = overrides if isinstance(overrides, dict) else {}
    override = overrides.get(metric_id)
    override = override if isinstance(override, dict) else {}
    metric_dimensions = override.get("enrichmentDimensions")
    metric_dimensions = metric_dimensions if isinstance(metric_dimensions, dict) else {}
    item = metric_dimensions.get(dimension)
    if item is not None:
        if not isinstance(item, dict):
            raise RuntimeError(f"Annotazione enrichment non valida: {metric_id}/{dimension}")
        return item, "metric_override"

    profiles = registry.get("sourceProfiles")
    profiles = profiles if isinstance(profiles, dict) else {}
    profile_id = str(policy.get("profileId") or "")
    profile = profiles.get(profile_id)
    profile = profile if isinstance(profile, dict) else {}
    profile_dimensions = profile.get("enrichmentDimensions")
    profile_dimensions = profile_dimensions if isinstance(profile_dimensions, dict) else {}
    item = profile_dimensions.get(dimension)
    if item is not None:
        if not isinstance(item, dict):
            raise RuntimeError(f"Annotazione enrichment profilo non valida: {profile_id}/{dimension}")
        return item, "source_profile"
    return None, ""


def _validate_annotation(
    annotation: dict[str, Any],
    origin: str,
    metric_id: str,
    dimension: str,
) -> tuple[str, str, str]:
    state = str(annotation.get("state") or "").strip()
    allowed = METRIC_ALLOWED_STATES if origin == "metric_override" else PROFILE_ALLOWED_STATES
    if state not in allowed:
        raise RuntimeError(
            f"Stato enrichment non ammesso per {origin}: {metric_id}/{dimension} -> {state!r}"
        )
    evidence = str(annotation.get("evidence") or "").strip()
    if not evidence:
        raise RuntimeError(f"Evidenza enrichment assente: {metric_id}/{dimension}")
    source_reference = str(annotation.get("sourceReference") or "").strip()
    if state in {"AVAILABLE_MISSING", "SOURCE_UNAVAILABLE"} and not source_reference:
        raise RuntimeError(
            f"Riferimento fonte obbligatorio per {state}: {metric_id}/{dimension}"
        )
    return state, evidence, source_reference


def build_matrix(data: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise RuntimeError("Catalogo pubblico privo di metrics")

    rows: list[dict[str, Any]] = []
    profiles: set[str] = set()
    state_counts = {state: 0 for state in sorted(FINAL_STATES)}
    unclassified = 0

    for metric_id, metric in sorted(metrics.items()):
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica pubblica non valida: {metric_id}")
        policy = resolve_metric_policy(metric_id, metric, registry)
        if not policy.get("resolved"):
            raise RuntimeError(f"Policy fonte non risolta per {metric_id}")
        profile_id = str(policy.get("profileId") or "")
        profiles.add(profile_id)
        source_url = str(policy.get("sourceUrl") or metric.get("sourceUrl") or "").strip()
        if not source_url:
            raise RuntimeError(f"sourceUrl assente per {metric_id}")

        for dimension in DIMENSIONS:
            acquired = acquired_evidence(metric, dimension)
            row: dict[str, Any] = {
                "metricId": metric_id,
                "sourceUrl": source_url,
                "sourceProfileId": profile_id,
                "dimension": dimension,
                "state": None,
                "evidence": "",
                "sourceReference": "",
                "classificationOrigin": "pending_source_evidence",
            }
            if acquired:
                row.update(
                    {
                        "state": "ACQUIRED",
                        "evidence": f"structured:{acquired}",
                        "sourceReference": source_url,
                        "classificationOrigin": "catalog_structure",
                    }
                )
            else:
                annotation, origin = _annotation(metric_id, policy, registry, dimension)
                if annotation is not None:
                    state, evidence, source_reference = _validate_annotation(
                        annotation, origin, metric_id, dimension
                    )
                    row.update(
                        {
                            "state": state,
                            "evidence": evidence,
                            "sourceReference": source_reference,
                            "classificationOrigin": origin,
                        }
                    )

            state = row["state"]
            if state is None:
                unclassified += 1
            else:
                state_counts[str(state)] += 1
            rows.append(row)

    pair_count = len(rows)
    classified = pair_count - unclassified
    payload = {
        "schemaVersion": 1,
        "generatedFrom": {
            "catalogVersion": str(data.get("version") or ""),
            "catalogUpdated": str(data.get("updated") or ""),
        },
        "dimensions": list(DIMENSIONS),
        "summary": {
            "publicMetricCount": len(metrics),
            "dimensionCount": len(DIMENSIONS),
            "pairCount": pair_count,
            "classifiedPairCount": classified,
            "unclassifiedPairCount": unclassified,
            "sourceProfileCount": len(profiles),
            **{f"state_{state}": count for state, count in state_counts.items()},
        },
        "rows": rows,
    }
    validate_matrix(payload, require_complete=False)
    return payload


def validate_matrix(payload: dict[str, Any], *, require_complete: bool) -> None:
    dimensions = payload.get("dimensions")
    rows = payload.get("rows")
    summary = payload.get("summary")
    if dimensions != list(DIMENSIONS):
        raise RuntimeError("Vocabolario dimensioni A3 non allineato")
    if not isinstance(rows, list) or not isinstance(summary, dict):
        raise RuntimeError("Matrice enrichment non valida")

    expected_pairs = int(summary.get("publicMetricCount") or 0) * len(DIMENSIONS)
    if len(rows) != expected_pairs or summary.get("pairCount") != expected_pairs:
        raise RuntimeError(
            f"Copertura coppie enrichment incoerente: {len(rows)} != {expected_pairs}"
        )

    seen: set[tuple[str, str]] = set()
    unclassified = 0
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Riga enrichment non-oggetto")
        pair = (str(row.get("metricId") or ""), str(row.get("dimension") or ""))
        if not pair[0] or pair[1] not in DIMENSIONS:
            raise RuntimeError(f"Coppia enrichment non valida: {pair}")
        if pair in seen:
            raise RuntimeError(f"Coppia enrichment duplicata: {pair}")
        seen.add(pair)
        state = row.get("state")
        if state is None:
            unclassified += 1
            continue
        if state not in FINAL_STATES:
            raise RuntimeError(f"Stato enrichment non valido: {pair} -> {state}")
        if not str(row.get("evidence") or "").strip():
            raise RuntimeError(f"Evidenza enrichment assente: {pair}")
        if state in {"AVAILABLE_MISSING", "SOURCE_UNAVAILABLE"} and not str(
            row.get("sourceReference") or ""
        ).strip():
            raise RuntimeError(f"Riferimento fonte assente: {pair}")

    if summary.get("unclassifiedPairCount") != unclassified:
        raise RuntimeError("Conteggio coppie non classificate incoerente")
    if require_complete and unclassified:
        raise RuntimeError(
            "A3.2 incompleto: "
            f"{unclassified} coppie richiedono evidenza fonte prima della classificazione finale"
        )


def write_matrix(
    data_path: Path,
    registry_path: Path,
    output_path: Path | None,
    *,
    allow_unclassified: bool,
) -> dict[str, Any]:
    payload = build_matrix(load(data_path), load(registry_path))
    validate_matrix(payload, require_complete=not allow_unclassified)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--allow-unclassified",
        action="store_true",
        help="Convalida la matrice derivata senza richiedere che A3.2 sia già completo.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = write_matrix(
        args.data,
        args.registry,
        args.output,
        allow_unclassified=args.allow_unclassified,
    )
    summary = payload["summary"]
    print(
        "A3 enrichment matrix: "
        f"{summary['publicMetricCount']} indicatori × {summary['dimensionCount']} dimensioni = "
        f"{summary['pairCount']} coppie · {summary['classifiedPairCount']} classificate · "
        f"{summary['unclassifiedPairCount']} da auditare."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
