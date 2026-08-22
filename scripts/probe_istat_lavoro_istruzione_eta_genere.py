#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://esploradati.istat.it/SDMXWS/rest"
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
FLOWS = {
    "labour": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
    "education": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
}
TOWNS = {
    "Camaiore":"046005", "Forte dei Marmi":"046013", "Massarosa":"046018",
    "Pietrasanta":"046024", "Seravezza":"046028", "Stazzema":"046030", "Viareggio":"046033",
}
GENDERS = {"T":"total", "M":"men", "F":"women"}
LABOUR_AGES = {"Y15-24":"15-24", "Y25-49":"25-49", "Y50-64":"50-64", "Y_GE65":"65plus", "Y_GE15":"15plus"}
EDU_AGES = {"Y9-24":"9-24", "Y25-49":"25-49", "Y50-64":"50-64", "Y_GE65":"65plus", "Y_GE9":"9plus"}


def fetch_csv(flow: str) -> list[dict]:
    refs = "+".join(TOWNS.values())
    key = ".".join(["A", refs] + [""] * 8)
    params = urllib.parse.urlencode({"startPeriod":"2024", "endPeriod":"2024", "format":"csvfile"})
    url = f"{BASE}/data/IT1,{flow},1.0/{key}/all?{params}"
    req = urllib.request.Request(url, headers={"User-Agent":"OsservatorioVersilia/1.0", "Accept":"application/vnd.sdmx.data+csv;version=1.0.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    print("FETCH", flow, len(raw), url)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))))


def f(value) -> float:
    return float(value)


def add_cells(a: dict, b: dict, fields: list[str]) -> dict:
    return {field: f(a[field]) + f(b[field]) for field in fields}


def build_labour(rows: list[dict]) -> dict:
    by = {}
    for row in rows:
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("CITIZENSHIP") != "TOTAL" or row.get("EDU_ATTAIN") != "ALL":
            continue
        age = LABOUR_AGES.get(row.get("AGE_NOCLASS"))
        gender = GENDERS.get(row.get("GENDER"))
        stat = row.get("CUR_ACT_STAT")
        town = row.get("REF_AREA")
        if age and gender and stat in {"1","12","22","99"} and town in TOWNS.values():
            by.setdefault(town, {}).setdefault(age, {}).setdefault(gender, {})[stat] = f(row["OBS_VALUE"])
    out = {}
    for name, code in TOWNS.items():
        town = by[code]
        for age in ["15-24","25-49","50-64","65plus","15plus"]:
            for gender in ["total","men","women"]:
                vals = town[age][gender]
                missing = {"1","12","22","99"} - set(vals)
                if missing:
                    raise RuntimeError(f"labour {name} {age} {gender}: missing {missing}")
        town["25-64"] = {}
        for gender in ["total","men","women"]:
            town["25-64"][gender] = add_cells(town["25-49"][gender], town["50-64"][gender], ["1","12","22","99"])
        clean = {}
        for age, age_data in town.items():
            clean[age] = {}
            for gender, vals in age_data.items():
                pop, employed, unemployed, active = vals["99"], vals["1"], vals["12"], vals["22"]
                if abs((employed + unemployed) - active) > 1e-6:
                    raise RuntimeError(f"labour {name} {age} {gender}: active mismatch")
                clean[age][gender] = {
                    "population": pop,
                    "employed": employed,
                    "unemployed": unemployed,
                    "active": active,
                    "employmentRate": employed / pop * 100 if pop else None,
                    "unemploymentRate": unemployed / active * 100 if active else None,
                    "activityRate": active / pop * 100 if pop else None,
                }
        out[name] = clean
    return out


def build_education(rows: list[dict]) -> dict:
    by = {}
    wanted = {"ALL","USE_IF","BL","ML_RDD"}
    for row in rows:
        if row.get("INDICATOR") != "RESPOP_AV" or row.get("CITIZENSHIP") != "TOTAL" or row.get("CUR_ACT_STAT") != "99":
            continue
        age = EDU_AGES.get(row.get("AGE_NOCLASS"))
        gender = GENDERS.get(row.get("GENDER"))
        edu = row.get("EDU_ATTAIN")
        town = row.get("REF_AREA")
        if age and gender and edu in wanted and town in TOWNS.values():
            by.setdefault(town, {}).setdefault(age, {}).setdefault(gender, {})[edu] = f(row["OBS_VALUE"])
    out = {}
    for name, code in TOWNS.items():
        town = by[code]
        for age in ["9-24","25-49","50-64","65plus","9plus"]:
            for gender in ["total","men","women"]:
                vals = town[age][gender]
                missing = wanted - set(vals)
                if missing:
                    raise RuntimeError(f"education {name} {age} {gender}: missing {missing}")
        town["25-64"] = {}
        for gender in ["total","men","women"]:
            town["25-64"][gender] = add_cells(town["25-49"][gender], town["50-64"][gender], list(wanted))
        clean = {}
        for age, age_data in town.items():
            clean[age] = {}
            for gender, vals in age_data.items():
                pop = vals["ALL"]
                diploma = vals["USE_IF"] + vals["BL"] + vals["ML_RDD"]
                tertiary = vals["BL"] + vals["ML_RDD"]
                clean[age][gender] = {
                    "population": pop,
                    "upperSecondaryPlus": diploma,
                    "tertiary": tertiary,
                    "diplomaPlus": diploma / pop * 100 if pop else None,
                    "tertiaryRate": tertiary / pop * 100 if pop else None,
                }
        out[name] = clean
    return out


def reconcile(snapshot: dict) -> None:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    metrics = {
        "employmentRate": ("labour", "employmentRate"),
        "unemploymentRate": ("labour", "unemploymentRate"),
        "activityRate": ("labour", "activityRate"),
        "diplomaPlus": ("education", "diplomaPlus"),
        "tertiary": ("education", "tertiaryRate"),
    }
    for metric_key, (section, field) in metrics.items():
        current = site["metrics"][metric_key]
        for row in current["rows"]:
            value = snapshot["towns"][row["town"]][section]["25-64"]["total"][field]
            if not math.isclose(value, float(row["value"]), abs_tol=0.11):
                raise RuntimeError(f"parity {metric_key}/{row['town']}: raw {value} current {row['value']}")
    print("PARITY_OK: i 5 valori 25-64 totali riconciliano con il sito entro l'arrotondamento pubblicato.")


def main() -> None:
    labour_rows = fetch_csv(FLOWS["labour"])
    time.sleep(13)
    education_rows = fetch_csv(FLOWS["education"])
    snapshot = {
        "version":"istat-lavoro-istruzione-eta-genere-2024-v1",
        "referenceYear":2024,
        "source": {
            "publisher":"Istat — Censimento permanente della popolazione",
            "labourDataflow":FLOWS["labour"],
            "educationDataflow":FLOWS["education"],
            "api":"https://esploradati.istat.it/SDMXWS/rest",
        },
        "dimensions": {
            "gender":{"total":"T","men":"M","women":"F"},
            "labourAges":["25-64","15-24","25-49","50-64","65plus","15plus"],
            "educationAges":["25-64","9-24","25-49","50-64","65plus","9plus"],
            "note":"25-64 è ricostruita esattamente sommando le classi ufficiali 25-49 e 50-64; le altre classi sono pubblicate direttamente dal dataflow.",
        },
        "towns": {},
    }
    labour = build_labour(labour_rows)
    education = build_education(education_rows)
    for town in TOWNS:
        snapshot["towns"][town] = {"code":TOWNS[town], "labour":labour[town], "education":education[town]}
    reconcile(snapshot)
    print("SNAPSHOT_JSON_BEGIN")
    print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",",":")))
    print("SNAPSHOT_JSON_END")


if __name__ == "__main__":
    main()
