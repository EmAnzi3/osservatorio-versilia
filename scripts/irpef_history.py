#!/usr/bin/env python3
"""Serie storica dell'addizionale comunale IRPEF dei sette Comuni negli scenari 20.000, 30.000 e 50.000 €.

Stessa regola del valore pubblicato e del confronto Toscana/Italia (`irpef_benchmarks.rule` e
`irpef_benchmarks.amount`): per ogni anno l'elenco generale MEF delle aliquote (CSV
`download.php?anno=A`) dà la disciplina di ciascun Comune; sotto la soglia di esenzione l'importo è
zero, altrimenti aliquota unica o scaglioni sull'intero imponibile, al centesimo.

Gli elenchi più vecchi descrivono le stesse regole con parole diverse. Prima della lettura si
uniformano solo queste varianti di scrittura, elencate in `WORDING` e registrate nello snapshot
Comune per Comune: «aliquota ordinaria» = «aliquota unica», «sino a» = «fino a», «superiori a» /
«maggiore di» = «oltre», «applicabile a» ripetuto, migliaia scritte con la virgola («75,000,00») e il
simbolo dell'euro. Una disciplina che resta ambigua (per esempio scaglioni riservati a certi redditi)
interrompe la serie: si pubblicano solo anni consecutivi, fino all'anno corrente, in cui tutti e sette
i Comuni si leggono. L'ultimo anno deve coincidere con i valori pubblicati.
"""
from __future__ import annotations

import hashlib
import csv
import io
import math
import re
from datetime import date
from typing import Any, Callable

import irpef_benchmarks as ib

SNAPSHOT = "data/source-snapshots/mef-irpef-serie.json"
METRIC = ib.METRIC
FIRST = 2007
TOWNS = {"046005": "B455", "046013": "D730", "046018": "F035", "046024": "G628",
         "046028": "I622", "046030": "I942", "046033": "L833"}
NAMES = {"046005": "CAMAIORE", "046013": "FORTE DEI MARMI", "046018": "MASSAROSA", "046024": "PIETRASANTA",
         "046028": "SERAVEZZA", "046030": "STAZZEMA", "046033": "VIAREGGIO"}
WORDING = (
    (r"(?i)\baliquota ordinaria\b", "Aliquota unica"),
    (r"(?i)^applicabile a applicabile a\b", "Applicabile a"),
    (r"(?i)\bsino ad?\b", "fino a"),
    (r"(?i)\b(?:superiori a|maggiore di)\b", "oltre"),
    (r"\b(\d{1,3}),(\d{3}),(\d{2})\b", r"\1.\2,\3"),
    ("\x80", ""),
    ("€", ""),
)


class IrpefHistoryError(RuntimeError):
    pass


class Unavailable(Exception):
    """L'elenco dell'anno non è pubblicato."""


def label(n: int) -> str:
    return f"{n:,.0f} €".replace(",", ".")


def normalize(row: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Uniforma le varianti di scrittura delle fasce; restituisce la riga e le fasce cambiate."""
    out, changed = dict(row), []
    for key, value in row.items():
        if not key.startswith("FASCIA") or not (value or "").strip():
            continue
        text = value.strip()
        for pattern, repl in WORDING:
            text = re.sub(pattern, repl, text)
        text = re.sub(r"\s+", " ", text).strip()
        if text != re.sub(r"\s+", " ", value.strip()):
            changed.append(f"{key}: «{value.strip()}» → «{text}»")
        out[key] = text
    return out, changed


def read_year(raw: bytes, year: int) -> dict[str, dict[str, Any]]:
    """Elenco MEF dell'anno → codice Istat → {rule, amounts, wording}; IrpefHistoryError se un Comune non si legge."""
    text = ib.decode(raw)
    if "<html" in text[:500].lower():
        raise Unavailable(year)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not {"CODICE_CATASTALE", "COMUNE", "ALIQUOTA", "FASCIA"}.issubset(reader.fieldnames or []):
        raise IrpefHistoryError(f"{year}: intestazione inattesa {reader.fieldnames}")
    by_cat = {c: code for code, c in TOWNS.items()}
    found: dict[str, dict[str, Any]] = {}
    for row in reader:
        code = by_cat.get((row.get("CODICE_CATASTALE") or "").strip().upper())
        if code is None:
            continue
        if code in found:
            raise IrpefHistoryError(f"{year} {NAMES[code]}: righe duplicate")
        if (row.get("COMUNE") or "").strip().upper() != NAMES[code]:
            raise IrpefHistoryError(f"{year}: codice {TOWNS[code]} con nome {row.get('COMUNE')!r}")
        fixed, wording = normalize(row)
        try:
            r = ib.rule(fixed)
            amounts = [ib.amount(r, n) for n in ib.SCENARIOS]
        except ib.Unreadable as why:
            raise IrpefHistoryError(f"{year} {NAMES[code]}: {why}") from why
        found[code] = {"rule": r, "amounts": dict(zip(map(str, ib.SCENARIOS), amounts)), "wording": wording}
    if set(found) != set(TOWNS):
        raise IrpefHistoryError(f"{year}: Comuni assenti {sorted(set(TOWNS) - set(found))}")
    return found


def build_snapshot(fetcher: Callable[[str], bytes], published: dict[str, list[float]], last: int) -> dict[str, Any]:
    """`published`: codice Istat → importi pubblicati nei tre scenari per l'anno `last`."""
    years: dict[int, dict[str, Any]] = {}
    stop = None
    for year in range(last, FIRST - 1, -1):
        url = ib.MEF_URL.format(year=year)
        try:
            raw = fetcher(url)
            towns = read_year(raw, year)
        except (Unavailable, IrpefHistoryError) as why:
            if year == last:
                raise IrpefHistoryError(f"anno corrente {year}: {why}") from why
            stop = f"{year}: {why}"
            break
        years[year] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "towns": towns}
    for code, values in published.items():
        live = [years[last]["towns"][code]["amounts"][str(n)] for n in ib.SCENARIOS]
        if any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(live, values)):
            raise IrpefHistoryError(f"{code} {last}: fonte {live} ≠ pubblicato {values}")
        if years[last]["towns"][code]["wording"]:
            raise IrpefHistoryError(f"{code} {last}: l'anno corrente non deve richiedere uniformazioni")
    ordered = sorted(years)
    if len(ordered) < 2:
        raise IrpefHistoryError(f"serie di un solo anno ({stop})")
    return {
        "schemaVersion": 1, "version": f"mef-irpef-serie-{ordered[0]}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Dipartimento delle Finanze — MEF", "sourceUrl": ib.SOURCE_PAGE, "years": ordered,
        "scenarios": list(ib.SCENARIOS),
        "rule": ("Elenco generale MEF delle aliquote dell'anno A: importo con la stessa regola del valore pubblicato "
                 "(sotto la soglia di esenzione zero, altrimenti aliquota unica o scaglioni sull'intero imponibile, al centesimo). "
                 "Varianti di scrittura uniformate prima della lettura: " + "; ".join(p for p, _ in WORDING) + ". "
                 "Solo anni consecutivi in cui tutti e sette i Comuni si leggono senza ambiguità."),
        "stoppedAt": stop,
        "sources": {str(y): {k: v for k, v in d.items() if k != "towns"} for y, d in years.items()},
        "towns": {code: {"cadastral": cat, **{str(y): years[y]["towns"][code] for y in ordered}} for code, cat in TOWNS.items()},
        "series": {code: {str(n): [years[y]["towns"][code]["amounts"][str(n)] for y in ordered] for n in ib.SCENARIOS} for code in TOWNS},
        "qualityGate": {"status": "PASS", "note": f"Anno {last} identico ai valori pubblicati per i 7 Comuni nei tre scenari."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    if snapshot["scenarios"] != list(ib.SCENARIOS):
        raise IrpefHistoryError("scenari diversi da quelli pubblicati")
    for row in metric["rows"]:
        series = snapshot["series"][row["code"]]
        for n, part in zip(ib.SCENARIOS, row["parts"]):
            if part["selectorLabel"] != label(n) or not math.isclose(series[str(n)][-1], part["value"], rel_tol=0, abs_tol=1e-9):
                raise IrpefHistoryError(f"{row['town']} {n}: serie {series[str(n)][-1]} ≠ valore {part['value']}")
        row["componentSeries"] = {label(n): {"years": list(years), "values": list(series[str(n)])} for n in ib.SCENARIOS}
        row["series"] = dict(row["componentSeries"][label(ib.SCENARIOS[0])])
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    note = (f" Serie {years[0]}–{years[-1]} dagli elenchi MEF di ciascun anno, con la stessa regola e gli stessi scenari;"
            " negli elenchi più vecchi sono uniformate solo varianti di scrittura (per esempio «aliquota ordinaria» per «aliquota unica»).")
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
