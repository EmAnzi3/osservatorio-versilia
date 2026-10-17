#!/usr/bin/env python3
"""Publish the reviewed guided reader inside the canonical static OV shell."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup
from build_a7_dossier_preview import preview, validate_repository_commit
from site_chrome import ensure_sitemap_entries, extract_native_shell
from a7_public_release import FILES, manifest_text
from a7_education_editorial import build_reading, write_report, territorial_evidence

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://osservatorioversilia.it/chiedi/'


def build(dist: Path = ROOT / 'dist', commit: str | None = None) -> Path:
    commit = commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    folder = dist / 'chiedi'
    page = folder / 'index.html'
    # Build an immutable graph before changing the HTML entry point. Every
    # relative module import and bundle fetch resolves inside this one graph.
    with tempfile.TemporaryDirectory(prefix='a7-public-release-') as tmp:
        stage = Path(tmp)
        preview(stage, commit, catalog=dist / 'data/site-data.json')
        original = BeautifulSoup((stage / 'index.html').read_text(encoding='utf-8'), 'html.parser')
        for name in ['public.css', 'public.mjs', 'education.mjs']:
            shutil.copyfile(ROOT / 'experiments/a7-dossier-preview' / name, stage / name)
        bundle = json.loads((stage / 'bundle.json').read_text())
        territorial = territorial_evidence(bundle, dist / 'data/site-data.json')
        validate_repository_commit(dict(bundle, cases=dict(bundle['cases'], **territorial)), commit)
        reading = build_reading(bundle, commit, territorial)
        css = (ROOT / 'experiments/a7-dossier-preview/education.css').read_text()
        (stage / 'public.css').write_text((stage / 'public.css').read_text() + '\n' + css)
        (stage / 'education.json').write_text(json.dumps(reading, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        write_report(reading, css, stage / 'education.pdf')
        release = json.loads((stage / 'release.mjs').read_text().removeprefix('export default ').strip().removesuffix(';'))
        release.update(educationSha256=hashlib.sha256((stage / 'education.json').read_bytes()).hexdigest(),
                       educationPdfSha256=hashlib.sha256((stage / 'education.pdf').read_bytes()).hexdigest())
        (stage / 'release.mjs').write_text('export default ' + json.dumps(release, ensure_ascii=False, sort_keys=True) + ';\n')
        assets = {name: (stage / name).read_bytes() for name in FILES}
        manifest = manifest_text(assets)
        relative = 'releases/' + hashlib.sha256(manifest.encode()).hexdigest() + '/'
        destination = folder / relative
        destination.mkdir(parents=True, exist_ok=True)
        for name, data in dict(assets, **{'manifest.json': manifest.encode()}).items():
            target = destination / name
            if target.exists() and target.read_bytes() != data:
                raise ValueError('immutable_a7_asset_changed:' + name)
            target.write_bytes(data)
    for name in (*FILES, 'preview.css'):
        (folder / name).unlink(missing_ok=True)
    hero = original.header
    hero.name = 'section'
    hero['class'] = ['a7-hero', 'editorial-hero']
    hero.h1.string = 'Chiedi alla Versilia'
    hero.select_one('.eyebrow').string = 'CONOSCERE IL TERRITORIO'
    hero.select_one('h1 + p').string = 'Lavoro, famiglie, scuola: parti dalle tue domande e scopri che cosa raccontano i dati di Massarosa.'
    hero.select_one('.notice').string = 'Si parte da Massarosa: lavoro e infanzia/scuola. Ogni lettura indica a quale periodo si riferiscono i dati e che cosa resta da approfondire.'
    for selector, text in {
        '#scrivi':'Da dove vuoi partire?',
        'label[for=domanda-testo]':'Scrivi la tua domanda',
        '#aiuto-testo':'Scrivi ciò che ti interessa: ti aiutiamo a scegliere fra le domande disponibili qui sotto.',
        '#verifica-testo':'Trova un percorso',
        '#scegli':'Lasciati guidare dalle domande',
        'label[for=dossier]':'Di cosa vuoi sapere di più?',
        'label[for=domanda]':'Scegli una domanda',
        '#mostra':'Scopri cosa dicono i dati',
        '#titolo-consenso':'Prima di proseguire',
        '#accetta':'Prosegui con questi limiti',
    }.items(): original.select_one(selector).string=text
    original.select_one('#domanda-testo')['placeholder']='Per esempio: come cambia il lavoro a Massarosa?'
    original.select_one('#selezione + p').string='Questi primi percorsi riguardano lavoro e infanzia/scuola a Massarosa. Puoi esplorarli anche senza scrivere una domanda.'
    original.select_one('#chiarimento > p').string='Per questa richiesta non abbiamo ancora una risposta pronta. Puoi scegliere una delle domande qui sotto: ciascuna apre una lettura diversa, con le sue fonti e i suoi limiti.'
    original.select_one('#consenso > p').string='I dati aiutano a leggere una parte del problema, ma non bastano a rispondere a tutto. In alcuni confronti mancano dati per uno o più Comuni: te lo indichiamo insieme a ciò che non possiamo concludere.'
    local_note=original.new_tag('p',attrs={'class':'a7-how'});local_note.string='Le prime letture: lavoro · infanzia e scuola · Massarosa';hero.append(local_note)
    grid=original.new_tag('div',attrs={'class':'a7-question-grid'})
    original.main.insert(0,grid)
    grid.append(original.select_one('#scrivi').parent)
    grid.append(original.select_one('#scegli').parent)
    local_footer = original.footer
    local_footer.name = 'section'
    local_footer['aria-label'] = 'Limiti delle letture'
    original.main.noscript.clear()
    fallback = original.new_tag('p')
    fallback.string = 'Per scegliere una domanda occorre JavaScript. '
    link = original.new_tag('a', href=relative + 'answers.md')
    link.string = 'Leggi le evidenze in formato testo.'
    fallback.append(link)
    original.main.noscript.append(fallback)
    content = original.main.decode_contents() + str(local_footer)
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
{styles}<link rel="stylesheet" href="{relative}public.css"><meta name="theme-color" content="#0F3654">
</head><body class="antialiased" data-page="special" data-theme="" data-town="" data-prerendered="true">
<a class="a7-skip" href="#a7-guided">Vai alle domande</a>
{shell.header}<div id="app"><div class="a7-banner">{hero}</div><main id="a7-guided" data-a7-release="{relative}" class="editorial-page page-width a7-guided">
<nav aria-label="Percorso pagina"><a href="../">Home</a> · Chiedi alla Versilia</nav>
{content}
<p>Approfondisci i dati: <a href="../comuni/massarosa/">scheda di Massarosa</a> · <a href="../confronta/lavoro/">lavoro</a> · <a href="../confronta/istruzione/">istruzione</a> · <a href="../stato-dati/">stato dei dati</a>.</p>
</main></div>{shell.footer}
<script src="{html.escape(shell.app_bundle, quote=True)}" defer></script><script type="module" src="{relative}public.mjs"></script>
</body></html>''', encoding='utf-8')
    from build_static_brand_impl import cache_bust_app_bundle, cache_bust_favicon, inject_pwa
    page.write_text(inject_pwa(cache_bust_app_bundle(cache_bust_favicon(page.read_text(encoding='utf-8'))), '../'), encoding='utf-8')
    ensure_sitemap_entries(dist, (URL,))
    return page


if __name__ == '__main__':
    print('A7 guided public page generated: ' + str(build()))
