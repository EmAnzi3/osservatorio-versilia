#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

GEN = Path('scripts/generate_territorio_v137_snapshot.py')
MAT = Path('scripts/materialize_territorio_v137.py')
VER = Path('scripts/verify_territorio_v137_dist.py')


def patch_generator():
    text = GEN.read_text(encoding='utf-8')
    old = 'frame = gpd.read_file(candidates[0], engine="pyogrio", columns=[])'
    new = 'frame = gpd.read_file(candidates[0], engine="pyogrio", columns=["classe_amm", "tip_pavim"])'
    if text.count(old) != 1:
        raise SystemExit(f'load_roads target count {text.count(old)}')
    text = text.replace(old, new, 1)

    old_helper = '''def clipped_line_km(frame: gpd.GeoDataFrame, polygon) -> float:\n    minx, miny, maxx, maxy = polygon.bounds\n    subset = frame.cx[minx:maxx, miny:maxy]\n    if subset.empty:\n        return 0.0\n    lengths = subset.geometry.intersection(polygon).length\n    return float(lengths.sum() / 1000)\n\n\n'''
    new_helper = old_helper + '''ROAD_ADMIN_CLASSES = {\n    "municipal": "Strada Comunale",\n    "provincial": "Strada Provinciale",\n    "regional": "Strada Regionale",\n    "state": "Strada Statale",\n    "private": "Strada Privata",\n}\nROAD_PAVEMENT_CLASSES = {\n    "paved": "pavimentata",\n    "unpaved": "non pavimentata",\n    "unclassified": "-",\n}\n\ndef clipped_category_km(frame: gpd.GeoDataFrame, polygon, column: str, value: str) -> float:\n    selected = frame[frame[column].astype(str).str.strip() == value]\n    return clipped_line_km(selected, polygon)\n\ndef road_breakdown(frame: gpd.GeoDataFrame, polygon) -> dict:\n    return {\n        "administrativeClassKm": {key: round(clipped_category_km(frame, polygon, "classe_amm", label), 6) for key, label in ROAD_ADMIN_CLASSES.items()},\n        "pavementKm": {key: round(clipped_category_km(frame, polygon, "tip_pavim", label), 6) for key, label in ROAD_PAVEMENT_CLASSES.items()},\n    }\n\n\n'''
    if text.count(old_helper) != 1:
        raise SystemExit(f'clipped helper target count {text.count(old_helper)}')
    text = text.replace(old_helper, new_helper, 1)

    start = text.index('def build_roads(frame, town_geoms, versilia_geom, areas_km2):')
    end = text.index('\n\ndef load_protected(', start)
    new_build = '''def build_roads(frame, town_geoms, versilia_geom, areas_km2):\n    municipalities = {}\n    for town in TOWNS:\n        km = clipped_line_km(frame, town_geoms[town])\n        municipalities[town] = {\n            "municipalAreaKm2": round(areas_km2[town], 6),\n            "graphKm": round(km, 6),\n            "graphDensity": round(km / areas_km2[town], 6),\n            **road_breakdown(frame, town_geoms[town]),\n        }\n    area = versilia_geom.area / 1_000_000\n    km = clipped_line_km(frame, versilia_geom)\n    return {\n        "referenceLabel": "Iter.Net 4.48 · giugno 2022",\n        "municipalities": municipalities,\n        "versilia": {\n            "unionAreaKm2": round(area, 6),\n            "graphKm": round(km, 6),\n            "graphDensity": round(km / area, 6),\n            **road_breakdown(frame, versilia_geom),\n        },\n    }\n'''
    text = text[:start] + new_build + text[end:]
    GEN.write_text(text, encoding='utf-8')


def patch_materializer():
    text = MAT.read_text(encoding='utf-8')
    start = text.index('def make_roads(snapshot: dict, ids: dict[str, dict]) -> dict:')
    end = text.index('\n\ndef install_road_metric', start)
    new_make = '''def make_roads(snapshot: dict, ids: dict[str, dict]) -> dict:\n    block = snapshot["roadNetworkProfile"]\n\n    def parts(item: dict) -> list[dict]:\n        admin = item["administrativeClassKm"]\n        pavement = item["pavementKm"]\n        return [\n            {"key": "length", "label": "Lunghezza del grafo", "value": float(item["graphKm"]), "unit": "km"},\n            {"key": "density", "label": "Densità del grafo", "value": float(item["graphDensity"]), "unit": "km_per_km2"},\n            {"key": "adminMunicipal", "label": "Strade comunali", "value": float(admin["municipal"]), "unit": "km"},\n            {"key": "adminProvincial", "label": "Strade provinciali", "value": float(admin["provincial"]), "unit": "km"},\n            {"key": "adminRegional", "label": "Strade regionali", "value": float(admin["regional"]), "unit": "km"},\n            {"key": "adminState", "label": "Strade statali", "value": float(admin["state"]), "unit": "km"},\n            {"key": "adminPrivate", "label": "Strade private", "value": float(admin["private"]), "unit": "km"},\n            {"key": "paved", "label": "Elementi pavimentati", "value": float(pavement["paved"]), "unit": "km"},\n            {"key": "unpaved", "label": "Elementi non pavimentati", "value": float(pavement["unpaved"]), "unit": "km"},\n            {"key": "pavementUnclassified", "label": "Pavimentazione non classificata", "value": float(pavement["unclassified"]), "unit": "km"},\n        ]\n\n    rows = []\n    for town in TOWNS:\n        item = block["municipalities"][town]\n        rows.append({\n            **identity(ids[town]), "value": float(item["graphKm"]), "formatted": fmt(float(item["graphKm"]), 1, " km"),\n            "parts": parts(item),\n            "municipalAreaKm2": float(item["municipalAreaKm2"]), "series": None, "normalized": None, "benchmarkValue": None,\n        })\n    versilia = block["versilia"]\n    return {\n        "meta": {"key": "roadNetworkProfile", "theme": "ambiente", "label": "Grafo viario Iter.Net", "shortLabel": "Grafo viario", "description": "Lunghezza e densità degli elementi stradali Iter.Net, con dettaglio per classe amministrativa e pavimentazione.", "unit": "km", "year": "2022", "source": "Regione Toscana — Iter.Net 4.48", "polarity": "neutral", "compositeType": "roadNetworkProfile", "defaultView": "length", "selectorLabel": "Lettura", "searchTerms": ["strade", "grafo viario", "Iter.Net", "rete stradale", "densità stradale", "strade comunali", "strade provinciali", "strade regionali", "strade statali", "pavimentazione"]},\n        "sourceUrl": snapshot["sources"]["regioneIterNet"]["page"], "rows": rows,\n        "aggregate": {"value": float(versilia["graphKm"]), "label": "Versilia · grafo viario Iter.Net", "note": "Lunghezze ricalcolate sul perimetro dissolto dei sette Comuni; i dettagli amministrativi e di pavimentazione derivano dagli attributi degli elementi Iter.Net.", "parts": parts(versilia)},\n        "normalizedAggregate": None,\n        "method": {"type": "Elaborazione GIS su grafo Iter.Net 4.48", "formula": "Lunghezza degli elementi stradali dopo clip; densità = km grafo / km². Le classi amministrative usano classe_amm; la pavimentazione usa tip_pavim. Versilia su unione dissolta.", "caveat": "Iter.Net rappresenta gli assi degli elementi stradali e può distinguere le carreggiate; i valori sono chilometri di elementi del grafo, non chilometri di strade univoche al centrolinea.", "coverage": "7/7"},\n    }\n'''
    MAT.write_text(text[:start] + new_make + text[end:], encoding='utf-8')


def patch_verifier():
    text = VER.read_text(encoding='utf-8')
    needle = '''if abs(float(road["aggregate"]["value"]) - 2029.655081) > 1e-6:\n    raise SystemExit("roadNetworkProfile: aggregato km inatteso")\n'''
    addition = needle + '''road_expected = ["length", "density", "adminMunicipal", "adminProvincial", "adminRegional", "adminState", "adminPrivate", "paved", "unpaved", "pavementUnclassified"]\nroad_parts = {p["key"]: p for p in road["aggregate"]["parts"]}\nif list(road_parts) != road_expected:\n    raise SystemExit(f"roadNetworkProfile: letture inattese {list(road_parts)}")\nadmin_sum = sum(float(road_parts[k]["value"]) for k in ["adminMunicipal", "adminProvincial", "adminRegional", "adminState", "adminPrivate"])\nif abs(admin_sum - float(road_parts["length"]["value"])) > 1e-5:\n    raise SystemExit(f"roadNetworkProfile: classi amministrative non chiudono sul totale: {admin_sum}")\npavement_sum = sum(float(road_parts[k]["value"]) for k in ["paved", "unpaved", "pavementUnclassified"])\nif abs(pavement_sum - float(road_parts["length"]["value"])) > 1e-5:\n    raise SystemExit(f"roadNetworkProfile: pavimentazione non chiude sul totale: {pavement_sum}")\nfor row in road["rows"]:\n    keys=[p["key"] for p in row["parts"]]\n    if keys != road_expected:\n        raise SystemExit(f"roadNetworkProfile: letture incomplete per {row['town']}")\n'''
    if text.count(needle) != 1:
        raise SystemExit(f'verifier target count {text.count(needle)}')
    VER.write_text(text.replace(needle, addition, 1), encoding='utf-8')


def regenerate_road_snapshot():
    spec = importlib.util.spec_from_file_location('v137gen', str(GEN))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        boundaries_zip = work / 'boundaries.zip'
        roads_zip = work / 'roads.zip'
        mod.download(mod.ISTAT_BOUNDARIES, boundaries_zip)
        mod.download(mod.ROADS, roads_zip)
        towns, versilia, areas, _ = mod.load_boundaries(boundaries_zip, work)
        roads, _ = mod.load_roads(roads_zip, work)
        block = mod.build_roads(roads, towns, versilia, areas)
    snapshot = json.loads(mod.OUT.read_text(encoding='utf-8'))
    snapshot['roadNetworkProfile'] = block
    mod.OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(block['versilia'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    patch_generator()
    patch_materializer()
    patch_verifier()
    regenerate_road_snapshot()
