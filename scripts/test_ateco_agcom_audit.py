#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_ateco_agcom_audit as enrich  # noqa: E402
import apply_agcom_absolute_policy as policy  # noqa: E402

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
    for index, (name, code, slug) in enumerate(TOWNS, 1):
        towns.append({"name": name, "code": code})
        rows.append({"town": name, "code": code, "slug": slug, "value": 1000 + index, "formatted": str(1000 + index), "series": None, "normalized": None, "benchmarkValue": 1000 + index})
    return {
        "towns": towns,
        "details": {code: {"economy": {}} for _, code, _ in TOWNS},
        "metrics": {
            "localUnits": {"rows": copy.deepcopy(rows)},
            "population": {"rows": [
                {**row, "value": 10000 + index * 1000}
                for index, row in enumerate(copy.deepcopy(rows), 1)
            ]},
            "ftthCoverageDesi": {"meta": {"key": "ftthCoverageDesi"}},
            "ftthCoverage20m": {"meta": {"key": "ftthCoverage20m"}},
            "ftthReachedHouseholds": {"meta": {"key": "ftthReachedHouseholds"}},
            "ftthUnreachedHouseholds": {"meta": {"key": "ftthUnreachedHouseholds"}},
        },
        "themes": {
            "mobilita": {
                "metrics": ["ftthCoverageDesi", "ftthReachedHouseholds", "ftthUnreachedHouseholds", "ftthCoverage20m"],
                "sections": [{"key": "connettivita", "metrics": ["ftthCoverageDesi", "ftthReachedHouseholds", "ftthUnreachedHouseholds", "ftthCoverage20m"]}],
            }
        },
    }


def asia_data():
    result = {}
    for index, (_, code, _) in enumerate(TOWNS, 1):
        result[code] = {
            "kpi": {"ul_totali": 1000 + index, "addetti_totali": 3000 + index},
            "ateco_dettaglio": {
                "2023": {
                    "43": {"TOTAL": {"ul": 200 + index, "addetti": 400 + index}},
                    "47": {"TOTAL": {"ul": 150 + index, "addetti": 500 + index}},
                    "56": {"TOTAL": {"ul": 80 + index, "addetti": 250 + index}},
                }
            },
        }
    return result


def snapshot_data(invalid_codes=None):
    invalid_codes = invalid_codes or []
    towns = []
    for index, (name, code, _) in enumerate(TOWNS, 1):
        resident = 4000 + index * 100
        reached = None if code in invalid_codes else 3000 + index * 80
        towns.append({
            "town": name,
            "code": code,
            "agcom": {
                "residentHouseholds": resident,
                "ftthHouseholds": reached,
                "ftthHouseholdsWithin20m": 2500 + index * 70,
            },
        })
    return {
        "towns": towns,
        "agcomAudit": {
            "invalidAbsoluteTownCodes": list(invalid_codes),
            "invalidAbsoluteTowns": [name for name, code, _ in TOWNS if code in invalid_codes],
        },
    }


def test_ateco_detail():
    data = base_data()
    enrich.build_ateco(data, asia_data())
    assert data["economyAteco"]["coverage"] == "7/7"
    assert data["economyAteco"]["year"] == 2023
    assert set(data["economyAteco"]["sectorCodes"]) == {"43", "47", "56"}
    massarosa = data["details"]["046018"]["economy"]
    assert len(massarosa["atecoSectors"]) == 3
    assert massarosa["topSectors"][0]["code"] == "47", "Il top per addetti deve essere ATECO 47"
    assert massarosa["topSectorsByUnits"][0]["code"] == "43", "Il top per unità locali deve essere ATECO 43"


def test_policy_six_of_seven():
    data = base_data()
    snapshot = snapshot_data(["046013"])
    updated, updated_snapshot, status, invalid = policy.apply_policy(data, snapshot)
    assert status == "published_partial"
    assert invalid == ["046013"]
    assert updated["metrics"]["ftthReachedHouseholds"]["method"]["coverage"] == "6/7"
    row = next(row for row in updated["metrics"]["ftthReachedHouseholds"]["rows"] if row["code"] == "046013")
    assert row["value"] is None and row["formatted"] == "n.d."
    assert updated_snapshot["coveragePolicy"]["minimumAcceptedCoverage"] == "6/7"


def test_policy_five_of_seven_omits_counts():
    data = base_data()
    snapshot = snapshot_data(["046013", "046018"])
    updated, updated_snapshot, status, invalid = policy.apply_policy(data, snapshot)
    assert status == "omitted_below_6_of_7"
    assert invalid == ["046013", "046018"]
    assert "ftthReachedHouseholds" not in updated["metrics"]
    assert "ftthUnreachedHouseholds" not in updated["metrics"]
    assert updated["themes"]["mobilita"]["sections"][0]["metrics"] == ["ftthCoverageDesi", "ftthCoverage20m"]
    assert updated_snapshot["coveragePolicy"]["publishedBroadbandMetrics"] == ["ftthCoverageDesi", "ftthCoverage20m"]


if __name__ == "__main__":
    test_ateco_detail()
    test_policy_six_of_seven()
    test_policy_five_of_seven_omits_counts()
    print("OK: test dettaglio ATECO e policy AGCOM 6/7")
