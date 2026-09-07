#!/usr/bin/env python3
"""Shared declarative content architecture for Osservatorio Versilia."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "ci" / "content-contract.json"


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def load_catalog(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    return json.loads((ROOT / contract["canonicalSources"]["catalog"]).read_text(encoding="utf-8"))


def load_source_registry(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    return json.loads((ROOT / contract["canonicalSources"]["sourceRegistry"]).read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def storage_type(metric: dict[str, Any]) -> str:
    return str(metric.get("dataStorage", {}).get("type") or "inline")


def configured_paths(group: str, contract: dict[str, Any] | None = None) -> set[Path]:
    contract = contract or load_contract()
    return {Path(path) for path in contract["pages"].get(group, [])}


def theme_membership(data: dict[str, Any]) -> dict[str, str]:
    metrics = data["metrics"]
    owners: dict[str, list[str]] = defaultdict(list)
    for theme_key, theme in data["themes"].items():
        theme_metrics = list(theme.get("metrics", []))
        duplicates = [key for key, count in Counter(theme_metrics).items() if count > 1]
        assert not duplicates, f"Metriche duplicate nel tema {theme_key}: {duplicates}"
        for metric_key in theme_metrics:
            assert metric_key in metrics, f"Metrica sconosciuta nel tema {theme_key}: {metric_key}"
            owners[metric_key].append(theme_key)

        seen_sections: set[str] = set()
        for section in theme.get("sections", []):
            section_metrics = list(section.get("metrics", []))
            duplicates = [key for key, count in Counter(section_metrics).items() if count > 1]
            assert not duplicates, f"Metriche duplicate nella sezione {theme_key}/{section.get('key')}: {duplicates}"
            for metric_key in section_metrics:
                assert metric_key in theme_metrics, (
                    f"Sezione {theme_key}/{section.get('key')} riferisce metrica fuori tema: {metric_key}"
                )
                assert metric_key not in seen_sections, (
                    f"Metrica ripetuta in più sezioni del tema {theme_key}: {metric_key}"
                )
                seen_sections.add(metric_key)

    missing = sorted(set(metrics) - set(owners))
    multiple = sorted(key for key, themes in owners.items() if len(themes) != 1)
    assert not missing, f"Metriche senza tema: {missing}"
    assert not multiple, f"Metriche assegnate a più temi: {multiple}"
    return {key: themes[0] for key, themes in owners.items()}


def route_owners(data: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[Path, str]:
    contract = contract or load_contract()
    owners: dict[Path, str] = {}

    def add(path: Path, owner: str) -> None:
        assert path not in owners, f"Route duplicata {path}: {owners[path]} e {owner}"
        owners[path] = owner

    for path in contract["pages"]["static"]:
        add(Path(path), f"static:{path}")
    for path in contract["pages"]["standalone"]:
        add(Path(path), f"standalone:{path}")
    for town in data["towns"]:
        add(Path("comuni") / slugify(town["name"]) / "index.html", f"town:{town['name']}")
    for theme_key in data["themes"]:
        add(Path("confronta") / theme_key / "index.html", f"theme:{theme_key}")
    for metric_key, metric in data["metrics"].items():
        kind = storage_type(metric)
        if kind == "special-route":
            detail_route = str(metric.get("meta", {}).get("detailRoute") or "").strip("/")
            assert detail_route, f"Route dedicata mancante: {metric_key}"
            add(Path(detail_route) / "index.html", f"special-route:{metric_key}")
        elif kind != "external-climate":
            label = str(metric.get("meta", {}).get("label") or "").strip()
            assert label, f"Label metrica mancante: {metric_key}"
            add(Path("indicatori") / slugify(label) / "index.html", f"indicator:{metric_key}")
    return owners


def expected_pages(data: dict[str, Any] | None = None, contract: dict[str, Any] | None = None) -> set[Path]:
    contract = contract or load_contract()
    data = data or load_catalog(contract)
    return set(route_owners(data, contract))


def visualization_family(metric: dict[str, Any]) -> str:
    kind = storage_type(metric)
    if kind == "special-route":
        return "special-route"
    if kind == "external-climate":
        return "external-climate"
    composite = str(metric.get("meta", {}).get("compositeType") or "").strip()
    if composite:
        return f"composite:{composite}"
    if metric.get("series") or any(row.get("series") or row.get("componentSeries") for row in metric.get("rows", [])):
        return "history"
    return "simple"


def _series_contract(series: object, owner: str) -> None:
    if not isinstance(series, dict):
        return
    years = series.get("years")
    values = series.get("values")
    if years is None and values is None:
        return
    assert isinstance(years, list) and isinstance(values, list), f"Serie non tabellare: {owner}"
    assert len(years) == len(values), f"Anni/valori disallineati: {owner}"
    assert len(years) == len({str(year) for year in years}), f"Anni duplicati: {owner}"


def validate_content_contract() -> dict[str, Any]:
    contract = load_contract()
    assert contract.get("schemaVersion") == 1
    data = load_catalog(contract)
    registry = load_source_registry(contract)

    assert isinstance(data.get("towns"), list) and data["towns"], "Catalogo comuni vuoto"
    assert isinstance(data.get("themes"), dict) and data["themes"], "Catalogo temi vuoto"
    assert isinstance(data.get("metrics"), dict) and data["metrics"], "Catalogo indicatori vuoto"

    town_names = [town["name"] for town in data["towns"]]
    assert len(town_names) == len(set(town_names)), f"Comuni duplicati: {town_names}"
    expected_towns = [town["name"] for town in registry.get("expectedTowns", [])]
    assert set(town_names) == set(expected_towns), (
        f"Perimetro comuni difforme dal registry: {sorted(town_names)} != {sorted(expected_towns)}"
    )

    membership = theme_membership(data)
    allowed_storage = set(contract["catalog"]["allowedStorageTypes"])
    external_storage = set(contract["catalog"]["externalStorageTypes"])
    storage_counts: Counter[str] = Counter()
    composite_types: set[str] = set()
    visualizations: Counter[str] = Counter()

    for metric_key, metric in data["metrics"].items():
        assert isinstance(metric, dict), f"Metrica non oggetto: {metric_key}"
        meta = metric.get("meta", {})
        assert isinstance(meta, dict), f"Meta non oggetto: {metric_key}"
        assert str(meta.get("label") or "").strip(), f"Label assente: {metric_key}"

        kind = storage_type(metric)
        assert kind in allowed_storage, f"Storage type non dichiarato per {metric_key}: {kind}"
        storage_counts[kind] += 1
        if kind == "special-route":
            assert str(meta.get("detailRoute") or "").strip("/"), f"detailRoute mancante: {metric_key}"

        declared_theme = str(meta.get("theme") or "").strip()
        if declared_theme:
            assert declared_theme == membership[metric_key], (
                f"Tema meta incoerente per {metric_key}: {declared_theme} != {membership[metric_key]}"
            )

        rows = metric.get("rows", [])
        assert isinstance(rows, list), f"Rows non lista: {metric_key}"
        seen_towns: set[str] = set()
        for index, row in enumerate(rows):
            assert isinstance(row, dict), f"Riga non oggetto: {metric_key}[{index}]"
            town = str(row.get("town") or "").strip()
            if town:
                assert town in town_names, f"Comune sconosciuto in {metric_key}: {town}"
                assert town not in seen_towns, f"Comune duplicato in {metric_key}: {town}"
                seen_towns.add(town)
            _series_contract(row.get("series"), f"{metric_key}/{town or index}/series")
            component_series = row.get("componentSeries")
            if isinstance(component_series, dict):
                for component, series in component_series.items():
                    _series_contract(series, f"{metric_key}/{town or index}/componentSeries/{component}")
        _series_contract(metric.get("series"), f"{metric_key}/series")

        composite = str(meta.get("compositeType") or "").strip()
        if composite:
            composite_types.add(composite)
        visualizations[visualization_family(metric)] += 1

    total = len(data["metrics"])
    external = sum(count for kind, count in storage_counts.items() if kind in external_storage)
    inline = total - external
    assert registry["expectedMetricCount"] == total, (registry["expectedMetricCount"], total)
    assert registry["expectedExternalMetricCount"] == external, (registry["expectedExternalMetricCount"], external)
    assert registry["expectedInlineMetricCount"] == inline, (registry["expectedInlineMetricCount"], inline)

    owners = route_owners(data, contract)
    assert owners, "Nessuna route pubblica risolta"

    frontend_paths = {
        path
        for pattern in contract["visualizations"]["frontendGlobs"]
        for path in ROOT.glob(pattern)
    }
    assert frontend_paths, "Sorgenti frontend del contratto visuale non trovate"
    frontend = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sorted(frontend_paths))
    for composite in sorted(composite_types):
        assert composite in frontend, f"Composite type senza implementazione frontend dichiarata: {composite}"

    return {
        "towns": len(town_names),
        "themes": len(data["themes"]),
        "metrics": total,
        "pages": len(owners),
        "storage": dict(sorted(storage_counts.items())),
        "visualizations": dict(sorted(visualizations.items())),
    }
