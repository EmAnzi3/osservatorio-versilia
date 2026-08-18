#!/usr/bin/env python3
"""Collega l'esperienza PNRR di revisione alle pagine della build statica.

Da eseguire dopo ``build_pnrr_toscana_deep_dive.py``. Aggiunge soltanto gli asset
runtime che trasformano il vecchio approfondimento comunale ambiguo nel dettaglio
PNRR del Comune e inseriscono il riepilogo PNRR nella pagina generale del tema.
"""
from __future__ import annotations

from pathlib import Path

DIST = Path("dist")
TOWN_SLUGS = (
    "camaiore",
    "forte-dei-marmi",
    "massarosa",
    "pietrasanta",
    "seravezza",
    "stazzema",
    "viareggio",
)


def inject(path: Path, prefix: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Pagina mancante: {path}")
    text = path.read_text(encoding="utf-8")
    css = f'{prefix}assets/pnrr-town-detail.css'
    js = f'{prefix}assets/pnrr-town-detail.js'

    if css not in text:
        text = text.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{css}">\n</head>',
            1,
        )
    if js not in text:
        text = text.replace(
            "</body>",
            f'  <script src="{js}" defer></script>\n</body>',
            1,
        )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    for slug in TOWN_SLUGS:
        inject(DIST / "comuni" / slug / "index.html", "../../")
    inject(DIST / "confronta" / "comunita" / "index.html", "../../")

    print("Esperienza PNRR collegata: 7 pagine comunali + confronto Investimenti e comunità")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
