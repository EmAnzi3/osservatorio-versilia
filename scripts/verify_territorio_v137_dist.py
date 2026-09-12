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

# Pin the exact official geometry used by the reproducible GIS snapshot.  This
# prevents a future regeneration from silently changing the municipal partition
# while keeping the Versilia total unchanged.
snapshot_path = Path("data/source-snapshots/territorio-v137-official.json")
if not snapshot_path.exists():
    raise SystemExit("snapshot territorio v1.37 mancante")
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
boundary = snapshot.get("measurementBoundary", {})
boundary_acq = boundary.get("acquisition", {})
expected_boundary = {
    "reference": "Confini amministrativi al 1 gennaio 2026 · generalizzati",
    "sourceLayer": "Com01012026_g_WGS84.shp",
    "url": "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip",
    "sha256": "b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6",
    "crs": "EPSG:3003",
}
actual_boundary = {
    "reference": boundary.get("reference"),
    "sourceLayer": boundary.get("sourceLayer"),
    "url": boundary_acq.get("url"),
    "sha256": boundary_acq.get("sha256"),
    "crs": boundary.get("crs"),
}
if actual_boundary != expected_boundary:
    raise SystemExit(f"measurementBoundary: provenance inattesa {actual_boundary}")

road = metrics["roadNetworkProfile"]
if abs(float(road["aggregate"]["value"]) - 2029.655081) > 1e-6:
    raise SystemExit("roadNetworkProfile: aggregato km inatteso")
road_expected = ["length", "density", "adminMunicipal", "adminProvincial", "adminRegional", "adminState", "adminPrivate", "paved", "unpaved", "pavementUnclassified"]
road_parts = {p["key"]: p for p in road["aggregate"]["parts"]}
if list(road_parts) != road_expected:
    raise SystemExit(f"roadNetworkProfile: letture inattese {list(road_parts)}")
admin_keys = ["adminMunicipal", "adminProvincial", "adminRegional", "adminState", "adminPrivate"]
pavement_keys = ["paved", "unpaved", "pavementUnclassified"]
admin_sum = sum(float(road_parts[k]["value"]) for k in admin_keys)
if abs(admin_sum - float(road_parts["length"]["value"])) > 1e-5:
    raise SystemExit(f"roadNetworkProfile: classi amministrative non chiudono sul totale: {admin_sum}")
pavement_sum = sum(float(road_parts[k]["value"]) for k in pavement_keys)
if abs(pavement_sum - float(road_parts["length"]["value"])) > 1e-5:
    raise SystemExit(f"roadNetworkProfile: pavimentazione non chiude sul totale: {pavement_sum}")

# These values are the exact result of clipping Iter.Net 4.48 against the
# pinned Istat 01/01/2026 generalized municipal geometries.  A total-only gate
# would not catch an accidental redistribution among municipalities.
road_town_expected = {
    "Camaiore": 480.955860,
    "Forte dei Marmi": 139.038100,
    "Massarosa": 313.923233,
    "Pietrasanta": 411.130550,
    "Seravezza": 153.945273,
    "Stazzema": 120.352216,
    "Viareggio": 410.309849,
}
for row in road["rows"]:
    keys = [p["key"] for p in row["parts"]]
    if keys != road_expected:
        raise SystemExit(f"roadNetworkProfile: letture incomplete per {row['town']}")
    parts = {p["key"]: p for p in row["parts"]}
    length = float(parts["length"]["value"])
    expected_length = road_town_expected[row["town"]]
    if abs(length - expected_length) > 1e-6:
        raise SystemExit(
            f"roadNetworkProfile: ripartizione comunale inattesa per {row['town']}: "
            f"{length} != {expected_length}"
        )
    row_admin_sum = sum(float(parts[k]["value"]) for k in admin_keys)
    if abs(row_admin_sum - length) > 1e-5:
        raise SystemExit(
            f"roadNetworkProfile: classi amministrative non chiudono per {row['town']}: {row_admin_sum}"
        )
    row_pavement_sum = sum(float(parts[k]["value"]) for k in pavement_keys)
    if abs(row_pavement_sum - length) > 1e-5:
        raise SystemExit(
            f"roadNetworkProfile: pavimentazione non chiude per {row['town']}: {row_pavement_sum}"
        )
if abs(sum(road_town_expected.values()) - float(road_parts["length"]["value"])) > 1e-6:
    raise SystemExit("roadNetworkProfile: vettore comunale pinned non chiude sul totale Versilia")

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
print("road-municipal-allocation", "pinned")
print("road-boundary-provenance", "pinned")
print("reticulum-managed-versilia-km", hydro_parts["managed"]["value"])
print("protected-dual-unit", "ok")
