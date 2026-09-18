#!/usr/bin/env python3
"""Route/storage-aware structural evidence for A3.2.

This module deliberately contains no metric IDs or source-profile IDs.  It
inspects an indicator's declared storage contract and, when present, the
structured payload materialized by that contract.  The caller may use the
returned evidence only for ACQUIRED: no source-availability or semantic state
is inferred here.
"""
from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path
from typing import Any, Iterable

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


def _norm(value: Any) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, (*path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, (*path, str(index)))


def _path(path: tuple[str, ...]) -> str:
    return ".".join(path) or "$"


def _storage(metric: dict[str, Any]) -> dict[str, Any]:
    for key in ("dataStorage", "data_storage", "storage"):
        value = metric.get(key)
        if isinstance(value, dict):
            return value
    meta = metric.get("meta")
    if isinstance(meta, dict):
        for key in ("dataStorage", "data_storage", "storage"):
            value = meta.get(key)
            if isinstance(value, dict):
                return value
    return {}


def _declared_path(storage: dict[str, Any]) -> str | None:
    for key in ("path", "directory", "dir", "basePath", "base_path"):
        value = storage.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lstrip("/")
    return None


def _declared_prefix(storage: dict[str, Any]) -> str | None:
    for key in ("prefix", "chunkPrefix", "chunk_prefix", "filePrefix", "file_prefix"):
        value = storage.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _decode_chunked_payload(directory: Path, prefix: str | None = None) -> Any | None:
    if not directory.is_dir():
        return None
    candidates = sorted(directory.glob(f"{prefix or ''}*.b64"))
    if not candidates:
        json_files = sorted(directory.glob("*.json"))
        if len(json_files) == 1:
            try:
                return json.loads(json_files[0].read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
        return None
    try:
        encoded = "".join(path.read_text(encoding="utf-8").strip() for path in candidates)
        raw = base64.b64decode(encoded, validate=False)
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, gzip.BadGzipFile, UnicodeDecodeError, json.JSONDecodeError):
        return None


def load_declared_payload(metric: dict[str, Any], repo_root: Path) -> tuple[Any | None, str | None]:
    """Load only a payload explicitly referenced by the metric storage contract."""
    storage = _storage(metric)
    declared = _declared_path(storage)
    if not storage or not declared:
        return None, None
    target = (repo_root / declared).resolve()
    try:
        target.relative_to(repo_root.resolve())
    except ValueError:
        return None, None
    if target.is_file():
        try:
            if target.suffix == ".json":
                return json.loads(target.read_text(encoding="utf-8")), declared
        except (OSError, json.JSONDecodeError):
            return None, None
        return None, None
    payload = _decode_chunked_payload(target, _declared_prefix(storage))
    return payload, declared if payload is not None else None


def _find_key(payload: Any, tokens: set[str]) -> str | None:
    normalized = {_norm(token) for token in tokens}
    for path, value in _walk(payload):
        if not path or value in (None, "", [], {}):
            continue
        key = _norm(path[-1])
        if key in normalized or any(token and token in key.split("_") for token in normalized):
            return _path(path)
    return None


def _find_series(payload: Any) -> str | None:
    period_tokens = {"year", "years", "anno", "anni", "date", "period", "periods"}
    for path, value in _walk(payload):
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, dict) for item in value):
            observed: set[str] = set()
            for item in value:
                assert isinstance(item, dict)
                for key, candidate in item.items():
                    if _norm(key) in period_tokens and candidate not in (None, ""):
                        observed.add(str(candidate))
            if len(observed) >= 2:
                return _path(path)
        if isinstance(value, dict):
            periods = None
            observations = None
            for key, candidate in value.items():
                norm = _norm(key)
                if norm in period_tokens and isinstance(candidate, list):
                    periods = candidate
                elif norm in {"value", "values", "valori", "count", "counts", "rate", "rates", "pct"} and isinstance(candidate, list):
                    observations = candidate
            if periods is not None and observations is not None and len(periods) >= 2 and len(periods) == len(observations):
                return _path(path)
    return None


def _find_ratio_pair(payload: Any) -> str | None:
    numerator_tokens = {
        "numerator", "numeratore", "voters", "votanti", "votes", "presenze", "count", "events",
    }
    denominator_tokens = {
        "denominator", "denominatore", "electors", "elettori", "eligible", "population", "residenti", "total",
    }
    for path, value in _walk(payload):
        if not isinstance(value, dict):
            continue
        keys = {_norm(key): key for key in value}
        num = next((keys[token] for token in numerator_tokens if token in keys), None)
        den = next((keys[token] for token in denominator_tokens if token in keys), None)
        if num is not None and den is not None:
            return f"{_path(path)}.{num}/{den}"
    return None


def _has_normalized_contract(storage: dict[str, Any]) -> str | None:
    for key, value in storage.items():
        norm = _norm(key)
        if norm in {
            "normalizedpercent",
            "normalized_percent",
            "normalizedpercentage",
            "normalized_percentage",
        } and value is True:
            return f"dataStorage.{key}=true"
        if norm in {"unit", "value_unit", "normalized_unit"} and _norm(value) in {"percent", "percentage", "pct", "per_100", "per100"}:
            return f"dataStorage.{key}={value}"
    return None


def _find_absolute_and_normalized(payload: Any) -> str | None:
    ratio = _find_ratio_pair(payload)
    if ratio:
        for path, value in _walk(payload):
            if not isinstance(value, dict):
                continue
            keys = {_norm(key) for key in value}
            if keys & {"pct", "percent", "percentage", "rate", "ratio", "share", "normalized", "value", "turnout"}:
                return ratio
    return None


def structured_route_evidence(metric: dict[str, Any], dimension: str, repo_root: Path) -> str | None:
    """Return machine-verifiable route/storage evidence for one A3.2 dimension."""
    if dimension not in DIMENSIONS:
        return None
    storage = _storage(metric)
    if not storage:
        return None

    if dimension == "assoluto_normalizzato":
        declared = _has_normalized_contract(storage)
        if declared:
            return declared

    payload, declared_path = load_declared_payload(metric, repo_root)
    if payload is None or declared_path is None:
        return None
    prefix = f"storage:{declared_path}:"

    if dimension == "serie_storica":
        hit = _find_series(payload)
    elif dimension == "sesso":
        hit = _find_key(payload, {"sex", "sesso", "male", "female", "maschi", "femmine", "men", "women"})
    elif dimension == "eta":
        hit = _find_key(payload, {"age", "eta", "age_group", "classe_eta"})
    elif dimension == "dettaglio_territoriale":
        hit = _find_key(payload, {"section", "sezione", "frazione", "district", "quartiere", "province", "provincia", "region", "regione", "territory", "territorio", "municipality", "municipalities", "town", "towns", "comune", "comuni"})
    elif dimension == "benchmark_toscana_italia":
        hit = _find_key(payload, {"toscana", "italia", "italy", "regional", "regionale", "national", "nazionale", "benchmark"})
    elif dimension == "assoluto_normalizzato":
        hit = _find_absolute_and_normalized(payload)
    elif dimension == "frequenza_infra_annuale":
        hit = _find_key(payload, {"month", "months", "mese", "mesi", "quarter", "quarters", "trimestre", "trimestri"})
    elif dimension == "numeratore_denominatore":
        hit = _find_ratio_pair(payload)
    else:  # categorie_specifiche
        hit = _find_key(payload, {"category", "categories", "categoria", "categorie", "taxonomy", "taxon", "type", "tipologia", "family", "families"})

    return f"{prefix}{hit}" if hit else None
