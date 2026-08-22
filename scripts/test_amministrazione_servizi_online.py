#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "regione-toscana-servizi-online-2018-2022.json"
KEY = "municipalOnlineServicesAdvanced"


def close(a: float, b: float, label: str) -> None:
    assert math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9), f"{label}: {a} != {b}"


def main() -> None:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    assert len(site["metrics"]) == 138, f"Attesi 138 indicatori, trovati {len(site['metrics'])}"
    assert registry["expectedMetricCount"] == 138
    assert registry["expectedInlineMetricCount"] == 134
    assert registry["expectedExternalMetricCount"] == 4

    metric = site["metrics"][KEY]
    assert metric["meta"]["year"] == "2022"
    assert metric["meta"]["unit"] == "percent"
    assert metric["meta"]["polarity"] == "neutral"
    assert metric["method"]["coverage"] == "7/7"
    assert "livelli 3 e 4" in metric["method"]["formula"]
    assert "24 servizi" in metric["method"]["caveat"]
    assert "27" in metric["method"]["caveat"]

    expected_towns = set(snapshot["towns"])
    assert {row["town"] for row in metric["rows"]} == expected_towns
    assert len(metric["rows"]) == 7

    values = []
    for row in metric["rows"]:
        raw = snapshot["towns"][row["town"]]
        close(row["value"], raw["2022"], f"online/{row['town']}/2022")
        assert row["series"]["years"] == [2018, 2022]
        assert len(row["series"]["values"]) == 2
        close(row["series"]["values"][0], raw["2018"], f"online/{row['town']}/2018")
        close(row["series"]["values"][1], raw["2022"], f"online/{row['town']}/serie2022")
        values.append(float(raw["2022"]))

    close(metric["aggregate"]["value"], sum(values) / 7, "online/Versilia")
    assert "media aritmetica" in metric["aggregate"]["note"].lower()
    assert "non è una media ponderata" in metric["aggregate"]["note"].lower()

    theme = site["themes"]["bilanci"]
    assert KEY in theme["metrics"]
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    assert section["metrics"][-1] == KEY
    assert len(section["metrics"]) == 5

    profile = registry["metricOverrides"][KEY]["profile"]
    assert profile == "regione-toscana-indicatori-comunali"
    assert registry["sourceProfiles"][profile]["publisher"].startswith("Regione Toscana")

    print("Servizi online avanzati verificati: ind18 Regione Toscana/Istat, 2022 definitivo, storico reale 2018→2022, copertura 7/7 e 138 indicatori totali.")


if __name__ == "__main__":
    main()
