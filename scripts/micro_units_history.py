#!/usr/bin/env python3
"""Serie 2018–2024 della quota di unità locali con meno di 10 addetti nei sette Comuni.

Stessa fonte e regola del valore pubblicato: Istat ASIA-UL, flusso SDMX
`DICA_ASIAULP_TERRIFDATA_7`, unità locali della classe 0–9 addetti (W0_9) sul totale
(TOTAL), totale attività economiche (0010), × 100, arrotondato a due decimali come il
valore pubblicato. Il totale di ogni anno deve coincidere con la serie già pubblicata delle
unità locali attive; l'ultimo anno con il valore corrente.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import date
from typing import Any, Callable

FLOW = "183_1163_DF_DICA_ASIAULP_TERRIFDATA_7"
BASE = "https://esploradati.istat.it/SDMXWS/rest/data"
SOURCE = f"https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0900ENT,1.0/DICA_ASIA/DICA_ASIAULP/{FLOW}"
SNAPSHOT = "data/source-snapshots/istat-micro-unita-serie.json"
METRIC = "microUnits"
TOWNS = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")
FIRST = 2018


class MicroUnitsError(RuntimeError):
    pass


def url(first: int, last: int) -> str:
    return f"{BASE}/IT1,{FLOW},1.0/A.{'+'.join(TOWNS)}.LU.0010.W0_9+TOTAL?startPeriod={first}&endPeriod={last}"


def parse(body: bytes, first: int, last: int) -> dict[str, dict[int, dict[str, int]]]:
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    need = {"DATAFLOW", "FREQ", "REF_AREA", "DATA_TYPE", "ECON_ACTIVITY_NACE_2007", "PERS_EMPL_SIZE_CLASS", "TIME_PERIOD", "OBS_VALUE"}
    if not need.issubset(reader.fieldnames or []):
        raise MicroUnitsError(f"schema SDMX inatteso: {reader.fieldnames}")
    out: dict[str, dict[int, dict[str, int]]] = {c: {} for c in TOWNS}
    for row in reader:
        if row["DATAFLOW"] != f"IT1:{FLOW}(1.0)" or row["FREQ"] != "A" or row["DATA_TYPE"] != "LU" or row["ECON_ACTIVITY_NACE_2007"] != "0010":
            raise MicroUnitsError(f"riga fuori perimetro {row}")
        area, size, year, raw = row["REF_AREA"], row["PERS_EMPL_SIZE_CLASS"], int(row["TIME_PERIOD"]), row["OBS_VALUE"].strip()
        if area not in out or size not in ("W0_9", "TOTAL") or not first <= year <= last:
            raise MicroUnitsError(f"area, classe o anno inattesi: {area} {size} {year}")
        if (row.get("OBS_STATUS") or "").strip():
            raise MicroUnitsError(f"{area} {year} {size}: osservazione con flag {row['OBS_STATUS']}")
        if not re.fullmatch(r"\d+", raw):
            raise MicroUnitsError(f"{area} {year} {size}: valore {raw!r}")
        cell = out[area].setdefault(year, {})
        if size in cell:
            raise MicroUnitsError(f"{area} {year} {size}: duplicato")
        cell[size] = int(raw)
    for area, years in out.items():
        if sorted(years) != list(range(first, last + 1)):
            raise MicroUnitsError(f"{area}: anni {sorted(years)}")
        for year, cell in years.items():
            if set(cell) != {"W0_9", "TOTAL"} or not 0 <= cell["W0_9"] <= cell["TOTAL"] or cell["TOTAL"] <= 0:
                raise MicroUnitsError(f"{area} {year}: componenti incoerenti {cell}")
    return out


def share(cell: dict[str, int]) -> float:
    return round(cell["W0_9"] / cell["TOTAL"] * 100, 2)


def build_snapshot(fetcher: Callable[[str], bytes], current: dict[str, float], local_units: dict[str, dict[int, int]], last: int) -> dict[str, Any]:
    """`current`: codice → quota pubblicata; `local_units`: codice → {anno: unità locali pubblicate}."""
    source = url(FIRST, last)
    body = fetcher(source)
    counts = parse(body, FIRST, last)
    for code in TOWNS:
        for year, cell in counts[code].items():
            published = local_units[code].get(year)
            if published != cell["TOTAL"]:
                raise MicroUnitsError(f"{code} {year}: totale {cell['TOTAL']} ≠ unità locali pubblicate {published}")
        if share(counts[code][last]) != current[code]:
            raise MicroUnitsError(f"{code} {last}: quota {share(counts[code][last])} ≠ pubblicata {current[code]}")
    years = list(range(FIRST, last + 1))
    return {
        "schemaVersion": 1, "version": f"istat-micro-unita-serie-{FIRST}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Istat — ASIA unità locali", "sourceUrl": SOURCE,
        "source": {"url": source, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)},
        "years": years,
        "rule": "Unità locali con 0–9 addetti (W0_9) / unità locali totali (TOTAL) × 100, totale attività (0010), arrotondato a due decimali come il valore pubblicato.",
        "towns": {c: {str(y): counts[c][y] for y in years} for c in TOWNS},
        "series": {c: [share(counts[c][y]) for y in years] for c in TOWNS},
        "qualityGate": {"status": "PASS", "note": f"Totali identici alla serie pubblicata delle unità locali {FIRST}–{last}; quota {last} identica al valore pubblicato."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    units = {r["code"]: r.get("series") for r in metrics["localUnits"]["rows"]}
    for row in metric["rows"]:
        values = snapshot["series"][row["code"]]
        series = units[row["code"]]
        totals = [snapshot["towns"][row["code"]][str(y)]["TOTAL"] for y in years]
        if values[-1] != row["value"] or not series or series["years"] != years or series["values"] != totals:
            raise MicroUnitsError(f"{row['town']}: serie non coerente con il valore o con le unità locali pubblicate")
        row["series"] = {"years": list(years), "values": list(values)}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    note = f" Serie {years[0]}–{years[-1]} dallo stesso flusso ASIA-UL; i totali coincidono con la serie delle unità locali attive."
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
