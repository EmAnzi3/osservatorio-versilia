#!/usr/bin/env python3
"""Validate the A6 minimal semantic model against the canonical catalog."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "site-data.json"
DEFAULT_CONTRACT = ROOT / "ci" / "semantic-model-contract.json"


def load_json(path: Path | str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON non-oggetto: {path}")
    return value


def _present(value: Any) -> bool:
    return value not in (None, "")


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _series_nodes(node: Any, path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(node, dict):
        series = node.get("series")
        if isinstance(series, dict):
            yield f"{path}.series", series
        for key, value in node.items():
            if key == "series":
                continue
            yield from _series_nodes(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _series_nodes(value, f"{path}[{index}]")


def _dimension_counts(metric: dict[str, Any], counts: Counter[str]) -> None:
    aggregate = metric.get("aggregate")
    if isinstance(aggregate, dict) and aggregate.get("parts"):
        counts["aggregate.parts"] += 1
    for row in metric.get("rows") or []:
        if not isinstance(row, dict):
            continue
        for key in ("parts", "detailParts"):
            if row.get(key):
                counts[f"rows[].{key}"] += 1
        if isinstance(row.get("normalized"), dict):
            counts["rows[].normalized"] += 1
        if isinstance(row.get("ratioComponents"), dict):
            counts["rows[].ratioComponents"] += 1


def _metric_has_unit(metric: dict[str, Any]) -> bool:
    meta = metric.get("meta") or {}
    if _present(meta.get("unit")) or _present(meta.get("summaryUnit")):
        return True
    aggregate = metric.get("aggregate")
    if isinstance(aggregate, dict):
        for part in aggregate.get("parts") or []:
            if isinstance(part, dict) and _present(part.get("unit")):
                return True
    for row in metric.get("rows") or []:
        if not isinstance(row, dict):
            continue
        normalized = row.get("normalized")
        if isinstance(normalized, dict) and _present(normalized.get("unit")):
            return True
        for key in ("parts", "detailParts"):
            for part in row.get(key) or []:
                if isinstance(part, dict) and _present(part.get("unit")):
                    return True
    return False


def validate_semantic_model_contract(
    data_path: Path | str = DEFAULT_DATA,
    contract_path: Path | str = DEFAULT_CONTRACT,
    *,
    layer: str = "source",
) -> dict[str, Any]:
    data = load_json(data_path)
    contract = load_json(contract_path)

    assert contract.get("schemaVersion") == 1, "Semantic model schemaVersion inatteso"
    scope = contract.get("scope") or {}
    assert scope.get("deriveFromCanonicalCatalog") is True
    assert scope.get("noMunicipalityInventory") is True
    assert scope.get("noThemeInventory") is True
    assert scope.get("noIndicatorInventory") is True

    source_of_truth = contract.get("sourceOfTruth") or {}
    assert source_of_truth.get("canonical") == "data/site-data.json"
    assert source_of_truth.get("effective") == "dist/data/site-data.json"
    layers = contract.get("layers") or {}
    assert set(layers) == {"source", "effective"}, f"Layer semantici inattesi: {sorted(layers)}"
    assert layer in layers, f"Layer semantico sconosciuto: {layer}"
    assert layers["source"].get("querySurface") is False
    assert layers["effective"].get("querySurface") is True
    assert layers["effective"].get("derived") is True

    towns = data.get("towns")
    themes = data.get("themes")
    metrics = data.get("metrics")
    assert isinstance(towns, list) and towns, "Catalogo senza Comuni"
    assert isinstance(themes, dict) and themes, "Catalogo senza temi"
    assert isinstance(metrics, dict) and metrics, "Catalogo senza indicatori"

    town_by_code: dict[str, dict[str, Any]] = {}
    town_by_name: dict[str, dict[str, Any]] = {}
    for index, town in enumerate(towns):
        assert isinstance(town, dict), f"Comune non-oggetto: towns[{index}]"
        code = str(town.get("code") or "").strip()
        name = str(town.get("name") or "").strip()
        assert code and name, f"Comune senza code/name: towns[{index}]"
        assert code not in town_by_code, f"Codice Comune duplicato: {code}"
        assert name not in town_by_name, f"Nome Comune duplicato: {name}"
        town_by_code[code] = town
        town_by_name[name] = town

    theme_metric_refs: set[str] = set()
    for theme_id, theme in themes.items():
        assert isinstance(theme, dict), f"Tema non-oggetto: {theme_id}"
        assert str(theme.get("label") or "").strip(), f"Tema senza label: {theme_id}"
        members = theme.get("metrics")
        assert isinstance(members, list) and members, f"Tema senza metrics: {theme_id}"
        for metric_id in members:
            assert metric_id in metrics, f"Tema {theme_id}: indicatore inesistente {metric_id}"
            theme_metric_refs.add(str(metric_id))

    counts: Counter[str] = Counter()
    sources: set[tuple[str, str]] = set()
    periods: set[str] = set()
    dimensions: Counter[str] = Counter()

    for metric_id, metric in metrics.items():
        assert isinstance(metric, dict), f"Indicatore non-oggetto: {metric_id}"
        meta = metric.get("meta")
        assert isinstance(meta, dict), f"Meta non-oggetto: {metric_id}"

        theme_id = str(meta.get("theme") or "").strip()
        assert theme_id in themes, f"Tema semantico sconosciuto {metric_id}: {theme_id!r}"
        assert metric_id in themes[theme_id].get("metrics", []), (
            f"Appartenenza tema non bidirezionale: {metric_id} -> {theme_id}"
        )
        assert str(meta.get("label") or "").strip(), f"Indicatore senza label: {metric_id}"

        current_period = str(meta.get("year") or "").strip()
        assert current_period, f"Periodo corrente mancante: {metric_id}"
        periods.add(current_period)

        source_label = str(meta.get("source") or "").strip()
        source_url = str(metric.get("sourceUrl") or "").strip()
        assert source_label and source_url, f"Fonte semantica incompleta: {metric_id}"
        assert source_url.startswith(("https://", "http://")), f"URL fonte non valido {metric_id}: {source_url}"
        sources.add((source_label, source_url))

        rows = metric.get("rows")
        assert isinstance(rows, list), f"Rows non-lista: {metric_id}"
        numeric_rows = 0
        for index, row in enumerate(rows):
            assert isinstance(row, dict), f"Riga non-oggetto {metric_id}[{index}]"
            value = row.get("value")
            if _finite(value):
                numeric_rows += 1
            town_name = str(row.get("town") or "").strip()
            town_code = str(row.get("code") or "").strip()
            if town_name or town_code:
                resolved_by_name = town_by_name.get(town_name) if town_name else None
                resolved_by_code = town_by_code.get(town_code) if town_code else None
                assert resolved_by_name or resolved_by_code, (
                    f"Riga comunale non risolta {metric_id}[{index}]: town={town_name!r} code={town_code!r}"
                )
                if resolved_by_name and resolved_by_code:
                    assert str(resolved_by_name.get("code")) == str(resolved_by_code.get("code")), (
                        f"Town/code incoerenti {metric_id}[{index}]: {town_name}/{town_code}"
                    )
                counts["municipalRows"] += 1

        if numeric_rows:
            assert _metric_has_unit(metric), f"Unità semantica non esplicita: {metric_id}"

        benchmark = meta.get("benchmark")
        if benchmark is not None:
            assert isinstance(benchmark, dict), f"Benchmark non-oggetto: {metric_id}"
            spec = contract.get("entities", {}).get("benchmark", {})
            for field in spec.get("requiredFields") or []:
                assert _present(benchmark.get(field)), f"Benchmark incompleto {metric_id}: {field}"
            value_fields = spec.get("valueFields") or []
            assert any(_finite(benchmark.get(field)) for field in value_fields), (
                f"Benchmark senza valori numerici: {metric_id}"
            )
            counts["benchmarkMetrics"] += 1

        for series_path, series in _series_nodes(metric, f"metrics.{metric_id}"):
            years = series.get("years")
            values = series.get("values")
            assert isinstance(years, list) and isinstance(values, list), f"Serie incompleta: {series_path}"
            assert len(years) == len(values) and years, (
                f"Serie years/values disallineata: {series_path} ({len(years)}/{len(values)})"
            )
            tokens = [str(year) for year in years]
            assert len(tokens) == len(set(tokens)), f"Periodi duplicati: {series_path}"
            periods.update(tokens)
            counts["historicalSeries"] += 1

        _dimension_counts(metric, dimensions)
        counts["metrics"] += 1

    missing_from_themes = set(metrics) - theme_metric_refs
    assert not missing_from_themes, (
        "Indicatori non referenziati da alcun tema: " + ", ".join(sorted(missing_from_themes)[:12])
    )

    return {
        "layer": layer,
        "municipalities": len(town_by_code),
        "themes": len(themes),
        "metrics": int(counts["metrics"]),
        "municipalRows": int(counts["municipalRows"]),
        "sources": len(sources),
        "periods": len(periods),
        "historicalSeries": int(counts["historicalSeries"]),
        "benchmarkMetrics": int(counts["benchmarkMetrics"]),
        "dimensionCarriers": dict(sorted(dimensions.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--layer", choices=("source", "effective"), default="source")
    args = parser.parse_args(argv)
    report = validate_semantic_model_contract(args.data, args.contract, layer=args.layer)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"A6 semantic model contract [{report['layer']}]: "
        f"{report['municipalities']} Comuni · {report['themes']} temi · {report['metrics']} indicatori · "
        f"{report['periods']} periodi · {report['sources']} fonti · "
        f"{report['historicalSeries']} serie storiche."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
