#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "istat-lavoro-istruzione-eta-genere-2024.json"
KEYS = ["employmentRate","unemploymentRate","activityRate","diplomaPlus","tertiary"]


def close(a,b,label,tol=1e-9):
    assert math.isclose(float(a),float(b),abs_tol=tol,rel_tol=1e-9), f"{label}: {a} != {b}"


def main():
    site=json.loads(SITE.read_text(encoding="utf-8"))
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    snap=json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert len(snap["towns"])==7
    expected_count=registry["expectedMetricCount"]
    assert len(site["metrics"])==expected_count, (
        "L'arricchimento non deve cambiare il totale indicatori: "
        f"site={len(site['metrics'])}, registry={expected_count}"
    )
    labour_theme=site["themes"]["lavoro"]
    assert "femaleEmploymentRate" not in labour_theme["metrics"] and "maleEmploymentRate" not in labour_theme["metrics"]
    assert "employmentGenderGap" in labour_theme["metrics"]
    assert "femaleEmploymentRate" in site["metrics"] and "maleEmploymentRate" in site["metrics"], "Metriche storiche legacy devono restare nel dataset"

    for key in KEYS:
        metric=site["metrics"][key]
        assert metric["meta"]["compositeType"]=="demographicBreakdown"
        assert metric["meta"]["defaultAge"]=="25-64" and metric["meta"]["defaultGender"]=="total"
        assert [g["key"] for g in metric["meta"]["genderOptions"]]==["total","men","women"]
        assert len(metric["rows"])==7 and metric["method"]["coverage"]=="7/7"
        expected_parts=len(metric["meta"]["ageOptions"])*3
        assert expected_parts==18
        for row in metric["rows"]:
            assert len(row["parts"])==18
            keys={part["key"] for part in row["parts"]}
            assert len(keys)==18 and "25-64|total" in keys and "25-64|women" in keys and "25-64|men" in keys
            default=next(part for part in row["parts"] if part["key"]=="25-64|total")
            assert abs(float(row["value"])-float(default["value"]))<=0.11
            for part in row["parts"]:
                if part["denominator"]:
                    close(part["value"],part["numerator"]/part["denominator"]*100,f"{key}/{row['town']}/{part['key']}")
        assert len(metric["aggregate"]["parts"])==18
        for part in metric["aggregate"]["parts"]:
            matching=[next(p for p in row["parts"] if p["key"]==part["key"]) for row in metric["rows"]]
            num=sum(p["numerator"] for p in matching); den=sum(p["denominator"] for p in matching)
            close(part["numerator"],num,f"{key}/agg-num/{part['key']}")
            close(part["denominator"],den,f"{key}/agg-den/{part['key']}")
            close(part["value"],num/den*100,f"{key}/agg/{part['key']}")

    mass=next(row for row in site["metrics"]["employmentRate"]["rows"] if row["town"]=="Massarosa")
    women=next(part for part in mass["parts"] if part["key"]=="25-64|women")
    men=next(part for part in mass["parts"] if part["key"]=="25-64|men")
    close(women["value"],64.89809668182583,"Massarosa occupazione donne")
    close(men["value"],81.8288788031602,"Massarosa occupazione uomini")
    edu=next(row for row in site["metrics"]["tertiary"]["rows"] if row["town"]=="Massarosa")
    edu_w=next(part for part in edu["parts"] if part["key"]=="25-64|women")
    close(edu_w["value"],20.90281286845208,"Massarosa terziario donne")
    print(
        "Lavoro/Istruzione età×genere verificati: 5 indicatori arricchiti, "
        f"18 combinazioni ciascuno, 7/7, totale indicatori invariato a {expected_count}."
    )

if __name__=="__main__": main()
