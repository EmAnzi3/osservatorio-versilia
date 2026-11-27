#!/usr/bin/env python3
"""Serie storica del costo totale del servizio rifiuti per abitante (ISPRA, CTOTab) nei sette Comuni.

Stessa regola del valore pubblicato (`audit_waste_cost_ispra.py`): per ogni anno si scorre l'intera
tabella regionale toscana dei costi comunali del Catasto Rifiuti e si accettano solo righe con
«N. di comuni» = 1, così un'aggregazione non viene mai attribuita a un Comune. Si usano solo anni
consecutivi, fino all'anno pubblicato, in cui tutti e sette i Comuni hanno una riga comunale;
l'anno pubblicato deve coincidere con i valori del catalogo.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date
from typing import Any, Callable

import audit_waste_cost_ispra as src

SNAPSHOT = "data/source-snapshots/ispra-costo-rifiuti-serie.json"
METRIC = "wasteServiceCost"
FIRST = 2010
URL = ("https://www.catasto-rifiuti.isprambiente.it/index.php?"
       "aa={year}&p={page}&pg=costicomuneproc&reg1=Toscana&regid=09&regid2=09")


class WasteHistoryError(RuntimeError):
    pass


def read_year(fetch: Callable[[str], str], year: int) -> tuple[dict[str, dict[str, float]], list[str], list[str]]:
    """Righe comunali (N. di comuni = 1) dei sette Comuni; restituisce anche le pagine lette e i Comuni assenti."""
    wanted = {src.norm(t): t for t in src.TOWNS}
    found: dict[str, dict[str, float]] = {}
    pages: list[str] = []
    for page in range(1, 25):
        url = URL.format(year=year, page=page)
        table = src.Tables()
        table.feed(fetch(url))
        pages.append(hashlib.sha256(url.encode()).hexdigest()[:12])
        rows_on_page = 0
        for row in table.rows:
            if len(row) < 5:
                continue
            municipalities, population, ctot = src.number(row[2]), src.number(row[3]), src.number(row[-1])
            if municipalities is None or population is None or ctot is None:
                continue
            rows_on_page += 1
            town = wanted.get(src.norm(row[0]))
            if town is None or int(round(municipalities)) != 1 or population <= 0:
                continue
            value = {"population": population, "ctot": ctot}
            if town in found and found[town] != value:
                raise WasteHistoryError(f"{year} {town}: righe duplicate incoerenti")
            found[town] = value
        if rows_on_page == 0:
            break
    return found, pages, [t for t in src.TOWNS if t not in found]


def build_snapshot(fetch: Callable[[str], str], published: dict[str, float], last: int) -> dict[str, Any]:
    """`published`: Comune → CTOTab pubblicato per l'anno `last`."""
    years: dict[int, dict[str, Any]] = {}
    stop = None
    for year in range(last, FIRST - 1, -1):
        found, pages, missing = read_year(fetch, year)
        if missing:
            if year == last:
                raise WasteHistoryError(f"anno pubblicato {year}: Comuni senza riga comunale {missing}")
            stop = f"{year}: Comuni senza riga comunale (o in gestione aggregata) {missing}"
            break
        years[year] = {"towns": found, "pagesRead": len(pages)}
    for town, value in published.items():
        if not math.isclose(years[last]["towns"][town]["ctot"], value, rel_tol=0, abs_tol=0.005):
            raise WasteHistoryError(f"{town} {last}: fonte {years[last]['towns'][town]['ctot']} ≠ pubblicato {value}")
    ordered = sorted(years)
    if len(ordered) < 2:
        raise WasteHistoryError(f"serie di un solo anno ({stop})")
    return {
        "schemaVersion": 1, "version": f"ispra-costo-rifiuti-serie-{ordered[0]}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "ISPRA — Catasto Rifiuti, costi comunali pro capite", "urlTemplate": URL, "years": ordered, "stoppedAt": stop,
        "rule": "CTOTab €/abitante dalla tabella regionale toscana, solo righe con «N. di comuni» = 1; anni consecutivi con 7/7 righe comunali.",
        "towns": {t: {str(y): years[y]["towns"][t] for y in ordered} for t in src.TOWNS},
        "qualityGate": {"status": "PASS", "note": f"Anno {last} identico ai valori pubblicati per i 7 Comuni."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    if str(years[-1]) != str(metric["meta"]["year"]):
        raise WasteHistoryError("serie non allineata all'anno pubblicato")
    for row in metric["rows"]:
        values = [snapshot["towns"][row["town"]][str(y)]["ctot"] for y in years]
        if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=0.005):
            raise WasteHistoryError(f"{row['town']}: serie {values[-1]} ≠ valore {row['value']}")
        row["series"] = {"years": list(years), "values": values}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    metric["method"]["historyNote"] = (f"Serie {years[0]}–{years[-1]} dal Catasto Rifiuti ISPRA, stessa voce CTOTab e solo righe comunali;"
                                       " euro correnti, non deflazionati.")
