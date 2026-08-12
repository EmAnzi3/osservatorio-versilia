#!/usr/bin/env python3
"""Copia la mini-app cartografica Percorsi nella build statica.

Le statistiche sono ormai parte del renderer principale dell'Osservatorio e
vengono preparate prima della seconda build della PR. Questo passaggio deve
quindi limitarsi a copiare la cartografia, senza aggiungere box o script nelle
pagine Mobilita/Comuni.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOURCE = ROOT / "percorsi"
TARGET = DIST / "percorsi"


def main() -> None:
    if not SOURCE.exists():
        raise RuntimeError(f"Percorsi Versilia non trovato: {SOURCE}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)

    index = TARGET / "index.html"
    text = index.read_text(encoding="utf-8")
    if "deeplink.js" not in text:
        pattern = r'(<script src="app\.js\?v=\d+"></script>)'
        match = re.search(pattern, text)
        if not match:
            raise RuntimeError("Anchor app.js non trovato nella cartografia")
        text = re.sub(pattern, r'\1\n<script src="deeplink.js?v=1"></script>', text, count=1)
        index.write_text(text, encoding="utf-8")

    required = (
        TARGET / "index.html",
        TARGET / "metodo.html",
        TARGET / "app.js",
        TARGET / "data-loader.js",
        TARGET / "deeplink.js",
        TARGET / "styles.css",
        TARGET / "osservatorio.css",
        TARGET / "data" / "master_summary.json",
        TARGET / "data" / "site_stats.json",
    )
    missing = [str(path.relative_to(DIST)) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Build Percorsi incompleta: {', '.join(missing)}")

    print("Cartografia Percorsi copiata nella build; statistiche gestite dal renderer principale dell'Osservatorio.")


if __name__ == "__main__":
    main()
