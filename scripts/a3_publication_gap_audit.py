# certification trigger: controlled A3 fan-in round 2
#!/usr/bin/env python3
"""Verify that A3-acquired history and Toscana/Italia benchmarks reach public UI contracts."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

PRIORITY_DIMENSIONS = ("serie_storica", "benchmark_toscana_italia")
PUBLIC_STATUSES = {"PUBLIC_RENDERED", "SPECIAL_ROUTE_RENDERED"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-object: {path}")
    return value


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _valid_series(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    years = value.get("years")
    values = value.get("values")
    if not isinstance(years, list) or not isinstance(values, list):
        return False
    if len(years) < 2 or len(years) != len(values):
        return False
    pairs = [
        (str(year), float(raw))
        for year, raw in zip(years, values, strict=True)
        if _finite(raw)
    ]
    return len(pairs) >= 2 and len({year for year, _ in pairs}) == len(pairs)


def _generic_history(metric: dict[str, Any]) -> bool:
    rows = [
        row
        for row in metric.get("rows", [])
        if isinstance(row, dict) and not row.get("notApplicable")
    ]
    if not rows:
        return False
    maps: list[set[str]] = []
    for row in rows:
        series = row.get("series")
        if not _valid_series(series):
            return False
        years = {
            str(year)
            for year, raw in zip(series["years"], series["values"], strict=True)
            if _finite(raw)
        }
        maps.append(years)
    common = set(maps[0])
    for years in maps[1:]:
        common &= years
    return len(common) >= 2


def _any_history(metric: dict[str, Any]) -> bool:
    return any(
        isinstance(row, dict) and _valid_series(row.get("series"))
        for row in metric.get("rows", [])
    )


def _history_payload(value: Any) -> bool:
    if _valid_series(value):
        return True
    if isinstance(value, dict):
        years = value.get("years")
        if isinstance(years, list) and len(years) >= 2:
            parallel = [
                raw
                for key, raw in value.items()
                if key != "years"
                and isinstance(raw, list)
                and len(raw) == len(years)
                and sum(_finite(item) for item in raw) >= 2
            ]
            if parallel:
                return True
        return any(_history_payload(item) for item in value.values())
    if isinstance(value, list) and len(value) >= 2:
        rows = [item for item in value if isinstance(item, dict)]
        if len(rows) == len(value) and all("year" in item for item in rows):
            return all(
                any(_finite(raw) for key, raw in item.items() if key != "year")
                for item in rows
            )
    return False


def _special_history_fields(metric: dict[str, Any]) -> set[str]:
    fields: set[str] = set()
    containers = [
        row for row in metric.get("rows", [])
        if isinstance(row, dict)
    ]
    aggregate = metric.get("aggregate")
    if isinstance(aggregate, dict):
        containers.append(aggregate)
    for container in containers:
        for key, value in container.items():
            if not re.search(r"(series|history|storico|andamento)", str(key), re.IGNORECASE):
                continue
            if _history_payload(value):
                fields.add(str(key))
    return fields


def _runtime_metric_history_context(runtime: str, metric_id: str) -> bool:
    if not metric_id or metric_id not in runtime:
        return False
    lower = runtime.lower()
    needle = metric_id.lower()
    start = 0
    while True:
        index = lower.find(needle, start)
        if index < 0:
            return False
        window = lower[max(0, index - 600): index + len(needle) + 600]
        if "history" in window or "storico" in window or "andamento" in window:
            return True
        start = index + len(needle)


def _valid_meta_benchmark(metric: dict[str, Any]) -> bool:
    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    benchmark = meta.get("benchmark")
    if not isinstance(benchmark, dict):
        return False
    if not _finite(benchmark.get("tuscany")):
        return False
    italy = benchmark.get("italy")
    if italy is not None and not _finite(italy):
        return False
    return all(str(benchmark.get(key) or "").strip() for key in ("year", "source", "url"))


def _route_index(dist: Path, metric: dict[str, Any]) -> Path | None:
    storage = metric.get("dataStorage")
    storage = storage if isinstance(storage, dict) else {}
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    route = storage.get("detailRoute") or meta.get("detailRoute")
    if not isinstance(route, str) or not route.strip():
        return None
    return dist / route.strip("/") / "index.html"


def _runtime_corpus(dist: Path) -> str:
    assets = dist / "assets"
    if not assets.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(assets.glob("*.js")):
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(chunks)


def _demographic_component_history(metric: dict[str, Any], runtime: str) -> str | None:
    """Certify the selectable demographic route without inventing default history."""
    meta = metric.get("meta", {})
    if not isinstance(meta, dict) or meta.get("compositeType") != "demographicBreakdown":
        return None
    rows = metric.get("rows", [])
    if not isinstance(rows, list) or len(rows) != 7 or not all(isinstance(row, dict) for row in rows):
        return None
    if any(row.get("notApplicable") for row in rows):
        return None
    if any(not row.get("code") or not row.get("town") for row in rows):
        return None
    if len({row["code"] for row in rows}) != 7 or len({row["town"] for row in rows}) != 7:
        return None

    options = []
    for field in ("ageOptions", "genderOptions"):
        values = meta.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(item, dict) for item in values):
            return None
        keys = [item.get("key") for item in values]
        if any(not isinstance(key, str) or not key for key in keys) or len(set(keys)) != len(keys):
            return None
        options.append(set(keys))

    def function_body(name: str) -> str:
        found = re.search(r"\bfunction\s+" + name + r"\s*\([^)]*\)\s*\{(.*?)(?=\n\s*function\s|\Z)", runtime, re.DOTALL)
        return found.group(1) if found else ""

    projection = function_body("compositeChoiceMetric")
    detector = function_body("hasComponentHistory")
    selector = function_body("currentCompositeChoice")
    if not ("demographicBreakdown" in projection and "row.parts" in projection
            and "item.key===selected" in re.sub(r"\s+", "", projection)
            and "series:part.series" in re.sub(r"\s+", "", projection)
            and "demographicBreakdown" in detector and "part.series" in detector
            and all(token in selector for token in ("data-demographic-age", "data-demographic-gender", "${age}|${gender}"))
            and re.search(r"hasComponentHistory\([^)]*\)[^\n;?]*\?\s*currentCompositeChoice\(", runtime)
            and re.search(r"historyMetric\(\s*compositeChoiceMetric\(", runtime)):
        return None

    candidates = None
    for row in rows:
        parts = row.get("parts")
        if not isinstance(parts, list) or not all(isinstance(part, dict) for part in parts):
            return None
        keys = [part.get("key") for part in parts]
        if any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
            return None
        available = {}
        for part in parts:
            age, gender = part.get("ageKey"), part.get("genderKey")
            key = part.get("key")
            if age not in options[0] or gender not in options[1] or key != f"{age}|{gender}":
                return None
            series = part.get("series")
            if (_valid_series(series) and all(_finite(value) for value in series["values"])
                    and all(re.fullmatch(r"[0-9]{4}", str(year)) for year in series["years"])):
                available[key] = {str(year) for year in series["years"]}
        if candidates is None:
            candidates = available
        else:
            candidates = {key: years & available[key] for key, years in candidates.items() if key in available}
    return next((key for key, years in (candidates or {}).items() if len(years) >= 2), None)


def _history_status(
    metric_id: str,
    metric: dict[str, Any],
    evidence: str,
    dist: Path,
    runtime: str,
) -> tuple[str, str]:
    if any(
        isinstance(row, dict) and isinstance(row.get("a3History"), dict)
        for row in metric.get("rows", [])
    ):
        return (
            "PUBLIC_PAYLOAD_NOT_RENDERED",
            "a3History is still present instead of canonical row.series years/values",
        )
    if _generic_history(metric):
        return (
            "PUBLIC_RENDERED",
            "canonical row.series years/values is consumable by the standard history renderer/export",
        )

    component = _demographic_component_history(metric, runtime)
    if component is not None:
        return ("SPECIAL_ROUTE_RENDERED", f"selectable demographic component {component} has common native history consumed by public age/gender selectors and history renderer")

    special_fields = _special_history_fields(metric)
    if special_fields:
        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        composite_type = str(meta.get("compositeType") or "")
        runtime_fields = {field for field in special_fields if field in runtime}
        specialist_contract = bool(
            runtime_fields
            and (
                (composite_type and composite_type in runtime)
                or _runtime_metric_history_context(runtime, metric_id)
            )
        )
        if specialist_contract:
            return (
                "SPECIAL_ROUTE_RENDERED",
                "specialist public runtime consumes historical field(s): "
                + ", ".join(sorted(runtime_fields)),
            )

    route = _route_index(dist, metric)
    if route is not None and route.is_file():
        text = route.read_text(encoding="utf-8", errors="ignore").lower()
        if "storico" in text or "andamento" in text:
            return (
                "SPECIAL_ROUTE_RENDERED",
                f"history published by specialist route {route.relative_to(dist)}",
            )

    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    if meta.get("allowPartialHistory") is True and _any_history(metric) and metric_id in runtime:
        return (
            "SPECIAL_ROUTE_RENDERED",
            "partial history is governed by a specialist public renderer",
        )

    tokens = [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]+", evidence)
        if token not in {"structured", "rows", "series", "values", "years", "storage", "data"}
    ]
    if _any_history(metric) and metric_id in runtime and any(token in runtime for token in tokens):
        return (
            "SPECIAL_ROUTE_RENDERED",
            "specialist history structure is consumed by public runtime",
        )

    return (
        "NOT_PUBLIC_DESPITE_ACQUIRED",
        "A3 reports acquired history but no public renderer contract was found",
    )


def _benchmark_status(
    metric_id: str,
    metric: dict[str, Any],
    evidence: str,
    dist: Path,
    runtime: str,
) -> tuple[str, str]:
    if _valid_meta_benchmark(metric):
        return (
            "PUBLIC_RENDERED",
            "meta.benchmark exposes Tuscany and optional Italy with year/source/link",
        )

    aggregate = metric.get("aggregate")
    national = metric.get("nationalBenchmark")
    if isinstance(aggregate, dict) and isinstance(national, dict):
        labels = f"{aggregate.get('label', '')} {national.get('label', '')}".lower()
        if (
            _finite(aggregate.get("value"))
            and _finite(national.get("value"))
            and "toscana" in labels
            and "italia" in labels
            and metric_id in runtime
        ):
            return (
                "SPECIAL_ROUTE_RENDERED",
                "specialist benchmark renderer consumes Toscana/Italia values",
            )

    route = _route_index(dist, metric)
    if route is not None and route.is_file():
        text = route.read_text(encoding="utf-8", errors="ignore").lower()
        if "toscana" in text or "regionale" in text:
            return (
                "SPECIAL_ROUTE_RENDERED",
                f"regional benchmark published by specialist route {route.relative_to(dist)}",
            )

    if evidence.endswith("method.reference") or evidence.endswith("method.riferimento"):
        return (
            "DETECTOR_FALSE_POSITIVE",
            "bibliographic/geographic reference text is not a numeric Toscana/Italia benchmark",
        )

    return (
        "NOT_PUBLIC_DESPITE_ACQUIRED",
        "A3 reports acquired benchmark but no public Toscana/Italia renderer contract was found",
    )


def build_report(data: dict[str, Any], matrix: dict[str, Any], dist: Path) -> dict[str, Any]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Effective Public Catalog without metrics")
    runtime = _runtime_corpus(dist)
    entries: list[dict[str, Any]] = []

    for row in matrix.get("rows", []):
        if (
            not isinstance(row, dict)
            or row.get("dimension") not in PRIORITY_DIMENSIONS
            or row.get("state") != "ACQUIRED"
        ):
            continue
        metric_id = str(row.get("metricId") or "")
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"ACQUIRED metric missing from effective catalog: {metric_id}")
        dimension = str(row["dimension"])
        evidence = str(row.get("evidence") or "")
        if dimension == "serie_storica":
            status, reason = _history_status(metric_id, metric, evidence, dist, runtime)
        else:
            status, reason = _benchmark_status(metric_id, metric, evidence, dist, runtime)

        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        entries.append(
            {
                "metricId": metric_id,
                "dimension": dimension,
                "publicationStatus": status,
                "evidence": evidence,
                "reason": reason,
                "source": str(meta.get("source") or ""),
                "period": str(meta.get("year") or ""),
                "unit": str(meta.get("unit") or ""),
                "sourceUrl": str(metric.get("sourceUrl") or ""),
            }
        )

    summary: dict[str, Any] = {}
    for dimension in PRIORITY_DIMENSIONS:
        dim_entries = [item for item in entries if item["dimension"] == dimension]
        counts = Counter(item["publicationStatus"] for item in dim_entries)
        public = sum(counts[state] for state in PUBLIC_STATUSES)
        summary[dimension] = {
            "acquired": len(dim_entries),
            "public": public,
            "notPublic": len(dim_entries) - public,
            "statuses": dict(sorted(counts.items())),
        }

    return {
        "schemaVersion": 1,
        "effectivePublicMetricCount": len(metrics),
        "matrixSummary": matrix.get("summary", {}),
        "summary": summary,
        "entries": sorted(entries, key=lambda item: (item["dimension"], item["metricId"])),
    }


def validate_report(report: dict[str, Any]) -> None:
    missing = [
        item for item in report["entries"]
        if item["publicationStatus"] not in PUBLIC_STATUSES
    ]
    incomplete_metadata = [
        item for item in report["entries"]
        if not item["source"] or not item["period"] or not item["unit"] or not item["sourceUrl"]
    ]
    if incomplete_metadata:
        detail = ", ".join(
            f"{item['metricId']}/{item['dimension']}"
            for item in incomplete_metadata[:20]
        )
        raise RuntimeError(
            f"A3 publication contract: source/period/unit/link missing: {detail}"
        )
    if missing:
        detail = ", ".join(
            f"{item['metricId']}/{item['dimension']}={item['publicationStatus']}"
            for item in missing[:20]
        )
        raise RuntimeError(f"A3 publication contract not closed: {detail}")


def markdown(report: dict[str, Any]) -> str:
    labels = {
        "serie_storica": "Serie storiche",
        "benchmark_toscana_italia": "Benchmark Toscana / Italia",
    }
    lines = [
        "# A3 - Publication gap audit",
        "",
        f"Effective Public Catalog: **{report['effectivePublicMetricCount']} indicators**.",
        "",
        "## Summary",
        "",
        "| Dimension | ACQUIRED | Public | Not public |",
        "|---|---:|---:|---:|",
    ]
    for dimension in PRIORITY_DIMENSIONS:
        item = report["summary"][dimension]
        lines.append(
            f"| {labels[dimension]} | {item['acquired']} | {item['public']} | {item['notPublic']} |"
        )
    lines += [
        "",
        "## ACQUIRED pairs",
        "",
        "| Indicator | Dimension | Publication status | Evidence |",
        "|---|---|---|---|",
    ]
    for item in report["entries"]:
        reason = item["reason"].replace("|", "/")
        lines.append(
            f"| `{item['metricId']}` | `{item['dimension']}` | "
            f"`{item['publicationStatus']}` | {reason} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    report = build_report(load(args.data), load(args.matrix), args.dist)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown(report), encoding="utf-8")

    for dimension, item in report["summary"].items():
        print(
            f"A3 publication {dimension}: "
            f"{item['public']}/{item['acquired']} public; {item['notPublic']} gap."
        )
    if args.strict:
        validate_report(report)


if __name__ == "__main__":
    main()
