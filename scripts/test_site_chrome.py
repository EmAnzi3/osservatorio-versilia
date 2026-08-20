#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

import copy_percorsi_dist
from site_chrome import ensure_sitemap_entries, extract_native_shell, search_fallback_link


TEMPLATE = '''<!doctype html><html lang="it"><head>
<link rel="stylesheet" href="../assets/fonts.css">
<link rel="stylesheet" href="../assets/static.css">
</head><body>
<div id="site-header-mount"><a class="skip-link" href="#app">Vai al contenuto</a>
<header class="site-header"><a href="../" class="site-brand">OV</a><div class="site-header-actions">
<nav aria-label="Navigazione principale"><a href="../#temi">Temi</a><a href="../#comuni">Comuni</a><a href="../progetto/">Il progetto</a><a href="../stato-dati/" data-data-status-nav="header">Stato dati</a><a href="../segnala/">Segnala</a></nav>
<button class="global-search-trigger" type="button"><span>Cerca</span><kbd>/</kbd></button></div></header></div>
<div id="app"><main><h1>Progetto</h1></main></div>
<div id="site-footer-mount"><footer class="site-footer"><nav class="footer-links" aria-label="Informazioni sul progetto"><a href="../progetto/">Il progetto</a><a href="../stato-dati/" data-data-status-nav="footer">Stato dei dati</a><a href="../progetto/#metodo">Metodo</a><a href="../progetto/#licenza">Licenza</a><a href="../progetto/#versioni">Versioni dei dati</a><a href="../segnala/">Segnala un dato</a><a href="mailto:info@osservatorioversilia.it">Contatti</a></nav></footer></div>
<noscript>no js</noscript><script src="../assets/app-bundle.js"></script></body></html>'''


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        dist = Path(directory)
        template = dist / "progetto" / "index.html"
        template.parent.mkdir(parents=True)
        template.write_text(TEMPLATE, encoding="utf-8")
        target = dist / "speciale" / "annidata" / "index.html"

        shell = extract_native_shell(dist, target)
        assert 'href="../../#temi"' in shell.header
        assert 'href="../../stato-dati/"' in shell.header
        assert 'href="../../progetto/#versioni"' in shell.footer
        assert shell.app_bundle == "../../assets/app-bundle.js"
        assert 'href="../../assets/fonts.css"' in shell.styles

        fallback = search_fallback_link(shell.header)
        assert '<a class="global-search-trigger" href="../../"' in fallback
        assert "<kbd" not in fallback
        assert '<button class="global-search-trigger"' not in fallback

        (dist / "sitemap.xml").write_text(
            '<?xml version="1.0"?><urlset><url><loc>https://osservatorioversilia.it/</loc>'
            '<lastmod>2026-08-16</lastmod></url></urlset>\n',
            encoding="utf-8",
        )
        ensure_sitemap_entries(
            dist,
            (
                "https://osservatorioversilia.it/pnrr/",
                "https://osservatorioversilia.it/pnrr/",
            ),
        )
        sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
        assert sitemap.count("https://osservatorioversilia.it/pnrr/") == 1
        assert "<lastmod>2026-08-16</lastmod>" in sitemap

        copy_percorsi_dist.DIST = dist
        copy_percorsi_dist.SOURCE = Path(__file__).resolve().parents[1] / "percorsi"
        copy_percorsi_dist.TARGET = dist / "percorsi"
        copy_percorsi_dist.main()

        map_page = (dist / "percorsi" / "index.html").read_text(encoding="utf-8")
        method_page = (dist / "percorsi" / "metodo.html").read_text(encoding="utf-8")
        assert map_page.count('data-data-status-nav="header"') == 1
        assert 'class="global-search-trigger" href="../"' in map_page
        assert 'id="map"' in map_page
        assert 'class="site-footer"' not in map_page
        assert method_page.count('data-data-status-nav="header"') == 1
        assert method_page.count('data-data-status-nav="footer"') == 1
        assert 'class="global-search-trigger" href="../"' in method_page
        sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
        assert sitemap.count("<loc>https://osservatorioversilia.it/percorsi/</loc>") == 1
        assert sitemap.count(
            "<loc>https://osservatorioversilia.it/percorsi/metodo.html</loc>"
        ) == 1

    print("Site chrome tests passed: contract, rebasing, fallback search, Percorsi and sitemap.")


if __name__ == "__main__":
    main()
