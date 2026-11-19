#!/usr/bin/env python3
"""Serie storiche del parco autovetture ACI per i sette Comuni: motorizzazione e quota Euro 0–3.

Ogni edizione dell'Autoritratto ACI contiene il foglio «AV per comune» del file
`Circolante_Copert_AAAA` (xlsx o, per alcuni anni, xls) con le autovetture per classe
Euro e il totale al 31 dicembre. Il 2021 non è pubblicato nell'archivio ACI.

* motorizzazione = autovetture al 31 dicembre / residenti al 1° gennaio dell'anno dopo × 1.000
  (stessa regola del valore corrente; residenti dalla serie pubblicata del catalogo);
* quota Euro 0–3 = autovetture Euro 0–3 / autovetture totali × 100.
I valori sono arrotondati a un decimale come quelli pubblicati; l'ultimo anno della serie
deve coincidere con il valore corrente del catalogo.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable

BASE = "https://aci.gov.it/app/uploads/"
ARCHIVES = {
    2018: "2025/02/Parco_Veicolare_2018.zip",
    2019: "2024/06/Parco_veicoli_2019.zip",
    2020: "2024/06/Autoritratto2020_Parco_veicolare.zip",
    2022: "2024/06/Consistenza_Parco_veicoli_2022.zip",
    2023: "2024/06/Autoritratto2023_Parco_veicolare.zip",
    2024: "2025/06/Autoritratto-2024-Parco-Veicolare.zip",
    2025: "2026/06/Autoritratto2025_Parco_veicolare.zip",
}
SNAPSHOT = "data/source-snapshots/aci-autovetture-serie.json"
TOWNS = {"046005": "CAMAIORE", "046013": "FORTE DEI MARMI", "046018": "MASSAROSA", "046024": "PIETRASANTA",
         "046028": "SERAVEZZA", "046030": "STAZZEMA", "046033": "VIAREGGIO"}
EURO = ("EURO 0", "EURO 1", "EURO 2", "EURO 3")


class VehiclesError(RuntimeError):
    pass


def _rows(name: str, raw: bytes) -> list[list[Any]]:
    """Righe del foglio «AV per comune» (xlsx con openpyxl, xls con xlrd)."""
    if name.lower().endswith(".xlsx"):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sheets = [s for s in wb.sheetnames if s.strip().upper().startswith("AV PER COMUNE")]
        if len(sheets) != 1:
            raise VehiclesError(f"{name}: fogli «AV per comune» {sheets}")
        ws = wb[sheets[0]]
        ws.reset_dimensions()
        return [list(r) for r in ws.iter_rows(values_only=True)]
    import xlrd

    book = xlrd.open_workbook(file_contents=raw)
    sheets = [s for s in book.sheet_names() if s.strip().upper().startswith("AV PER COMUNE")]
    if len(sheets) != 1:
        raise VehiclesError(f"{name}: fogli «AV per comune» {sheets}")
    sh = book.sheet_by_name(sheets[0])
    return [[(None if c.ctype in (0, 6) else c.value) for c in sh.row(i)] for i in range(sh.nrows)]


def year_counts(raw: bytes, year: int) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if "copert" in n.lower() and n.lower().endswith((".xlsx", ".xls"))]
        if len(names) != 1:
            raise VehiclesError(f"{year}: file Copert {names} fra {z.namelist()}")
        rows = _rows(names[0], z.read(names[0]))
    head = next((i for i, r in enumerate(rows) if r and str(r[0] or "").strip().upper() == "PROVINCIA"), None)
    if head is None:
        raise VehiclesError(f"{year}: intestazione PROVINCIA/COMUNE assente")
    header = [str(h or "").strip().upper() for h in rows[head]]
    if header[1] != "COMUNE" or any(e not in header for e in EURO) or "TOTALE" not in header:
        raise VehiclesError(f"{year}: intestazione inattesa {header}")
    idx = {h: header.index(h) for h in (*EURO, "TOTALE")}
    out, province = {}, None
    for r in rows[head + 1:]:
        if not r or len(r) <= idx["TOTALE"]:
            continue
        if r[0]:
            province = str(r[0]).strip().upper()
        name = str(r[1] or "").strip().upper()
        if province == "LUCCA" and name in TOWNS.values():
            num = lambda v: int(round(float(v))) if v not in (None, "") else 0
            euro = [num(r[idx[e]]) for e in EURO]
            total = num(r[idx["TOTALE"]])
            if name in {v["name"] for v in out.values()} or total <= 0:
                raise VehiclesError(f"{year}: riga duplicata o vuota per {name}")
            code = next(c for c, n in TOWNS.items() if n == name)
            out[code] = {"name": name, "euro0to3": euro, "total": total}
    if set(out) != set(TOWNS):
        raise VehiclesError(f"{year}: Comuni trovati {sorted(v['name'] for v in out.values())}")
    return {"member": names[0], "towns": out}


def round1(x: Decimal) -> float:
    return float(x.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def build_snapshot(fetcher: Callable[[str], bytes], population: dict[str, dict[int, int]], current: dict[str, dict[str, float]]) -> dict[str, Any]:
    """`population`: codice → {anno: residenti al 1° gennaio}; `current`: metrica → {codice: valore pubblicato}."""
    years = {}
    for year, path in sorted(ARCHIVES.items()):
        url = BASE + path
        raw = fetcher(url)
        counts = year_counts(raw, year)
        years[year] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), **counts}
    series = {"motorization": {}, "pollutingCars": {}}
    for code in TOWNS:
        mot, pol = [], []
        for year, y in years.items():
            t = y["towns"][code]
            pop = population[code].get(year + 1)
            if not pop:
                raise VehiclesError(f"{code}: residenti al 1° gennaio {year + 1} assenti")
            mot.append(round1(Decimal(t["total"]) / Decimal(pop) * 1000))
            pol.append(round1(Decimal(sum(t["euro0to3"])) / Decimal(t["total"]) * 100))
        series["motorization"][code] = mot
        series["pollutingCars"][code] = pol
    last = max(years)
    for key, values in current.items():
        for code, value in values.items():
            if series[key][code][-1] != value:
                raise VehiclesError(f"{key} {code} {last}: serie {series[key][code][-1]} ≠ pubblicato {value}")
    return {
        "schemaVersion": 1, "version": f"aci-autovetture-serie-{min(years)}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "ACI — Autoritratto, parco veicolare", "sourceUrl": "https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/",
        "years": sorted(years), "missingYears": [y for y in range(min(years), last + 1) if y not in years],
        "archives": {str(y): {k: v for k, v in d.items() if k != "towns"} for y, d in years.items()},
        "towns": {code: {str(y): years[y]["towns"][code] for y in years} for code in TOWNS},
        "series": series,
        "rule": ("Motorizzazione = autovetture al 31 dicembre / residenti al 1° gennaio dell'anno successivo × 1.000; "
                 "quota Euro 0–3 = autovetture Euro 0–3 / totale × 100; arrotondamento a un decimale come i valori pubblicati."),
        "qualityGate": {"status": "PASS", "note": f"Ultimo anno ({last}) identico al valore pubblicato per i 7 Comuni."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    years = snapshot["years"]
    for key in ("motorization", "pollutingCars"):
        metric = metrics[key]
        for row in metric["rows"]:
            values = snapshot["series"][key][row["code"]]
            if values[-1] != row["value"]:
                raise VehiclesError(f"{key} {row['town']}: serie {values[-1]} ≠ valore {row['value']}")
            row["series"] = {"years": list(years), "values": list(values)}
        metric["meta"].setdefault("sourceMeta", {})
        metric["meta"]["sourceMeta"]["historySnapshot"] = path
        gap = ", ".join(str(y) for y in snapshot["missingYears"])
        note = f" Serie {years[0]}–{years[-1]} dagli archivi ACI dell'Autoritratto" + (f"; il {gap} non è pubblicato." if gap else ".")
        if note.strip() not in metric["method"].get("caveat", ""):
            metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
