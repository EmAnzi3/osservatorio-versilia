#!/usr/bin/env python3
"""Include Percorsi Versilia e il relativo strato statistico nella build statica."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOURCE = ROOT / "percorsi"
TARGET = DIST / "percorsi"
INTEGRATION_ASSETS = ("percorsi-integration.css", "percorsi-integration.js")
INTEGRATION_VERSION = "20260812-2"
TOWN_SLUGS = (
    "camaiore",
    "forte-dei-marmi",
    "massarosa",
    "pietrasanta",
    "seravezza",
    "stazzema",
    "viareggio",
)


def inject_integration_assets(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Pagina da integrare non trovata: {path}")
    text = path.read_text(encoding="utf-8")
    prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
    relative_root = "" if prefix == "." else f"{prefix}/"
    css = f"{relative_root}assets/percorsi-integration.css?v={INTEGRATION_VERSION}"
    js = f"{relative_root}assets/percorsi-integration.js?v={INTEGRATION_VERSION}"
    if "assets/percorsi-integration.css" not in text:
        text = text.replace("</head>", f'  <link rel="stylesheet" href="{css}">\n</head>')
    if "assets/percorsi-integration.js" not in text:
        text = text.replace("</body>", f'  <script src="{js}" defer></script>\n</body>')
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        raise RuntimeError(f"Percorsi Versilia non trovato: {SOURCE}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)

    dist_assets = DIST / "assets"
    dist_assets.mkdir(parents=True, exist_ok=True)
    for name in INTEGRATION_ASSETS:
        source = ROOT / "assets" / name
        if not source.exists() or source.stat().st_size == 0:
            raise RuntimeError(f"Asset integrazione Percorsi mancante: {source}")
        shutil.copy2(source, dist_assets / name)

    inject_integration_assets(DIST / "confronta" / "mobilita" / "index.html")
    for slug in TOWN_SLUGS:
        inject_integration_assets(DIST / "comuni" / slug / "index.html")

    required = (
        TARGET / "index.html",
        TARGET / "app.js",
        TARGET / "data-loader.js",
        TARGET / "styles.css",
        TARGET / "data" / "master_summary.json",
        TARGET / "data" / "site_stats.json",
        dist_assets / "percorsi-integration.css",
        dist_assets / "percorsi-integration.js",
    )
    missing = [str(path.relative_to(DIST)) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Build Percorsi incompleta: {', '.join(missing)}")
    print("Percorsi Versilia e statistiche di mobilità lenta inclusi nella build statica.")


if __name__ == "__main__":
    main()
