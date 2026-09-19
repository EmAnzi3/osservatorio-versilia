#!/usr/bin/env python3
"""A3.5 lotto 3: integra dimensioni Frame SBS Territoriale già congelate.

Il lotto usa esclusivamente gli snapshot Istat Frame SBS v1.34.0 già versionati.
Non modifica i valori pubblici: aggiunge strutture di enrichment verificabili per
categorie economiche, assoluto/normalizzato e, dove applicabile,
numeratore/denominatore.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "economia-prodotta-frame-sbs-v134.json"
YEAR = 2023
SOURCE = "Istat — Frame SBS Territoriale"
SOURCE_SNAPSHOT = "data/source-snapshots/economia-prodotta-frame-sbs-v134.json"

TARGET_METRICS = (
    "businessTurnover",
    "businessValueAdded",
    "labourProductivity",
    "turnoverPerPersonEmployed",
    "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee",
    "labourCost",
    "grossOperatingMargin",
)
RATIO_TARGETS = (
    "labourProductivity",
    "turnoverPerPersonEmployed",
    "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee",
)
SCOPES = ("total", "industry", "services")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_snapshot_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise RuntimeError("Manifest Frame SBS privo di parts")
    for name in parts:
        part_path = SNAPSHOT_PATH.parent / str(name)
        part = load(part_path)
        columns = part.get("columns")
        raw_rows = part.get("rows")
        if not isinstance(columns, list) or not isinstance(raw_rows, list):
            raise RuntimeError(f"Snapshot Frame SBS non valido: {part_path}")
        for raw in raw_rows:
            if not isinstance(raw, list) or len(raw) != len(columns):
                raise RuntimeError(f"Riga Frame SBS non allineata: {part_path}")
            rows.append(dict(zip(columns, raw, strict=True)))
    return rows


def _rows_by_town(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica Frame SBS senza rows")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Riga metrica Frame SBS non-oggetto")
        town = str(row.get("town") or "").strip()
        if not town or town in out:
            raise RuntimeError(f"Comune mancante o duplicato: {town!r}")
        out[town] = row
    return out


def _snapshot_index(rows: list[dict[str, Any]]) -> dict[tuple[int, str, str], dict[str, Any]]:
    out: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (int(row["year"]), str(row["scope"]), str(row["town"]))
        if key in out:
            raise RuntimeError(f"Riga Frame SBS duplicata: {key}")
        out[key] = row
    return out


def _num(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RuntimeError(f"{label}: valore numerico mancante")
    return float(value)


def _assert_close(actual: float, expected: float, label: str, *, abs_tol: float = 1e-6, rel_tol: float = 1e-10) -> None:
    tolerance = max(abs_tol, abs(float(expected)) * rel_tol)
    if abs(float(actual) - float(expected)) > tolerance:
        raise RuntimeError(f"{label}: {actual} != {expected} (tol={tolerance})")


def _formula_tolerance(metric_id: str) -> tuple[float, float]:
    # Gli aggregati monetari delle tavole comunali sono congelati in migliaia
    # di euro, mentre alcuni rapporti Istat sono pubblicati direttamente.
    # Le tolleranze coprono esclusivamente tale arrotondamento della fonte.
    if metric_id in {"businessValueAdded", "labourProductivity"}:
        return 10.0, 3e-4
    if metric_id == "averageGrossRemunerationPerEmployee":
        return 50.0, 2e-3
    if metric_id == "valueAddedTurnoverShare":
        return 0.06, 3e-3
    return 1e-6, 1e-10


def _assert_ratio(metric_id: str, observed: float, numerator: float, denominator: float, scale: float, label: str) -> None:
    if denominator == 0:
        raise RuntimeError(f"{label}: denominatore nullo")
    expected = numerator / denominator * scale
    abs_tol, rel_tol = _formula_tolerance(metric_id)
    _assert_close(observed, expected, label, abs_tol=abs_tol, rel_tol=rel_tol)


def _category_payload(metric: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    scopes = row.get("economicScopes")
    if not isinstance(scopes, dict) or set(scopes) != set(SCOPES):
        raise RuntimeError(f"{row.get('town')}: economicScopes Frame SBS incompleto")
    categories = []
    for key in SCOPES:
        item = scopes[key]
        if not isinstance(item, dict):
            raise RuntimeError(f"{row.get('town')}/{key}: scope non-oggetto")
        value = _num(item.get("value"), f"{row.get('town')}/{key}")
        categories.append(
            {
                "key": key,
                "label": str(item.get("label") or key),
                "value": value,
                "unit": metric.get("meta", {}).get("unit"),
                "series": item.get("series"),
            }
        )
    return {
        "dimension": "categorie_specifiche",
        "year": YEAR,
        "source": SOURCE,
        "sourceUrl": metric.get("sourceUrl"),
        "sourceSnapshot": SOURCE_SNAPSHOT,
        "categories": categories,
    }


def _components(metric_id: str, raw: dict[str, Any]) -> dict[str, float]:
    persons = _num(raw.get("personsEmployed"), f"{metric_id}: personsEmployed")
    employees = _num(raw.get("employees"), f"{metric_id}: employees")
    turnover_eur = _num(raw.get("turnoverThousandEuro"), f"{metric_id}: turnover") * 1000.0
    value_added_eur = _num(raw.get("valueAddedThousandEuro"), f"{metric_id}: value added") * 1000.0
    wages_eur = _num(raw.get("grossWagesThousandEuro"), f"{metric_id}: gross wages") * 1000.0
    labour_cost_raw = raw.get("labourCostThousandEuro")
    labour_cost_eur = _num(labour_cost_raw, f"{metric_id}: labour cost") * 1000.0
    gross_margin_eur = value_added_eur - labour_cost_eur
    if persons <= 0 or employees <= 0 or turnover_eur == 0:
        raise RuntimeError(f"{metric_id}: denominatore Frame SBS non valido")
    return {
        "persons": persons,
        "employees": employees,
        "turnoverEur": turnover_eur,
        "valueAddedEur": value_added_eur,
        "wagesEur": wages_eur,
        "labourCostEur": labour_cost_eur,
        "grossMarginEur": gross_margin_eur,
    }


def _absolute_normalized(metric_id: str, raw: dict[str, Any], row_value: float) -> dict[str, Any]:
    c = _components(metric_id, raw)

    if metric_id == "businessTurnover":
        absolute = c["turnoverEur"] / 1_000_000.0
        normalized = c["turnoverEur"] / c["persons"]
        denominator = ("Addetti", c["persons"])
        normalized_label = "Fatturato per addetto"
    elif metric_id in {"businessValueAdded", "labourProductivity"}:
        absolute = c["valueAddedEur"] / 1_000_000.0
        normalized = _num(raw.get("valueAddedPerPersonEmployedThousandEuro"), f"{metric_id}: VA/addetto") * 1000.0
        denominator = ("Addetti", c["persons"])
        normalized_label = "Valore aggiunto per addetto"
    elif metric_id == "turnoverPerPersonEmployed":
        absolute = c["turnoverEur"] / 1_000_000.0
        normalized = c["turnoverEur"] / c["persons"]
        denominator = ("Addetti", c["persons"])
        normalized_label = "Fatturato per addetto"
    elif metric_id == "valueAddedTurnoverShare":
        absolute = c["valueAddedEur"] / 1_000_000.0
        normalized = _num(raw.get("valueAddedTurnoverPercent"), f"{metric_id}: VA/fatturato")
        denominator = ("Fatturato", c["turnoverEur"])
        normalized_label = "Valore aggiunto sul fatturato"
    elif metric_id == "averageGrossRemunerationPerEmployee":
        absolute = c["wagesEur"] / 1_000_000.0
        normalized = _num(raw.get("averageGrossRemunerationPerEmployeeThousandEuro"), f"{metric_id}: retribuzione/dipendente") * 1000.0
        denominator = ("Dipendenti", c["employees"])
        normalized_label = "Retribuzione media lorda per dipendente"
    elif metric_id == "labourCost":
        absolute = c["labourCostEur"] / 1_000_000.0
        normalized = c["labourCostEur"] / c["persons"]
        denominator = ("Addetti", c["persons"])
        normalized_label = "Costo del lavoro per addetto"
    elif metric_id == "grossOperatingMargin":
        absolute = c["grossMarginEur"] / 1_000_000.0
        normalized = c["grossMarginEur"] / c["persons"]
        denominator = ("Addetti", c["persons"])
        normalized_label = "Margine operativo lordo per addetto"
    else:
        raise KeyError(metric_id)

    if metric_id in {"businessTurnover", "businessValueAdded", "labourCost", "grossOperatingMargin"}:
        _assert_close(row_value, absolute, f"{metric_id}: valore assoluto pubblico")
    else:
        _assert_close(row_value, normalized, f"{metric_id}: valore normalizzato pubblico")

    if metric_id == "valueAddedTurnoverShare":
        numerator_for_formula = c["valueAddedEur"]
        scale = 100.0
    elif metric_id == "averageGrossRemunerationPerEmployee":
        numerator_for_formula = c["wagesEur"]
        scale = 1.0
    elif metric_id in {"businessValueAdded", "labourProductivity"}:
        numerator_for_formula = c["valueAddedEur"]
        scale = 1.0
    elif metric_id in {"businessTurnover", "turnoverPerPersonEmployed"}:
        numerator_for_formula = c["turnoverEur"]
        scale = 1.0
    elif metric_id == "labourCost":
        numerator_for_formula = c["labourCostEur"]
        scale = 1.0
    else:
        numerator_for_formula = c["grossMarginEur"]
        scale = 1.0

    _assert_ratio(
        metric_id,
        normalized,
        numerator_for_formula,
        denominator[1],
        scale,
        f"{metric_id}: assoluto/normalizzato",
    )

    return {
        "dimension": "assoluto_normalizzato",
        "year": YEAR,
        "source": SOURCE,
        "sourceSnapshot": SOURCE_SNAPSHOT,
        "absolute": {
            "label": "Grandezza assoluta collegata",
            "value": absolute,
            "unit": "millionCurrency",
        },
        "normalized": {
            "label": normalized_label,
            "value": normalized,
            "unit": "percent" if metric_id == "valueAddedTurnoverShare" else "currency",
            "denominator": {
                "label": denominator[0],
                "value": denominator[1],
            },
        },
    }


def _ratio_payload(metric_id: str, raw: dict[str, Any], row_value: float) -> dict[str, Any]:
    c = _components(metric_id, raw)
    if metric_id == "labourProductivity":
        numerator = ("Valore aggiunto", c["valueAddedEur"], "currency")
        denominator = ("Addetti", c["persons"], "number")
        scale = 1.0
    elif metric_id == "turnoverPerPersonEmployed":
        numerator = ("Fatturato", c["turnoverEur"], "currency")
        denominator = ("Addetti", c["persons"], "number")
        scale = 1.0
    elif metric_id == "valueAddedTurnoverShare":
        numerator = ("Valore aggiunto", c["valueAddedEur"], "currency")
        denominator = ("Fatturato", c["turnoverEur"], "currency")
        scale = 100.0
    elif metric_id == "averageGrossRemunerationPerEmployee":
        numerator = ("Retribuzioni lorde", c["wagesEur"], "currency")
        denominator = ("Dipendenti", c["employees"], "number")
        scale = 1.0
    else:
        raise KeyError(metric_id)

    _assert_ratio(metric_id, row_value, numerator[1], denominator[1], scale, f"{metric_id}: numeratore/denominatore")
    return {
        "dimension": "numeratore_denominatore",
        "year": YEAR,
        "source": SOURCE,
        "sourceSnapshot": SOURCE_SNAPSHOT,
        "scale": scale,
        "numerator": {"label": numerator[0], "value": numerator[1], "unit": numerator[2]},
        "denominator": {"label": denominator[0], "value": denominator[1], "unit": denominator[2]},
    }


def apply_enrichment(site: dict[str, Any], snapshot_manifest: dict[str, Any]) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    missing = [metric_id for metric_id in TARGET_METRICS if metric_id not in metrics]
    if missing:
        raise RuntimeError(f"Metriche Frame SBS A3.5 mancanti: {missing}")

    manifest_towns = snapshot_manifest.get("towns")
    if not isinstance(manifest_towns, list) or len(manifest_towns) != 7:
        raise RuntimeError("Manifest Frame SBS senza perimetro 7/7")
    expected_towns = {str(item.get("name")) for item in manifest_towns if isinstance(item, dict)}

    raw_rows = load_snapshot_rows(snapshot_manifest)
    index = _snapshot_index(raw_rows)
    enriched_rows = 0

    for metric_id in TARGET_METRICS:
        metric = metrics[metric_id]
        rows = _rows_by_town(metric)
        if set(rows) != expected_towns:
            raise RuntimeError(f"{metric_id}: perimetro comunale non allineato allo snapshot")

        for town, row in rows.items():
            raw = index.get((YEAR, "total", town))
            if not isinstance(raw, dict):
                raise RuntimeError(f"{metric_id}/{town}: riga Frame SBS {YEAR}/total mancante")
            row_value = _num(row.get("value"), f"{metric_id}/{town}: value")
            row["frameSbsCategories"] = _category_payload(metric, row)
            row["frameSbsScaleCompanion"] = _absolute_normalized(metric_id, raw, row_value)
            if metric_id in RATIO_TARGETS:
                row["frameSbsRatioComponents"] = _ratio_payload(metric_id, raw, row_value)
            enriched_rows += 1

    return {
        "metricsEnriched": len(TARGET_METRICS),
        "towns": len(expected_towns),
        "rowsEnriched": enriched_rows,
        "categoryPairs": len(TARGET_METRICS),
        "absoluteNormalizedPairs": len(TARGET_METRICS),
        "ratioPairs": len(RATIO_TARGETS),
        "pairsAcquired": len(TARGET_METRICS) * 2 + len(RATIO_TARGETS),
    }


def main() -> None:
    site = load(SITE_PATH)
    snapshot = load(SNAPSHOT_PATH)
    summary = apply_enrichment(site, snapshot)
    save(SITE_PATH, site)
    print(
        "A3.5 Frame SBS: "
        f"{summary['metricsEnriched']} metriche × {summary['towns']} comuni; "
        f"{summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate "
        f"({summary['categoryPairs']} categorie, "
        f"{summary['absoluteNormalizedPairs']} assoluto/normalizzato, "
        f"{summary['ratioPairs']} numeratore/denominatore)."
    )


if __name__ == "__main__":
    main()
