#!/usr/bin/env python3
"""Materializza il supporto GIS riproducibile del Lotto 6 v1.26.0."""
from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/source-snapshots/bonifica-rischio-v126-gis.json"
TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
SOURCES = {
    "istatBoundaries": {
        "url": "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip",
        "sha256": "b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6",
        "label": "Istat — Confini delle unità amministrative al 1 gennaio 2026, versione generalizzata",
    },
    "reticulum": {
        "url": "https://www.regione.toscana.it/documents/d/guest/infrastruttura_rev25-zip",
        "sha256": "68d6bb2986c056e1c041009a21e3b9eb89de81d02830d412354c5770d7d9b122",
        "label": "Regione Toscana — Reticolo idrografico e di gestione DCRT 24/2025",
    },
    "hydraulicWorks": {
        "url": "https://www.regione.toscana.it/documents/10180/22470380/shp%2Bfiles%2Bcensimento%2Bopere%2Bidrauliche.zip/de6d5e57-de9f-4555-7e55-52ff32654a0e?t=1636713609857",
        "sha256": "532b29090ce6fd09f06cf87a1f074b173eeddb57cb3ee1a92560e74ef17bb560",
        "label": "Regione Toscana — Ricognizione opere idrauliche DGRT 1155/2021",
    },
}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path, expected_sha: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "osservatorio-versilia/1.26 GIS materializer"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        out.write(response.read())
    actual = file_sha256(path)
    if actual != expected_sha:
        raise RuntimeError(f"SHA-256 inatteso per {url}: {actual} != {expected_sha}")
    if not zipfile.is_zipfile(path):
        raise RuntimeError(f"Sorgente non ZIP: {url}")
    return {"sizeBytes": path.stat().st_size, "sha256": actual}


def extract(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        zf.extractall(dest)


def find_shp(root: Path, predicate) -> Path:
    matches = sorted(p for p in root.rglob("*.shp") if predicate(p.name.lower()))
    if len(matches) != 1:
        raise RuntimeError(f"Shapefile atteso non univoco in {root}: {[p.name for p in matches]}")
    return matches[0]


def pick_column(gdf: gpd.GeoDataFrame, candidates: tuple[str, ...]) -> str:
    lookup = {c.upper(): c for c in gdf.columns}
    for candidate in candidates:
        if candidate.upper() in lookup:
            return lookup[candidate.upper()]
    raise RuntimeError(f"Colonna non trovata tra {candidates}; disponibili: {list(gdf.columns)}")


def r6(value: float) -> float:
    return round(float(value), 6)


def clean_type(value) -> str:
    text = "" if value is None else str(value).strip()
    return text or "n.d."


def clipped_length_km(gdf: gpd.GeoDataFrame, polygon) -> tuple[float, int]:
    hit = gdf[gdf.geometry.intersects(polygon)].copy()
    clipped = hit.geometry.intersection(polygon)
    clipped = clipped[~clipped.is_empty]
    return r6(clipped.length.sum() / 1000), int(len(clipped))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ov-bonifica-gis-") as td:
        work = Path(td)
        downloaded = {}
        for key, source in SOURCES.items():
            archive = work / f"{key}.zip"
            downloaded[key] = download(source["url"], archive, source["sha256"])
            dest = work / key
            dest.mkdir()
            extract(archive, dest)

        # Confini comunali Istat 2026.
        comuni_shp = find_shp(work / "istatBoundaries", lambda n: n.startswith("com") and "01012026" in n)
        comuni = gpd.read_file(comuni_shp)
        name_col = pick_column(comuni, ("COMUNE", "DEN_COM", "DEN_COMUNE"))
        code_col = pick_column(comuni, ("PRO_COM_T", "PRO_COM", "COD_COM", "CODICE_COM"))
        comuni[name_col] = comuni[name_col].astype(str).str.strip()
        selected = comuni[comuni[name_col].isin(TOWNS)].copy()
        if sorted(selected[name_col].tolist()) != sorted(TOWNS):
            raise RuntimeError("I sette Comuni non sono tutti presenti nel confine Istat 2026")
        selected = selected.to_crs(epsg=3003)[[name_col, code_col, "geometry"]].set_index(name_col).loc[TOWNS]
        versilia_geom = selected.geometry.union_all()
        boundaries = {
            town: {"istatCode": str(row[code_col]), "areaKm2": r6(row.geometry.area / 1_000_000)}
            for town, row in selected.iterrows()
        }

        # Reticolo gestito dal Consorzio 1 Toscana Nord.
        ret_shp = find_shp(work / "reticulum", lambda n: n == "reticolodcr242025.shp")
        ret = gpd.read_file(ret_shp)
        required = {"COMPLR79", "RETGESLR79", "IDRETLR79"}
        if len(ret) != 215923 or not required.issubset(ret.columns):
            raise RuntimeError(f"Contratto reticolo inatteso: {len(ret)} feature, campi={list(ret.columns)}")
        ret = ret.to_crs(epsg=3003)
        managed = ret[(ret["COMPLR79"] == "Toscana Nord") & (ret["RETGESLR79"] == "SI")].copy()
        if len(managed) != 26133:
            raise RuntimeError(f"Filtro Toscana Nord inatteso: {len(managed)} feature")
        source_sum = managed.length.sum()
        source_union = managed.geometry.union_all().length
        if abs(source_sum - source_union) > 0.01:
            raise RuntimeError("Il reticolo gestito contiene sovrapposizioni lineari significative: serve deduplica esplicita")
        managed_by_town = {}
        for town, row in selected.iterrows():
            km, count = clipped_length_km(managed, row.geometry)
            managed_by_town[town] = {"km": km, "sourceFeaturesIntersecting": count}
        aggregate_km, aggregate_features = clipped_length_km(managed, versilia_geom)

        # Censimento opere idrauliche DGRT 1155/2021.
        outer = work / "hydraulicWorks"
        nested = sorted(outer.rglob("DGRT_1155_2021_ricognizione_opere_idrauliche.zip"))
        if len(nested) != 1:
            raise RuntimeError(f"Archivio interno opere non univoco: {nested}")
        inner = work / "hydraulicWorksNested"
        inner.mkdir()
        extract(nested[0], inner)
        layer_paths = {
            "area": find_shp(inner, lambda n: n == "opi_a_dgrt_1155_21.shp"),
            "line": find_shp(inner, lambda n: n == "opi_l_dgrt_1155_21.shp"),
            "point": find_shp(inner, lambda n: n == "opi_pt_dgrt_1155_21.shp"),
        }
        works = {kind: gpd.read_file(path).to_crs(epsg=3003) for kind, path in layer_paths.items()}
        expected_counts = {"area": 82, "line": 2572, "point": 1012}
        for kind, gdf in works.items():
            if len(gdf) != expected_counts[kind] or "TIPOLOGIA" not in gdf.columns:
                raise RuntimeError(f"Contratto opere {kind} inatteso: {len(gdf)} feature, campi={list(gdf.columns)}")

        works_by_town = {}
        for town, row in selected.iterrows():
            polygon = row.geometry
            town_out = {}
            for kind, gdf in works.items():
                hit = gdf[gdf.geometry.intersects(polygon)].copy()
                item = {
                    "sourceFeaturesIntersecting": int(len(hit)),
                    "types": dict(sorted(Counter(clean_type(v) for v in hit["TIPOLOGIA"]).items(), key=lambda kv: (-kv[1], kv[0]))),
                }
                if kind == "line":
                    clipped = hit.geometry.intersection(polygon)
                    item["clippedKm"] = r6(clipped[~clipped.is_empty].length.sum() / 1000)
                elif kind == "area":
                    clipped = hit.geometry.intersection(polygon)
                    item["clippedHectares"] = r6(clipped[~clipped.is_empty].area.sum() / 10_000)
                town_out[kind] = item
            town_out["featurePresenceTotal"] = sum(town_out[k]["sourceFeaturesIntersecting"] for k in ("area", "line", "point"))
            works_by_town[town] = town_out

        works_aggregate = {}
        for kind, gdf in works.items():
            hit = gdf[gdf.geometry.intersects(versilia_geom)].copy()
            works_aggregate[kind] = {
                "uniqueSourceFeatures": int(len(hit)),
                "types": dict(sorted(Counter(clean_type(v) for v in hit["TIPOLOGIA"]).items(), key=lambda kv: (-kv[1], kv[0]))),
            }
        works_aggregate["uniqueSourceFeaturesTotal"] = sum(works_aggregate[k]["uniqueSourceFeatures"] for k in ("area", "line", "point"))

        result = {
            "schemaVersion": 1,
            "snapshotVersion": "2026-08-31-gis-v1",
            "verifiedAt": "2026-08-30T23:40:01+00:00",
            "scope": {"towns": TOWNS, "crsForMeasurements": "EPSG:3003"},
            "sources": {
                key: {"label": source["label"], "url": source["url"], **downloaded[key]}
                for key, source in SOURCES.items()
            },
            "boundaries": {
                "sourceLayer": comuni_shp.name,
                "method": "Selezione dei sette Comuni Istat al 1 gennaio 2026 e riproiezione in EPSG:3003.",
                "byTown": boundaries,
            },
            "managedReticulum": {
                "sourceLayer": ret_shp.name,
                "filter": {"COMPLR79": "Toscana Nord", "RETGESLR79": "SI"},
                "sourceFeaturesAfterFilter": int(len(managed)),
                "sourceNetworkKm": r6(source_union / 1000),
                "method": "Intersezione con i confini comunali Istat 2026 e ricalcolo della lunghezza sulla geometria risultante. Il campo LENGTH della sorgente non viene riutilizzato. Il controllo union_all conferma assenza di sovrapposizioni lineari significative nel reticolo filtrato.",
                "byTown": managed_by_town,
                "aggregateSevenTowns": {"km": aggregate_km, "uniqueSourceFeaturesIntersecting": aggregate_features},
            },
            "hydraulicWorks": {
                "approval": "DGRT 1155/2021",
                "sourceFeatureCounts": {kind: int(len(gdf)) for kind, gdf in works.items()},
                "method": "Conteggio delle feature ufficiali areali, lineari e puntuali che intersecano ciascun confine Istat 2026. Una feature che attraversa più Comuni compare nelle rispettive schede; l'aggregato dei sette Comuni è invece ricalcolato sulla loro unione e deduplicato per feature sorgente.",
                "byTown": works_by_town,
                "aggregateSevenTowns": works_aggregate,
            },
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {OUT}")
        print(json.dumps({"managedReticulum": result["managedReticulum"], "hydraulicWorks": result["hydraulicWorks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
