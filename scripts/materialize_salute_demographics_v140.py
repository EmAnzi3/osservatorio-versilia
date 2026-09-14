#!/usr/bin/env python3
"""Enrich Salute metrics with ARS sex/age dimensions and Tuscany benchmark.

Input is the reviewed compact snapshot ``ars-salute-demographics-v140.json``.
No live network access is used by the public build. Existing metric values and
histories remain canonical; this overlay only adds source-published dimensions to
the same indicators and period.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "ars-salute-demographics-v140.json"

SEX_ORDER = ["totale", "maschi", "femmine"]
SEX_LABELS = {"totale": "Totale", "maschi": "Maschi", "femmine": "Femmine"}
AGE_ORDER = ["totale", "16-44", "45-64", "65-84", "85+"]
AGE_LABELS = {
    "totale": "Totale",
    "16-44": "16–44 anni",
    "45-64": "45–64 anni",
    "65-84": "65–84 anni",
    "85+": "85+ anni",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value) -> str:
    return str(value or "").strip().casefold()


def selected_value(row: dict) -> tuple[float | None, str]:
    standardized = row.get("standardized")
    if standardized is not None:
        return float(standardized), "standardized"
    raw = row.get("raw")
    if raw is not None:
        return float(raw), "raw"
    return None, "missing"


def label_options(values: set[str], order: list[str], labels: dict[str, str]) -> list[dict]:
    keys = [key for key in order if key in values]
    keys.extend(sorted(values - set(keys), key=str.casefold))
    return [{"key": key, "label": labels.get(key, key)} for key in keys]


def make_part(source: dict, unit: str, has_age: bool) -> dict:
    sex = norm(source.get("sex")) or "totale"
    age = norm(source.get("strato1")) or "totale"
    value, measurement = selected_value(source)
    base = {
        "value": value,
        "unit": unit,
        "measurement": measurement,
        "numerator": source.get("num"),
        "denominator": source.get("den"),
        "ci95Low": source.get("ci95Low"),
        "ci95High": source.get("ci95High"),
    }
    if has_age:
        return {
            "key": f"{age}|{sex}",
            "label": f"{AGE_LABELS.get(age, age)} · {SEX_LABELS.get(sex, sex)}",
            "ageKey": age,
            "ageLabel": AGE_LABELS.get(age, age),
            "genderKey": sex,
            "genderLabel": SEX_LABELS.get(sex, sex),
            **base,
        }
    return {
        "key": sex,
        "label": SEX_LABELS.get(sex, sex),
        **base,
    }


def sort_parts(parts: list[dict], has_age: bool) -> list[dict]:
    sex_rank = {key: index for index, key in enumerate(SEX_ORDER)}
    age_rank = {key: index for index, key in enumerate(AGE_ORDER)}
    if has_age:
        return sorted(
            parts,
            key=lambda part: (
                age_rank.get(part.get("ageKey"), 999),
                sex_rank.get(part.get("genderKey"), 999),
                part.get("key", ""),
            ),
        )
    return sorted(parts, key=lambda part: (sex_rank.get(part.get("key"), 999), part.get("key", "")))


def default_part(parts: list[dict], has_age: bool) -> dict | None:
    expected = "totale|totale" if has_age else "totale"
    return next((part for part in parts if part.get("key") == expected), parts[0] if parts else None)


def assert_same_default(metric_key: str, expected, observed, unit: str) -> None:
    if expected is None or observed is None:
        raise RuntimeError(f"{metric_key}: valore base assente durante la riconciliazione demografica")
    tolerance = 0.051 if unit == "years" else 0.011
    if abs(float(expected) - float(observed)) > tolerance:
        raise RuntimeError(
            f"{metric_key}: la lettura Totale non riconcilia con il valore pubblicato: "
            f"catalogo={expected}, ARS={observed}"
        )


def main() -> int:
    if not SNAPSHOT.is_file():
        raise RuntimeError(f"Snapshot demografico Salute mancante: {SNAPSHOT}")

    data = load(DATA)
    snapshot = load(SNAPSHOT)
    if snapshot.get("release") != "v1.40.0":
        raise RuntimeError(f"Release snapshot inattesa: {snapshot.get('release')}")

    applied = []
    for source_indicator in snapshot.get("indicators", {}).values():
        key = source_indicator["key"]
        metric = data.get("metrics", {}).get(key)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Snapshot demografico: metrica catalogo assente: {key}")
        meta = metric.setdefault("meta", {})
        unit = meta.get("unit") or source_indicator.get("unit")
        source_rows = source_indicator.get("rows") or []

        ages = {norm(row.get("strato1")) for row in source_rows if norm(row.get("strato1"))}
        ages.discard("")
        non_total_ages = {age for age in ages if age != "totale"}
        has_age = bool(non_total_ages)
        sexes = {norm(row.get("sex")) for row in source_rows if norm(row.get("sex"))}
        if not {"totale", "maschi", "femmine"}.issubset(sexes):
            raise RuntimeError(f"{key}: dettaglio sesso ARS incompleto: {sorted(sexes)}")

        by_geo: dict[str, list[dict]] = defaultdict(list)
        for source_row in source_rows:
            by_geo[str(source_row.get("geoCode") or "").strip()].append(source_row)

        if has_age:
            age_values = {"totale", *non_total_ages}
            meta["compositeType"] = "demographicBreakdown"
            meta["ageOptions"] = label_options(age_values, AGE_ORDER, AGE_LABELS)
            meta["genderOptions"] = label_options(sexes, SEX_ORDER, SEX_LABELS)
            meta["defaultAge"] = "totale"
            meta["defaultGender"] = "totale"
            meta["demographicSelectorNote"] = (
                "Fasce d’età e sesso pubblicati da ARS Toscana per lo stesso indicatore e periodo."
            )
        else:
            meta["compositeType"] = "sexBreakdown"
            meta["sexOptions"] = label_options(sexes, SEX_ORDER, SEX_LABELS)
            meta["defaultSex"] = "totale"
            meta["selectorLabel"] = "Sesso"

        meta["demographicSource"] = {
            "publisher": "ARS Toscana",
            "indicatorId": source_indicator["indicatorId"],
            "period": source_indicator["period"],
            "snapshot": "data/source-snapshots/ars-salute-demographics-v140.json",
            "measurementRule": "misura_standardizzata se pubblicata; altrimenti misura_grezza della stessa riga ARS",
        }

        # Rows use Observatory town names/codes; source geography codes are kept in
        # the snapshot and matched here by the official municipality name.
        source_by_town = defaultdict(list)
        for source_row in source_rows:
            geography = str(source_row.get("geography") or "").strip()
            if geography:
                source_by_town[geography].append(source_row)

        for town_row in metric.get("rows", []):
            sources = source_by_town.get(town_row.get("town"), [])
            if not sources:
                raise RuntimeError(f"{key}: nessuna dimensione ARS per {town_row.get('town')}")
            parts = sort_parts([make_part(row, unit, has_age) for row in sources], has_age)
            base = default_part(parts, has_age)
            assert_same_default(key, town_row.get("value"), base.get("value") if base else None, unit)
            town_row["parts"] = parts

        versilia_sources = by_geo.get("202M", [])
        tuscany_sources = by_geo.get("90", [])
        if not versilia_sources or not tuscany_sources:
            raise RuntimeError(f"{key}: riferimento Versilia/Toscana incompleto nello snapshot")

        aggregate_parts = sort_parts([make_part(row, unit, has_age) for row in versilia_sources], has_age)
        aggregate_default = default_part(aggregate_parts, has_age)
        assert_same_default(key, metric.get("aggregate", {}).get("value"), aggregate_default.get("value") if aggregate_default else None, unit)
        metric.setdefault("aggregate", {})["parts"] = aggregate_parts
        metric["aggregate"]["note"] = (
            "Aggregato ufficiale Zona Versilia pubblicato da ARS Toscana per la lettura selezionata; "
            "non è una media dei valori comunali."
        )

        tuscany_parts = sort_parts([make_part(row, unit, has_age) for row in tuscany_sources], has_age)
        metric["tuscany"] = {
            "label": "Regione Toscana",
            "parts": tuscany_parts,
            "source": "ARS Toscana",
            "period": source_indicator["period"],
            "url": source_indicator["exportUrl"],
            "note": "Stessa fonte, periodo, definizione e dimensione demografica della lettura selezionata.",
        }
        tuscany_default = default_part(tuscany_parts, has_age)
        if tuscany_default and tuscany_default.get("value") is not None:
            meta["benchmark"] = {
                "year": str(meta.get("year") or source_indicator["period"]),
                "source": "ARS Toscana",
                "tuscany": tuscany_default["value"],
                "italy": None,
                "url": source_indicator["exportUrl"],
                "note": "Confronto omogeneo con Regione Toscana dalla stessa fonte ARS. Il dato Italia non è presente nello stesso export.",
            }

        applied.append(key)

    save(DATA, data)
    print(f"Salute v1.40 demographic overlay: {len(applied)} metriche arricchite")
    print("Metriche:", ", ".join(applied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
