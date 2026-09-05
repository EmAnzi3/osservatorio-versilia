#!/usr/bin/env python3
"""Materializza l'Atlante Registro Imprese nella shell canonica del sito."""
from __future__ import annotations

from pathlib import Path

from site_chrome import ensure_sitemap_entries, synchronize_native_page

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = DIST / "confronta" / "economia" / "atlante-attivita-economiche" / "index.html"
CANONICAL = "https://osservatorioversilia.it/confronta/economia/atlante-attivita-economiche/"


def main() -> None:
    if not TARGET.exists():
        raise RuntimeError(f"Pagina Atlante non trovata nella build: {TARGET}")
    synchronize_native_page(DIST, TARGET)
    ensure_sitemap_entries(DIST, (CANONICAL,))
    print("Atlante attività economiche materializzato nella shell canonica.")


if __name__ == "__main__":
    main()
