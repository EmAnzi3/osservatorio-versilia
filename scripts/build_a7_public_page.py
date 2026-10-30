#!/usr/bin/env python3
"""Pagina pubblica «Chiedi alla Versilia» nella shell statica canonica del sito.

Dal 30 ottobre 2026 (A7.5.6, decisione del proprietario) la pagina ospita solo
l'esploratore dei dati, inserito da `build_a7_explorer_preview`, e un rimando ai
dossier. Le domande guidate del pilota (offerta educativa e percorsi su
Massarosa) non sono più pubblicate: i loro temi sono coperti dai dossier in forma
di relazione. Il pilota resta verificato come esperimento, fuori dalla pagina.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path

from site_chrome import ensure_sitemap_entries, extract_native_shell

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://osservatorioversilia.it/chiedi/'
STYLE_SOURCE = ROOT / 'experiments/a7-dossier-preview/public.css'
STYLE = 'chiedi.css'
TITLE = 'Chiedi alla Versilia · Osservatorio Versilia'
DESCRIPTION = ('Scegli un indicatore e un confronto: valori dei sette Comuni della Versilia, confronti con Toscana e '
               'Italia, serie e variazioni, con periodi, fonti e limiti di ogni dato.')


def social(title: str, description: str) -> str:
    image = 'https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg'
    alt = 'Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia'
    og = {'og:title': title, 'og:description': description, 'og:type': 'website', 'og:locale': 'it_IT', 'og:url': URL,
          'og:site_name': 'Osservatorio Versilia', 'og:image': image, 'og:image:alt': alt}
    twitter = {'card': 'summary_large_image', 'title': title, 'description': description, 'site': '@OssVersilia',
               'image': image, 'image:alt': alt}
    esc = lambda value: html.escape(value, quote=True)
    return '\n'.join([f'<meta property="{k}" content="{esc(v)}">' for k, v in og.items()]
                     + [f'<meta name="twitter:{k}" content="{esc(v)}">' for k, v in twitter.items()])


def build(dist: Path = ROOT / 'dist', commit: str | None = None) -> Path:
    """`commit` è accettato per compatibilità con la build: la pagina non incorpora più un rilascio del pilota."""
    folder = dist / 'chiedi'
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / 'index.html'
    # Il foglio di stile della pagina: lo stesso del pilota, con il percorso
    # dell'immagine del banner riportato alla cartella della pagina.
    css = STYLE_SOURCE.read_text(encoding='utf-8').replace("url('../../../assets/", "url('../assets/")
    (folder / STYLE).write_text(css, encoding='utf-8')
    shell = extract_native_shell(dist, page)
    # The seven-route secondary-page stylesheet has its own approved scope.
    styles = '\n'.join(line for line in shell.styles.splitlines() if 'secondary-pages-ui.css' not in line)
    structured = json.dumps({'@context': 'https://schema.org', '@type': 'WebPage', 'name': TITLE,
                             'description': DESCRIPTION, 'url': URL}, ensure_ascii=False)
    structured_hash = base64.b64encode(hashlib.sha256(structured.encode()).digest()).decode()
    page.write_text(f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'sha256-{structured_hash}'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'">
<title>{TITLE}</title><meta name="description" content="{html.escape(DESCRIPTION, quote=True)}">{social(TITLE, DESCRIPTION)}
<link rel="canonical" href="{URL}"><script type="application/ld+json">{structured}</script>
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="manifest" href="../site.webmanifest">
{styles}<link rel="stylesheet" href="{STYLE}"><meta name="theme-color" content="#0F3654">
</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
<a class="a7-skip" href="#a7-guided">Vai all’esplorazione dei dati</a>
{shell.header}<div id="app"><div class="a7-banner"><section class="a7-hero editorial-hero">
<p class="eyebrow">CONOSCERE IL TERRITORIO</p>
<h1>Chiedi alla Versilia</h1>
<p>Scegli un indicatore e che cosa vuoi sapere: il valore di un Comune, il confronto fra i sette Comuni, l’andamento nel tempo o il confronto con Toscana e Italia.</p>
<p class="notice">Ogni risultato riporta periodo, fonte e limiti del dato. Puoi copiarne il link, scaricare i dati o salvarlo in PDF.</p>
<p class="a7-how">Esplorazione dei dati · Dossier</p>
</section></div><main id="a7-guided" class="editorial-page page-width a7-guided">
<nav aria-label="Percorso pagina"><a href="../">Home</a> · Chiedi alla Versilia</nav>
<section class="a7-dossier-link" aria-labelledby="chiedi-dossier">
<h2 id="chiedi-dossier">Preferisci una lettura già pronta?</h2>
<p>I dossier raccontano i grandi temi della Versilia — casa, lavoro, turismo, anziani e scuola — con grafici, confronti e una versione per ciascun Comune.</p>
<p><a href="../dossier/">Vai ai dossier</a></p>
</section>
<p>Approfondisci i dati: <a href="../#comuni">schede dei Comuni</a> · <a href="../stato-dati/">stato dei dati</a> · <a href="../segnala/">segnala un errore</a>.</p>
</main></div>{shell.footer}
<script src="{html.escape(shell.app_bundle, quote=True)}" defer></script>
</body></html>''', encoding='utf-8')
    from build_static_brand_impl import cache_bust_app_bundle, cache_bust_favicon, inject_pwa
    page.write_text(inject_pwa(cache_bust_app_bundle(cache_bust_favicon(page.read_text(encoding='utf-8'))), '../'), encoding='utf-8')
    ensure_sitemap_entries(dist, (URL,))
    return page


if __name__ == '__main__':
    print('Pagina «Chiedi alla Versilia» generata: ' + str(build()))
