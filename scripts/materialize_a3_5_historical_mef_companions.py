#!/usr/bin/env python3
"""A3.5 lotto 6: serie e companion MEF da snapshot già versionati.

Il lotto non modifica valori, testi o rendering pubblici. Aggiunge soltanto
strutture di enrichment ignorate dalla UI e verificabili contro snapshot
ufficiali già presenti nella repository.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
FRAME_MANIFEST_PATH = ROOT / "data" / "source-snapshots" / "economia-prodotta-frame-sbs-v134.json"
ASIA_PATH = ROOT / "data" / "source-snapshots" / "agid-asia-agcom-2026-08.json"
DEMOGRAPHY_PATH = ROOT / "data" / "source-snapshots" / "istat-demography-lotto-a-2026-08.json"
BILANCI_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
MEF_INCOME_PATH = ROOT / "data" / "source-snapshots" / "mef-income-lotto-a-2024.json"
MUNICIPAL_IRPEF_PATH = ROOT / "data" / "source-snapshots" / "costi-fiscalita-redditi-draft-2026-08.json"

HISTORY_TARGETS = (
    "industryValueAddedShare",
    "industryWorkerShare",
    "localEmployeesChange",
    "localUnitsChange",
    "populationChange",
    "rigidExpenditureShare",
)
BUSINESS_CATEGORY_TARGETS = (
    "industryValueAddedShare",
    "industryWorkerShare",
)
MEF_RATIO_TARGETS = (
    "incomeSourceProfile",
    "pensionIncomeShare",
)
MUNICIPAL_IRPEF_TARGET = "municipalIrpef"


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


def _attach_history(
    row: dict[str, Any],
    *,
    metric_id: str,
    points: list[tuple[int, float]],
    source: str,
    source_snapshot: str,
    note: str,
    tolerance: float = 1e-8,
) -> None:
    if len(points) < 2:
        raise RuntimeError(f"{metric_id}/{row.get('town')}: storico insufficiente")
    years = [int(year) for year, _value in points]
    if len(set(years)) != len(years) or years != sorted(years):
        raise RuntimeError(f"{metric_id}/{row.get('town')}: annualità storiche non valide")
    values = [_num(value, f"{metric_id}/{row.get('town')}/{year}") for year, value in points]
    _assert_close(
        _num(row.get("value"), f"{metric_id}/{row.get('town')}: value"),
        values[-1],
        f"{metric_id}/{row.get('town')}: ultimo punto storico",
        tolerance=tolerance,
    )
    row["a3History"] = {
        "source": source,
        "sourceSnapshot": source_snapshot,
        "note": note,
        "series": [
            {"year": year, "value": value}
            for year, value in zip(years, values, strict=True)
        ],
    }


def _load_frame_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise RuntimeError("Manifest Frame SBS privo di parts")
    out: list[dict[str, Any]] = []
    for name in parts:
        part_path = FRAME_MANIFEST_PATH.parent / str(name)
        part = load(part_path)
        columns = part.get("columns")
        rows = part.get("rows")
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise RuntimeError(f"Snapshot Frame SBS non valido: {part_path}")
        for raw in rows:
            if not isinstance(raw, list) or len(raw) != len(columns):
                raise RuntimeError(f"Riga Frame SBS non allineata: {part_path}")
            out.append(dict(zip(columns, raw, strict=True)))
    return out


def _apply_business(
    metrics: dict[str, Any],
    frame_manifest: dict[str, Any],
    asia: dict[str, Any],
) -> tuple[int, int]:
    frame_rows = _load_frame_rows(frame_manifest)
    frame_index = {
        (int(raw["year"]), str(raw["scope"]), str(raw["town"])): raw
        for raw in frame_rows
    }
    years = list(range(2015, 2024))
    source = "Istat — Frame SBS Territoriale"
    frame_snapshot = "data/source-snapshots/economia-prodotta-frame-sbs-v134.json"

    history_pairs = 0
    category_pairs = 0
    for metric_id, column in (
        ("industryValueAddedShare", "valueAddedThousandEuro"),
        ("industryWorkerShare", "personsEmployed"),
    ):
        for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
            points: list[tuple[int, float]] = []
            for year in years:
                industry = frame_index[(year, "industry", town)]
                total = frame_index[(year, "total", town)]
                numerator = _num(industry.get(column), f"{metric_id}/{town}/{year}: industry")
                denominator = _num(total.get(column), f"{metric_id}/{town}/{year}: total")
                if denominator == 0:
                    raise RuntimeError(f"{metric_id}/{town}/{year}: denominatore nullo")
                points.append((year, numerator / denominator * 100.0))
            _attach_history(
                row,
                metric_id=metric_id,
                points=points,
                source=source,
                source_snapshot=frame_snapshot,
                note="Serie calcolata dagli stessi aggregati comunali industria/totale usati dal valore corrente.",
                tolerance=1e-10,
            )

            industry = frame_index[(2023, "industry", town)]
            services = frame_index[(2023, "services", town)]
            total = frame_index[(2023, "total", town)]
            denominator = _num(total.get(column), f"{metric_id}/{town}: total")
            categories = []
            for key, label, raw in (
                ("industry", "Industria", industry),
                ("services", "Servizi", services),
            ):
                value = _num(raw.get(column), f"{metric_id}/{town}/{key}") / denominator * 100.0
                categories.append({"key": key, "label": label, "value": value, "unit": "percent"})
            _assert_close(
                _num(row.get("value"), f"{metric_id}/{town}: value"),
                categories[0]["value"],
                f"{metric_id}/{town}: categoria industria",
                tolerance=1e-10,
            )
            row["businessCategoryBreakdown"] = {
                "year": 2023,
                "source": source,
                "sourceSnapshot": frame_snapshot,
                "categories": categories,
            }
        history_pairs += 1
        category_pairs += 1

    asia_rows = asia.get("towns")
    if not isinstance(asia_rows, list) or len(asia_rows) != 7:
        raise RuntimeError("Snapshot ASIA privo di 7 Comuni")
    asia_by_town = {str(item["town"]): item["asia"] for item in asia_rows}

    for metric_id, field in (
        ("localEmployeesChange", "employeesAverageAnnual"),
        ("localUnitsChange", "localUnits"),
    ):
        for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
            raw = asia_by_town.get(town)
            if not isinstance(raw, dict):
                raise RuntimeError(f"{metric_id}/{town}: ASIA mancante")
            raw_years = raw.get("years")
            raw_values = raw.get(field)
            if not isinstance(raw_years, list) or not isinstance(raw_values, list):
                raise RuntimeError(f"{metric_id}/{town}: serie ASIA mancante")
            if len(raw_years) != len(raw_values) or len(raw_years) < 2:
                raise RuntimeError(f"{metric_id}/{town}: serie ASIA non allineata")
            base = _num(raw_values[0], f"{metric_id}/{town}: baseline")
            if base == 0:
                raise RuntimeError(f"{metric_id}/{town}: baseline nulla")
            points = [
                (int(year), (_num(value, f"{metric_id}/{town}/{year}") / base - 1.0) * 100.0)
                for year, value in zip(raw_years, raw_values, strict=True)
            ]
            _attach_history(
                row,
                metric_id=metric_id,
                points=points,
                source="Istat — ASIA unità locali",
                source_snapshot="data/source-snapshots/agid-asia-agcom-2026-08.json",
                note=f"Variazione cumulata rispetto al {int(raw_years[0])}, coerente con la definizione del valore pubblico.",
                tolerance=1e-10,
            )
        history_pairs += 1

    return history_pairs, category_pairs


def _apply_population_change(metrics: dict[str, Any], demography: dict[str, Any]) -> int:
    towns = demography.get("posas", {}).get("towns")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot demografico POSAS privo di 7 Comuni")

    metric_id = "populationChange"
    for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
        history = towns.get(town)
        if not isinstance(history, list) or len(history) < 2:
            raise RuntimeError(f"{metric_id}/{town}: storico POSAS mancante")
        ordered = sorted(history, key=lambda item: int(item["year"]))
        base_year = int(ordered[0]["year"])
        if base_year != 2019:
            raise RuntimeError(f"{metric_id}/{town}: baseline attesa 2019")
        base = _num(ordered[0].get("population"), f"{metric_id}/{town}: popolazione 2019")
        points = [
            (
                int(item["year"]),
                (_num(item.get("population"), f"{metric_id}/{town}/{item['year']}") / base - 1.0) * 100.0,
            )
            for item in ordered
        ]
        _attach_history(
            row,
            metric_id=metric_id,
            points=points,
            source="Istat — popolazione residente",
            source_snapshot="data/source-snapshots/istat-demography-lotto-a-2026-08.json",
            note="Variazione cumulata della popolazione rispetto al 1° gennaio 2019.",
            tolerance=1e-10,
        )
    return 1


def _apply_rigid_expenditure_history(metrics: dict[str, Any], bilanci: dict[str, Any]) -> int:
    metric_snapshot = bilanci.get("metrics", {}).get("rigidExpenditureShare")
    if not isinstance(metric_snapshot, dict):
        raise RuntimeError("Snapshot rigidExpenditureShare mancante")
    years = metric_snapshot.get("years")
    values = metric_snapshot.get("values")
    if not isinstance(years, list) or len(years) < 2 or not isinstance(values, dict):
        raise RuntimeError("Storico rigidExpenditureShare non valido")

    metric_id = "rigidExpenditureShare"
    for town, row in _rows_by_town(metrics[metric_id], metric_id).items():
        town_values = values.get(town)
        if not isinstance(town_values, dict):
            raise RuntimeError(f"{metric_id}/{town}: storico mancante")
        points = [
            (int(year), _num(town_values.get(str(year)), f"{metric_id}/{town}/{year}"))
            for year in years
        ]
        _attach_history(
            row,
            metric_id=metric_id,
            points=points,
            source="OpenBDAP — indicatori di bilancio",
            source_snapshot="data/source-snapshots/bilanci-v1.6.0.json",
            note="Serie ufficiale dell'indicatore di rigidità della spesa congelata nello snapshot OpenBDAP.",
            tolerance=1e-8,
        )
    return 1


def _attach_mef_components(
    row: dict[str, Any],
    *,
    metric_id: str,
    numerator: float,
    denominator: float,
    normalized: float,
    absolute: float,
    scale: float,
    formula: str,
    source_snapshot: str,
) -> None:
    if denominator == 0:
        raise RuntimeError(f"{metric_id}/{row.get('town')}: denominatore nullo")
    expected = numerator / denominator * scale
    _assert_close(normalized, expected, f"{metric_id}/{row.get('town')}: formula", tolerance=1e-10)
    _assert_close(
        _num(row.get("value"), f"{metric_id}/{row.get('town')}: value"),
        normalized,
        f"{metric_id}/{row.get('town')}: valore pubblico",
        tolerance=1e-10,
    )
    row["mefScaleComponents"] = {
        "source": "Dipartimento delle Finanze — MEF",
        "sourceSnapshot": source_snapshot,
        "formula": formula,
        "scale": scale,
        "numerator": numerator,
        "denominator": denominator,
        "absolute": absolute,
        "normalized": normalized,
    }


def _apply_mef_income(metrics: dict[str, Any], mef: dict[str, Any]) -> int:
    towns = mef.get("towns")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot redditi MEF privo di 7 Comuni")

    for town, row in _rows_by_town(metrics["incomeSourceProfile"], "incomeSourceProfile").items():
        raw = towns.get(town)
        if not isinstance(raw, dict):
            raise RuntimeError(f"incomeSourceProfile/{town}: snapshot mancante")
        sources = raw.get("incomeSources")
        if not isinstance(sources, list):
            raise RuntimeError(f"incomeSourceProfile/{town}: incomeSources mancanti")
        employment = next((item for item in sources if item.get("key") == "employment"), None)
        if not isinstance(employment, dict):
            raise RuntimeError(f"incomeSourceProfile/{town}: fonte employment mancante")
        numerator = _num(employment.get("amountEuro"), f"incomeSourceProfile/{town}: amount")
        denominator = _num(employment.get("frequency"), f"incomeSourceProfile/{town}: frequency")
        normalized = numerator / denominator
        _attach_mef_components(
            row,
            metric_id="incomeSourceProfile",
            numerator=numerator,
            denominator=denominator,
            normalized=normalized,
            absolute=numerator,
            scale=1.0,
            formula="ammontare redditi da lavoro dipendente / contribuenti con quella fonte",
            source_snapshot="data/source-snapshots/mef-income-lotto-a-2024.json",
        )

    for town, row in _rows_by_town(metrics["pensionIncomeShare"], "pensionIncomeShare").items():
        raw = towns.get(town)
        if not isinstance(raw, dict):
            raise RuntimeError(f"pensionIncomeShare/{town}: snapshot mancante")
        pension = raw.get("pensionIncome")
        total = raw.get("totalIncome")
        if not isinstance(pension, dict) or not isinstance(total, dict):
            raise RuntimeError(f"pensionIncomeShare/{town}: componenti mancanti")
        numerator = _num(pension.get("amountEuro"), f"pensionIncomeShare/{town}: pension")
        denominator = _num(total.get("amountEuro"), f"pensionIncomeShare/{town}: total")
        normalized = numerator / denominator * 100.0
        _attach_mef_components(
            row,
            metric_id="pensionIncomeShare",
            numerator=numerator,
            denominator=denominator,
            normalized=normalized,
            absolute=numerator,
            scale=100.0,
            formula="ammontare redditi da pensione / reddito complessivo × 100",
            source_snapshot="data/source-snapshots/mef-income-lotto-a-2024.json",
        )

    return 4


def _apply_municipal_irpef(metrics: dict[str, Any], fiscal: dict[str, Any]) -> int:
    towns = fiscal.get("municipalIrpef", {}).get("towns")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot addizionale comunale IRPEF privo di 7 Comuni")
    scenario_income = 20_000.0

    for town, row in _rows_by_town(metrics[MUNICIPAL_IRPEF_TARGET], MUNICIPAL_IRPEF_TARGET).items():
        raw = towns.get(town)
        if not isinstance(raw, dict):
            raise RuntimeError(f"municipalIrpef/{town}: snapshot mancante")
        amounts = raw.get("amounts")
        if not isinstance(amounts, dict):
            raise RuntimeError(f"municipalIrpef/{town}: scenari mancanti")
        absolute = _num(amounts.get("20000"), f"municipalIrpef/{town}: 20000")
        _assert_close(
            _num(row.get("value"), f"municipalIrpef/{town}: value"),
            absolute,
            f"municipalIrpef/{town}: valore pubblico",
            tolerance=1e-10,
        )
        row["municipalIrpefScaleCompanion"] = {
            "year": 2025,
            "source": "Dipartimento delle Finanze — MEF",
            "sourceSnapshot": "data/source-snapshots/costi-fiscalita-redditi-draft-2026-08.json",
            "scenarioIncome": scenario_income,
            "absolute": absolute,
            "normalized": absolute / scenario_income * 100.0,
            "normalizedUnit": "percent",
        }
    return 1


def apply_enrichment(
    site: dict[str, Any],
    frame_manifest: dict[str, Any],
    asia: dict[str, Any],
    demography: dict[str, Any],
    bilanci: dict[str, Any],
    mef_income: dict[str, Any],
    municipal_irpef: dict[str, Any],
) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")

    required = set(HISTORY_TARGETS) | set(BUSINESS_CATEGORY_TARGETS) | set(MEF_RATIO_TARGETS) | {MUNICIPAL_IRPEF_TARGET}
    missing = sorted(required - set(metrics))
    if missing:
        raise RuntimeError(f"Metriche lotto 6 mancanti: {missing}")

    business_history, business_categories = _apply_business(metrics, frame_manifest, asia)
    demographic_history = _apply_population_change(metrics, demography)
    openbdap_history = _apply_rigid_expenditure_history(metrics, bilanci)
    mef_pairs = _apply_mef_income(metrics, mef_income)
    municipal_pairs = _apply_municipal_irpef(metrics, municipal_irpef)

    pairs = business_history + business_categories + demographic_history + openbdap_history + mef_pairs + municipal_pairs
    if pairs != 13:
        raise RuntimeError(f"Conteggio coppie lotto 6 inatteso: {pairs}")

    return {
        "metricsEnriched": len(required),
        "historyPairs": business_history + demographic_history + openbdap_history,
        "businessCategoryPairs": business_categories,
        "mefPairs": mef_pairs,
        "municipalIrpefPairs": municipal_pairs,
        "pairsAcquired": pairs,
    }


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_enrichment(
        site,
        load(FRAME_MANIFEST_PATH),
        load(ASIA_PATH),
        load(DEMOGRAPHY_PATH),
        load(BILANCI_PATH),
        load(MEF_INCOME_PATH),
        load(MUNICIPAL_IRPEF_PATH),
    )
    save(SITE_PATH, site)
    print(
        "A3.5 historical + MEF companions: "
        f"{summary['metricsEnriched']} metriche; {summary['pairsAcquired']} coppie integrate "
        f"({summary['historyPairs']} storiche, {summary['businessCategoryPairs']} categorie business, "
        f"{summary['mefPairs']} companion MEF, {summary['municipalIrpefPairs']} addizionale IRPEF)."
    )


if __name__ == "__main__":
    main()
