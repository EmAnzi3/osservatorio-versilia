#!/usr/bin/env python3
"""POC: aggregate one full year of LaMMA 1 km daily precipitation at three Versilia points."""
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

YEAR = 2015
URL = f"https://geoportale.lamma.rete.toscana.it/download/spazializzazioni/Prec_giornaliero_{YEAR}.zip"
POINTS = {
    "Viareggio": (10.2568, 43.8745),
    "Massarosa": (10.3407, 43.8686),
    "Stazzema": (10.2954, 43.9974),
}


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"})
    with urllib.request.urlopen(req, timeout=300) as response, dest.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def sample_one(path: Path) -> tuple[dict[str, float | None], dict]:
    with rasterio.open(path) as src:
        coords = list(POINTS.values())
        if src.crs and src.crs.to_string() not in {"EPSG:4326", "OGC:CRS84"}:
            xs, ys = zip(*coords)
            tx, ty = transform("EPSG:4326", src.crs, list(xs), list(ys))
            coords = list(zip(tx, ty))
        raw = list(src.sample(coords, indexes=1, masked=False))
        values = {}
        for i, name in enumerate(POINTS):
            x = float(raw[i][0])
            if not math.isfinite(x) or (src.nodata is not None and math.isclose(x, float(src.nodata), abs_tol=1e-8)):
                values[name] = None
            else:
                values[name] = x
        meta = {
            "crs": src.crs.to_string() if src.crs else None,
            "resolution": [abs(float(src.transform.a)), abs(float(src.transform.e))],
            "width": src.width,
            "height": src.height,
        }
        return values, meta


def summarize(series: list[float]) -> dict:
    return {
        "days": len(series),
        "annual_precip_mm": sum(series),
        "wet_days_ge_1mm": sum(v >= 1.0 for v in series),
        "days_ge_20mm": sum(v >= 20.0 for v in series),
        "days_ge_50mm": sum(v >= 50.0 for v in series),
        "max_daily_mm": max(series) if series else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/runtime/meteo-poc/lamma-precip-2015.json")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="lamma-precip-") as tmp_name:
        tmp = Path(tmp_name)
        archive = tmp / f"precip-{YEAR}.zip"
        print(f"[lamma-precip] downloading {URL}")
        download(URL, archive)
        print(f"[lamma-precip] archive size={archive.stat().st_size} bytes")
        extract = tmp / "rasters"
        extract.mkdir()
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract)
        tiffs = sorted(p for p in extract.rglob("*") if p.suffix.lower() in {".tif", ".tiff"})
        print(f"[lamma-precip] tiffs={len(tiffs)}")
        if len(tiffs) < 360:
            raise RuntimeError(f"Expected about 365 daily rasters, found {len(tiffs)}")

        series = {name: [] for name in POINTS}
        raster_meta = None
        missing = {name: 0 for name in POINTS}
        daily = []
        for tif in tiffs:
            values, meta = sample_one(tif)
            raster_meta = raster_meta or meta
            row = {"file": tif.name, "values_mm": values}
            daily.append(row)
            for name, value in values.items():
                if value is None:
                    missing[name] += 1
                else:
                    series[name].append(value)

        summary = {}
        for name in POINTS:
            if missing[name] > 5:
                raise RuntimeError(f"Too many missing daily values for {name}: {missing[name]}")
            summary[name] = summarize(series[name])
            summary[name]["missing_days"] = missing[name]
            print(f"[lamma-precip] {name}: {summary[name]}")

        payload = {
            "status": "POC point samples, not municipal averages",
            "year": YEAR,
            "source_url": URL,
            "license": "Creative Commons Attribution (catalog metadata)",
            "points": POINTS,
            "raster": raster_meta,
            "summary": summary,
            "daily": daily,
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
