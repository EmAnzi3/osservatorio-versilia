#!/usr/bin/env python3
"""Inietta OVUXHistory e l'enhancer che sostituisce i grafici editoriali duplicati.

Il risultato runtime di Letture e Meteo usa lo stesso modulo grafico delle
schede/confronti. L'iniezione avviene dopo sync_editorial_layout, che rimuove i
runtime generici dalle pagine speciali.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
TARGETS = [
    DIST / 'letture' / 'una-versilia-che-cambia' / 'index.html',
    DIST / 'confronta' / 'meteo-clima' / 'index.html',
]


def inject(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f'Pagina editoriale mancante: {path}')
    text = path.read_text(encoding='utf-8')
    toolkit = Path(os.path.relpath(DIST / 'assets' / 'ux-history-core.js', path.parent)).as_posix()
    enhancer = Path(os.path.relpath(DIST / 'assets' / 'editorial-canonical-charts.js', path.parent)).as_posix()
    if 'assets/ux-history-core.js' not in text:
        text = text.replace('</body>', f'  <script src="{toolkit}?v=20260819-editorial-exact" defer></script>\n</body>', 1)
    if 'assets/editorial-canonical-charts.js' not in text:
        text = text.replace('</body>', f'  <script src="{enhancer}?v=20260819-editorial-exact" defer></script>\n</body>', 1)
    if text.index('assets/ux-history-core.js') > text.index('assets/editorial-canonical-charts.js'):
        raise RuntimeError(f'Ordine script canonici errato: {path}')
    path.write_text(text, encoding='utf-8')


def main() -> None:
    source = ROOT / 'assets' / 'editorial-canonical-charts.js'
    target = DIST / 'assets' / 'editorial-canonical-charts.js'
    if not source.exists():
        raise RuntimeError('Enhancer grafici editoriali mancante')
    target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
    for path in TARGETS:
        inject(path)
    print('Grafici editoriali agganciati a OVUXHistory: Lettura demografica + Meteo e clima')


if __name__ == '__main__':
    main()
