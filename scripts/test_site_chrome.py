#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

import copy_percorsi_dist
from site_chrome import (
    assert_navigation_contract,
    ensure_sitemap_entries,
    extract_native_shell,
    synchronize_native_page,
)


TEMPLATE = '''<!doctype html><html lang="it"><head>
<link rel="stylesheet" href="../assets/fonts.css">
<link rel="stylesheet" href="../assets/static.css">
</head><body>
<div id="site-header-mount"><a class="skip-link" href="#app">Vai al contenuto</a>
<header class="site-header"><a href="../" class="site-brand">OV</a><div class="site-header-actions">
<nav aria-label="Navigazione principale"><a href="../#temi">Temi</a><a href="../#comuni">Comuni</a><a href="../opportunita/">Opportunità</a><a href="../progetto/">Il progetto</a><a href="../stato-dati/" data-data-status-nav="header">Stato dati</a><a href="../segnala/">Segnala</a></nav>
<button class="global-search-trigger" type="button"><span>Cerca</span><kbd>/</kbd></button></div></header></div>
<div id="app"><main><h1>Progetto</h1></main></div>
<div id="site-footer-mount"><footer class="site-footer"><nav class="footer-links" aria-label="Informazioni sul progetto"><a href="../progetto/">Il progetto</a><a href="../stato-dati/" data-data-status-nav="footer">Stato dei dati</a><a href="../opportunita/">Opportunità</a><a href="../progetto/#metodo">Metodo</a><a href="../progetto/#licenza">Licenza</a><a href="../progetto/#versioni">Versioni dei dati</a><a href="../segnala/">Segnala un dato</a><a href="mailto:info@osservatorioversilia.it">Contatti</a></nav><div class="footer-social" data-social-placement="footer"><strong>Social</strong><div class="social-links"><a href="https://example.test/">Profilo</a></div></div><div class="footer-note"><span>Nota</span></div></footer></div>
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

        special = dist / "speciale" / "index.html"
        special.parent.mkdir(parents=True, exist_ok=True)
        special.write_text(
            '<!doctype html><html><head></head><body data-page="special">'
            '<div id="site-header-mount"></div><main id="app"><h1>Speciale</h1></main>'
            '<div id="site-footer-mount"></div></body></html>',
            encoding="utf-8",
        )
        synchronize_native_page(dist, special)
        synchronized = special.read_text(encoding="utf-8")
        assert '<button class="global-search-trigger"' in synchronized
        assert "../assets/app-bundle.js" in synchronized
        assert synchronized.count('class="site-footer"') == 1
        assert 'data-social-placement="footer"' in synchronized

        noindex = dist / "bozza" / "index.html"
        noindex.parent.mkdir(parents=True, exist_ok=True)
        noindex.write_text(
            '<!doctype html><html><head><meta name="robots" content="noindex,nofollow"></head>'
            '<body data-page="special"><div id="site-header-mount"></div>'
            '<main id="app"><h1>Bozza</h1></main><div id="site-footer-mount"></div></body></html>',
            encoding="utf-8",
        )
        synchronize_native_page(dist, noindex)
        noindex_text = noindex.read_text(encoding="utf-8")
        assert 'data-social-placement="footer"' not in noindex_text
        assert 'class="footer-note"' in noindex_text

        fallback = shell.header.replace(
            '<button class="global-search-trigger" type="button"><span>Cerca</span><kbd>/</kbd></button>',
            '<a class="global-search-trigger" href="../../"><span>Cerca</span></a>',
        )
        try:
            assert_navigation_contract(fallback, shell.footer)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Il contratto deve rifiutare la ricerca fallback")

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
        assert '<button class="global-search-trigger"' in map_page
        assert "<kbd>/</kbd>" in map_page
        assert 'data-page="special"' in map_page
        assert "../assets/app-bundle.js" in map_page
        assert 'id="map"' in map_page
        assert 'class="site-footer"' not in map_page
        assert method_page.count('data-data-status-nav="header"') == 1
        assert method_page.count('data-data-status-nav="footer"') == 1
        assert '<button class="global-search-trigger"' in method_page
        assert "<kbd>/</kbd>" in method_page
        assert 'data-page="special"' in method_page
        assert "../assets/app-bundle.js" in method_page
        sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
        assert sitemap.count("<loc>https://osservatorioversilia.it/percorsi/</loc>") == 1
        assert sitemap.count(
            "<loc>https://osservatorioversilia.it/percorsi/metodo.html</loc>"
        ) == 1

    print("Site chrome tests passed: contract, rebasing, live search, Percorsi and sitemap.")


if __name__ == "__main__":
    main()
