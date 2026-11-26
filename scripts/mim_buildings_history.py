#!/usr/bin/env python3
"""Serie storica dei cinque indicatori dell'Anagrafe dell'Edilizia Scolastica MIM (scuole statali).

Stessa regola del valore pubblicato (a.s. 2024/25): per ogni anno scolastico il CSV MIM del dataset
dà, riga per scuola, l'edificio e i suoi attributi; le scuole sono collocate nel Comune con
l'anagrafe delle scuole statali dello stesso anno; ogni edificio conta una volta e le quote sono
calcolate con le funzioni di `materialize_scuola_mim` (denominatore = risposte definite;
NON DEFINITO resta separato).

Si usano solo gli anni pubblicati dal MIM con lo stesso tracciato (STA2021, dal 2020/21). Un anno
in cui un campo ha valori fuori dal tracciato noto, un edificio con attributi discordanti nei sette
Comuni o un edificio associato a più Comuni della Versilia non entra nella serie di quell'indicatore.
L'anno 2024/25 deve riprodurre esattamente i conteggi dello snapshot pubblicato.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from collections import Counter
from datetime import date
from typing import Any, Callable

import materialize_scuola_mim as ms

SNAPSHOT = "data/source-snapshots/mim-edilizia-scolastica-serie.json"
PUBLISHED = "data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json"
BASE = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/"
LAST = "2024/25"
REGISTRY = {  # anagrafe scuole statali per anno scolastico
    "2020/21": "SCUANAGRAFESTAT20202120210831.csv", "2021/22": "SCUANAGRAFESTAT20212220220831.csv",
    "2022/23": "SCUANAGRAFESTAT20222320230831.csv", "2023/24": "SCUANAGRAFESTAT20232420240831.csv",
    "2024/25": "SCUANAGRAFESTAT20242520250831.csv",
}
STAMPS = {"2020/21": "20202120211116", "2021/22": "20212220220908", "2022/23": "20222320230731",
          "2023/24": "20232420250714", "2024/25": "20242520250806"}
DATASETS = {  # indicatore → (prefisso file MIM, campi locali → colonna, funzione delle parti)
    ms.SAFETY_KEY: ("EDICONSICUREZZASTA2021", {"agibilita": "CERTIFICATOSEGNALAZIONEAGIBILITA", "cpi": "CERTIFICATOPREVENZIONEINCENDI",
                    "sciaAntincendio": "SCIAANTINCENDIO", "rinnovoAntincendio": "ATTESTAZIONERINNOVOPERIODICOCONFORMITAANTINCENDIO"}, ms.safety_parts),
    ms.ACCESS_KEY: ("EDISUPBARARCSTA2021", {"accessibilita": "ACCORGIMENTISUPERAMENTOBARRIEREARCHITETTONICHE"}, ms.accessibility_parts),
    ms.FACILITIES_KEY: ("EDIAMBFUNZSTA2021", {"mensa": "MENSA", "palestra": "PALESTRA"}, ms.facilities_parts),
    ms.AGE_KEY: ("EDIETAORIGINESTA2021", {"periodoCostruzione": "PERIODOCOSTRUZIONE"}, ms.age_parts),
    ms.TRANSPORT_KEY: ("EDICOLLEGAMENTISTA2021", {"scuolabus": "SCUOLABUS", "tplUrbano": "TRASPORTIPUBBLICIURBANI",
                       "tplInterurbano": "TRASPORTIPUBBLICIINTERURBANI"}, ms.transport_parts),
}
UNKNOWN = {"NON DEFINITO", "", "-", "_"}
ALLOWED = {"SI", "NO"} | UNKNOWN
EXTRA = {"agibilita": {"IN PARTE"}}  # agibilità parziale: valore del tracciato, non conta come piena (status_part)


class MimHistoryError(RuntimeError):
    pass


class Unavailable(Exception):
    """File non pubblicato per quell'anno scolastico."""


def dataset_url(prefix: str, year: str) -> str:
    return f"{BASE}{prefix}{STAMPS[year]}.csv"


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()


def canon(field: str, value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if field == "periodoCostruzione":
        return "NON DEFINITO" if text.upper() in UNKNOWN else text.lower()
    return text.upper()


def read_csv(raw: bytes, what: str) -> list[dict[str, str]]:
    text = raw.decode("utf-8-sig", errors="replace")
    if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        raise Unavailable(what)
    try:
        delimiter = csv.Sniffer().sniff(text[:12000], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = [{norm(k): v for k, v in row.items() if k is not None} for row in reader]
    if not rows:
        raise MimHistoryError(f"{what}: CSV vuoto")
    return rows


def school_towns(rows: list[dict[str, str]], towns: set[str]) -> dict[str, str]:
    """Codice scuola → Comune (maiuscolo); per le scuole fuori dalla Versilia il valore è stringa vuota."""
    out: dict[str, str] = {}
    for row in rows:
        code = (row.get("CODICESCUOLA") or "").strip().upper()
        if not code:
            continue
        town = norm(row.get("DESCRIZIONECOMUNE"))
        town = town if town in towns else ""
        if code in out and out[code] != town:
            raise MimHistoryError(f"anagrafe: {code} in due Comuni")
        out[code] = town
    return out


def town_counts(rows: list[dict[str, str]], schools: dict[str, str], fields: dict[str, str], what: str) -> dict[str, dict[str, Any]]:
    """Comune (maiuscolo) → {buildings, campo → Counter}; edifici univoci, attributi coerenti."""
    buildings: dict[str, dict[str, Any]] = {}
    missing = [col for col in fields.values() if col not in rows[0]]
    if missing or "CODICEEDIFICIO" not in rows[0] or "CODICESCUOLA" not in rows[0]:
        raise MimHistoryError(f"{what}: colonne assenti {missing}")
    unmapped = set()
    for row in rows:
        code = (row.get("CODICESCUOLA") or "").strip().upper()
        town = schools.get(code)
        if town is None and code.startswith("LU"):
            unmapped.add(code)  # scuola della provincia di Lucca assente dalle anagrafi: potrebbe essere in Versilia
        bid = (row.get("CODICEEDIFICIO") or "").strip()
        if not town or not bid:
            continue
        rec = buildings.setdefault(bid, {"towns": set(), "fields": {k: set() for k in fields}})
        rec["towns"].add(town)
        for local, col in fields.items():
            rec["fields"][local].add(canon(local, row.get(col)))
    if unmapped:
        raise MimHistoryError(f"{what}: scuole lucchesi non collocabili {sorted(unmapped)[:5]}")
    out: dict[str, dict[str, Any]] = {}
    for bid, rec in buildings.items():
        if len(rec["towns"]) != 1:
            raise MimHistoryError(f"{what}: edificio {bid} in più Comuni {sorted(rec['towns'])}")
        town = next(iter(rec["towns"]))
        entry = out.setdefault(town, {"buildings": 0, **{k: Counter() for k in fields}})
        entry["buildings"] += 1
        for local, values in rec["fields"].items():
            if len(values) != 1:
                raise MimHistoryError(f"{what}: edificio {bid} con valori discordanti per {local} {sorted(values)}")
            value = next(iter(values))
            allowed = set(ms.PERIOD_ORDER) | {"NON DEFINITO"} if local == "periodoCostruzione" else ALLOWED | EXTRA.get(local, set())
            if value not in allowed:
                raise MimHistoryError(f"{what}: valore fuori tracciato {local}={value!r}")
            entry[local][value] += 1
    return out


def build_snapshot(fetcher: Callable[[str], bytes], published: dict[str, Any]) -> dict[str, Any]:
    towns = {norm(t): t for t in published["towns"]}
    years = list(STAMPS)
    sources: dict[str, Any] = {}
    data: dict[str, dict[str, Any]] = {key: {} for key in DATASETS}
    skipped: dict[str, list[str]] = {key: [] for key in DATASETS}
    registries: dict[str, dict[str, str]] = {}
    for year in years:
        url = BASE + REGISTRY[year]
        try:
            raw = fetcher(url)
            registries[year] = school_towns(read_csv(raw, url), set(towns))
        except Unavailable:
            if year == LAST:
                raise MimHistoryError(f"anagrafe {year} non disponibile")
            continue
        sources[f"anagrafe {year}"] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    for year in years:
        # anagrafe dell'anno; per i codici che non vi compaiono, quella dell'anno più vicino che li contiene
        schools: dict[str, str] = {}
        for other in sorted(registries, key=lambda y: (abs(years.index(y) - years.index(year)), -years.index(y)), reverse=True):
            schools.update(registries[other])
        for key, (prefix, fields, _) in DATASETS.items():
            url = dataset_url(prefix, year)
            try:
                raw = fetcher(url)
                counts = town_counts(read_csv(raw, url), schools, fields, f"{prefix} {year}")
            except (Unavailable, MimHistoryError) as why:
                if year == LAST:
                    raise MimHistoryError(f"{key} {year}: {why}") from why
                skipped[key].append(f"{year}: {why}")
                continue
            if set(counts) != set(towns):
                skipped[key].append(f"{year}: Comuni senza edifici {sorted(set(towns) - set(counts))}")
                continue
            sources[f"{prefix} {year}"] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            data[key][year] = {towns[t]: {"buildings": c["buildings"], **{f: dict(c[f]) for f in fields}} for t, c in counts.items()}
    for key, (_, fields, _) in DATASETS.items():
        for town, expected in published["towns"].items():
            got = data[key][LAST][town]
            if got["buildings"] != int(expected["buildings"]):
                raise MimHistoryError(f"{key} {town} {LAST}: edifici {got['buildings']} ≠ {expected['buildings']}")
            for field in fields:
                want = {canon(field, k): int(v) for k, v in expected[field].items() if int(v)}
                if got[field] != want:
                    raise MimHistoryError(f"{key} {town} {LAST}/{field}: {got[field]} ≠ {want}")
        if len(data[key]) < 2:
            raise MimHistoryError(f"{key}: un solo anno scolastico leggibile ({skipped[key]})")
    return {
        "schemaVersion": 1, "version": f"mim-edilizia-scolastica-serie-{years[0].replace('/', '')}-{LAST.replace('/', '')}-v1",
        "retrieved": date.today().isoformat(), "publisher": "Ministero dell'Istruzione e del Merito — Open Data, Anagrafe dell'Edilizia Scolastica",
        "license": "IODL 2.0",
        "rule": ("Per anno scolastico: CSV del dataset (tracciato STA2021, scuole statali) e anagrafe delle scuole statali dello stesso anno; "
                 "edifici univoci per Comune, quote con le funzioni di materialize_scuola_mim. Anni con valori fuori tracciato, edifici "
                 "discordanti o in più Comuni esclusi dall'indicatore; 2024/25 identico allo snapshot pubblicato."),
        "years": {key: sorted(values) for key, values in data.items()}, "skipped": skipped,
        "sources": sources, "towns": data,
        "qualityGate": {"status": "PASS", "note": f"{LAST} identico ai conteggi pubblicati per i 7 Comuni nei cinque dataset."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    for key, (_, _, parts_of) in DATASETS.items():
        metric = metrics[key]
        years = snapshot["years"][key]
        if not years or years[-1] != LAST or metric["meta"]["year"] != LAST:
            raise MimHistoryError(f"{key}: serie non allineata all'anno pubblicato")
        for row in metric["rows"]:
            by_year = {y: parts_of(snapshot["towns"][key][y][row["town"]]) for y in years}
            for part, live in zip(row["parts"], by_year[LAST]):
                same = (part["value"] is None and live["value"] is None) or (
                    part["value"] is not None and live["value"] is not None and math.isclose(part["value"], live["value"], rel_tol=0, abs_tol=1e-9))
                if part["selectorLabel"] != live["selectorLabel"] or not same:
                    raise MimHistoryError(f"{key} {row['town']} {part['selectorLabel']}: serie ≠ valore pubblicato")
            series = {}
            for index, part in enumerate(row["parts"]):
                points = [(y, by_year[y][index]["value"]) for y in years if by_year[y][index]["value"] is not None]
                series[part["selectorLabel"]] = {"years": [y for y, _ in points], "values": [v for _, v in points]}
            row["componentSeries"] = series
            row["series"] = dict(series[row["parts"][0]["selectorLabel"]]) if series[row["parts"][0]["selectorLabel"]]["years"] else None
        metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
        gaps = [s for s in snapshot["skipped"][key]]
        note = f"Serie {years[0]}–{years[-1]} dai file MIM di ciascun anno scolastico, con la stessa regola."
        if gaps:
            note += " Anni non inclusi: " + "; ".join(gaps) + "."
        metric["method"]["historyNote"] = note
