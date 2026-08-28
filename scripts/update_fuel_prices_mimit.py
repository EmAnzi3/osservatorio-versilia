#!/usr/bin/env python3
"""Aggiorna l'indicatore carburanti con l'ultimo CSV ufficiale MIMIT.

Non è collegato al workflow periodico: l'esecuzione resta esplicita e produce
solo valori ricostruibili dalla fonte primaria, con mediana comunale dei prezzi
self-service. Stazzema può restare n.d.; gli altri sei Comuni devono essere coperti.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

import audit_fuel_prices_mimit as audit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "costi-fiscalita-validated-2026-08.json"
METRIC_KEY = "fuelPrices"

MONTHS = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile", 5: "maggio", 6: "giugno",
    7: "luglio", 8: "agosto", 9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect() -> dict[str, Any]:
    anag_date, anag = audit.parse_export(audit.fetch(audit.ANAG))
    price_date, prices = audit.parse_export(audit.fetch(audit.PRICES))
    if not anag or not prices:
        raise RuntimeError("dataset MIMIT vuoto")

    aid = audit.find_field(anag[0], "idimpianto")
    atown = audit.find_field(anag[0], "Comune")
    aprov = audit.find_field(anag[0], "Provincia")
    pid = audit.find_field(prices[0], "idimpianto")
    pfuel = audit.find_field(prices[0], "descCarburante")
    pprice = audit.find_field(prices[0], "prezzo")
    pself = audit.find_field(prices[0], "isSelf")

    wanted = {audit.norm(town): town for town in audit.TOWNS}
    station_town: dict[str, str] = {}
    for row in anag:
        town = wanted.get(audit.norm(row.get(atown, "")))
        if not town:
            continue
        province = audit.norm(row.get(aprov, ""))
        if province not in {"lu", "lucca"} and "lucca" not in province:
            continue
        station_town[str(row.get(aid, "")).strip()] = town

    values = {town: {fuel: [] for fuel in audit.FUELS} for town in audit.TOWNS}
    seen: set[tuple[str, str]] = set()
    for row in prices:
        station = str(row.get(pid, "")).strip()
        town = station_town.get(station)
        if not town or str(row.get(pself, "")).strip() not in {"1", "1.0"}:
            continue
        fuel = audit.norm(row.get(pfuel, ""))
        if fuel not in audit.FUELS:
            continue
        try:
            price = float(str(row.get(pprice, "")).strip().replace(",", "."))
        except ValueError:
            continue
        if not 0.5 <= price <= 5:
            continue
        key = (station, fuel)
        if key in seen:
            continue
        seen.add(key)
        values[town][fuel].append(price)

    towns: dict[str, Any] = {}
    covered = 0
    for town in audit.TOWNS:
        benzina = values[town]["benzina"]
        gasolio = values[town]["gasolio"]
        item = {
            "benzina": round(statistics.median(benzina), 3) if benzina else None,
            "gasolio": round(statistics.median(gasolio), 3) if gasolio else None,
            "stations": max(len(benzina), len(gasolio)),
        }
        if item["benzina"] is not None and item["gasolio"] is not None:
            covered += 1
        towns[town] = item

    missing = [
        town for town in audit.TOWNS
        if town != "Stazzema" and (towns[town]["benzina"] is None or towns[town]["gasolio"] is None)
    ]
    if missing:
        raise RuntimeError(f"copertura insufficiente nei sei comuni attesi: {missing}")

    reference_date = price_date or anag_date
    if not reference_date:
        raise RuntimeError("data di riferimento MIMIT non trovata")
    return {
        "source": "MIMIT - Prezzi praticati e anagrafica impianti",
        "sourceUrls": {"anagrafica": audit.ANAG, "prezzi": audit.PRICES},
        "referenceDate": reference_date,
        "statistic": "mediana comunale impianti attivi, self-service",
        "coverage": f"{covered}/7",
        "towns": towns,
    }


def human_date(value: str) -> str:
    try:
        year, month, day = (int(part) for part in value.split("-"))
        return f"{day} {MONTHS[month]} {year}"
    except Exception:
        return value


def mean(values: list[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return statistics.fmean(valid) if valid else None


def update_metric(data: dict[str, Any], fuel: dict[str, Any]) -> None:
    metric = data.get("metrics", {}).get(METRIC_KEY)
    if not isinstance(metric, dict):
        raise RuntimeError(f"indicatore {METRIC_KEY} non trovato")

    reference_date = str(fuel["referenceDate"])
    metric.setdefault("meta", {})["year"] = reference_date
    metric["sourceUrl"] = audit.PRICES

    row_by_town = {
        str(row.get("town")): row
        for row in metric.get("rows", [])
        if isinstance(row, dict)
    }
    for town in audit.TOWNS:
        row = row_by_town.get(town)
        if row is None:
            raise RuntimeError(f"riga carburanti mancante per {town}")
        values = fuel["towns"][town]
        benzina = values["benzina"]
        gasolio = values["gasolio"]
        row["value"] = benzina
        row["benchmarkValue"] = benzina
        row["series"] = {"years": [reference_date], "values": [benzina]}
        row["stationCount"] = int(values["stations"])
        row["parts"] = [
            {"label": "Benzina self", "selectorLabel": "Benzina self", "value": benzina, "unit": "eurliter"},
            {"label": "Gasolio self", "selectorLabel": "Gasolio self", "value": gasolio, "unit": "eurliter"},
        ]
        row["componentSeries"] = {
            "Benzina self": {"years": [reference_date], "values": [benzina]},
            "Gasolio self": {"years": [reference_date], "values": [gasolio]},
        }

    benzina_values = [fuel["towns"][town]["benzina"] for town in audit.TOWNS]
    gasolio_values = [fuel["towns"][town]["gasolio"] for town in audit.TOWNS]
    aggregate = metric.setdefault("aggregate", {})
    aggregate["value"] = mean(benzina_values)
    parts = aggregate.setdefault("parts", [])
    by_label = {str(part.get("label")): part for part in parts if isinstance(part, dict)}
    for label, value in (("Benzina self", mean(benzina_values)), ("Gasolio self", mean(gasolio_values))):
        part = by_label.get(label)
        if part is None:
            part = {"label": label, "selectorLabel": label, "unit": "eurliter"}
            parts.append(part)
        part["value"] = value

    method = metric.setdefault("method", {})
    method["coverage"] = str(fuel["coverage"])
    method["caveat"] = f"Fotografia del {human_date(reference_date)}; Stazzema non ha impianti attivi nel dataset."


def main() -> int:
    current = collect()
    data = load(DATA)
    validated = load(SNAPSHOT)
    previous = str(validated.get("fuel", {}).get("referenceDate") or "")
    validated["fuel"] = current
    update_metric(data, current)
    save(SNAPSHOT, validated)
    save(DATA, data)
    print(json.dumps({
        "status": "updated" if previous != current["referenceDate"] else "refreshed_same_period",
        "previousReferenceDate": previous,
        "referenceDate": current["referenceDate"],
        "coverage": current["coverage"],
        "towns": current["towns"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())