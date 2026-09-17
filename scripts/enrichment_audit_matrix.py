#!/usr/bin/env python3
"""Derived A3 enrichment classification matrix.

The public metric inventory is always derived from the Effective Public Catalog.
Only the four final states defined by A3.1 are accepted. ``state: null`` means
"not classified yet" and strict validation rejects it; it is not a fifth state.
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
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value))
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _token_in_text(value: Any, token: str) -> bool:
    text = _norm(value)
    normalized = _norm(token)
    if not text or not normalized:
        return False
    if text == normalized:
        return True
    if "_" in normalized:
        return normalized in text
    return normalized in text.split("_")


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
    return bool(path) and any(_token_in_text(path[-1], token) for token in tokens)


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
        if not all(isinstance(item, dict) for item in value):
            continue
        periods: set[str] = set()
        for item in value:
            assert isinstance(item, dict)
            for key, candidate in item.items():
                if any(_token_in_text(key, token) for token in period_tokens) and _has_value(candidate):
                    periods.add(str(candidate))
        if len(periods) >= 2:
            return _path_text(path)

    # Several materialized public metrics store history as a compact object
    # ``{"years": [...], "values": [...]}`` rather than as a list of points.
    # Treat it as structural evidence only when both vectors are aligned and
    # contain at least two actual observations.
    period_vector_keys = {"years", "anni", "periods", "periodi", "dates"}
    value_vector_keys = {"values", "valori"}
    for path, value in _walk(metric):
        if not isinstance(value, dict):
            continue
        normalized = {_norm(key): item for key, item in value.items()}
        periods = next(
            (normalized[key] for key in period_vector_keys if key in normalized), None
        )
        values = next(
            (normalized[key] for key in value_vector_keys if key in normalized), None
        )
        if not isinstance(periods, list) or not isinstance(values, list):
            continue
        if len(periods) < 2 or len(periods) != len(values):
            continue
        if sum(1 for item in values if _has_value(item)) < 2:
            continue
        return _path_text(path)
    return None


def _find_labeled_dimension(metric: dict[str, Any], tokens: set[str]) -> str | None:
    direct = _find_key(metric, tokens)
    if direct:
        return direct
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
        if _norm(path[-1]) not in label_keys:
            continue
        if any(_token_in_text(value, token) for token in tokens):
            return _path_text(path)
    return None


def _find_benchmark(metric: dict[str, Any]) -> str | None:
    geographies = {"toscana", "italia", "italy", "nazionale", "national", "regionale"}
    for path, value in _walk(metric):
        if not path or not _has_value(value):
            continue
        key = path[-1]
        if any(_token_in_text(key, token) for token in geographies):
            return _path_text(path)
        if not any(_token_in_text(key, token) for token in {"benchmark", "reference", "riferimento"}):
            continue
        candidates: list[Any]
        if isinstance(value, dict):
            candidates = [*value.keys(), *value.values()]
        elif isinstance(value, list):
            candidates = value
        else:
            candidates = [value]
        if any(
            _token_in_text(candidate, token)
            for candidate in candidates
            for token in geographies
            if isinstance(candidate, (str, int, float))
        ):
            return _path_text(path)
    return None


def _find_territorial_detail(metric: dict[str, Any]) -> str | None:
    return _find_labeled_dimension(
        metric,
        {
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
        },
    )


def _find_absolute_normalized(metric: dict[str, Any]) -> str | None:
    absolute = _find_key(
        metric,
        {
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
        },
    )
    normalized = _find_key(
        metric,
        {
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
        },
    )
    if absolute and normalized and absolute != normalized:
        return f"{absolute} + {normalized}"

    # The public catalog also has an explicit normalization contract: metadata
    # under ``meta.normalized`` plus a base ``value`` and its normalized twin.
    # This is stronger evidence than inferring normalization from labels alone.
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    normalized_meta = meta.get("normalized")
    if not isinstance(normalized_meta, dict) or not normalized_meta:
        return None

    rows = metric.get("rows")
    if isinstance(rows, list):
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            normalized_value = row.get("normalized")
            normalized_key = "normalized"
            if not _has_value(normalized_value):
                normalized_value = row.get("normalizedValue")
                normalized_key = "normalizedValue"
            if _has_value(row.get("value")) and _has_value(normalized_value):
                return f"rows.{index}.value + rows.{index}.{normalized_key}"

    aggregate = metric.get("aggregate")
    normalized_aggregate = metric.get("normalizedAggregate")
    if isinstance(aggregate, dict) and isinstance(normalized_aggregate, dict):
        if _has_value(aggregate.get("value")) and _has_value(normalized_aggregate.get("value")):
            return "aggregate.value + normalizedAggregate.value"
    return None


def _find_infra_annual(metric: dict[str, Any]) -> str | None:
    direct = _find_labeled_dimension(
        metric,
        {
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
        },
    )
    if direct:
        return direct
    month = re.compile(r"^(?:20\d{2})[-/](?:0?[1-9]|1[0-2])(?:[-/]\d{1,2})?$")
    quarter = re.compile(r"^(?:20\d{2})[-_ ]?q[1-4]$", re.IGNORECASE)
    for path, value in _walk(metric):
        if isinstance(value, str) and (month.match(value.strip()) or quarter.match(value.strip())):
            return _path_text(path)
    return None


def _find_numerator_denominator(metric: dict[str, Any]) -> str | None:
    numerator = _find_key(metric, {"numerator", "numeratore"})
    denominator = _find_key(metric, {"denominator", "denominatore"})
    if numerator and denominator:
        return f"{numerator} + {denominator}"
    return None


def _find_specific_categories(metric: dict[str, Any]) -> str | None:
    labeled = _find_labeled_dimension(
        metric,
        {
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
        },
    )
    if labeled:
        return labeled

    # Composite public indicators expose categorical choices through the same
    # structural contract used by the UI: a selector label and at least two
    # identifiable ``aggregate.parts``. Do not infer categories from parts alone.
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    selector_label = meta.get("selectorLabel")
    aggregate = metric.get("aggregate")
    aggregate = aggregate if isinstance(aggregate, dict) else {}
    parts = aggregate.get("parts")
    if not isinstance(selector_label, str) or not selector_label.strip():
        return None
    if not isinstance(parts, list) or len(parts) < 2:
        return None
    identifiable = sum(
        1
        for part in parts
        if isinstance(part, dict)
        and any(_has_value(part.get(key)) for key in ("key", "label", "selectorLabel"))
    )
    if identifiable >= 2:
        return "meta.selectorLabel + aggregate.parts"
    return None


def acquired_evidence(metric: dict[str, Any], dimension: str) -> str | None:
    detectors = {
        "serie_storica": _find_series,
        "sesso": lambda item: _find_labeled_dimension(
            item, {"sesso", "sex", "gender", "maschi", "femmine", "male", "female"}
        ),
        "eta": lambda item: _find_labeled_dimension(
            item, {"eta", "age", "fascia_eta", "classe_eta", "age_class"}
        ),
        "dettaglio_territoriale": _find_territorial_detail,
        "benchmark_toscana_italia": _find_benchmark,
        "assoluto_normalizzato": _find_absolute_normalized,
        "frequenza_infra_annuale": _find_infra_annual,
        "numeratore_denominatore": _find_numerator_denominator,
        "categorie_specifiche": _find_specific_categories,
    }
    detector = detectors.get(dimension)
    if detector is None:
        raise RuntimeError(f"Dimensione A3 non riconosciuta: {dimension}")
    return detector(metric)


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
        raise RuntimeError(f"Riferimento fonte obbligatorio per {state}: {metric_id}/{dimension}")
    return state, evidence, source_reference


def build_matrix(data: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise RuntimeError("Catalogo pubblico privo di metrics")

    rows: list[dict[str, Any]] = []
    profiles: set[str] = set()
    counts = {state: 0 for state in sorted(FINAL_STATES)}
    unclassified = 0

    for metric_id, metric in sorted(metrics.items()):
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica pubblica non valida: {metric_id}")
        policy = resolve_metric_policy(metric_id, metric, registry)
        if not policy.get("resolved"):
            raise RuntimeError(f"Policy fonte non risolta per {metric_id}")
        profile_id = str(policy.get("profileId") or "")
        source_url = str(policy.get("sourceUrl") or metric.get("sourceUrl") or "").strip()
        if not source_url:
            raise RuntimeError(f"sourceUrl assente per {metric_id}")
        profiles.add(profile_id)

        for dimension in DIMENSIONS:
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
            structured = acquired_evidence(metric, dimension)
            if structured:
                row.update(
                    state="ACQUIRED",
                    evidence=f"structured:{structured}",
                    sourceReference=source_url,
                    classificationOrigin="catalog_structure",
                )
            else:
                annotation, origin = _annotation(metric_id, policy, registry, dimension)
                if annotation is not None:
                    state, evidence, reference = _validate_annotation(
                        annotation, origin, metric_id, dimension
                    )
                    row.update(
                        state=state,
                        evidence=evidence,
                        sourceReference=reference,
                        classificationOrigin=origin,
                    )
            if row["state"] is None:
                unclassified += 1
            else:
                counts[str(row["state"])] += 1
            rows.append(row)

    pair_count = len(rows)
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
            "classifiedPairCount": pair_count - unclassified,
            "unclassifiedPairCount": unclassified,
            "sourceProfileCount": len(profiles),
            **{f"state_{state}": count for state, count in counts.items()},
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

    expected = int(summary.get("publicMetricCount") or 0) * len(DIMENSIONS)
    if len(rows) != expected or summary.get("pairCount") != expected:
        raise RuntimeError(f"Copertura coppie enrichment incoerente: {len(rows)} != {expected}")

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
    parser.add_argument("--allow-unclassified", action="store_true")
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
