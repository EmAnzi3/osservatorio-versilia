#!/usr/bin/env python3
"""Consumo di suolo ISPRA: nuova edizione annuale nei sette Comuni, Toscana e Italia.

Usato da `update_source_data.py ispra-soil --year AAAA`. Legge l'archivio
completo «Com_Prov_Reg_Naz» dell'edizione AAAA+1 dalla libreria ISPRA e:

- ricostruisce in `territorio-v137-official.json` le famiglie `landUse` e
  `landUseChange` (2006, 2012, 2015…AAAA) dall'edizione nuova, che rivede anche
  gli anni precedenti; i fogli `_rev` non sono usati, quindi il flusso dell'ultimo
  anno è misurato da ISPRA sulla carta rivista dell'anno prima e non coincide con
  la differenza tra gli stock pubblicati;
- scrive `a3-ispra-soil-benchmark-AAAA.json` con Toscana e Italia dalle righe
  ufficiali dell'edizione;
- aggiorna nel catalogo valori correnti, serie e benchmark dei due indicatori.

Il m² per residente usa la popolazione canonica del catalogo dello stesso anno.
Quando ISPRA rivede i confini, la superficie comunale di un anno può differire
da quella dell'ultimo anno: la riga di quell'anno porta allora `municipalAreaHa`.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "source-snapshots" / "territorio-v137-official.json"
BENCH_PREFIX = "data/source-snapshots/a3-ispra-soil-benchmark-"
LIBRARY = "https://groupware.sinanet.isprambiente.it/uso-copertura-e-consumo-di-suolo/library/consumo-di-suolo/indicatori"
PAGE = "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo"
TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
CODES = {"Camaiore": "046005", "Forte dei Marmi": "046013", "Massarosa": "046018", "Pietrasanta": "046024",
         "Seravezza": "046028", "Stazzema": "046030", "Viareggio": "046033"}
UA = {"User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"}


class SoilError(RuntimeError):
    pass


def stock_years(year: int) -> list[int]:
    return [2006, 2012, *range(2015, year + 1)]


def change_years(year: int) -> list[int]:
    return [2012, *range(2015, year + 1)]


def latest_benchmark() -> Path:
    found = sorted(ROOT.glob(BENCH_PREFIX + "*.json"),
                   key=lambda p: int(re.search(r"(\d{4})\.json$", p.name).group(1)))
    if not found:
        raise SoilError("nessuno snapshot benchmark ISPRA suolo")
    return found[-1]


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
        return r.read()


def edition_url(year: int) -> str:
    page = fetch(LIBRARY).decode("utf-8", errors="replace")
    pattern = rf"href=[\"']([^\"']*consumo_suolo_{year + 1}_Com_Prov_Reg_Naz_v[\d.]+\.xlsx)[\"']"
    found = sorted(set(re.findall(pattern, page, flags=re.I)))
    if not found:
        raise SoilError(f"edizione {year + 1} non trovata nella libreria ISPRA")
    url = found[-1]
    return url if url.startswith("http") else "https://groupware.sinanet.isprambiente.it" + url


def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or value is None:
        raise SoilError(f"{label}: valore assente")
    x = float(value)
    if not math.isfinite(x):
        raise SoilError(f"{label}: valore non finito")
    return x


def sheet(wb, name: str, key: str) -> dict[int, dict[str, Any]]:
    if name not in wb.sheetnames:
        raise SoilError(f"foglio {name} assente")
    rows = wb[name].iter_rows(values_only=True)
    headers = [str(h) if h is not None else "" for h in next(rows)]
    if key not in headers or not {"csuolo1", "csuolo2", "csuolo4"} <= set(headers):
        raise SoilError(f"{name}: intestazioni inattese")
    out = {}
    for raw in rows:
        try:
            code = int(raw[headers.index(key)])
        except (TypeError, ValueError):
            continue
        out[code] = dict(zip(headers, raw))
    return out


def populations(site: dict) -> dict[str, dict[int, float]]:
    metric = site["metrics"]["population"]
    out = {}
    for row in metric["rows"]:
        s = row.get("series") or {}
        out[row["town"]] = {int(y): float(v) for y, v in zip(s.get("years", []), s.get("values", [])) if v is not None}
        out[row["town"]][int(str(metric["meta"]["year"])[:4])] = float(row["value"])
    if set(out) != set(TOWNS):
        raise SoilError("popolazione: copertura non 7/7")
    return out


def build(wb, year: int, pops: dict[str, dict[int, float]]) -> tuple[dict, dict, dict]:
    years, cyears = stock_years(year), change_years(year)
    data = {y: sheet(wb, f"Comuni_{y}", "pro_com") for y in years}
    land, change = {}, {}
    for town in TOWNS:
        code = int(CODES[town])
        if any(code not in data[y] for y in years):
            raise SoilError(f"{town}: Comune assente in almeno un'annualità")
        latest = data[year][code]
        area = finite(latest["csuolo1"], town) + finite(latest["csuolo2"], town)
        rows, crow = {}, {}
        for y in years:
            r = data[y][code]
            consumed, pct = finite(r["csuolo1"], f"{town} {y}"), finite(r["csuolo4"], f"{town} {y}")
            pop = pops[town].get(y)
            rows[str(y)] = {"consumedHa": round(consumed, 6), "consumedPct": round(pct, 6),
                            "sqmPerResident": round(consumed * 10_000 / pop, 6) if pop else None,
                            "population": int(round(pop)) if pop else None}
            year_area = round(consumed + finite(r["csuolo2"], f"{town} {y}"), 6)
            if not math.isclose(year_area, round(area, 6), rel_tol=0, abs_tol=1e-9):
                rows[str(y)]["municipalAreaHa"] = year_area  # superficie ISPRA di quell'anno, se diversa dall'ultima
            if y in cyears:
                crow[str(y)] = {"grossHa": round(float(r["csuolo10"] or 0), 6), "netHa": round(float(r["csuolo8"] or 0), 6)}
        land[town] = {"municipalAreaHa": round(area, 6), "rows": rows}
        change[town] = {"rows": crow}
    vland, vchange = {}, {}
    for y in years:
        consumed = sum(land[t]["rows"][str(y)]["consumedHa"] for t in TOWNS)
        area = sum(finite(data[y][int(CODES[t])]["csuolo1"], t) + finite(data[y][int(CODES[t])]["csuolo2"], t) for t in TOWNS)
        pop = [pops[t].get(y) for t in TOWNS]
        total = sum(pop) if all(pop) else None
        vland[str(y)] = {"consumedHa": round(consumed, 6), "consumedPct": round(consumed / area * 100, 6),
                         "sqmPerResident": round(consumed * 10_000 / total, 6) if total else None,
                         "population": int(round(total)) if total else None}
    for y in cyears:
        vchange[str(y)] = {k: round(sum(change[t]["rows"][str(y)][k] for t in TOWNS), 6) for k in ("grossHa", "netHa")}
    regions = sheet(wb, f"Regioni_{year}", "cod_reg")
    national = sheet(wb, f"Nazionale_{year}", "cod_naz")
    if 9 not in regions or str(regions[9].get("nome_regione")) != "Toscana" or len(regions) != 20 or 0 not in national:
        raise SoilError("righe ufficiali Toscana/Italia inattese")
    tus, ita = regions[9], national[0]
    bench = {
        "landUse": {"year": str(year), "unit": "percent", "formula": "suolo consumato / superficie territoriale × 100",
                    "tuscany": finite(tus["csuolo4"], "Toscana"), "italy": finite(ita["csuolo4"], "Italia")},
        "landUseChange": {"year": str(year), "unit": "hectares", "formula": f"incremento netto {year - 1}-{year} [ettari]",
                          "tuscany": finite(tus["csuolo8"], "Toscana"), "italy": finite(ita["csuolo8"], "Italia")},
    }
    return ({"years": years, "municipalities": land, "versilia": {"rows": vland}},
            {"years": cyears, "municipalities": change, "versilia": {"rows": vchange}}, bench)


def fmt(value: float, digits: int, suffix: str) -> str:
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suffix
