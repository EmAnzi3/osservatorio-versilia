#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("dist/data/site-data.json")
if not p.exists():
    raise SystemExit("dist/data/site-data.json mancante")
d = json.loads(p.read_text(encoding="utf-8"))
metrics = d.get("metrics", {})
if len(metrics) != 203:
    raise SystemExit(f"catalogo finale {len(metrics)}, attesi 203")
expected = {"landUse", "landUseChange", "protectedNaturalAreas", "managedReticulumLength", "roadNetworkProfile"}
if not expected.issubset(metrics):
    raise SystemExit(f"metriche v1.37 mancanti: {sorted(expected - set(metrics))}")
towns = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
for key in expected:
    rows = metrics[key].get("rows", [])
    if [r.get("town") for r in rows] != towns:
        raise SystemExit(f"{key}: copertura/ordine non 7/7")
if d.get("version") != "v1.37.0":
    raise SystemExit(f"versione finale inattesa: {d.get('version')}")
road = metrics["roadNetworkProfile"]
if road["meta"].get("compositeType") != "roadNetworkProfile":
    raise SystemExit("roadNetworkProfile: compositeType inatteso")
if abs(float(road["aggregate"]["value"]) - 2029.655081) > 1e-6:
    raise SystemExit("roadNetworkProfile: aggregato km inatteso")
hydro = metrics["managedReticulumLength"]
parts = {x["key"]: x for x in hydro["aggregate"]["parts"]}
if abs(float(parts["managed"]["value"]) - 745.041751) > 1e-6:
    raise SystemExit("reticolo gestito: regressione aggregato")
land = metrics["landUse"]
cam = next(r for r in land["rows"] if r["town"] == "Camaiore")
sq = cam["seriesByView"]["sqmPerResident"]
if sq["years"] != [2019, 2020, 2021, 2022, 2023, 2024]:
    raise SystemExit(f"landUse: anni pro capite inattesi {sq['years']}")
print("canonical-dist-metrics", len(metrics))
print("road-versilia-km", road["aggregate"]["value"])
print("reticulum-managed-versilia-km", parts["managed"]["value"])
