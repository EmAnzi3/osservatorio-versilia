#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
BENCH = ROOT / "data" / "source-snapshots" / "a3-mim-building-benchmark-2024-25.json"
LOCAL = ROOT / "data" / "source-snapshots" / "mim-edilizia-scolastica-versilia-2024-25.json"
BENCH_REF = "data/source-snapshots/a3-mim-building-benchmark-2024-25.json"
SCHOOL_YEAR = "2024/25"

SOURCE_PAGES = {
    "schoolBuildingSafetyDocs": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0171EDICONSICUREZZASTA2021",
    "schoolBuildingAccessibility": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0156EDISUPBARARCSTA2021",
    "schoolBuildingFacilities": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0151EDIAMBFUNZSTA2021",
    "schoolBuildingAge": "https://dati.istruzione.it/opendata/opendata/catalog/EDIETAORIGINESTA2021",
    "schoolBuildingTransport": "https://dati.istruzione.it/opendata/opendata/catalog/EDICOLLEGAMENTISTA2021",
}

TARGETS = {
    "schoolBuildingSafetyDocs": {
        "field": "agibilita",
        "part": "Agibilità piena",
        "note": "Quota di edifici con agibilità piena sulle risposte definite. IN PARTE resta nel denominatore ma non nel numeratore; NON DEFINITO è escluso.",
    },
    "schoolBuildingAccessibility": {
        "field": "accessibilita",
        "part": "Con accorgimenti per il superamento delle barriere",
        "note": "Quota di edifici con accorgimenti per il superamento delle barriere sulle risposte definite.",
    },
    "schoolBuildingFacilities": {
        "field": "mensa",
        "part": "Edifici con mensa",
        "note": "Quota di edifici con mensa sulle risposte definite.",
    },
    "schoolBuildingAge": {
        "field": "periodoCostruzione",
        "part": "Edifici costruiti entro il 1970",
        "note": "Quota di edifici costruiti entro il 1970 sugli edifici con periodo di costruzione definito; tutte le classi definite MIM, incluse 1993–1996 e dal 2018 in poi, concorrono al denominatore.",
    },
    "schoolBuildingTransport": {
        "field": "scuolabus",
        "part": "Edifici raggiungibili con scuolabus",
        "note": "Quota di edifici raggiungibili con scuolabus sulle risposte definite.",
    },
}

AGE_PERIODS = [
    "prima del 1800",
    "tra il 1800 e il 1899",
    "tra il 1900 e il 1933",
    "tra il 1934 e il 1949",
    "tra il 1950 e il 1970",
    "tra il 1971 e il 1975",
    "tra il 1976 e il 1992",
    "tra il 1993 e il 1996",
    "tra il 1997 e il 2008",
    "tra il 2009 e il 2017",
    "dal 2018 in poi",
]
UNKNOWN = {"NON DEFINITO", "", "-", "_"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()


def finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"Valore numerico atteso, ricevuto {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"Valore non finito: {value!r}")
    return result


def assert_close(actual: Any, expected: float, label: str, tol: float = 1e-10) -> None:
    value = finite(actual)
    if not math.isclose(value, float(expected), rel_tol=0.0, abs_tol=tol):
        raise RuntimeError(f"{label}: {value} != {expected}")


def count(statuses: dict[str, Any], key: str) -> int:
    target = norm(key)
    return sum(int(v or 0) for k, v in statuses.items() if norm(k) == target)


def known_total(statuses: dict[str, Any]) -> int:
    return sum(int(v or 0) for k, v in statuses.items() if norm(k) not in UNKNOWN)


def yes_share(statuses: dict[str, Any]) -> float:
    denominator = known_total(statuses)
    if denominator <= 0:
        raise RuntimeError("Denominatore risposte definite nullo")
    return count(statuses, "SI") / denominator * 100.0


def age_share(statuses: dict[str, Any]) -> float:
    normalized = {str(k).strip().lower(): int(v or 0) for k, v in statuses.items()}
    defined = sum(normalized.get(period, 0) for period in AGE_PERIODS)
    if defined <= 0:
        raise RuntimeError("Denominatore periodo costruzione definito nullo")
    old = sum(normalized.get(period, 0) for period in AGE_PERIODS[:5])
    return old / defined * 100.0


def metric_value(metric_id: str, statuses: dict[str, Any]) -> float:
    if metric_id == "schoolBuildingAge":
        return age_share(statuses)
    return yes_share(statuses)


def validate_benchmark_snapshot(snap: dict[str, Any]) -> None:
    if snap.get("schoolYear") != SCHOOL_YEAR:
        raise RuntimeError("Snapshot MIM edilizia con anno scolastico inatteso")
    gate = snap.get("qualityGate") or {}
    if gate.get("status") != "PASS":
        raise RuntimeError("Snapshot MIM edilizia senza quality gate PASS")
    if int(gate.get("unmappedSchoolRows", -1)) != 0 or int(gate.get("conflictCount", -1)) != 0:
        raise RuntimeError("Snapshot MIM edilizia con unmapped/conflicts")
    reconciled = set(gate.get("reconciledMetrics") or [])
    if reconciled != set(TARGETS):
        raise RuntimeError("Snapshot MIM edilizia non riconciliato 5/5")

    raw = snap.get("raw") or {}
    benchmarks = snap.get("benchmarks") or {}
    for metric_id in TARGETS:
        metric_raw = raw.get(metric_id)
        spec = benchmarks.get(metric_id)
        if not isinstance(metric_raw, dict) or not isinstance(spec, dict):
            raise RuntimeError(f"{metric_id}: raw/benchmark mancante")
        if spec.get("schoolYear") != SCHOOL_YEAR or spec.get("unit") != "percent":
            raise RuntimeError(f"{metric_id}: contratto benchmark inatteso")
        for scope in ("tuscany", "italy"):
            scope_raw = metric_raw.get(scope) or {}
            statuses = scope_raw.get("statuses")
            if not isinstance(statuses, dict):
                raise RuntimeError(f"{metric_id}/{scope}: statuses mancanti")
            buildings = int(scope_raw.get("buildings") or 0)
            if buildings <= 0 or sum(int(v or 0) for v in statuses.values()) != buildings:
                raise RuntimeError(f"{metric_id}/{scope}: conteggi edificio non riconciliati")
            expected = metric_value(metric_id, statuses)
            assert_close(spec.get(scope), expected, f"{metric_id}/{scope}", 1e-12)


def validate_public(metrics: dict[str, Any], local: dict[str, Any]) -> None:
    towns = local.get("towns")
    if not isinstance(towns, dict) or len(towns) != 7 or int(local.get("uniqueBuildingsVersilia") or 0) != 109:
        raise RuntimeError("Snapshot locale MIM non è il governato 109 edifici / 7 Comuni")

    for metric_id, cfg in TARGETS.items():
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"{metric_id}: metrica pubblica mancante")
        rows = metric.get("rows")
        if not isinstance(rows, list):
            raise RuntimeError(f"{metric_id}: rows mancanti")
        by_town = {str(row.get("town")): row for row in rows if isinstance(row, dict) and row.get("town")}
        if set(by_town) != set(towns):
            raise RuntimeError(f"{metric_id}: perimetro pubblico non riconciliato 7/7")
        for town, town_raw in towns.items():
            statuses = town_raw.get(cfg["field"])
            if not isinstance(statuses, dict):
                raise RuntimeError(f"{metric_id}/{town}: campo {cfg['field']} mancante")
            expected = metric_value(metric_id, statuses)
            assert_close(by_town[town].get("value"), expected, f"{metric_id}/{town}")


def main() -> None:
    site = load(SITE)
    snap = load(BENCH)
    local = load(LOCAL)
    validate_benchmark_snapshot(snap)

    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    validate_public(metrics, local)

    benchmarks = snap["benchmarks"]
    updated = 0
    for metric_id, cfg in TARGETS.items():
        metric = metrics[metric_id]
        meta = metric.get("meta")
        if not isinstance(meta, dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        if str(meta.get("year")) != SCHOOL_YEAR or str(meta.get("unit")) != "percent":
            raise RuntimeError(f"{metric_id}: anno/unità pubblici inattesi")
        if str(metric.get("sourceUrl") or "") != SOURCE_PAGES[metric_id]:
            raise RuntimeError(f"{metric_id}: sourceUrl pubblico inatteso")

        spec = benchmarks[metric_id]
        meta["benchmark"] = {
            "year": SCHOOL_YEAR,
            "tuscany": finite(spec["tuscany"]),
            "italy": finite(spec["italy"]),
            "source": "MIM — Anagrafe dell'Edilizia Scolastica",
            "url": SOURCE_PAGES[metric_id],
            "sourceSnapshot": BENCH_REF,
            "part": cfg["part"],
            "note": cfg["note"],
        }
        updated += 1

    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"A3 benchmark MIM edilizia: {updated} metriche Toscana/Italia materializzate; gate 5/5 e riconciliazione Versilia 7/7.")


if __name__ == "__main__":
    main()
