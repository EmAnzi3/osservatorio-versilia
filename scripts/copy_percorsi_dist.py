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

from site_chrome import ensure_sitemap_entries, extract_native_shell, search_fallback_link

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOURCE = ROOT / "percorsi"
TARGET = DIST / "percorsi"


def ensure_shell_styles(document: str, styles: str) -> str:
    missing = []
    for stylesheet in styles.splitlines():
        item = stylesheet.strip()
        href = re.search(r'href="([^"]+)"', item)
        if href and f'href="{href.group(1)}"' not in document:
            missing.append(f"  {item}")
    if missing:
        document = document.replace("</head>", "\n".join(missing) + "\n</head>", 1)
    return document


def integrate_canonical_chrome() -> None:
    """Riusa la shell OV; la mappa mantiene solo l'eccezione footer full-screen."""
    index = TARGET / "index.html"
    method = TARGET / "metodo.html"

    index_shell = extract_native_shell(DIST, index, require_bundle=False)
    index_header = search_fallback_link(index_shell.header)
    index_header = index_header.replace(
        '<div id="site-header-mount">',
        '<div id="site-header-mount" class="percorsi-site-header">',
        1,
    )
    index_header = index_header.replace('href="#app">Vai al contenuto', 'href="#map">Vai alla mappa', 1)
    index_text = index.read_text(encoding="utf-8")
    header_start = index_text.find('<div id="site-header-mount"')
    content_start = index_text.find('<div class="map-context-bar"', header_start)
    if min(header_start, content_start) < 0:
        raise RuntimeError("Shell cartografica non riconoscibile")
    index_text = index_text[:header_start] + index_header + index_text[content_start:]
    index_text = ensure_shell_styles(index_text, index_shell.styles)
    index.write_text(index_text, encoding="utf-8")

    method_shell = extract_native_shell(DIST, method, require_bundle=False)
    method_header = search_fallback_link(method_shell.header)
    method_text = method.read_text(encoding="utf-8")
    if '<div id="site-header-mount">' not in method_text:
        method_text = method_text.replace(
            "<body>",
            '<body class="antialiased percorsi-method-page">\n' + method_header,
            1,
        )
    if '<div id="site-footer-mount">' not in method_text:
        method_text = method_text.replace(
            "</body>",
            method_shell.footer + "</body>",
            1,
        )
    method_text = ensure_shell_styles(method_text, method_shell.styles)
    method.write_text(method_text, encoding="utf-8")


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

    integrate_canonical_chrome()
    ensure_sitemap_entries(
        DIST,
        (
            "https://osservatorioversilia.it/percorsi/",
            "https://osservatorioversilia.it/percorsi/metodo.html",
        ),
    )

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

    print(
        "Cartografia Percorsi copiata nella build e riallineata alla shell OV; "
        "la mappa full-screen mantiene l'eccezione footer."
    )


if __name__ == "__main__":
    main()
