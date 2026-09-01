#!/usr/bin/env python3
"""Blocca i Social Kit che divergono dai dataset canonici dell'Osservatorio.

Il controllo e' intenzionalmente ridondante rispetto al renderer: rilegge il
pacchetto gia' generato e lo confronta con una copia immutata dei dataset
canonici. In questo modo un errore nel renderer, una trasformazione non
tracciata o una modifica manuale dei valori non puo' arrivare all'upload come
pacchetto pubblicabile.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "social-kit" / "dist"
DEFAULT_SITE = ROOT / "data" / "site-data.json"
DEFAULT_CLIMATE = ROOT / "data" / "meteo-clima-minmax-poc.json"
TOLERANCE = 1e-8


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(actual: Any, expected: Any) -> bool:
    try:
        return math.isclose(float(actual), float(expected), rel_tol=TOLERANCE, abs_tol=TOLERANCE)
    except (TypeError, ValueError):
        return False


def fmt_it(value: float, decimals: int = 0) -> str:
    raw = f"{value:,.{decimals}f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_value(value: float, unit: str, signed: bool = False) -> str:
    prefix = "+" if signed and value > 0 else ""
    if unit == "percent":
        return f"{prefix}{fmt_it(value, 1)}%"
    if unit == "currency":
        return f"{prefix}{fmt_it(value, 0)} €"
    if unit == "celsius":
        return f"{prefix}{fmt_it(value, 1)} °C"
    if unit == "percentage_points":
        return f"{prefix}{fmt_it(value, 1)} punti"
    if unit == "per1000":
        return f"{prefix}{fmt_it(value, 1)} ogni 1.000"
    if unit == "per10k":
        return f"{prefix}{fmt_it(value, 1)} ogni 10.000"
    if unit == "minutes":
        return f"{prefix}{fmt_it(value, 1)} min"
    if unit == "years":
        return f"{prefix}{fmt_it(value, 1)} anni"
    decimals = 0 if float(value).is_integer() or unit in {"number", "people"} else 1
    return prefix + fmt_it(value, decimals)


def visible_text(svg_path: Path) -> str:
    root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    return " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))


def site_metric(site: dict[str, Any], metric_key: str) -> dict[str, Any]:
    metric = site.get("metrics", {}).get(metric_key)
    if not isinstance(metric, dict):
        raise KeyError(f"Indicatore canonico inesistente: {metric_key}")
    return metric


def canonical_site_values(metric: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in metric.get("rows", []):
        town = row.get("town")
        value = row.get("value")
        if not town or value is None:
            raise ValueError(f"Valore canonico corrente mancante per {town or 'Comune sconosciuto'}")
        values[str(town)] = float(value)
    return values


def canonical_site_series(metric: dict[str, Any], town: str) -> dict[int, float]:
    row = next((item for item in metric.get("rows", []) if item.get("town") == town), None)
    if not row or not row.get("series"):
        return {}
    years = [int(year) for year in row["series"].get("years", [])]
    values = [float(value) for value in row["series"].get("values", [])]
    if len(years) != len(values):
        raise ValueError(f"Serie canonica incoerente: {town}")
    return dict(zip(years, values))


def canonical_climate_values(climate: dict[str, Any], metric_key: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for town, item in climate.get("municipalities", {}).items():
        latest = item.get("latestComplete", {})
        if metric_key not in latest:
            raise ValueError(f"Valore climatico corrente mancante: {town} / {metric_key}")
        values[town] = float(latest[metric_key])
    return values


def canonical_climate_series(climate: dict[str, Any], metric_key: str, town: str) -> dict[int, float]:
    item = climate.get("municipalities", {}).get(town)
    if not item:
        return {}
    years = [int(year) for year in item.get("years", [])]
    values = [float(value) for value in item.get(metric_key, [])]
    if len(years) != len(values):
        raise ValueError(f"Serie climatica incoerente: {town} / {metric_key}")
    return dict(zip(years, values))


def aggregate_mode(unit: str) -> str:
    return "sum" if unit in {"number", "people"} else "mean"


def aggregate(values: list[float], mode: str) -> float:
    return sum(values) if mode == "sum" else mean(values)


def check_equal(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{label}: {actual!r} != {expected!r}")


def check_numeric(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if not close(actual, expected):
        errors.append(f"{label}: {actual!r} != {expected!r}")


def check_comparison(
    errors: list[str],
    post_id: str,
    comparison: dict[str, Any] | None,
    current_values: dict[str, float],
    series_for: Any,
    unit: str,
) -> int:
    if not comparison:
        return 0
    checks = 0
    comp_type = comparison.get("type")
    rows = comparison.get("rows") or []
    if set(row.get("town") for row in rows) != set(current_values):
        errors.append(f"{post_id}: Comuni del confronto non coerenti con i valori canonici")
        return checks

    if comp_type == "base_year":
        match = re.search(r"(\d{4})", str(comparison.get("label", "")))
        if not match:
            errors.append(f"{post_id}: anno base non ricavabile dal confronto")
            return checks
        base_year = int(match.group(1))
        display_unit = comparison.get("display_unit")
        expected_display_unit = "percentage_points" if unit == "percent" else "percent"
        check_equal(errors, f"{post_id}: unita confronto", display_unit, expected_display_unit)
        for row in rows:
            town = row["town"]
            series = series_for(town)
            if base_year not in series:
                errors.append(f"{post_id}: {town} non ha il {base_year} nella serie canonica")
                continue
            base = series[base_year]
            current = current_values[town]
            delta = current - base
            display = delta if unit == "percent" else (delta / base * 100.0 if base else 0.0)
            check_numeric(errors, f"{post_id}: {town} base", row.get("base"), base)
            check_numeric(errors, f"{post_id}: {town} corrente confronto", row.get("current"), current)
            check_numeric(errors, f"{post_id}: {town} delta", row.get("delta"), delta)
            check_numeric(errors, f"{post_id}: {town} display", row.get("display"), display)
            checks += 4
        return checks

    if comp_type == "period_mean":
        label = str(comparison.get("label", ""))
        years = [int(value) for value in re.findall(r"\d{4}", label)]
        if len(years) < 4:
            errors.append(f"{post_id}: periodi del confronto non ricavabili")
            return checks
        base_from, base_to, current_from, current_to = years[:4]
        for row in rows:
            town = row["town"]
            series = series_for(town)
            base_values = [series[year] for year in range(base_from, base_to + 1) if year in series]
            curr_values = [series[year] for year in range(current_from, current_to + 1) if year in series]
            if len(base_values) != base_to - base_from + 1 or len(curr_values) != current_to - current_from + 1:
                errors.append(f"{post_id}: periodi canonici incompleti per {town}")
                continue
            base = mean(base_values)
            current = mean(curr_values)
            check_numeric(errors, f"{post_id}: {town} media base", row.get("base"), base)
            check_numeric(errors, f"{post_id}: {town} media corrente", row.get("current"), current)
            check_numeric(errors, f"{post_id}: {town} differenza", row.get("display"), current - base)
            checks += 3
        return checks

    errors.append(f"{post_id}: formula di confronto non autorizzata: {comp_type!r}")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default=str(DEFAULT_DIST))
    parser.add_argument("--canonical-site", default=str(DEFAULT_SITE))
    parser.add_argument("--canonical-climate", default=str(DEFAULT_CLIMATE))
    args = parser.parse_args()

    dist = Path(args.dist)
    site_path = Path(args.canonical_site)
    climate_path = Path(args.canonical_climate)
    site = load(site_path)
    climate = load(climate_path) if climate_path.exists() else {}
    manifest = load(dist / "manifest.json")

    errors: list[str] = []
    numeric_checks = 0
    rendered_checks = 0
    post_reports: list[dict[str, Any]] = []

    for item in manifest.get("items", []):
        post_id = item.get("post_id")
        post_dir = dist / str(post_id)
        provenance_path = post_dir / "provenienza.json"
        if not provenance_path.exists():
            errors.append(f"{post_id}: provenienza.json mancante")
            continue
        provenance = load(provenance_path)
        dataset = provenance.get("dataset") or {}
        dataset_path = dataset.get("path")
        metric_key = provenance.get("metric")

        if dataset_path == "data/site-data.json":
            metric = site_metric(site, str(metric_key))
            meta = metric.get("meta", {})
            current_values = canonical_site_values(metric)
            series_for = lambda town, metric=metric: canonical_site_series(metric, town)
            unit = str(meta.get("unit"))
            check_equal(errors, f"{post_id}: versione dataset", dataset.get("version"), site.get("version"))
            check_equal(errors, f"{post_id}: stato dataset", dataset.get("status"), "published")
            check_equal(errors, f"{post_id}: tema", provenance.get("theme"), meta.get("theme"))
            check_equal(errors, f"{post_id}: fonte", provenance.get("source"), meta.get("source"))
            check_equal(errors, f"{post_id}: URL fonte", provenance.get("source_url"), metric.get("sourceUrl") or meta.get("sourceUrl"))
            check_equal(errors, f"{post_id}: metodo", provenance.get("method"), metric.get("method", {}))
            try:
                expected_year = int(meta.get("year"))
            except (TypeError, ValueError):
                errors.append(f"{post_id}: anno canonico non numerico: {meta.get('year')!r}")
                expected_year = None
            if expected_year is not None:
                check_equal(errors, f"{post_id}: anno corrente", provenance.get("current_year"), expected_year)
        elif dataset_path == "data/meteo-clima-minmax-poc.json":
            if metric_key not in {"tmin", "tmax"}:
                errors.append(f"{post_id}: metrica climatica non autorizzata: {metric_key}")
                continue
            current_values = canonical_climate_values(climate, str(metric_key))
            series_for = lambda town, climate=climate, key=str(metric_key): canonical_climate_series(climate, key, town)
            unit = "celsius"
            check_equal(errors, f"{post_id}: versione dataset climatico", dataset.get("version"), climate.get("version"))
            check_equal(errors, f"{post_id}: stato dataset climatico", dataset.get("status"), climate.get("status"))
            years = sorted(set.intersection(*(set(series_for(town)) for town in current_values))) if current_values else []
            if years:
                check_equal(errors, f"{post_id}: anno climatico corrente", provenance.get("current_year"), years[-1])
        else:
            errors.append(f"{post_id}: dataset non autorizzato: {dataset_path!r}")
            continue

        actual_values = provenance.get("current_values") or {}
        if set(actual_values) != set(current_values):
            errors.append(f"{post_id}: copertura comunale diversa dal dataset canonico")
        for town, expected in current_values.items():
            if town not in actual_values:
                continue
            check_numeric(errors, f"{post_id}: valore corrente {town}", actual_values[town], expected)
            numeric_checks += 1

        history = provenance.get("history") or {}
        mode = aggregate_mode(unit)
        for year_text, actual in history.items():
            year = int(year_text)
            values: list[float] = []
            for town in current_values:
                series = series_for(town)
                if year not in series:
                    errors.append(f"{post_id}: {town} non ha il {year} nella serie canonica")
                    values = []
                    break
                values.append(series[year])
            if values:
                expected = aggregate(values, mode)
                check_numeric(errors, f"{post_id}: storico aggregato {year}", actual, expected)
                numeric_checks += 1

        numeric_checks += check_comparison(
            errors,
            str(post_id),
            provenance.get("comparison"),
            current_values,
            series_for,
            unit,
        )

        cards = item.get("cards") or []
        if not cards:
            errors.append(f"{post_id}: manifest senza card")
        else:
            current_svg = post_dir / "cards" / f"{cards[0]['filename']}.svg"
            if not current_svg.exists():
                errors.append(f"{post_id}: SVG della card corrente mancante")
            else:
                text = visible_text(current_svg)
                for town, value in current_values.items():
                    expected_text = fmt_value(value, unit)
                    if town not in text or expected_text not in text:
                        errors.append(f"{post_id}: card corrente non contiene il valore canonico {town} = {expected_text}")
                    rendered_checks += 1

            comparison = provenance.get("comparison")
            if comparison and len(cards) >= 3:
                change_svg = post_dir / "cards" / f"{cards[2]['filename']}.svg"
                if not change_svg.exists():
                    errors.append(f"{post_id}: SVG della card confronto mancante")
                else:
                    text = visible_text(change_svg)
                    display_unit = comparison.get("display_unit") or "percentage_points"
                    for row in comparison.get("rows") or []:
                        expected_text = fmt_value(float(row["display"]), str(display_unit), True)
                        if row["town"] not in text or expected_text not in text:
                            errors.append(f"{post_id}: card confronto non contiene {row['town']} = {expected_text}")
                        rendered_checks += 1

        post_reports.append({
            "post_id": post_id,
            "metric": metric_key,
            "dataset": dataset_path,
            "towns": len(current_values),
            "status": "checked",
        })

    report = {
        "status": "FAIL" if errors else "PASS",
        "policy": "social-data-fidelity-v1",
        "canonical": {
            "site_data": {"path": str(site_path), "sha256": sha256(site_path), "version": site.get("version")},
            "climate_data": {"path": str(climate_path), "sha256": sha256(climate_path) if climate_path.exists() else None, "version": climate.get("version")},
        },
        "posts_checked": len(post_reports),
        "numeric_checks": numeric_checks,
        "rendered_value_checks": rendered_checks,
        "posts": post_reports,
        "errors": errors,
    }
    (dist / "data-fidelity.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print("SOCIAL DATA FIDELITY: FAIL")
        for error in errors:
            print(f"- {error}")
        print("Nessun pacchetto deve essere pubblicato o caricato come Social Kit valido.")
        return 1

    print(
        f"SOCIAL DATA FIDELITY: PASS · {len(post_reports)} caroselli · "
        f"{numeric_checks} controlli numerici · {rendered_checks} controlli sui valori renderizzati"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
