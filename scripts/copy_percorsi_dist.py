#!/usr/bin/env python3
"""Include il tool standalone Percorsi Versilia nella build statica."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "percorsi"
TARGET = ROOT / "dist" / "percorsi"


def main() -> None:
    if not SOURCE.exists():
        raise RuntimeError(f"Percorsi Versilia non trovato: {SOURCE}")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)
    required = (
        TARGET / "index.html",
        TARGET / "app.js",
        TARGET / "data-loader.js",
        TARGET / "styles.css",
        TARGET / "data" / "master_summary.json",
    )
    missing = [str(path.relative_to(ROOT / "dist")) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Build Percorsi incompleta: {', '.join(missing)}")
    print("Percorsi Versilia incluso nella build statica.")


if __name__ == "__main__":
    main()
