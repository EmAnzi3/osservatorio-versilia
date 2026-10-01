#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
BENCH = ROOT / "data" / "source-snapshots" / "a3-mef-benchmark-2024.json"
MUNICIPAL = ROOT / "data" / "source-snapshots" / "mef-income-lotto-a-2024.json"
BENCH_REF = "data/source-snapshots/a3-mef-benchmark-2024.json"
SOURCE_URL = "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"

TARGETS = {
    "incomeSourceProfile": {
        "unit": "currency",
        "year": "2024",
        "note": "Benchmark riferito alla componente predefinita «Lavoro dipendente e assimilati»: ammontare / frequenza della stessa fonte.",
    },
    "pensionIncomeShare": {
        "unit": "percent",
        "year": "2024",
        "note": "Quota dell'ammontare dei redditi da pensione sul reddito complessivo. Toscana e Italia sono calcolate sui rispettivi ammontari aggregati.",
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def num(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result


def close(actual: Any, expected: float, label: str, tol: float = 1e-8) -> None:
    a = num(actual, label)
    if not math.isclose(a, float(expected), rel_tol=0.0, abs_tol=tol):
        raise RuntimeError(f"{label}: {a} != {expected}")


def rows_by_town(metric: dict[str, Any], metric_id: str) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"{metric_id}: rows mancanti")
    out = {str(row.get("town")): row for row in rows if isinstance(row, dict) and row.get("town")}
    if len(out) != 7:
        raise RuntimeError(f"{metric_id}: perimetro pubblico non 7/7")
    return out


def validate_benchmark_snapshot(snap: dict[str, Any]) -> None:
    if snap.get("taxYear") != 2024 or snap.get("declarationYear") != 2025:
        raise RuntimeError("Snapshot MEF benchmark con annualità inattesa")
    if (snap.get("acquisitionGate") or {}).get("status") != "PASS":
        raise RuntimeError("Snapshot MEF benchmark senza acquisition gate PASS")

    comp = snap.get("components") or {}
    bench = snap.get("benchmarks") or {}
    for scope in ("tuscany", "italy"):
        raw = comp.get(scope) or {}
        total_freq = num(raw.get("totalIncomeFrequency"), f"{scope}: totalIncomeFrequency")
        total_amount = num(raw.get("totalIncomeAmountEuro"), f"{scope}: totalIncomeAmountEuro")
        emp_freq = num(raw.get("employmentIncomeFrequency"), f"{scope}: employmentIncomeFrequency")
        emp_amount = num(raw.get("employmentIncomeAmountEuro"), f"{scope}: employmentIncomeAmountEuro")
        pension_amount = num(raw.get("pensionIncomeAmountEuro"), f"{scope}: pensionIncomeAmountEuro")
        close((bench["incomeSourceProfile"] or {}).get(scope), emp_amount / emp_freq, f"incomeSourceProfile/{scope}", 1e-12)
        close((bench["pensionIncomeShare"] or {}).get(scope), pension_amount / total_amount * 100.0, f"pensionIncomeShare/{scope}", 1e-12)


def validate_public(metrics: dict[str, Any], municipal: dict[str, Any]) -> None:
    towns = municipal.get("towns")
    if not isinstance(towns, dict) or len(towns) != 7:
        raise RuntimeError("Snapshot comunale MEF non 7/7")

    source_rows = rows_by_town(metrics["incomeSourceProfile"], "incomeSourceProfile")
    pension_rows = rows_by_town(metrics["pensionIncomeShare"], "pensionIncomeShare")
    if set(source_rows) != set(towns) or set(pension_rows) != set(towns):
        raise RuntimeError("Perimetro comunale MEF non riconciliato")

    for town, raw in towns.items():
        total = raw.get("totalIncome") or {}
        total_amount = num(total.get("amountEuro"), f"{town}: totalIncome amount")
        sources = raw.get("incomeSources")
        if not isinstance(sources, list):
            raise RuntimeError(f"{town}: incomeSources mancanti")
        employment = next((item for item in sources if item.get("key") == "employment"), None)
        if not isinstance(employment, dict):
            raise RuntimeError(f"{town}: fonte employment mancante")
        emp_freq = num(employment.get("frequency"), f"{town}: employment frequency")
        emp_amount = num(employment.get("amountEuro"), f"{town}: employment amount")
        expected_emp = emp_amount / emp_freq
        close(source_rows[town].get("value"), expected_emp, f"incomeSourceProfile/{town}")
        parts = source_rows[town].get("parts")
        if not isinstance(parts, list) or not parts:
            raise RuntimeError(f"incomeSourceProfile/{town}: parts mancanti")
        if str(parts[0].get("label")) != "Lavoro dipendente e assimilati":
            raise RuntimeError(f"incomeSourceProfile/{town}: componente predefinita inattesa")
        close(parts[0].get("value"), expected_emp, f"incomeSourceProfile/{town}/part0")

        pension = raw.get("pensionIncome") or {}
        pension_amount = num(pension.get("amountEuro"), f"{town}: pension amount")
        close(pension_rows[town].get("value"), pension_amount / total_amount * 100.0, f"pensionIncomeShare/{town}")


def main() -> None:
    site = load(SITE)
    snap = load(BENCH)
    municipal = load(MUNICIPAL)
    validate_benchmark_snapshot(snap)

    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    for metric_id in TARGETS:
        if not isinstance(metrics.get(metric_id), dict):
            raise RuntimeError(f"{metric_id}: metrica pubblica mancante")

    validate_public(metrics, municipal)
    benchmarks = snap.get("benchmarks") or {}

    updated = 0
    for metric_id, cfg in TARGETS.items():
        metric = metrics[metric_id]
        meta = metric.get("meta")
        if not isinstance(meta, dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        if str(meta.get("year")) != cfg["year"] or str(meta.get("unit")) != cfg["unit"]:
            raise RuntimeError(f"{metric_id}: anno/unità pubblici inattesi")
        if str(metric.get("sourceUrl") or "") != SOURCE_URL:
            raise RuntimeError(f"{metric_id}: sourceUrl MEF inatteso")

        spec = benchmarks.get(metric_id)
        if not isinstance(spec, dict):
            raise RuntimeError(f"{metric_id}: benchmark assente")
        if str(spec.get("year")) != cfg["year"] or str(spec.get("unit")) != cfg["unit"]:
            raise RuntimeError(f"{metric_id}: anno/unità benchmark inattesi")
        tuscany = num(spec.get("tuscany"), f"{metric_id}/tuscany")
        italy = num(spec.get("italy"), f"{metric_id}/italy")

        payload = {
            "year": cfg["year"],
            "tuscany": tuscany,
            "italy": italy,
            "source": "MEF — Dipartimento Finanze",
            "url": SOURCE_URL,
            "sourceSnapshot": BENCH_REF,
            "note": cfg["note"],
        }
        if metric_id == "incomeSourceProfile":
            payload["part"] = "Lavoro dipendente e assimilati"
        meta["benchmark"] = payload
        updated += 1

    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"A3 benchmark MEF: {updated} metriche Toscana/Italia materializzate e riconciliate 7/7.")


if __name__ == "__main__":
    main()
