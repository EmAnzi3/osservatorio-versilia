#!/usr/bin/env python3
from pathlib import Path


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: attesa 1 occorrenza, trovate {count}")
    return text.replace(old, new, 1)


materializer = Path("scripts/materialize_territorio_v137.py")
s = materializer.read_text(encoding="utf-8")
s = once(
    s,
    '''            sqm = nonnegative(row.get("sqmPerResident"), f"{town}.{year}.sqmPerResident")
            close(pct, consumed_ha / area_ha * 100, f"{town}.{year}.consumedPct", abs_tol=0.03)
            if sqm <= 0:
                raise RuntimeError(f"v1.37: m2/residente non valido: {town} {year}")
''',
    '''            close(pct, consumed_ha / area_ha * 100, f"{town}.{year}.consumedPct", abs_tol=0.03)
            sqm_raw = row.get("sqmPerResident")
            if year >= 2019:
                sqm = nonnegative(sqm_raw, f"{town}.{year}.sqmPerResident")
                if sqm <= 0:
                    raise RuntimeError(f"v1.37: m2/residente non valido: {town} {year}")
            elif sqm_raw is not None:
                raise RuntimeError(f"v1.37: m2/residente inatteso prima del 2019: {town} {year}")
''',
    "validator sqm",
)
s = once(
    s,
    '''def make_land_use(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["landUse"]
    years = block["years"]
    rows = []
''',
    '''def make_land_use(snapshot: dict, ids: dict[str, dict]) -> dict:
    block = snapshot["landUse"]
    years = block["years"]
    sqm_years = [year for year in years if year >= 2019]
    rows = []
''',
    "sqm years",
)
s = once(
    s,
    '''                "sqmPerResident": {"years": years, "values": [float(item["rows"][str(y)]["sqmPerResident"]) for y in years]},
''',
    '''                "sqmPerResident": {"years": sqm_years, "values": [float(item["rows"][str(y)]["sqmPerResident"]) for y in sqm_years]},
''',
    "town sqm series",
)
s = once(
    s,
    '''                "sqmPerResident": {"years": years, "values": [float(block["versilia"]["rows"][str(y)]["sqmPerResident"]) for y in years]},
''',
    '''                "sqmPerResident": {"years": sqm_years, "values": [float(block["versilia"]["rows"][str(y)]["sqmPerResident"]) for y in sqm_years]},
''',
    "versilia sqm series",
)
s = once(
    s,
    '''        "method": {"type": "Dato ufficiale ISPRA", "formula": "Stock: ha; quota: ha consumati / ha territoriali × 100; pro capite: m² consumati / residenti.", "caveat": "Sono riportate solo le annualita' ufficiali disponibili; nessuna interpolazione.", "coverage": "7/7"},
''',
    '''        "method": {"type": "Dato ufficiale ISPRA", "formula": "Stock: ha; quota: ha consumati / ha territoriali × 100; pro capite: m² consumati / residenti.", "caveat": "Stock e quota seguono le annualita' ISPRA 2006, 2012 e 2015–2024. Il dato m²/residente è mostrato nel periodo 2019–2024, sovrapposto alla serie demografica canonica disponibile; nessuna interpolazione.", "coverage": "7/7"},
''',
    "method caveat",
)
materializer.write_text(s, encoding="utf-8")

brand = Path("scripts/build_static_brand.py")
s = brand.read_text(encoding="utf-8")
s = once(
    s,
    '''TERRITORIO_UCS_REFINER = ROOT / "scripts" / "refine_territorio_ucs_release_v2.py"
''',
    '''TERRITORIO_UCS_REFINER = ROOT / "scripts" / "refine_territorio_ucs_release_v2.py"
TERRITORIO_V137_MATERIALIZER = ROOT / "scripts" / "materialize_territorio_v137.py"
TERRITORIO_V137_RUNTIME_PATCH = ROOT / "scripts" / "patch_territorio_v137_runtime.py"
''',
    "canonical constants",
)
s = once(
    s,
    '''        _ORIGINAL_RUN_PATH(str(TERRITORIO_UCS_REFINER), run_name="__main__")
        return result
''',
    '''        _ORIGINAL_RUN_PATH(str(TERRITORIO_UCS_REFINER), run_name="__main__")
        _ORIGINAL_RUN_PATH(str(TERRITORIO_V137_MATERIALIZER), run_name="__main__")
        return result
''',
    "canonical materializer hook",
)
s = once(
    s,
    '''    exec(compile(source, str(path), "exec"), globals_dict)
    return globals_dict
''',
    '''    exec(compile(source, str(path), "exec"), globals_dict)
    _ORIGINAL_RUN_PATH(str(TERRITORIO_V137_RUNTIME_PATCH), run_name="__main__")
    return globals_dict
''',
    "canonical runtime hook",
)
brand.write_text(s, encoding="utf-8")

qa = Path(".github/workflows/territorio-v137-runtime-qa.yml")
qa.write_text('''name: Territorio v1.37 canonical QA

on:
  push:
    branches:
      - draft/territorio-indicatori-v137
    paths:
      - scripts/build_static_brand.py
      - scripts/materialize_territorio_v137.py
      - scripts/patch_territorio_v137_runtime.py
      - data/source-snapshots/territorio-v137-official.json
      - .github/workflows/territorio-v137-runtime-qa.yml
  workflow_dispatch:

permissions:
  contents: read

jobs:
  canonical-build:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Compile v1.37 Python
        run: python -m py_compile scripts/materialize_territorio_v137.py scripts/patch_territorio_v137_runtime.py scripts/build_static_brand.py
      - name: Run canonical static build
        run: python scripts/build_static_brand.py
      - name: Assert canonical dist contract
        run: python scripts/verify_territorio_v137_dist.py
      - name: Assert final runtime tokens
        run: |
          grep -R -q "territoryProfileTypes" dist/assets
          grep -R -q "sqm_per_resident" dist/assets
          grep -R -q "km_per_km2" dist/assets
''', encoding="utf-8")

verify = Path("scripts/verify_territorio_v137_dist.py")
verify.write_text('''#!/usr/bin/env python3
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
''', encoding="utf-8")

for obsolete in (
    ".github/workflows/territorio-v137-source-inventory.yml",
    ".github/workflows/territorio-v137-source-structure.yml",
    "scripts/inspect_territorio_v137_sources.py",
    "scripts/inspect_territorio_v137_structure.py",
    ".github/workflows/territorio-v137-integrate.yml",
    "scripts/apply_territorio_v137_patches.py",
):
    p = Path(obsolete)
    if p.exists():
        p.unlink()

print("v1.37 canonical integration patches prepared")
