#!/usr/bin/env python3
"""A3.5 lotto 5: companion strutturali da componenti già versionati.

Il lotto non introduce nuovi valori pubblici. Espone soltanto componenti
numerici già congelati o già materializzati da lotti A3.5 precedenti, così
numeratore/denominatore e assoluto/normalizzato diventano verificabili dalla
struttura del catalogo effettivo.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import materialize_a3_5_openbdap_ratio_components as openbdap

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
LIA_PATH = ROOT / "data" / "source-snapshots" / "lia-v1.4.0.json"
DEMOGRAPHY_PATH = ROOT / "data" / "source-snapshots" / "istat-demography-lotto-a-2026-08.json"
AGRICULTURE_PATH = ROOT / "data" / "source-snapshots" / "istat-agricoltura-territorio-2020.json"
ASIA_PATH = ROOT / "data" / "source-snapshots" / "agid-asia-agcom-2026-08.json"
FRAME_PATH = ROOT / "data" / "source-snapshots" / "economia-prodotta-frame-sbs-v134-2021-2023.json"

OPENBDAP_TARGETS = tuple(openbdap.TARGET_METRICS)
CENSUS_TARGETS = ("cohabitingHouseholds", "oldAgeIndex")
AGRICULTURE_TARGETS = (
    "agriculturalUsedArea",
    "averageAgriculturalFarmSize",
    "irrigatedAgriculturalArea",
)
BUSINESS_TARGETS = (
    "employeesPerLocalUnit",
    "localEmployeesChange",
    "localUnitsChange",
    "industryValueAddedShare",
    "industryWorkerShare",
)
SOURCE_TARGETS = CENSUS_TARGETS + AGRICULTURE_TARGETS + BUSINESS_TARGETS

ABSOLUTE_NORMALIZED_SOURCE_TARGETS = {
    "cohabitingHouseholds",
    "oldAgeIndex",
    "averageAgriculturalFarmSize",
    *BUSINESS_TARGETS,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _num(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result


def _assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance):
        raise RuntimeError(f"{label}: {actual} != {expected}")


def _rows_by_town(metric: dict[str, Any], metric_id: str) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"{metric_id}: rows mancanti")
    result = {
        str(row["town"]): row
        for row in rows
        if isinstance(row, dict) and row.get("town")
    }
    if len(result) != 7:
        raise RuntimeError(f"{metric_id}: perimetro comunale atteso 7/7")
    return result


def _ratio_value(numerator: float, denominator: float, scale: float, transform: str) -> float:
    if denominator == 0:
        raise RuntimeError("Denominatore nullo")
    if transform == "ratio":
        return numerator / denominator * scale
    if transform == "pct_change":
        return (numerator / denominator - 1.0) * 100.0
    raise RuntimeError(f"Trasformazione non supportata: {transform}")


def _component_payload(
    *,
    numerator: float,
    denominator: float,
    normalized: float,
    absolute: float,
    scale: float,
    transform: str,
    formula: str,
    source: str,
    source_snapshot: str,
    reference_year: str,
    include_absolute_normalized: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "referenceYear": reference_year,
        "source": source,
        "sourceSnapshot": source_snapshot,
        "formula": formula,
        "transform": transform,
        "scale": scale,
        "numerator": numerator,
        "denominator": denominator,
    }
    if include_absolute_normalized:
        payload["absolute"] = absolute
        payload["normalized"] = normalized
    return payload


def _attach_source_component(
    *,
    row: dict[str, Any],
    metric_id: str,
    numerator: float,
    denominator: float,
    normalized: float,
    absolute: float,
    scale: float,
    transform: str,
    formula: str,
    source: str,
    source_snapshot: str,
    reference_year: str,
    tolerance: float = 1e-8,
) -> None:
    expected = _ratio_value(numerator, denominator, scale, transform)
    _assert_close(normalized, expected, metric_id, tolerance=tolerance)
    row["sourceBackedComponents"] = _component_payload(
        numerator=numerator,
        denominator=denominator,
        normalized=normalized,
        absolute=absolute,
        scale=scale,
        transform=transform,
        formula=formula,
        source=source,
        source_snapshot=source_snapshot,
        reference_year=reference_year,
        include_absolute_normalized=metric_id in ABSOLUTE_NORMALIZED_SOURCE_TARGETS,
    )


def _apply_openbdap_scale_companions(metrics: dict[str, Any]) -> int:
    rows_enriched = 0
    for metric_id in OPENBDAP_TARGETS:
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Metrica OpenBDAP mancante: {metric_id}")
        for town, row in _rows_by_town(metric, metric_id).items():
            payload = row.get("ratioComponents")
            if not isinstance(payload, dict):
                raise RuntimeError(f"{metric_id}/{town}: ratioComponents del lotto 2 mancanti")
            expected = openbdap._ratio_value(payload)
            openbdap._assert_close(float(row["value"]), expected, f"{metric_id}/{town}")
            numerator = payload.get("numerator")
            if not isinstance(numerator, dict):
                raise RuntimeError(f"{metric_id}/{town}: numeratore strutturato mancante")
            row["openBdapScaleCompanion"] = {
                "year": payload.get("year"),
                "source": payload.get("source"),
                "sourceUrl": payload.get("sourceUrl"),
                "sourceSnapshot": payload.get("sourceSnapshot"),
                "absolute": _num(numerator.get("value"), f"{metric_id}/{town}: absolute"),
                "normalized": _num(row.get("value"), f"{metric_id}/{town}: normalized"),
            }
            rows_enriched += 1
    return rows_enriched


def _apply_census(metrics: dict[str, Any], lia: dict[str, Any], demography: dict[str, Any]) -> int:
    raw_lia = lia.get("raw", {}).get("istat2023")
    if not isinstance(raw_lia, list) or len(raw_lia) != 7:
        raise RuntimeError("Snapshot LIA privo di 7 righe Istat 2023")
    lia_by_town = {str(row["town"]): row for row in raw_lia}

    demo_towns = demography.get("posas", {}).get("towns")
    if not isinstance(demo_towns, dict) or len(demo_towns) != 7:
        raise RuntimeError("Snapshot demografico privo di 7 Comuni")

    rows_enriched = 0

    metric = metrics["cohabitingHouseholds"]
    for town, row in _rows_by_town(metric, "cohabitingHouseholds").items():
        raw = lia_by_town[town]
        numerator = _num(raw["PF9"], f"cohabitingHouseholds/{town}: PF9")
        denominator = _num(raw["PF1"], f"cohabitingHouseholds/{town}: PF1")
        normalized = _num(row["value"], f"cohabitingHouseholds/{town}: value")
        _attach_source_component(
            row=row,
            metric_id="cohabitingHouseholds",
            numerator=numerator,
            denominator=denominator,
            normalized=normalized,
            absolute=numerator,
            scale=100.0,
            transform="ratio",
            formula="PF9 / PF1 × 100",
            source="Istat — Censimento permanente della popolazione",
            source_snapshot="data/source-snapshots/lia-v1.4.0.json",
            reference_year="2023",
        )
        rows_enriched += 1

    metric = metrics["oldAgeIndex"]
    for town, row in _rows_by_town(metric, "oldAgeIndex").items():
        history = demo_towns.get(town)
        if not isinstance(history, list):
            raise RuntimeError(f"oldAgeIndex/{town}: serie demografica mancante")
        raw = next((item for item in history if int(item.get("year", -1)) == 2026), None)
        if not isinstance(raw, dict):
            raise RuntimeError(f"oldAgeIndex/{town}: componenti 2026 mancanti")
        numerator = _num(raw["age65plus"], f"oldAgeIndex/{town}: age65plus")
        denominator = _num(raw["age0to14"], f"oldAgeIndex/{town}: age0to14")
        normalized = _num(row["value"], f"oldAgeIndex/{town}: value")
        _attach_source_component(
            row=row,
            metric_id="oldAgeIndex",
            numerator=numerator,
            denominator=denominator,
            normalized=normalized,
            absolute=numerator,
            scale=100.0,
            transform="ratio",
            formula="residenti 65+ / residenti 0–14 × 100",
            source="Istat — popolazione per classi di età",
            source_snapshot="data/source-snapshots/istat-demography-lotto-a-2026-08.json",
            reference_year="2026",
            tolerance=0.051,
        )
        rows_enriched += 1

    return rows_enriched


def _apply_agriculture(metrics: dict[str, Any], agriculture: dict[str, Any]) -> int:
    towns = agriculture.get("towns")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot agricoltura territorio privo di 7 Comuni")

    rows_enriched = 0
    configs = {
        "agriculturalUsedArea": {
            "numerator": lambda raw: raw["sauLocalizedHa"],
            "denominator": lambda raw: raw["municipalAreaKm2"] * 100.0,
            "absolute": lambda raw: raw["sauLocalizedHa"],
            "normalized": lambda row: row["normalized"]["value"],
            "scale": 100.0,
            "formula": "SAU localizzata / superficie comunale in ettari × 100",
        },
        "averageAgriculturalFarmSize": {
            "numerator": lambda raw: raw["sauCenterHa"],
            "denominator": lambda raw: raw["farmsWithSau"],
            "absolute": lambda raw: raw["sauCenterHa"],
            "normalized": lambda row: row["value"],
            "scale": 1.0,
            "formula": "SAU delle aziende / aziende con SAU",
        },
        "irrigatedAgriculturalArea": {
            "numerator": lambda raw: raw["irrigatedAreaHa"],
            "denominator": lambda raw: raw["sauCenterHa"],
            "absolute": lambda raw: raw["irrigatedAreaHa"],
            "normalized": lambda row: row["normalized"]["value"],
            "scale": 100.0,
            "formula": "superficie irrigata / SAU delle aziende × 100",
        },
    }

    for metric_id, cfg in configs.items():
        metric = metrics[metric_id]
        rows = metric.get("rows")
        if not isinstance(rows, list) or len(rows) != 7:
            raise RuntimeError(f"{metric_id}: attese 7 righe")
        for row in rows:
            code = str(row.get("code") or "")
            raw = towns.get(code)
            if not isinstance(raw, dict):
                raise RuntimeError(f"{metric_id}/{code}: snapshot agricolo mancante")
            numerator = _num(cfg["numerator"](raw), f"{metric_id}/{code}: numerator")
            denominator = _num(cfg["denominator"](raw), f"{metric_id}/{code}: denominator")
            absolute = _num(cfg["absolute"](raw), f"{metric_id}/{code}: absolute")
            normalized = _num(cfg["normalized"](row), f"{metric_id}/{code}: normalized")
            _attach_source_component(
                row=row,
                metric_id=metric_id,
                numerator=numerator,
                denominator=denominator,
                normalized=normalized,
                absolute=absolute,
                scale=float(cfg["scale"]),
                transform="ratio",
                formula=str(cfg["formula"]),
                source="Istat — 7° Censimento generale dell'agricoltura 2020",
                source_snapshot="data/source-snapshots/istat-agricoltura-territorio-2020.json",
                reference_year="2020",
            )
            rows_enriched += 1
    return rows_enriched


def _frame_2023(frame: dict[str, Any]) -> dict[str, dict[str, list[Any]]]:
    columns = frame.get("columns")
    rows = frame.get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise RuntimeError("Snapshot Frame SBS non valido")
    idx = {str(name): pos for pos, name in enumerate(columns)}
    required = {"year", "scope", "town", "personsEmployed", "valueAddedThousandEuro"}
    if not required.issubset(idx):
        raise RuntimeError(f"Colonne Frame SBS mancanti: {sorted(required - set(idx))}")
    result: dict[str, dict[str, list[Any]]] = {}
    for raw in rows:
        if int(raw[idx["year"]]) != 2023:
            continue
        town = str(raw[idx["town"]])
        scope = str(raw[idx["scope"]])
        result.setdefault(town, {})[scope] = raw
    if len(result) != 7 or any(not {"total", "industry"}.issubset(scopes) for scopes in result.values()):
        raise RuntimeError("Snapshot Frame SBS 2023 incompleto")
    result["__index__"] = idx  # type: ignore[assignment]
    return result


def _apply_business(metrics: dict[str, Any], asia: dict[str, Any], frame: dict[str, Any]) -> int:
    asia_rows = asia.get("towns")
    if not isinstance(asia_rows, list) or len(asia_rows) != 7:
        raise RuntimeError("Snapshot ASIA privo di 7 Comuni")
    asia_by_town = {str(item["town"]): item for item in asia_rows}

    frame_data = _frame_2023(frame)
    idx = frame_data.pop("__index__")  # type: ignore[arg-type]

    rows_enriched = 0
    for metric_id in ("employeesPerLocalUnit", "localEmployeesChange", "localUnitsChange"):
        for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
            raw = asia_by_town[town].get("asia")
            if not isinstance(raw, dict):
                raise RuntimeError(f"{metric_id}/{town}: ASIA mancante")
            units = raw.get("localUnits")
            employees = raw.get("employeesAverageAnnual")
            if not isinstance(units, list) or not isinstance(employees, list) or len(units) != 6 or len(employees) != 6:
                raise RuntimeError(f"{metric_id}/{town}: serie ASIA inattesa")

            if metric_id == "employeesPerLocalUnit":
                numerator = _num(employees[-1], f"{metric_id}/{town}: employees 2023")
                denominator = _num(units[-1], f"{metric_id}/{town}: units 2023")
                scale, transform = 1.0, "ratio"
                formula = "addetti medi annui 2023 / unità locali attive 2023"
            elif metric_id == "localEmployeesChange":
                numerator = _num(employees[-1], f"{metric_id}/{town}: employees 2023")
                denominator = _num(employees[0], f"{metric_id}/{town}: employees 2018")
                scale, transform = 100.0, "pct_change"
                formula = "((addetti 2023 / addetti 2018) − 1) × 100"
            else:
                numerator = _num(units[-1], f"{metric_id}/{town}: units 2023")
                denominator = _num(units[0], f"{metric_id}/{town}: units 2018")
                scale, transform = 100.0, "pct_change"
                formula = "((unità locali 2023 / unità locali 2018) − 1) × 100"

            normalized = _num(row["value"], f"{metric_id}/{town}: value")
            _attach_source_component(
                row=row,
                metric_id=metric_id,
                numerator=numerator,
                denominator=denominator,
                normalized=normalized,
                absolute=numerator,
                scale=scale,
                transform=transform,
                formula=formula,
                source="Istat — ASIA unità locali",
                source_snapshot="data/source-snapshots/agid-asia-agcom-2026-08.json",
                reference_year="2018–2023" if transform == "pct_change" else "2023",
            )
            rows_enriched += 1

    for metric_id, column in (
        ("industryValueAddedShare", "valueAddedThousandEuro"),
        ("industryWorkerShare", "personsEmployed"),
    ):
        for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
            scopes = frame_data[town]
            industry = scopes["industry"]
            total = scopes["total"]
            numerator = _num(industry[idx[column]], f"{metric_id}/{town}: industry")
            denominator = _num(total[idx[column]], f"{metric_id}/{town}: total")
            normalized = _num(row["value"], f"{metric_id}/{town}: value")
            _attach_source_component(
                row=row,
                metric_id=metric_id,
                numerator=numerator,
                denominator=denominator,
                normalized=normalized,
                absolute=numerator,
                scale=100.0,
                transform="ratio",
                formula=(
                    "valore aggiunto industria / valore aggiunto totale × 100"
                    if metric_id == "industryValueAddedShare"
                    else "addetti industria / addetti totali × 100"
                ),
                source="Istat — Frame SBS Territoriale",
                source_snapshot="data/source-snapshots/economia-prodotta-frame-sbs-v134-2021-2023.json",
                reference_year="2023",
            )
            rows_enriched += 1

    return rows_enriched


def apply_enrichment(
    site: dict[str, Any],
    lia: dict[str, Any],
    demography: dict[str, Any],
    agriculture: dict[str, Any],
    asia: dict[str, Any],
    frame: dict[str, Any],
) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")

    missing = [metric_id for metric_id in OPENBDAP_TARGETS + SOURCE_TARGETS if metric_id not in metrics]
    if missing:
        raise RuntimeError(f"Metriche lotto 5 mancanti: {missing}")

    openbdap_rows = _apply_openbdap_scale_companions(metrics)
    census_rows = _apply_census(metrics, lia, demography)
    agriculture_rows = _apply_agriculture(metrics, agriculture)
    business_rows = _apply_business(metrics, asia, frame)

    return {
        "metricsEnriched": len(OPENBDAP_TARGETS) + len(SOURCE_TARGETS),
        "rowsEnriched": openbdap_rows + census_rows + agriculture_rows + business_rows,
        "openBdapScalePairs": len(OPENBDAP_TARGETS),
        "censusPairs": 4,
        "agriculturePairs": 4,
        "businessPairs": 10,
        "pairsAcquired": len(OPENBDAP_TARGETS) + 4 + 4 + 10,
    }


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_enrichment(
        site,
        load(LIA_PATH),
        load(DEMOGRAPHY_PATH),
        load(AGRICULTURE_PATH),
        load(ASIA_PATH),
        load(FRAME_PATH),
    )
    save(SITE_PATH, site)
    print(
        "A3.5 source-backed companions: "
        f"{summary['metricsEnriched']} metriche; {summary['pairsAcquired']} coppie integrate "
        f"({summary['openBdapScalePairs']} OpenBDAP assoluto/normalizzato, "
        f"{summary['censusPairs']} census, {summary['agriculturePairs']} agricoltura, "
        f"{summary['businessPairs']} business)."
    )


if __name__ == "__main__":
    main()
