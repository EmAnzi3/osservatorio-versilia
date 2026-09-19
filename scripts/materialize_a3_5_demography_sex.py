#!/usr/bin/env python3
"""A3.5 lotto 1: integra la dimensione sesso per tre indicatori demografici."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
DEMOGRAPHY_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-demography-lotto-a-2026-08.json"
RCS_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-rcs-demography-2025.json"

TARGET_METRICS = ("population", "dependencyIndices", "foreignResidents")
SEX_GROUPS = (("men", "Maschi"), ("women", "Femmine"))
POSAS_SOURCE_URL = "https://demo.istat.it/"
RCS_SOURCE_URL = "https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rows_by_town(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("Metrica senza rows")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Riga metrica non-oggetto")
        town = str(row.get("town") or "").strip()
        if not town or town in out:
            raise RuntimeError(f"Comune mancante o duplicato: {town!r}")
        out[town] = row
    return out


def _sum_age_sex(detail: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"men": 0, "women": 0, "total": 0}
    seen_ages: set[int] = set()
    for item in detail:
        if not isinstance(item, dict):
            raise RuntimeError("POSAS ageSex: record non-oggetto")
        age = int(item["age"])
        if age in seen_ages:
            raise RuntimeError(f"POSAS ageSex: età duplicata {age}")
        seen_ages.add(age)
        men = int(item["men"])
        women = int(item["women"])
        total = int(item["total"])
        if men < 0 or women < 0 or total != men + women:
            raise RuntimeError(f"POSAS ageSex incoerente per età {age}: {item}")
        totals["men"] += men
        totals["women"] += women
        totals["total"] += total
    if not seen_ages:
        raise RuntimeError("POSAS ageSex vuoto")
    return totals


def _population_breakdown(detail: list[dict[str, Any]], *, year: int) -> dict[str, Any]:
    totals = _sum_age_sex(detail)
    total = totals["total"]
    groups = []
    for key, label in SEX_GROUPS:
        count = totals[key]
        groups.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "value": count,
                "sharePercent": count / total * 100 if total else 0.0,
            }
        )
    return {
        "dimension": "sesso",
        "year": year,
        "unit": "number",
        "source": "Istat — popolazione residente per età e sesso (POSAS)",
        "sourceUrl": POSAS_SOURCE_URL,
        "total": total,
        "groups": groups,
    }


def _dependency_for_sex(detail: list[dict[str, Any]], sex_key: str) -> dict[str, Any]:
    bands = {"age0to14": 0, "age15to64": 0, "age65plus": 0}
    for item in detail:
        age = int(item["age"])
        count = int(item[sex_key])
        if age <= 14:
            bands["age0to14"] += count
        elif age <= 64:
            bands["age15to64"] += count
        else:
            bands["age65plus"] += count
    denominator = bands["age15to64"]
    if denominator <= 0:
        raise RuntimeError(f"Denominatore 15–64 nullo per {sex_key}")
    structural = (bands["age0to14"] + bands["age65plus"]) / denominator * 100
    elderly = bands["age65plus"] / denominator * 100
    return {
        "value": structural,
        "parts": [
            {
                "key": "structural",
                "label": "Indice di dipendenza strutturale",
                "value": structural,
                "unit": "per100",
                "numerator": bands["age0to14"] + bands["age65plus"],
                "denominator": denominator,
            },
            {
                "key": "elderly",
                "label": "Indice di dipendenza degli anziani",
                "value": elderly,
                "unit": "per100",
                "numerator": bands["age65plus"],
                "denominator": denominator,
            },
        ],
        "populationBands": bands,
    }


def _dependency_breakdown(detail: list[dict[str, Any]], *, year: int) -> dict[str, Any]:
    groups = []
    for key, label in SEX_GROUPS:
        item = _dependency_for_sex(detail, key)
        groups.append({"key": key, "label": label, **item})
    return {
        "dimension": "sesso",
        "year": year,
        "unit": "per100",
        "source": "Istat — popolazione residente per età e sesso (POSAS)",
        "sourceUrl": POSAS_SOURCE_URL,
        "groups": groups,
    }


def _foreign_breakdown(citizenship: list[dict[str, Any]], *, year: int) -> dict[str, Any]:
    totals = {"men": 0, "women": 0, "total": 0}
    for item in citizenship:
        if not isinstance(item, dict):
            raise RuntimeError("RCS cittadinanza: record non-oggetto")
        men = int(item["men"])
        women = int(item["women"])
        total = int(item["total"])
        if men < 0 or women < 0 or total != men + women:
            raise RuntimeError(f"RCS cittadinanza incoerente: {item}")
        totals["men"] += men
        totals["women"] += women
        totals["total"] += total
    total = totals["total"]
    if total <= 0:
        raise RuntimeError("RCS cittadinanza: totale nullo")
    groups = []
    for key, label in SEX_GROUPS:
        count = totals[key]
        groups.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "value": count,
                "shareWithinForeignResidentsPercent": count / total * 100,
            }
        )
    return {
        "dimension": "sesso",
        "year": year,
        "unit": "number",
        "basis": "residenti di cittadinanza non italiana",
        "source": "Istat RCS — popolazione residente per cittadinanza",
        "sourceUrl": RCS_SOURCE_URL,
        "total": total,
        "groups": groups,
        "note": (
            "Le percentuali descrivono la composizione per sesso dei residenti stranieri; "
            "non sono quote calcolate sulla popolazione maschile o femminile complessiva."
        ),
    }


def _combine_age_sex(details: list[list[dict[str, Any]]]) -> list[dict[str, int]]:
    by_age: dict[int, dict[str, int]] = {}
    for detail in details:
        for item in detail:
            age = int(item["age"])
            target = by_age.setdefault(age, {"age": age, "men": 0, "women": 0, "total": 0})
            target["men"] += int(item["men"])
            target["women"] += int(item["women"])
            target["total"] += int(item["total"])
    return [by_age[age] for age in sorted(by_age)]


def _assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-7) -> None:
    if abs(float(actual) - float(expected)) > tolerance:
        raise RuntimeError(f"{label}: {actual} != {expected}")


def apply_enrichment(
    site: dict[str, Any],
    demography_snapshot: dict[str, Any],
    rcs_snapshot: dict[str, Any],
) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    missing = [key for key in TARGET_METRICS if key not in metrics]
    if missing:
        raise RuntimeError(f"Metriche A3.5 mancanti: {missing}")

    age_sex = demography_snapshot.get("posas", {}).get("ageSex2026")
    rcs_towns = rcs_snapshot.get("towns")
    if not isinstance(age_sex, dict) or not isinstance(rcs_towns, dict):
        raise RuntimeError("Snapshot demografici privi delle strutture richieste")

    population = metrics["population"]
    dependency = metrics["dependencyIndices"]
    foreign = metrics["foreignResidents"]
    population_rows = _rows_by_town(population)
    dependency_rows = _rows_by_town(dependency)
    foreign_rows = _rows_by_town(foreign)

    towns = set(population_rows)
    if towns != set(dependency_rows) or towns != set(foreign_rows):
        raise RuntimeError("Perimetro comunale non allineato tra le tre metriche")
    if towns != set(age_sex) or towns != set(rcs_towns):
        raise RuntimeError("Perimetro 7 Comuni non allineato agli snapshot A3.5")

    all_age_sex: list[list[dict[str, Any]]] = []
    foreign_all: list[dict[str, Any]] = []

    for town in sorted(towns):
        detail = age_sex[town]
        if not isinstance(detail, list):
            raise RuntimeError(f"{town}: dettaglio POSAS non-lista")
        all_age_sex.append(detail)

        pop_breakdown = _population_breakdown(detail, year=2026)
        current_population = int(population_rows[town]["value"])
        if pop_breakdown["total"] != current_population:
            raise RuntimeError(
                f"{town}: popolazione POSAS {pop_breakdown['total']} != catalogo {current_population}"
            )
        population_rows[town]["sexBreakdown"] = pop_breakdown

        dependency_breakdown = _dependency_breakdown(detail, year=2026)
        men_dependency = _dependency_for_sex(detail, "men")
        women_dependency = _dependency_for_sex(detail, "women")
        combined_structural = (
            men_dependency["parts"][0]["numerator"] + women_dependency["parts"][0]["numerator"]
        ) / (
            men_dependency["parts"][0]["denominator"] + women_dependency["parts"][0]["denominator"]
        ) * 100
        _assert_close(
            combined_structural,
            float(dependency_rows[town]["value"]),
            f"{town}: dipendenza complessiva",
        )
        dependency_rows[town]["sexBreakdown"] = dependency_breakdown

        town_rcs = rcs_towns[town]
        citizenship = town_rcs.get("citizenship")
        if not isinstance(citizenship, list):
            raise RuntimeError(f"{town}: cittadinanze RCS non-lista")
        foreign_breakdown = _foreign_breakdown(citizenship, year=2025)
        expected_foreign = int(town_rcs["citizenshipTotal"])
        if foreign_breakdown["total"] != expected_foreign:
            raise RuntimeError(
                f"{town}: totale stranieri RCS {foreign_breakdown['total']} != {expected_foreign}"
            )
        existing_count = foreign_rows[town].get("count")
        if existing_count is not None and int(existing_count) != expected_foreign:
            raise RuntimeError(
                f"{town}: count foreignResidents {existing_count} != RCS {expected_foreign}"
            )
        foreign_rows[town]["sexBreakdown"] = foreign_breakdown
        foreign_all.extend(citizenship)

    combined_age_sex = _combine_age_sex(all_age_sex)
    population_aggregate = population.get("aggregate")
    dependency_aggregate = dependency.get("aggregate")
    foreign_aggregate = foreign.get("aggregate")
    if not all(
        isinstance(item, dict)
        for item in (population_aggregate, dependency_aggregate, foreign_aggregate)
    ):
        raise RuntimeError("Aggregate A3.5 mancanti")

    pop_aggregate_breakdown = _population_breakdown(combined_age_sex, year=2026)
    if pop_aggregate_breakdown["total"] != int(population_aggregate["value"]):
        raise RuntimeError("Popolazione Versilia non riconciliata")
    population_aggregate["sexBreakdown"] = pop_aggregate_breakdown

    dependency_aggregate_breakdown = _dependency_breakdown(combined_age_sex, year=2026)
    total_men = _dependency_for_sex(combined_age_sex, "men")
    total_women = _dependency_for_sex(combined_age_sex, "women")
    combined_value = (
        total_men["parts"][0]["numerator"] + total_women["parts"][0]["numerator"]
    ) / (
        total_men["parts"][0]["denominator"] + total_women["parts"][0]["denominator"]
    ) * 100
    _assert_close(
        combined_value,
        float(dependency_aggregate["value"]),
        "Versilia: dipendenza complessiva",
    )
    dependency_aggregate["sexBreakdown"] = dependency_aggregate_breakdown

    foreign_aggregate_breakdown = _foreign_breakdown(foreign_all, year=2025)
    rcs_versilia = rcs_snapshot.get("aggregate", {}).get("Versilia", {})
    expected_aggregate_foreign = int(rcs_versilia.get("citizenshipTotal") or 0)
    if foreign_aggregate_breakdown["total"] != expected_aggregate_foreign:
        raise RuntimeError(
            "Residenti stranieri Versilia non riconciliati con aggregate RCS"
        )
    existing_aggregate_count = foreign_aggregate.get("count")
    if (
        existing_aggregate_count is not None
        and int(existing_aggregate_count) != expected_aggregate_foreign
    ):
        raise RuntimeError(
            f"foreignResidents aggregate count {existing_aggregate_count} != RCS "
            f"{expected_aggregate_foreign}"
        )
    foreign_aggregate["sexBreakdown"] = foreign_aggregate_breakdown

    return {"metricsEnriched": 3, "towns": len(towns), "pairsAcquired": 3}


def main() -> int:
    site = load(SITE_PATH)
    demography = load(DEMOGRAPHY_SNAPSHOT_PATH)
    rcs = load(RCS_SNAPSHOT_PATH)
    summary = apply_enrichment(site, demography, rcs)
    save(SITE_PATH, site)
    print(
        "A3.5 demografia sesso: "
        f"{summary['metricsEnriched']} metriche × {summary['towns']} comuni; "
        f"{summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
