#!/usr/bin/env python3
"""Materializza il renderer v4 dei Rapporti dopo la build editoriale.

Il renderer e' mantenuto in parti sorgente per rendere verificabile il contratto
fondamentale: i grafici dei Rapporti non hanno un motore autonomo. Le pagine
caricano direttamente assets/ux-history-core.js, lo stesso modulo usato dal sito,
e il bundle dei Rapporti si limita a comporre analisi, figure e tabelle attorno
a quei componenti canonici.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PARTS = ROOT / "assets" / "rapporti-parts"


def bundle() -> str:
    paths = sorted(PARTS.glob("*.txt"))
    if not paths:
        raise RuntimeError("Parti del renderer Rapporti v4 non trovate")
    text = "".join(path.read_text(encoding="utf-8") for path in paths)
    if "const history = window.OVUXHistory" not in text:
        raise RuntimeError("Il renderer v4 non dichiara il toolkit grafico canonico")
    if "historicalChartMarkup(metric" in text and "history.historicalChartMarkup" not in text:
        raise RuntimeError("Rilevato un renderer storico parallelo")
    return text


def upgrade_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "assets/rapporti.js" not in text:
        raise RuntimeError(f"Bootstrap Rapporti assente: {path}")
    if "assets/ux-history-core.js" not in text:
        match = re.search(r'<script\b[^>]*src="([^"]*assets/rapporti\.js[^"]*)"[^>]*></script>', text, re.I)
        if not match:
            raise RuntimeError(f"Script Rapporti non trovato: {path}")
        src = match.group(1)
        prefix = src.split("assets/rapporti.js", 1)[0]
        toolkit = f'<script src="{prefix}assets/ux-history-core.js?v=20260819-report-v4" defer></script>\n  '
        text = text[:match.start()] + toolkit + text[match.start():]
    if 'data-report-version="4"' not in text:
        text = text.replace('class="antialiased report-page"', 'class="antialiased report-page" data-report-version="4"', 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    asset = DIST / "assets" / "rapporti.js"
    asset.parent.mkdir(parents=True, exist_ok=True)
    runtime = bundle()
    asset.write_text(runtime, encoding="utf-8")

    pages = sorted((DIST / "rapporti").glob("**/index.html"))
    if len(pages) != 9:
        raise RuntimeError(f"Attese 9 pagine Rapporti, trovate {len(pages)}")
    for page in pages:
        upgrade_page(page)

    print(f"Rapporti v4 materializzati: {len(pages)} pagine; grafici delegati a OVUXHistory")


if __name__ == "__main__":
    main()
