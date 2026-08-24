#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "istat-lavoro-istruzione-eta-genere-2024.json"
KEYS = ["employmentRate", "unemploymentRate", "activityRate", "diplomaPlus", "tertiary"]
LABOUR_ORDER = ["15-24", "25-49", "50-64", "65plus", "25-64", "15plus"]
EDUCATION_ORDER = ["9-24", "25-49", "50-64", "65plus", "25-64", "9plus"]


def close(a, b, label, tol=1e-9):
    assert math.isclose(float(a), float(b), abs_tol=tol, rel_tol=1e-9), f"{label}: {a} != {b}"


def main():
    site = json.loads(SITE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert len(snap["towns"]) == 7
    expected_count = registry["expectedMetricCount"]
    assert len(site["metrics"]) == expected_count, (
        "L'arricchimento non deve cambiare il totale indicatori: "
        f"site={len(site['metrics'])}, registry={expected_count}"
    )
    labour_theme = site["themes"]["lavoro"]
    historical_gender = {"femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"}
    assert historical_gender <= set(labour_theme["metrics"])
    gender_section = next(section for section in labour_theme["sections"] if section["key"] == "genere")
    assert gender_section["label"] == "Serie storiche 15–64"
    assert gender_section["metrics"] == ["femaleEmploymentRate", "maleEmploymentRate", "employmentGenderGap"]
    assert "2021–2023" in gender_section["description"] and "2024" in gender_section["description"]

    for key in KEYS:
        metric = site["metrics"][key]
        assert metric["meta"]["compositeType"] == "demographicBreakdown"
        assert metric["meta"]["defaultAge"] == "25-64" and metric["meta"]["defaultGender"] == "total"
        assert [g["key"] for g in metric["meta"]["genderOptions"]] == ["total", "men", "women"]
        age_keys = [a["key"] for a in metric["meta"]["ageOptions"]]
        expected_order = LABOUR_ORDER if key in {"employmentRate", "unemploymentRate", "activityRate"} else EDUCATION_ORDER
        assert age_keys == expected_order, f"{key}: ordine fasce incoerente {age_keys}"
        assert [a["group"] for a in metric["meta"]["ageOptions"][:4]] == ["Fasce non sovrapposte"] * 4
        assert [a["group"] for a in metric["meta"]["ageOptions"][4:]] == ["Aggregati"] * 2
        assert metric["meta"]["pyramidAgeKeys"] == expected_order[:4]
        assert len(metric["rows"]) == 7 and metric["method"]["coverage"] == "7/7"
        expected_parts = len(metric["meta"]["ageOptions"]) * 3
        assert expected_parts == 18
        for row in metric["rows"]:
            assert len(row["parts"]) == 18
            keys = {part["key"] for part in row["parts"]}
            assert len(keys) == 18 and "25-64|total" in keys and "25-64|women" in keys and "25-64|men" in keys
            default = next(part for part in row["parts"] if part["key"] == "25-64|total")
            assert abs(float(row["value"]) - float(default["value"])) <= 0.11
            for part in row["parts"]:
                if part["denominator"]:
                    close(part["value"], part["numerator"] / part["denominator"] * 100, f"{key}/{row['town']}/{part['key']}")
        assert len(metric["aggregate"]["parts"]) == 18
        for part in metric["aggregate"]["parts"]:
            matching = [next(p for p in row["parts"] if p["key"] == part["key"]) for row in metric["rows"]]
            num = sum(p["numerator"] for p in matching)
            den = sum(p["denominator"] for p in matching)
            close(part["numerator"], num, f"{key}/agg-num/{part['key']}")
            close(part["denominator"], den, f"{key}/agg-den/{part['key']}")
            close(part["value"], num / den * 100, f"{key}/agg/{part['key']}")

    mass = next(row for row in site["metrics"]["employmentRate"]["rows"] if row["town"] == "Massarosa")
    women = next(part for part in mass["parts"] if part["key"] == "25-64|women")
    men = next(part for part in mass["parts"] if part["key"] == "25-64|men")
    close(women["value"], 64.89809668182583, "Massarosa occupazione donne")
    close(men["value"], 81.8288788031602, "Massarosa occupazione uomini")
    edu = next(row for row in site["metrics"]["tertiary"]["rows"] if row["town"] == "Massarosa")
    edu_w = next(part for part in edu["parts"] if part["key"] == "25-64|women")
    close(edu_w["value"], 20.90281286845208, "Massarosa terziario donne")
    print(
        "Lavoro/Istruzione età×genere verificati: 5 indicatori, ordine fasce logico, "
        f"piramide su 4 fasce non sovrapposte, serie 15–64 preservate, 7/7, totale indicatori invariato a {expected_count}."
    )


if __name__ == "__main__":
    main()
