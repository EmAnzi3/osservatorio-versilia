#!/usr/bin/env python3
"""Download LaMMA temperature climatology GeoTIFFs and sample representative Versilia points."""
from __future__ import annotations

import argparse
import json
import math
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import rasterio
from rasterio.warp import transform

DATASETS = {
    "temperature_mean_1995_2014": "https://geoportale.lamma.rete.toscana.it/download/spazializzazioni/Tmed_climatologia.zip",
}
POINTS = {
    "Viareggio": (10.2568, 43.8745),
    "Massarosa": (10.3407, 43.8686),
    "Stazzema": (10.2954, 43.9974),
}


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.1"})
    with urllib.request.urlopen(req, timeout=180) as response, dest.open("wb") as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def clean_value(value, nodata):
    x = float(value)
    if nodata is not None and math.isclose(x, float(nodata), rel_tol=0, abs_tol=1e-8):
        return None
    if not math.isfinite(x):
        return None
    return x


def sample_tiff(path: Path) -> dict:
    with rasterio.open(path) as src:
        coords_wgs84 = list(POINTS.values())
        if src.crs and src.crs.to_string() not in {"EPSG:4326", "OGC:CRS84"}:
            xs, ys = zip(*coords_wgs84)
            tx, ty = transform("EPSG:4326", src.crs, list(xs), list(ys))
            coords = list(zip(tx, ty))
        else:
            coords = coords_wgs84
        values = list(src.sample(coords, indexes=1, masked=False))
        samples = {name: clean_value(values[i][0], src.nodata) for i, name in enumerate(POINTS)}
        return {
            "file": path.name,
            "crs": src.crs.to_string() if src.crs else None,
            "width": src.width,
            "height": src.height,
            "resolution": [abs(float(src.transform.a)), abs(float(src.transform.e))],
            "bounds": [float(x) for x in src.bounds],
            "nodata": src.nodata,
            "samples": samples,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/runtime/meteo-poc/lamma-temperature-samples.json")
    args = parser.parse_args()
    results = {}

    with tempfile.TemporaryDirectory(prefix="lamma-poc-") as temp_name:
        temp = Path(temp_name)
        for dataset, url in DATASETS.items():
            archive = temp / f"{dataset}.zip"
            print(f"[lamma-sample] downloading {dataset}")
            download(url, archive)
            extract_dir = temp / dataset
            extract_dir.mkdir()
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract_dir)
                members = zf.namelist()
            tiffs = sorted([p for p in extract_dir.rglob("*") if p.suffix.lower() in {".tif", ".tiff"}])
            print(f"[lamma-sample] {dataset}: archive={archive.stat().st_size} bytes, members={len(members)}, tiffs={len(tiffs)}")
            sampled = []
            for tif in tiffs:
                info = sample_tiff(tif)
                sampled.append(info)
                s = info["samples"]
                if "annuale" in info["file"] or "mensile" in info["file"]:
                    print(f"  {info['file']} | Viareggio={s['Viareggio']} | Massarosa={s['Massarosa']} | Stazzema={s['Stazzema']}")
            results[dataset] = {"url": url, "archive_bytes": archive.stat().st_size, "rasters": sampled}

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"points": POINTS, "datasets": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
