#!/usr/bin/env python3
"""Quality gate del draft Welfare + prima infanzia dopo la materializzazione."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
SNAP = json.loads((ROOT / "data" / "source-snapshots" / "welfare-prima-infanzia-draft-2026-08.json").read_text(encoding="utf-8"))

KEYS = ["socialSpendingPerResident", "socialSpendingByUserArea", "earlyChildhoodPotentialCapacityRate"]
TOWNS = {"Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"}

assert SITE["version"] == "1.18.0-draft"
assert len(SITE["metrics"]) == 146, len(SITE["metrics"])
for key in KEYS:
    assert key in SITE["metrics"], key
    rows = SITE["metrics"][key]["rows"]
    assert len(rows) == 7, (key, len(rows))
    assert {row["town"] for row in rows} == TOWNS

community = SITE["themes"]["comunita"]
assert community["label"] == "Comunità e welfare"
welfare_section = next(s for s in community["sections"] if s["key"] == "welfare-servizi-sociali")
assert welfare_section["metrics"] == KEYS[:2]
assert all(key in community["metrics"] for key in KEYS[:2])

education = SITE["themes"]["istruzione"]
early_section = next(s for s in education["sections"] if s["key"] == "prima-infanzia")
assert early_section["metrics"] == [KEYS[2]]
assert KEYS[2] in education["metrics"]

spending = SITE["metrics"][KEYS[0]]
assert spending["meta"]["year"] == "2022"
assert spending["meta"]["unit"] == "eurPerResident"
massarosa_spend = next(r for r in spending["rows"] if r["town"] == "Massarosa")
assert abs(massarosa_spend["value"] - 97.68949478749) < 1e-9
assert massarosa_spend["series"]["years"] == list(range(2014, 2023))
assert len(massarosa_spend["series"]["values"]) == 9

composition = SITE["metrics"][KEYS[1]]
assert composition["meta"]["compositeType"] == "distribution"
for row in composition["rows"]:
    assert len(row["parts"]) == 7
    assert abs(sum(part["value"] for part in row["parts"]) - 100.0) < 0.05, row["town"]
assert abs(sum(part["value"] for part in composition["aggregate"]["parts"]) - 100.0) < 1e-8

first = SITE["metrics"][KEYS[2]]
assert first["meta"]["year"] == "2024/25"
assert first["meta"]["polarity"] == "positive"
expected = {
    "Camaiore": (177, 436), "Forte dei Marmi": (63, 75), "Massarosa": (87, 297),
    "Pietrasanta": (221, 295), "Seravezza": (0, 168), "Stazzema": (0, 35), "Viareggio": (483, 911),
}
for row in first["rows"]:
    cap, children = expected[row["town"]]
    assert row["potentialCapacity"] == cap
    assert row["children3to36Months"] == children
    assert abs(row["value"] - cap / children * 100) < 1e-9
assert abs(first["aggregate"]["value"] - 1031 / 2217 * 100) < 1e-9

assert set(SNAP["towns"]) == TOWNS
assert SNAP["status"] == "draft-verified-7of7"
assert "socialServiceProfessionalUsers" not in SITE["metrics"], "La presa in carico non deve entrare nel lotto base senza verifica dedicata"

print("OK Welfare + prima infanzia draft: 3 indicatori, copertura 7/7, 146 totali.")
