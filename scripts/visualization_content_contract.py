#!/usr/bin/env python3
"""Validate the A4 visualization/content contract against a catalog.

The contract is global and declarative: it describes formatting and comparison
rules without maintaining a second inventory of metrics.
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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON non-oggetto: {path}")
    return value


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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
        if isinstance(normalized, dict) and normalized.get("unit") not in (None, ""):
            token = normalized["unit"]
            assert token in units, f"Unità normalizzata non governata {metric_id}: {token}"
            unit_counts[str(token)] += 1

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
        "unitCount": len(unit_counts),
        "units": dict(sorted(unit_counts.items())),
        "compositeTypes": dict(sorted(composite_counts.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    report = validate_visualization_content_contract(args.data, args.contract)
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
        f"{report['missingRows']} n.d. · {report['notApplicableRows']} n.a."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
