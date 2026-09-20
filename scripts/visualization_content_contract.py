#!/usr/bin/env python3
"""Validate the A4 visualization/content contract against a catalog.

The contract is global and declarative: it describes formatting, comparison and
aggregation rules without maintaining a second inventory of metrics.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "ci" / "visualization-content-contract.json"
DEFAULT_DATA = ROOT / "data" / "site-data.json"
DEFAULT_VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON non-oggetto: {path}")
    return value


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _assert_close(actual: float, expected: float, *, absolute: float, relative: float, label: str) -> None:
    tolerance = max(float(absolute), abs(float(expected)) * float(relative))
    if abs(float(actual) - float(expected)) > tolerance:
        raise AssertionError(f"{label}: {actual} != {expected} (tolleranza {tolerance})")


def _governed_unit(token: Any, units: dict[str, Any], label: str, unit_counts: Counter[str]) -> None:
    if token in (None, ""):
        return
    assert token in units, f"Unità non governata {label}: {token}"
    unit_counts[str(token)] += 1


def _classify_aggregate(metric: dict[str, Any], *, absolute: float, relative: float) -> str:
    aggregate = metric.get("aggregate")
    aggregate_value = aggregate.get("value") if isinstance(aggregate, dict) else None
    values = [
        row.get("value")
        for row in metric.get("rows", [])
        if isinstance(row, dict) and _finite(row.get("value"))
    ]
    if not _finite(aggregate_value) or not values:
        return "nonNumeric"
    mean = sum(float(value) for value in values) / len(values)
    total = sum(float(value) for value in values)
    if abs(float(aggregate_value) - mean) <= max(absolute, abs(mean) * relative):
        return "townSimpleMean"
    if abs(float(aggregate_value) - total) <= max(absolute, abs(total) * relative):
        return "townSum"
    return "other"


def _validate_ratio_components(
    metric_id: str,
    metric: dict[str, Any],
    aggregation: dict[str, Any],
    summary: Counter[str],
) -> None:
    field = str(aggregation.get("ratioComponentsField") or "ratioComponents")
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict)]
    component_rows = [row for row in rows if isinstance(row.get(field), dict)]
    if not component_rows:
        return

    numeric_rows = [row for row in rows if _finite(row.get("value"))]
    assert len(component_rows) == len(numeric_rows), (
        f"Componenti rapporto parziali {metric_id}: {len(component_rows)}/{len(numeric_rows)} righe numeriche"
    )

    absolute = float(aggregation.get("absoluteTolerance", 1e-7))
    relative = float(aggregation.get("relativeTolerance", 1e-10))
    non_zero = bool(aggregation.get("denominatorMustBeNonZero", True))
    scales: set[float] = set()
    numerators: list[float] = []
    denominators: list[float] = []

    for row in component_rows:
        town = str(row.get("town") or "?")
        payload = row[field]
        numerator = payload.get("numerator")
        denominator = payload.get("denominator")
        assert isinstance(numerator, dict) and isinstance(denominator, dict), (
            f"Componenti rapporto incompleti {metric_id}/{town}"
        )
        numerator_value = numerator.get("value")
        denominator_value = denominator.get("value")
        scale = payload.get("scale", 1.0)
        assert _finite(numerator_value) and _finite(denominator_value) and _finite(scale), (
            f"Componenti rapporto non numerici {metric_id}/{town}"
        )
        if non_zero:
            assert float(denominator_value) != 0.0, f"Denominatore nullo {metric_id}/{town}"
        expected = float(numerator_value) / float(denominator_value) * float(scale)
        _assert_close(
            float(row["value"]),
            expected,
            absolute=absolute,
            relative=relative,
            label=f"Formula rapporto {metric_id}/{town}",
        )
        numerators.append(float(numerator_value))
        denominators.append(float(denominator_value))
        scales.add(float(scale))

    assert len(scales) == 1, f"Scale rapporto non uniformi {metric_id}: {sorted(scales)}"
    denominator_total = sum(denominators)
    if non_zero:
        assert denominator_total != 0.0, f"Denominatore aggregato nullo {metric_id}"
    expected_aggregate = sum(numerators) / denominator_total * next(iter(scales))
    aggregate = metric.get("aggregate")
    assert isinstance(aggregate, dict) and _finite(aggregate.get("value")), (
        f"Aggregato rapporto mancante/non numerico {metric_id}"
    )
    _assert_close(
        float(aggregate["value"]),
        expected_aggregate,
        absolute=absolute,
        relative=relative,
        label=f"Aggregato ponderato {metric_id}",
    )
    if aggregation.get("requireDeclaredAggregateForRatioComponents") is True:
        assert metric.get("meta", {}).get("comparisonReference") == "aggregate", (
            f"Rapporto ponderato senza comparisonReference=aggregate: {metric_id}"
        )

    summary["ratioComponentMetrics"] += 1
    summary["ratioComponentRows"] += len(component_rows)


def validate_visual_runtime_contract(path: Path | str = DEFAULT_VISUAL_GRAMMAR) -> dict[str, bool]:
    """Lock visible generic comparison semantics to the A4 contract."""
    text = Path(path).read_text(encoding="utf-8")
    required = {
        "hoverUsesFormatter": "hoverLabel.textContent",
        "hoverFormatterCall": "formatAxis(value, unit)",
        "ariaFormatterCall": "formatAxis(aggregate?.value, unit)",
        "legendUsesResolvedReference": "aggregate?.label || 'Versilia'",
        "missingVisibleLabel": "Dato non disponibile",
        "notApplicableVisibleLabel": "Non applicabile",
        "missingToken": "headline: 'n.d.'",
        "notApplicableToken": "headline: 'n.a.'",
    }
    for label, needle in required.items():
        assert needle in text, f"Contratto runtime visuale non rispettato: {label}"
    return {label: True for label in required}


def validate_visualization_content_contract(
    data_path: Path | str = DEFAULT_DATA,
    contract_path: Path | str = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    data_path = Path(data_path)
    contract_path = Path(contract_path)
    data = load_json(data_path)
    contract = load_json(contract_path)

    assert contract.get("schemaVersion") == 1, "Visualization contract schemaVersion inatteso"
    assert contract.get("scope", {}).get("noMetricInventory") is True, (
        "Il contratto A4 non deve diventare un secondo inventario di metriche"
    )

    units = contract.get("units")
    assert isinstance(units, dict) and units, "Contratto A4 senza unità"
    for token, spec in units.items():
        assert isinstance(token, str) and token, "Token unità vuoto"
        assert isinstance(spec, dict), f"Spec unità non-oggetto: {token}"
        assert isinstance(spec.get("family"), str) and spec["family"], f"Famiglia unità mancante: {token}"
        assert isinstance(spec.get("fractionDigits"), int) and spec["fractionDigits"] >= 0, (
            f"Precisione unità non valida: {token}"
        )
        assert isinstance(spec.get("suffix"), str), f"Suffix unità non valido: {token}"
        assert isinstance(spec.get("genericSurface"), bool), f"genericSurface non booleano: {token}"

    missing = contract.get("missingData", {})
    assert missing.get("mustRemainDistinct") is True
    assert missing.get("nullToken") != missing.get("notApplicableToken"), (
        "Dato mancante e non applicabile devono restare distinti"
    )
    assert missing.get("nullLabel") != missing.get("notApplicableLabel")

    polarity = contract.get("polarity", {})
    allowed_polarity = set(polarity.get("allowed") or [])
    assert allowed_polarity == {"neutral", "positive", "negative"}, allowed_polarity
    assert polarity.get("rankingOrder") == "descending-numeric"
    assert polarity.get("colorMeaning") == "theme-not-quality"
    assert polarity.get("interpretationOnly") is True

    comparison = contract.get("comparison", {})
    allowed_references = set(comparison.get("allowedReferences") or [])
    allowed_differences = set(comparison.get("allowedDifferenceModes") or [])
    assert allowed_references == {"aggregate"}, allowed_references
    assert comparison.get("fallbackWhenOmitted") == "simple-mean-available-towns"
    assert comparison.get("defaultDifferenceMode") == "relativePercent"
    assert allowed_differences == {"percentagePoints", "absolute", "shareOfAggregate"}

    aggregation = contract.get("aggregation")
    assert isinstance(aggregation, dict), "Contratto A4 senza regole di aggregazione"
    assert aggregation.get("ratioFormula") == "sum(numerator) / sum(denominator) * scale"
    assert aggregation.get("requireDeclaredAggregateForRatioComponents") is True
    assert aggregation.get("denominatorMustBeNonZero") is True
    assert _finite(aggregation.get("absoluteTolerance")) and float(aggregation["absoluteTolerance"]) > 0
    assert _finite(aggregation.get("relativeTolerance")) and float(aggregation["relativeTolerance"]) > 0

    benchmarks = contract.get("benchmarks", {})
    required_benchmark_fields = tuple(benchmarks.get("requiredFields") or [])
    benchmark_value_fields = tuple(benchmarks.get("valueFields") or [])
    assert required_benchmark_fields
    assert benchmark_value_fields

    metrics = data.get("metrics")
    assert isinstance(metrics, dict) and metrics, f"Catalogo metriche vuoto: {data_path}"

    summary: Counter[str] = Counter()
    unit_counts: Counter[str] = Counter()
    composite_counts: Counter[str] = Counter()
    aggregate_shapes: Counter[str] = Counter()

    for metric_id, metric in metrics.items():
        assert isinstance(metric, dict), f"Metrica non-oggetto: {metric_id}"
        meta = metric.get("meta")
        assert isinstance(meta, dict), f"Meta non-oggetto: {metric_id}"

        for field, token in (
            ("meta.unit", meta.get("unit")),
            ("meta.summaryUnit", meta.get("summaryUnit")),
        ):
            if token in (None, ""):
                continue
            assert token in units, f"Unità non governata {metric_id}/{field}: {token}"
            unit_counts[str(token)] += 1

        normalized = meta.get("normalized")
        normalized_unit = normalized.get("unit") if isinstance(normalized, dict) else None
        if normalized_unit not in (None, ""):
            _governed_unit(normalized_unit, units, f"{metric_id}/meta.normalized.unit", unit_counts)

        metric_polarity = meta.get("polarity")
        assert metric_polarity in allowed_polarity, (
            f"Polarità non governata {metric_id}: {metric_polarity!r}"
        )

        reference = meta.get("comparisonReference")
        if reference in (None, ""):
            summary["fallbackComparisonReference"] += 1
        else:
            assert reference in allowed_references, (
                f"comparisonReference non governato {metric_id}: {reference}"
            )
            summary["explicitComparisonReference"] += 1

        difference = meta.get("comparisonDifference")
        if difference not in (None, ""):
            assert difference in allowed_differences, (
                f"comparisonDifference non governato {metric_id}: {difference}"
            )

        benchmark = meta.get("benchmark")
        if benchmark is not None:
            assert isinstance(benchmark, dict), f"Benchmark non-oggetto: {metric_id}"
            missing_fields = [
                field
                for field in required_benchmark_fields
                if benchmark.get(field) in (None, "")
            ]
            assert not missing_fields, f"Benchmark incompleto {metric_id}: {missing_fields}"
            assert any(
                _finite(benchmark.get(field))
                for field in benchmark_value_fields
            ), f"Benchmark senza valore numerico Toscana/Italia: {metric_id}"
            summary["benchmarkMetrics"] += 1

        aggregate = metric.get("aggregate")
        assert isinstance(aggregate, dict), f"Aggregato mancante/non-oggetto: {metric_id}"
        for part_index, part in enumerate(aggregate.get("parts") or []):
            if isinstance(part, dict):
                _governed_unit(
                    part.get("unit"),
                    units,
                    f"{metric_id}/aggregate.parts[{part_index}].unit",
                    unit_counts,
                )

        composite = str(meta.get("compositeType") or "").strip()
        if composite:
            composite_counts[composite] += 1
            summary["compositeMetrics"] += 1

        rows = metric.get("rows", [])
        assert isinstance(rows, list), f"Rows non-lista: {metric_id}"
        for index, row in enumerate(rows):
            assert isinstance(row, dict), f"Riga non-oggetto {metric_id}[{index}]"
            summary["rows"] += 1
            if row.get(missing.get("notApplicableFlag", "notApplicable")):
                assert row.get("value") is None, (
                    f"Riga non applicabile con value numerico: {metric_id}/{row.get('town') or index}"
                )
                summary["notApplicableRows"] += 1
            elif row.get("value") is None:
                summary["missingRows"] += 1

            row_normalized = row.get("normalized")
            if isinstance(row_normalized, dict):
                row_unit = row_normalized.get("unit")
                _governed_unit(
                    row_unit,
                    units,
                    f"{metric_id}/{row.get('town') or index}/normalized.unit",
                    unit_counts,
                )
                if normalized_unit not in (None, "") and row_unit not in (None, ""):
                    assert row_unit == normalized_unit, (
                        f"Unità normalizzata incoerente {metric_id}/{row.get('town') or index}: "
                        f"{row_unit} != {normalized_unit}"
                    )

            for part_index, part in enumerate(row.get("parts") or []):
                if isinstance(part, dict):
                    _governed_unit(
                        part.get("unit"),
                        units,
                        f"{metric_id}/{row.get('town') or index}/parts[{part_index}].unit",
                        unit_counts,
                    )

        _validate_ratio_components(metric_id, metric, aggregation, summary)
        aggregate_shapes[
            _classify_aggregate(
                metric,
                absolute=float(aggregation["absoluteTolerance"]),
                relative=float(aggregation["relativeTolerance"]),
            )
        ] += 1
        summary["metrics"] += 1

    return {
        "metrics": int(summary["metrics"]),
        "rows": int(summary["rows"]),
        "benchmarkMetrics": int(summary["benchmarkMetrics"]),
        "compositeMetrics": int(summary["compositeMetrics"]),
        "explicitComparisonReference": int(summary["explicitComparisonReference"]),
        "fallbackComparisonReference": int(summary["fallbackComparisonReference"]),
        "missingRows": int(summary["missingRows"]),
        "notApplicableRows": int(summary["notApplicableRows"]),
        "ratioComponentMetrics": int(summary["ratioComponentMetrics"]),
        "ratioComponentRows": int(summary["ratioComponentRows"]),
        "unitCount": len(unit_counts),
        "units": dict(sorted(unit_counts.items())),
        "compositeTypes": dict(sorted(composite_counts.items())),
        "aggregateShapes": dict(sorted(aggregate_shapes.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--visual-grammar", type=Path, default=DEFAULT_VISUAL_GRAMMAR)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    report = validate_visualization_content_contract(args.data, args.contract)
    runtime = validate_visual_runtime_contract(args.visual_grammar)
    report["runtimeContractChecks"] = len(runtime)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(
        "A4 visualization/content contract: "
        f"{report['metrics']} metriche · {report['rows']} righe · "
        f"{report['explicitComparisonReference']} confronti aggregati espliciti · "
        f"{report['fallbackComparisonReference']} fallback media semplice · "
        f"{report['ratioComponentMetrics']} rapporti ponderati verificati · "
        f"{report['missingRows']} n.d. · {report['notApplicableRows']} n.a."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
