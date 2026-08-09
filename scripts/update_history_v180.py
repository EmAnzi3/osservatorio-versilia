#!/usr/bin/env python3
"""Aggiunge il primo lotto storico v1.8 da dati censuari Istat omogenei.

Il 2021 entra soltanto per gli indicatori ricostruibili con le stesse variabili
elementari usate nel 2023. Il valore 2023 viene prima ricalcolato e confrontato
con quello già pubblicato; una discordanza interrompe l'aggiornamento.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
LIA_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "lia-v1.4.0.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-sections-history-v1.8.0.json"

TOWN_ORDER = [
    "Massarosa",
    "Viareggio",
    "Camaiore",
    "Pietrasanta",
    "Seravezza",
    "Forte dei Marmi",
    "Stazzema",
]

RAW_2021 = {
    "Massarosa": {"P1": 21823, "male1564": 7000, "female1564": 6989, "P102": 4968, "P103": 3731, "PF1": 9030, "PF3": 2616, "A3": 1996, "A8": 10931},
    "Viareggio": {"P1": 61045, "male1564": 18817, "female1564": 19087, "P102": 12919, "P103": 10108, "PF1": 28903, "PF3": 11741, "A3": 10627, "A8": 38806},
    "Camaiore": {"P1": 31821, "male1564": 10010, "female1564": 10156, "P102": 7039, "P103": 5329, "PF1": 14173, "PF3": 5159, "A3": 8343, "A8": 22303},
    "Pietrasanta": {"P1": 23066, "male1564": 6843, "female1564": 7307, "P102": 4700, "P103": 3714, "PF1": 10493, "PF3": 3942, "A3": 7932, "A8": 18196},
    "Seravezza": {"P1": 12441, "male1564": 3780, "female1564": 3962, "P102": 2600, "P103": 1999, "PF1": 5488, "PF3": 1896, "A3": 2058, "A8": 7472},
    "Forte dei Marmi": {"P1": 6943, "male1564": 1960, "female1564": 2081, "P102": 1249, "P103": 1013, "PF1": 3416, "PF3": 1542, "A3": 5135, "A8": 8493},
    "Stazzema": {"P1": 2890, "male1564": 928, "female1564": 872, "P102": 632, "P103": 385, "PF1": 1364, "PF3": 566, "A3": 2181, "A8": 3532},
}

PF3_2023 = {
    "Massarosa": 2664,
    "Viareggio": 11981,
    "Camaiore": 5237,
    "Pietrasanta": 4066,
    "Seravezza": 1946,
    "Forte dei Marmi": 1549,
    "Stazzema": 579,
}

FORMULAS = {
    "femaleEmploymentRate": lambda row: 100 * row["P103"] / row["female1564"],
    "maleEmploymentRate": lambda row: 100 * row["P102"] / row["male1564"],
    "employmentGenderGap": lambda row: (
        100 * row["P102"] / row["male1564"]
        - 100 * row["P103"] / row["female1564"]
    ),
    "housingStockPer1000": lambda row: 1000 * row["A8"] / row["P1"],
    "nonOccupiedHomesPer1000": lambda row: 1000 * row["A3"] / row["P1"],
    "vacantHomes": lambda row: 100 * row["A3"] / row["A8"],
    "singleHouseholds": lambda row: 100 * row["PF3"] / row["PF1"],
}

FORMULA_LABELS = {
    "femaleEmploymentRate": "P103 / somma(P70:P79) × 100",
    "maleEmploymentRate": "P102 / somma(P33:P42) × 100",
    "employmentGenderGap": "maleEmploymentRate − femaleEmploymentRate",
    "housingStockPer1000": "A8 / P1 × 1.000",
    "nonOccupiedHomesPer1000": "A3 / P1 × 1.000",
    "vacantHomes": "A3 / A8 × 100",
    "singleHouseholds": "PF3 / PF1 × 100",
}

SOURCE_FILES = {
    "2021": {
        "download": "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip",
        "data": {"name": "R09_indicatori_2021_sezioni.xlsx", "sha256": "408cc0d50ed81dd5a73e9c137d919613c316fb64b2866e4bcd84dd09e318d858", "bytes": 18296161},
        "layout": {"name": "TRACCIATO FILE REGIONALI.xlsx", "sha256": "24bb72159ec554bbafa5ea2dfd5b9a712cad6077ee50b70e5ee0ed7a0c2a44b7", "bytes": 13611},
    },
    "2023": {
        "download": "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip",
        "data": {"name": "R09_Toscana_2023_sezioni.xlsx", "sha256": "ac4a4068e5ed2fb93ecbed96bc882914e7feef3d4d0db17013dceb4dcac95fdf", "bytes": 18784761},
        "layout": {"name": "TRACCIATO FILE REGIONALI.xlsx", "sha256": "98071eb0f9e71a1bc59f5eb49503b8d31e7adc010aaa6c30d96ff3d9d1bfe3be", "bytes": 13786},
    },
}


def load_raw_2023() -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    snapshot = json.loads(LIA_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    raw = {row["town"]: row for row in snapshot["raw"]["istat2023"]}
    for town, pf3 in PF3_2023.items():
        raw[town]["PF3"] = pf3
    codes = {row["name"]: row["code"] for row in snapshot["scope"]["towns"]}
    if set(raw) != set(TOWN_ORDER):
        raise RuntimeError("Lo snapshot Istat 2023 non copre i sette Comuni attesi.")
    return raw, codes


def verify_current_values(data: dict, raw_2023: dict[str, dict[str, float]]) -> None:
    for metric_key, formula in FORMULAS.items():
        rows = {row["town"]: row for row in data["metrics"][metric_key]["rows"]}
        for town in TOWN_ORDER:
            calculated = formula(raw_2023[town])
            published = float(rows[town]["value"])
            tolerance = 0.051 if metric_key in {"vacantHomes", "singleHouseholds"} else 1e-9
            if abs(calculated - published) > tolerance:
                raise RuntimeError(
                    f"Verifica 2023 fallita per {metric_key}/{town}: "
                    f"pubblicato {published}, ricalcolato {calculated}."
                )


def add_series(data: dict) -> None:
    for metric_key, formula in FORMULAS.items():
        for row in data["metrics"][metric_key]["rows"]:
            row["series"] = {
                "years": [2021, 2023],
                "values": [formula(RAW_2021[row["town"]]), row["value"]],
            }


def write_snapshot(raw_2023: dict[str, dict[str, float]], codes: dict[str, str]) -> None:
    snapshot = {
        "version": "istat-sections-history-v1.8.0",
        "created": "2026-08-09",
        "scope": {
            "towns": [
                {"name": town, "code": codes[town]}
                for town in TOWN_ORDER
            ],
            "coverage": "7/7",
            "years": [2021, 2023],
        },
        "source": {
            "publisher": "Istat",
            "landing": "https://www.istat.it/notizia/dati-per-sezioni-di-censimento/",
            "license": "CC BY 4.0",
            "files": SOURCE_FILES,
        },
        "comparabilityCheck": {
            "result": "accepted",
            "criterion": "Stesse variabili elementari e stessa formula nel 2021 e nel 2023; il ricalcolo 2023 coincide con i valori già pubblicati entro la loro precisione.",
            "variables": ["P1", "P33-P42", "P70-P79", "P102", "P103", "PF1", "PF3", "A3", "A8"],
        },
        "raw": {
            "2021": [
                {"town": town, "code": codes[town], **RAW_2021[town]}
                for town in TOWN_ORDER
            ],
            "2023": [
                {
                    "town": town,
                    "code": codes[town],
                    **{key: raw_2023[town][key] for key in RAW_2021[town]},
                }
                for town in TOWN_ORDER
            ],
        },
        "acceptedIndicators": [
            {"key": key, "formula": FORMULA_LABELS[key], "years": [2021, 2023]}
            for key in FORMULAS
        ],
        "rejectedCandidates": [
            {
                "key": "cohabitingHouseholds",
                "reason": "La variabile PF9, usata nel 2023, non è presente nel tracciato regionale 2021; la serie non viene costruita.",
            },
            {
                "key": "householdSize",
                "reason": "La classe PF8 raggruppa le famiglie con sei o più componenti; il valore medio esatto non è ricostruibile senza introdurre un'approssimazione.",
            },
        ],
    }
    SNAPSHOT_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    raw_2023, codes = load_raw_2023()
    verify_current_values(data, raw_2023)
    add_series(data)
    data["version"] = "v1.8.0"
    data["updated"] = "9 agosto 2026"
    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_snapshot(raw_2023, codes)
    print("Storico Istat v1.8.0 applicato: 7 indicatori, 2021–2023, copertura 7/7.")


if __name__ == "__main__":
    main()
