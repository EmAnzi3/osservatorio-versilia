#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import math
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("update_agid_indicators.py")
spec = importlib.util.spec_from_file_location("update_agid_indicators", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)

TOWNS = [
    ("Massarosa", "046018", "massarosa"),
    ("Viareggio", "046033", "viareggio"),
    ("Camaiore", "046005", "camaiore"),
    ("Pietrasanta", "046024", "pietrasanta"),
    ("Seravezza", "046028", "seravezza"),
    ("Forte dei Marmi", "046013", "forte-dei-marmi"),
    ("Stazzema", "046030", "stazzema"),
]


def base_data():
    rows = []
    towns = []
    for i, (name, code, slug) in enumerate(TOWNS, start=1):
        towns.append({"name": name, "code": code})
        rows.append({
            "town": name,
            "code": code,
            "slug": slug,
            "value": 100 * i,
            "formatted": str(100 * i),
            "series": None,
            "normalized": None,
            "benchmarkValue": 100 * i,
        })
    return {
        "version": "v1.6.0",
        "updated": "6 agosto 2026",
        "themes": {
            "economia": {
                "description": "old",
                "metrics": ["localUnits", "microUnits"],
                "sections": [{"key": "produzione", "description": "old", "metrics": ["localUnits", "microUnits"]}],
                "featured": ["localUnits"],
            },
            "mobilita": {
                "label": "Mobilità e sicurezza",
                "question": "old",
                "description": "old",
                "metrics": ["evPoints", "roadInjuries"],
                "sections": [
                    {"key": "veicoli", "metrics": ["evPoints"]},
                    {"key": "sicurezza", "metrics": ["roadInjuries"]},
                ],
                "featured": ["roadInjuries"],
            },
        },
        "towns": towns,
        "metrics": {
            "localUnits": {
                "meta": {"key": "localUnits"},
                "sourceUrl": "old",
                "rows": rows,
                "aggregate": None,
                "normalizedAggregate": None,
                "method": {},
            },
            "microUnits": {"meta": {"key": "microUnits"}},
        },
    }


def source_maps():
    asia = {}
    agcom = {}
    for i, (_, code, _) in enumerate(TOWNS, start=1):
        ul = [100 * i + offset for offset in range(6)]
        employees = [value * (2.0 + i / 10) for value in ul]
        asia[code] = {
            "_years_available": [2018, 2019, 2020, 2021, 2022, 2023],
            "_latest_year": 2023,
            "kpi": {
                "ul_totali": ul[-1],
                "addetti_totali": employees[-1],
                "addetti_per_ul": employees[-1] / ul[-1],
            },
            "serie_storica": {
                "anni": [2018, 2019, 2020, 2021, 2022, 2023],
                "ul": ul,
                "addetti": employees,
            },
        }
        resident = 1000 * i
        reached = 600 * i
        reached_20m = 700 * i
        agcom[code] = {
            "_data_period": "31/12/2025",
            "kpi": {
                "famiglie_residenti": resident,
                "famiglie_ftth": reached,
                "famiglie_ftth_20m": reached_20m,
                "copertura_ftth_desi_pct": 60.0,
                "copertura_ftth_20m_pct": 70.0,
            },
        }
    return asia, agcom


def test_apply_updates():
    base = base_data()
    asia, agcom = source_maps()
    updated, snapshot = module.apply_updates(base, asia, agcom, "2026-08-07T00:00:00+00:00")

    assert base["version"] == "v1.6.0", "La funzione deve lavorare su una copia"
    assert updated["version"] == "v1.7.0"
    assert len(updated["metrics"]) == 10
    for key in module.NEW_ECONOMY_KEYS + module.NEW_BROADBAND_KEYS:
        assert key in updated["metrics"], key
        assert len(updated["metrics"][key]["rows"]) == 7

    local = updated["metrics"]["localUnits"]
    assert local["rows"][0]["series"]["years"] == [2018, 2019, 2020, 2021, 2022, 2023]
    assert local["rows"][0]["value"] == 105

    employees = updated["metrics"]["localEmployees"]
    assert math.isclose(employees["rows"][0]["value"], 220.5)
    assert employees["meta"]["year"] == "2023"

    avg = updated["metrics"]["employeesPerLocalUnit"]
    assert math.isclose(avg["rows"][0]["value"], 2.1)

    ftth = updated["metrics"]["ftthCoverageDesi"]
    assert math.isclose(ftth["aggregate"]["value"], 60.0)
    assert updated["metrics"]["ftthUnreachedHouseholds"]["aggregate"]["value"] == 11200
    assert updated["themes"]["mobilita"]["label"] == "Mobilità e infrastrutture"
    assert updated["themes"]["mobilita"]["sections"][-2]["key"] == "connettivita"
    assert len(snapshot["towns"]) == 7


def test_validation():
    asia, agcom = source_maps()
    bad = copy.deepcopy(asia["046018"])
    bad["_latest_year"] = 2024
    try:
        module.validate_asia("046018", bad)
    except module.DataError:
        pass
    else:
        raise AssertionError("Annualità ASIA inattesa non respinta")

    bad_agcom = copy.deepcopy(agcom["046018"])
    bad_agcom["kpi"]["famiglie_ftth"] = 2000
    try:
        module.validate_agcom("046018", bad_agcom)
    except module.DataError:
        pass
    else:
        raise AssertionError("Copertura AGCOM incoerente non respinta")


if __name__ == "__main__":
    test_apply_updates()
    test_validation()
    print("OK: test indicatori ASIA e AGCOM")
