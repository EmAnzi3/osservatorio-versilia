#!/usr/bin/env python3
"""Publish the reviewed guided reader inside the canonical static OV shell."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup
from build_a7_dossier_preview import preview
from site_chrome import ensure_sitemap_entries, extract_native_shell

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://osservatorioversilia.it/chiedi/'


def build(dist: Path = ROOT / 'dist', commit: str | None = None) -> Path:
    commit = commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    folder = dist / 'chiedi'
    # Original builder checks Git snapshots before emitting any answer assets.
    preview(folder, commit, catalog=dist / 'data/site-data.json')
    page = folder / 'index.html'
    original = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
    hero = original.header
    hero.name = 'section'
    hero['class'] = ['a7-hero']
    hero.h1.string = 'Chiedi alla Versilia'
    hero.select_one('.eyebrow').string = 'Percorsi guidati · Massarosa'
    hero.select_one('.notice').string = 'Primi percorsi sperimentali: Massarosa, lavoro e infanzia/scuola. Le evidenze si riferiscono ai periodi indicati, non automaticamente alla situazione di oggi.'
    local_footer = original.footer
    local_footer.name = 'section'
    local_footer['aria-label'] = 'Limiti delle letture'
    original.main.noscript.clear()
    fallback = original.new_tag('p')
    fallback.string = 'Per scegliere una domanda occorre JavaScript. '
    link = original.new_tag('a', href='answers.md')
    link.string = 'Leggi le evidenze in formato testo.'
    fallback.append(link)
    original.main.noscript.append(fallback)
    content = str(hero) + original.main.decode_contents() + str(local_footer)
    shell = extract_native_shell(dist, page)
    # The seven-route secondary-page stylesheet has its own approved scope.
    styles = '\n'.join(line for line in shell.styles.splitlines() if 'secondary-pages-ui.css' not in line)
    title = 'Chiedi alla Versilia · Osservatorio Versilia'
    description = 'Esplora lavoro e infanzia/scuola a Massarosa con domande guidate, evidenze verificabili, fonti e limiti espliciti.'
    image = 'https://osservatorioversilia.it/images/versilia-viareggio-apuane.jpg'
    image_alt = 'Viareggio e le Alpi Apuane, immagine di Osservatorio Versilia'
    metas = {'og:title': title, 'og:description': description, 'og:type': 'website', 'og:locale': 'it_IT', 'og:url': URL, 'og:site_name': 'Osservatorio Versilia', 'og:image': image, 'og:image:alt': image_alt}
    social = '\n'.join(f'<meta property="{key}" content="{html.escape(value, quote=True)}">' for key, value in metas.items())
    twitter = {'card': 'summary_large_image', 'title': title, 'description': description, 'site': '@OssVersilia', 'image': image, 'image:alt': image_alt}
    social += '\n' + '\n'.join(f'<meta name="twitter:{key}" content="{html.escape(value, quote=True)}">' for key, value in twitter.items())
    structured = json.dumps({'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'description': description, 'url': URL}, ensure_ascii=False)
    structured_hash = base64.b64encode(hashlib.sha256(structured.encode()).digest()).decode()
    page.write_text(f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'sha256-{structured_hash}'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'">
<title>{title}</title><meta name="description" content="{description}">{social}
<link rel="canonical" href="{URL}"><script type="application/ld+json">{structured}</script>
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="manifest" href="../site.webmanifest">
{styles}<link rel="stylesheet" href="public.css"><meta name="theme-color" content="#0F3654">
</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
<a class="a7-skip" href="#a7-guided">Vai alle domande</a>
{shell.header}<div id="app"><main id="a7-guided" class="editorial-page page-width a7-guided">
<nav aria-label="Percorso pagina"><a href="../">Home</a> · Chiedi alla Versilia</nav>
{content}
<p>Approfondisci i dati: <a href="../comuni/massarosa/">scheda di Massarosa</a> · <a href="../confronta/lavoro/">lavoro</a> · <a href="../confronta/istruzione/">istruzione</a> · <a href="../stato-dati/">stato dei dati</a>.</p>
</main></div>{shell.footer}
<script src="{html.escape(shell.app_bundle, quote=True)}" defer></script><script type="module" src="preview.mjs"></script>
</body></html>''', encoding='utf-8')
    from build_static_brand_impl import cache_bust_app_bundle, cache_bust_favicon, inject_pwa
    page.write_text(inject_pwa(cache_bust_app_bundle(cache_bust_favicon(page.read_text(encoding='utf-8'))), '../'), encoding='utf-8')
    shutil.copyfile(ROOT / 'experiments/a7-dossier-preview/public.css', folder / 'public.css')
    # The isolated preview stylesheet is not used by the public shell.
    (folder / 'preview.css').unlink()
    ensure_sitemap_entries(dist, (URL,))
    return page


if __name__ == '__main__':
    print('A7 guided public page generated: ' + str(build()))
