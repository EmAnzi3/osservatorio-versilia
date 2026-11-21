#!/usr/bin/env python3
"""Serie dell'Anagrafe dell'Edilizia Scolastica MIM per i sette Comuni (a.s. 2020/21–2024/25).

Stessa regola dei valori pubblicati (`mim-edilizia-scolastica-versilia-2024-25.json`, materializzato da
`materialize_scuola_mim.py`): per ogni anno scolastico gli edifici univoci (CODICEEDIFICIO) delle scuole
statali localizzate nel Comune secondo l'anagrafe delle scuole dello stesso anno; per ogni campo i
conteggi delle risposte (SI, NO, NON DEFINITO, periodo di costruzione). Un edificio con risposte
discordanti fra le righe delle scuole che lo usano resta fuori, come nel calcolo pubblicato. L'anno
2024/25 deve coincidere, Comune per Comune e campo per campo, con i conteggi pubblicati.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import date
from typing import Any, Callable

import school_history as sh

BASE = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/"
SNAPSHOT = "data/source-snapshots/mim-edilizia-scolastica-serie.json"
CURRENT = "data/source-snapshots/mim-edilizia-scolastica-versilia-2024-25.json"
# Data di pubblicazione nel nome dei file (catalogo MIM, dataset «...STA2021»): stessa per i cinque dataset.
STAMPS = {2020: "20211116", 2021: "20220908", 2022: "20230731", 2023: "20250714", 2024: "20250806"}
DATASETS = {
    "schoolBuildingSafetyDocs": ("EDICONSICUREZZASTA2021", {
        "agibilita": "CERTIFICATOSEGNALAZIONEAGIBILITA", "cpi": "CERTIFICATOPREVENZIONEINCENDI",
        "sciaAntincendio": "SCIAANTINCENDIO", "rinnovoAntincendio": "ATTESTAZIONERINNOVOPERIODICOCONFORMITAANTINCENDIO"}),
    "schoolBuildingAccessibility": ("EDISUPBARARCSTA2021", {"accessibilita": "ACCORGIMENTISUPERAMENTOBARRIEREARCHITETTONICHE"}),
    "schoolBuildingFacilities": ("EDIAMBFUNZSTA2021", {"mensa": "MENSA", "palestra": "PALESTRA"}),
    "schoolBuildingAge": ("EDIETAORIGINESTA2021", {"periodoCostruzione": "PERIODOCOSTRUZIONE"}),
    "schoolBuildingTransport": ("EDICOLLEGAMENTISTA2021", {
        "scuolabus": "SCUOLABUS", "tplUrbano": "TRASPORTIPUBBLICIURBANI", "tplInterurbano": "TRASPORTIPUBBLICIINTERURBANI"}),
}
TOWNS = {code: name for code, name in sh.TOWNS.items()}
TOWN_LABELS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
               "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}


class BuildingsError(RuntimeError):
    pass


class Unavailable(Exception):
    """Il file di quell'anno non è pubblicato."""


def file_name(prefix: str, start: int) -> str:
    return f"{prefix}{start}{(start + 1) % 100:02d}{STAMPS[start]}.csv"


def canon(field: str, value: Any) -> str:
    s = re.sub(r"\s+", " ", str(value or "").strip())
    return s.lower() if field == "periodoCostruzione" else s.upper()


def schools(registry: list[dict[str, str]]) -> dict[str, str]:
    """codice scuola → codice Istat del Comune, solo scuole dei sette Comuni (stessa regola della serie alunni)."""
    return sh.town_schools(registry)


def town_counts(rows: list[dict[str, str]], school_town: dict[str, str], fields: dict[str, str]) -> dict[str, Any]:
    buildings: dict[str, dict[str, Any]] = {}
    for row in rows:
        town = school_town.get(sh.norm(row.get("CODICESCUOLA")))
        bid = str(row.get("CODICEEDIFICIO") or "").strip()
        if not town or not bid:
            continue
        rec = buildings.setdefault(bid, {"towns": set(), "fields": {k: set() for k in fields}})
        rec["towns"].add(town)
        for local, col in fields.items():
            if col not in row:
                raise BuildingsError(f"colonna {col} assente")
            rec["fields"][local].add(canon(local, row.get(col)))
    out = {c: {"buildings": 0, "fields": {k: Counter() for k in fields}} for c in TOWNS}
    excluded = 0
    for bid, rec in buildings.items():
        if len(rec["towns"]) != 1 or any(len(v) != 1 for v in rec["fields"].values()):
            excluded += 1  # edificio in due Comuni o con risposte discordanti: fuori, come nel calcolo pubblicato
            continue
        town = next(iter(rec["towns"]))
        out[town]["buildings"] += 1
        for local, values in rec["fields"].items():
            out[town]["fields"][local][next(iter(values))] += 1
    return {"towns": {c: {"buildings": v["buildings"], **{k: dict(cnt) for k, cnt in v["fields"].items()}} for c, v in out.items()},
            "excludedBuildings": excluded}


def build_snapshot(fetcher: Callable[[str], bytes], current: dict[str, Any], first: int = 2020, last: int = 2024) -> dict[str, Any]:
    """`current`: snapshot pubblicato 2024/25 (conteggi per Comune e campo)."""
    if current.get("schoolYear") != sh.label(last):
        raise BuildingsError(f"snapshot corrente {current.get('schoolYear')} ≠ {sh.label(last)}")
    years: dict[int, dict[str, Any]] = {}
    archives: dict[str, Any] = {}
    for start in range(first, last + 1):
        names = sh.files(start)
        reg_raw = {role: fetcher(BASE + names[role]) for role in ("registry_state", "registry_private")}
        school_town = schools(sh.rows(reg_raw["registry_state"], names["registry_state"]) + sh.rows(reg_raw["registry_private"], names["registry_private"]))
        archive = {role: {"url": BASE + names[role], "sha256": hashlib.sha256(b).hexdigest()} for role, b in reg_raw.items()}
        per_metric = {}
        for key, (prefix, fields) in DATASETS.items():
            name = file_name(prefix, start)
            try:
                raw = fetcher(BASE + name)
            except Unavailable:
                if start == last:
                    raise BuildingsError(f"{key}: anno corrente {sh.label(last)} non disponibile")
                continue
            per_metric[key] = town_counts(sh.rows(raw, name), school_town, fields)
            archive[key] = {"url": BASE + name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                            "excludedBuildings": per_metric[key]["excludedBuildings"]}
        years[start] = per_metric
        archives[sh.label(start)] = archive
    # Riconciliazione con i conteggi pubblicati 2024/25, Comune per Comune e campo per campo.
    errors = []
    for key, (_, fields) in DATASETS.items():
        got = years[last][key]["towns"]
        for code, name in TOWN_LABELS.items():
            expected = current["towns"][name]
            if got[code]["buildings"] != int(expected["buildings"]):
                errors.append(f"{key} {name}: edifici {got[code]['buildings']} ≠ {expected['buildings']}")
            for field in fields:
                exp = {canon(field, k): int(v or 0) for k, v in (expected.get(field) or {}).items()}
                if got[code][field] != exp:
                    errors.append(f"{key} {name} {field}: {got[code][field]} ≠ {exp}")
    if errors:
        raise BuildingsError("riconciliazione 2024/25: " + "; ".join(errors[:12]))
    series = {}
    for key in DATASETS:
        # Serie continua che termina con l'anno corrente: un anno mancante interrompe la serie.
        starts = []
        for start in range(last, first - 1, -1):
            if key not in years[start]:
                break
            starts.insert(0, start)
        series[key] = {"schoolYears": [sh.label(s) for s in starts],
                       "towns": {c: {sh.label(s): years[s][key]["towns"][c] for s in starts} for c in TOWNS}}
    return {
        "schemaVersion": 1, "version": f"mim-edilizia-scolastica-serie-{sh.label(first).replace('/', '-')}-{sh.label(last).replace('/', '-')}-v1",
        "retrieved": date.today().isoformat(), "publisher": "MIM — Anagrafe dell'Edilizia Scolastica",
        "rule": ("Edifici univoci delle scuole statali localizzate nel Comune secondo l'anagrafe delle scuole dell'anno; conteggi delle "
                 "risposte per campo; edifici in più Comuni o con risposte discordanti esclusi, come nel calcolo pubblicato."),
        "archives": archives, "metrics": series,
        "qualityGate": {"status": "PASS", "note": f"a.s. {sh.label(last)} identico ai conteggi pubblicati per 7 Comuni, 5 indicatori e tutti i campi."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str, parts_for: dict[str, Callable[[dict], list[dict]]]) -> None:
    """`parts_for`: indicatore → funzione dei conteggi che restituisce le parti (stesse di materialize_scuola_mim)."""
    for key, block in snapshot["metrics"].items():
        metric = metrics.get(key)
        labels = block["schoolYears"]
        if not metric or len(labels) < 2 or labels[-1] != metric["meta"]["year"]:
            continue
        for row in metric["rows"]:
            per_year = [parts_for[key](block["towns"][row["code"]][y]) for y in labels]
            current = row.get("parts") or []
            last = per_year[-1]
            if [p["selectorLabel"] for p in last] != [p["selectorLabel"] for p in current] or any(
                    (a["value"] is None) != (b["value"] is None) or (a["value"] is not None and abs(a["value"] - b["value"]) > 1e-9)
                    for a, b in zip(last, current)):
                raise BuildingsError(f"{key} {row['town']}: ultimo anno diverso dalle parti pubblicate")
            row["componentSeries"] = {p["selectorLabel"]: {"years": list(labels), "values": [ps[i]["value"] for ps in per_year]}
                                      for i, p in enumerate(current)}
            row["series"] = row["componentSeries"][current[0]["selectorLabel"]]
        metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
        note = f" Serie dall'a.s. {labels[0]} al {labels[-1]}, con l'anagrafe delle scuole di ciascun anno."
        if note.strip() not in metric["method"].get("caveat", ""):
            metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
