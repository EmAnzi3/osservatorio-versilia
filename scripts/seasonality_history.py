#!/usr/bin/env python3
"""Serie storica della concentrazione turistica nei tre mesi principali (Regione Toscana).

Stessa regola del valore pubblicato (`acquire_a3_benchmark_regione_toscana_tourism_annual.py`):
dal file regionale «Movimento turistico per comune e mese» le presenze dei dodici mesi, al netto
delle locazioni; quota = presenze dei tre mesi con più presenze / presenze annue × 100. Il totale
mensile deve coincidere con la somma dei mesi e con le presenze annue già pubblicate nella serie
del movimento per comune. Sono pubblicati come file scaricabili solo gli anni 2024 e 2025: gli anni
precedenti sono consultabili solo dalla banca dati interattiva, non come tavola comunale mensile.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date
from typing import Any, Callable

SNAPSHOT = "data/source-snapshots/regione-toscana-stagionalita-serie.json"
METRIC = "tourismSeasonality"
PRESENCES = "tourismPresences"
URLS = {
    2024: "https://www.regione.toscana.it/documents/d/guest/5-movimento-comune_mese-ods",
    2025: "https://www.regione.toscana.it/documents/d/guest/5-movimento-comune_mese-2025-agg-maggio-2026-",
}


class SeasonalityError(RuntimeError):
    pass


def share(months: list[float]) -> float:
    return math.fsum(sorted(months, reverse=True)[:3]) / math.fsum(months) * 100


def read_year(rows: list[list[Any]], towns: list[str], presences: dict[str, float], year: int) -> dict[str, Any]:
    import acquire_a3_benchmark_regione_toscana_tourism_annual as rt
    by_name = rt.find_rows(rows)
    out = {}
    for town in towns:
        row = by_name.get(town.casefold())
        if row is None:
            raise SeasonalityError(f"{year} {town}: riga mensile assente")
        months = [rt.number(row[i], f"{year}/{town}/mese-{m}") for m, i in enumerate(range(3, 26, 2), 1)]
        total = rt.number(row[27], f"{year}/{town}/totale")
        if not math.isclose(math.fsum(months), total, rel_tol=0, abs_tol=0.1):
            raise SeasonalityError(f"{year} {town}: mesi {math.fsum(months)} ≠ totale {total}")
        if not math.isclose(total, presences[town], rel_tol=0, abs_tol=0.1):
            raise SeasonalityError(f"{year} {town}: totale mensile {total} ≠ presenze pubblicate {presences[town]}")
        out[town] = {"months": months, "presences": total, "share": share(months)}
    return out


def build_snapshot(fetch: Callable[[str], bytes], site: dict[str, Any]) -> dict[str, Any]:
    import acquire_a3_benchmark_regione_toscana_tourism_annual as rt
    metric = site["metrics"][METRIC]
    towns = [r["town"] for r in metric["rows"]]
    pres = {r["town"]: dict(zip(map(int, r["series"]["years"]), r["series"]["values"])) for r in site["metrics"][PRESENCES]["rows"]}
    years: dict[int, Any] = {}
    sources = {}
    for year, url in URLS.items():
        raw = fetch(url)
        sources[str(year)] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        years[year] = read_year(rt.ods_rows(raw), towns, {t: pres[t][year] for t in towns}, year)
    last = int(metric["meta"]["year"])
    for row in metric["rows"]:
        if not math.isclose(years[last][row["town"]]["share"], row["value"], rel_tol=0, abs_tol=1e-9):
            raise SeasonalityError(f"{row['town']} {last}: ricalcolo {years[last][row['town']]['share']} ≠ pubblicato {row['value']}")
    ordered = sorted(years)
    return {
        "schemaVersion": 1, "version": f"regione-toscana-stagionalita-serie-{ordered[0]}-{ordered[-1]}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Regione Toscana — Ufficio regionale di Statistica / Istat", "years": ordered, "sources": sources,
        "rule": "Presenze mensili al netto delle locazioni; tre mesi con più presenze / presenze annue × 100; totale = somma dei mesi = presenze pubblicate.",
        "towns": {t: {str(y): years[y][t] for y in ordered} for t in towns},
        "qualityGate": {"status": "PASS", "note": f"{last} identico al valore pubblicato per i 7 Comuni; anni con file mensile scaricabile: {ordered}."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    if str(years[-1]) != str(metric["meta"]["year"]):
        raise SeasonalityError("serie non allineata all'anno pubblicato")
    for row in metric["rows"]:
        values = [snapshot["towns"][row["town"]][str(y)]["share"] for y in years]
        if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-9):
            raise SeasonalityError(f"{row['town']}: serie ≠ valore pubblicato")
        row["series"] = {"years": list(years), "values": values}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    metric["method"]["historyNote"] = (f"Serie {years[0]}–{years[-1]}: la Regione pubblica la tavola comunale mensile solo da questi anni;"
                                       " presenze al netto delle locazioni, stessa regola del valore corrente.")
