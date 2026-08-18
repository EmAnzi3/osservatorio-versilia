#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

DATA = Path("data/site-data.json")

EXPECTED_TOWN_WORKS = {
    "Camaiore": 3,
    "Forte dei Marmi": 2,
    "Massarosa": 2,
    "Pietrasanta": 3,
    "Seravezza": 2,
    "Stazzema": 3,
    "Viareggio": 7,
}


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    metrics = data["metrics"]
    deep = data["pnrrDeepDive"]

    concluded = metrics["pnrrConcluded"]["aggregate"]
    expected_concluded = 74 / 101 * 100.0
    assert math.isclose(float(concluded["value"]), expected_concluded, abs_tol=1e-12)
    assert concluded["label"] == "Versilia · 74 su 101"
    assert "74 progetti su 101" in concluded["note"]
    assert not math.isclose(float(concluded["value"]), 50.0, abs_tol=1e-12)

    population = sum(float(row["value"]) for row in metrics["population"]["rows"])
    expected_funding = 36683107.64 / population
    funding = metrics["pnrrFunding"]["aggregate"]
    assert math.isclose(float(funding["value"]), expected_funding, abs_tol=1e-12)
    assert funding["label"] == "Versilia · risorse PNRR per residente"
    assert 231.40 < float(funding["value"]) < 231.42

    assert deep["totals"]["projects"] == 101
    assert deep["totals"]["concluded"] == 74
    assert deep["physicalWorks"]["count"] == 22
    counts = Counter(work["town"] for work in deep["physicalWorks"]["works"])
    assert dict(counts) == EXPECTED_TOWN_WORKS

    massarosa = [row for row in deep["towns"] if row["town"] == "Massarosa"][0]
    assert massarosa["projects"] == 11
    assert massarosa["concluded"] == 10
    assert math.isclose(float(massarosa["funding"]), 5965208.14, abs_tol=0.01)
    massarosa_works = [work for work in deep["physicalWorks"]["works"] if work["town"] == "Massarosa"]
    assert {work["title"] for work in massarosa_works} == {
        "Asilo nido Girotondo a Piano di Mommio",
        "Piscina comunale G. Frati",
    }
    assert {work["status"] for work in massarosa_works} == {"Collaudo avviato"}

    # Il vecchio 67 è un dato BDAP-MOP separato: non è il numero dei progetti PNRR.
    government = data["details"]["046018"]["government"]
    assert government["publicWorks"] == 67
    assert government["pnrrProjects"] == 11
    assert metrics["publicWorks"]["meta"]["source"] == "MEF / RGS — BDAP-MOP"
    assert metrics["pnrrFunding"]["meta"]["source"] == "Regione Toscana — Open Data PNRR"

    dist = Path("dist")
    if dist.exists():
        for relative in [
            "comuni/massarosa/index.html",
            "comuni/viareggio/index.html",
            "confronta/comunita/index.html",
        ]:
            text = (dist / relative).read_text(encoding="utf-8")
            assert "assets/pnrr-town-detail.css" in text
            assert "assets/pnrr-town-detail.js" in text

    print(
        "OK: benchmark Versilia 74/101, €231,41/residente, "
        "22 opere fisiche e separazione BDAP/PNRR verificati"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
