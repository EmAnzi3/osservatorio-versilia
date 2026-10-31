#!/usr/bin/env python3
"""Dossier in forma di relazione: controlli sulla pagina pubblicata nella build.

Verifica che ogni cifra mostrata coincida con una risposta calcolata dal motore,
che la pagina non rimandi a GitHub né offra JSON, che i numeri abbiano al
massimo due decimali, che il testo sia italiano senza codici tecnici e che la
versione per ciascun Comune sia completa. Il dossier resta fuori dall'indice dei
motori di ricerca finché il proprietario non ne approva il lancio.
"""
import argparse
import csv
import io
import re
from pathlib import Path

from bs4 import BeautifulSoup

from build_dossier_reports import DOSSIERS, Engine, period_label

TECHNICAL = re.compile(r'\w:\w|[|_]|\b[a-z]+[A-Z][a-zA-Z]*\b|nativeRatio|undefined|NaN')
ENGLISH = re.compile(r'\b(the|and|not|with|is|are|of)\b')


def verify(dist: Path):
    engine = Engine(dist / 'data/site-data.json')
    for key, make in DOSSIERS.items():
        dossier = make(engine)
        folder = dist / 'dossier' / dossier['slug']
        page = folder / 'index.html'
        text = page.read_text(encoding='utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        main = soup.select_one('main.dr')
        assert main is not None, key
        assert not soup.select_one('meta[name=robots]'), ('pagina_non_indicizzabile', key)
        assert f"https://osservatorioversilia.it/dossier/{dossier['slug']}/" in (dist / 'sitemap.xml').read_text(encoding='utf-8'), ('sitemap', key)
        hrefs = [a.get('href', '') for a in soup.select('a[href]')]
        assert not [h for h in hrefs if 'github' in h.lower()], ('link_github', key)
        assert not [h for h in hrefs if re.search(r'\.json(\b|$)', h)], ('json_scaricabile', key)
        for name in (f'{key}-versilia.pdf', f'{key}-dati.csv'):
            assert name in hrefs and (folder / name).exists(), ('download_mancante', name)

        visible = main.get_text(' ', strip=True)
        assert not re.search(r'\d,\d{3}', visible), ('troppi_decimali', re.findall(r'\S*\d,\d{3}\S*', visible)[:5])
        assert not TECHNICAL.search(visible), ('codice_tecnico', TECHNICAL.findall(visible)[:5])
        assert not ENGLISH.search(visible), ('testo_inglese', ENGLISH.findall(visible)[:5])

        # Un capitolo per voce dell'indice, ciascuno con la sua frase per Comune.
        chapters = main.select('section.dr-chapter[id]')
        toc = [a['href'][1:] for a in main.select('.dr-toc a')]
        assert [c['id'] for c in chapters] == toc, ('indice', toc)
        codes = set(engine.codes)
        for chapter in chapters:
            if chapter.select_one('.dr-why'):
                towns = [p['data-town'] for p in chapter.select('.dr-town-text')]
                assert sorted(towns) == sorted(codes), ('frasi_per_comune', chapter['id'])
        assert sorted(c['data-town'] for c in main.select('.dr-town-card')) == sorted(codes)
        options = [o['data-code'] for o in main.select('#dr-town option[data-code]')]
        assert sorted(options) == sorted(codes)
        assert not main.select('[data-town][hidden]:not(.dr-town-text):not(.dr-town-card)')

        # Grafici: ogni barra riporta il valore della risposta del motore.
        # Una misura può comparire solo nel testo (per esempio gli arrivi), mai un
        # grafico senza la sua misura.
        charts = main.select('figure.dr-chart')
        by_key = {f['aria-labelledby'].removeprefix('fig-'): f for f in charts}
        assert len(by_key) == len(charts) and set(by_key) <= set(dossier['measures']), sorted(by_key)
        assert len(charts) >= len(dossier['measures']) - 2, (len(charts), len(dossier['measures']))
        for key_, figure in by_key.items():
            measure = dossier['measures'][key_]
            shown = [(r['data-town'], r.select_one('.dr-val').get_text()) for r in figure.select('.dr-row')]
            assert shown == [(c, measure.short(v)) for c, v, _ in measure.ranking], ('grafico', measure.key)
            assert period_label(measure.period) in figure.figcaption.get_text()

        # CSV: separatore italiano, una riga per valore pubblicato.
        rows = list(csv.reader(io.StringIO((folder / f'{key}-dati.csv').read_bytes().decode('utf-8-sig')), delimiter=';'))
        assert rows[0] == ['Indicatore', 'Territorio', 'Periodo', 'Valore', 'Unità', 'Fonte']
        expected = sum(len(m.ranking) + len(m.benchmarks) + (m.versilia is not None) for m in dossier['measures'].values())
        assert len(rows) - 1 == expected, (len(rows) - 1, expected)
        assert all(re.fullmatch(r'−?-?\d+(,\d{1,2})?', r[3]) for r in rows[1:]), 'valori_csv'
        assert (folder / f'{key}-versilia.pdf').read_bytes()[:5] == b'%PDF-'
        yield key, len(chapters), engine.answers


def verify_index(dist: Path) -> int:
    """L'indice elenca ogni dossier una volta, con pagina, PDF e CSV esistenti."""
    soup = BeautifulSoup((dist / 'dossier/index.html').read_text(encoding='utf-8'), 'html.parser')
    assert not soup.select_one('meta[name=robots]'), 'indice_non_indicizzabile'
    assert 'https://osservatorioversilia.it/dossier/</loc>' in (dist / 'sitemap.xml').read_text(encoding='utf-8'), 'sitemap_indice'
    cards = soup.select('main.dr-index .dr-card')
    slugs = [c.select_one('a.dr-card-link')['href'].rstrip('/') for c in cards]
    assert len(slugs) == len(DOSSIERS) == len(set(slugs)), slugs
    for card, slug_ in zip(cards, slugs):
        assert (dist / 'dossier' / slug_ / 'index.html').exists(), slug_
        for a in card.select('.dr-card-files a'):
            assert (dist / 'dossier' / a['href']).exists(), a['href']
        assert not TECHNICAL.search(card.get_text(' ', strip=True)), slug_
    return len(cards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=Path(__file__).resolve().parents[1] / 'dist')
    dist = parser.parse_args().dist
    for key, chapters, answers in verify(dist):
        print(f'Dossier {key} PASS: {chapters} sezioni, versioni per 7 Comuni, nessun link a GitHub né JSON, '
              f'{answers} risposte calcolate dal motore')
    print(f'Indice dei dossier PASS: {verify_index(dist)} dossier con pagina, PDF e CSV')


if __name__ == '__main__':
    main()
