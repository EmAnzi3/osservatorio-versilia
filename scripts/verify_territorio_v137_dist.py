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
if abs(float(road["aggregate"]["value"]) - 2029.655081) > 1e-6:
    raise SystemExit("roadNetworkProfile: aggregato km inatteso")
hydro = metrics["managedReticulumLength"]
hydro_parts = {x["key"]: x for x in hydro["aggregate"]["parts"]}
if abs(float(hydro_parts["managed"]["value"]) - 745.041751) > 1e-6:
    raise SystemExit("reticolo gestito: regressione aggregato")
land = metrics["landUse"]
cam = next(r for r in land["rows"] if r["town"] == "Camaiore")
if cam["seriesByView"]["sqmPerResident"]["years"] != [2019, 2020, 2021, 2022, 2023, 2024]:
    raise SystemExit("landUse: anni pro capite inattesi")
for row in land["rows"]:
    parts = {p["key"]: p for p in row["parts"]}
    if parts["hectares"].get("unit") != "hectares":
        raise SystemExit(f"landUse: unità ettari non canonica per {row['town']}")
change = metrics["landUseChange"]
for row in change["rows"]:
    if any(p.get("unit") != "hectares" for p in row["parts"]):
        raise SystemExit(f"landUseChange: unità ettari non canonica per {row['town']}")
protected = metrics["protectedNaturalAreas"]
if protected["meta"].get("selectorLabel") != "Tutela":
    raise SystemExit("aree protette: selectorLabel mancante")
if "ANPIL" not in protected.get("method", {}).get("caveat", ""):
    raise SystemExit("aree protette: caveat ANPIL mancante")
for row in protected["rows"]:
    if not row.get("municipalAreaHa", 0) > 0:
        raise SystemExit(f"aree protette: area comunale non valida per {row['town']}")
    for part in row.get("parts", []):
        if part.get("unit") != "percent" or part.get("ha") is None or float(part["ha"]) < 0:
            raise SystemExit(f"aree protette: doppia unità incompleta per {row['town']}/{part.get('key')}")
    total = next(p for p in row["parts"] if p["key"] == "total")
    if float(total["ha"]) > float(row["municipalAreaHa"]) + 1e-5:
        raise SystemExit(f"aree protette: unione > area comunale per {row['town']}")
print("canonical-dist-metrics", len(metrics))
print("road-versilia-km", road["aggregate"]["value"])
print("reticulum-managed-versilia-km", hydro_parts["managed"]["value"])
print("protected-dual-unit", "ok")
