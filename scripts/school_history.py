#!/usr/bin/env python3
"""Serie storiche MIM per i sette Comuni: alunni, alunni per classe, tempo pieno nella primaria.

Stessa regola del valore pubblicato (a.s. 2024/25), ripetuta per ogni anno scolastico dal
2015/16: le scuole statali e paritarie localizzate nel Comune (anagrafe MIM dell'anno:
REGIONE = TOSCANA, PROVINCIA = LUCCA, DESCRIZIONECOMUNE), gli alunni (maschi + femmine) e le
classi delle scuole primarie e secondarie, gli alunni della primaria a «TEMPO PIENO» sul totale
della primaria. L'ultimo anno deve coincidere con i valori pubblicati (stessi conteggi).
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import defaultdict
from datetime import date
from typing import Any, Callable

BASE = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
SNAPSHOT = "data/source-snapshots/mim-alunni-serie.json"
KEYS = ("schoolStudents", "studentsPerClass", "primaryFullTimeShare")
TOWNS = {"046005": "CAMAIORE", "046013": "FORTE DEI MARMI", "046018": "MASSAROSA", "046024": "PIETRASANTA",
         "046028": "SERAVEZZA", "046030": "STAZZEMA", "046033": "VIAREGGIO"}
ORDERS = ("PRIMARIA", "SECONDARIA")


def files(start: int) -> dict[str, str]:
    """Nomi dei file MIM dell'anno scolastico start/start+1 (dati al 31 agosto dell'anno dopo;
    l'anagrafe 2017/18 è quella al 1° settembre 2017)."""
    tag = f"{start}{(start + 1) % 100:02d}"
    stamp = f"{start + 1}0831"
    registry = "20170901" if start == 2017 else stamp
    return {"registry_state": f"SCUANAGRAFESTAT{tag}{registry}.csv", "registry_private": f"SCUANAGRAFEPAR{tag}{registry}.csv",
            "classes_state": f"ALUCORSOINDCLASTA{tag}{stamp}.csv", "classes_private": f"ALUCORSOINDCLAPAR{tag}{stamp}.csv",
            "time_state": f"ALUTEMPOSCUOLASTA{tag}{stamp}.csv", "time_private": f"ALUTEMPOSCUOLAPAR{tag}{stamp}.csv"}


class SchoolError(RuntimeError):
    pass


def norm(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip().upper())


def num(x: Any) -> int:
    text = str(x or "").strip()
    if not text:
        return 0
    value = float(text.replace(",", "."))
    if not value.is_integer() or value < 0:
        raise SchoolError(f"valore non intero {x!r}")
    return int(value)


def rows(raw: bytes, name: str) -> list[dict[str, str]]:
    text = raw.decode("utf-8-sig", errors="replace")
    if "<html" in text[:500].lower():
        raise SchoolError(f"{name}: risposta HTML invece di CSV")
    try:
        delim = csv.Sniffer().sniff(text[:12000], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    out = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    if not out:
        raise SchoolError(f"{name}: CSV vuoto")
    return out


def town_schools(registry: list[dict[str, str]]) -> dict[str, str]:
    """codice scuola → codice ISTAT del Comune (solo i sette Comuni)."""
    by_name = {n: c for c, n in TOWNS.items()}
    out: dict[str, str] = {}
    for r in registry:
        code = norm(r.get("CODICESCUOLA"))
        town = by_name.get(norm(r.get("DESCRIZIONECOMUNE")))
        if not code or not town or norm(r.get("REGIONE")) != "TOSCANA" or norm(r.get("PROVINCIA")) != "LUCCA":
            continue
        if out.get(code, town) != town:
            raise SchoolError(f"anagrafe: {code} in due Comuni")
        out[code] = town
    return out


def year_counts(fetcher: Callable[[str], bytes], start: int) -> dict[str, Any]:
    names = files(start)
    raw = {role: fetcher(BASE + name) for role, name in names.items()}
    schools = town_schools(rows(raw["registry_state"], names["registry_state"]) + rows(raw["registry_private"], names["registry_private"]))
    if set(schools.values()) != set(TOWNS):
        raise SchoolError(f"{start}: Comuni senza scuole {sorted(set(TOWNS) - set(schools.values()))}")
    t = {c: defaultdict(int) for c in TOWNS}
    for role in ("classes_state", "classes_private"):
        for r in rows(raw[role], names[role]):
            town = schools.get(norm(r.get("CODICESCUOLA")))
            if town and any(o in norm(r.get("ORDINESCUOLA")) for o in ORDERS):
                t[town]["students"] += num(r.get("ALUNNIMASCHI")) + num(r.get("ALUNNIFEMMINE"))
                t[town]["classes"] += num(r.get("CLASSI"))
    for role in ("time_state", "time_private"):
        for r in rows(raw[role], names[role]):
            town = schools.get(norm(r.get("CODICESCUOLA")))
            if town and "PRIMARIA" in norm(r.get("ORDINESCUOLA")):
                n = num(r.get("ALUNNIMASCHI")) + num(r.get("ALUNNIFEMMINE"))
                t[town]["primary_students"] += n
                if norm(r.get("TEMPOSCUOLA")) == "TEMPO PIENO":
                    t[town]["full_time_students"] += n
    for code, v in t.items():
        if not v["students"] or not v["classes"] or not v["primary_students"]:
            raise SchoolError(f"{start} {code}: conteggi vuoti {dict(v)}")
    return {"files": {role: {"url": BASE + names[role], "sha256": hashlib.sha256(raw[role]).hexdigest(), "bytes": len(raw[role])} for role in names},
            "towns": {c: dict(v) for c, v in t.items()}}


def values(counts: dict[str, int]) -> dict[str, float]:
    return {"schoolStudents": counts["students"], "studentsPerClass": counts["students"] / counts["classes"],
            "primaryFullTimeShare": counts["full_time_students"] / counts["primary_students"] * 100}


def label(start: int) -> str:
    return f"{start}/{(start + 1) % 100:02d}"


def build_snapshot(fetcher: Callable[[str], bytes], current: dict[str, dict[str, float]], last: int, first: int = 2015) -> dict[str, Any]:
    """`current`: metrica → {codice: valore pubblicato}; `last`: primo anno dell'a.s. corrente (2024 per 2024/25)."""
    years = {start: year_counts(fetcher, start) for start in range(first, last + 1)}
    for key, towns in current.items():
        for code, value in towns.items():
            got = values(years[last]["towns"][code])[key]
            if got != value:
                raise SchoolError(f"{key} {code} {label(last)}: ricostruito {got} ≠ pubblicato {value}")
    starts = sorted(years)
    return {
        "schemaVersion": 1, "version": f"mim-alunni-serie-{label(first).replace('/', '-')}-{label(last).replace('/', '-')}-v1",
        "retrieved": date.today().isoformat(), "publisher": "MIM — Portale unico dei dati della scuola",
        "sourceUrl": "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti",
        "schoolYears": [label(s) for s in starts],
        "rule": ("Scuole statali e paritarie localizzate nel Comune secondo l'anagrafe MIM dell'anno; alunni maschi + femmine "
                 "e classi delle scuole primarie e secondarie; quota della primaria a TEMPO PIENO sul totale della primaria."),
        "archives": {label(s): years[s]["files"] for s in starts},
        "towns": {c: {label(s): years[s]["towns"][c] for s in starts} for c in TOWNS},
        "series": {k: {c: [values(years[s]["towns"][c])[k] for s in starts] for c in TOWNS} for k in KEYS},
        "qualityGate": {"status": "PASS", "note": f"a.s. {label(last)} identico ai valori pubblicati per i 7 Comuni e i 3 indicatori."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    years = snapshot["schoolYears"]
    for key in KEYS:
        metric = metrics[key]
        for row in metric["rows"]:
            series = snapshot["series"][key][row["code"]]
            if series[-1] != row["value"]:
                raise SchoolError(f"{key} {row['town']}: serie {series[-1]} ≠ valore {row['value']}")
            row["series"] = {"years": list(years), "values": list(series)}
        metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
        note = f" Serie dall'a.s. {years[0]} al {years[-1]}, con l'anagrafe delle scuole di ciascun anno."
        if note.strip() not in metric["method"].get("caveat", ""):
            metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
