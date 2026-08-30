#!/usr/bin/env python3
"""Materializza il supporto GIS del Lotto 6 usando esclusivamente fonti ufficiali.

Scarica e verifica:
- confini comunali Istat al 1 gennaio 2026 (generalizzati);
- reticolo idrografico e di gestione DCRT 24/2025 della Regione Toscana;
- ricognizione delle opere idrauliche DGRT 1155/2021.

Il risultato e' uno snapshot JSON riproducibile. Le lunghezze vengono sempre
ricalcolate sulle geometrie dopo l'intersezione con i confini comunali.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/source-snapshots/bonifica-rischio-v126-gis.json"

TOWNS = [
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
]

SOURCES = {
    "istatBoundaries": {
        "url": "https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip",
        "sha256": "b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6",
        "label": "Istat - Confini delle unita amministrative al 1 gennaio 2026, versione generalizzata",
    },
    "reticulum": {
        "url": "https://www.regione.toscana.it/documents/d/guest/infrastruttura_rev25-zip",
        "sha256": "68d6bb2986c056e1c041009a21e3b9eb89de81d02830d412354c5770d7d9b122",
        "label": "Regione Toscana - Reticolo idrografico e di gestione DCRT 24/2025",
    },
    "hydraulicWorks": {
        "url": "https://www.regione.toscana.it/documents/10180/22470380/shp%2Bfiles%2Bcensimento%2Bopere%2Bidrauliche.zip/de6d5e57-de9f-4555-7e55-52ff32654a0e?t=1636713609857",
        "sha256": "532b29090ce6fd09f06cf87a1f074b173eeddb57cb3ee1a92560e74ef17bb560",
        "label": "Regione Toscana - Ricognizione opere idrauliche DGRT 1155/2021",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path, expected_sha: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "osservatorio-versilia/1.26 GIS materializer"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        out.write(response.read())
    actual = sha256(path)
    if actual != expected_sha:
        raise RuntimeError(f"SHA-256 inatteso per {url}: {actual} != {expected_sha}")
    if not zipfile.is_zipfile(path):
        raise RuntimeError(f"La sorgente verificata non e' uno ZIP valido: {url}")
    return {"sizeBytes": path.stat().st_size, "sha256": actual}


def extract_zip(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        zf.extractall(dest)


def find_shp(root: Path, predicate) -> Path:
    matches = sorted(p for p in root.rglob("*.shp") if predicate(p.name.lower()))
    if not matches:
        raise RuntimeError(f"Shapefile atteso non trovato in {root}")
    if len(matches) > 1:
        raise RuntimeError(f"Shapefile ambiguo in {root}: {[p.name for p in matches]}")
    return matches[0]


def pick_column(gdf: gpd.GeoDataFrame, candidates: tuple[str, ...]) -> str:
    lookup = {c.upper(): c for c in gdf.columns}
    for candidate in candidates:
        if candidate.upper() in lookup:
            return lookup[candidate.upper()]
    raise RuntimeError(f"Nessuna colonna tra {candidates}; disponibili: {list(gdf.columns)}")


def round6(value: float) -> float:
    return round(float(value), 6)


def clean_type(value) -> str:
    if value is None:
        return "n.d."
    text = str(value).strip()
    return text if text else "n.d."


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ov-bonifica-gis-") as td:
        work = Path(td)
        downloaded = {}
        for key, source in SOURCES.items():
            target = work / f"{key}.zip"
            downloaded[key] = download(source["url"], target, source["sha256"])
            source_dir = work / key
            source_dir.mkdir()
            extract_zip(target, source_dir)

        # Confini comunali Istat 2026.
        istat_root = work / "istatBoundaries"
        comuni_shp = find_shp(
            istat_root,
            lambda n: n.startswith("com") and "01012026" in n,
        )
        comuni = gpd.read_file(comuni_shp)
        name_col = pick_column(comuni, ("COMUNE", "DEN_COM", "DEN_COMUNE"))
        code_col = pick_column(comuni, ("PRO_COM_T", "PRO_COM", "COD_COM", "CODICE_COM"))
        comuni[name_col] = comuni[name_col].astype(str).str.strip()
        selected = comuni[comuni[name_col].isin(TOWNS)].copy()
        found = sorted(selected[name_col].tolist())
        if found != sorted(TOWNS):
            raise RuntimeError(f"Comuni Istat mancanti: attesi {sorted(TOWNS)}, trovati {found}")
        selected = selected.to_crs(epsg=3003)
        selected = selected[[name_col, code_col, "geometry"]].set_index(name_col).loc[TOWNS]

        boundaries_out = {}
        for town, row in selected.iterrows():
            boundaries_out[town] = {
                "istatCode": str(row[code_col]),
                "areaKm2": round6(row.geometry.area / 1_000_000),
            }

        # Reticolo gestito dal Consorzio 1 Toscana Nord.
        ret_root = work / "reticulum"
        ret_shp = find_shp(ret_root, lambda n: n == "reticolodcr242025.shp")
        ret = gpd.read_file(ret_shp)
        if ret.crs is None:
            raise RuntimeError("CRS assente nel reticolo")
        ret = ret.to_crs(epsg=3003)
        required = {"COMPLR79", "RETGESLR79", "IDRETLR79"}
        missing = required.difference(ret.columns)
        if missing:
            raise RuntimeError(f"Campi reticolo mancanti: {sorted(missing)}")
        managed = ret[(ret["COMPLR79"] == "Toscana Nord") & (ret["RETGESLR79"] == "SI")].copy()
        managed_out = {}
        for town, row in selected.iterrows():
            poly = row.geometry
            hit = managed[managed.geometry.intersects(poly)].copy()
            clipped = hit.geometry.intersection(poly)
            clipped = clipped[~clipped.is_empty]
            managed_out[town] = {
                "km": round6(clipped.length.sum() / 1000),
                "sourceFeaturesIntersecting": int(len(clipped)),
            }

        # Opere idrauliche DGRT 1155/2021: si separano le tre geometrie ufficiali.
        works_root = work / "hydraulicWorks"
        nested = sorted(works_root.rglob("DGRT_1155_2021_ricognizione_opere_idrauliche.zip"))
        if len(nested) != 1:
            raise RuntimeError(f"Archivio interno opere non univoco: {nested}")
        nested_root = work / "hydraulicWorksNested"
        nested_root.mkdir()
        extract_zip(nested[0], nested_root)

        layers = {
            "area": find_shp(nested_root, lambda n: n == "opi_a_dgrt_1155_21.shp"),
            "line": find_shp(nested_root, lambda n: n == "opi_l_dgrt_1155_21.shp"),
            "point": find_shp(nested_root, lambda n: n == "opi_pt_dgrt_1155_21.shp"),
        }
        works = {kind: gpd.read_file(path).to_crs(epsg=3003) for kind, path in layers.items()}
        for kind, gdf in works.items():
            if "TIPOLOGIA" not in gdf.columns:
                raise RuntimeError(f"TIPOLOGIA assente nel layer opere {kind}")

        works_out = {}
        for town, row in selected.iterrows():
            poly = row.geometry
            town_out = {}
            for kind, gdf in works.items():
                hit = gdf[gdf.geometry.intersects(poly)].copy()
                types = Counter(clean_type(v) for v in hit["TIPOLOGIA"].tolist())
                item = {
                    "sourceFeaturesIntersecting": int(len(hit)),
                    "types": dict(sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))),
                }
                if kind == "line":
                    clipped = hit.geometry.intersection(poly)
                    clipped = clipped[~clipped.is_empty]
                    item["clippedKm"] = round6(clipped.length.sum() / 1000)
                elif kind == "area":
                    clipped = hit.geometry.intersection(poly)
                    clipped = clipped[~clipped.is_empty]
                    item["clippedHectares"] = round6(clipped.area.sum() / 10_000)
                town_out[kind] = item
            town_out["featurePresenceTotal"] = sum(
                town_out[k]["sourceFeaturesIntersecting"] for k in ("area", "line", "point")
            )
            works_out[town] = town_out

        result = {
            "schemaVersion": 1,
            "snapshotVersion": "2026-08-31-gis-v1",
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "scope": {"towns": TOWNS, "crsForMeasurements": "EPSG:3003"},
            "sources": {
                key: {
                    "label": SOURCES[key]["label"],
                    "url": SOURCES[key]["url"],
                    **downloaded[key],
                }
                for key in SOURCES
            },
            "boundaries": {
                "sourceLayer": comuni_shp.name,
                "method": "Selezione dei sette Comuni Istat 2026 e riproiezione in EPSG:3003.",
                "byTown": boundaries_out,
            },
            "managedReticulum": {
                "sourceLayer": ret_shp.name,
                "filter": {"COMPLR79": "Toscana Nord", "RETGESLR79": "SI"},
                "method": "Intersezione geometrica con il confine comunale Istat 2026 e ricalcolo della lunghezza della geometria risultante; il campo LENGTH della sorgente non viene riutilizzato.",
                "sourceFeaturesAfterFilter": int(len(managed)),
                "byTown": managed_out,
            },
            "hydraulicWorks": {
                "approval": "DGRT 1155/2021",
                "method": "Per ciascun Comune si contano le feature ufficiali areali, lineari e puntuali che intersecano il confine Istat 2026. Per linee e aree si riportano anche lunghezza/area dopo clipping. Una feature che attraversa piu Comuni puo comparire in piu schede comunali; featurePresenceTotal non e' un totale regionale deduplicato di opere fisiche.",
                "sourceFeatureCounts": {kind: int(len(gdf)) for kind, gdf in works.items()},
                "byTown": works_out,
            },
        }

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {OUT}")
        print(json.dumps({"managedReticulum": managed_out, "hydraulicWorks": works_out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
